#property strict
#property indicator_chart_window
#property indicator_buffers 0

input string SnapshotChannel = "mtc-set-from-hq";
input int SnapshotIntervalSeconds = 5;
input int SnapshotBars = 240;

string SNAPSHOT_SCHEMA = "metafx-hq-mt4-snapshot-v1";


bool IsSafeChannel(const string value)
{
   int length = StringLen(value);
   if(length < 5 || length > 120 || StringSubstr(value, 0, 4) != "mtc-")
      return false;
   for(int index = 0; index < length; index++)
   {
      int character = StringGetCharacter(value, index);
      bool safe =
         (character >= 'a' && character <= 'z') ||
         (character >= 'A' && character <= 'Z') ||
         (character >= '0' && character <= '9') ||
         character == '-' || character == '_' || character == '.';
      if(!safe)
         return false;
   }
   return true;
}


string JsonEscape(const string value)
{
   string escaped = "";
   for(int index = 0; index < StringLen(value); index++)
   {
      string character = StringSubstr(value, index, 1);
      int code = StringGetCharacter(value, index);
      if(character == "\\")
         escaped += "\\\\";
      else if(character == "\"")
         escaped += "\\\"";
      else if(code < 32)
         escaped += " ";
      else
         escaped += character;
   }
   return escaped;
}


string JsonString(const string value)
{
   return "\"" + JsonEscape(value) + "\"";
}


string JsonNumber(const double value, const int digits)
{
   if(!MathIsValidNumber(value))
      return "0";
   return DoubleToString(value, digits);
}


string TimeframeLabel()
{
   switch(Period())
   {
      case PERIOD_M1:  return "M1";
      case PERIOD_M5:  return "M5";
      case PERIOD_M15: return "M15";
      case PERIOD_M30: return "M30";
      case PERIOD_H1:  return "H1";
      case PERIOD_H4:  return "H4";
      case PERIOD_D1:  return "D1";
      case PERIOD_W1:  return "W1";
      case PERIOD_MN1: return "MN1";
   }
   return "M1";
}


datetime BrokerDayStart()
{
   return StrToTime(TimeToString(TimeCurrent(), TIME_DATE));
}


string BuildBarsJson()
{
   int available = Bars - 1;
   int requested = MathMax(20, MathMin(SnapshotBars, 1000));
   int count = MathMin(available, requested);
   string rows = "[";
   bool first = true;
   for(int shift = count; shift >= 1; shift--)
   {
      if(iTime(Symbol(), Period(), shift) <= 0)
         continue;
      if(!first)
         rows += ",";
      first = false;
      rows += "{";
      rows += "\"time\":" + IntegerToString((int)iTime(Symbol(), Period(), shift)) + ",";
      rows += "\"open\":" + JsonNumber(iOpen(Symbol(), Period(), shift), Digits) + ",";
      rows += "\"high\":" + JsonNumber(iHigh(Symbol(), Period(), shift), Digits) + ",";
      rows += "\"low\":" + JsonNumber(iLow(Symbol(), Period(), shift), Digits) + ",";
      rows += "\"close\":" + JsonNumber(iClose(Symbol(), Period(), shift), Digits) + ",";
      rows += "\"volume\":" + IntegerToString((int)iVolume(Symbol(), Period(), shift));
      rows += "}";
   }
   rows += "]";
   return rows;
}


void ReadDailySummary(
   double &realized_profit,
   int &trades_closed,
   int &wins,
   int &losses
)
{
   realized_profit = 0.0;
   trades_closed = 0;
   wins = 0;
   losses = 0;
   datetime day_start = BrokerDayStart();
   int total = OrdersHistoryTotal();
   for(int index = 0; index < total; index++)
   {
      if(!OrderSelect(index, SELECT_BY_POS, MODE_HISTORY))
         continue;
      int order_type = OrderType();
      if((order_type != OP_BUY && order_type != OP_SELL) || OrderCloseTime() < day_start)
         continue;
      double result = OrderProfit() + OrderSwap() + OrderCommission();
      realized_profit += result;
      trades_closed++;
      if(result > 0.0)
         wins++;
      else if(result < 0.0)
         losses++;
   }
}


void ReadPositionSummary(
   int &position_count,
   int &buy_count,
   int &sell_count,
   double &total_lots,
   double &floating_profit
)
{
   position_count = 0;
   buy_count = 0;
   sell_count = 0;
   total_lots = 0.0;
   floating_profit = 0.0;
   int total = OrdersTotal();
   for(int index = 0; index < total; index++)
   {
      if(!OrderSelect(index, SELECT_BY_POS, MODE_TRADES))
         continue;
      int order_type = OrderType();
      if(order_type != OP_BUY && order_type != OP_SELL)
         continue;
      position_count++;
      if(order_type == OP_BUY)
         buy_count++;
      else
         sell_count++;
      total_lots += OrderLots();
      floating_profit += OrderProfit() + OrderSwap() + OrderCommission();
   }
}


string BuildSnapshotJson()
{
   RefreshRates();
   double realized_profit;
   int trades_closed;
   int wins;
   int losses;
   ReadDailySummary(realized_profit, trades_closed, wins, losses);

   int position_count;
   int buy_count;
   int sell_count;
   double total_lots;
   double floating_profit;
   ReadPositionSummary(
      position_count,
      buy_count,
      sell_count,
      total_lots,
      floating_profit
   );

   double spread_points = Point > 0.0 ? (Ask - Bid) / Point : 0.0;
   string server_day = TimeToString(BrokerDayStart(), TIME_DATE);
   string payload = "{";
   payload += "\"schemaVersion\":" + JsonString(SNAPSHOT_SCHEMA) + ",";
   payload += "\"adapterId\":" + JsonString(SnapshotChannel) + ",";
   payload += "\"mode\":\"read_only\",";
   payload += "\"chart\":{";
   payload += "\"symbol\":" + JsonString(Symbol()) + ",";
   payload += "\"timeframe\":" + JsonString(TimeframeLabel()) + ",";
   payload += "\"bid\":" + JsonNumber(Bid, Digits) + ",";
   payload += "\"ask\":" + JsonNumber(Ask, Digits) + ",";
   payload += "\"spreadPoints\":" + JsonNumber(spread_points, 2) + ",";
   payload += "\"bars\":" + BuildBarsJson();
   payload += "},";
   payload += "\"daily\":{";
   payload += "\"serverDay\":" + JsonString(server_day) + ",";
   payload += "\"realizedProfit\":" + JsonNumber(realized_profit, 2) + ",";
   payload += "\"floatingProfit\":" + JsonNumber(floating_profit, 2) + ",";
   payload += "\"netPnl\":" + JsonNumber(realized_profit + floating_profit, 2) + ",";
   payload += "\"tradesClosed\":" + IntegerToString(trades_closed) + ",";
   payload += "\"wins\":" + IntegerToString(wins) + ",";
   payload += "\"losses\":" + IntegerToString(losses);
   payload += "},";
   payload += "\"accountSummary\":{";
   payload += "\"currency\":" + JsonString(AccountCurrency()) + ",";
   payload += "\"balance\":" + JsonNumber(AccountBalance(), 2) + ",";
   payload += "\"equity\":" + JsonNumber(AccountEquity(), 2) + ",";
   payload += "\"margin\":" + JsonNumber(AccountMargin(), 2) + ",";
   payload += "\"freeMargin\":" + JsonNumber(AccountFreeMargin(), 2);
   payload += "},";
   payload += "\"positionsSummary\":{";
   payload += "\"count\":" + IntegerToString(position_count) + ",";
   payload += "\"buyCount\":" + IntegerToString(buy_count) + ",";
   payload += "\"sellCount\":" + IntegerToString(sell_count) + ",";
   payload += "\"totalLots\":" + JsonNumber(total_lots, 2) + ",";
   payload += "\"floatingProfit\":" + JsonNumber(floating_profit, 2);
   payload += "}";
   payload += "}";
   return payload;
}


bool WriteSnapshot()
{
   if(!IsSafeChannel(SnapshotChannel))
      return false;
   string folder = "MetafxHQ\\" + SnapshotChannel;
   FolderCreate("MetafxHQ", FILE_COMMON);
   if(!FolderCreate(folder, FILE_COMMON) && GetLastError() != 5004)
      ResetLastError();

   string temporary_name = folder + "\\snapshot.tmp";
   string final_name = folder + "\\snapshot.json";
   int handle = FileOpen(
      temporary_name,
      FILE_WRITE | FILE_TXT | FILE_ANSI | FILE_COMMON
   );
   if(handle == INVALID_HANDLE)
      return false;
   FileWriteString(handle, BuildSnapshotJson());
   FileFlush(handle);
   FileClose(handle);
   ResetLastError();
   return FileMove(
      temporary_name,
      FILE_COMMON,
      final_name,
      FILE_COMMON | FILE_REWRITE
   );
}


int OnInit()
{
   if(!IsSafeChannel(SnapshotChannel))
   {
      Print("MetafxHQ: SnapshotChannel ต้องเป็น Candidate ID ที่ขึ้นต้นด้วย mtc-");
      return INIT_PARAMETERS_INCORRECT;
   }
   if(SnapshotBars < 20 || SnapshotBars > 1000)
   {
      Print("MetafxHQ: SnapshotBars must be between 20 and 1000 closed bars.");
      return INIT_PARAMETERS_INCORRECT;
   }
   EventSetTimer(MathMax(2, MathMin(SnapshotIntervalSeconds, 60)));
   WriteSnapshot();
   return INIT_SUCCEEDED;
}


void OnDeinit(const int reason)
{
   EventKillTimer();
}


void OnTimer()
{
   WriteSnapshot();
}


int OnCalculate(
   const int rates_total,
   const int prev_calculated,
   const datetime &time[],
   const double &open[],
   const double &high[],
   const double &low[],
   const double &close[],
   const long &tick_volume[],
   const long &volume[],
   const int &spread[]
)
{
   return rates_total;
}
