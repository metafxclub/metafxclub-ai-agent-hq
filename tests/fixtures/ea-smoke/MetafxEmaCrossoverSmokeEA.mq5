#property strict
#property version   "1.00"
#property description "Tester-only EMA 10/60 crossover acceptance fixture"

#include <Trade/Trade.mqh>

#define SIGNAL_DATA_UNAVAILABLE -2
#define SIGNAL_NONE -1
#define COMPLETED_ORDER_MEMORY 8

input double StopLossPips   = 30.0;
input double TakeProfitPips = 60.0;

enum SmokeSignal
{
   SIGNAL_BUY  = 0,
   SIGNAL_SELL = 1
};

const int   EMA_FAST_PERIOD = 10;
const int   EMA_SLOW_PERIOD = 60;
const ulong SMOKE_MAGIC     = 26061060;
const double SMOKE_LOT      = 0.01;

CTrade trade;

int      gFastEmaHandle = INVALID_HANDLE;
int      gSlowEmaHandle = INVALID_HANDLE;
datetime gLastBarOpenTime = 0;
int      gBuySignals = 0;
int      gSellSignals = 0;
int      gBuyEntries = 0;
int      gSellEntries = 0;
int      gRejectedRequests = 0;
int      gOrphanEntries = 0;
int      gDataUnavailable = 0;
ulong    gSignalSequence = 0;
ulong    gPendingSignalSeq = 0;
int      gPendingDirection = SIGNAL_NONE;
datetime gPendingClosedBarTime = 0;
datetime gPendingSetTime = 0;
uint     gPendingRequestId = 0;
bool     gPendingRequestIdentityBound = false;
ulong    gPendingOrderTicket = 0;
ulong    gPendingAcceptedDealTicket = 0;
bool     gPendingEntryCounted = false;
bool     gPendingOrderFinalized = false;
int      gPendingFillCount = 0;
ulong    gCompletedOrderTickets[COMPLETED_ORDER_MEMORY];
ulong    gCompletedOrderSeqs[COMPLETED_ORDER_MEMORY];
int      gCompletedOrderDirections[COMPLETED_ORDER_MEMORY];
datetime gCompletedOrderBars[COMPLETED_ORDER_MEMORY];
int      gCompletedOrderCursor = 0;
double   gLastFastPrevious = EMPTY_VALUE;
double   gLastFastClosed = EMPTY_VALUE;
double   gLastSlowPrevious = EMPTY_VALUE;
double   gLastSlowClosed = EMPTY_VALUE;
string   gLastOutcome = "not_started";

void UpdateProofComment()
{
   Comment(StringFormat(
      "Metafx EMA 10/60 tester smoke\n"
      "Expected BUY signals: %d | Executed BUY entries: %d\n"
      "Expected SELL signals: %d | Executed SELL entries: %d\n"
      "EMA[2->1] fast=%.8f->%.8f slow=%.8f->%.8f\n"
      "Outcome: %s | Rejected: %d | Orphan: %d | Pending: %d | Data unavailable retries: %d",
      gBuySignals,
      gBuyEntries,
      gSellSignals,
      gSellEntries,
      gLastFastPrevious,
      gLastFastClosed,
      gLastSlowPrevious,
      gLastSlowClosed,
      gLastOutcome,
      gRejectedRequests,
      gOrphanEntries,
      gPendingSignalSeq == 0 ? 0 : 1,
      gDataUnavailable
   ));
}

string DirectionText(const int direction)
{
   if(direction == SIGNAL_BUY) return("BUY");
   if(direction == SIGNAL_SELL) return("SELL");
   return("NONE");
}

void EmitSignalEvent(
   const ulong seq,
   const int direction,
   const datetime closedBarTime,
   const double fast2,
   const double fast1,
   const double slow2,
   const double slow1)
{
   PrintFormat(
      "EMA_SMOKE_V1 {\"event\":\"signal\",\"seq\":%I64u,\"direction\":\"%s\",\"closed_bar_time\":%I64d,\"fast_period\":%d,\"slow_period\":%d,\"previous_shift\":2,\"current_shift\":1,\"fast_2\":%.10f,\"fast_1\":%.10f,\"slow_2\":%.10f,\"slow_1\":%.10f}",
      seq,
      DirectionText(direction),
      (long)closedBarTime,
      EMA_FAST_PERIOD,
      EMA_SLOW_PERIOD,
      fast2,
      fast1,
      slow2,
      slow1
   );
}

void ClearPendingSignal()
{
   gPendingSignalSeq = 0;
   gPendingDirection = SIGNAL_NONE;
   gPendingClosedBarTime = 0;
   gPendingSetTime = 0;
   gPendingRequestId = 0;
   gPendingRequestIdentityBound = false;
   gPendingOrderTicket = 0;
   gPendingAcceptedDealTicket = 0;
   gPendingEntryCounted = false;
   gPendingOrderFinalized = false;
   gPendingFillCount = 0;
}

void SetPendingSignal(
   const ulong seq,
   const int direction,
   const datetime closedBarTime)
{
   gPendingSignalSeq = seq;
   gPendingDirection = direction;
   gPendingClosedBarTime = closedBarTime;
   gPendingSetTime = TimeCurrent();
   gPendingRequestId = 0;
   gPendingRequestIdentityBound = false;
   gPendingOrderTicket = 0;
   gPendingAcceptedDealTicket = 0;
   gPendingEntryCounted = false;
   gPendingOrderFinalized = false;
   gPendingFillCount = 0;
   PrintFormat(
      "EMA_SMOKE_V1 {\"event\":\"pending\",\"seq\":%I64u,\"direction\":\"%s\",\"closed_bar_time\":%I64d}",
      seq,
      DirectionText(direction),
      (long)closedBarTime
   );
}

bool BindPendingRequest(
   const ulong seq,
   const uint requestId,
   const ulong orderTicket,
   const ulong dealTicket)
{
   // request_id is zero-based in the MT5 Strategy Tester, so id 0 is valid
   // for the first synchronous request.  The explicit bound flag distinguishes
   // that valid identity from the reset state while order/deal stays required.
   if(gPendingSignalSeq != seq ||
      (orderTicket == 0 && dealTicket == 0)) return(false);
   gPendingRequestId = requestId;
   gPendingOrderTicket = orderTicket;
   gPendingAcceptedDealTicket = dealTicket;
   gPendingRequestIdentityBound = true;
   PrintFormat(
      "EMA_SMOKE_AUDIT_V1 {\"event\":\"accepted\",\"seq\":%I64u,\"request_id\":%u,\"order\":%I64u,\"deal\":%I64u}",
      seq,
      requestId,
      orderTicket,
      dealTicket
   );
   return(true);
}

void RememberCompletedOrder(
   const ulong orderTicket,
   const ulong seq,
   const int direction,
   const datetime closedBarTime)
{
   if(orderTicket == 0) return;
   const int slot = gCompletedOrderCursor % COMPLETED_ORDER_MEMORY;
   gCompletedOrderTickets[slot] = orderTicket;
   gCompletedOrderSeqs[slot] = seq;
   gCompletedOrderDirections[slot] = direction;
   gCompletedOrderBars[slot] = closedBarTime;
   ++gCompletedOrderCursor;
}

bool MatchCompletedOrder(
   const ulong orderTicket,
   const int direction,
   ulong &seq,
   datetime &closedBarTime)
{
   if(orderTicket == 0) return(false);
   for(int index = 0; index < COMPLETED_ORDER_MEMORY; ++index)
   {
      if(gCompletedOrderTickets[index] != orderTicket ||
         gCompletedOrderDirections[index] != direction) continue;
      seq = gCompletedOrderSeqs[index];
      closedBarTime = gCompletedOrderBars[index];
      return(true);
   }
   return(false);
}

void CompletePendingSignal(const string reason)
{
   if(gPendingSignalSeq == 0) return;
   const ulong seq = gPendingSignalSeq;
   const uint requestId = gPendingRequestId;
   const ulong orderTicket = gPendingOrderTicket;
   const int direction = gPendingDirection;
   const datetime closedBarTime = gPendingClosedBarTime;
   const int fills = gPendingFillCount;
   RememberCompletedOrder(orderTicket, seq, direction, closedBarTime);
   PrintFormat(
      "EMA_SMOKE_AUDIT_V1 {\"event\":\"entry_complete\",\"seq\":%I64u,\"request_id\":%u,\"order\":%I64u,\"fills\":%d,\"reason\":\"%s\"}",
      seq,
      requestId,
      orderTicket,
      fills,
      reason
   );
   ClearPendingSignal();
   UpdateProofComment();
}

bool RejectSignal(
   const ulong seq,
   const int direction,
   const datetime closedBarTime,
   const string reason)
{
   ++gRejectedRequests;
   if(gPendingSignalSeq == seq) ClearPendingSignal();
   gLastOutcome = reason;
   PrintFormat(
      "EMA_SMOKE_V1 {\"event\":\"rejected\",\"seq\":%I64u,\"direction\":\"%s\",\"closed_bar_time\":%I64d,\"reason\":\"%s\"}",
      seq,
      DirectionText(direction),
      (long)closedBarTime,
      reason
   );
   UpdateProofComment();
   return(false);
}

bool ResolvePendingTimeout()
{
   if(gPendingSignalSeq == 0) return(false);
   if(gPendingOrderFinalized && gPendingEntryCounted)
   {
      CompletePendingSignal("order_finalized");
      return(true);
   }
   const int timeoutSeconds = (int)MathMax((double)PeriodSeconds(_Period), 60.0);
   if(gPendingSetTime > 0 && TimeCurrent() - gPendingSetTime <= timeoutSeconds)
      return(false);
   if(gPendingEntryCounted)
   {
      CompletePendingSignal("entry_timeout_finalized");
      return(true);
   }
   const ulong seq = gPendingSignalSeq;
   const int direction = gPendingDirection;
   const datetime closedBarTime = gPendingClosedBarTime;
   RejectSignal(seq, direction, closedBarTime, "pending_timeout");
   return(true);
}

int VolumeDigits(const double step)
{
   for(int digits = 0; digits <= 8; ++digits)
   {
      const double scaled = step * MathPow(10.0, digits);
      if(MathAbs(scaled - MathRound(scaled)) <= 1e-8)
         return(digits);
   }
   return(8);
}

double NormalizeSmokeVolume()
{
   const double minimum = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   const double maximum = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   const double step    = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);

   if(!MathIsValidNumber(minimum) || !MathIsValidNumber(maximum) ||
      !MathIsValidNumber(step) || minimum <= 0.0 || maximum < minimum || step <= 0.0)
      return(0.0);

   if(SMOKE_LOT < minimum - 1e-9 || SMOKE_LOT > maximum + 1e-9)
      return(0.0);
   const double aligned = MathRound(SMOKE_LOT / step) * step;
   if(MathAbs(aligned - SMOKE_LOT) > MathMax(1e-9, step * 1e-8))
      return(0.0);
   if(aligned < minimum - 1e-9 || aligned > maximum + 1e-9)
      return(0.0);
   return(NormalizeDouble(aligned, VolumeDigits(step)));
}

double PipSize()
{
   const int digits = (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS);
   const double point = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
   if(point <= 0.0 || !MathIsValidNumber(point))
      return(0.0);
   return((digits == 3 || digits == 5) ? point * 10.0 : point);
}

double BrokerProtectionDistance()
{
   const double point = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
   double tickSize = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   if(point <= 0.0 || !MathIsValidNumber(point))
      return(0.0);
   if(tickSize <= 0.0 || !MathIsValidNumber(tickSize)) tickSize = point;

   const long stopsLevelPoints = SymbolInfoInteger(_Symbol, SYMBOL_TRADE_STOPS_LEVEL);
   const long freezeLevelPoints = SymbolInfoInteger(_Symbol, SYMBOL_TRADE_FREEZE_LEVEL);
   const long protectionLevelPoints = MathMax(
      MathMax(stopsLevelPoints, 0),
      MathMax(freezeLevelPoints, 0)
   );
   return((double)protectionLevelPoints * point + tickSize);
}

double NormalizePriceDirectional(const double price, const bool roundUp)
{
   const int digits = (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS);
   double tickSize = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   if(tickSize <= 0.0 || !MathIsValidNumber(tickSize))
      tickSize = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
   if(tickSize <= 0.0 || !MathIsValidNumber(tickSize))
      return(0.0);

   const double ticks = price / tickSize;
   const double rounded = roundUp
      ? MathCeil(ticks - 1e-9) * tickSize
      : MathFloor(ticks + 1e-9) * tickSize;
   return(NormalizeDouble(rounded, digits));
}

bool TradeResultAccepted()
{
   const uint retcode = trade.ResultRetcode();
   return(retcode == TRADE_RETCODE_DONE ||
          retcode == TRADE_RETCODE_DONE_PARTIAL ||
          retcode == TRADE_RETCODE_PLACED);
}

int CountManagedPositions(int &singleDirection)
{
   int count = 0;
   singleDirection = SIGNAL_NONE;

   for(int index = PositionsTotal() - 1; index >= 0; --index)
   {
      const ulong ticket = PositionGetTicket(index);
      if(ticket == 0)
         continue;
      if(PositionGetString(POSITION_SYMBOL) != _Symbol)
         continue;
      if((ulong)PositionGetInteger(POSITION_MAGIC) != SMOKE_MAGIC)
         continue;

      const ENUM_POSITION_TYPE type = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
      const int direction = (type == POSITION_TYPE_BUY) ? SIGNAL_BUY : SIGNAL_SELL;
      if(count == 0)
         singleDirection = direction;
      else if(singleDirection != direction)
         singleDirection = SIGNAL_NONE;
      ++count;
   }
   for(int index = OrdersTotal() - 1; index >= 0; --index)
   {
      const ulong ticket = OrderGetTicket(index);
      if(ticket == 0)
         continue;
      if(OrderGetString(ORDER_SYMBOL) != _Symbol)
         continue;
      if((ulong)OrderGetInteger(ORDER_MAGIC) != SMOKE_MAGIC)
         continue;
      singleDirection = SIGNAL_NONE;
      ++count;
   }
   return(count);
}

bool CloseManagedPositions()
{
   bool allClosed = true;
   for(int index = PositionsTotal() - 1; index >= 0; --index)
   {
      const ulong ticket = PositionGetTicket(index);
      if(ticket == 0)
         continue;
      if(PositionGetString(POSITION_SYMBOL) != _Symbol)
         continue;
      if((ulong)PositionGetInteger(POSITION_MAGIC) != SMOKE_MAGIC)
         continue;

      ResetLastError();
      const bool sent = trade.PositionClose(ticket);
      if(!sent || !TradeResultAccepted())
      {
         allClosed = false;
         PrintFormat(
            "SMOKE_CLOSE rejected | ticket=%I64u | retcode=%u | last_error=%d",
            ticket,
            trade.ResultRetcode(),
            GetLastError()
         );
      }
   }
   UpdateProofComment();
   return(allClosed);
}

int ReadClosedBarSignal(
   double &fastPreviousValue,
   double &fastClosedValue,
   double &slowPreviousValue,
   double &slowClosedValue)
{
   double fastPrevious[1];
   double fastClosed[1];
   double slowPrevious[1];
   double slowClosed[1];

   // Index 2 is the bar before the latest completed bar; index 1 is the
   // latest completed bar. Index 0 is intentionally never used for signals.
   if(CopyBuffer(gFastEmaHandle, 0, 2, 1, fastPrevious) != 1 ||
      CopyBuffer(gFastEmaHandle, 0, 1, 1, fastClosed) != 1 ||
      CopyBuffer(gSlowEmaHandle, 0, 2, 1, slowPrevious) != 1 ||
      CopyBuffer(gSlowEmaHandle, 0, 1, 1, slowClosed) != 1)
   {
      PrintFormat("SMOKE_DATA CopyBuffer not ready | last_error=%d", GetLastError());
      ++gDataUnavailable;
      gLastOutcome = "data_unavailable";
      UpdateProofComment();
      return(SIGNAL_DATA_UNAVAILABLE);
   }

   if(!MathIsValidNumber(fastPrevious[0]) || !MathIsValidNumber(fastClosed[0]) ||
      !MathIsValidNumber(slowPrevious[0]) || !MathIsValidNumber(slowClosed[0]) ||
      fastPrevious[0] == EMPTY_VALUE || fastClosed[0] == EMPTY_VALUE ||
      slowPrevious[0] == EMPTY_VALUE || slowClosed[0] == EMPTY_VALUE)
   {
      ++gDataUnavailable;
      gLastOutcome = "data_unavailable";
      UpdateProofComment();
      return(SIGNAL_DATA_UNAVAILABLE);
   }

   fastPreviousValue = fastPrevious[0];
   fastClosedValue = fastClosed[0];
   slowPreviousValue = slowPrevious[0];
   slowClosedValue = slowClosed[0];
   gLastFastPrevious = fastPreviousValue;
   gLastFastClosed = fastClosedValue;
   gLastSlowPrevious = slowPreviousValue;
   gLastSlowClosed = slowClosedValue;

   if(fastPreviousValue <= slowPreviousValue && fastClosedValue > slowClosedValue)
      return(SIGNAL_BUY);
   if(fastPreviousValue >= slowPreviousValue && fastClosedValue < slowClosedValue)
      return(SIGNAL_SELL);
   gLastOutcome = "no_signal";
   UpdateProofComment();
   return(SIGNAL_NONE);
}

bool ResolveSmokeFillingMode(ENUM_ORDER_TYPE_FILLING &filling)
{
   const long flags = SymbolInfoInteger(_Symbol, SYMBOL_FILLING_MODE);
   const long execution = SymbolInfoInteger(_Symbol, SYMBOL_TRADE_EXEMODE);
   if((flags & SYMBOL_FILLING_FOK) == SYMBOL_FILLING_FOK)
   {
      filling = ORDER_FILLING_FOK;
      return(true);
   }
   if((flags & SYMBOL_FILLING_IOC) == SYMBOL_FILLING_IOC)
   {
      filling = ORDER_FILLING_IOC;
      return(true);
   }
   if(execution != SYMBOL_TRADE_EXECUTION_MARKET)
   {
      filling = ORDER_FILLING_RETURN;
      return(true);
   }
   return(false);
}

bool OpenSignal(
   const int signal,
   const ulong signalSeq,
   const datetime closedBarTime)
{
   MqlTick tick;
   if(!SymbolInfoTick(_Symbol, tick))
   {
      PrintFormat("SMOKE_REQUEST no tick | last_error=%d", GetLastError());
      return(RejectSignal(signalSeq, signal, closedBarTime, "invalid_tick"));
   }
   if(!MathIsValidNumber(tick.bid) || !MathIsValidNumber(tick.ask) ||
      tick.bid <= 0.0 || tick.ask <= 0.0 || tick.ask < tick.bid)
   {
      Print("SMOKE_REQUEST invalid bid/ask contract");
      return(RejectSignal(signalSeq, signal, closedBarTime, "invalid_tick"));
   }

   const double volume = NormalizeSmokeVolume();
   if(volume <= 0.0)
   {
      Print("SMOKE_REQUEST invalid broker volume contract");
      return(RejectSignal(signalSeq, signal, closedBarTime, "invalid_volume"));
   }

   const double pip = PipSize();
   const double brokerMinimum = BrokerProtectionDistance();
   if(pip <= 0.0 || brokerMinimum <= 0.0)
   {
      Print("SMOKE_REQUEST invalid point/pip/stop-distance contract");
      return(RejectSignal(signalSeq, signal, closedBarTime, "invalid_stop_contract"));
   }
   const double requestedSLDistance = StopLossPips * pip;
   const double requestedTPDistance = TakeProfitPips * pip;
   const double entryPrice = signal == SIGNAL_BUY ? tick.ask : tick.bid;
   double stopLoss = 0.0;
   double takeProfit = 0.0;
   bool sent = false;

   if(signal == SIGNAL_BUY)
   {
      stopLoss = NormalizePriceDirectional(
         MathMin(entryPrice - requestedSLDistance, tick.bid - brokerMinimum),
         false
      );
      takeProfit = NormalizePriceDirectional(
         MathMax(entryPrice + requestedTPDistance, tick.ask + brokerMinimum),
         true
      );
   }
   else if(signal == SIGNAL_SELL)
   {
      stopLoss = NormalizePriceDirectional(
         MathMax(entryPrice + requestedSLDistance, tick.ask + brokerMinimum),
         true
      );
      takeProfit = NormalizePriceDirectional(
         MathMin(entryPrice - requestedTPDistance, tick.bid - brokerMinimum),
         false
      );
   }

   const bool buyStopsValid = signal == SIGNAL_BUY &&
      stopLoss <= entryPrice - requestedSLDistance + 1e-9 &&
      takeProfit >= entryPrice + requestedTPDistance - 1e-9 &&
      stopLoss <= tick.bid - brokerMinimum + 1e-9 &&
      takeProfit >= tick.ask + brokerMinimum - 1e-9;
   const bool sellStopsValid = signal == SIGNAL_SELL &&
      stopLoss >= entryPrice + requestedSLDistance - 1e-9 &&
      takeProfit <= entryPrice - requestedTPDistance + 1e-9 &&
      stopLoss >= tick.ask + brokerMinimum - 1e-9 &&
      takeProfit <= tick.bid - brokerMinimum + 1e-9;
   if(stopLoss <= 0.0 || takeProfit <= 0.0 ||
      (!buyStopsValid && !sellStopsValid))
      return(RejectSignal(signalSeq, signal, closedBarTime, "invalid_normalized_stops"));

   SetPendingSignal(signalSeq, signal, closedBarTime);
   ResetLastError();
   if(signal == SIGNAL_BUY)
      sent = trade.Buy(volume, _Symbol, entryPrice, stopLoss, takeProfit, "EMA10x60 smoke BUY");
   else if(signal == SIGNAL_SELL)
      sent = trade.Sell(volume, _Symbol, entryPrice, stopLoss, takeProfit, "EMA10x60 smoke SELL");

   if(!sent || !TradeResultAccepted())
   {
      PrintFormat(
         "SMOKE_REQUEST %s rejected | retcode=%u | last_error=%d | volume=%.8f | sl=%.8f | tp=%.8f",
         signal == SIGNAL_BUY ? "BUY" : "SELL",
         trade.ResultRetcode(),
         GetLastError(),
         volume,
         stopLoss,
         takeProfit
      );
      return(RejectSignal(signalSeq, signal, closedBarTime, "open_rejected"));
   }

   MqlTradeResult acceptedResult = {};
   trade.Result(acceptedResult);
   if(!BindPendingRequest(
      signalSeq,
      acceptedResult.request_id,
      acceptedResult.order,
      acceptedResult.deal))
      return(RejectSignal(signalSeq, signal, closedBarTime, "accepted_identity_missing"));

   PrintFormat(
      "SMOKE_REQUEST %s accepted | volume=%.8f | sl=%.8f | tp=%.8f | retcode=%u",
      signal == SIGNAL_BUY ? "BUY" : "SELL",
      volume,
      stopLoss,
      takeProfit,
      trade.ResultRetcode()
   );
   if(gPendingSignalSeq == signalSeq)
   {
      gLastOutcome = signal == SIGNAL_BUY ? "buy_request_accepted" : "sell_request_accepted";
      UpdateProofComment();
   }
   return(true);
}

void ProcessSignal(
   const int signal,
   const datetime closedBarTime,
   const double fast2,
   const double fast1,
   const double slow2,
   const double slow1)
{
   if(signal == SIGNAL_BUY)
   {
      ++gBuySignals;
      gLastOutcome = "buy_signal";
   }
   else if(signal == SIGNAL_SELL)
   {
      ++gSellSignals;
      gLastOutcome = "sell_signal";
   }
   else
      return;

   const ulong signalSeq = ++gSignalSequence;
   EmitSignalEvent(
      signalSeq,
      signal,
      closedBarTime,
      fast2,
      fast1,
      slow2,
      slow1
   );

   PrintFormat(
      "SMOKE_SIGNAL %s expected | buy_signals=%d | sell_signals=%d",
      signal == SIGNAL_BUY ? "BUY" : "SELL",
      gBuySignals,
      gSellSignals
   );
   UpdateProofComment();

   int currentDirection = SIGNAL_NONE;
   const int managedCount = CountManagedPositions(currentDirection);
   if(managedCount == 1 && currentDirection == signal)
   {
      RejectSignal(signalSeq, signal, closedBarTime, "same_direction_exists");
      return;
   }

   // Opposite, mixed, or duplicate managed positions are closed first. A new
   // entry is allowed only after the symbol/magic invariant is empty again.
   if(managedCount > 0)
   {
      if(!CloseManagedPositions())
      {
         RejectSignal(signalSeq, signal, closedBarTime, "close_failed");
         return;
      }
      int remainingDirection = SIGNAL_NONE;
      if(CountManagedPositions(remainingDirection) != 0)
      {
         Print("SMOKE_INVARIANT managed position remained after close; reverse blocked");
         RejectSignal(signalSeq, signal, closedBarTime, "existing_managed_position");
         return;
      }
   }

   OpenSignal(signal, signalSeq, closedBarTime);
}

int OnInit()
{
   // This fixture is an acceptance-test instrument, not a live trading EA.
   if(MQLInfoInteger(MQL_TESTER) == 0)
   {
      Print("SMOKE_GUARD tester-only EA refused to initialize outside Strategy Tester");
      return(INIT_FAILED);
   }
   if(!MathIsValidNumber(StopLossPips) || !MathIsValidNumber(TakeProfitPips) ||
      StopLossPips <= 0.0 || TakeProfitPips <= 0.0)
   {
      Print("SMOKE_GUARD StopLossPips and TakeProfitPips must be finite and positive");
      return(INIT_PARAMETERS_INCORRECT);
   }

   gFastEmaHandle = iMA(_Symbol, PERIOD_CURRENT, EMA_FAST_PERIOD, 0, MODE_EMA, PRICE_CLOSE);
   gSlowEmaHandle = iMA(_Symbol, PERIOD_CURRENT, EMA_SLOW_PERIOD, 0, MODE_EMA, PRICE_CLOSE);
   if(gFastEmaHandle == INVALID_HANDLE || gSlowEmaHandle == INVALID_HANDLE)
   {
      PrintFormat("SMOKE_INIT EMA handle creation failed | last_error=%d", GetLastError());
      return(INIT_FAILED);
   }

   trade.SetExpertMagicNumber(SMOKE_MAGIC);
   trade.SetAsyncMode(false);
   trade.SetDeviationInPoints(20);
   ENUM_ORDER_TYPE_FILLING filling = ORDER_FILLING_FOK;
   if(!ResolveSmokeFillingMode(filling))
   {
      PrintFormat("SMOKE_INIT unsupported symbol filling mode | last_error=%d", GetLastError());
      return(INIT_FAILED);
   }
   trade.SetTypeFilling(filling);

   gLastOutcome = "ready";
   UpdateProofComment();
   PrintFormat(
      "SMOKE_INIT ready | symbol=%s | timeframe=%s | EMA=%d/%d | SL=%.2f pips | TP=%.2f pips",
      _Symbol,
      EnumToString((ENUM_TIMEFRAMES)_Period),
      EMA_FAST_PERIOD,
      EMA_SLOW_PERIOD,
      StopLossPips,
      TakeProfitPips
   );
   return(INIT_SUCCEEDED);
}

void OnDeinit(const int reason)
{
   if(gPendingSignalSeq != 0)
   {
      if(gPendingEntryCounted)
         CompletePendingSignal("deinit_entry_complete");
      else
      {
         const ulong seq = gPendingSignalSeq;
         const int direction = gPendingDirection;
         const datetime closedBarTime = gPendingClosedBarTime;
         RejectSignal(seq, direction, closedBarTime, "deinit_pending");
      }
   }
   if(gFastEmaHandle != INVALID_HANDLE)
      IndicatorRelease(gFastEmaHandle);
   if(gSlowEmaHandle != INVALID_HANDLE)
      IndicatorRelease(gSlowEmaHandle);

   PrintFormat(
      "EMA_SMOKE_V1 {\"event\":\"final\",\"reason\":%d,\"signal\":%d,\"entry\":%d,\"rejected\":%d,\"orphan\":%d,\"pending\":%d,\"data_unavailable\":%d,\"buy_signals\":%d,\"sell_signals\":%d,\"buy_entries\":%d,\"sell_entries\":%d,\"outcome\":\"%s\"}",
      reason,
      gBuySignals + gSellSignals,
      gBuyEntries + gSellEntries,
      gRejectedRequests,
      gOrphanEntries,
      gPendingSignalSeq == 0 ? 0 : 1,
      gDataUnavailable,
      gBuySignals,
      gSellSignals,
      gBuyEntries,
      gSellEntries,
      gLastOutcome
   );
   Comment("");
}

void OnTick()
{
   if(MQLInfoInteger(MQL_TESTER) == 0) return;
   if(gPendingSignalSeq != 0)
   {
      ResolvePendingTimeout();
      return;
   }
   const datetime currentBarOpenTime = iTime(_Symbol, PERIOD_CURRENT, 0);
   if(currentBarOpenTime <= 0 || currentBarOpenTime == gLastBarOpenTime)
      return;

   double fastPreviousValue = EMPTY_VALUE;
   double fastClosedValue = EMPTY_VALUE;
   double slowPreviousValue = EMPTY_VALUE;
   double slowClosedValue = EMPTY_VALUE;
   const int signal = ReadClosedBarSignal(
      fastPreviousValue,
      fastClosedValue,
      slowPreviousValue,
      slowClosedValue
   );
   if(signal == SIGNAL_DATA_UNAVAILABLE)
      return;

   const datetime closedBarTime = iTime(_Symbol, PERIOD_CURRENT, 1);
   if(closedBarTime <= 0)
   {
      ++gDataUnavailable;
      gLastOutcome = "closed_bar_time_unavailable";
      UpdateProofComment();
      return;
   }

   // Commit this bar only after all four closed-bar reads are ready. A
   // transient CopyBuffer miss is retried on the next tick of the same bar.
   gLastBarOpenTime = currentBarOpenTime;
   ProcessSignal(
      signal,
      closedBarTime,
      fastPreviousValue,
      fastClosedValue,
      slowPreviousValue,
      slowClosedValue
   );
}

void OnTradeTransaction(
   const MqlTradeTransaction &transaction,
   const MqlTradeRequest &request,
   const MqlTradeResult &result
)
{
   if(transaction.type == TRADE_TRANSACTION_REQUEST)
   {
      if(gPendingSignalSeq != 0 && gPendingRequestIdentityBound &&
         result.request_id == gPendingRequestId &&
         request.action == TRADE_ACTION_DEAL &&
         request.symbol == _Symbol && request.magic == SMOKE_MAGIC &&
         (int)request.type == gPendingDirection)
      {
         if(gPendingOrderTicket == 0 && result.order != 0)
            gPendingOrderTicket = result.order;
         if(gPendingAcceptedDealTicket == 0 && result.deal != 0)
            gPendingAcceptedDealTicket = result.deal;
      }
      return;
   }
   if((transaction.type == TRADE_TRANSACTION_ORDER_DELETE ||
       transaction.type == TRADE_TRANSACTION_HISTORY_ADD) &&
      gPendingSignalSeq != 0 && gPendingOrderTicket != 0 &&
      transaction.order == gPendingOrderTicket)
   {
      gPendingOrderFinalized = true;
      PrintFormat(
         "EMA_SMOKE_AUDIT_V1 {\"event\":\"order_finalized\",\"seq\":%I64u,\"request_id\":%u,\"order\":%I64u}",
         gPendingSignalSeq,
         gPendingRequestId,
         gPendingOrderTicket
      );
      return;
   }
   if(transaction.type != TRADE_TRANSACTION_DEAL_ADD || transaction.deal == 0)
      return;
   if(!HistoryDealSelect(transaction.deal))
      return;
   if(HistoryDealGetString(transaction.deal, DEAL_SYMBOL) != _Symbol)
      return;
   if((ulong)HistoryDealGetInteger(transaction.deal, DEAL_MAGIC) != SMOKE_MAGIC)
      return;

   const ENUM_DEAL_ENTRY entry = (ENUM_DEAL_ENTRY)HistoryDealGetInteger(transaction.deal, DEAL_ENTRY);
   if(entry != DEAL_ENTRY_IN && entry != DEAL_ENTRY_INOUT)
      return;

   const ENUM_DEAL_TYPE type = (ENUM_DEAL_TYPE)HistoryDealGetInteger(transaction.deal, DEAL_TYPE);
   int direction = SIGNAL_NONE;
   if(type == DEAL_TYPE_BUY) direction = SIGNAL_BUY;
   else if(type == DEAL_TYPE_SELL) direction = SIGNAL_SELL;
   else return;

   const ulong dealOrder = (ulong)HistoryDealGetInteger(transaction.deal, DEAL_ORDER);
   ulong completedSeq = 0;
   datetime completedClosedBarTime = 0;
   if(MatchCompletedOrder(
      dealOrder,
      direction,
      completedSeq,
      completedClosedBarTime))
   {
      PrintFormat(
         "EMA_SMOKE_AUDIT_V1 {\"event\":\"entry_fill_late\",\"seq\":%I64u,\"direction\":\"%s\",\"closed_bar_time\":%I64d,\"order\":%I64u,\"deal\":%I64u}",
         completedSeq,
         DirectionText(direction),
         (long)completedClosedBarTime,
         dealOrder,
         transaction.deal
      );
      return;
   }
   const bool acceptedDealMatches = gPendingOrderTicket == 0 &&
      gPendingAcceptedDealTicket != 0 &&
      transaction.deal == gPendingAcceptedDealTicket;
   const bool acceptedOrderMatches = gPendingOrderTicket != 0 &&
      dealOrder != 0 && dealOrder == gPendingOrderTicket;
   if(gPendingSignalSeq == 0 || !gPendingRequestIdentityBound ||
      gPendingDirection != direction || dealOrder == 0 ||
      (!acceptedDealMatches && !acceptedOrderMatches))
   {
      ++gOrphanEntries;
      gLastOutcome = "orphan_entry";
      PrintFormat(
         "EMA_SMOKE_V1 {\"event\":\"orphan_entry\",\"direction\":\"%s\",\"order\":%I64u,\"deal\":%I64u,\"orphan\":%d}",
         DirectionText(direction),
         dealOrder,
         transaction.deal,
         gOrphanEntries
      );
      UpdateProofComment();
      return;
   }

   if(gPendingOrderTicket == 0) gPendingOrderTicket = dealOrder;
   const ulong matchedSeq = gPendingSignalSeq;
   const datetime matchedClosedBarTime = gPendingClosedBarTime;
   ++gPendingFillCount;
   if(!gPendingEntryCounted)
   {
      gPendingEntryCounted = true;
      if(direction == SIGNAL_BUY)
      {
         ++gBuyEntries;
         gLastOutcome = "buy_entry_executed";
      }
      else
      {
         ++gSellEntries;
         gLastOutcome = "sell_entry_executed";
      }

      PrintFormat(
         "EMA_SMOKE_V1 {\"event\":\"entry\",\"seq\":%I64u,\"direction\":\"%s\",\"closed_bar_time\":%I64d,\"deal\":%I64u}",
         matchedSeq,
         DirectionText(direction),
         (long)matchedClosedBarTime,
         transaction.deal
      );
      PrintFormat(
         "EMA_SMOKE_AUDIT_V1 {\"event\":\"entry_identity\",\"seq\":%I64u,\"request_id\":%u,\"order\":%I64u,\"deal\":%I64u}",
         matchedSeq,
         gPendingRequestId,
         dealOrder,
         transaction.deal
      );
   }
   else
   {
      PrintFormat(
         "EMA_SMOKE_AUDIT_V1 {\"event\":\"entry_fill\",\"seq\":%I64u,\"direction\":\"%s\",\"closed_bar_time\":%I64d,\"order\":%I64u,\"deal\":%I64u,\"late\":false}",
         matchedSeq,
         DirectionText(direction),
         (long)matchedClosedBarTime,
         dealOrder,
         transaction.deal
      );
   }
   UpdateProofComment();
}

double OnTester()
{
   // Non-zero only when the Strategy Tester actually executed entry deals.
   return((double)(gBuyEntries + gSellEntries));
}
