#property strict
#property version   "1.03"
#property description "Metafxclub AI Agent HQ Unified MT5 Gateway"
#property description "Snapshot publisher plus guarded FILE_COMMON command adapter"

enum ENUM_GATEWAY_MODE
{
   GATEWAY_SHADOW = 0,
   GATEWAY_DEMO = 1,
   GATEWAY_LIVE = 2
};

enum ENUM_POSITION_LIFECYCLE_MODE
{
   LIFECYCLE_SLTP_ONLY = 0,
   LIFECYCLE_MAX_HOLDING = 1,
   LIFECYCLE_SESSION_CLOSE = 2,
   LIFECYCLE_MAX_HOLDING_AND_SESSION_CLOSE = 3
};

enum ENUM_MONEY_MANAGEMENT_MODE
{
   MONEY_MANAGEMENT_FIXED_LOT = 0,
   MONEY_MANAGEMENT_RISK_PERCENT = 1
};

enum ENUM_RISK_CAPITAL_BASE
{
   RISK_CAPITAL_BALANCE = 0,
   RISK_CAPITAL_EQUITY = 1
};

input string SnapshotChannel = "mtc-set-from-hq";
input ENUM_GATEWAY_MODE GatewayMode = GATEWAY_SHADOW;
input bool LiveArmed = false;
input bool SingleHostLiveAcknowledged = false;
input string TrustedSigningKeyId = "";
input ENUM_MONEY_MANAGEMENT_MODE MoneyManagementMode = MONEY_MANAGEMENT_FIXED_LOT;
input double FixedLot = 0.01;
input double RiskPercent = 1.0;
input ENUM_RISK_CAPITAL_BASE RiskCapitalBase = RISK_CAPITAL_EQUITY;
input double EstimatedCommissionPerLot = 0.0;
input bool CommissionFreeAccountConfirmed = false;
input int MagicNumber = 4186001;
input string ManagedMagicNumbers = "4186001";
input int PollIntervalSeconds = 1;
input int SnapshotIntervalSeconds = 5;
input int SnapshotBars = 240;
input int MaxCommandBytes = 8192;
input int MaxCommandTtlSeconds = 120;
input int MaxHeartbeatTtlSeconds = 60;
input int MaxClockSkewSeconds = 10;
input int MaxSpreadPoints = 30;
input int SlippagePoints = 3;
input string AllowedSymbols = "XAUUSD";
input string AllowedTimeframes = "M5,M15,M30,H1,H4,D1,W1,MN1";
input bool RequireHeartbeat = true;
input int MaxSnapshotAgeSeconds = 300;
input int MaxSignalDriftPoints = 100;
input int MaxQuoteAgeSeconds = 30;
input int MaxManagedOpenPositions = 1;
input double MaxManagedTotalLots = 0.10;
input int MaxTradesPerBrokerDay = 6;
input double MaxLossPerTradePercent = 1.0;
input double MaxDailyLossPercent = 3.0;
input double MaxManagedWeeklyLossPercent = 5.0;
input int MaxConsecutiveManagedLosses = 3;
input int ConsecutiveLossCooldownMinutes = 240;
input double MaxAccountEquityDrawdownPercent = 10.0;
input double MinRewardRiskRatio = 1.0;
input double MinProjectedMarginLevelPercent = 300.0;
input ENUM_POSITION_LIFECYCLE_MODE PositionLifecycleMode = LIFECYCLE_SLTP_ONLY;
input int MaxHoldingMinutes = 0;
input int SessionCloseHourBroker = 23;
input int SessionCloseMinuteBroker = 55;
input bool EnableRolloverEntryBlock = false;
input int RolloverStartHourBroker = 23;
input int RolloverEndHourBroker = 1;

string COMMAND_SCHEMA = "metafx-hq-mt4-command-v2";
string HEARTBEAT_SCHEMA = "metafx-hq-mt4-heartbeat-v1";
string SIGNED_ENVELOPE_SCHEMA = "metafx-hq-mt4-signed-envelope-v1";
string SIGNATURE_ALGORITHM = "HMAC-SHA256";
string ACK_SCHEMA = "metafx-hq-mt4-ack-v3";
string STATUS_SCHEMA = "metafx-hq-mt4-status-v5";
string SNAPSHOT_SCHEMA = "metafx-hq-mt4-snapshot-v1";
string EXECUTION_ATTEMPT_SCHEMA = "metafx-hq-mt5-execution-attempt-v1";
string EA_PROFILE = "special";
string EA_VERSION = "1.03";
const int ATOMIC_WRITE_MAX_ATTEMPTS = 3;
const int ATOMIC_WRITE_BACKOFF_MILLIS = 25;
const int LEGACY_BACKFILL_MAX_ACKS = 256;
const int PORTFOLIO_POLICY_PREFIX_HEX_LENGTH = 16;
const int PORTFOLIO_POLICY_MAX_EXPANDED_PATH_LENGTH = 259;
int g_last_snapshot_attempt_at = 0;
int g_last_snapshot_success_at = 0;
bool g_last_snapshot_write_ok = false;
int g_consecutive_atomic_write_failures = 0;
int g_last_atomic_write_error = 0;
int g_last_atomic_write_failure_at = 0;
string g_last_atomic_write_path = "";
int g_legacy_backfill_scanned = 0;
int g_legacy_backfill_recovered = 0;
int g_legacy_backfill_skipped = 0;
int g_legacy_backfill_ambiguous = 0;
int g_channel_lock_handle = INVALID_HANDLE;
int g_account_execution_lock_handle = INVALID_HANDLE;
int g_live_account_owner_handle = INVALID_HANDLE;
string g_live_account_owner_path = "";
string g_live_account_owner_digest = "";
int g_portfolio_policy_lease_handle = INVALID_HANDLE;
string g_portfolio_policy_lease_path = "";
string g_portfolio_policy_digest = "";
int g_portfolio_policy_lease_open_error = 0;
int g_portfolio_policy_lease_scan_error = 0;
int g_portfolio_policy_lease_expanded_path_length = 0;
uint g_last_tick_millis = 0;
int g_risk_cache_at = 0;
int g_cached_managed_positions = 0;
double g_cached_managed_lots = 0.0;
int g_cached_trades_today = 0;
double g_cached_managed_daily_pnl = 0.0;
double g_cached_managed_weekly_pnl = 0.0;
int g_cached_consecutive_losses = 0;
int g_cached_cooldown_until = 0;
double g_cached_account_drawdown_percent = 0.0;
double g_cached_margin_level_percent = 0.0;
bool g_cached_execution_guard_ready = false;
string g_cached_execution_guard_reason = "STARTING";
bool g_cached_history_telemetry_ready = false;
int g_last_outcome_refresh_at = 0;
bool g_ack_has_execution_evidence = false;
double g_ack_filled_price = 0.0;
double g_ack_filled_slippage_points = 0.0;
double g_ack_actual_stop_loss = 0.0;
double g_ack_actual_take_profit = 0.0;
int g_ack_actual_magic_number = 0;
string g_ack_actual_comment = "";
string g_ack_verification_status = "NOT_APPLICABLE";
string g_ack_execution_state = "NONE";
int g_ack_closed_at = 0;
double g_ack_closed_pnl = 0.0;
bool g_ack_has_closed_pnl = false;
bool g_crypto_self_test_ok = false;
string g_active_signing_key_id = "";
string g_trusted_signing_key_id = "";
bool g_signing_key_pinned = false;
string g_last_signature_verification_status = "NOT_CHECKED";
string g_init_warning_code = "";
bool g_ack_has_sizing_evidence = false;
double g_ack_reported_volume = 0.0;
string g_ack_position_sizing_mode = "";
double g_ack_risk_percent = 0.0;
string g_ack_risk_capital_base = "";
double g_ack_estimated_commission_per_lot = 0.0;
double g_ack_risk_capital_amount = 0.0;
double g_ack_estimated_risk_money = 0.0;

const int MAX_SAFE_SPREAD_POINTS = 10000;
const int MAX_SAFE_SLIPPAGE_POINTS = 1000;
const int MAX_SAFE_SIGNAL_DRIFT_POINTS = 10000;

struct CommandPayload
{
   string schema_version;
   string command_id;
   string idempotency_key;
   string channel_id;
   string mission_id;
   string council_decision_id;
   string owner_agent_id;
   string snapshot_id;
   int snapshot_observed_at;
   int bar_time;
   double reference_price;
   string action;
   string symbol;
   string timeframe;
   double stop_loss;
   double take_profit;
   int issued_at;
   int expires_at;
   string heartbeat_id;
   string signature_verification_status;
};


struct LegacyExecutedAck
{
   string command_id;
   string symbol;
   string action;
   string actual_comment;
   ulong ticket;
   int magic_number;
   int observed_at;
   double fixed_lot;
   double filled_price;
   double filled_slippage_points;
   double stop_loss;
   double take_profit;
};


struct ExecutionAttempt
{
   string stage;
   string account_binding_id;
   string stream_key;
   string signed_command_digest;
   string broker_comment;
   string order_id;
   string deal_id;
   string request_id;
   string retcode;
   string retcode_external;
   bool api_accepted;
   string api_error;
   double expected_volume;
   string position_sizing_mode;
   double risk_percent;
   string risk_capital_base;
   double estimated_commission_per_lot;
   double risk_capital_amount;
   double estimated_risk_money;
};



bool IsDemo()
{
   ENUM_ACCOUNT_TRADE_MODE mode =
      (ENUM_ACCOUNT_TRADE_MODE)AccountInfoInteger(ACCOUNT_TRADE_MODE);
   return mode != ACCOUNT_TRADE_MODE_REAL;
}


bool IsConnected()
{
   return TerminalInfoInteger(TERMINAL_CONNECTED) != 0;
}


bool IsExpertEnabled()
{
   return TerminalInfoInteger(TERMINAL_TRADE_ALLOWED) != 0 &&
      MQLInfoInteger(MQL_TRADE_ALLOWED) != 0 &&
      AccountInfoInteger(ACCOUNT_TRADE_ALLOWED) != 0 &&
      AccountInfoInteger(ACCOUNT_TRADE_EXPERT) != 0;
}


bool IsTradeAllowed()
{
   return IsExpertEnabled();
}


double AccountBalance()
{
   return AccountInfoDouble(ACCOUNT_BALANCE);
}


double AccountEquity()
{
   return AccountInfoDouble(ACCOUNT_EQUITY);
}


double AccountMargin()
{
   return AccountInfoDouble(ACCOUNT_MARGIN);
}


double AccountFreeMargin()
{
   return AccountInfoDouble(ACCOUNT_MARGIN_FREE);
}


string AccountCurrency()
{
   return AccountInfoString(ACCOUNT_CURRENCY);
}


string Trimmed(string value)
{
   StringTrimLeft(value);
   StringTrimRight(value);
   return value;
}


string Uppercase(string value)
{
   StringToUpper(value);
   return value;
}


string Lowercase(string value)
{
   StringToLower(value);
   return value;
}


string NormalizeSigningKeyId(const string value)
{
   return Lowercase(Trimmed(value));
}


bool IsWhitespace(const string value)
{
   return value == " " || value == "\t" || value == "\r" || value == "\n";
}


void SkipWhitespace(const string text, int &position)
{
   int length = StringLen(text);
   while(position < length && IsWhitespace(StringSubstr(text, position, 1)))
      position++;
}


bool IsSafeIdentifier(const string value)
{
   int length = StringLen(value);
   if(length < 1 || length > 120)
      return false;
   for(int index = 0; index < length; index++)
   {
      int code = StringGetCharacter(value, index);
      bool allowed =
         (code >= 'a' && code <= 'z') ||
         (code >= 'A' && code <= 'Z') ||
         (code >= '0' && code <= '9') ||
         code == '-' ||
         code == '_';
      if(!allowed)
         return false;
   }
   return true;
}


bool IsLowerHexIdentifierPart(
   const string value,
   const int offset,
   const int expected_length
)
{
   if(offset < 0 || expected_length < 1 ||
      StringLen(value) != offset + expected_length)
      return false;
   for(int index = offset; index < StringLen(value); index++)
   {
      int code = StringGetCharacter(value, index);
      bool allowed =
         (code >= '0' && code <= '9') ||
         (code >= 'a' && code <= 'f');
      if(!allowed)
         return false;
   }
   return true;
}


bool IsCommandIdentifier(const string value)
{
   return StringSubstr(value, 0, 4) == "cmd-" &&
      IsLowerHexIdentifierPart(value, 4, 24);
}


bool IsIdempotencyIdentifier(const string value)
{
   return StringSubstr(value, 0, 5) == "idem-" &&
      IsLowerHexIdentifierPart(value, 5, 32);
}


bool IsHeartbeatIdentifier(const string value)
{
   return StringSubstr(value, 0, 3) == "hb-" &&
      IsLowerHexIdentifierPart(value, 3, 24);
}


bool IsSafeChannel(const string value)
{
   return StringLen(value) >= 5 &&
          StringSubstr(value, 0, 4) == "mtc-" &&
          IsSafeIdentifier(value);
}


bool IsSha256Hex(const string value)
{
   if(StringLen(value) != 64)
      return false;
   for(int index = 0; index < 64; index++)
   {
      int code = StringGetCharacter(value, index);
      bool allowed =
         (code >= '0' && code <= '9') ||
         (code >= 'a' && code <= 'f');
      if(!allowed)
         return false;
   }
   return true;
}


bool IsIntegerToken(const string value)
{
   int length = StringLen(value);
   if(length < 1)
      return false;
   int index = 0;
   string first = StringSubstr(value, 0, 1);
   if(first == "-" || first == "+")
      index++;
   if(index >= length)
      return false;
   for(; index < length; index++)
   {
      int code = StringGetCharacter(value, index);
      if(code < '0' || code > '9')
         return false;
   }
   return true;
}


bool IsDecimalToken(const string value)
{
   int length = StringLen(value);
   if(length < 1)
      return false;
   int index = 0;
   int digit_count = 0;
   int dot_count = 0;
   string first = StringSubstr(value, 0, 1);
   if(first == "-" || first == "+")
      index++;
   for(; index < length; index++)
   {
      int code = StringGetCharacter(value, index);
      if(code >= '0' && code <= '9')
      {
         digit_count++;
         continue;
      }
      if(code == '.' && dot_count == 0)
      {
         dot_count++;
         continue;
      }
      return false;
   }
   return digit_count > 0;
}


bool ParseQuotedString(
   const string text,
   int &position,
   string &value,
   string &reason
)
{
   int length = StringLen(text);
   if(position >= length || StringSubstr(text, position, 1) != "\"")
   {
      reason = "JSON_STRING_EXPECTED";
      return false;
   }
   position++;
   value = "";
   while(position < length)
   {
      string current = StringSubstr(text, position, 1);
      if(current == "\"")
      {
         position++;
         return true;
      }
      if(current == "\\")
      {
         reason = "JSON_ESCAPES_NOT_SUPPORTED";
         return false;
      }
      if(StringGetCharacter(text, position) < 32)
      {
         reason = "JSON_CONTROL_CHARACTER";
         return false;
      }
      value += current;
      position++;
   }
   reason = "JSON_UNTERMINATED_STRING";
   return false;
}


int FindKey(string &keys[], const string key)
{
   for(int index = 0; index < ArraySize(keys); index++)
   {
      if(keys[index] == key)
         return index;
   }
   return -1;
}


bool ParseFlatJson(
   const string text,
   string &keys[],
   string &values[],
   int &quoted[],
   string &reason
)
{
   ArrayResize(keys, 0);
   ArrayResize(values, 0);
   ArrayResize(quoted, 0);
   int position = 0;
   int length = StringLen(text);
   SkipWhitespace(text, position);
   if(position >= length || StringSubstr(text, position, 1) != "{")
   {
      reason = "JSON_OBJECT_EXPECTED";
      return false;
   }
   position++;
   SkipWhitespace(text, position);
   if(position < length && StringSubstr(text, position, 1) == "}")
   {
      position++;
      SkipWhitespace(text, position);
      if(position != length)
      {
         reason = "JSON_TRAILING_DATA";
         return false;
      }
      return true;
   }

   while(position < length)
   {
      string key = "";
      if(!ParseQuotedString(text, position, key, reason))
         return false;
      if(FindKey(keys, key) >= 0)
      {
         reason = "JSON_DUPLICATE_KEY_" + key;
         return false;
      }
      SkipWhitespace(text, position);
      if(position >= length || StringSubstr(text, position, 1) != ":")
      {
         reason = "JSON_COLON_EXPECTED";
         return false;
      }
      position++;
      SkipWhitespace(text, position);
      if(position >= length)
      {
         reason = "JSON_VALUE_EXPECTED";
         return false;
      }

      string value = "";
      int is_quoted = 0;
      if(StringSubstr(text, position, 1) == "\"")
      {
         is_quoted = 1;
         if(!ParseQuotedString(text, position, value, reason))
            return false;
      }
      else
      {
         int start = position;
         while(position < length)
         {
            string current = StringSubstr(text, position, 1);
            if(current == "," || current == "}")
               break;
            if(current == "{" || current == "[")
            {
               reason = "JSON_NESTED_VALUES_NOT_ALLOWED";
               return false;
            }
            position++;
         }
         value = Trimmed(StringSubstr(text, start, position - start));
         if(StringLen(value) == 0)
         {
            reason = "JSON_VALUE_EXPECTED";
            return false;
         }
      }

      int size = ArraySize(keys);
      ArrayResize(keys, size + 1);
      ArrayResize(values, size + 1);
      ArrayResize(quoted, size + 1);
      keys[size] = key;
      values[size] = value;
      quoted[size] = is_quoted;

      SkipWhitespace(text, position);
      if(position >= length)
      {
         reason = "JSON_OBJECT_NOT_CLOSED";
         return false;
      }
      string delimiter = StringSubstr(text, position, 1);
      if(delimiter == "}")
      {
         position++;
         SkipWhitespace(text, position);
         if(position != length)
         {
            reason = "JSON_TRAILING_DATA";
            return false;
         }
         return true;
      }
      if(delimiter != ",")
      {
         reason = "JSON_COMMA_EXPECTED";
         return false;
      }
      position++;
      SkipWhitespace(text, position);
   }

   reason = "JSON_OBJECT_NOT_CLOSED";
   return false;
}


bool IsForbiddenSizingKey(const string key)
{
   string normalized = Uppercase(key);
   return normalized == "LOT" ||
          normalized == "LOTS" ||
          normalized == "VOLUME" ||
          normalized == "FIXEDLOT" ||
          normalized == "RISK" ||
          normalized == "RISKPERCENT" ||
          normalized == "RISK_PERCENT" ||
          normalized == "POSITION_SIZING" ||
          normalized == "POSITIONSIZING" ||
          normalized == "MONEY_MANAGEMENT" ||
          normalized == "MONEYMANAGEMENT" ||
          normalized == "RISK_CAPITAL_BASE" ||
          normalized == "RISKCAPITALBASE";
}


bool IsAllowedCommandKey(const string key)
{
   return key == "schemaVersion" ||
          key == "commandId" ||
          key == "idempotencyKey" ||
          key == "channelId" ||
           key == "missionId" ||
           key == "councilDecisionId" ||
           key == "ownerAgentId" ||
           key == "snapshotId" ||
           key == "snapshotObservedAt" ||
           key == "barTime" ||
           key == "referencePrice" ||
           key == "action" ||
          key == "symbol" ||
          key == "timeframe" ||
          key == "stopLoss" ||
          key == "takeProfit" ||
          key == "issuedAt" ||
          key == "expiresAt" ||
          key == "heartbeatId";
}


bool ReadRequiredString(
   string &keys[],
   string &values[],
   int &quoted[],
   const string key,
   string &value,
   string &reason
)
{
   int index = FindKey(keys, key);
   if(index < 0)
   {
      reason = "MISSING_" + key;
      return false;
   }
   if(quoted[index] != 1)
   {
      reason = "STRING_REQUIRED_" + key;
      return false;
   }
   value = values[index];
   if(StringLen(value) == 0)
   {
      reason = "EMPTY_" + key;
      return false;
   }
   return true;
}


void ReadOptionalString(
   string &keys[],
   string &values[],
   int &quoted[],
   const string key,
   string &value
)
{
   int index = FindKey(keys, key);
   value = "";
   if(index >= 0 && quoted[index] == 1)
      value = values[index];
}


bool ReadRequiredInteger(
   string &keys[],
   string &values[],
   int &quoted[],
   const string key,
   int &value,
   string &reason
)
{
   int index = FindKey(keys, key);
   if(index < 0)
   {
      reason = "MISSING_" + key;
      return false;
   }
   if(quoted[index] != 0 || !IsIntegerToken(values[index]))
   {
      reason = "INTEGER_REQUIRED_" + key;
      return false;
   }
   long parsed = StringToInteger(values[index]);
   if(parsed < 0 || parsed > 2147483647)
   {
      reason = "INTEGER_RANGE_" + key;
      return false;
   }
   value = (int)parsed;
   return true;
}


bool ReadRequiredDouble(
   string &keys[],
   string &values[],
   int &quoted[],
   const string key,
   double &value,
   string &reason
)
{
   int index = FindKey(keys, key);
   if(index < 0)
   {
      reason = "MISSING_" + key;
      return false;
   }
   if(quoted[index] != 0 || !IsDecimalToken(values[index]))
   {
      reason = "NUMBER_REQUIRED_" + key;
      return false;
   }
   value = StringToDouble(values[index]);
   if(!MathIsValidNumber(value))
   {
      reason = "INVALID_NUMBER_" + key;
      return false;
   }
   return true;
}


bool ReadRequiredBoolean(
   string &keys[],
   string &values[],
   int &quoted[],
   const string key,
   bool &value,
   string &reason
)
{
   int index = FindKey(keys, key);
   if(index < 0)
   {
      reason = "MISSING_" + key;
      return false;
   }
   if(quoted[index] != 0 ||
      (values[index] != "true" && values[index] != "false"))
   {
      reason = "BOOLEAN_REQUIRED_" + key;
      return false;
   }
   value = values[index] == "true";
   return true;
}


bool IsUnsignedIntegerText(const string value)
{
   int length = StringLen(value);
   if(length < 1 || length > 20)
      return false;
   for(int index = 0; index < length; index++)
   {
      int character = StringGetCharacter(value, index);
      if(character < '0' || character > '9')
         return false;
   }
   return true;
}


bool IsSignedIntegerText(const string value)
{
   int length = StringLen(value);
   if(length < 1 || length > 20)
      return false;
   int start = StringSubstr(value, 0, 1) == "-" ? 1 : 0;
   if(start == length)
      return false;
   for(int index = start; index < length; index++)
   {
      int character = StringGetCharacter(value, index);
      if(character < '0' || character > '9')
         return false;
   }
   return true;
}


void ResetCommand(CommandPayload &command)
{
   command.schema_version = "";
   command.command_id = "";
   command.idempotency_key = "";
   command.channel_id = "";
   command.mission_id = "";
   command.council_decision_id = "";
   command.owner_agent_id = "";
   command.snapshot_id = "";
   command.snapshot_observed_at = 0;
   command.bar_time = 0;
   command.reference_price = 0.0;
   command.action = "";
   command.symbol = "";
   command.timeframe = "";
   command.stop_loss = 0.0;
   command.take_profit = 0.0;
   command.issued_at = 0;
   command.expires_at = 0;
   command.heartbeat_id = "";
   command.signature_verification_status = "NOT_CHECKED";
}


bool ParseCommandPayload(
   const string raw,
   CommandPayload &command,
   string &reason
)
{
   ResetCommand(command);
   string keys[];
   string values[];
   int quoted[];
   if(!ParseFlatJson(raw, keys, values, quoted, reason))
      return false;

   for(int index = 0; index < ArraySize(keys); index++)
   {
      if(IsForbiddenSizingKey(keys[index]))
      {
         reason = "FORBIDDEN_AI_SIZE_FIELD_" + keys[index];
         return false;
      }
      if(!IsAllowedCommandKey(keys[index]))
      {
         reason = "UNKNOWN_FIELD_" + keys[index];
         return false;
      }
   }

   if(!ReadRequiredString(keys, values, quoted, "schemaVersion", command.schema_version, reason))
      return false;
   if(!ReadRequiredString(keys, values, quoted, "commandId", command.command_id, reason))
      return false;
   if(!ReadRequiredString(keys, values, quoted, "idempotencyKey", command.idempotency_key, reason))
      return false;
   if(!ReadRequiredString(keys, values, quoted, "channelId", command.channel_id, reason))
      return false;
   ReadOptionalString(keys, values, quoted, "missionId", command.mission_id);
   ReadOptionalString(keys, values, quoted, "councilDecisionId", command.council_decision_id);
   ReadOptionalString(keys, values, quoted, "ownerAgentId", command.owner_agent_id);
   if(!ReadRequiredString(keys, values, quoted, "snapshotId", command.snapshot_id, reason))
      return false;
   if(!ReadRequiredInteger(keys, values, quoted, "snapshotObservedAt", command.snapshot_observed_at, reason))
      return false;
   if(!ReadRequiredInteger(keys, values, quoted, "barTime", command.bar_time, reason))
      return false;
   if(!ReadRequiredDouble(keys, values, quoted, "referencePrice", command.reference_price, reason))
      return false;
   if(!ReadRequiredString(keys, values, quoted, "action", command.action, reason))
      return false;
   if(!ReadRequiredString(keys, values, quoted, "symbol", command.symbol, reason))
      return false;
   if(!ReadRequiredString(keys, values, quoted, "timeframe", command.timeframe, reason))
      return false;
   if(!ReadRequiredDouble(keys, values, quoted, "stopLoss", command.stop_loss, reason))
      return false;
   if(!ReadRequiredDouble(keys, values, quoted, "takeProfit", command.take_profit, reason))
      return false;
   if(!ReadRequiredInteger(keys, values, quoted, "issuedAt", command.issued_at, reason))
      return false;
   if(!ReadRequiredInteger(keys, values, quoted, "expiresAt", command.expires_at, reason))
      return false;
   if(!ReadRequiredString(keys, values, quoted, "heartbeatId", command.heartbeat_id, reason))
      return false;

   command.action = Uppercase(command.action);
   command.symbol = Uppercase(command.symbol);
   command.timeframe = Uppercase(command.timeframe);
   return true;
}


string BasePath()
{
   return "MetafxHQ\\" + SnapshotChannel + "\\trade-gateway";
}


string CommandPath()
{
   return BasePath() + "\\command.json";
}


string HeartbeatPath()
{
   return BasePath() + "\\heartbeat.json";
}


string StatusPath()
{
   return BasePath() + "\\status.json";
}


string CapabilitiesPath()
{
   return BasePath() + "\\capabilities.json";
}


string InitStatusPath()
{
   return BasePath() + "\\init-status.json";
}


string SigningKeysPath()
{
   return BasePath() + "\\keys";
}


string ActiveSigningKeyPath()
{
   return SigningKeysPath() + "\\active-key.id";
}


string SigningKeyPath(const string key_id)
{
   return SigningKeysPath() + "\\" + key_id + ".key";
}


string SnapshotPath()
{
   return "MetafxHQ\\" + SnapshotChannel + "\\snapshot.json";
}


string KillMarkerPath()
{
   return BasePath() + "\\kill.switch";
}


string AckPath(const string command_id)
{
   return BasePath() + "\\acks\\" + command_id + ".json";
}


string CommandLedgerPath(const string command_id)
{
   return BasePath() + "\\processed\\commands\\" + command_id + ".json";
}


string IdempotencyLedgerPath(const string idempotency_key)
{
   return BasePath() + "\\processed\\idempotency\\" + idempotency_key + ".json";
}


string ExecutionAttemptPath(const string command_id)
{
   return BasePath() + "\\state\\execution-attempt-" + command_id + ".json";
}


string LegacyLastOrderBarPath()
{
   return BasePath() + "\\state\\last-order-bar.txt";
}


string LastOrderBarPath()
{
   // The backend bar claim is channel + symbol + timeframe + bar time.  Keep
   // the EA crash-recovery claim at exactly the same scope so moving this EA
   // to another allowed chart never causes a false cross-stream duplicate and
   // never releases the original stream's claim.
   return BasePath() + "\\state\\last-order-bar-" +
      Uppercase(Symbol()) + "-" + CurrentTimeframeName() + ".txt";
}


string ChannelLockPath()
{
   return BasePath() + "\\state\\channel-owner.lock";
}


bool AccountIdentityDigest(string &digest_hex)
{
   digest_hex = "";
   long account_login = AccountInfoInteger(ACCOUNT_LOGIN);
   string server = Uppercase(Trimmed(AccountInfoString(ACCOUNT_SERVER)));
   if(account_login <= 0 || StringLen(server) < 1)
      return false;
   // Keep MT4 as the legacy cross-platform lock namespace. Changing only the
   // MT5 side would let MT4 and MT5 execute concurrently on the same account.
   string identity = "MT4|" + StringFormat("%I64d", account_login) +
      "|" + server;
   uchar identity_bytes[];
   uchar digest[];
   if(!StringToAsciiBytes(identity, identity_bytes) ||
      !Sha256Bytes(identity_bytes, digest))
   {
      WipeBytes(identity_bytes);
      WipeBytes(digest);
      return false;
   }
   digest_hex = BytesToHex(digest);
   WipeBytes(identity_bytes);
   WipeBytes(digest);
   return IsSha256Hex(digest_hex);
}


bool ProtocolAccountBindingId(string &digest_hex)
{
   digest_hex = "";
   long account_login = AccountInfoInteger(ACCOUNT_LOGIN);
   string server = Uppercase(Trimmed(AccountInfoString(ACCOUNT_SERVER)));
   if(account_login <= 0 || StringLen(server) < 1)
      return false;
   // This digest is an opaque wire binding only.  Keep the separate legacy
   // MT4 account digest above for the shared same-machine execution lock.
   string identity = "MT5|" + StringFormat("%I64d", account_login) +
      "|" + server;
   uchar identity_bytes[];
   uchar digest[];
   if(!StringToAsciiBytes(identity, identity_bytes) ||
      !Sha256Bytes(identity_bytes, digest))
   {
      WipeBytes(identity_bytes);
      WipeBytes(digest);
      return false;
   }
   digest_hex = BytesToHex(digest);
   WipeBytes(identity_bytes);
   WipeBytes(digest);
   return IsSha256Hex(digest_hex);
}


bool ProtocolStreamKey(
   const CommandPayload &command,
   string &digest_hex
)
{
   digest_hex = "";
   string identity = command.channel_id + "\n" +
      Uppercase(command.symbol) + "\n" +
      Uppercase(command.timeframe);
   uchar identity_bytes[];
   uchar digest[];
   if(!StringToAsciiBytes(identity, identity_bytes) ||
      !Sha256Bytes(identity_bytes, digest))
   {
      WipeBytes(identity_bytes);
      WipeBytes(digest);
      return false;
   }
   digest_hex = BytesToHex(digest);
   WipeBytes(identity_bytes);
   WipeBytes(digest);
   return IsSha256Hex(digest_hex);
}


bool SignedCommandDigest(
   const string signed_raw,
   string &digest_hex
)
{
   digest_hex = "";
   uchar command_bytes[];
   uchar digest[];
   if(!StringToAsciiBytes(signed_raw, command_bytes) ||
      !Sha256Bytes(command_bytes, digest))
   {
      WipeBytes(command_bytes);
      WipeBytes(digest);
      return false;
   }
   digest_hex = BytesToHex(digest);
   WipeBytes(command_bytes);
   WipeBytes(digest);
   return IsSha256Hex(digest_hex);
}


bool AccountExecutionLockPath(string &path)
{
   path = "";
   string account_digest = "";
   if(!AccountIdentityDigest(account_digest))
      return false;
   path = "MetafxHQ\\locks\\account-execution-" + account_digest + ".lock";
   return true;
}


bool LiveAccountOwnerLockPath(string &path, string &account_digest)
{
   path = "";
   account_digest = "";
   if(!AccountIdentityDigest(account_digest))
      return false;
   path = "MetafxHQ\\locks\\account-live-owner-" +
      account_digest + ".lock";
   return true;
}


bool LiveAccountOwnerLockReady(string &reason)
{
   if(GatewayMode != GATEWAY_LIVE)
   {
      reason = "NOT_REQUIRED";
      return true;
   }
   if(g_live_account_owner_handle == INVALID_HANDLE)
   {
      reason = "LIVE_ACCOUNT_OWNER_LOCK_UNAVAILABLE";
      return false;
   }
   string expected_path = "";
   string current_digest = "";
   if(!LiveAccountOwnerLockPath(expected_path, current_digest))
   {
      reason = "ACCOUNT_IDENTITY_BINDING_UNAVAILABLE";
      return false;
   }
   if(current_digest != g_live_account_owner_digest ||
      expected_path != g_live_account_owner_path)
   {
      reason = "LIVE_ACCOUNT_BINDING_CHANGED";
      return false;
   }
   reason = "READY";
   return true;
}


bool AcquireLiveAccountOwnerLock(string &reason)
{
   if(GatewayMode != GATEWAY_LIVE)
   {
      reason = "NOT_REQUIRED";
      return true;
   }
   if(g_live_account_owner_handle != INVALID_HANDLE)
      return LiveAccountOwnerLockReady(reason);

   string path = "";
   string account_digest = "";
   if(!LiveAccountOwnerLockPath(path, account_digest))
   {
      reason = "ACCOUNT_IDENTITY_BINDING_UNAVAILABLE";
      return false;
   }
   ResetLastError();
   int handle = FileOpen(
      path,
      FILE_READ | FILE_WRITE | FILE_BIN | FILE_ANSI | FILE_COMMON |
      FILE_SHARE_READ
   );
   if(handle == INVALID_HANDLE)
   {
      reason = "LIVE_ACCOUNT_OWNER_LOCK_UNAVAILABLE";
      return false;
   }
   FileSeek(handle, 0, SEEK_SET);
   FileWriteString(
      handle,
      "MetafxHQTradeGateway|MT5|LIVE|" + SnapshotChannel + "|" +
      account_digest + "|" + IntegerToString(NowUtc())
   );
   FileFlush(handle);
   g_live_account_owner_handle = handle;
   g_live_account_owner_path = path;
   g_live_account_owner_digest = account_digest;
   reason = "READY";
   return true;
}


void ReleaseLiveAccountOwnerLock()
{
   if(g_live_account_owner_handle != INVALID_HANDLE)
      FileClose(g_live_account_owner_handle);
   g_live_account_owner_handle = INVALID_HANDLE;
   g_live_account_owner_path = "";
   g_live_account_owner_digest = "";
}


bool AccountPortfolioPolicyDirectoryPath(string &path)
{
   path = "";
   string account_digest = "";
   if(!AccountIdentityDigest(account_digest))
      return false;
   path = "MetafxHQ\\account-policies\\" + account_digest;
   return true;
}


bool AccountPortfolioPolicyPath(string &path)
{
   string directory = "";
   if(!AccountPortfolioPolicyDirectoryPath(directory))
      return false;
   path = directory + "\\portfolio-policy-v1.txt";
   return true;
}


string DailyLossLockPath()
{
   return BasePath() + "\\state\\daily-loss-" +
      TimeToString(BrokerDayStart(), TIME_DATE) + ".lock";
}


datetime BrokerWeekStart()
{
   datetime day_start = BrokerDayStart();
   MqlDateTime parts;
   if(!TimeToStruct(day_start, parts))
      return day_start;
   int days_since_monday = (parts.day_of_week + 6) % 7;
   return day_start - days_since_monday * 86400;
}


string WeeklyLossLockPath()
{
   return BasePath() + "\\state\\weekly-loss-" +
      IntegerToString((int)BrokerWeekStart()) + ".lock";
}


string OutcomePath(const string command_id)
{
   return BasePath() + "\\outcomes\\" + command_id + ".json";
}


string TicketMapPath(const ulong ticket)
{
   return BasePath() + "\\tickets\\" + StringFormat("%I64u", ticket) + ".json";
}


string LifecycleAttemptPath(const ulong ticket)
{
   return BasePath() + "\\state\\lifecycle-close-" +
      StringFormat("%I64u", ticket) + ".lock";
}


string AuditPath()
{
   return BasePath() + "\\audit\\events.jsonl";
}


void EnsureFolder(const string folder)
{
   ResetLastError();
   FolderCreate(folder, FILE_COMMON);
   ResetLastError();
}


void EnsureFolders()
{
   EnsureFolder("MetafxHQ");
   EnsureFolder("MetafxHQ\\locks");
   EnsureFolder("MetafxHQ\\account-policies");
   string account_policy_directory = "";
   if(AccountPortfolioPolicyDirectoryPath(account_policy_directory))
      EnsureFolder(account_policy_directory);
   EnsureFolder("MetafxHQ\\" + SnapshotChannel);
   EnsureFolder(BasePath());
   EnsureFolder(BasePath() + "\\acks");
   EnsureFolder(BasePath() + "\\processed");
   EnsureFolder(BasePath() + "\\processed\\commands");
   EnsureFolder(BasePath() + "\\processed\\idempotency");
   EnsureFolder(BasePath() + "\\state");
   EnsureFolder(BasePath() + "\\audit");
   EnsureFolder(BasePath() + "\\outcomes");
   EnsureFolder(BasePath() + "\\tickets");
   EnsureFolder(SigningKeysPath());
}


bool AcquireChannelLock()
{
   if(g_channel_lock_handle != INVALID_HANDLE)
      return true;
   ResetLastError();
   g_channel_lock_handle = FileOpen(
      ChannelLockPath(),
      FILE_READ | FILE_WRITE | FILE_BIN | FILE_ANSI | FILE_COMMON |
      FILE_SHARE_READ
   );
   if(g_channel_lock_handle == INVALID_HANDLE)
      return false;
   FileSeek(g_channel_lock_handle, 0, SEEK_SET);
   FileWriteString(
      g_channel_lock_handle,
      "MetafxHQTradeGateway|" + SnapshotChannel + "|" +
      IntegerToString(NowUtc())
   );
   FileFlush(g_channel_lock_handle);
   return true;
}


void ReleaseChannelLock()
{
   if(g_channel_lock_handle == INVALID_HANDLE)
      return;
   FileClose(g_channel_lock_handle);
   g_channel_lock_handle = INVALID_HANDLE;
}


bool ReadCommonText(
   const string path,
   int maximum_bytes,
   string &value
)
{
   value = "";
   ResetLastError();
   int handle = FileOpen(
      path,
      FILE_READ | FILE_BIN | FILE_ANSI | FILE_COMMON |
      FILE_SHARE_READ | FILE_SHARE_WRITE
   );
   if(handle == INVALID_HANDLE)
      return false;
   int size = (int)FileSize(handle);
   if(size <= 0 || size > maximum_bytes)
   {
      FileClose(handle);
      return false;
   }
   value = FileReadString(handle, size);
   FileClose(handle);
   return StringLen(value) > 0;
}


bool IsSigningKeyId(const string value)
{
   return StringLen(value) == 67 &&
      StringSubstr(value, 0, 3) == "hk-" &&
      IsSha256Hex(StringSubstr(value, 3));
}


int HexNibble(const int code)
{
   if(code >= '0' && code <= '9')
      return code - '0';
   if(code >= 'a' && code <= 'f')
      return code - 'a' + 10;
   return -1;
}


bool IsLowerHex(const string value)
{
   int length = StringLen(value);
   if(length < 1 || (length % 2) != 0)
      return false;
   for(int index = 0; index < length; index++)
   {
      if(HexNibble(StringGetCharacter(value, index)) < 0)
         return false;
   }
   return true;
}


bool HexToBytes(const string value, uchar &bytes[])
{
   ArrayResize(bytes, 0);
   if(!IsLowerHex(value))
      return false;
   int byte_count = StringLen(value) / 2;
   ArrayResize(bytes, byte_count);
   for(int index = 0; index < byte_count; index++)
   {
      int high = HexNibble(StringGetCharacter(value, index * 2));
      int low = HexNibble(StringGetCharacter(value, index * 2 + 1));
      if(high < 0 || low < 0)
      {
         ArrayResize(bytes, 0);
         return false;
      }
      bytes[index] = (uchar)(high * 16 + low);
   }
   return true;
}


string BytesToHex(const uchar &bytes[])
{
   string digits = "0123456789abcdef";
   string result = "";
   for(int index = 0; index < ArraySize(bytes); index++)
   {
      int value = (int)bytes[index];
      result += StringSubstr(digits, value / 16, 1);
      result += StringSubstr(digits, value % 16, 1);
   }
   return result;
}


void WipeBytes(uchar &bytes[])
{
   for(int index = 0; index < ArraySize(bytes); index++)
      bytes[index] = 0;
   ArrayResize(bytes, 0);
}


bool StringToAsciiBytes(const string value, uchar &bytes[])
{
   ArrayResize(bytes, 0);
   int length = StringLen(value);
   for(int index = 0; index < length; index++)
   {
      int code = StringGetCharacter(value, index);
      if(code < 0 || code > 127)
         return false;
   }
   if(length == 0)
      return true;
   int copied = StringToCharArray(value, bytes, 0, length, CP_UTF8);
   if(copied != length)
   {
      WipeBytes(bytes);
      return false;
   }
   ArrayResize(bytes, length);
   return true;
}


bool Sha256Bytes(const uchar &data[], uchar &digest[])
{
   uchar empty_key[];
   ArrayResize(empty_key, 0);
   ArrayResize(digest, 0);
   int size = CryptEncode(CRYPT_HASH_SHA256, data, empty_key, digest);
   WipeBytes(empty_key);
   if(size != 32 || ArraySize(digest) != 32)
   {
      WipeBytes(digest);
      return false;
   }
   return true;
}


void JoinBytes(
   const uchar &first[],
   const uchar &second[],
   uchar &joined[]
)
{
   int first_size = ArraySize(first);
   int second_size = ArraySize(second);
   ArrayResize(joined, first_size + second_size);
   for(int index = 0; index < first_size; index++)
      joined[index] = first[index];
   for(int offset = 0; offset < second_size; offset++)
      joined[first_size + offset] = second[offset];
}


bool HmacSha256(
   const uchar &secret_key[],
   const uchar &message[],
   uchar &digest[]
)
{
   uchar normalized_key[];
   if(ArraySize(secret_key) > 64)
   {
      if(!Sha256Bytes(secret_key, normalized_key))
         return false;
   }
   else
   {
      ArrayResize(normalized_key, ArraySize(secret_key));
      for(int source_index = 0; source_index < ArraySize(secret_key); source_index++)
         normalized_key[source_index] = secret_key[source_index];
   }

   uchar key_block[];
   uchar inner_pad[];
   uchar outer_pad[];
   ArrayResize(key_block, 64);
   ArrayResize(inner_pad, 64);
   ArrayResize(outer_pad, 64);
   ArrayInitialize(key_block, 0);
   for(int key_index = 0; key_index < ArraySize(normalized_key); key_index++)
      key_block[key_index] = normalized_key[key_index];
   for(int pad_index = 0; pad_index < 64; pad_index++)
   {
      inner_pad[pad_index] = (uchar)(key_block[pad_index] ^ 0x36);
      outer_pad[pad_index] = (uchar)(key_block[pad_index] ^ 0x5c);
   }

   uchar inner_input[];
   uchar inner_digest[];
   uchar outer_input[];
   JoinBytes(inner_pad, message, inner_input);
   if(!Sha256Bytes(inner_input, inner_digest))
   {
      WipeBytes(normalized_key);
      WipeBytes(key_block);
      WipeBytes(inner_pad);
      WipeBytes(outer_pad);
      WipeBytes(inner_input);
      return false;
   }
   JoinBytes(outer_pad, inner_digest, outer_input);
   bool ok = Sha256Bytes(outer_input, digest);
   WipeBytes(normalized_key);
   WipeBytes(key_block);
   WipeBytes(inner_pad);
   WipeBytes(outer_pad);
   WipeBytes(inner_input);
   WipeBytes(inner_digest);
   WipeBytes(outer_input);
   return ok;
}


bool ConstantTimeHexEquals(const string expected_hex, const string actual_hex)
{
   uchar expected[];
   uchar actual[];
   if(!HexToBytes(expected_hex, expected) || !HexToBytes(actual_hex, actual))
   {
      WipeBytes(expected);
      WipeBytes(actual);
      return false;
   }
   if(ArraySize(expected) != ArraySize(actual))
   {
      WipeBytes(expected);
      WipeBytes(actual);
      return false;
   }
   int difference = 0;
   for(int index = 0; index < ArraySize(expected); index++)
      difference |= ((int)expected[index] ^ (int)actual[index]);
   WipeBytes(expected);
   WipeBytes(actual);
   return difference == 0;
}


bool ReadSigningKey(
   const string key_id,
   uchar &secret_key[],
   string &reason
)
{
   ArrayResize(secret_key, 0);
   if(!IsSigningKeyId(key_id))
   {
      reason = "SIGNING_KEY_ID_INVALID";
      return false;
   }
   ResetLastError();
   int handle = FileOpen(
      SigningKeyPath(key_id),
      FILE_READ | FILE_BIN | FILE_COMMON | FILE_SHARE_READ
   );
   if(handle == INVALID_HANDLE)
   {
      reason = "SIGNING_KEY_FILE_MISSING";
      return false;
   }
   int size = (int)FileSize(handle);
   if(size != 32)
   {
      FileClose(handle);
      reason = "SIGNING_KEY_LENGTH_INVALID";
      return false;
   }
   ArrayResize(secret_key, 32);
   uint read_count = FileReadArray(handle, secret_key, 0, 32);
   FileClose(handle);
   if(read_count != 32)
   {
      WipeBytes(secret_key);
      reason = "SIGNING_KEY_READ_FAILED";
      return false;
   }
   uchar key_hash[];
   if(!Sha256Bytes(secret_key, key_hash))
   {
      WipeBytes(secret_key);
      reason = "SIGNING_KEY_HASH_FAILED";
      return false;
   }
   string derived_key_id = "hk-" + BytesToHex(key_hash);
   WipeBytes(key_hash);
   if(derived_key_id != key_id)
   {
      WipeBytes(secret_key);
      reason = "SIGNING_KEY_ID_HASH_MISMATCH";
      return false;
   }
   return true;
}


bool LoadActiveSigningKey(
   string &key_id,
   uchar &secret_key[],
   string &reason
)
{
   key_id = "";
   ArrayResize(secret_key, 0);
   g_active_signing_key_id = "";
   g_signing_key_pinned = false;
   if(!g_crypto_self_test_ok)
   {
      reason = "CRYPTO_SELF_TEST_FAILED";
      return false;
   }
   string pointer = "";
   if(!ReadCommonText(ActiveSigningKeyPath(), 128, pointer))
   {
      reason = "ACTIVE_SIGNING_KEY_POINTER_MISSING";
      return false;
   }
   key_id = Trimmed(pointer);
   if(!IsSigningKeyId(key_id))
   {
      reason = "ACTIVE_SIGNING_KEY_ID_INVALID";
      return false;
   }
   g_active_signing_key_id = key_id;
   bool explicit_pin_matches = StringLen(g_trusted_signing_key_id) > 0 &&
      g_trusted_signing_key_id == key_id;
   if(GatewayMode == GATEWAY_LIVE && StringLen(g_trusted_signing_key_id) == 0)
   {
      reason = "LIVE_SIGNING_KEY_PIN_REQUIRED";
      return false;
   }
   if(GatewayMode == GATEWAY_LIVE && !explicit_pin_matches)
   {
      reason = "LIVE_SIGNING_KEY_PIN_MISMATCH";
      return false;
   }
   if(!ReadSigningKey(key_id, secret_key, reason))
      return false;
   // Shadow/Demo may follow the backend-owned active pointer, but "pinned"
   // remains literal: true only for an explicit normalized signing-key pin.
   g_signing_key_pinned = explicit_pin_matches;
   return true;
}


bool RefreshSigningReadiness(string &reason)
{
   string key_id = "";
   uchar secret_key[];
   bool ready = LoadActiveSigningKey(key_id, secret_key, reason);
   WipeBytes(secret_key);
   return ready;
}


bool CryptoSelfTest()
{
   // Python-compatible integration vector: key bytes 00..1f and the exact
   // MT5 account-bound signed-envelope preimage used by the HQ local runner.
   uchar secret_key[];
   ArrayResize(secret_key, 32);
   for(int index = 0; index < 32; index++)
      secret_key[index] = (uchar)index;
   string key_id = "hk-630dcd2966c4336691125448bbb25b4ff412a49c732db2c8abc1b8581bd710dd";
   string payload_hex = "7b22736368656d6156657273696f6e223a226d65746166782d68712d6d74342d636f6d6d616e642d7632227d";
   string account_binding_id =
      "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
   string preimage = "METAFXHQ|MT5|COMMAND|HMAC-SHA256|V1\n" +
      key_id + "\nmtc-demo-01\n" + account_binding_id + "\n" +
      payload_hex;
   uchar message[];
   uchar digest[];
   bool ok = StringToAsciiBytes(preimage, message) &&
      HmacSha256(secret_key, message, digest) &&
      ConstantTimeHexEquals(
         "696a44edd69a0e1852096634ffae68737655c5aa4d12cb26c03039f72aa94753",
         BytesToHex(digest)
      );
   WipeBytes(secret_key);
   WipeBytes(message);
   WipeBytes(digest);
   return ok;
}


bool SignatureFailure(string &reason, const string reason_code)
{
   reason = reason_code;
   g_last_signature_verification_status = reason_code;
   return false;
}


bool VerifySignedEnvelope(
   const string raw,
   const string kind,
   string &inner_payload,
   string &reason
)
{
   inner_payload = "";
   string normalized_kind = Uppercase(kind);
   if(normalized_kind != "COMMAND" && normalized_kind != "HEARTBEAT")
      return SignatureFailure(reason, "SIGNED_ENVELOPE_KIND_INVALID");
   string keys[];
   string values[];
   int quoted[];
   string parse_reason = "";
   if(!ParseFlatJson(raw, keys, values, quoted, parse_reason))
      return SignatureFailure(reason, "SIGNED_ENVELOPE_" + parse_reason);
   if(ArraySize(keys) != 5)
      return SignatureFailure(reason, "SIGNED_ENVELOPE_FIELD_COUNT_INVALID");
   for(int index = 0; index < ArraySize(keys); index++)
   {
      if(keys[index] != "schemaVersion" &&
         keys[index] != "algorithm" &&
         keys[index] != "keyId" &&
         keys[index] != "payloadHex" &&
         keys[index] != "signatureHex")
         return SignatureFailure(reason, "SIGNED_ENVELOPE_UNKNOWN_FIELD");
   }

   string schema = "";
   string algorithm = "";
   string key_id = "";
   string payload_hex = "";
   string signature_hex = "";
   string field_reason = "";
   if(!ReadRequiredString(keys, values, quoted, "schemaVersion", schema, field_reason) ||
      !ReadRequiredString(keys, values, quoted, "algorithm", algorithm, field_reason) ||
      !ReadRequiredString(keys, values, quoted, "keyId", key_id, field_reason) ||
      !ReadRequiredString(keys, values, quoted, "payloadHex", payload_hex, field_reason) ||
      !ReadRequiredString(keys, values, quoted, "signatureHex", signature_hex, field_reason))
      return SignatureFailure(reason, "SIGNED_ENVELOPE_" + field_reason);
   if(schema != SIGNED_ENVELOPE_SCHEMA)
      return SignatureFailure(reason, "SIGNED_ENVELOPE_SCHEMA_MISMATCH");
   if(algorithm != SIGNATURE_ALGORITHM)
      return SignatureFailure(reason, "SIGNED_ENVELOPE_ALGORITHM_MISMATCH");
   if(!IsSigningKeyId(key_id))
      return SignatureFailure(reason, "SIGNED_ENVELOPE_KEY_ID_INVALID");
   if(!IsSha256Hex(signature_hex))
      return SignatureFailure(reason, "SIGNED_ENVELOPE_SIGNATURE_HEX_INVALID");
   if(!IsLowerHex(payload_hex) || StringLen(payload_hex) / 2 > MaxCommandBytes)
      return SignatureFailure(reason, "SIGNED_ENVELOPE_PAYLOAD_HEX_INVALID");

   string active_key_id = "";
   uchar secret_key[];
   string key_reason = "";
   if(!LoadActiveSigningKey(active_key_id, secret_key, key_reason))
      return SignatureFailure(reason, key_reason);
   if(key_id != active_key_id)
   {
      WipeBytes(secret_key);
      return SignatureFailure(reason, "SIGNED_ENVELOPE_KEY_NOT_ACTIVE");
   }

   string account_binding_id = "";
   if(!ProtocolAccountBindingId(account_binding_id))
   {
      WipeBytes(secret_key);
      return SignatureFailure(reason, "ACCOUNT_IDENTITY_BINDING_UNAVAILABLE");
   }
   string preimage = "METAFXHQ|MT5|" + normalized_kind +
      "|HMAC-SHA256|V1\n" + key_id + "\n" +
      SnapshotChannel + "\n" + account_binding_id + "\n" + payload_hex;
   uchar message[];
   uchar digest[];
   if(!StringToAsciiBytes(preimage, message) ||
      !HmacSha256(secret_key, message, digest))
   {
      WipeBytes(secret_key);
      WipeBytes(message);
      WipeBytes(digest);
      return SignatureFailure(reason, "SIGNED_ENVELOPE_HMAC_FAILED");
   }
   string calculated_signature = BytesToHex(digest);
   WipeBytes(secret_key);
   WipeBytes(message);
   WipeBytes(digest);
   if(!ConstantTimeHexEquals(signature_hex, calculated_signature))
      return SignatureFailure(reason, "SIGNED_ENVELOPE_SIGNATURE_MISMATCH");

   uchar payload_bytes[];
   if(!HexToBytes(payload_hex, payload_bytes))
      return SignatureFailure(reason, "SIGNED_ENVELOPE_PAYLOAD_DECODE_FAILED");
   for(int byte_index = 0; byte_index < ArraySize(payload_bytes); byte_index++)
   {
      int code = (int)payload_bytes[byte_index];
      if(code != 9 && code != 10 && code != 13 && (code < 32 || code > 126))
      {
         WipeBytes(payload_bytes);
         return SignatureFailure(reason, "SIGNED_ENVELOPE_PAYLOAD_NOT_ASCII_JSON");
      }
   }
   inner_payload = CharArrayToString(
      payload_bytes,
      0,
      ArraySize(payload_bytes),
      CP_UTF8
   );
   WipeBytes(payload_bytes);
   if(StringLen(inner_payload) < 2)
      return SignatureFailure(reason, "SIGNED_ENVELOPE_PAYLOAD_EMPTY");
   g_last_signature_verification_status = "VERIFIED";
   reason = "";
   return true;
}


bool SameCommandPayload(
   const CommandPayload &expected,
   const CommandPayload &actual
)
{
   return expected.schema_version == actual.schema_version &&
      expected.command_id == actual.command_id &&
      expected.idempotency_key == actual.idempotency_key &&
      expected.channel_id == actual.channel_id &&
      expected.mission_id == actual.mission_id &&
      expected.council_decision_id == actual.council_decision_id &&
      expected.owner_agent_id == actual.owner_agent_id &&
      expected.snapshot_id == actual.snapshot_id &&
      expected.snapshot_observed_at == actual.snapshot_observed_at &&
      expected.bar_time == actual.bar_time &&
      expected.reference_price == actual.reference_price &&
      expected.action == actual.action &&
      expected.symbol == actual.symbol &&
      expected.timeframe == actual.timeframe &&
      expected.stop_loss == actual.stop_loss &&
      expected.take_profit == actual.take_profit &&
      expected.issued_at == actual.issued_at &&
      expected.expires_at == actual.expires_at &&
      expected.heartbeat_id == actual.heartbeat_id;
}


bool ParseCommand(
   const string signed_raw,
   CommandPayload &command,
   string &reason
)
{
   ResetCommand(command);
   string inner_payload = "";
   if(!VerifySignedEnvelope(
      signed_raw,
      "COMMAND",
      inner_payload,
      reason
   ))
      return false;
   if(!ParseCommandPayload(inner_payload, command, reason))
   {
      reason = "SIGNED_COMMAND_PAYLOAD_" + reason;
      command.signature_verification_status = "VERIFIED";
      return false;
   }
   command.signature_verification_status = "VERIFIED";
   return true;
}


bool ReverifyCommandEnvelope(
   const string signed_raw,
   const CommandPayload &expected,
   string &reason
)
{
   CommandPayload actual;
   if(!ParseCommand(signed_raw, actual, reason))
      return false;
   if(!SameCommandPayload(expected, actual))
      return SignatureFailure(reason, "SIGNED_COMMAND_REVERIFY_MISMATCH");
   return true;
}


bool TryWriteCommonTextAtomic(
   const string final_path,
   const string temporary_path,
   const string value,
   int &error_code
)
{
   error_code = 0;
   ResetLastError();
   int handle = FileOpen(
      temporary_path,
      FILE_WRITE | FILE_BIN | FILE_ANSI | FILE_COMMON
   );
   if(handle == INVALID_HANDLE)
   {
      error_code = GetLastError();
      return false;
   }
   ResetLastError();
   uint written = FileWriteString(handle, value);
   int write_error = GetLastError();
   FileFlush(handle);
   FileClose(handle);
   if((int)written != StringLen(value))
   {
      // GetLastError can legitimately remain zero on a short binary write;
      // use -1 as an explicit local sentinel instead of inventing an MT4
      // runtime error code.
      error_code = write_error > 0 ? write_error : -1;
      return false;
   }
   ResetLastError();
   if(!FileMove(
      temporary_path,
      FILE_COMMON,
      final_path,
      FILE_COMMON | FILE_REWRITE
   ))
   {
      error_code = GetLastError();
      return false;
   }
   return true;
}


bool AcquireAccountExecutionLock()
{
   if(g_account_execution_lock_handle != INVALID_HANDLE)
      return true;
   string path = "";
   if(!AccountExecutionLockPath(path))
      return false;
   ResetLastError();
   g_account_execution_lock_handle = FileOpen(
      path,
      FILE_READ | FILE_WRITE | FILE_BIN | FILE_ANSI | FILE_COMMON |
      FILE_SHARE_READ
   );
   if(g_account_execution_lock_handle == INVALID_HANDLE)
      return false;
   FileSeek(g_account_execution_lock_handle, 0, SEEK_SET);
   FileWriteString(
      g_account_execution_lock_handle,
      "MetafxHQTradeGateway|" + SnapshotChannel + "|" +
      Uppercase(Symbol()) + "|" + CurrentTimeframeName() + "|" +
      IntegerToString(NowUtc())
   );
   FileFlush(g_account_execution_lock_handle);
   return true;
}


void ReleaseAccountExecutionLock()
{
   if(g_account_execution_lock_handle == INVALID_HANDLE)
      return;
   FileClose(g_account_execution_lock_handle);
   g_account_execution_lock_handle = INVALID_HANDLE;
}


bool WriteCommonTextAtomicWithTemporary(
   const string final_path,
   const string temporary_path,
   const string value
)
{
   int last_error = 0;
   for(int attempt = 1; attempt <= ATOMIC_WRITE_MAX_ATTEMPTS; attempt++)
   {
      if(TryWriteCommonTextAtomic(
         final_path,
         temporary_path,
         value,
         last_error
      ))
      {
         g_consecutive_atomic_write_failures = 0;
         return true;
      }
      if(attempt < ATOMIC_WRITE_MAX_ATTEMPTS)
         Sleep(ATOMIC_WRITE_BACKOFF_MILLIS * attempt);
   }
   g_consecutive_atomic_write_failures++;
   g_last_atomic_write_error = last_error;
   g_last_atomic_write_failure_at = NowUtc();
   g_last_atomic_write_path = final_path;
   Print(
      "MetafxHQ: Atomic write failed after ",
      IntegerToString(ATOMIC_WRITE_MAX_ATTEMPTS),
      " attempts; path=", final_path,
      " GetLastError=", IntegerToString(last_error),
      " consecutiveFailures=",
      IntegerToString(g_consecutive_atomic_write_failures)
   );
   return false;
}


bool WriteCommonTextAtomic(
   const string final_path,
   const string value
)
{
   return WriteCommonTextAtomicWithTemporary(
      final_path,
      final_path + ".tmp",
      value
   );
}


bool AppendAudit(const string json_line)
{
   ResetLastError();
   int handle = FileOpen(
      AuditPath(),
      FILE_READ | FILE_WRITE | FILE_TXT | FILE_ANSI | FILE_COMMON |
      FILE_SHARE_READ
   );
   if(handle == INVALID_HANDLE)
      return false;
   FileSeek(handle, 0, SEEK_END);
   FileWriteString(handle, json_line + "\r\n");
   FileFlush(handle);
   FileClose(handle);
   return true;
}


string JsonEscape(const string value)
{
   string result = "";
   int length = StringLen(value);
   for(int index = 0; index < length; index++)
   {
      string current = StringSubstr(value, index, 1);
      if(current == "\\")
         result += "\\\\";
      else if(current == "\"")
         result += "\\\"";
      else if(current == "\r")
         result += "\\r";
      else if(current == "\n")
         result += "\\n";
      else if(current == "\t")
         result += "\\t";
      else
         result += current;
   }
   return result;
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


bool Sha256TextHex(const string value, string &digest_hex)
{
   digest_hex = "";
   uchar value_bytes[];
   uchar digest[];
   if(!StringToAsciiBytes(value, value_bytes) ||
      !Sha256Bytes(value_bytes, digest))
   {
      WipeBytes(value_bytes);
      WipeBytes(digest);
      return false;
   }
   digest_hex = BytesToHex(digest);
   WipeBytes(value_bytes);
   WipeBytes(digest);
   return IsSha256Hex(digest_hex);
}


bool NormalizedManagedMagicNumbers(string &normalized)
{
   normalized = "";
   string parts[];
   int count = StringSplit(ManagedMagicNumbers, ',', parts);
   if(count < 1 || count > 32)
      return false;
   int values[];
   ArrayResize(values, count);
   for(int index = 0; index < count; index++)
   {
      string token = Trimmed(parts[index]);
      if(!IsIntegerToken(token))
         return false;
      long value = StringToInteger(token);
      if(value <= 0 || value > 2147483647)
         return false;
      values[index] = (int)value;
   }
   for(int left = 0; left < count - 1; left++)
   {
      for(int right = left + 1; right < count; right++)
      {
         if(values[right] < values[left])
         {
            int temporary = values[left];
            values[left] = values[right];
            values[right] = temporary;
         }
      }
   }
   for(int sorted_index = 0; sorted_index < count; sorted_index++)
   {
      if(sorted_index > 0 && values[sorted_index] == values[sorted_index - 1])
         return false;
      if(sorted_index > 0)
         normalized += ",";
      normalized += IntegerToString(values[sorted_index]);
   }
   return StringLen(normalized) > 0;
}


bool BuildPortfolioPolicyCanonical(
   string &canonical,
   string &policy_digest
)
{
   canonical = "";
   policy_digest = "";
   string normalized_magics = "";
   if(!NormalizedManagedMagicNumbers(normalized_magics))
      return false;
   canonical = "schema=metafx-hq-account-portfolio-policy-v1";
   canonical += "|managedMagicNumbers=" + normalized_magics;
   canonical += "|positionSizingMode=" + PositionSizingModeName();
   canonical += "|riskPercent=" +
      DoubleToString(EffectiveRiskPercent(), 8);
   canonical += "|riskCapitalBase=" + RiskCapitalBaseName();
   canonical += "|estimatedCommissionPerLot=" +
      DoubleToString(EffectiveEstimatedCommissionPerLot(), 8);
   canonical += "|commissionFreeAccountConfirmed=" +
      (CommissionFreeAccountConfirmed ? "true" : "false");
   canonical += "|maxManagedOpenPositions=" +
      IntegerToString(MaxManagedOpenPositions);
   canonical += "|maxManagedTotalLots=" +
      DoubleToString(MaxManagedTotalLots, 8);
   canonical += "|maxTradesPerBrokerDay=" +
      IntegerToString(MaxTradesPerBrokerDay);
   canonical += "|maxDailyLossPercent=" +
      DoubleToString(MaxDailyLossPercent, 8);
   canonical += "|maxManagedWeeklyLossPercent=" +
      DoubleToString(MaxManagedWeeklyLossPercent, 8);
   canonical += "|maxConsecutiveManagedLosses=" +
      IntegerToString(MaxConsecutiveManagedLosses);
   canonical += "|consecutiveLossCooldownMinutes=" +
      IntegerToString(ConsecutiveLossCooldownMinutes);
   canonical += "|maxAccountEquityDrawdownPercent=" +
      DoubleToString(MaxAccountEquityDrawdownPercent, 8);
   return Sha256TextHex(canonical, policy_digest);
}


bool AccountPortfolioPolicyLeasePath(
   const string policy_digest,
   string &path
)
{
   path = "";
   if(!IsSha256Hex(policy_digest))
      return false;
   string directory = "";
   string channel_digest = "";
   if(!AccountPortfolioPolicyDirectoryPath(directory) ||
      !Sha256TextHex(SnapshotChannel, channel_digest))
      return false;
   // Keep the legacy policy-*.lease namespace so an older v2.16 instance
   // sees this compact slot and stops fail-closed instead of running beside
   // an instance whose lease format it cannot validate.  Prefixes only select
   // the filesystem slot; full digests in the V2 payload authorize the lease.
   path = directory + "\\policy-p-" + StringSubstr(
      policy_digest,
      0,
      PORTFOLIO_POLICY_PREFIX_HEX_LENGTH
   ) + "-c-" + StringSubstr(
      channel_digest,
      0,
      PORTFOLIO_POLICY_PREFIX_HEX_LENGTH
   ) + ".lease";
   return true;
}


int CommonFilesExpandedPathLength(const string relative_path)
{
   string common_root = TerminalInfoString(TERMINAL_COMMONDATA_PATH);
   if(StringLen(common_root) < 3 || StringLen(relative_path) < 1)
      return -1;
   return StringLen(common_root) + StringLen("\\Files\\") +
      StringLen(relative_path);
}


bool LegacyPortfolioPolicyDigestsFromLeaseName(
   const string file_name,
   string &policy_digest,
   string &channel_digest
)
{
   policy_digest = "";
   channel_digest = "";
   string prefix = "policy-";
   string channel_marker = "-channel-";
   string suffix = ".lease";
   int expected_length = StringLen(prefix) + 64 +
      StringLen(channel_marker) + 64 + StringLen(suffix);
   if(StringLen(file_name) != expected_length ||
      StringSubstr(file_name, 0, StringLen(prefix)) != prefix ||
      StringSubstr(
         file_name,
         StringLen(prefix) + 64,
         StringLen(channel_marker)
      ) != channel_marker ||
      StringSubstr(
         file_name,
         expected_length - StringLen(suffix)
      ) != suffix)
      return false;
   policy_digest = StringSubstr(file_name, StringLen(prefix), 64);
   channel_digest = StringSubstr(
      file_name,
      StringLen(prefix) + 64 + StringLen(channel_marker),
      64
   );
   return IsSha256Hex(policy_digest) && IsSha256Hex(channel_digest);
}


bool CompactPortfolioPolicyPrefixesFromLeaseName(
   const string file_name,
   string &policy_prefix,
   string &channel_prefix
)
{
   policy_prefix = "";
   channel_prefix = "";
   string prefix = "policy-p-";
   string channel_marker = "-c-";
   string suffix = ".lease";
   int expected_length = StringLen(prefix) +
      PORTFOLIO_POLICY_PREFIX_HEX_LENGTH + StringLen(channel_marker) +
      PORTFOLIO_POLICY_PREFIX_HEX_LENGTH + StringLen(suffix);
   if(StringLen(file_name) != expected_length ||
      StringSubstr(file_name, 0, StringLen(prefix)) != prefix ||
      StringSubstr(
         file_name,
         StringLen(prefix) + PORTFOLIO_POLICY_PREFIX_HEX_LENGTH,
         StringLen(channel_marker)
      ) != channel_marker ||
      StringSubstr(
         file_name,
         expected_length - StringLen(suffix)
      ) != suffix)
      return false;
   policy_prefix = StringSubstr(
      file_name,
      StringLen(prefix),
      PORTFOLIO_POLICY_PREFIX_HEX_LENGTH
   );
   channel_prefix = StringSubstr(
      file_name,
      StringLen(prefix) + PORTFOLIO_POLICY_PREFIX_HEX_LENGTH +
         StringLen(channel_marker),
      PORTFOLIO_POLICY_PREFIX_HEX_LENGTH
   );
   return IsLowerHexIdentifierPart(
      policy_prefix,
      0,
      PORTFOLIO_POLICY_PREFIX_HEX_LENGTH
   ) && IsLowerHexIdentifierPart(
      channel_prefix,
      0,
      PORTFOLIO_POLICY_PREFIX_HEX_LENGTH
   );
}


bool ParsePortfolioPolicyLeaseEvidence(
   const string file_name,
   const string raw,
   const string expected_account_digest,
   string &policy_digest,
   string &channel_digest
)
{
   policy_digest = "";
   channel_digest = "";
   string legacy_policy_digest = "";
   string legacy_channel_digest = "";
   bool legacy_name = LegacyPortfolioPolicyDigestsFromLeaseName(
      file_name,
      legacy_policy_digest,
      legacy_channel_digest
   );
   string compact_policy_prefix = "";
   string compact_channel_prefix = "";
   bool compact_name = CompactPortfolioPolicyPrefixesFromLeaseName(
      file_name,
      compact_policy_prefix,
      compact_channel_prefix
   );
   if(legacy_name == compact_name)
      return false;

   string parts[];
   int count = StringSplit(Trimmed(raw), '|', parts);
   if(legacy_name)
   {
      if(count != 4 || parts[0] != "MetafxHQPortfolioPolicy" ||
         !IsSha256Hex(parts[1]) || !IsSafeChannel(parts[2]) ||
         !IsIntegerToken(parts[3]) ||
         (int)StringToInteger(parts[3]) < 946684800 ||
         parts[1] != legacy_policy_digest ||
         !Sha256TextHex(parts[2], channel_digest) ||
         channel_digest != legacy_channel_digest)
         return false;
      policy_digest = parts[1];
      return true;
   }

   if(count != 6 || parts[0] != "MetafxHQPortfolioPolicyV2" ||
      !IsSha256Hex(parts[1]) || !IsSha256Hex(parts[2]) ||
      !IsSha256Hex(parts[3]) || !IsSafeChannel(parts[4]) ||
      !IsIntegerToken(parts[5]) ||
      (int)StringToInteger(parts[5]) < 946684800 ||
      parts[1] != expected_account_digest ||
      StringSubstr(
         parts[2],
         0,
         PORTFOLIO_POLICY_PREFIX_HEX_LENGTH
      ) != compact_policy_prefix ||
      StringSubstr(parts[3], 0, PORTFOLIO_POLICY_PREFIX_HEX_LENGTH) !=
         compact_channel_prefix)
      return false;
   // The compact filename is only a slot selector.  Recompute the complete
   // digest from the non-secret channel carried by the bounded V2 payload so
   // a tail-only digest mutation cannot borrow a valid 16-hex slot prefix.
   string observed_channel_digest = "";
   if(!Sha256TextHex(parts[4], observed_channel_digest) ||
      observed_channel_digest != parts[3])
      return false;
   policy_digest = parts[2];
   channel_digest = observed_channel_digest;
   return true;
}


bool InspectPortfolioPolicyLeases(
   const string directory,
   const string expected_account_digest,
   const string expected_policy_digest,
   int &active_lease_count,
   string &reason
)
{
   active_lease_count = 0;
   string file_name = "";
   // AcquirePortfolioPolicyLease ensures the canonical policy file exists
   // before this call.  Enumerating the whole account-policy directory means
   // INVALID_HANDLE can therefore never mean an ordinary empty result.
   ResetLastError();
   long search_handle = FileFindFirst(
      directory + "\\*",
      file_name,
      FILE_COMMON
   );
   if(search_handle == INVALID_HANDLE)
   {
      g_portfolio_policy_lease_scan_error = GetLastError();
      reason = "PORTFOLIO_POLICY_STATE_INVALID";
      return false;
   }
   while(true)
   {
      if(StringSubstr(file_name, 0, StringLen("policy-")) == "policy-")
      {
         string lease_path = directory + "\\" + file_name;
         // Probe ownership before parsing. A crash may leave an empty or
         // partial file, but once its exclusive handle is gone it is stale
         // evidence and can be removed safely without trusting its payload.
         ResetLastError();
         int stale_handle = FileOpen(
            lease_path,
            FILE_READ | FILE_WRITE | FILE_BIN | FILE_ANSI | FILE_COMMON
         );
         if(stale_handle != INVALID_HANDLE)
         {
            FileClose(stale_handle);
            ResetLastError();
            if(!FileDelete(lease_path, FILE_COMMON) &&
               FileIsExist(lease_path, FILE_COMMON))
            {
               FileFindClose(search_handle);
               reason = "PORTFOLIO_POLICY_STALE_LEASE_CLEANUP_FAILED";
               return false;
            }
         }
         else
         {
            string raw = "";
            string active_policy_digest = "";
            string active_channel_digest = "";
            if(!ReadCommonText(lease_path, 512, raw) ||
               !ParsePortfolioPolicyLeaseEvidence(
                  file_name,
                  raw,
                  expected_account_digest,
                  active_policy_digest,
                  active_channel_digest
               ))
            {
               FileFindClose(search_handle);
               reason = "PORTFOLIO_POLICY_STATE_INVALID";
               return false;
            }
            active_lease_count++;
            if(active_policy_digest != expected_policy_digest)
            {
               FileFindClose(search_handle);
               reason = "PORTFOLIO_POLICY_MISMATCH";
               return false;
            }
         }
      }

      ResetLastError();
      bool has_next = FileFindNext(search_handle, file_name);
      int find_next_error = GetLastError();
      if(has_next)
         continue;
      FileFindClose(search_handle);
      if(find_next_error != 0)
      {
         g_portfolio_policy_lease_scan_error = find_next_error;
         reason = "PORTFOLIO_POLICY_STATE_INVALID";
         return false;
      }
      return true;
   }
   reason = "PORTFOLIO_POLICY_STATE_INVALID";
   return false;
}


bool AcquirePortfolioPolicyLease(string &reason)
{
   reason = "";
   if(g_portfolio_policy_lease_handle != INVALID_HANDLE)
      return true;
   string canonical = "";
   string expected_digest = "";
   string directory = "";
   string policy_path = "";
   string account_digest = "";
   string channel_digest = "";
   if(!BuildPortfolioPolicyCanonical(canonical, expected_digest) ||
      !AccountPortfolioPolicyDirectoryPath(directory) ||
      !AccountPortfolioPolicyPath(policy_path) ||
      !AccountIdentityDigest(account_digest) ||
      !Sha256TextHex(SnapshotChannel, channel_digest))
   {
      reason = "PORTFOLIO_POLICY_STATE_INVALID";
      return false;
   }
   // Keep the expected non-secret policy digest available to init diagnostics
   // even when another live instance holds a mismatched policy and OnInit
   // stops fail-closed before status.json can be published.
   g_portfolio_policy_digest = expected_digest;
   g_portfolio_policy_lease_scan_error = 0;

   // Seed a non-authorizing marker before enumeration so FileFindFirst
   // returning an invalid handle is an I/O/state failure, never an ambiguous
   // empty match. Do not repair the canonical policy before active leases have
   // been inspected; missing/corrupt policy with an owner must remain invalid.
   string scan_anchor_path = directory + "\\scan-anchor-v1.txt";
   if(!FileIsExist(scan_anchor_path, FILE_COMMON) &&
      !WriteCommonTextAtomic(
         scan_anchor_path,
         "MetafxHQPortfolioPolicyScanAnchorV1"
      ))
   {
      reason = "PORTFOLIO_POLICY_STATE_INVALID";
      return false;
   }

   int active_lease_count = 0;
   if(!InspectPortfolioPolicyLeases(
      directory,
      account_digest,
      expected_digest,
      active_lease_count,
      reason
   ))
   {
      return false;
   }

   if(active_lease_count > 0)
   {
      string stored_policy = "";
      bool policy_exists = FileIsExist(policy_path, FILE_COMMON);
      if(!ReadCommonText(policy_path, 4096, stored_policy) ||
         !policy_exists || Trimmed(stored_policy) != canonical)
      {
         reason = "PORTFOLIO_POLICY_STATE_INVALID";
         return false;
      }
   }
   else if(!WriteCommonTextAtomic(policy_path, canonical))
   {
      reason = "PORTFOLIO_POLICY_STATE_INVALID";
      return false;
   }

   string own_lease_path = "";
   if(!AccountPortfolioPolicyLeasePath(expected_digest, own_lease_path))
   {
      reason = "PORTFOLIO_POLICY_STATE_INVALID";
      return false;
   }
   g_portfolio_policy_lease_open_error = 0;
   g_portfolio_policy_lease_expanded_path_length =
      CommonFilesExpandedPathLength(own_lease_path);
   if(g_portfolio_policy_lease_expanded_path_length < 1 ||
      g_portfolio_policy_lease_expanded_path_length >
         PORTFOLIO_POLICY_MAX_EXPANDED_PATH_LENGTH)
   {
      reason = "PORTFOLIO_POLICY_STATE_INVALID";
      return false;
   }
   ResetLastError();
   int lease_handle = FileOpen(
      own_lease_path,
      FILE_READ | FILE_WRITE | FILE_BIN | FILE_ANSI | FILE_COMMON |
      FILE_SHARE_READ
   );
   if(lease_handle == INVALID_HANDLE)
   {
      g_portfolio_policy_lease_open_error = GetLastError();
      reason = "PORTFOLIO_POLICY_LEASE_UNAVAILABLE";
      return false;
   }
   FileSeek(lease_handle, 0, SEEK_SET);
   string lease_payload =
      "MetafxHQPortfolioPolicyV2|" + account_digest + "|" +
      expected_digest + "|" + channel_digest + "|" +
      SnapshotChannel + "|" +
      IntegerToString(NowUtc());
   uint written = FileWriteString(
      lease_handle,
      lease_payload
   );
   FileFlush(lease_handle);
   if(written != (uint)StringLen(lease_payload))
   {
      g_portfolio_policy_lease_open_error = GetLastError();
      FileClose(lease_handle);
      FileDelete(own_lease_path, FILE_COMMON);
      reason = "PORTFOLIO_POLICY_STATE_INVALID";
      return false;
   }
   g_portfolio_policy_lease_handle = lease_handle;
   g_portfolio_policy_lease_path = own_lease_path;
   g_portfolio_policy_digest = expected_digest;
   return true;
}


void ReleasePortfolioPolicyLease()
{
   string lease_path = g_portfolio_policy_lease_path;
   if(g_portfolio_policy_lease_handle != INVALID_HANDLE)
      FileClose(g_portfolio_policy_lease_handle);
   g_portfolio_policy_lease_handle = INVALID_HANDLE;
   g_portfolio_policy_lease_path = "";
   g_portfolio_policy_digest = "";
   if(StringLen(lease_path) > 0)
   {
      ResetLastError();
      FileDelete(lease_path, FILE_COMMON);
      ResetLastError();
   }
}


int NowUtc()
{
   datetime value = TimeGMT();
   if(value <= 0)
      value = TimeLocal();
   return (int)value;
}


bool GatewayModeIsValid()
{
   return GatewayMode == GATEWAY_SHADOW ||
      GatewayMode == GATEWAY_DEMO ||
      GatewayMode == GATEWAY_LIVE;
}


bool PositionLifecycleModeIsValid()
{
   return PositionLifecycleMode == LIFECYCLE_SLTP_ONLY ||
      PositionLifecycleMode == LIFECYCLE_MAX_HOLDING ||
      PositionLifecycleMode == LIFECYCLE_SESSION_CLOSE ||
      PositionLifecycleMode == LIFECYCLE_MAX_HOLDING_AND_SESSION_CLOSE;
}


bool ValidateConfiguredModes(string &reason)
{
   if(!GatewayModeIsValid())
   {
      reason = "GATEWAY_MODE_INVALID";
      return false;
   }
   if(!PositionLifecycleModeIsValid())
   {
      reason = "POSITION_LIFECYCLE_MODE_INVALID";
      return false;
   }
   reason = "READY";
   return true;
}


string ModeName()
{
   if(GatewayMode == GATEWAY_SHADOW)
      return "shadow";
   if(GatewayMode == GATEWAY_DEMO)
      return "demo";
   if(GatewayMode == GATEWAY_LIVE)
      return "live";
   return "invalid";
}


string AccountModeName()
{
   ENUM_ACCOUNT_TRADE_MODE mode =
      (ENUM_ACCOUNT_TRADE_MODE)AccountInfoInteger(ACCOUNT_TRADE_MODE);
   return mode == ACCOUNT_TRADE_MODE_REAL ? "live" : "demo";
}


string JsonBoolean(const bool value)
{
   if(value)
      return "true";
   return "false";
}


string LifecycleModeName()
{
   if(PositionLifecycleMode == LIFECYCLE_SLTP_ONLY)
      return "SLTP_ONLY";
   if(PositionLifecycleMode == LIFECYCLE_MAX_HOLDING)
      return "MAX_HOLDING";
   if(PositionLifecycleMode == LIFECYCLE_SESSION_CLOSE)
      return "SESSION_CLOSE";
   if(PositionLifecycleMode == LIFECYCLE_MAX_HOLDING_AND_SESSION_CLOSE)
      return "MAX_HOLDING_AND_SESSION_CLOSE";
   return "INVALID";
}


bool SignedCommandVerificationAvailable()
{
   string reason = "";
   return RefreshSigningReadiness(reason);
}


string BuildCapabilitiesJson()
{
   string signing_reason = "";
   bool signed_ready = RefreshSigningReadiness(signing_reason);
   bool demo_account = IsDemo();
   bool demo_ready = GatewayMode == GATEWAY_DEMO &&
      demo_account && signed_ready;
   bool explicit_live_pin = StringLen(g_trusted_signing_key_id) > 0 &&
      g_trusted_signing_key_id == g_active_signing_key_id;
   bool live_commission_policy_confirmed =
      LiveCommissionPolicyConfirmed();
   bool live_symbol_exact_allowlist_confirmed =
      LiveSymbolExactAllowlistConfirmed();
   string live_owner_reason = "";
   bool live_owner_ready = LiveAccountOwnerLockReady(live_owner_reason);
   // LIVE is deliberately limited to one Windows user on one host. FILE_COMMON
   // cannot coordinate another user, machine, or VPS, so the operator must
   // explicitly acknowledge that boundary before this local owner lock counts.
   bool live_ready = GatewayMode == GATEWAY_LIVE &&
      !demo_account && LiveArmed && SingleHostLiveAcknowledged &&
      signed_ready && explicit_live_pin &&
      live_commission_policy_confirmed &&
      live_symbol_exact_allowlist_confirmed && live_owner_ready;
   string live_block_reason = "";
   if(GatewayMode != GATEWAY_LIVE)
      live_block_reason = "LIVE_MODE_NOT_SELECTED";
   else if(demo_account)
      live_block_reason = "LIVE_MODE_REQUIRES_NON_DEMO_ACCOUNT";
   else if(!LiveArmed)
      live_block_reason = "LIVE_NOT_ARMED";
   else if(!SingleHostLiveAcknowledged)
      live_block_reason = "SINGLE_HOST_LIVE_ACK_REQUIRED";
   else if(!signed_ready)
      live_block_reason = signing_reason;
   else if(!explicit_live_pin)
      live_block_reason = "LIVE_SIGNING_KEY_NOT_PINNED";
   else if(!live_commission_policy_confirmed)
      live_block_reason = "LIVE_COMMISSION_POLICY_UNCONFIRMED";
   else if(!live_symbol_exact_allowlist_confirmed)
      live_block_reason = "LIVE_SYMBOL_REQUIRES_EXACT_ALLOWLIST";
   else if(!live_owner_ready)
      live_block_reason = live_owner_reason;
   string payload = "{";
   payload += "\"schemaVersion\":\"metafx-hq-mt4-capabilities-v1\",";
   payload += "\"channelId\":" + JsonString(SnapshotChannel) + ",";
   payload += "\"gatewayMode\":" + JsonString(ModeName()) + ",";
   payload += "\"demoAccount\":" + JsonBoolean(demo_account) + ",";
   payload += "\"accountMode\":" + JsonString(AccountModeName()) + ",";
   payload += "\"commandSchemaVersion\":" + JsonString(COMMAND_SCHEMA) + ",";
   payload += "\"ackSchemaVersion\":" + JsonString(ACK_SCHEMA) + ",";
   payload += "\"shadowValidationAvailable\":true,";
   payload += "\"signedEnvelopeSchemaVersion\":" + JsonString(SIGNED_ENVELOPE_SCHEMA) + ",";
   payload += "\"signatureAlgorithm\":" + JsonString(SIGNATURE_ALGORITHM) + ",";
   payload += "\"demoExecutionAvailable\":" + JsonBoolean(demo_ready) + ",";
   payload += "\"signedCommandVerification\":" +
      JsonBoolean(signed_ready) + ",";
   payload += "\"activeSigningKeyId\":" + JsonString(g_active_signing_key_id) + ",";
   payload += "\"signingKeyPinned\":" + JsonBoolean(g_signing_key_pinned) + ",";
   payload += "\"singleHostLiveAcknowledged\":" +
      JsonBoolean(SingleHostLiveAcknowledged) + ",";
   payload += "\"liveSafetyScope\":\"single_windows_user_file_common_only\",";
   payload += "\"liveExecutionAvailable\":" + JsonBoolean(live_ready) + ",";
   payload += "\"liveBlockReason\":" + JsonString(live_block_reason) + ",";
   payload += "\"portfolioGuardScope\":\"MANAGED_MAGIC_NUMBERS_ACCOUNT_WIDE\",";
   payload += "\"historyScope\":\"MT5_SELECTED_DEAL_HISTORY\",";
   payload += "\"managedMagicNumbers\":" + JsonString(ManagedMagicNumbers) + ",";
   payload += "\"positionLifecycleMode\":" + JsonString(LifecycleModeName()) + ",";
   payload += "\"outcomeTracking\":false,";
   payload += "\"postOrderVerification\":true,";
   payload += "\"executionUnknownRecovery\":\"EA_RECONCILE_OR_BACKEND_QUARANTINE\"";
   payload += "}";
   return payload;
}


bool WriteCapabilitiesSnapshot()
{
   return WriteCommonTextAtomic(CapabilitiesPath(), BuildCapabilitiesJson());
}


void ResetAckExecutionEvidence()
{
   g_ack_has_execution_evidence = false;
   g_ack_filled_price = 0.0;
   g_ack_filled_slippage_points = 0.0;
   g_ack_actual_stop_loss = 0.0;
   g_ack_actual_take_profit = 0.0;
   g_ack_actual_magic_number = 0;
   g_ack_actual_comment = "";
   g_ack_verification_status = "NOT_APPLICABLE";
   g_ack_execution_state = "NONE";
   g_ack_closed_at = 0;
   g_ack_closed_pnl = 0.0;
   g_ack_has_closed_pnl = false;
   g_ack_has_sizing_evidence = false;
   g_ack_reported_volume = 0.0;
   g_ack_position_sizing_mode = "";
   g_ack_risk_percent = 0.0;
   g_ack_risk_capital_base = "";
   g_ack_estimated_commission_per_lot = 0.0;
   g_ack_risk_capital_amount = 0.0;
   g_ack_estimated_risk_money = 0.0;
}


void SetAckSizingEvidence(
   const double reported_volume,
   const string position_sizing_mode,
   const double risk_percent,
   const string risk_capital_base,
   const double estimated_commission_per_lot,
   const double risk_capital_amount,
   const double estimated_risk_money
)
{
   g_ack_has_sizing_evidence = true;
   g_ack_reported_volume = reported_volume;
   g_ack_position_sizing_mode = position_sizing_mode;
   g_ack_risk_percent = risk_percent;
   g_ack_risk_capital_base = risk_capital_base;
   g_ack_estimated_commission_per_lot = estimated_commission_per_lot;
   g_ack_risk_capital_amount = risk_capital_amount;
   g_ack_estimated_risk_money = estimated_risk_money;
}


string BuildStatusJson()
{
   UpdateRiskTelemetry(false);
   bool signed_ready = SignedCommandVerificationAvailable();
   bool demo_account = IsDemo();
   string normalized_managed_magics = "";
   string normalized_allowed_symbols = "";
   string normalized_allowed_timeframes = "";
   bool status_config_valid =
      NormalizedManagedMagicNumbers(normalized_managed_magics) &&
      NormalizeAllowedSymbolsCsv(
         AllowedSymbols,
         normalized_allowed_symbols
      ) &&
      NormalizeAllowedTimeframesCsv(
         AllowedTimeframes,
         normalized_allowed_timeframes
      );
   bool portfolio_policy_ready =
      status_config_valid &&
      g_portfolio_policy_lease_handle != INVALID_HANDLE &&
      IsSha256Hex(g_portfolio_policy_digest);
   string account_binding_id = "";
   bool account_binding_ready =
      ProtocolAccountBindingId(account_binding_id);
   if(!account_binding_ready)
   {
      g_cached_execution_guard_ready = false;
      g_cached_execution_guard_reason =
         "ACCOUNT_IDENTITY_BINDING_UNAVAILABLE";
   }
   string payload = "{";
   payload += "\"schemaVersion\":" + JsonString(STATUS_SCHEMA) + ",";
   payload += "\"eaVersion\":" + JsonString(EA_VERSION) + ",";
   payload += "\"channelId\":" + JsonString(SnapshotChannel) + ",";
   payload += "\"profile\":" + JsonString(EA_PROFILE) + ",";
   payload += "\"mode\":" + JsonString(ModeName()) + ",";
   payload += "\"terminalPlatform\":\"mt5\",";
   payload += "\"accountBindingId\":" +
      JsonString(account_binding_id) + ",";
   payload += "\"demoAccount\":" + JsonBoolean(demo_account) + ",";
   payload += "\"accountMode\":" + JsonString(AccountModeName()) + ",";
   payload += "\"liveArmed\":" + JsonBoolean(LiveArmed) + ",";
   payload += "\"singleHostLiveAcknowledged\":" +
      JsonBoolean(SingleHostLiveAcknowledged) + ",";
   payload += "\"liveSafetyScope\":\"single_windows_user_file_common_only\",";
   payload += "\"fixedLot\":" + DoubleToString(FixedLot, LotDigits()) + ",";
   payload += "\"positionSizingMode\":" +
      JsonString(PositionSizingModeName()) + ",";
   payload += "\"riskPercent\":" +
      JsonNumber(EffectiveRiskPercent(), 8) + ",";
   payload += "\"riskCapitalBase\":" +
      JsonString(RiskCapitalBaseName()) + ",";
   payload += "\"estimatedCommissionPerLot\":" +
      JsonNumber(EffectiveEstimatedCommissionPerLot(), 8) + ",";
   payload += "\"commissionFreeAccountConfirmed\":" +
      JsonBoolean(CommissionFreeAccountConfirmed) + ",";
   payload += "\"brokerVolumeMin\":" +
      JsonNumber(SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN), LotDigits()) + ",";
   payload += "\"brokerVolumeMax\":" +
      JsonNumber(SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX), LotDigits()) + ",";
   payload += "\"brokerVolumeStep\":" +
      JsonNumber(SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP), LotDigits()) + ",";
   payload += "\"symbol\":" + JsonString(Symbol()) + ",";
   payload += "\"timeframe\":" + JsonString(CurrentTimeframeName()) + ",";
   payload += "\"observedAt\":" + IntegerToString(NowUtc()) + ",";
   payload += "\"autoTradingAllowed\":" + JsonBoolean(IsExpertEnabled()) + ",";
   payload += "\"tradeAllowed\":" + JsonBoolean(IsTradeAllowed()) + ",";
   payload += "\"killSwitchActive\":" +
      JsonBoolean(FileIsExist(KillMarkerPath(), FILE_COMMON)) + ",";
   payload += "\"commandSchemaVersion\":" + JsonString(COMMAND_SCHEMA) + ",";
   payload += "\"ackSchemaVersion\":" + JsonString(ACK_SCHEMA) + ",";
   payload += "\"signedCommandVerificationAvailable\":" + JsonBoolean(signed_ready) + ",";
   payload += "\"activeSigningKeyId\":" + JsonString(g_active_signing_key_id) + ",";
   payload += "\"signingKeyPinned\":" + JsonBoolean(g_signing_key_pinned) + ",";
   payload += "\"signatureAlgorithm\":" + JsonString(SIGNATURE_ALGORITHM) + ",";
   payload += "\"lastSignatureVerificationStatus\":" + JsonString(g_last_signature_verification_status) + ",";
   payload += "\"executionGuardReady\":" + JsonBoolean(g_cached_execution_guard_ready) + ",";
   payload += "\"executionGuardReason\":" + JsonString(g_cached_execution_guard_reason) + ",";
   payload += "\"portfolioPolicyStatus\":" +
      JsonString(portfolio_policy_ready ? "ready" : "not_ready") + ",";
   payload += "\"portfolioPolicyDigest\":" +
      JsonString(g_portfolio_policy_digest) + ",";
   payload += "\"portfolioGuardScope\":\"MANAGED_MAGIC_NUMBERS_ACCOUNT_WIDE\",";
   payload += "\"managedMagicNumbers\":" +
      JsonString(normalized_managed_magics) + ",";
   payload += "\"allowedSymbols\":" +
      JsonString(normalized_allowed_symbols) + ",";
   payload += "\"allowedTimeframes\":" +
      JsonString(normalized_allowed_timeframes) + ",";
   payload += "\"concurrencyBoundary\":\"same_windows_user_file_common\",";
   payload += "\"crossVpsDistributedLock\":false,";
   payload += "\"maxManagedPositions\":" + IntegerToString(MaxManagedOpenPositions) + ",";
   payload += "\"currentManagedPositions\":" + IntegerToString(g_cached_managed_positions) + ",";
   payload += "\"maxManagedLots\":" + JsonNumber(MaxManagedTotalLots, LotDigits()) + ",";
   payload += "\"currentManagedLots\":" + JsonNumber(g_cached_managed_lots, LotDigits()) + ",";
   payload += "\"maxTradesToday\":" + IntegerToString(MaxTradesPerBrokerDay) + ",";
   payload += "\"currentTradesToday\":" + IntegerToString(g_cached_trades_today) + ",";
   payload += "\"maxLossPerTradePercent\":" + JsonNumber(MaxLossPerTradePercent, 2) + ",";
   payload += "\"maxDailyLossPercent\":" + JsonNumber(MaxDailyLossPercent, 2) + ",";
   payload += "\"managedDailyPnl\":" + JsonNumber(g_cached_managed_daily_pnl, 2) + ",";
   payload += "\"maxAccountEquityDrawdownPercent\":" + JsonNumber(MaxAccountEquityDrawdownPercent, 2) + ",";
   payload += "\"currentAccountEquityDrawdownPercent\":" + JsonNumber(g_cached_account_drawdown_percent, 2) + ",";
   payload += "\"minRewardRiskRatio\":" + JsonNumber(MinRewardRiskRatio, 2) + ",";
   payload += "\"minProjectedMarginLevelPercent\":" + JsonNumber(MinProjectedMarginLevelPercent, 2) + ",";
   payload += "\"currentMarginLevelPercent\":" + JsonNumber(g_cached_margin_level_percent, 2) + ",";
   payload += "\"maxSnapshotAgeSeconds\":" + IntegerToString(MaxSnapshotAgeSeconds) + ",";
   payload += "\"maxSignalDriftPoints\":" + IntegerToString(MaxSignalDriftPoints) + ",";
   payload += "\"maxQuoteAgeSeconds\":" + IntegerToString(MaxQuoteAgeSeconds);
   payload += "}";
   return payload;
}


bool WriteStatusSnapshot()
{
   return WriteCommonTextAtomic(StatusPath(), BuildStatusJson());
}


void InvalidatePublishedRuntimeState()
{
   // A chart symbol/timeframe change deinitializes the EA before the new chart
   // initializes. Remove the old READY/status/snapshot immediately so the
   // backend cannot briefly bind a fresh command to the previous chart.
   ResetLastError();
   FileDelete(StatusPath(), FILE_COMMON);
   ResetLastError();
   FileDelete(CapabilitiesPath(), FILE_COMMON);
   ResetLastError();
   FileDelete(SnapshotPath(), FILE_COMMON);
   ResetLastError();
}


int VolumeDigitsForValue(const double value)
{
   if(!MathIsValidNumber(value) || value <= 0.0)
      return 0;
   int digits = 0;
   double scaled = value;
   while(digits < 8 && MathAbs(scaled - MathRound(scaled)) > 0.00000001)
   {
      scaled *= 10.0;
      digits++;
   }
   return digits;
}


int LotDigits()
{
   double minimum = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double step = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   int minimum_digits = VolumeDigitsForValue(minimum);
   int step_digits = VolumeDigitsForValue(step);
   if(minimum_digits == 0 && step_digits == 0 &&
      (minimum <= 0.0 || step <= 0.0))
      return 2;
   return minimum_digits > step_digits ? minimum_digits : step_digits;
}


int SymbolPriceDigits()
{
   long digits = 0;
   if(!SymbolInfoInteger(_Symbol, SYMBOL_DIGITS, digits) ||
      digits < 0 || digits > 8)
      return _Digits;
   return (int)digits;
}


double NormalizeSymbolPrice(const double value)
{
   return NormalizeDouble(value, SymbolPriceDigits());
}


string BuildAckJson(
   const CommandPayload &command,
   const string status,
   const string reason_code,
   const ulong ticket,
   const int error_code,
   const bool state_persisted
)
{
   string payload = "{";
   payload += "\"schemaVersion\":" + JsonString(ACK_SCHEMA) + ",";
   payload += "\"profile\":" + JsonString(EA_PROFILE) + ",";
   payload += "\"commandId\":" + JsonString(command.command_id) + ",";
   payload += "\"idempotencyKey\":" + JsonString(command.idempotency_key) + ",";
   payload += "\"channelId\":" + JsonString(SnapshotChannel) + ",";
   payload += "\"missionId\":" + JsonString(command.mission_id) + ",";
   payload += "\"councilDecisionId\":" + JsonString(command.council_decision_id) + ",";
   payload += "\"ownerAgentId\":" + JsonString(command.owner_agent_id) + ",";
   payload += "\"snapshotId\":" + JsonString(command.snapshot_id) + ",";
   payload += "\"snapshotObservedAt\":" + IntegerToString(command.snapshot_observed_at) + ",";
   payload += "\"barTime\":" + IntegerToString(command.bar_time) + ",";
   // Preserve the exact command identity.  The council reference can be a
   // bid/ask midpoint with one more decimal than the broker display _Digits.
   payload += "\"referencePrice\":" + JsonNumber(command.reference_price, 8) + ",";
   payload += "\"eaClosedBarTime\":" + IntegerToString((int)iTime(Symbol(), Period(), 1)) + ",";
   payload += "\"status\":" + JsonString(status) + ",";
   payload += "\"reasonCode\":" + JsonString(reason_code) + ",";
   payload += "\"mode\":" + JsonString(ModeName()) + ",";
   payload += "\"action\":" + JsonString(command.action) + ",";
   payload += "\"symbol\":" + JsonString(command.symbol) + ",";
   payload += "\"timeframe\":" + JsonString(command.timeframe) + ",";
   double reported_volume = g_ack_has_sizing_evidence
      ? g_ack_reported_volume
      : 0.0;
   payload += "\"fixedLot\":" +
      DoubleToString(reported_volume, LotDigits()) + ",";
   payload += "\"positionSizingMode\":" +
      JsonString(
         g_ack_has_sizing_evidence
            ? g_ack_position_sizing_mode
            : PositionSizingModeName()
      ) + ",";
   payload += "\"riskPercent\":" + JsonNumber(
      g_ack_has_sizing_evidence
         ? g_ack_risk_percent
         : EffectiveRiskPercent(),
      8
   ) + ",";
   payload += "\"riskCapitalBase\":" +
      JsonString(
         g_ack_has_sizing_evidence
            ? g_ack_risk_capital_base
            : RiskCapitalBaseName()
      ) + ",";
   payload += "\"estimatedCommissionPerLot\":" + JsonNumber(
      g_ack_has_sizing_evidence
         ? g_ack_estimated_commission_per_lot
          : EffectiveEstimatedCommissionPerLot(),
      8
   ) + ",";
   if(g_ack_has_sizing_evidence)
   {
      payload += "\"riskCapitalAmount\":" +
         JsonNumber(g_ack_risk_capital_amount, 8) + ",";
      payload += "\"estimatedRiskMoney\":" +
         JsonNumber(g_ack_estimated_risk_money, 8) + ",";
   }
   else
   {
      payload += "\"riskCapitalAmount\":null,";
      payload += "\"estimatedRiskMoney\":null,";
   }
   payload += "\"observedAt\":" + IntegerToString(NowUtc()) + ",";
   if(ticket > 0)
      payload += "\"ticket\":" + StringFormat("%I64u", ticket) + ",";
   else
      payload += "\"ticket\":null,";
   if(g_ack_has_execution_evidence)
   {
      payload += "\"filledPrice\":" + JsonNumber(g_ack_filled_price, _Digits) + ",";
      payload += "\"filledSlippagePoints\":" + JsonNumber(g_ack_filled_slippage_points, 2) + ",";
      payload += "\"actualStopLoss\":" + JsonNumber(g_ack_actual_stop_loss, _Digits) + ",";
      payload += "\"actualTakeProfit\":" + JsonNumber(g_ack_actual_take_profit, _Digits) + ",";
      payload += "\"actualMagicNumber\":" + IntegerToString(g_ack_actual_magic_number) + ",";
   }
   else
   {
      payload += "\"filledPrice\":null,";
      payload += "\"filledSlippagePoints\":null,";
      payload += "\"actualStopLoss\":null,";
      payload += "\"actualTakeProfit\":null,";
      payload += "\"actualMagicNumber\":null,";
   }
   payload += "\"actualComment\":" + JsonString(g_ack_actual_comment) + ",";
   payload += "\"signatureVerificationStatus\":" +
      JsonString(command.signature_verification_status) + ",";
   payload += "\"verificationStatus\":" + JsonString(g_ack_verification_status) + ",";
   payload += "\"executionState\":" + JsonString(g_ack_execution_state) + ",";
   if(g_ack_closed_at > 0)
      payload += "\"closedAt\":" + IntegerToString(g_ack_closed_at) + ",";
   else
      payload += "\"closedAt\":null,";
   if(g_ack_has_closed_pnl)
      payload += "\"closedPnl\":" + JsonNumber(g_ack_closed_pnl, 2) + ",";
   else
      payload += "\"closedPnl\":null,";
   payload += "\"errorCode\":" + IntegerToString(error_code) + ",";
   payload += "\"statePersisted\":" + (state_persisted ? "true" : "false");
   payload += "}";
   return payload;
}


string BuildSystemAckJson(
   const string status,
   const string reason_code
)
{
   string payload = "{";
   payload += "\"schemaVersion\":" + JsonString(ACK_SCHEMA) + ",";
   payload += "\"profile\":" + JsonString(EA_PROFILE) + ",";
   payload += "\"commandId\":\"unknown\",";
   payload += "\"idempotencyKey\":\"unknown\",";
   payload += "\"channelId\":" + JsonString(SnapshotChannel) + ",";
   payload += "\"status\":" + JsonString(status) + ",";
   payload += "\"reasonCode\":" + JsonString(reason_code) + ",";
   payload += "\"mode\":" + JsonString(ModeName()) + ",";
   payload += "\"signatureVerificationStatus\":" +
      JsonString(g_last_signature_verification_status) + ",";
   payload += "\"observedAt\":" + IntegerToString(NowUtc());
   payload += "}";
   return payload;
}


void PublishSystemAck(
   const string status,
   const string reason_code
)
{
   string payload = BuildSystemAckJson(status, reason_code);
   WriteCommonTextAtomic(BasePath() + "\\acks\\last-invalid.json", payload);
   AppendAudit(payload);
   Print("MetafxHQ Trade Gateway ", status, " ", reason_code);
}


bool WriteExecutionMarkers(
   const CommandPayload &command,
   const string payload
)
{
   bool command_written = WriteCommonTextAtomic(
      CommandLedgerPath(command.command_id),
      payload
   );
   bool idempotency_written = WriteCommonTextAtomic(
      IdempotencyLedgerPath(command.idempotency_key),
      payload
   );
   return command_written && idempotency_written;
}


bool IsExecutionAttemptKey(const string key)
{
   return key == "schemaVersion" ||
      key == "stage" ||
      key == "commandId" ||
      key == "idempotencyKey" ||
      key == "channelId" ||
      key == "accountBindingId" ||
      key == "streamKey" ||
      key == "signedCommandDigest" ||
      key == "snapshotId" ||
      key == "barTime" ||
      key == "action" ||
      key == "symbol" ||
      key == "timeframe" ||
      key == "brokerComment" ||
      key == "expectedVolume" ||
      key == "positionSizingMode" ||
      key == "riskPercent" ||
      key == "riskCapitalBase" ||
      key == "estimatedCommissionPerLot" ||
      key == "riskCapitalAmount" ||
      key == "estimatedRiskMoney" ||
      key == "expectedStopLoss" ||
      key == "expectedTakeProfit" ||
      key == "orderId" ||
      key == "dealId" ||
      key == "requestId" ||
      key == "retcode" ||
      key == "retcodeExternal" ||
      key == "apiAccepted" ||
      key == "apiError" ||
      key == "observedAt";
}


bool BuildExecutionAttemptJson(
   const CommandPayload &command,
   const string signed_raw,
   const double expected_volume,
   const string stage,
   const bool api_accepted,
   const MqlTradeResult &result,
   const int api_error,
   string &payload
)
{
   payload = "";
   if(!g_ack_has_sizing_evidence ||
      !MathIsValidNumber(expected_volume) || expected_volume <= 0.0 ||
      MathAbs(expected_volume - g_ack_reported_volume) > 0.00000001)
      return false;
   string account_binding_id = "";
   string stream_key = "";
   string signed_command_digest = "";
   if(!ProtocolAccountBindingId(account_binding_id) ||
      !ProtocolStreamKey(command, stream_key) ||
      !SignedCommandDigest(signed_raw, signed_command_digest))
      return false;
   payload = "{";
   payload += "\"schemaVersion\":" +
      JsonString(EXECUTION_ATTEMPT_SCHEMA) + ",";
   payload += "\"stage\":" + JsonString(stage) + ",";
   payload += "\"commandId\":" + JsonString(command.command_id) + ",";
   payload += "\"idempotencyKey\":" +
      JsonString(command.idempotency_key) + ",";
   payload += "\"channelId\":" + JsonString(command.channel_id) + ",";
   payload += "\"accountBindingId\":" +
      JsonString(account_binding_id) + ",";
   payload += "\"streamKey\":" + JsonString(stream_key) + ",";
   payload += "\"signedCommandDigest\":" +
      JsonString(signed_command_digest) + ",";
   payload += "\"snapshotId\":" + JsonString(command.snapshot_id) + ",";
   payload += "\"barTime\":" + IntegerToString(command.bar_time) + ",";
   payload += "\"action\":" + JsonString(command.action) + ",";
   payload += "\"symbol\":" + JsonString(command.symbol) + ",";
   payload += "\"timeframe\":" + JsonString(command.timeframe) + ",";
   payload += "\"brokerComment\":" +
      JsonString("HQ:" + command.command_id) + ",";
   payload += "\"expectedVolume\":" +
      DoubleToString(expected_volume, 8) + ",";
   payload += "\"positionSizingMode\":" +
      JsonString(g_ack_position_sizing_mode) + ",";
   payload += "\"riskPercent\":" +
      JsonNumber(g_ack_risk_percent, 8) + ",";
   payload += "\"riskCapitalBase\":" +
      JsonString(g_ack_risk_capital_base) + ",";
   payload += "\"estimatedCommissionPerLot\":" +
      JsonNumber(g_ack_estimated_commission_per_lot, 8) + ",";
   payload += "\"riskCapitalAmount\":" +
      JsonNumber(g_ack_risk_capital_amount, 8) + ",";
   payload += "\"estimatedRiskMoney\":" +
      JsonNumber(g_ack_estimated_risk_money, 8) + ",";
   payload += "\"expectedStopLoss\":" +
      JsonNumber(NormalizeSymbolPrice(command.stop_loss), _Digits) + ",";
   payload += "\"expectedTakeProfit\":" +
      JsonNumber(NormalizeSymbolPrice(command.take_profit), _Digits) + ",";
   payload += "\"orderId\":" +
      JsonString(StringFormat("%I64u", result.order)) + ",";
   payload += "\"dealId\":" +
      JsonString(StringFormat("%I64u", result.deal)) + ",";
   payload += "\"requestId\":" +
      JsonString(StringFormat("%u", result.request_id)) + ",";
   payload += "\"retcode\":" +
      JsonString(StringFormat("%u", result.retcode)) + ",";
   payload += "\"retcodeExternal\":" +
      JsonString(IntegerToString(result.retcode_external)) + ",";
   payload += "\"apiAccepted\":" + JsonBoolean(api_accepted) + ",";
   payload += "\"apiError\":" + JsonString(IntegerToString(api_error)) + ",";
   payload += "\"observedAt\":" + IntegerToString(NowUtc());
   payload += "}";
   return true;
}


bool WriteExecutionAttempt(
   const CommandPayload &command,
   const string signed_raw,
   const double expected_volume,
   const string stage,
   const bool api_accepted,
   const MqlTradeResult &result,
   const int api_error
)
{
   string payload = "";
   if(!BuildExecutionAttemptJson(
         command,
         signed_raw,
         expected_volume,
         stage,
         api_accepted,
         result,
         api_error,
         payload
      ))
      return false;
   return WriteCommonTextAtomic(
      ExecutionAttemptPath(command.command_id),
      payload
   );
}


bool ReadExecutionAttempt(
   const CommandPayload &command,
   const string signed_raw,
   ExecutionAttempt &attempt,
   string &reason
)
{
   ZeroMemory(attempt);
   string raw = "";
   if(!ReadCommonText(
         ExecutionAttemptPath(command.command_id),
         MaxCommandBytes,
         raw
      ))
   {
      reason = "EXECUTION_ATTEMPT_UNREADABLE";
      return false;
   }
   string keys[];
   string values[];
   int quoted[];
   if(!ParseFlatJson(raw, keys, values, quoted, reason) ||
       ArraySize(keys) != 31)
   {
      reason = "EXECUTION_ATTEMPT_SCHEMA_INVALID";
      return false;
   }
   for(int index = 0; index < ArraySize(keys); index++)
   {
      if(!IsExecutionAttemptKey(keys[index]))
      {
         reason = "EXECUTION_ATTEMPT_SCHEMA_INVALID";
         return false;
      }
   }

   string schema_version = "";
   string command_id = "";
   string idempotency_key = "";
   string channel_id = "";
   string snapshot_id = "";
   string action = "";
   string symbol = "";
   string timeframe = "";
   int bar_time = 0;
   double expected_volume = 0.0;
   double risk_capital_amount = 0.0;
   double estimated_risk_money = 0.0;
   double expected_stop_loss = 0.0;
   double expected_take_profit = 0.0;
   int observed_at = 0;
   if(!ReadRequiredString(keys, values, quoted, "schemaVersion", schema_version, reason) ||
      !ReadRequiredString(keys, values, quoted, "stage", attempt.stage, reason) ||
      !ReadRequiredString(keys, values, quoted, "commandId", command_id, reason) ||
      !ReadRequiredString(keys, values, quoted, "idempotencyKey", idempotency_key, reason) ||
      !ReadRequiredString(keys, values, quoted, "channelId", channel_id, reason) ||
      !ReadRequiredString(keys, values, quoted, "accountBindingId", attempt.account_binding_id, reason) ||
      !ReadRequiredString(keys, values, quoted, "streamKey", attempt.stream_key, reason) ||
      !ReadRequiredString(keys, values, quoted, "signedCommandDigest", attempt.signed_command_digest, reason) ||
      !ReadRequiredString(keys, values, quoted, "snapshotId", snapshot_id, reason) ||
      !ReadRequiredInteger(keys, values, quoted, "barTime", bar_time, reason) ||
      !ReadRequiredString(keys, values, quoted, "action", action, reason) ||
      !ReadRequiredString(keys, values, quoted, "symbol", symbol, reason) ||
      !ReadRequiredString(keys, values, quoted, "timeframe", timeframe, reason) ||
       !ReadRequiredString(keys, values, quoted, "brokerComment", attempt.broker_comment, reason) ||
       !ReadRequiredDouble(keys, values, quoted, "expectedVolume", expected_volume, reason) ||
       !ReadRequiredString(
          keys,
          values,
          quoted,
          "positionSizingMode",
          attempt.position_sizing_mode,
          reason
       ) ||
       !ReadRequiredDouble(
          keys,
          values,
          quoted,
          "riskPercent",
          attempt.risk_percent,
          reason
       ) ||
       !ReadRequiredString(
          keys,
          values,
          quoted,
          "riskCapitalBase",
          attempt.risk_capital_base,
          reason
       ) ||
       !ReadRequiredDouble(
          keys,
          values,
          quoted,
          "estimatedCommissionPerLot",
          attempt.estimated_commission_per_lot,
          reason
       ) ||
       !ReadRequiredDouble(keys, values, quoted, "riskCapitalAmount", risk_capital_amount, reason) ||
       !ReadRequiredDouble(keys, values, quoted, "estimatedRiskMoney", estimated_risk_money, reason) ||
      !ReadRequiredDouble(keys, values, quoted, "expectedStopLoss", expected_stop_loss, reason) ||
      !ReadRequiredDouble(keys, values, quoted, "expectedTakeProfit", expected_take_profit, reason) ||
      !ReadRequiredString(keys, values, quoted, "orderId", attempt.order_id, reason) ||
      !ReadRequiredString(keys, values, quoted, "dealId", attempt.deal_id, reason) ||
      !ReadRequiredString(keys, values, quoted, "requestId", attempt.request_id, reason) ||
      !ReadRequiredString(keys, values, quoted, "retcode", attempt.retcode, reason) ||
      !ReadRequiredString(keys, values, quoted, "retcodeExternal", attempt.retcode_external, reason) ||
      !ReadRequiredBoolean(keys, values, quoted, "apiAccepted", attempt.api_accepted, reason) ||
      !ReadRequiredString(keys, values, quoted, "apiError", attempt.api_error, reason) ||
      !ReadRequiredInteger(keys, values, quoted, "observedAt", observed_at, reason))
   {
      reason = "EXECUTION_ATTEMPT_SCHEMA_INVALID";
      return false;
   }

   string current_account_binding_id = "";
   string expected_stream_key = "";
   string expected_signed_digest = "";
   const double volume_tolerance = 0.00000001;
   double price_tolerance = MathMax(
      0.00000001,
      SymbolInfoDouble(_Symbol, SYMBOL_POINT) / 2.0
   );
   if(schema_version != EXECUTION_ATTEMPT_SCHEMA ||
      (attempt.stage != "EXECUTING" &&
       attempt.stage != "ORDER_SEND_RETURNED") ||
      command_id != command.command_id ||
      idempotency_key != command.idempotency_key ||
      channel_id != command.channel_id ||
      snapshot_id != command.snapshot_id ||
      bar_time != command.bar_time ||
      action != command.action ||
      symbol != command.symbol ||
      timeframe != command.timeframe ||
       attempt.broker_comment != "HQ:" + command.command_id ||
       !MathIsValidNumber(expected_volume) ||
       expected_volume <= 0.0 ||
       (attempt.position_sizing_mode != "FIXED_LOT" &&
        attempt.position_sizing_mode != "RISK_PERCENT") ||
       !MathIsValidNumber(attempt.risk_percent) ||
       attempt.risk_percent < 0.0 || attempt.risk_percent > 100.0 ||
       (attempt.position_sizing_mode == "RISK_PERCENT" &&
        attempt.risk_percent < 0.00000001) ||
       (attempt.risk_capital_base != "BALANCE" &&
        attempt.risk_capital_base != "EQUITY") ||
       !MathIsValidNumber(attempt.estimated_commission_per_lot) ||
       attempt.estimated_commission_per_lot < 0.0 ||
       attempt.estimated_commission_per_lot > 1000000.0 ||
       !MathIsValidNumber(risk_capital_amount) ||
       risk_capital_amount <= 0.0 ||
       !MathIsValidNumber(estimated_risk_money) ||
       estimated_risk_money < 0.00000001 ||
      MathAbs(expected_stop_loss - NormalizeSymbolPrice(command.stop_loss)) > price_tolerance ||
      MathAbs(expected_take_profit - NormalizeSymbolPrice(command.take_profit)) > price_tolerance ||
      !ProtocolAccountBindingId(current_account_binding_id) ||
      attempt.account_binding_id != current_account_binding_id ||
      !ProtocolStreamKey(command, expected_stream_key) ||
      attempt.stream_key != expected_stream_key ||
      !SignedCommandDigest(signed_raw, expected_signed_digest) ||
      attempt.signed_command_digest != expected_signed_digest ||
      !IsUnsignedIntegerText(attempt.order_id) ||
      !IsUnsignedIntegerText(attempt.deal_id) ||
      !IsUnsignedIntegerText(attempt.request_id) ||
      !IsUnsignedIntegerText(attempt.retcode) ||
      !IsSignedIntegerText(attempt.retcode_external) ||
      !IsSignedIntegerText(attempt.api_error) ||
      observed_at < 946684800)
   {
      reason = "EXECUTION_ATTEMPT_IDENTITY_MISMATCH";
      return false;
   }
   attempt.expected_volume = expected_volume;
   attempt.risk_capital_amount = risk_capital_amount;
   attempt.estimated_risk_money = estimated_risk_money;
   return true;
}


void FinalizeCommand(
   const CommandPayload &command,
   const string status,
   const string reason_code,
   const ulong ticket,
   const int error_code
)
{
   string first_payload = BuildAckJson(
      command,
      status,
      reason_code,
      ticket,
      error_code,
      true
   );
   bool state_persisted = WriteExecutionMarkers(command, first_payload);
   string payload = BuildAckJson(
      command,
      status,
      reason_code,
      ticket,
      error_code,
      state_persisted
   );
   if(state_persisted)
      WriteExecutionMarkers(command, payload);
   WriteCommonTextAtomic(AckPath(command.command_id), payload);
   AppendAudit(payload);
   Print(
      "MetafxHQ Trade Gateway ",
      status,
      " ",
      reason_code,
      " command=",
      command.command_id
   );
}


bool CsvContains(const string csv, const string candidate)
{
   string parts[];
   int count = StringSplit(csv, ',', parts);
   string normalized_candidate = Uppercase(Trimmed(candidate));
   for(int index = 0; index < count; index++)
   {
      if(Uppercase(Trimmed(parts[index])) == normalized_candidate)
         return true;
   }
   return false;
}


bool IsBrokerSuffixCharacter(const int code)
{
   return (code >= 'A' && code <= 'Z') ||
      (code >= '0' && code <= '9') ||
      code == '.' || code == '_' || code == '#' || code == '-';
}


bool IsBrokerNamespaceDelimiter(const int code)
{
   return code == '.' || code == '_' || code == '#' || code == '-';
}


bool IsAllowedBrokerPrefix(
   const string candidate,
   const int prefix_length
)
{
   if(prefix_length < 1 || prefix_length > 8 ||
      prefix_length > StringLen(candidate))
      return false;
   for(int index = 0; index < prefix_length; index++)
   {
      if(!IsBrokerSuffixCharacter(
            StringGetCharacter(candidate, index)
         ))
         return false;
   }

   // A single leading marker (for example mXAUUSD) is common at brokers.
   // Longer namespace prefixes must end in a delimiter, for example
   // GOLD.XAUUSD. This rejects ambiguous embedded names such as FOOXAUUSD.
   if(prefix_length == 1)
      return true;
   return IsBrokerNamespaceDelimiter(
      StringGetCharacter(candidate, prefix_length - 1)
   );
}


bool HasSingleBrokerBaseOccurrence(
   const string candidate,
   const string allowed
)
{
   // Affixes may surround one canonical base, but repeated bases such as
   // XAUUSDXAUUSD are ambiguous and must never be treated as a broker suffix.
   int first = StringFind(candidate, allowed);
   if(first < 0)
      return false;
   return StringFind(candidate, allowed, first + 1) < 0;
}


bool IsAllowedBrokerSymbol(const string csv, const string candidate)
{
   string parts[];
   int count = StringSplit(csv, ',', parts);
   string normalized_candidate = Uppercase(Trimmed(candidate));
   for(int index = 0; index < count; index++)
   {
      string allowed = Uppercase(Trimmed(parts[index]));
      if(allowed == normalized_candidate)
         return true;

      // A six-character base such as EURUSD or XAUUSD may match a bounded
      // broker prefix/suffix (for example mXAUUSD, GOLD.XAUUSD, EURUSD.m,
      // XAUUSDpro or mXAUUSD-ECN). The command must still name the exact chart
      // Symbol(), so this never permits a command to cross from one attached
      // broker symbol to another.
      int base_length = StringLen(allowed);
      int actual_length = StringLen(normalized_candidate);
      if(base_length < 6 || actual_length <= base_length ||
         actual_length > base_length + 16 ||
         !HasSingleBrokerBaseOccurrence(normalized_candidate, allowed))
         continue;

      for(int prefix_length = 0; prefix_length <= 8; prefix_length++)
      {
         int suffix_length = actual_length - prefix_length - base_length;
         if(suffix_length < 0 || suffix_length > 8 ||
            (prefix_length == 0 && suffix_length == 0) ||
            StringSubstr(
               normalized_candidate,
               prefix_length,
               base_length
            ) != allowed)
            continue;
         if(prefix_length > 0 &&
            !IsAllowedBrokerPrefix(
               normalized_candidate,
               prefix_length
            ))
            continue;

         bool suffix_valid = true;
         int suffix_start = prefix_length + base_length;
         for(int suffix_index = suffix_start;
            suffix_index < actual_length;
            suffix_index++)
         {
            if(!IsBrokerSuffixCharacter(
               StringGetCharacter(normalized_candidate, suffix_index)
            ))
            {
               suffix_valid = false;
               break;
            }
         }
         if(suffix_valid)
            return true;
      }
   }
   return false;
}


bool IsManagedMagic(const int magic_number)
{
   string parts[];
   int count = StringSplit(ManagedMagicNumbers, ',', parts);
   for(int index = 0; index < count; index++)
   {
      string token = Trimmed(parts[index]);
      if(IsIntegerToken(token) && (int)StringToInteger(token) == magic_number)
         return true;
   }
   return false;
}


bool ValidateManagedMagicConfiguration(string &reason)
{
   string parts[];
   int count = StringSplit(ManagedMagicNumbers, ',', parts);
   if(count < 1 || count > 32)
   {
      reason = "MANAGED_MAGIC_LIST_INVALID";
      return false;
   }
   for(int index = 0; index < count; index++)
   {
      string token = Trimmed(parts[index]);
      if(!IsIntegerToken(token) || StringToInteger(token) <= 0)
      {
         reason = "MANAGED_MAGIC_LIST_INVALID";
         return false;
      }
      for(int other = index + 1; other < count; other++)
      {
         if(Trimmed(parts[other]) == token)
         {
            reason = "MANAGED_MAGIC_LIST_DUPLICATE";
            return false;
         }
      }
   }
   if(!IsManagedMagic(MagicNumber))
   {
      reason = "CURRENT_MAGIC_NOT_IN_MANAGED_PORTFOLIO";
      return false;
   }
   return true;
}



bool NormalizeAllowedSymbolsCsv(
   const string csv,
   string &normalized
)
{
   normalized = "";
   string parts[];
   int count = StringSplit(csv, ',', parts);
   if(count < 1 || count > 64)
      return false;
   for(int index = 0; index < count; index++)
   {
      string token = Uppercase(Trimmed(parts[index]));
      int length = StringLen(token);
      if(length < 2 || length > 24)
         return false;
      for(int character = 0; character < length; character++)
      {
         int code = StringGetCharacter(token, character);
         bool allowed =
            (code >= 'A' && code <= 'Z') ||
            (code >= '0' && code <= '9') ||
            code == '.' || code == '_' || code == '#' || code == '-';
         if(!allowed)
            return false;
      }
      for(int earlier = 0; earlier < index; earlier++)
      {
         if(Uppercase(Trimmed(parts[earlier])) == token)
            return false;
      }
      if(index > 0)
         normalized += ",";
      normalized += token;
   }
   return StringLen(normalized) > 0;
}


bool NormalizeAllowedTimeframesCsv(
   const string csv,
   string &normalized
)
{
   normalized = "";
   string parts[];
   int count = StringSplit(csv, ',', parts);
   if(count < 1 || count > 8)
      return false;
   for(int index = 0; index < count; index++)
   {
      string token = Uppercase(Trimmed(parts[index]));
      if(token != "M5" && token != "M15" && token != "M30" &&
         token != "H1" && token != "H4" && token != "D1" &&
         token != "W1" && token != "MN1")
         return false;
      for(int earlier = 0; earlier < index; earlier++)
      {
         if(Uppercase(Trimmed(parts[earlier])) == token)
            return false;
      }
      if(index > 0)
         normalized += ",";
      normalized += token;
   }
   return StringLen(normalized) > 0;
}


int TimeframeToPeriod(const string timeframe)
{
   string normalized = Uppercase(timeframe);
   if(normalized == "M5")
      return PERIOD_M5;
   if(normalized == "M15")
      return PERIOD_M15;
   if(normalized == "M30")
      return PERIOD_M30;
   if(normalized == "H1")
      return PERIOD_H1;
   if(normalized == "H4")
      return PERIOD_H4;
   if(normalized == "D1")
      return PERIOD_D1;
   if(normalized == "W1")
      return PERIOD_W1;
   if(normalized == "MN1")
      return PERIOD_MN1;
   return 0;
}


string CurrentTimeframeName()
{
   if(_Period == PERIOD_M5)
      return "M5";
   if(_Period == PERIOD_M15)
      return "M15";
   if(_Period == PERIOD_M30)
      return "M30";
   if(_Period == PERIOD_H1)
      return "H1";
   if(_Period == PERIOD_H4)
      return "H4";
   if(_Period == PERIOD_D1)
      return "D1";
   if(_Period == PERIOD_W1)
      return "W1";
   if(_Period == PERIOD_MN1)
      return "MN1";
   return "UNSUPPORTED";
}


bool IsHedgingAccount()
{
   ENUM_ACCOUNT_MARGIN_MODE margin_mode =
      (ENUM_ACCOUNT_MARGIN_MODE)AccountInfoInteger(ACCOUNT_MARGIN_MODE);
   return margin_mode == ACCOUNT_MARGIN_MODE_RETAIL_HEDGING;
}


datetime BrokerDayStart()
{
   datetime broker_now = TimeCurrent();
   MqlDateTime parts;
   if(broker_now <= 0 || !TimeToStruct(broker_now, parts))
      return 0;
   parts.hour = 0;
   parts.min = 0;
   parts.sec = 0;
   return StructToTime(parts);
}


bool UlongArrayContains(const ulong &values[], const ulong candidate)
{
   for(int index = 0; index < ArraySize(values); index++)
   {
      if(values[index] == candidate)
         return true;
   }
   return false;
}


bool ReadHistoryDealIntegerStrict(
   const ulong ticket,
   const ENUM_DEAL_PROPERTY_INTEGER property_id,
   long &value
)
{
   value = 0;
   ResetLastError();
   return HistoryDealGetInteger(ticket, property_id, value);
}


bool ReadHistoryDealDoubleStrict(
   const ulong ticket,
   const ENUM_DEAL_PROPERTY_DOUBLE property_id,
   double &value
)
{
   value = 0.0;
   ResetLastError();
   return HistoryDealGetDouble(ticket, property_id, value);
}


bool ReadSnapshotDailySummary(
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
   datetime now = TimeCurrent();
   if(day_start <= 0 || now <= 0 || !HistorySelect(day_start, now))
      return false;
   int total = HistoryDealsTotal();
   if(total < 0)
      return false;
   for(int index = 0; index < total; index++)
   {
      ulong deal_ticket = HistoryDealGetTicket(index);
      if(deal_ticket == 0)
         return false;
      long deal_type_value = 0;
      long entry_value = 0;
      if(!ReadHistoryDealIntegerStrict(
            deal_ticket,
            DEAL_TYPE,
            deal_type_value
         ) ||
         !ReadHistoryDealIntegerStrict(
            deal_ticket,
            DEAL_ENTRY,
            entry_value
         ))
         return false;
      ENUM_DEAL_TYPE deal_type =
         (ENUM_DEAL_TYPE)deal_type_value;
      ENUM_DEAL_ENTRY entry =
         (ENUM_DEAL_ENTRY)entry_value;
      if((deal_type != DEAL_TYPE_BUY && deal_type != DEAL_TYPE_SELL) ||
         (entry != DEAL_ENTRY_OUT && entry != DEAL_ENTRY_OUT_BY))
         continue;
      double profit = 0.0;
      double swap = 0.0;
      double commission = 0.0;
      double fee = 0.0;
      if(!ReadHistoryDealDoubleStrict(deal_ticket, DEAL_PROFIT, profit) ||
         !ReadHistoryDealDoubleStrict(deal_ticket, DEAL_SWAP, swap) ||
         !ReadHistoryDealDoubleStrict(deal_ticket, DEAL_COMMISSION, commission) ||
         !ReadHistoryDealDoubleStrict(deal_ticket, DEAL_FEE, fee))
         return false;
      double result = profit + swap + commission + fee;
      realized_profit += result;
      trades_closed++;
      if(result > 0.0)
         wins++;
      else if(result < 0.0)
         losses++;
   }
   return true;
}


bool ReadSelectedPositionIntegerStrict(
   const ENUM_POSITION_PROPERTY_INTEGER property_id,
   long &value
)
{
   value = 0;
   ResetLastError();
   return PositionGetInteger(property_id, value);
}


bool ReadSelectedPositionDoubleStrict(
   const ENUM_POSITION_PROPERTY_DOUBLE property_id,
   double &value
)
{
   value = 0.0;
   ResetLastError();
   return PositionGetDouble(property_id, value);
}


bool ReadSnapshotPositionSummary(
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
   int total = PositionsTotal();
   for(int index = 0; index < total; index++)
   {
      ulong ticket = PositionGetTicket(index);
      if(ticket == 0)
         return false;
      long type_value = 0;
      double volume = 0.0;
      double profit = 0.0;
      double swap = 0.0;
      if(!ReadSelectedPositionIntegerStrict(POSITION_TYPE, type_value) ||
         !ReadSelectedPositionDoubleStrict(POSITION_VOLUME, volume) ||
         !ReadSelectedPositionDoubleStrict(POSITION_PROFIT, profit) ||
         !ReadSelectedPositionDoubleStrict(POSITION_SWAP, swap))
         return false;
      if(!MathIsValidNumber(volume) || volume <= 0.0 ||
         !MathIsValidNumber(profit) || !MathIsValidNumber(swap))
         return false;
      ENUM_POSITION_TYPE type =
         (ENUM_POSITION_TYPE)type_value;
      if(type != POSITION_TYPE_BUY && type != POSITION_TYPE_SELL)
         continue;
      position_count++;
      if(type == POSITION_TYPE_BUY)
         buy_count++;
      else
         sell_count++;
      total_lots += volume;
      floating_profit += profit + swap;
      if(!MathIsValidNumber(total_lots) || total_lots < 0.0 ||
         !MathIsValidNumber(floating_profit))
         return false;
   }
   return true;
}


bool ReadManagedOpenState(
   int &positions,
   double &lots,
   double &floating_pnl
)
{
   positions = 0;
   lots = 0.0;
   floating_pnl = 0.0;
   int total = PositionsTotal();
   for(int index = 0; index < total; index++)
   {
      ulong ticket = PositionGetTicket(index);
      if(ticket == 0)
         return false;
      long magic = 0;
      if(!ReadSelectedPositionIntegerStrict(POSITION_MAGIC, magic))
         return false;
      if(magic < 1 || magic > 2147483647 ||
         !IsManagedMagic((int)magic))
         continue;
      double volume = 0.0;
      double profit = 0.0;
      double swap = 0.0;
      if(!ReadSelectedPositionDoubleStrict(POSITION_VOLUME, volume) ||
         !ReadSelectedPositionDoubleStrict(POSITION_PROFIT, profit) ||
         !ReadSelectedPositionDoubleStrict(POSITION_SWAP, swap))
         return false;
      if(!MathIsValidNumber(volume) || volume <= 0.0 ||
         !MathIsValidNumber(profit) || !MathIsValidNumber(swap))
         return false;
      positions++;
      lots += volume;
      floating_pnl += profit + swap;
      if(!MathIsValidNumber(lots) || lots < 0.0 ||
         !MathIsValidNumber(floating_pnl))
         return false;
   }
   return true;
}


bool CountManagedTradesSince(const datetime since, int &count)
{
   count = 0;
   datetime now = TimeCurrent();
   if(since <= 0 || now <= 0 || !HistorySelect(since, now))
      return false;
   ulong seen_positions[];
   ArrayResize(seen_positions, 0);
   int total = HistoryDealsTotal();
   if(total < 0)
      return false;
   for(int index = 0; index < total; index++)
   {
      ulong deal_ticket = HistoryDealGetTicket(index);
      if(deal_ticket == 0)
         return false;
      long entry_value = 0;
      long type_value = 0;
      long magic = 0;
      if(!ReadHistoryDealIntegerStrict(deal_ticket, DEAL_ENTRY, entry_value) ||
         !ReadHistoryDealIntegerStrict(deal_ticket, DEAL_TYPE, type_value) ||
         !ReadHistoryDealIntegerStrict(deal_ticket, DEAL_MAGIC, magic))
         return false;
      ENUM_DEAL_ENTRY entry =
         (ENUM_DEAL_ENTRY)entry_value;
      ENUM_DEAL_TYPE type =
         (ENUM_DEAL_TYPE)type_value;
      if(entry != DEAL_ENTRY_IN ||
         (type != DEAL_TYPE_BUY && type != DEAL_TYPE_SELL) ||
         magic < 1 || magic > 2147483647 ||
         !IsManagedMagic((int)magic))
         continue;
      long position_id_value = 0;
      if(!ReadHistoryDealIntegerStrict(
            deal_ticket,
            DEAL_POSITION_ID,
            position_id_value
         ))
         return false;
      ulong position_id = (ulong)position_id_value;
      if(position_id == 0 || UlongArrayContains(seen_positions, position_id))
         continue;
      int size = ArraySize(seen_positions);
      if(ArrayResize(seen_positions, size + 1) != size + 1)
         return false;
      seen_positions[size] = position_id;
   }
   count = ArraySize(seen_positions);
   return true;
}


bool CountManagedTradesToday(int &count)
{
   return CountManagedTradesSince(BrokerDayStart(), count);
}


bool IsBrokerCostDealType(const ENUM_DEAL_TYPE type)
{
   return type == DEAL_TYPE_CHARGE ||
      type == DEAL_TYPE_CORRECTION ||
      type == DEAL_TYPE_COMMISSION ||
      type == DEAL_TYPE_COMMISSION_DAILY ||
      type == DEAL_TYPE_COMMISSION_MONTHLY ||
      type == DEAL_TYPE_COMMISSION_AGENT_DAILY ||
      type == DEAL_TYPE_COMMISSION_AGENT_MONTHLY ||
      type == DEAL_TYPE_INTEREST ||
      type == DEAL_TYPE_BUY_CANCELED ||
      type == DEAL_TYPE_SELL_CANCELED;
}


bool ManagedPnlSince(const datetime since, double &pnl)
{
   pnl = 0.0;
   datetime now = TimeCurrent();
   if(since <= 0 || now <= 0 || !HistorySelect(since, now))
      return false;
   int total = HistoryDealsTotal();
   if(total < 0)
      return false;
   ulong managed_positions[];
   ulong managed_orders[];
   for(int index = 0; index < total; index++)
   {
      ulong deal_ticket = HistoryDealGetTicket(index);
      if(deal_ticket == 0)
         return false;
      long type_value = 0;
      long magic = 0;
      long position_id_value = 0;
      long order_id_value = 0;
      if(!ReadHistoryDealIntegerStrict(deal_ticket, DEAL_TYPE, type_value) ||
         !ReadHistoryDealIntegerStrict(deal_ticket, DEAL_MAGIC, magic) ||
         !ReadHistoryDealIntegerStrict(deal_ticket, DEAL_POSITION_ID, position_id_value) ||
         !ReadHistoryDealIntegerStrict(deal_ticket, DEAL_ORDER, order_id_value))
         return false;
      ENUM_DEAL_TYPE type =
         (ENUM_DEAL_TYPE)type_value;
      if((type != DEAL_TYPE_BUY && type != DEAL_TYPE_SELL) ||
         magic < 1 || magic > 2147483647 ||
         !IsManagedMagic((int)magic))
         continue;
      ulong position_id = (ulong)position_id_value;
      ulong order_id = (ulong)order_id_value;
      if(position_id > 0 &&
         !UlongArrayContains(managed_positions, position_id))
      {
         int size = ArraySize(managed_positions);
         if(ArrayResize(managed_positions, size + 1) != size + 1)
            return false;
         managed_positions[size] = position_id;
      }
      if(order_id > 0 && !UlongArrayContains(managed_orders, order_id))
      {
         int size = ArraySize(managed_orders);
         if(ArrayResize(managed_orders, size + 1) != size + 1)
            return false;
         managed_orders[size] = order_id;
      }
   }

   for(int index = 0; index < total; index++)
   {
      ulong deal_ticket = HistoryDealGetTicket(index);
      if(deal_ticket == 0)
         return false;
      long type_value = 0;
      long magic = 0;
      long position_id_value = 0;
      long order_id_value = 0;
      if(!ReadHistoryDealIntegerStrict(deal_ticket, DEAL_TYPE, type_value) ||
         !ReadHistoryDealIntegerStrict(deal_ticket, DEAL_MAGIC, magic) ||
         !ReadHistoryDealIntegerStrict(deal_ticket, DEAL_POSITION_ID, position_id_value) ||
         !ReadHistoryDealIntegerStrict(deal_ticket, DEAL_ORDER, order_id_value))
         return false;
      ENUM_DEAL_TYPE type = (ENUM_DEAL_TYPE)type_value;
      double profit = 0.0;
      double swap = 0.0;
      double commission = 0.0;
      double fee = 0.0;
      if(!ReadHistoryDealDoubleStrict(deal_ticket, DEAL_PROFIT, profit) ||
         !ReadHistoryDealDoubleStrict(deal_ticket, DEAL_SWAP, swap) ||
         !ReadHistoryDealDoubleStrict(deal_ticket, DEAL_COMMISSION, commission) ||
         !ReadHistoryDealDoubleStrict(deal_ticket, DEAL_FEE, fee))
         return false;
      double result = profit + swap + commission + fee;
      bool managed_trade =
         (type == DEAL_TYPE_BUY || type == DEAL_TYPE_SELL) &&
         magic >= 1 && magic <= 2147483647 &&
         IsManagedMagic((int)magic);
      bool linked_to_managed_lifecycle =
         UlongArrayContains(managed_positions, (ulong)position_id_value) ||
         UlongArrayContains(managed_orders, (ulong)order_id_value);
      if(managed_trade || linked_to_managed_lifecycle)
      {
         pnl += result;
         continue;
      }
      // Broker costs may have magic=0 and no usable position/order link.  A
      // negative account-level adjustment is included conservatively so a
      // missing attribution can only tighten, never relax, the loss caps.
      if(type != DEAL_TYPE_BUY && type != DEAL_TYPE_SELL && result < 0.0)
      {
         if(IsBrokerCostDealType(type) || !linked_to_managed_lifecycle)
            pnl += result;
      }
   }
   return true;
}


bool ManagedDailyPnl(double &pnl)
{
   return ManagedPnlSince(BrokerDayStart(), pnl);
}


bool ManagedWeeklyPnl(double &pnl)
{
   return ManagedPnlSince(BrokerWeekStart(), pnl);
}


bool ManagedRiskPnlIncludingFloatingLoss(
   const double realized_pnl,
   const double floating_pnl,
   double &risk_pnl
)
{
   if(!MathIsValidNumber(realized_pnl) ||
      !MathIsValidNumber(floating_pnl))
      return false;
   // Open managed losses consume both the daily and weekly loss budgets.
   // Floating profit is deliberately not allowed to offset realized loss:
   // until that profit is closed it cannot relax a fail-closed loss guard.
   risk_pnl = realized_pnl + MathMin(0.0, floating_pnl);
   return MathIsValidNumber(risk_pnl);
}


bool HistoryPositionIsManaged(
   const ulong position_id,
   const int total,
   bool &is_managed
)
{
   is_managed = false;
   if(position_id == 0)
      return true;
   for(int index = 0; index < total; index++)
   {
      ulong deal_ticket = HistoryDealGetTicket(index);
      if(deal_ticket == 0)
         return false;
      long candidate_position = 0;
      if(!ReadHistoryDealIntegerStrict(
            deal_ticket,
            DEAL_POSITION_ID,
            candidate_position
         ))
         return false;
      if((ulong)candidate_position != position_id)
         continue;
      long type_value = 0;
      long magic = 0;
      if(!ReadHistoryDealIntegerStrict(deal_ticket, DEAL_TYPE, type_value) ||
         !ReadHistoryDealIntegerStrict(deal_ticket, DEAL_MAGIC, magic))
         return false;
      ENUM_DEAL_TYPE type = (ENUM_DEAL_TYPE)type_value;
      if((type == DEAL_TYPE_BUY || type == DEAL_TYPE_SELL) &&
         magic >= 1 && magic <= 2147483647 &&
         IsManagedMagic((int)magic))
      {
         is_managed = true;
         return true;
      }
   }
   return true;
}


bool ManagedPositionLifecyclePnl(
   const ulong position_id,
   const int total,
   double &result,
   int &latest_exit_time
)
{
   result = 0.0;
   latest_exit_time = 0;
   bool saw_entry = false;
   if(position_id == 0)
      return false;
   for(int index = 0; index < total; index++)
   {
      ulong deal_ticket = HistoryDealGetTicket(index);
      if(deal_ticket == 0)
         return false;
      long candidate_position = 0;
      if(!ReadHistoryDealIntegerStrict(
            deal_ticket,
            DEAL_POSITION_ID,
            candidate_position
         ))
         return false;
      if((ulong)candidate_position != position_id)
         continue;
      long entry_value = 0;
      long time_value = 0;
      double profit = 0.0;
      double swap = 0.0;
      double commission = 0.0;
      double fee = 0.0;
      if(!ReadHistoryDealIntegerStrict(deal_ticket, DEAL_ENTRY, entry_value) ||
         !ReadHistoryDealIntegerStrict(deal_ticket, DEAL_TIME, time_value) ||
         !ReadHistoryDealDoubleStrict(deal_ticket, DEAL_PROFIT, profit) ||
         !ReadHistoryDealDoubleStrict(deal_ticket, DEAL_SWAP, swap) ||
         !ReadHistoryDealDoubleStrict(deal_ticket, DEAL_COMMISSION, commission) ||
         !ReadHistoryDealDoubleStrict(deal_ticket, DEAL_FEE, fee))
         return false;
      result += profit + swap + commission + fee;
      ENUM_DEAL_ENTRY entry = (ENUM_DEAL_ENTRY)entry_value;
      if(entry == DEAL_ENTRY_IN || entry == DEAL_ENTRY_INOUT)
         saw_entry = true;
      if((entry == DEAL_ENTRY_OUT || entry == DEAL_ENTRY_OUT_BY) &&
         time_value > latest_exit_time)
         latest_exit_time = (int)time_value;
   }
   // A position opened before the bounded streak horizon would otherwise
   // expose only its exit-side P/L and could be classified incorrectly.
   // Treat that history as incomplete and fail closed.
   return saw_entry && latest_exit_time > 0;
}


bool ReadManagedLossStreak(
   int &loss_count,
   int &cooldown_until
)
{
   loss_count = 0;
   cooldown_until = 0;
   datetime now = TimeCurrent();
   // A true consecutive streak can cross a broker day/week boundary and can
   // contain long gaps. Select the complete available broker history, then
   // walk backward only until a non-loss or the configured cap proves the
   // current streak. Missing lifecycle entry data fails closed below.
   if(now <= 0 || !HistorySelect(0, now))
      return false;
   int total = HistoryDealsTotal();
   if(total < 0)
      return false;
   int most_recent_loss_time = 0;
   ulong seen_positions[];
   for(int index = total - 1; index >= 0; index--)
   {
      ulong deal_ticket = HistoryDealGetTicket(index);
      if(deal_ticket == 0)
         return false;
      long type_value = 0;
      long entry_value = 0;
      long magic = 0;
      long position_id_value = 0;
      if(!ReadHistoryDealIntegerStrict(deal_ticket, DEAL_TYPE, type_value) ||
         !ReadHistoryDealIntegerStrict(deal_ticket, DEAL_ENTRY, entry_value) ||
         !ReadHistoryDealIntegerStrict(deal_ticket, DEAL_MAGIC, magic) ||
         !ReadHistoryDealIntegerStrict(
            deal_ticket,
            DEAL_POSITION_ID,
            position_id_value
         ))
         return false;
      ENUM_DEAL_TYPE type =
         (ENUM_DEAL_TYPE)type_value;
      ENUM_DEAL_ENTRY entry =
         (ENUM_DEAL_ENTRY)entry_value;
      ulong position_id = (ulong)position_id_value;
      bool managed_exit =
         (type == DEAL_TYPE_BUY || type == DEAL_TYPE_SELL) &&
         (entry == DEAL_ENTRY_OUT || entry == DEAL_ENTRY_OUT_BY) &&
         magic >= 1 && magic <= 2147483647 &&
         IsManagedMagic((int)magic);
      if(managed_exit)
      {
         if(position_id == 0)
            return false;
         if(UlongArrayContains(seen_positions, position_id))
            continue;
         int size = ArraySize(seen_positions);
         if(ArrayResize(seen_positions, size + 1) != size + 1)
            return false;
         seen_positions[size] = position_id;
         double lifecycle_result = 0.0;
         int lifecycle_close_time = 0;
         if(!ManagedPositionLifecyclePnl(
               position_id,
               total,
               lifecycle_result,
               lifecycle_close_time
            ))
            return false;
         if(lifecycle_result >= 0.0)
            break;
         loss_count++;
         if(most_recent_loss_time == 0)
            most_recent_loss_time = lifecycle_close_time;
         if(loss_count >= MaxConsecutiveManagedLosses)
            break;
         continue;
      }

      double profit = 0.0;
      double swap = 0.0;
      double commission = 0.0;
      double fee = 0.0;
      if(!ReadHistoryDealDoubleStrict(deal_ticket, DEAL_PROFIT, profit) ||
         !ReadHistoryDealDoubleStrict(deal_ticket, DEAL_SWAP, swap) ||
         !ReadHistoryDealDoubleStrict(deal_ticket, DEAL_COMMISSION, commission) ||
         !ReadHistoryDealDoubleStrict(deal_ticket, DEAL_FEE, fee))
         return false;
      double result = profit + swap + commission + fee;
      if(type == DEAL_TYPE_BUY || type == DEAL_TYPE_SELL || result >= 0.0)
         continue;
      bool linked_position_is_managed = false;
      if(!HistoryPositionIsManaged(
            position_id,
            total,
            linked_position_is_managed
         ))
         return false;
      if(linked_position_is_managed)
         continue;
      // An unlinked negative charge cannot safely be assigned to another
      // strategy.  Treat it as a conservative loss event instead of letting
      // the consecutive-loss cooldown read a false zero.
      loss_count++;
      if(most_recent_loss_time == 0)
      {
         long deal_time_value = 0;
         if(!ReadHistoryDealIntegerStrict(
               deal_ticket,
               DEAL_TIME,
               deal_time_value
            ))
            return false;
         most_recent_loss_time = (int)deal_time_value;
      }
      if(loss_count >= MaxConsecutiveManagedLosses)
         break;
   }
   if(loss_count >= MaxConsecutiveManagedLosses &&
      most_recent_loss_time > 0)
   {
      cooldown_until =
         most_recent_loss_time + ConsecutiveLossCooldownMinutes * 60;
   }
   return true;
}


bool CurrentAccountDrawdownPercent(double &drawdown_percent)
{
   drawdown_percent = 0.0;
   double balance = AccountInfoDouble(ACCOUNT_BALANCE);
   double equity = AccountInfoDouble(ACCOUNT_EQUITY);
   if(!MathIsValidNumber(balance) || balance <= 0.0 ||
      !MathIsValidNumber(equity) || equity < 0.0)
      return false;
   if(equity < balance)
      drawdown_percent = (balance - equity) / balance * 100.0;
   return MathIsValidNumber(drawdown_percent) && drawdown_percent >= 0.0;
}


bool CurrentMarginLevelPercent(double &margin_level_percent)
{
   margin_level_percent = 0.0;
   double margin = AccountInfoDouble(ACCOUNT_MARGIN);
   double equity = AccountInfoDouble(ACCOUNT_EQUITY);
   if(!MathIsValidNumber(margin) || margin < 0.0 ||
      !MathIsValidNumber(equity) || equity <= 0.0)
      return false;
   if(margin == 0.0)
   {
      margin_level_percent = 999999.0;
      return true;
   }
   double level = AccountInfoDouble(ACCOUNT_MARGIN_LEVEL);
   if(level > 0.0 && MathIsValidNumber(level))
      margin_level_percent = level;
   else
      margin_level_percent = equity / margin * 100.0;
   return MathIsValidNumber(margin_level_percent) &&
      margin_level_percent > 0.0;
}


bool SnapshotMarketOpen(
   const MqlTick &tick,
   const bool tick_available
)
{
   if(!IsConnected() || !tick_available ||
      tick.bid <= 0.0 || tick.ask <= tick.bid)
      return false;
   ENUM_SYMBOL_TRADE_MODE trade_mode =
      (ENUM_SYMBOL_TRADE_MODE)SymbolInfoInteger(
         _Symbol,
         SYMBOL_TRADE_MODE
      );
   if(trade_mode == SYMBOL_TRADE_MODE_DISABLED)
      return false;
   datetime server_now = TimeCurrent();
   return tick.time > 0 &&
      server_now > 0 &&
      server_now >= tick.time &&
      server_now - tick.time <= MaxQuoteAgeSeconds;
}


string BuildSnapshotBarsJson()
{
   int requested = MathMax(20, MathMin(SnapshotBars, 1000));
   MqlRates rates[];
   ArraySetAsSeries(rates, false);
   int copied = CopyRates(_Symbol, _Period, 1, requested, rates);
   if(copied <= 0)
      return "[]";
   string rows = "[";
   for(int index = 0; index < copied; index++)
   {
      if(index > 0)
         rows += ",";
      rows += "{";
      rows += "\"time\":" +
         StringFormat("%I64d", (long)rates[index].time) + ",";
      rows += "\"open\":" + JsonNumber(rates[index].open, _Digits) + ",";
      rows += "\"high\":" + JsonNumber(rates[index].high, _Digits) + ",";
      rows += "\"low\":" + JsonNumber(rates[index].low, _Digits) + ",";
      rows += "\"close\":" + JsonNumber(rates[index].close, _Digits) + ",";
      rows += "\"volume\":" +
         StringFormat("%I64d", rates[index].tick_volume);
      rows += "}";
   }
   rows += "]";
   return rows;
}


bool BuildSnapshotJson(string &payload)
{
   payload = "";
   if(!UpdateRiskTelemetry(false))
      return false;
   MqlTick tick;
   ZeroMemory(tick);
   bool tick_available = SymbolInfoTick(_Symbol, tick);

   double realized_profit = 0.0;
   int trades_closed = 0;
   int wins = 0;
   int losses = 0;
   if(!ReadSnapshotDailySummary(
      realized_profit,
      trades_closed,
      wins,
      losses
   ))
      return false;
   string account_binding_id = "";
   if(!ProtocolAccountBindingId(account_binding_id))
      return false;

   int position_count = 0;
   int buy_count = 0;
   int sell_count = 0;
   double total_lots = 0.0;
   double floating_profit = 0.0;
   if(!ReadSnapshotPositionSummary(
      position_count,
      buy_count,
      sell_count,
      total_lots,
      floating_profit
   ))
      return false;

   double point = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
   double spread_points =
      point > 0.0 && tick.ask >= tick.bid
      ? (tick.ask - tick.bid) / point
      : 0.0;
   string server_day = TimeToString(BrokerDayStart(), TIME_DATE);
   payload = "{";
   payload += "\"schemaVersion\":" + JsonString(SNAPSHOT_SCHEMA) + ",";
   payload += "\"adapterId\":" + JsonString(SnapshotChannel) + ",";
   payload += "\"mode\":\"read_only\",";
   payload += "\"terminalPlatform\":\"mt5\",";
   payload += "\"accountBindingId\":" +
      JsonString(account_binding_id) + ",";
   payload += "\"chart\":{";
   payload += "\"symbol\":" + JsonString(_Symbol) + ",";
   payload += "\"timeframe\":" + JsonString(CurrentTimeframeName()) + ",";
   payload += "\"bid\":" + JsonNumber(tick.bid, _Digits) + ",";
   payload += "\"ask\":" + JsonNumber(tick.ask, _Digits) + ",";
   payload += "\"spreadPoints\":" + JsonNumber(spread_points, 2) + ",";
   bool market_open = SnapshotMarketOpen(tick, tick_available);
   payload += "\"marketOpen\":" + JsonBoolean(market_open) + ",";
   payload += "\"marketSession\":" +
      JsonString(
         market_open ? "BROKER_FEED_ACTIVE" : "BROKER_FEED_INACTIVE"
      ) + ",";
   payload += "\"bars\":" + BuildSnapshotBarsJson();
   payload += "},";
   payload += "\"daily\":{";
   payload += "\"scope\":\"ACCOUNT_WIDE\",";
   payload += "\"serverDay\":" + JsonString(server_day) + ",";
   payload += "\"realizedProfit\":" + JsonNumber(realized_profit, 2) + ",";
   payload += "\"floatingProfit\":" + JsonNumber(floating_profit, 2) + ",";
   payload += "\"netPnl\":" +
      JsonNumber(realized_profit + floating_profit, 2) + ",";
   payload += "\"tradesClosed\":" + IntegerToString(trades_closed) + ",";
   payload += "\"wins\":" + IntegerToString(wins) + ",";
   payload += "\"losses\":" + IntegerToString(losses);
   payload += "},";
   payload += "\"accountSummary\":{";
   payload += "\"currency\":" +
      JsonString(AccountInfoString(ACCOUNT_CURRENCY)) + ",";
   payload += "\"balance\":" +
      JsonNumber(AccountInfoDouble(ACCOUNT_BALANCE), 2) + ",";
   payload += "\"equity\":" +
      JsonNumber(AccountInfoDouble(ACCOUNT_EQUITY), 2) + ",";
   payload += "\"margin\":" +
      JsonNumber(AccountInfoDouble(ACCOUNT_MARGIN), 2) + ",";
   payload += "\"freeMargin\":" +
      JsonNumber(AccountInfoDouble(ACCOUNT_MARGIN_FREE), 2);
   payload += "},";
   payload += "\"positionsSummary\":{";
   payload += "\"scope\":\"ACCOUNT_WIDE\",";
   payload += "\"count\":" + IntegerToString(position_count) + ",";
   payload += "\"buyCount\":" + IntegerToString(buy_count) + ",";
   payload += "\"sellCount\":" + IntegerToString(sell_count) + ",";
   payload += "\"totalLots\":" + JsonNumber(total_lots, LotDigits()) + ",";
   payload += "\"floatingProfit\":" + JsonNumber(floating_profit, 2);
   payload += "},";
   payload += "\"managedSummary\":{";
   payload += "\"scope\":\"MANAGED_MAGIC_NUMBERS_ACCOUNT_WIDE\",";
   payload += "\"managedMagicNumbers\":" +
      JsonString(ManagedMagicNumbers) + ",";
   payload += "\"positionCount\":" +
      IntegerToString(g_cached_managed_positions) + ",";
   payload += "\"totalLots\":" +
      JsonNumber(g_cached_managed_lots, LotDigits()) + ",";
   payload += "\"dailyPnl\":" +
      JsonNumber(g_cached_managed_daily_pnl, 2) + ",";
   payload += "\"weeklyPnl\":" +
      JsonNumber(g_cached_managed_weekly_pnl, 2) + ",";
   payload += "\"consecutiveLosses\":" +
      IntegerToString(g_cached_consecutive_losses) + ",";
   payload += "\"cooldownUntil\":" +
      IntegerToString(g_cached_cooldown_until) + ",";
   payload += "\"lifecycleMode\":\"SLTP_ONLY\"";
   payload += "}";
   payload += "}";
   return true;
}


bool WriteSnapshot()
{
   g_last_snapshot_attempt_at = NowUtc();
   string payload = "";
   bool ok = BuildSnapshotJson(payload) &&
      WriteCommonTextAtomic(SnapshotPath(), payload);
   g_last_snapshot_write_ok = ok;
   if(ok)
      g_last_snapshot_success_at = g_last_snapshot_attempt_at;
   return ok;
}


bool IsSnapshotDue(const int now_utc)
{
   return g_last_snapshot_attempt_at <= 0 ||
      now_utc - g_last_snapshot_attempt_at >= SnapshotIntervalSeconds;
}


void PublishSnapshotIfDue(const bool force)
{
   int now = NowUtc();
   if(force || IsSnapshotDue(now))
      WriteSnapshot();
}


string PositionSizingModeName()
{
   if(MoneyManagementMode == MONEY_MANAGEMENT_FIXED_LOT)
      return "FIXED_LOT";
   if(MoneyManagementMode == MONEY_MANAGEMENT_RISK_PERCENT)
      return "RISK_PERCENT";
   return "INVALID";
}


string RiskCapitalBaseName()
{
   if(RiskCapitalBase == RISK_CAPITAL_BALANCE)
      return "BALANCE";
   if(RiskCapitalBase == RISK_CAPITAL_EQUITY)
      return "EQUITY";
   return "INVALID";
}


double EffectiveRiskPercent()
{
   return NormalizeDouble(RiskPercent, 8);
}


double EffectiveEstimatedCommissionPerLot()
{
   if(!MathIsValidNumber(EstimatedCommissionPerLot))
      return 0.0;
   return NormalizeDouble(EstimatedCommissionPerLot, 8);
}


bool LiveCommissionPolicyConfirmed()
{
   return MathIsValidNumber(EstimatedCommissionPerLot) &&
      EstimatedCommissionPerLot >= 0.0 &&
      EstimatedCommissionPerLot <= 1000000.0 &&
      (EffectiveEstimatedCommissionPerLot() >= 0.00000001 ||
       CommissionFreeAccountConfirmed);
}


bool LiveSymbolExactAllowlistConfirmed()
{
   return CsvContains(AllowedSymbols, _Symbol);
}


bool ReadBrokerVolumeLimits(
   double &minimum,
   double &maximum,
   double &step,
   string &reason
)
{
   minimum = 0.0;
   maximum = 0.0;
   step = 0.0;
   if(!SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN, minimum) ||
      !SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX, maximum) ||
      !SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP, step) ||
      !MathIsValidNumber(minimum) ||
      !MathIsValidNumber(maximum) ||
      !MathIsValidNumber(step) ||
      minimum <= 0.0 || maximum < minimum || step <= 0.0)
   {
      reason = "BROKER_VOLUME_LIMITS_UNAVAILABLE";
      return false;
   }
   return true;
}


bool ValidateVolumeOnBrokerGrid(
   const double volume,
   const double minimum,
   const double maximum,
   const double step,
   string &reason
)
{
   if(!MathIsValidNumber(volume) ||
      volume < minimum - 0.00000001 ||
      volume > maximum + 0.00000001)
   {
      reason = "ORDER_VOLUME_OUTSIDE_BROKER_LIMITS";
      return false;
   }
   double steps = (volume - minimum) / step;
   if(MathAbs(steps - MathRound(steps)) > 0.00000001)
   {
      reason = "ORDER_VOLUME_NOT_ON_BROKER_STEP";
      return false;
   }
   return true;
}


bool ValidateFixedLot(string &reason)
{
   double minimum = 0.0;
   double maximum = 0.0;
   double step = 0.0;
   if(!ReadBrokerVolumeLimits(minimum, maximum, step, reason))
      return false;
   if(!ValidateVolumeOnBrokerGrid(
         FixedLot,
         minimum,
         maximum,
         step,
         reason
      ))
   {
      if(reason == "ORDER_VOLUME_OUTSIDE_BROKER_LIMITS")
         reason = "FIXED_LOT_OUTSIDE_BROKER_LIMITS";
      else if(reason == "ORDER_VOLUME_NOT_ON_BROKER_STEP")
         reason = "FIXED_LOT_NOT_ON_BROKER_STEP";
      return false;
   }
   return true;
}


bool ValidateMoneyManagementConfiguration(string &reason)
{
   if(MoneyManagementMode != MONEY_MANAGEMENT_FIXED_LOT &&
      MoneyManagementMode != MONEY_MANAGEMENT_RISK_PERCENT)
   {
      reason = "MONEY_MANAGEMENT_MODE_INVALID";
      return false;
   }
   if(RiskCapitalBase != RISK_CAPITAL_BALANCE &&
      RiskCapitalBase != RISK_CAPITAL_EQUITY)
   {
      reason = "RISK_CAPITAL_BASE_INVALID";
      return false;
   }
   if(!MathIsValidNumber(FixedLot) || FixedLot < 0.0 || FixedLot > 1000.0)
   {
      reason = "FIXED_LOT_CONFIGURATION_INVALID";
      return false;
   }
   if(!MathIsValidNumber(RiskPercent) ||
      RiskPercent < 0.0 || RiskPercent > 100.0)
   {
      reason = "RISK_PERCENT_INVALID_OR_ABOVE_HARD_CAP";
      return false;
   }
   double effective_risk_percent = EffectiveRiskPercent();
   if(!MathIsValidNumber(effective_risk_percent))
   {
      reason = "RISK_PERCENT_INVALID_OR_ABOVE_HARD_CAP";
      return false;
   }
   if(MoneyManagementMode == MONEY_MANAGEMENT_RISK_PERCENT &&
      (effective_risk_percent < 0.00000001 ||
       effective_risk_percent > MaxLossPerTradePercent))
   {
      reason = "RISK_PERCENT_INVALID_OR_ABOVE_HARD_CAP";
      return false;
   }
   if(!MathIsValidNumber(EstimatedCommissionPerLot) ||
      EstimatedCommissionPerLot < 0.0 ||
      EstimatedCommissionPerLot > 1000000.0)
   {
      reason = "ESTIMATED_COMMISSION_PER_LOT_INVALID";
      return false;
   }
   if(GatewayMode == GATEWAY_LIVE && !LiveCommissionPolicyConfirmed())
   {
      reason = "LIVE_COMMISSION_POLICY_UNCONFIRMED";
      return false;
   }
   double minimum = 0.0;
   double maximum = 0.0;
   double step = 0.0;
   if(!ReadBrokerVolumeLimits(minimum, maximum, step, reason))
      return false;
   if(MaxManagedTotalLots + 0.00000001 < minimum)
   {
      reason = "MANAGED_LOT_CAP_BELOW_BROKER_MINIMUM";
      return false;
   }
   if(MoneyManagementMode == MONEY_MANAGEMENT_FIXED_LOT &&
      !ValidateFixedLot(reason))
      return false;
   return true;
}


bool ResolveReadinessProbeVolume(double &probe_volume, string &reason)
{
   probe_volume = FixedLot;
   if(MoneyManagementMode == MONEY_MANAGEMENT_RISK_PERCENT)
   {
      double minimum = 0.0;
      double maximum = 0.0;
      double step = 0.0;
      if(!ReadBrokerVolumeLimits(minimum, maximum, step, reason))
         return false;
      probe_volume = minimum;
   }
   if(!MathIsValidNumber(probe_volume) || probe_volume <= 0.0)
   {
      reason = "READINESS_VOLUME_INVALID";
      return false;
   }
   return true;
}


bool SelectedRiskCapital(double &capital, string &reason)
{
   capital = RiskCapitalBase == RISK_CAPITAL_BALANCE
      ? AccountInfoDouble(ACCOUNT_BALANCE)
      : AccountInfoDouble(ACCOUNT_EQUITY);
   if(!MathIsValidNumber(capital) || capital <= 0.0)
   {
      reason = "RISK_CAPITAL_UNAVAILABLE";
      return false;
   }
   return true;
}


bool ReadFreshTick(MqlTick &tick, string &reason)
{
   ZeroMemory(tick);
   if(!SymbolInfoTick(_Symbol, tick) ||
      tick.bid <= 0.0 || tick.ask <= tick.bid)
   {
      reason = "QUOTE_UNAVAILABLE";
      return false;
   }
   datetime server_now = TimeCurrent();
   if(server_now <= 0 || tick.time <= 0 || server_now < tick.time ||
      server_now - tick.time > MaxQuoteAgeSeconds)
   {
      reason = "QUOTE_STALE_OR_FUTURE";
      return false;
   }
   return true;
}


bool ValidateStopsWithTick(
   const CommandPayload &command,
   const MqlTick &tick,
   string &reason
)
{
   double point = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
   long stop_level = SymbolInfoInteger(_Symbol, SYMBOL_TRADE_STOPS_LEVEL);
   long freeze_level = SymbolInfoInteger(
      _Symbol,
      SYMBOL_TRADE_FREEZE_LEVEL
   );
   double minimum_distance =
      (double)MathMax(stop_level, freeze_level) * point;
   double stop_loss = NormalizeSymbolPrice(command.stop_loss);
   double take_profit = NormalizeSymbolPrice(command.take_profit);
   double entry_price =
      command.action == "BUY" ? tick.ask : tick.bid;
   if(point <= 0.0 || entry_price <= 0.0 ||
      stop_loss <= 0.0 || take_profit <= 0.0)
   {
      reason = "STOP_CONFIGURATION_INVALID";
      return false;
   }
   if(command.action == "BUY")
   {
      if(stop_loss >= entry_price || take_profit <= entry_price ||
         entry_price - stop_loss + point * 0.0001 < minimum_distance ||
         take_profit - entry_price + point * 0.0001 < minimum_distance)
      {
         reason = "BUY_STOPS_INVALID";
         return false;
      }
   }
   else
   {
      if(stop_loss <= entry_price || take_profit >= entry_price ||
         stop_loss - entry_price + point * 0.0001 < minimum_distance ||
         entry_price - take_profit + point * 0.0001 < minimum_distance)
      {
         reason = "SELL_STOPS_INVALID";
         return false;
      }
   }
   return true;
}


bool ReadDirectionalSymbolVolume(
   const ENUM_ORDER_TYPE requested_type,
   double &directional_volume,
   string &reason
)
{
   directional_volume = 0.0;
   bool requested_buy = requested_type == ORDER_TYPE_BUY;
   int position_total = PositionsTotal();
   for(int index = 0; index < position_total; index++)
   {
      ulong ticket = PositionGetTicket(index);
      if(ticket == 0)
      {
         reason = "BROKER_VOLUME_EXPOSURE_UNAVAILABLE";
         return false;
      }
      string symbol = "";
      long type_value = 0;
      double position_volume = 0.0;
      if(!ReadSelectedPositionStringStrict(POSITION_SYMBOL, symbol) ||
         !ReadSelectedPositionIntegerStrict(POSITION_TYPE, type_value) ||
         !ReadSelectedPositionDoubleStrict(
            POSITION_VOLUME,
            position_volume
         ))
      {
         reason = "BROKER_VOLUME_EXPOSURE_UNAVAILABLE";
         return false;
      }
      if(Uppercase(symbol) != Uppercase(_Symbol))
         continue;
      bool position_buy =
         (ENUM_POSITION_TYPE)type_value == POSITION_TYPE_BUY;
      if(position_buy == requested_buy)
         directional_volume += position_volume;
   }

   int order_total = OrdersTotal();
   for(int index = 0; index < order_total; index++)
   {
      ulong ticket = OrderGetTicket(index);
      if(ticket == 0)
      {
         reason = "BROKER_VOLUME_EXPOSURE_UNAVAILABLE";
         return false;
      }
      string symbol = "";
      long type_value = 0;
      double order_volume = 0.0;
      if(!ReadSelectedOrderStringStrict(ORDER_SYMBOL, symbol) ||
         !ReadSelectedOrderIntegerStrict(ORDER_TYPE, type_value) ||
         !ReadSelectedOrderDoubleStrict(
            ORDER_VOLUME_CURRENT,
            order_volume
         ))
      {
         reason = "BROKER_VOLUME_EXPOSURE_UNAVAILABLE";
         return false;
      }
      if(Uppercase(symbol) != Uppercase(_Symbol))
         continue;
      ENUM_ORDER_TYPE order_type = (ENUM_ORDER_TYPE)type_value;
      bool order_buy = order_type == ORDER_TYPE_BUY ||
         order_type == ORDER_TYPE_BUY_LIMIT ||
         order_type == ORDER_TYPE_BUY_STOP ||
         order_type == ORDER_TYPE_BUY_STOP_LIMIT;
      bool order_sell = order_type == ORDER_TYPE_SELL ||
         order_type == ORDER_TYPE_SELL_LIMIT ||
         order_type == ORDER_TYPE_SELL_STOP ||
         order_type == ORDER_TYPE_SELL_STOP_LIMIT;
      if((requested_buy && order_buy) || (!requested_buy && order_sell))
         directional_volume += order_volume;
   }
   if(!MathIsValidNumber(directional_volume) || directional_volume < 0.0)
   {
      reason = "BROKER_VOLUME_EXPOSURE_UNAVAILABLE";
      return false;
   }
   return true;
}


bool ResolveOrderVolume(
   const CommandPayload &command,
   const MqlTick &tick,
   double &volume,
   double &risk_capital_amount,
   double &estimated_risk_money,
   string &reason
)
{
   volume = 0.0;
   risk_capital_amount = 0.0;
   estimated_risk_money = 0.0;
   if(!ValidateMoneyManagementConfiguration(reason))
      return false;

   double minimum = 0.0;
   double maximum = 0.0;
   double step = 0.0;
   if(!ReadBrokerVolumeLimits(minimum, maximum, step, reason))
      return false;

   if(!SelectedRiskCapital(risk_capital_amount, reason))
      return false;
   ENUM_ORDER_TYPE type = command.action == "BUY"
      ? ORDER_TYPE_BUY
      : ORDER_TYPE_SELL;
   double entry = command.action == "BUY" ? tick.ask : tick.bid;
   double point = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
   double risk_entry = command.action == "BUY"
      ? entry + (double)SlippagePoints * point
      : entry - (double)SlippagePoints * point;
   double stop_loss = NormalizeSymbolPrice(command.stop_loss);
   double one_lot_result = 0.0;
   if(entry <= 0.0 || point <= 0.0 || risk_entry <= 0.0 ||
      stop_loss <= 0.0 ||
      !OrderCalcProfit(
         type,
         _Symbol,
         1.0,
         risk_entry,
         stop_loss,
         one_lot_result
      ) ||
      !MathIsValidNumber(one_lot_result) || one_lot_result >= 0.0)
   {
      reason = "RISK_STOP_LOSS_CALCULATION_FAILED";
      return false;
   }

   double symbol_volume_limit = 0.0;
   if(!SymbolInfoDouble(
         _Symbol,
         SYMBOL_VOLUME_LIMIT,
         symbol_volume_limit
      ) ||
      !MathIsValidNumber(symbol_volume_limit) ||
      symbol_volume_limit < 0.0)
   {
      reason = "BROKER_VOLUME_LIMIT_UNAVAILABLE";
      return false;
   }
   double directional_volume = 0.0;
   if(!ReadDirectionalSymbolVolume(type, directional_volume, reason))
      return false;
   int managed_positions = 0;
   double managed_lots = 0.0;
   double managed_floating_pnl = 0.0;
   if(!ReadManagedOpenState(
         managed_positions,
         managed_lots,
         managed_floating_pnl
      ))
   {
      reason = "POSITION_TELEMETRY_UNAVAILABLE";
      return false;
   }
   double remaining_managed_lots = MaxManagedTotalLots - managed_lots;
   double maximum_allowed = MathMin(
      maximum,
      MathMax(0.0, remaining_managed_lots)
   );
   if(symbol_volume_limit > 0.0)
      maximum_allowed = MathMin(
         maximum_allowed,
         MathMax(0.0, symbol_volume_limit - directional_volume)
      );

   double risk_budget = 0.0;
   if(MoneyManagementMode == MONEY_MANAGEMENT_FIXED_LOT)
   {
      volume = FixedLot;
      if(volume > maximum_allowed + 0.00000001)
      {
         reason = "FIXED_LOT_EXCEEDS_AVAILABLE_VOLUME_LIMIT";
         return false;
      }
   }
   else
   {
      double requested_risk_budget =
         risk_capital_amount * EffectiveRiskPercent() / 100.0;
      double balance_risk_cap =
         AccountInfoDouble(ACCOUNT_BALANCE) *
         MaxLossPerTradePercent / 100.0;
      risk_budget = MathMin(requested_risk_budget, balance_risk_cap);
      double loss_per_lot =
         -one_lot_result + EffectiveEstimatedCommissionPerLot();
      if(!MathIsValidNumber(risk_budget) || risk_budget < 0.00000001 ||
         !MathIsValidNumber(loss_per_lot) || loss_per_lot <= 0.0)
      {
         reason = "RISK_BUDGET_INVALID";
         return false;
      }
      double raw_volume = risk_budget / loss_per_lot;
      if(!MathIsValidNumber(raw_volume) ||
         raw_volume + 0.00000001 < minimum ||
         maximum_allowed + 0.00000001 < minimum)
      {
         reason = "RISK_VOLUME_BELOW_BROKER_MINIMUM";
         return false;
      }
      double capped_volume = MathMin(raw_volume, maximum_allowed);
      double step_count = MathFloor(
         (capped_volume - minimum) / step + 0.0000000001
      );
      volume = NormalizeDouble(
         minimum + MathMax(0.0, step_count) * step,
         LotDigits()
      );
      while(volume > capped_volume + 0.00000001 &&
         volume - step >= minimum - 0.00000001)
         volume = NormalizeDouble(volume - step, LotDigits());
   }

   if(!ValidateVolumeOnBrokerGrid(
         volume,
         minimum,
         maximum,
         step,
         reason
      ) ||
      volume > MaxManagedTotalLots + 0.00000001)
   {
      if(reason == "")
         reason = "ORDER_VOLUME_EXCEEDS_MANAGED_LOT_CAP";
      return false;
   }

   while(true)
   {
      double exact_stop_result = 0.0;
      if(!OrderCalcProfit(
            type,
            _Symbol,
            volume,
            risk_entry,
            stop_loss,
            exact_stop_result
         ) ||
         !MathIsValidNumber(exact_stop_result) || exact_stop_result >= 0.0)
      {
         reason = "BROKER_RISK_CALCULATION_FAILED";
         return false;
      }
      estimated_risk_money =
         -exact_stop_result +
         EffectiveEstimatedCommissionPerLot() * volume;
      double tolerance = MoneyManagementMode == MONEY_MANAGEMENT_RISK_PERCENT
         ? risk_budget * 0.000000001
         : 0.0;
      if(MoneyManagementMode != MONEY_MANAGEMENT_RISK_PERCENT ||
         estimated_risk_money <= risk_budget + tolerance)
         break;
      volume = NormalizeDouble(volume - step, LotDigits());
      if(volume < minimum - 0.00000001)
      {
         reason = "RISK_VOLUME_BELOW_BROKER_MINIMUM";
         return false;
      }
   }
   if(!MathIsValidNumber(estimated_risk_money) ||
      estimated_risk_money < 0.00000001)
   {
      reason = "RISK_ESTIMATE_BELOW_WIRE_MINIMUM";
      return false;
   }

   double required_margin = 0.0;
   double free_margin = AccountInfoDouble(ACCOUNT_MARGIN_FREE);
   if(!OrderCalcMargin(
         type,
         _Symbol,
         volume,
         risk_entry,
         required_margin
      ) ||
      !MathIsValidNumber(required_margin) || required_margin < 0.0 ||
      !MathIsValidNumber(free_margin) || free_margin <= 0.0 ||
      required_margin > free_margin + 0.00000001)
   {
      reason = "BROKER_MARGIN_CALCULATION_FAILED_OR_INSUFFICIENT";
      return false;
   }
   return true;
}


bool ValidateClosedBarBinding(
   const CommandPayload &command,
   const MqlTick &tick,
   string &reason
)
{
   if(!IsSha256Hex(command.snapshot_id))
   {
      reason = "SNAPSHOT_ID_INVALID";
      return false;
   }
   int now = NowUtc();
   if(command.snapshot_observed_at > now + MaxClockSkewSeconds ||
      command.snapshot_observed_at < now - MaxSnapshotAgeSeconds)
   {
      reason = "SNAPSHOT_STALE_OR_FUTURE";
      return false;
   }
   datetime closed_bar = iTime(_Symbol, _Period, 1);
   datetime open_bar = iTime(_Symbol, _Period, 0);
   if(closed_bar <= 0 || open_bar <= 0 ||
      command.bar_time != (int)closed_bar ||
      command.bar_time >= (int)open_bar)
   {
      reason = "CLOSED_BAR_IDENTITY_MISMATCH";
      return false;
   }
   double point = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
   double entry_price =
      command.action == "BUY" ? tick.ask : tick.bid;
   if(command.reference_price <= 0.0 || point <= 0.0 ||
      MathAbs(entry_price - command.reference_price) / point >
         MaxSignalDriftPoints)
   {
      reason = "SIGNAL_PRICE_DRIFT_EXCEEDED";
      return false;
   }
   return true;
}


bool IsTradeSessionOpen(string &reason)
{
   ENUM_SYMBOL_TRADE_MODE trade_mode =
      (ENUM_SYMBOL_TRADE_MODE)SymbolInfoInteger(
         _Symbol,
         SYMBOL_TRADE_MODE
      );
   if(trade_mode == SYMBOL_TRADE_MODE_DISABLED ||
      trade_mode == SYMBOL_TRADE_MODE_CLOSEONLY)
   {
      reason = "SYMBOL_TRADING_DISABLED";
      return false;
   }

   datetime broker_now = TimeCurrent();
   MqlDateTime now_parts;
   if(broker_now <= 0 || !TimeToStruct(broker_now, now_parts))
   {
      reason = "BROKER_TIME_UNAVAILABLE";
      return false;
   }
   int now_seconds =
      now_parts.hour * 3600 + now_parts.min * 60 + now_parts.sec;
   bool observed_session = false;
   bool inside_session = false;
   for(uint session_index = 0; session_index < 16; session_index++)
   {
      datetime session_from = 0;
      datetime session_to = 0;
      if(!SymbolInfoSessionTrade(
         _Symbol,
         (ENUM_DAY_OF_WEEK)now_parts.day_of_week,
         session_index,
         session_from,
         session_to
       ))
      {
         if(!observed_session)
         {
            reason = "BROKER_TRADE_SESSION_UNAVAILABLE";
            return false;
         }
         break;
      }
      observed_session = true;
      MqlDateTime from_parts;
      MqlDateTime to_parts;
      if(!TimeToStruct(session_from, from_parts) ||
         !TimeToStruct(session_to, to_parts))
      {
         reason = "BROKER_TRADE_SESSION_INVALID";
         return false;
      }
      int from_seconds =
         from_parts.hour * 3600 + from_parts.min * 60 + from_parts.sec;
      int to_seconds =
         to_parts.hour * 3600 + to_parts.min * 60 + to_parts.sec;
      if(from_seconds == to_seconds ||
         (from_seconds < to_seconds &&
          now_seconds >= from_seconds && now_seconds < to_seconds) ||
         (from_seconds > to_seconds &&
          (now_seconds >= from_seconds || now_seconds < to_seconds)))
      {
         inside_session = true;
         break;
      }
   }
   if(!observed_session)
   {
      reason = "BROKER_TRADE_SESSION_UNAVAILABLE";
      return false;
   }
   if(!inside_session)
   {
      reason = "BROKER_SESSION_OR_SYMBOL_CLOSED";
      return false;
   }
   return true;
}


bool SelectFillingMode(
   ENUM_ORDER_TYPE_FILLING &filling,
   string &reason
)
{
   long flags = SymbolInfoInteger(_Symbol, SYMBOL_FILLING_MODE);
   ENUM_SYMBOL_TRADE_EXECUTION execution =
      (ENUM_SYMBOL_TRADE_EXECUTION)SymbolInfoInteger(
         _Symbol,
         SYMBOL_TRADE_EXEMODE
      );
   if((flags & SYMBOL_FILLING_FOK) == SYMBOL_FILLING_FOK)
   {
      filling = ORDER_FILLING_FOK;
      return true;
   }
   if((flags & SYMBOL_FILLING_IOC) == SYMBOL_FILLING_IOC)
   {
      filling = ORDER_FILLING_IOC;
      return true;
   }
   if(execution != SYMBOL_TRADE_EXECUTION_MARKET)
   {
      filling = ORDER_FILLING_RETURN;
      return true;
   }
   reason = "BROKER_FILLING_MODE_UNSUPPORTED";
   return false;
}


bool BuildTradeRequest(
   const CommandPayload &command,
   const MqlTick &tick,
   const double order_volume,
   MqlTradeRequest &request,
   string &reason
)
{
   ZeroMemory(request);
   ENUM_SYMBOL_TRADE_MODE trade_mode =
      (ENUM_SYMBOL_TRADE_MODE)SymbolInfoInteger(
         _Symbol,
         SYMBOL_TRADE_MODE
      );
   if(command.action == "BUY" &&
      trade_mode != SYMBOL_TRADE_MODE_FULL &&
      trade_mode != SYMBOL_TRADE_MODE_LONGONLY)
   {
      reason = "SYMBOL_BUY_NOT_ALLOWED";
      return false;
   }
   if(command.action == "SELL" &&
      trade_mode != SYMBOL_TRADE_MODE_FULL &&
      trade_mode != SYMBOL_TRADE_MODE_SHORTONLY)
   {
      reason = "SYMBOL_SELL_NOT_ALLOWED";
      return false;
   }
   if(!IsTradeSessionOpen(reason))
      return false;

   ENUM_ORDER_TYPE_FILLING filling;
   if(!SelectFillingMode(filling, reason))
      return false;

   request.action = TRADE_ACTION_DEAL;
   request.magic = (ulong)MagicNumber;
   request.order = 0;
   request.symbol = _Symbol;
   request.volume = order_volume;
   request.price = command.action == "BUY" ? tick.ask : tick.bid;
   request.stoplimit = 0.0;
   request.sl = NormalizeSymbolPrice(command.stop_loss);
   request.tp = NormalizeSymbolPrice(command.take_profit);
   request.deviation = (ulong)SlippagePoints;
   request.type =
      command.action == "BUY" ? ORDER_TYPE_BUY : ORDER_TYPE_SELL;
   request.type_filling = filling;
   request.type_time = ORDER_TIME_GTC;
   request.expiration = 0;
   request.comment = "HQ:" + command.command_id;
   request.position = 0;
   request.position_by = 0;
   return true;
}


bool CheckTradeRequest(
   const MqlTradeRequest &request,
   MqlTradeCheckResult &check_result,
   string &reason
)
{
   ZeroMemory(check_result);
   ResetLastError();
   if(!OrderCheck(request, check_result))
   {
      int error_code = GetLastError();
      reason = "ORDER_CHECK_API_FAILED_" + IntegerToString(error_code);
      return false;
   }
   // MqlTradeCheckResult uses zero for a successful request check.
   // TRADE_RETCODE_DONE belongs to MqlTradeResult after OrderSend.
   if(check_result.retcode != 0)
   {
      reason =
         "ORDER_CHECK_RETCODE_" +
         IntegerToString((int)check_result.retcode);
      return false;
   }
   double projected_level = check_result.margin_level;
   if(!MathIsValidNumber(projected_level))
   {
      reason = "BROKER_MARGIN_TELEMETRY_INVALID";
      return false;
   }
   if(projected_level <= 0.0)
   {
      double projected_margin = check_result.margin;
      double account_equity = AccountInfoDouble(ACCOUNT_EQUITY);
      double projected_profit = check_result.profit;
      double projected_equity =
         account_equity + projected_profit;
      if(!MathIsValidNumber(projected_margin) ||
         projected_margin <= 0.0 ||
         !MathIsValidNumber(account_equity) || account_equity <= 0.0 ||
         !MathIsValidNumber(projected_profit) ||
         !MathIsValidNumber(projected_equity) || projected_equity <= 0.0)
      {
         reason = "BROKER_MARGIN_TELEMETRY_INVALID";
         return false;
      }
      projected_level = projected_equity / projected_margin * 100.0;
   }
   if(!MathIsValidNumber(projected_level) || projected_level <= 0.0)
   {
      reason = "BROKER_MARGIN_TELEMETRY_INVALID";
      return false;
   }
   if(projected_level < MinProjectedMarginLevelPercent)
   {
      reason = "PROJECTED_MARGIN_LEVEL_TOO_LOW";
      return false;
   }
   return true;
}


bool ValidateCurrentRiskState(
   const double proposed_volume,
   string &reason
)
{
   double floating_pnl = 0.0;
   int positions = 0;
   double lots = 0.0;
   if(!ReadManagedOpenState(positions, lots, floating_pnl))
   {
      reason = "POSITION_TELEMETRY_UNAVAILABLE";
      return false;
   }
   if(positions >= MaxManagedOpenPositions)
   {
      reason = "MAX_MANAGED_POSITIONS_REACHED";
      return false;
   }
   if(!MathIsValidNumber(proposed_volume) || proposed_volume < 0.0)
   {
      reason = "PROPOSED_VOLUME_INVALID";
      return false;
   }
   if(lots + proposed_volume >
      MaxManagedTotalLots + 0.00000001)
   {
      reason = "MAX_MANAGED_LOTS_EXCEEDED";
      return false;
   }
   int trades_today = 0;
   if(!CountManagedTradesToday(trades_today))
   {
      reason = "HISTORY_TELEMETRY_UNAVAILABLE";
      return false;
   }
   if(trades_today >= MaxTradesPerBrokerDay)
   {
      reason = "MAX_TRADES_PER_DAY_REACHED";
      return false;
   }
   double balance = AccountInfoDouble(ACCOUNT_BALANCE);
   if(!MathIsValidNumber(balance) || balance <= 0.0)
   {
      reason = "ACCOUNT_BALANCE_INVALID";
      return false;
   }
   double daily_pnl = 0.0;
   if(!ManagedDailyPnl(daily_pnl))
   {
      reason = "HISTORY_TELEMETRY_UNAVAILABLE";
      return false;
   }
   double daily_risk_pnl = 0.0;
   if(!ManagedRiskPnlIncludingFloatingLoss(
         daily_pnl,
         floating_pnl,
         daily_risk_pnl
      ))
   {
      reason = "POSITION_TELEMETRY_UNAVAILABLE";
      return false;
   }
   if(daily_risk_pnl < 0.0 &&
      -daily_risk_pnl / balance * 100.0 >= MaxDailyLossPercent)
   {
      reason = "MAX_DAILY_LOSS_REACHED";
      return false;
   }
   double weekly_pnl = 0.0;
   if(!ManagedWeeklyPnl(weekly_pnl))
   {
      reason = "HISTORY_TELEMETRY_UNAVAILABLE";
      return false;
   }
   double weekly_risk_pnl = 0.0;
   if(!ManagedRiskPnlIncludingFloatingLoss(
         weekly_pnl,
         floating_pnl,
         weekly_risk_pnl
      ))
   {
      reason = "POSITION_TELEMETRY_UNAVAILABLE";
      return false;
   }
   if(weekly_risk_pnl < 0.0 &&
      -weekly_risk_pnl / balance * 100.0 >=
         MaxManagedWeeklyLossPercent)
   {
      reason = "MAX_WEEKLY_LOSS_REACHED";
      return false;
   }
   int loss_count = 0;
   int cooldown_until = 0;
   if(!ReadManagedLossStreak(loss_count, cooldown_until))
   {
      reason = "HISTORY_TELEMETRY_UNAVAILABLE";
      return false;
   }
   datetime broker_now = TimeCurrent();
   if(broker_now <= 0)
   {
      reason = "HISTORY_TELEMETRY_UNAVAILABLE";
      return false;
   }
   if(loss_count >= MaxConsecutiveManagedLosses &&
      (int)broker_now < cooldown_until)
   {
      reason = "CONSECUTIVE_LOSS_COOLDOWN_ACTIVE";
      return false;
   }
   double account_drawdown_percent = 0.0;
   if(!CurrentAccountDrawdownPercent(account_drawdown_percent))
   {
      reason = "ACCOUNT_EQUITY_TELEMETRY_INVALID";
      return false;
   }
   if(account_drawdown_percent >= MaxAccountEquityDrawdownPercent)
   {
      reason = "MAX_ACCOUNT_DRAWDOWN_REACHED";
      return false;
   }
   return true;
}


bool ValidateRiskEnvelope(
   const CommandPayload &command,
   const MqlTick &tick,
   const double order_volume,
   double &final_estimated_risk_money,
   string &reason
)
{
   final_estimated_risk_money = 0.0;
   if(!ValidateCurrentRiskState(order_volume, reason))
      return false;
   ENUM_ORDER_TYPE type =
      command.action == "BUY" ? ORDER_TYPE_BUY : ORDER_TYPE_SELL;
   double entry = command.action == "BUY" ? tick.ask : tick.bid;
   double point = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
   double risk_entry = command.action == "BUY"
      ? entry + (double)SlippagePoints * point
      : entry - (double)SlippagePoints * point;
   double stop_loss = NormalizeSymbolPrice(command.stop_loss);
   double take_profit = NormalizeSymbolPrice(command.take_profit);
   double stop_result = 0.0;
   double target_result = 0.0;
   if(!MathIsValidNumber(entry) || entry <= 0.0 ||
      !MathIsValidNumber(point) || point <= 0.0 ||
      !MathIsValidNumber(risk_entry) || risk_entry <= 0.0 ||
      !OrderCalcProfit(
         type,
         _Symbol,
         order_volume,
         risk_entry,
         stop_loss,
         stop_result
      ) ||
      !OrderCalcProfit(
         type,
         _Symbol,
         order_volume,
         risk_entry,
         take_profit,
         target_result
      ))
   {
      reason = "BROKER_RISK_CALCULATION_FAILED";
      return false;
   }
   double reserved_commission =
      EffectiveEstimatedCommissionPerLot() * order_volume;
   double loss_money = MathMax(0.0, -stop_result) + reserved_commission;
   double reward_money =
      MathMax(0.0, target_result) - reserved_commission;
   double balance = AccountInfoDouble(ACCOUNT_BALANCE);
   if(loss_money < 0.00000001 || reward_money <= 0.0 ||
      !MathIsValidNumber(balance) || balance <= 0.0 ||
      !MathIsValidNumber(loss_money) ||
      !MathIsValidNumber(reward_money) ||
      !MathIsValidNumber(reserved_commission))
   {
      reason = "RISK_ESTIMATE_INVALID";
      return false;
   }
   final_estimated_risk_money = loss_money;
   if(loss_money / balance * 100.0 > MaxLossPerTradePercent)
   {
      reason = "MAX_LOSS_PER_TRADE_EXCEEDED";
      return false;
   }
   if(MoneyManagementMode == MONEY_MANAGEMENT_RISK_PERCENT)
   {
      double risk_capital = 0.0;
      if(!SelectedRiskCapital(risk_capital, reason))
         return false;
      double live_risk_budget =
         risk_capital * EffectiveRiskPercent() / 100.0;
      double persisted_risk_budget =
         g_ack_risk_capital_amount * g_ack_risk_percent / 100.0;
      if(!g_ack_has_sizing_evidence ||
         !MathIsValidNumber(persisted_risk_budget) ||
         persisted_risk_budget < 0.00000001)
      {
         reason = "RISK_STATE_UNAVAILABLE";
         return false;
      }
      double risk_budget = MathMin(
         live_risk_budget,
         persisted_risk_budget
      );
      if(!MathIsValidNumber(risk_budget) || risk_budget < 0.00000001)
      {
         reason = "RISK_BUDGET_INVALID";
         return false;
      }
      double tolerance = risk_budget * 0.000000001;
      if(loss_money > risk_budget + tolerance)
      {
         reason = "RISK_PERCENT_BUDGET_EXCEEDED";
         return false;
      }
   }
   if(reward_money / loss_money + 0.00000001 <
      MinRewardRiskRatio)
   {
      reason = "MIN_REWARD_RISK_NOT_MET";
      return false;
   }
   return true;
}


bool ValidateHeartbeat(
   const CommandPayload &command,
   string &reason
)
{
   if(!RequireHeartbeat)
      return true;
   string raw = "";
   if(!ReadCommonText(HeartbeatPath(), MaxCommandBytes, raw))
   {
      reason = "HEARTBEAT_MISSING";
      return false;
   }
   raw = Trimmed(raw);
   string inner_payload = "";
   if(!VerifySignedEnvelope(raw, "HEARTBEAT", inner_payload, reason))
   {
      reason = "HEARTBEAT_" + reason;
      return false;
   }
   string keys[];
   string values[];
   int quoted[];
   if(!ParseFlatJson(inner_payload, keys, values, quoted, reason))
   {
      reason = "HEARTBEAT_" + reason;
      return false;
   }
   string schema = "";
   string channel = "";
   string heartbeat_id = "";
   int issued_at = 0;
   int expires_at = 0;
   if(!ReadRequiredString(
         keys, values, quoted, "schemaVersion", schema, reason
      ) ||
      !ReadRequiredString(
         keys, values, quoted, "channelId", channel, reason
      ) ||
      !ReadRequiredString(
         keys, values, quoted, "heartbeatId", heartbeat_id, reason
      ) ||
      !ReadRequiredInteger(
         keys, values, quoted, "issuedAt", issued_at, reason
      ) ||
      !ReadRequiredInteger(
         keys, values, quoted, "expiresAt", expires_at, reason
      ))
   {
      reason = "HEARTBEAT_" + reason;
      return false;
   }
   if(ArraySize(keys) != 5)
   {
      reason = "HEARTBEAT_UNKNOWN_FIELDS";
      return false;
   }
   int now = NowUtc();
   if(schema != HEARTBEAT_SCHEMA)
   {
      reason = "HEARTBEAT_SCHEMA_MISMATCH";
      return false;
   }
   if(channel != SnapshotChannel ||
      heartbeat_id != command.heartbeat_id)
   {
      reason = "HEARTBEAT_IDENTITY_MISMATCH";
      return false;
   }
   if(issued_at > now + MaxClockSkewSeconds ||
      expires_at < now ||
      expires_at <= issued_at ||
      expires_at - issued_at > MaxHeartbeatTtlSeconds)
   {
      reason = "HEARTBEAT_EXPIRED_OR_INVALID";
      return false;
   }
   return true;
}


bool ReadLastOrderBar(int &bar_time)
{
   bar_time = 0;
   string raw = "";
   string path = LastOrderBarPath();
   bool state_exists = FileIsExist(path, FILE_COMMON);
   if(!ReadCommonText(path, 256, raw))
      return !state_exists;
   raw = Trimmed(raw);
   string parts[];
   int count = StringSplit(raw, '|', parts);
   if(count != 5 || parts[0] != "v2" ||
      parts[1] != SnapshotChannel ||
      Uppercase(parts[2]) != Uppercase(_Symbol) ||
      Uppercase(parts[3]) != CurrentTimeframeName() ||
      !IsIntegerToken(parts[4]))
      return false;
   bar_time = (int)StringToInteger(parts[4]);
   return bar_time >= 946684800;
}


bool WriteLastOrderBar(const int bar_time)
{
   if(bar_time < 946684800)
      return false;
   return WriteCommonTextAtomic(
      LastOrderBarPath(),
      "v2|" + SnapshotChannel + "|" + Uppercase(_Symbol) + "|" +
      CurrentTimeframeName() + "|" + IntegerToString(bar_time)
   );
}


bool ValidateRuntime(
   const CommandPayload &command,
   const double order_volume,
   string &reason
)
{
   if(!ValidateConfiguredModes(reason))
      return false;
   if(GatewayMode == GATEWAY_LIVE)
   {
      if(IsDemo())
      {
         reason = "LIVE_MODE_REQUIRES_NON_DEMO_ACCOUNT";
         return false;
      }
      if(!LiveArmed)
      {
         reason = "LIVE_NOT_ARMED";
         return false;
      }
      if(!SingleHostLiveAcknowledged)
      {
         reason = "SINGLE_HOST_LIVE_ACK_REQUIRED";
         return false;
      }
      if(!LiveAccountOwnerLockReady(reason))
         return false;
   }
   if(!IsHedgingAccount())
   {
      reason = "MT5_HEDGING_ACCOUNT_REQUIRED";
      return false;
   }
   if(command.schema_version != COMMAND_SCHEMA)
   {
      reason = "COMMAND_SCHEMA_MISMATCH";
      return false;
   }
   if(!IsCommandIdentifier(command.command_id) ||
      !IsIdempotencyIdentifier(command.idempotency_key) ||
      !IsHeartbeatIdentifier(command.heartbeat_id))
   {
      reason = "UNSAFE_COMMAND_IDENTIFIER";
      return false;
   }
   if(command.channel_id != SnapshotChannel)
   {
      reason = "CHANNEL_MISMATCH";
      return false;
   }
   if(command.action != "BUY" && command.action != "SELL")
   {
      reason = "ACTION_NOT_ALLOWED";
      return false;
   }
   if(FileIsExist(KillMarkerPath(), FILE_COMMON))
   {
      reason = "KILL_SWITCH_ACTIVE";
      return false;
   }
   if(GatewayMode == GATEWAY_LIVE &&
      !CsvContains(AllowedSymbols, command.symbol))
   {
      reason = "LIVE_SYMBOL_REQUIRES_EXACT_ALLOWLIST";
      return false;
   }
   if((GatewayMode != GATEWAY_LIVE &&
       !IsAllowedBrokerSymbol(AllowedSymbols, command.symbol)) ||
      Uppercase(_Symbol) != command.symbol)
   {
      reason = "SYMBOL_NOT_ALLOWED_OR_NOT_ATTACHED";
      return false;
   }
   int command_period = TimeframeToPeriod(command.timeframe);
   if(command_period == 0 ||
      !CsvContains(AllowedTimeframes, command.timeframe) ||
      command_period != (int)_Period)
   {
      reason = "TIMEFRAME_NOT_ALLOWED_OR_NOT_ATTACHED";
      return false;
   }

   int now = NowUtc();
   if(command.issued_at > now + MaxClockSkewSeconds ||
      command.expires_at < now ||
      command.expires_at <= command.issued_at ||
      command.expires_at - command.issued_at > MaxCommandTtlSeconds)
   {
      reason = "COMMAND_EXPIRED_OR_INVALID_TTL";
      return false;
   }
   if(!ValidateHeartbeat(command, reason))
      return false;
   if(!ValidateMoneyManagementConfiguration(reason))
      return false;
   if(!IsConnected())
   {
      reason = "TERMINAL_NOT_CONNECTED";
      return false;
   }

   MqlTick tick;
   if(!ReadFreshTick(tick, reason))
      return false;
   if(!ValidateClosedBarBinding(command, tick, reason))
      return false;
   double point = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
   double spread_points =
      point > 0.0 ? (tick.ask - tick.bid) / point : 999999999.0;
   if(MaxSpreadPoints <= 0 ||
      spread_points > (double)MaxSpreadPoints)
   {
      reason = "SPREAD_LIMIT_EXCEEDED";
      return false;
   }
   if(!ValidateStopsWithTick(command, tick, reason))
      return false;
   double preliminary_estimated_risk_money = 0.0;
   if(!ValidateRiskEnvelope(
         command,
         tick,
         order_volume,
         preliminary_estimated_risk_money,
         reason
      ))
      return false;

   MqlTradeRequest request;
   MqlTradeCheckResult check_result;
   if(!BuildTradeRequest(
         command,
         tick,
         order_volume,
         request,
         reason
      ) ||
      !CheckTradeRequest(request, check_result, reason))
      return false;

   int last_bar = 0;
   if(!ReadLastOrderBar(last_bar))
   {
      reason = "LAST_ORDER_BAR_STATE_INVALID";
      return false;
   }
   if(last_bar == command.bar_time)
   {
      reason = "ONE_ORDER_PER_BAR_LIMIT";
      return false;
   }
   if(!SignedCommandVerificationAvailable())
   {
      reason = "SIGNED_COMMAND_VERIFICATION_NOT_READY";
      return false;
   }
   if(GatewayMode == GATEWAY_SHADOW)
      return true;
   if(MQLInfoInteger(MQL_TESTER) != 0 ||
      MQLInfoInteger(MQL_OPTIMIZATION) != 0)
   {
      reason = "TESTER_EXECUTION_DISABLED";
      return false;
   }
   if(GatewayMode == GATEWAY_DEMO && !IsDemo())
   {
      reason = "DEMO_MODE_REQUIRES_DEMO_ACCOUNT";
      return false;
   }
   if(!IsTradeAllowed())
   {
      reason = "EA_TRADING_NOT_ALLOWED";
      return false;
   }
   return true;
}


bool UpdateRiskTelemetry(const bool force)
{
   int now = NowUtc();
   if(!force && g_risk_cache_at > 0 &&
      now >= g_risk_cache_at &&
      now - g_risk_cache_at < 5)
      return g_cached_history_telemetry_ready;
   double floating_pnl = 0.0;
   if(!ReadManagedOpenState(
      g_cached_managed_positions,
      g_cached_managed_lots,
      floating_pnl
   ))
   {
      g_cached_history_telemetry_ready = false;
      g_cached_execution_guard_ready = false;
      g_cached_execution_guard_reason =
         "POSITION_TELEMETRY_UNAVAILABLE";
      g_risk_cache_at = now;
      return false;
   }
   int trades_today = 0;
   double daily_pnl = 0.0;
   double weekly_pnl = 0.0;
   int consecutive_losses = 0;
   int cooldown_until = 0;
   if(!CountManagedTradesToday(trades_today) ||
      !ManagedDailyPnl(daily_pnl) ||
      !ManagedWeeklyPnl(weekly_pnl) ||
      !ReadManagedLossStreak(consecutive_losses, cooldown_until))
   {
      g_cached_history_telemetry_ready = false;
      g_cached_execution_guard_ready = false;
      g_cached_execution_guard_reason =
         "HISTORY_TELEMETRY_UNAVAILABLE";
      g_risk_cache_at = now;
      return false;
   }
   double daily_risk_pnl = 0.0;
   double weekly_risk_pnl = 0.0;
   if(!ManagedRiskPnlIncludingFloatingLoss(
         daily_pnl,
         floating_pnl,
         daily_risk_pnl
      ) ||
      !ManagedRiskPnlIncludingFloatingLoss(
         weekly_pnl,
         floating_pnl,
         weekly_risk_pnl
      ))
   {
      g_cached_history_telemetry_ready = false;
      g_cached_execution_guard_ready = false;
      g_cached_execution_guard_reason =
         "POSITION_TELEMETRY_UNAVAILABLE";
      g_risk_cache_at = now;
      return false;
   }
   g_cached_trades_today = trades_today;
   g_cached_managed_daily_pnl = daily_risk_pnl;
   g_cached_managed_weekly_pnl = weekly_risk_pnl;
   g_cached_consecutive_losses = consecutive_losses;
   g_cached_cooldown_until = cooldown_until;
   if(!CurrentAccountDrawdownPercent(
         g_cached_account_drawdown_percent
      ) ||
      !CurrentMarginLevelPercent(g_cached_margin_level_percent))
   {
      g_cached_history_telemetry_ready = false;
      g_cached_execution_guard_ready = false;
      g_cached_execution_guard_reason =
         "ACCOUNT_EQUITY_TELEMETRY_INVALID";
      g_risk_cache_at = now;
      return false;
   }
   g_cached_history_telemetry_ready = true;
   string reason = "";
   double readiness_probe_volume = 0.0;
   if(!IsHedgingAccount())
   {
      g_cached_execution_guard_ready = false;
      g_cached_execution_guard_reason =
         "MT5_HEDGING_ACCOUNT_REQUIRED";
   }
   else if(FileIsExist(KillMarkerPath(), FILE_COMMON))
   {
      g_cached_execution_guard_ready = false;
      g_cached_execution_guard_reason = "KILL_SWITCH_ACTIVE";
   }
   else if(!IsConnected())
   {
      g_cached_execution_guard_ready = false;
      g_cached_execution_guard_reason = "TERMINAL_NOT_CONNECTED";
   }
   else if(GatewayMode == GATEWAY_LIVE && IsDemo())
   {
      g_cached_execution_guard_ready = false;
      g_cached_execution_guard_reason =
         "LIVE_MODE_REQUIRES_NON_DEMO_ACCOUNT";
   }
   else if(GatewayMode == GATEWAY_LIVE && !LiveArmed)
   {
      g_cached_execution_guard_ready = false;
      g_cached_execution_guard_reason = "LIVE_NOT_ARMED";
   }
   else if(GatewayMode == GATEWAY_LIVE &&
      !SingleHostLiveAcknowledged)
   {
      g_cached_execution_guard_ready = false;
      g_cached_execution_guard_reason =
         "SINGLE_HOST_LIVE_ACK_REQUIRED";
   }
   else if(GatewayMode == GATEWAY_LIVE &&
      !LiveAccountOwnerLockReady(reason))
   {
      g_cached_execution_guard_ready = false;
      g_cached_execution_guard_reason = reason;
   }
   else if(!ValidateMoneyManagementConfiguration(reason))
   {
      g_cached_execution_guard_ready = false;
      g_cached_execution_guard_reason = reason;
   }
   else if(!ResolveReadinessProbeVolume(readiness_probe_volume, reason))
   {
      g_cached_execution_guard_ready = false;
      g_cached_execution_guard_reason = reason;
   }
   else if(!ValidateCurrentRiskState(readiness_probe_volume, reason))
   {
      g_cached_execution_guard_ready = false;
      g_cached_execution_guard_reason = reason;
   }
   else if(!SignedCommandVerificationAvailable())
   {
      g_cached_execution_guard_ready = false;
      g_cached_execution_guard_reason =
         "SIGNED_COMMAND_VERIFICATION_NOT_READY";
   }
   else if(GatewayMode != GATEWAY_SHADOW && !IsTradeAllowed())
   {
      g_cached_execution_guard_ready = false;
      g_cached_execution_guard_reason = "EA_TRADING_NOT_ALLOWED";
   }
   else
   {
      g_cached_execution_guard_ready = true;
      g_cached_execution_guard_reason = "READY";
   }
   g_risk_cache_at = now;
   return true;
}


string BrokerRetcodeReason(const uint retcode)
{
   return "BROKER_RETCODE_" + IntegerToString((int)retcode);
}


bool IsDefinitiveRejectTradeRetcode(const uint retcode)
{
   // Positive allowlist only.  A newly introduced server retcode is unsafe by
   // default because OrderSend(true) proves transport acceptance, not a fill.
   return retcode == TRADE_RETCODE_REQUOTE ||
      retcode == TRADE_RETCODE_REJECT ||
      retcode == TRADE_RETCODE_CANCEL ||
      retcode == TRADE_RETCODE_INVALID ||
      retcode == TRADE_RETCODE_INVALID_VOLUME ||
      retcode == TRADE_RETCODE_INVALID_PRICE ||
      retcode == TRADE_RETCODE_INVALID_STOPS ||
      retcode == TRADE_RETCODE_TRADE_DISABLED ||
      retcode == TRADE_RETCODE_MARKET_CLOSED ||
      retcode == TRADE_RETCODE_NO_MONEY ||
      retcode == TRADE_RETCODE_PRICE_CHANGED ||
      retcode == TRADE_RETCODE_PRICE_OFF ||
      retcode == TRADE_RETCODE_INVALID_EXPIRATION ||
      retcode == TRADE_RETCODE_TOO_MANY_REQUESTS ||
      retcode == TRADE_RETCODE_NO_CHANGES ||
      retcode == TRADE_RETCODE_SERVER_DISABLES_AT ||
      retcode == TRADE_RETCODE_CLIENT_DISABLES_AT ||
      retcode == TRADE_RETCODE_FROZEN ||
      retcode == TRADE_RETCODE_INVALID_FILL ||
      retcode == TRADE_RETCODE_ONLY_REAL ||
      retcode == TRADE_RETCODE_LIMIT_ORDERS ||
      retcode == TRADE_RETCODE_LIMIT_VOLUME ||
      retcode == TRADE_RETCODE_INVALID_ORDER ||
      retcode == TRADE_RETCODE_POSITION_CLOSED ||
      retcode == TRADE_RETCODE_INVALID_CLOSE_VOLUME ||
      retcode == TRADE_RETCODE_CLOSE_ORDER_EXIST ||
      retcode == TRADE_RETCODE_LIMIT_POSITIONS ||
      retcode == TRADE_RETCODE_LONG_ONLY ||
      retcode == TRADE_RETCODE_SHORT_ONLY ||
      retcode == TRADE_RETCODE_CLOSE_ONLY ||
      retcode == TRADE_RETCODE_FIFO_CLOSE ||
      retcode == TRADE_RETCODE_HEDGE_PROHIBITED;
}


bool IsAmbiguousTradeRetcode(const uint retcode)
{
   // Includes PLACED, DONE_PARTIAL, ERROR, TIMEOUT, CONNECTION, LOCKED,
   // ORDER_CHANGED and every unknown/future enum value.  None may be resent.
   return retcode != TRADE_RETCODE_DONE &&
      !IsDefinitiveRejectTradeRetcode(retcode);
}


bool FindPositionByIdentifier(
   const ulong position_identifier,
   ulong &position_ticket
)
{
   position_ticket = 0;
   if(position_identifier == 0)
      return false;
   int total = PositionsTotal();
   for(int index = 0; index < total; index++)
   {
      ulong ticket = PositionGetTicket(index);
      if(ticket == 0)
         continue;
      ulong identifier =
         (ulong)PositionGetInteger(POSITION_IDENTIFIER);
      if(identifier == position_identifier)
      {
         position_ticket = ticket;
         return true;
      }
   }
   return false;
}


string FilledRiskAssessmentCode(
   const string action,
   const double volume,
   const double requested_entry,
   const double filled_entry,
   const double stop_loss,
   const double estimated_commission_per_lot,
   const double pre_send_estimated_risk
)
{
   if(!MathIsValidNumber(volume) || volume <= 0.0 ||
      !MathIsValidNumber(filled_entry) || filled_entry <= 0.0 ||
      !MathIsValidNumber(stop_loss) || stop_loss <= 0.0 ||
      !MathIsValidNumber(estimated_commission_per_lot) ||
      estimated_commission_per_lot < 0.0 ||
      !MathIsValidNumber(pre_send_estimated_risk) ||
      pre_send_estimated_risk < 0.00000001)
      return "RISK_UNAVAILABLE";
   ENUM_ORDER_TYPE type = action == "BUY"
      ? ORDER_TYPE_BUY
      : ORDER_TYPE_SELL;
   double stop_result = 0.0;
   if(!OrderCalcProfit(
         type,
         _Symbol,
         volume,
         filled_entry,
         NormalizeSymbolPrice(stop_loss),
         stop_result
      ) ||
      !MathIsValidNumber(stop_result) || stop_result >= 0.0)
      return "RISK_UNAVAILABLE";
   double actual_risk =
      -stop_result + estimated_commission_per_lot * volume;
   if(!MathIsValidNumber(actual_risk) || actual_risk < 0.00000001)
      return "RISK_UNAVAILABLE";
   bool slippage_reserve_exceeded = false;
   double point = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
   if(MathIsValidNumber(requested_entry) && requested_entry > 0.0 &&
      MathIsValidNumber(point) && point > 0.0)
   {
      double adverse_slippage_points = action == "BUY"
         ? MathMax(0.0, filled_entry - requested_entry) / point
         : MathMax(0.0, requested_entry - filled_entry) / point;
      if(adverse_slippage_points > (double)SlippagePoints + 0.00000001)
         slippage_reserve_exceeded = true;
   }
   double risk_tolerance = pre_send_estimated_risk * 0.000000001;
   if(actual_risk > pre_send_estimated_risk + risk_tolerance)
      return slippage_reserve_exceeded
         ? "SLIPPAGE_RESERVE_AND_RISK_ESTIMATE_EXCEEDED"
         : "RISK_ESTIMATE_EXCEEDED";
   if(slippage_reserve_exceeded)
      return "SLIPPAGE_RESERVE_EXCEEDED";
   return "WITHIN_ESTIMATE";
}


bool CaptureExecutionEvidence(
   const CommandPayload &command,
   const MqlTradeRequest &request,
   const MqlTradeResult &result,
   ulong &position_ticket,
   string &reason
)
{
   position_ticket = 0;
   if(result.deal == 0)
   {
      reason = "DEAL_TICKET_MISSING";
      return false;
   }
   ResetLastError();
   if(!HistoryDealSelect(result.deal))
   {
      reason = "DEAL_HISTORY_SELECT_FAILED";
      return false;
   }
   ENUM_DEAL_TYPE expected_deal_type =
      command.action == "BUY" ? DEAL_TYPE_BUY : DEAL_TYPE_SELL;
   ENUM_DEAL_TYPE actual_deal_type =
      (ENUM_DEAL_TYPE)HistoryDealGetInteger(result.deal, DEAL_TYPE);
   ENUM_DEAL_ENTRY entry =
      (ENUM_DEAL_ENTRY)HistoryDealGetInteger(result.deal, DEAL_ENTRY);
   long magic = HistoryDealGetInteger(result.deal, DEAL_MAGIC);
   string symbol = HistoryDealGetString(result.deal, DEAL_SYMBOL);
   string comment = HistoryDealGetString(result.deal, DEAL_COMMENT);
   double volume = HistoryDealGetDouble(result.deal, DEAL_VOLUME);
   double deal_price = HistoryDealGetDouble(result.deal, DEAL_PRICE);
   ulong position_identifier =
      (ulong)HistoryDealGetInteger(result.deal, DEAL_POSITION_ID);
   const double volume_tolerance = 0.00000001;
   if(actual_deal_type != expected_deal_type ||
      entry != DEAL_ENTRY_IN ||
      magic != (long)MagicNumber ||
      Uppercase(symbol) != Uppercase(_Symbol) ||
      comment != request.comment ||
      MathAbs(volume - request.volume) > volume_tolerance ||
      deal_price <= 0.0 ||
      position_identifier == 0)
   {
      reason = "DEAL_EXECUTION_EVIDENCE_MISMATCH";
      return false;
   }

   if(!FindPositionByIdentifier(
      position_identifier,
      position_ticket
   ))
   {
      reason = "POSITION_EVIDENCE_NOT_VISIBLE";
      return false;
   }
   ENUM_POSITION_TYPE expected_position_type =
      command.action == "BUY"
      ? POSITION_TYPE_BUY
      : POSITION_TYPE_SELL;
   ENUM_POSITION_TYPE actual_position_type =
      (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
   long position_magic = PositionGetInteger(POSITION_MAGIC);
   string position_symbol = PositionGetString(POSITION_SYMBOL);
   string position_comment = PositionGetString(POSITION_COMMENT);
   double position_volume = PositionGetDouble(POSITION_VOLUME);
   double position_sl = PositionGetDouble(POSITION_SL);
   double position_tp = PositionGetDouble(POSITION_TP);
   double point = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
   double price_tolerance = MathMax(0.00000001, point / 2.0);
   if(actual_position_type != expected_position_type ||
      position_magic != (long)MagicNumber ||
      Uppercase(position_symbol) != Uppercase(_Symbol) ||
      position_comment != request.comment ||
      MathAbs(position_volume - request.volume) > volume_tolerance ||
      MathAbs(position_sl - request.sl) > price_tolerance ||
      MathAbs(position_tp - request.tp) > price_tolerance)
   {
      reason = "POSITION_EXECUTION_EVIDENCE_MISMATCH";
      return false;
   }

   g_ack_has_execution_evidence = true;
   g_ack_filled_price = deal_price;
   g_ack_filled_slippage_points =
      point > 0.0
      ? MathAbs(deal_price - request.price) / point
      : 0.0;
   g_ack_actual_stop_loss = position_sl;
   g_ack_actual_take_profit = position_tp;
   g_ack_actual_magic_number = MagicNumber;
   g_ack_actual_comment = position_comment;
   g_ack_execution_state = "OPEN";
   string risk_assessment = FilledRiskAssessmentCode(
      command.action,
      request.volume,
      request.price,
      deal_price,
      position_sl,
      g_ack_estimated_commission_per_lot,
      g_ack_estimated_risk_money
   );
   // Keep verificationStatus inside the backend's closed ACK vocabulary.
   // The reason code carries the stronger post-fill truth without falsely
   // claiming that a verified broker position is unverified.
   g_ack_verification_status = "VERIFIED_OPEN";
   if(risk_assessment ==
      "SLIPPAGE_RESERVE_AND_RISK_ESTIMATE_EXCEEDED")
   {
      reason =
         "ORDER_VERIFIED_OPEN_SLIPPAGE_RESERVE_AND_RISK_ESTIMATE_EXCEEDED";
   }
   else if(risk_assessment == "RISK_ESTIMATE_EXCEEDED")
   {
      reason = "ORDER_VERIFIED_OPEN_RISK_ESTIMATE_EXCEEDED";
   }
   else if(risk_assessment == "SLIPPAGE_RESERVE_EXCEEDED")
   {
      reason = "ORDER_VERIFIED_OPEN_SLIPPAGE_RESERVE_EXCEEDED";
   }
   else if(risk_assessment == "RISK_UNAVAILABLE")
   {
      reason = "ORDER_VERIFIED_OPEN_RISK_UNAVAILABLE";
   }
   else
   {
      reason = "ORDER_VERIFIED_OPEN";
   }
   return true;
}


void WriteDuplicateAck(
   const CommandPayload &command,
   const string reason_code
)
{
   ResetAckExecutionEvidence();
   string payload = BuildAckJson(
      command,
      "DUPLICATE",
      reason_code,
      0,
      0,
      true
   );
   WriteCommonTextAtomic(AckPath(command.command_id), payload);
   AppendAudit(payload);
}


void RepairAckFromLedger(const CommandPayload &command)
{
   string raw = "";
   if(ReadCommonText(
      CommandLedgerPath(command.command_id),
      MaxCommandBytes,
      raw
   ))
      WriteCommonTextAtomic(AckPath(command.command_id), raw);
}


bool ReadProcessedCommandStatus(
   const CommandPayload &command,
   string &status
)
{
   status = "";
   string payload = "";
   if(!ReadCommonText(
         CommandLedgerPath(command.command_id),
         MaxCommandBytes,
         payload
      ))
      return false;
   string keys[];
   string values[];
   int quoted[];
   string reason = "";
   if(!ParseFlatJson(payload, keys, values, quoted, reason))
      return false;
   int index = FindKey(keys, "status");
   if(index < 0 || quoted[index] != 1)
      return false;
   status = Uppercase(values[index]);
   return true;
}


bool ReadSelectedPositionStringStrict(
   const ENUM_POSITION_PROPERTY_STRING property_id,
   string &value
)
{
   value = "";
   ResetLastError();
   return PositionGetString(property_id, value);
}


bool ReadSelectedOrderIntegerStrict(
   const ENUM_ORDER_PROPERTY_INTEGER property_id,
   long &value
)
{
   value = 0;
   ResetLastError();
   return OrderGetInteger(property_id, value);
}


bool ReadSelectedOrderDoubleStrict(
   const ENUM_ORDER_PROPERTY_DOUBLE property_id,
   double &value
)
{
   value = 0.0;
   ResetLastError();
   return OrderGetDouble(property_id, value);
}


bool ReadSelectedOrderStringStrict(
   const ENUM_ORDER_PROPERTY_STRING property_id,
   string &value
)
{
   value = "";
   ResetLastError();
   return OrderGetString(property_id, value);
}


bool ReadHistoryOrderIntegerStrict(
   const ulong ticket,
   const ENUM_ORDER_PROPERTY_INTEGER property_id,
   long &value
)
{
   value = 0;
   ResetLastError();
   return HistoryOrderGetInteger(ticket, property_id, value);
}


bool ReadHistoryOrderDoubleStrict(
   const ulong ticket,
   const ENUM_ORDER_PROPERTY_DOUBLE property_id,
   double &value
)
{
   value = 0.0;
   ResetLastError();
   return HistoryOrderGetDouble(ticket, property_id, value);
}


bool ReadHistoryOrderStringStrict(
   const ulong ticket,
   const ENUM_ORDER_PROPERTY_STRING property_id,
   string &value
)
{
   value = "";
   ResetLastError();
   return HistoryOrderGetString(ticket, property_id, value);
}


bool ReadHistoryDealStringStrict(
   const ulong ticket,
   const ENUM_DEAL_PROPERTY_STRING property_id,
   string &value
)
{
   value = "";
   ResetLastError();
   return HistoryDealGetString(ticket, property_id, value);
}


bool FindRecoveryOpenPosition(
   const CommandPayload &command,
   const double expected_volume,
   int &match_count,
   ulong &position_ticket,
   double &open_price,
   double &stop_loss,
   double &take_profit,
   string &reason
)
{
   match_count = 0;
   position_ticket = 0;
   open_price = 0.0;
   stop_loss = 0.0;
   take_profit = 0.0;
   string expected_comment = "HQ:" + command.command_id;
   ENUM_POSITION_TYPE expected_type = command.action == "BUY"
      ? POSITION_TYPE_BUY
      : POSITION_TYPE_SELL;
   const double volume_tolerance = 0.00000001;
   double price_tolerance = MathMax(
      0.00000001,
      SymbolInfoDouble(_Symbol, SYMBOL_POINT) / 2.0
   );
   int total = PositionsTotal();
   for(int index = 0; index < total; index++)
   {
      ulong ticket = PositionGetTicket(index);
      if(ticket == 0)
      {
         reason = "RECOVERY_POSITION_TELEMETRY_UNAVAILABLE";
         return false;
      }
      string comment = "";
      if(!ReadSelectedPositionStringStrict(POSITION_COMMENT, comment))
      {
         reason = "RECOVERY_POSITION_TELEMETRY_UNAVAILABLE";
         return false;
      }
      if(comment != expected_comment)
         continue;
      long magic = 0;
      long type_value = 0;
      string symbol = "";
      double volume = 0.0;
      double selected_open_price = 0.0;
      double selected_sl = 0.0;
      double selected_tp = 0.0;
      if(!ReadSelectedPositionIntegerStrict(POSITION_MAGIC, magic) ||
         !ReadSelectedPositionIntegerStrict(POSITION_TYPE, type_value) ||
         !ReadSelectedPositionStringStrict(POSITION_SYMBOL, symbol) ||
         !ReadSelectedPositionDoubleStrict(POSITION_VOLUME, volume) ||
         !ReadSelectedPositionDoubleStrict(POSITION_PRICE_OPEN, selected_open_price) ||
         !ReadSelectedPositionDoubleStrict(POSITION_SL, selected_sl) ||
         !ReadSelectedPositionDoubleStrict(POSITION_TP, selected_tp))
      {
         reason = "RECOVERY_POSITION_TELEMETRY_UNAVAILABLE";
         return false;
      }
      if(magic != (long)MagicNumber ||
         (ENUM_POSITION_TYPE)type_value != expected_type ||
         Uppercase(symbol) != command.symbol ||
         MathAbs(volume - expected_volume) > volume_tolerance ||
         MathAbs(selected_sl - NormalizeSymbolPrice(command.stop_loss)) > price_tolerance ||
         MathAbs(selected_tp - NormalizeSymbolPrice(command.take_profit)) > price_tolerance ||
         selected_open_price <= 0.0)
      {
         reason = "RECOVERY_POSITION_IDENTITY_MISMATCH";
         return false;
      }
      match_count++;
      position_ticket = ticket;
      open_price = selected_open_price;
      stop_loss = selected_sl;
      take_profit = selected_tp;
   }
   return true;
}


bool FindRecoveryCurrentOrders(
   const CommandPayload &command,
   const double expected_volume,
   int &match_count,
   ulong &matched_ticket,
   string &reason
)
{
   match_count = 0;
   matched_ticket = 0;
   string expected_comment = "HQ:" + command.command_id;
   ENUM_ORDER_TYPE expected_type = command.action == "BUY"
      ? ORDER_TYPE_BUY
      : ORDER_TYPE_SELL;
   const double volume_tolerance = 0.00000001;
   double price_tolerance = MathMax(
      0.00000001,
      SymbolInfoDouble(_Symbol, SYMBOL_POINT) / 2.0
   );
   int total = OrdersTotal();
   for(int index = 0; index < total; index++)
   {
      ulong ticket = OrderGetTicket(index);
      if(ticket == 0)
      {
         reason = "RECOVERY_ORDER_TELEMETRY_UNAVAILABLE";
         return false;
      }
      string comment = "";
      if(!ReadSelectedOrderStringStrict(ORDER_COMMENT, comment))
      {
         reason = "RECOVERY_ORDER_TELEMETRY_UNAVAILABLE";
         return false;
      }
      if(comment != expected_comment)
         continue;
      long magic = 0;
      long type_value = 0;
      string symbol = "";
      double volume = 0.0;
      double stop_loss = 0.0;
      double take_profit = 0.0;
      if(!ReadSelectedOrderIntegerStrict(ORDER_MAGIC, magic) ||
         !ReadSelectedOrderIntegerStrict(ORDER_TYPE, type_value) ||
         !ReadSelectedOrderStringStrict(ORDER_SYMBOL, symbol) ||
         !ReadSelectedOrderDoubleStrict(ORDER_VOLUME_INITIAL, volume) ||
         !ReadSelectedOrderDoubleStrict(ORDER_SL, stop_loss) ||
         !ReadSelectedOrderDoubleStrict(ORDER_TP, take_profit))
      {
         reason = "RECOVERY_ORDER_TELEMETRY_UNAVAILABLE";
         return false;
      }
      if(magic != (long)MagicNumber ||
         (ENUM_ORDER_TYPE)type_value != expected_type ||
         Uppercase(symbol) != command.symbol ||
         MathAbs(volume - expected_volume) > volume_tolerance ||
         MathAbs(stop_loss - NormalizeSymbolPrice(command.stop_loss)) > price_tolerance ||
         MathAbs(take_profit - NormalizeSymbolPrice(command.take_profit)) > price_tolerance)
      {
         reason = "RECOVERY_ORDER_IDENTITY_MISMATCH";
         return false;
      }
      match_count++;
      matched_ticket = ticket;
   }
   return true;
}


bool FindRecoveryHistory(
   const CommandPayload &command,
   const double expected_volume,
   int &order_match_count,
   ulong &order_ticket,
   double &order_stop_loss,
   double &order_take_profit,
   int &deal_match_count,
   ulong &deal_ticket,
   ulong &position_identifier,
   double &entry_price,
   double &entry_volume,
   double &exit_volume,
   int &closed_at,
   double &closed_pnl,
   string &reason
)
{
   order_match_count = 0;
   order_ticket = 0;
   order_stop_loss = 0.0;
   order_take_profit = 0.0;
   deal_match_count = 0;
   deal_ticket = 0;
   position_identifier = 0;
   entry_price = 0.0;
   entry_volume = 0.0;
   exit_volume = 0.0;
   closed_at = 0;
   closed_pnl = 0.0;
   datetime now = TimeCurrent();
   datetime utc_now = TimeGMT();
   long command_age_seconds =
      (long)utc_now - (long)command.issued_at;
   if(now <= 0 || utc_now <= 0 ||
      command_age_seconds < -(long)MaxClockSkewSeconds)
   {
      reason = "RECOVERY_HISTORY_TELEMETRY_UNAVAILABLE";
      return false;
   }
   // DEAL/ORDER history uses broker-server time. Convert the UTC command age
   // into that clock domain and include a one-day DST/offset safety cushion.
   long lookback_seconds = command_age_seconds + 86400;
   if(lookback_seconds < 300)
      lookback_seconds = 300;
   datetime since = now - (datetime)lookback_seconds;
   if(since <= 0 || !HistorySelect(since, now))
   {
      reason = "RECOVERY_HISTORY_TELEMETRY_UNAVAILABLE";
      return false;
   }
   string expected_comment = "HQ:" + command.command_id;
   ENUM_ORDER_TYPE expected_order_type = command.action == "BUY"
      ? ORDER_TYPE_BUY
      : ORDER_TYPE_SELL;
   ENUM_DEAL_TYPE expected_deal_type = command.action == "BUY"
      ? DEAL_TYPE_BUY
      : DEAL_TYPE_SELL;
   const double volume_tolerance = 0.00000001;
   double price_tolerance = MathMax(
      0.00000001,
      SymbolInfoDouble(_Symbol, SYMBOL_POINT) / 2.0
   );
   int order_total = HistoryOrdersTotal();
   if(order_total < 0)
   {
      reason = "RECOVERY_HISTORY_TELEMETRY_UNAVAILABLE";
      return false;
   }
   for(int index = 0; index < order_total; index++)
   {
      ulong ticket = HistoryOrderGetTicket(index);
      if(ticket == 0)
      {
         reason = "RECOVERY_HISTORY_TELEMETRY_UNAVAILABLE";
         return false;
      }
      string comment = "";
      if(!ReadHistoryOrderStringStrict(ticket, ORDER_COMMENT, comment))
      {
         reason = "RECOVERY_HISTORY_TELEMETRY_UNAVAILABLE";
         return false;
      }
      if(comment != expected_comment)
         continue;
      long magic = 0;
      long type_value = 0;
      string symbol = "";
      double volume = 0.0;
      double stop_loss = 0.0;
      double take_profit = 0.0;
      if(!ReadHistoryOrderIntegerStrict(ticket, ORDER_MAGIC, magic) ||
         !ReadHistoryOrderIntegerStrict(ticket, ORDER_TYPE, type_value) ||
         !ReadHistoryOrderStringStrict(ticket, ORDER_SYMBOL, symbol) ||
         !ReadHistoryOrderDoubleStrict(ticket, ORDER_VOLUME_INITIAL, volume) ||
         !ReadHistoryOrderDoubleStrict(ticket, ORDER_SL, stop_loss) ||
         !ReadHistoryOrderDoubleStrict(ticket, ORDER_TP, take_profit))
      {
         reason = "RECOVERY_HISTORY_TELEMETRY_UNAVAILABLE";
         return false;
      }
      if(magic != (long)MagicNumber ||
         (ENUM_ORDER_TYPE)type_value != expected_order_type ||
         Uppercase(symbol) != command.symbol ||
         MathAbs(volume - expected_volume) > volume_tolerance ||
         MathAbs(stop_loss - NormalizeSymbolPrice(command.stop_loss)) > price_tolerance ||
         MathAbs(take_profit - NormalizeSymbolPrice(command.take_profit)) > price_tolerance)
      {
         reason = "RECOVERY_HISTORY_ORDER_IDENTITY_MISMATCH";
         return false;
      }
      order_match_count++;
      order_ticket = ticket;
      order_stop_loss = stop_loss;
      order_take_profit = take_profit;
   }

   int deal_total = HistoryDealsTotal();
   if(deal_total < 0)
   {
      reason = "RECOVERY_HISTORY_TELEMETRY_UNAVAILABLE";
      return false;
   }
   for(int index = 0; index < deal_total; index++)
   {
      ulong ticket = HistoryDealGetTicket(index);
      if(ticket == 0)
      {
         reason = "RECOVERY_HISTORY_TELEMETRY_UNAVAILABLE";
         return false;
      }
      string comment = "";
      if(!ReadHistoryDealStringStrict(ticket, DEAL_COMMENT, comment))
      {
         reason = "RECOVERY_HISTORY_TELEMETRY_UNAVAILABLE";
         return false;
      }
      if(comment != expected_comment)
         continue;
      long magic = 0;
      long type_value = 0;
      long entry_value = 0;
      long position_id_value = 0;
      string symbol = "";
      double volume = 0.0;
      double price = 0.0;
      if(!ReadHistoryDealIntegerStrict(ticket, DEAL_MAGIC, magic) ||
         !ReadHistoryDealIntegerStrict(ticket, DEAL_TYPE, type_value) ||
         !ReadHistoryDealIntegerStrict(ticket, DEAL_ENTRY, entry_value) ||
         !ReadHistoryDealIntegerStrict(ticket, DEAL_POSITION_ID, position_id_value) ||
         !ReadHistoryDealStringStrict(ticket, DEAL_SYMBOL, symbol) ||
         !ReadHistoryDealDoubleStrict(ticket, DEAL_VOLUME, volume) ||
         !ReadHistoryDealDoubleStrict(ticket, DEAL_PRICE, price))
      {
         reason = "RECOVERY_HISTORY_TELEMETRY_UNAVAILABLE";
         return false;
      }
      if((ENUM_DEAL_ENTRY)entry_value != DEAL_ENTRY_IN)
         continue;
      if(magic != (long)MagicNumber ||
         (ENUM_DEAL_TYPE)type_value != expected_deal_type ||
         Uppercase(symbol) != command.symbol ||
         MathAbs(volume - expected_volume) > volume_tolerance ||
         price <= 0.0 ||
         position_id_value <= 0)
      {
         reason = "RECOVERY_HISTORY_DEAL_IDENTITY_MISMATCH";
         return false;
      }
      deal_match_count++;
      deal_ticket = ticket;
      position_identifier = (ulong)position_id_value;
      entry_price = price;
      entry_volume = volume;
   }

   if(deal_match_count == 1 && position_identifier > 0)
   {
      for(int index = 0; index < deal_total; index++)
      {
         ulong ticket = HistoryDealGetTicket(index);
         if(ticket == 0)
         {
            reason = "RECOVERY_HISTORY_TELEMETRY_UNAVAILABLE";
            return false;
         }
         long position_id_value = 0;
         if(!ReadHistoryDealIntegerStrict(
               ticket,
               DEAL_POSITION_ID,
               position_id_value
            ))
         {
            reason = "RECOVERY_HISTORY_TELEMETRY_UNAVAILABLE";
            return false;
         }
         if((ulong)position_id_value != position_identifier)
            continue;
         long entry_value = 0;
         long time_value = 0;
         double volume = 0.0;
         double profit = 0.0;
         double swap = 0.0;
         double commission = 0.0;
         double fee = 0.0;
         if(!ReadHistoryDealIntegerStrict(ticket, DEAL_ENTRY, entry_value) ||
            !ReadHistoryDealIntegerStrict(ticket, DEAL_TIME, time_value) ||
            !ReadHistoryDealDoubleStrict(ticket, DEAL_VOLUME, volume) ||
            !ReadHistoryDealDoubleStrict(ticket, DEAL_PROFIT, profit) ||
            !ReadHistoryDealDoubleStrict(ticket, DEAL_SWAP, swap) ||
            !ReadHistoryDealDoubleStrict(ticket, DEAL_COMMISSION, commission) ||
            !ReadHistoryDealDoubleStrict(ticket, DEAL_FEE, fee))
         {
            reason = "RECOVERY_HISTORY_TELEMETRY_UNAVAILABLE";
            return false;
         }
         closed_pnl += profit + swap + commission + fee;
         if((ENUM_DEAL_ENTRY)entry_value == DEAL_ENTRY_OUT ||
            (ENUM_DEAL_ENTRY)entry_value == DEAL_ENTRY_OUT_BY)
         {
            exit_volume += volume;
            if(time_value > closed_at)
               closed_at = (int)time_value;
         }
      }
   }
   return true;
}


void MarkRecoveryUnknown(
   const CommandPayload &command,
   const string reason
)
{
   g_ack_verification_status = "SELECT_FAILED";
   g_ack_execution_state = "UNKNOWN";
   FinalizeCommand(command, "EXECUTION_UNKNOWN", reason, 0, 0);
}


void ReconcileExecutingCommand(
   const CommandPayload &command,
   const string signed_raw
)
{
   ExecutionAttempt attempt;
   string reason = "";
   if(!ReadExecutionAttempt(command, signed_raw, attempt, reason))
   {
      MarkRecoveryUnknown(command, reason);
      return;
   }
   // The volume and monetary evidence are immutable command state. Recovery
   // must never resize from a newer tick, balance, or equity value.
   SetAckSizingEvidence(
      attempt.expected_volume,
      attempt.position_sizing_mode,
      attempt.risk_percent,
      attempt.risk_capital_base,
      attempt.estimated_commission_per_lot,
      attempt.risk_capital_amount,
      attempt.estimated_risk_money
   );
   if(!AcquireAccountExecutionLock())
   {
      MarkRecoveryUnknown(command, "RECONCILIATION_LOCK_UNAVAILABLE");
      return;
   }

   int position_count = 0;
   ulong position_ticket = 0;
   double open_price = 0.0;
   double position_sl = 0.0;
   double position_tp = 0.0;
   int active_order_count = 0;
   ulong active_order_ticket = 0;
   int history_order_count = 0;
   ulong history_order_ticket = 0;
   double history_order_sl = 0.0;
   double history_order_tp = 0.0;
   int deal_count = 0;
   ulong deal_ticket = 0;
   ulong position_identifier = 0;
   double entry_price = 0.0;
   double entry_volume = 0.0;
   double exit_volume = 0.0;
   int closed_at = 0;
   double closed_pnl = 0.0;
   bool telemetry_ready =
       FindRecoveryOpenPosition(
          command,
          attempt.expected_volume,
         position_count,
         position_ticket,
         open_price,
         position_sl,
         position_tp,
         reason
      ) &&
       FindRecoveryCurrentOrders(
          command,
          attempt.expected_volume,
         active_order_count,
         active_order_ticket,
         reason
      ) &&
       FindRecoveryHistory(
          command,
          attempt.expected_volume,
         history_order_count,
         history_order_ticket,
         history_order_sl,
         history_order_tp,
         deal_count,
         deal_ticket,
         position_identifier,
         entry_price,
         entry_volume,
         exit_volume,
         closed_at,
         closed_pnl,
         reason
      );
   ReleaseAccountExecutionLock();
   if(!telemetry_ready)
   {
      MarkRecoveryUnknown(command, reason);
      return;
   }

   ulong expected_order = (ulong)StringToInteger(attempt.order_id);
   ulong expected_deal = (ulong)StringToInteger(attempt.deal_id);
   bool order_id_matches = expected_order == 0 ||
      expected_order == active_order_ticket ||
      expected_order == history_order_ticket;
   bool deal_id_matches = expected_deal == 0 || expected_deal == deal_ticket;
   if(!order_id_matches || !deal_id_matches ||
      position_count > 1 || active_order_count > 1 ||
      history_order_count > 1 || deal_count > 1)
   {
      MarkRecoveryUnknown(command, "MULTIPLE_OR_MISMATCHED_RECOVERY_EVIDENCE");
      return;
   }

   if(position_count == 1 && active_order_count == 0)
   {
      g_ack_has_execution_evidence = true;
      g_ack_filled_price = open_price;
      g_ack_filled_slippage_points = 0.0;
      g_ack_actual_stop_loss = position_sl;
      g_ack_actual_take_profit = position_tp;
      g_ack_actual_magic_number = MagicNumber;
      g_ack_actual_comment = attempt.broker_comment;
      g_ack_verification_status = "VERIFIED_OPEN";
      g_ack_execution_state = "OPEN";
      FinalizeCommand(
         command,
         "EXECUTED",
         "RECOVERED_ORDER_FOUND",
         position_ticket,
         0
      );
      return;
   }

   const double volume_tolerance = 0.00000001;
   if(position_count == 0 && active_order_count == 0 &&
      history_order_count == 1 && deal_count == 1 &&
      exit_volume + volume_tolerance >= entry_volume &&
      closed_at > 0)
   {
      g_ack_has_execution_evidence = true;
      g_ack_filled_price = entry_price;
      g_ack_filled_slippage_points = 0.0;
      g_ack_actual_stop_loss = history_order_sl;
      g_ack_actual_take_profit = history_order_tp;
      g_ack_actual_magic_number = MagicNumber;
      g_ack_actual_comment = attempt.broker_comment;
      g_ack_verification_status = "VERIFIED_CLOSED";
      g_ack_execution_state = "CLOSED";
      g_ack_closed_at = closed_at;
      g_ack_closed_pnl = closed_pnl;
      g_ack_has_closed_pnl = true;
      FinalizeCommand(
         command,
         "EXECUTED",
         "RECOVERED_ORDER_FOUND",
         position_identifier,
         0
      );
      return;
   }

   MarkRecoveryUnknown(command, "RESTART_RECONCILIATION_REQUIRED");
}


void ExecuteCommand(
   const CommandPayload &command,
   const string signed_raw,
   const double order_volume,
   const double risk_capital_amount,
   const double estimated_risk_money
)
{
   SetAckSizingEvidence(
      order_volume,
      PositionSizingModeName(),
      EffectiveRiskPercent(),
      RiskCapitalBaseName(),
      EffectiveEstimatedCommissionPerLot(),
      risk_capital_amount,
      estimated_risk_money
   );
   string marker_reason = "";
   if(!ReverifyCommandEnvelope(signed_raw, command, marker_reason))
   {
      FinalizeCommand(command, "REJECTED", marker_reason, 0, 0);
      return;
   }
   MqlTradeResult executing_result;
   ZeroMemory(executing_result);
   string executing_payload = BuildAckJson(
      command,
      "EXECUTING",
      "EXECUTION_STARTED",
      0,
      0,
      true
   );
   // Persist the opaque account/stream/full-command digest plus both durable
   // idempotency markers before any one-bar claim or broker call.  A partial
   // write is fail-closed and ProcessCommandFile will reconcile, never resend.
   if(!WriteExecutionAttempt(
         command,
         signed_raw,
         order_volume,
         "EXECUTING",
         false,
         executing_result,
         0
      ) ||
      !WriteExecutionMarkers(command, executing_payload))
   {
      string failed_payload = BuildAckJson(
         command,
         "FAILED_FINAL",
         "IDEMPOTENCY_STATE_WRITE_FAILED",
         0,
         GetLastError(),
         false
      );
      WriteCommonTextAtomic(AckPath(command.command_id), failed_payload);
      AppendAudit(failed_payload);
      return;
   }
   WriteCommonTextAtomic(AckPath(command.command_id), executing_payload);
   AppendAudit(executing_payload);

   if(!AcquireAccountExecutionLock())
   {
      FinalizeCommand(
         command,
         "REJECTED",
         "ACCOUNT_EXECUTION_LOCK_UNAVAILABLE",
         0,
         GetLastError()
      );
      return;
   }

   do
   {
      string reason = "";
       if(!ValidateRuntime(command, order_volume, reason))
      {
         FinalizeCommand(command, "REJECTED", reason, 0, 0);
         break;
      }

      MqlTick tick;
      if(!ReadFreshTick(tick, reason))
      {
         FinalizeCommand(command, "REJECTED", reason, 0, 0);
         break;
      }
      MqlTradeRequest request;
      MqlTradeCheckResult check_result;
      double final_estimated_risk_money = 0.0;
       if(!ValidateStopsWithTick(command, tick, reason) ||
          !ValidateRiskEnvelope(
             command,
             tick,
             order_volume,
             final_estimated_risk_money,
             reason
          ) ||
          !BuildTradeRequest(
             command,
             tick,
             order_volume,
             request,
             reason
          ) ||
          !CheckTradeRequest(request, check_result, reason))
      {
         FinalizeCommand(command, "REJECTED", reason, 0, 0);
         break;
      }

      // Refresh only the monetary estimate from the exact under-lock tick
      // used to build the request. Volume and policy stay immutable.
      g_ack_estimated_risk_money = final_estimated_risk_money;
      string final_executing_payload = BuildAckJson(
         command,
         "EXECUTING",
         "FINAL_RISK_VALIDATED",
         0,
         0,
         true
      );
      if(!WriteExecutionAttempt(
            command,
            signed_raw,
            order_volume,
            "EXECUTING",
            false,
            executing_result,
            0
         ) ||
         !WriteExecutionMarkers(command, final_executing_payload))
      {
         FinalizeCommand(
            command,
            "FAILED_FINAL",
            "FINAL_RISK_STATE_WRITE_FAILED",
            0,
            GetLastError()
         );
         break;
      }
      WriteCommonTextAtomic(
         AckPath(command.command_id),
         final_executing_payload
      );
      AppendAudit(final_executing_payload);

      if(!ReverifyCommandEnvelope(signed_raw, command, reason))
      {
         FinalizeCommand(command, "REJECTED", reason, 0, 0);
         break;
      }
      if(!WriteLastOrderBar(command.bar_time))
      {
         FinalizeCommand(
            command,
            "FAILED_FINAL",
            "ORDER_BAR_STATE_WRITE_FAILED",
            0,
            GetLastError()
         );
         break;
      }
      if(FileIsExist(KillMarkerPath(), FILE_COMMON))
      {
         FinalizeCommand(
            command,
            "REJECTED",
            "KILL_SWITCH_ACTIVE",
            0,
            0
         );
         break;
      }
      if(command.expires_at < NowUtc())
      {
         FinalizeCommand(
            command,
            "REJECTED",
            "COMMAND_EXPIRED",
            0,
            0
         );
         break;
      }
      if(!ReverifyCommandEnvelope(signed_raw, command, reason))
      {
         FinalizeCommand(command, "REJECTED", reason, 0, 0);
         break;
      }
      // Re-check the persistent account owner immediately before the only
      // broker send. This also detects an account/server switch after OnInit.
      if(GatewayMode == GATEWAY_LIVE &&
         !LiveAccountOwnerLockReady(reason))
      {
         FinalizeCommand(command, "REJECTED", reason, 0, 0);
         break;
      }

      MqlTradeResult result;
      ZeroMemory(result);
      ResetLastError();
      bool sent = OrderSend(request, result);
      int api_error = GetLastError();
      if(!WriteExecutionAttempt(
             command,
             signed_raw,
             order_volume,
             "ORDER_SEND_RETURNED",
            sent,
            result,
            api_error
         ))
      {
         g_ack_verification_status = "SELECT_FAILED";
         g_ack_execution_state = "UNKNOWN";
         FinalizeCommand(
            command,
            "EXECUTION_UNKNOWN",
            "ORDER_SEND_RESULT_PERSIST_FAILED",
            0,
            api_error
         );
         break;
      }
      if(!sent)
      {
         if(result.deal > 0 || result.order > 0 ||
            IsAmbiguousTradeRetcode(result.retcode))
         {
            g_ack_verification_status = "SELECT_FAILED";
            g_ack_execution_state = "UNKNOWN";
            FinalizeCommand(
               command,
               "EXECUTION_UNKNOWN",
               "ORDER_SEND_API_UNCERTAIN",
               0,
               api_error
            );
         }
         else
         {
            FinalizeCommand(
               command,
               "FAILED_FINAL",
               "ORDER_SEND_API_FAILED",
               0,
               api_error
            );
         }
         break;
      }
      if(result.retcode != TRADE_RETCODE_DONE)
      {
         if(result.deal > 0 || result.order > 0 ||
            IsAmbiguousTradeRetcode(result.retcode))
         {
            g_ack_verification_status = "SELECT_FAILED";
            g_ack_execution_state = "UNKNOWN";
            FinalizeCommand(
               command,
               "EXECUTION_UNKNOWN",
               BrokerRetcodeReason(result.retcode),
               0,
               (int)result.retcode
            );
         }
         else
         {
            FinalizeCommand(
               command,
               "FAILED_FINAL",
               BrokerRetcodeReason(result.retcode),
               0,
               (int)result.retcode
            );
         }
         break;
      }

      ulong position_ticket = 0;
      bool verified = false;
      string verification_reason = "";
      for(int attempt = 0; attempt < 10; attempt++)
      {
         if(CaptureExecutionEvidence(
            command,
            request,
            result,
            position_ticket,
            verification_reason
         ))
         {
            verified = true;
            break;
         }
         if(attempt < 9)
            Sleep(50);
      }
      if(!verified)
      {
         g_ack_verification_status = "MISMATCH";
         g_ack_execution_state = "UNKNOWN";
         FinalizeCommand(
            command,
            "EXECUTION_UNKNOWN",
            verification_reason,
            position_ticket,
            0
         );
         break;
      }

      UpdateRiskTelemetry(true);
      FinalizeCommand(
         command,
         "EXECUTED",
         verification_reason,
         position_ticket,
         0
      );
   }
   while(false);

   ReleaseAccountExecutionLock();
}


void ProcessCommandFile()
{
   ResetAckExecutionEvidence();
   string signed_raw = "";
   if(!ReadCommonText(CommandPath(), MaxCommandBytes, signed_raw))
      return;
   signed_raw = Trimmed(signed_raw);

   CommandPayload command;
   string reason = "";
   if(!ParseCommand(signed_raw, command, reason))
   {
      if(IsCommandIdentifier(command.command_id) &&
         IsIdempotencyIdentifier(command.idempotency_key))
         FinalizeCommand(command, "REJECTED", reason, 0, 0);
      else
         PublishSystemAck("REJECTED", reason);
      return;
   }

   bool execution_attempt_exists = FileIsExist(
      ExecutionAttemptPath(command.command_id),
      FILE_COMMON
   );
   if(FileIsExist(
         CommandLedgerPath(command.command_id),
         FILE_COMMON
      ))
   {
      string processed_status = "";
      if(ReadProcessedCommandStatus(command, processed_status) &&
         (processed_status == "EXECUTING" ||
          processed_status == "EXECUTION_UNKNOWN"))
      {
         ReconcileExecutingCommand(command, signed_raw);
         return;
      }
      if(StringLen(processed_status) == 0 && execution_attempt_exists)
      {
         ReconcileExecutingCommand(command, signed_raw);
         return;
      }
      if(!FileIsExist(AckPath(command.command_id), FILE_COMMON))
         RepairAckFromLedger(command);
      return;
   }
   if(execution_attempt_exists)
   {
      ReconcileExecutingCommand(command, signed_raw);
      return;
   }
   if(FileIsExist(
      IdempotencyLedgerPath(command.idempotency_key),
      FILE_COMMON
   ))
   {
      WriteDuplicateAck(
         command,
         "IDEMPOTENCY_KEY_ALREADY_SEEN"
      );
      return;
   }

   MqlTick sizing_tick;
   double order_volume = 0.0;
   double risk_capital_amount = 0.0;
   double estimated_risk_money = 0.0;
   if(!ReadFreshTick(sizing_tick, reason) ||
      !ValidateStopsWithTick(command, sizing_tick, reason) ||
      !ResolveOrderVolume(
         command,
         sizing_tick,
         order_volume,
         risk_capital_amount,
         estimated_risk_money,
         reason
      ))
   {
      FinalizeCommand(command, "REJECTED", reason, 0, 0);
      return;
   }
   SetAckSizingEvidence(
      order_volume,
      PositionSizingModeName(),
      EffectiveRiskPercent(),
      RiskCapitalBaseName(),
      EffectiveEstimatedCommissionPerLot(),
      risk_capital_amount,
      estimated_risk_money
   );
   if(!ValidateRuntime(command, order_volume, reason))
   {
      FinalizeCommand(command, "REJECTED", reason, 0, 0);
      return;
   }
   if(GatewayMode == GATEWAY_SHADOW)
   {
      FinalizeCommand(
         command,
         "SHADOWED",
         "VALIDATED_WITHOUT_ORDER_SEND",
         0,
         0
      );
      return;
   }
   ExecuteCommand(
      command,
      signed_raw,
      order_volume,
      risk_capital_amount,
      estimated_risk_money
   );
}


void UpdateChartStatus()
{
   UpdateRiskTelemetry(false);
   string live_owner_reason = "";
   bool live_owner_ready =
      LiveAccountOwnerLockReady(live_owner_reason);
   string state = "READY";
   if(FileIsExist(KillMarkerPath(), FILE_COMMON))
      state = "KILL SWITCH ACTIVE";
   string snapshot_state = "WAITING";
   if(g_last_snapshot_success_at > 0 && g_last_snapshot_write_ok)
   {
      snapshot_state =
         "READY " +
         TimeToString(
            (datetime)g_last_snapshot_success_at,
            TIME_SECONDS
         ) +
         " UTC";
   }
   else if(g_last_snapshot_attempt_at > 0)
      snapshot_state = "WRITE ERROR";
   Comment(
      "MetafxHQ Unified MT5 Snapshot + Trade Gateway\n",
      "Safety: HEDGING ACCOUNT ONLY\n",
      "Mode: ", ModeName(), "\n",
      "LiveArmed: ", LiveArmed ? "true" : "false", "\n",
      "SingleHostLiveAcknowledged: ",
         SingleHostLiveAcknowledged ? "true" : "false", "\n",
      "Live Owner Lock: ",
         GatewayMode != GATEWAY_LIVE
         ? "not required"
         : (live_owner_ready ? "ready" : live_owner_reason), "\n",
      "Live Safety Scope: ONE WINDOWS USER / ONE HOST ONLY\n",
      "Cross-VPS Distributed Lock: false\n",
      "Channel: ", SnapshotChannel, "\n",
      "Chart: ", _Symbol, " ", CurrentTimeframeName(), "\n",
      "Snapshot: ", snapshot_state, "\n",
      "Position Sizing: ", PositionSizingModeName(), "\n",
      "Fixed Lot: ", DoubleToString(FixedLot, LotDigits()), "\n",
      "Risk Percent: ",
         DoubleToString(EffectiveRiskPercent(), 8), "% of ",
         RiskCapitalBaseName(), "\n",
      "Estimated Commission/Lot: ",
         DoubleToString(EffectiveEstimatedCommissionPerLot(), 8), " ",
         AccountCurrency(), "\n",
      "Risk Guard: ", g_cached_execution_guard_reason, "\n",
      "State: ", state
   );
}


bool RecordInitDiagnostic(
   const string severity,
   const string stage,
   const string reason_code,
   const int return_code
)
{
   if(!IsSafeChannel(SnapshotChannel))
      return false;
   EnsureFolders();
   string payload = "{";
   payload += "\"schemaVersion\":\"metafx-hq-mt4-init-status-v1\",";
   payload += "\"eaVersion\":" + JsonString(EA_VERSION) + ",";
   payload += "\"channelId\":" + JsonString(SnapshotChannel) + ",";
   payload += "\"profile\":" + JsonString(EA_PROFILE) + ",";
   payload += "\"gatewayMode\":" + JsonString(ModeName()) + ",";
   payload += "\"accountMode\":" + JsonString(AccountModeName()) + ",";
   payload += "\"liveArmed\":" + JsonBoolean(LiveArmed) + ",";
   payload += "\"severity\":" + JsonString(severity) + ",";
   payload += "\"stage\":" + JsonString(stage) + ",";
   payload += "\"reasonCode\":" + JsonString(reason_code) + ",";
   payload += "\"warningCode\":" + JsonString(g_init_warning_code) + ",";
   payload += "\"portfolioPolicyLeaseOpenErrorCode\":" +
      IntegerToString(g_portfolio_policy_lease_open_error) + ",";
   payload += "\"portfolioPolicyLeaseScanErrorCode\":" +
      IntegerToString(g_portfolio_policy_lease_scan_error) + ",";
   payload += "\"portfolioPolicyLeaseExpandedPathLength\":" +
      IntegerToString(g_portfolio_policy_lease_expanded_path_length) + ",";
   payload += "\"portfolioPolicyLeaseMaxPathLength\":" +
      IntegerToString(PORTFOLIO_POLICY_MAX_EXPANDED_PATH_LENGTH) + ",";
   payload += "\"returnCode\":" + IntegerToString(return_code) + ",";
   payload += "\"observedAt\":" + IntegerToString(NowUtc());
   payload += "}";
   bool status_ok = WriteCommonTextAtomic(InitStatusPath(), payload);
   bool audit_ok = AppendAudit(payload);
   return status_ok && audit_ok;
}


int InitFailure(
   const int return_code,
   const string stage,
   const string reason_code,
   const string message
)
{
   Print(message);
   RecordInitDiagnostic("error", stage, reason_code, return_code);
   return return_code;
}


int OnInit()
{
   g_init_warning_code = "";
   g_trusted_signing_key_id =
      NormalizeSigningKeyId(TrustedSigningKeyId);

   if(!IsSafeChannel(SnapshotChannel))
   {
      Print("MetafxHQ MT5: SNAPSHOT_CHANNEL_INVALID");
      return INIT_PARAMETERS_INCORRECT;
   }
   string mode_reason = "";
   if(!ValidateConfiguredModes(mode_reason))
   {
      return InitFailure(
         INIT_PARAMETERS_INCORRECT,
         "inputs",
         mode_reason,
         "MetafxHQ MT5: " + mode_reason
      );
   }
   if(PositionLifecycleMode != LIFECYCLE_SLTP_ONLY)
   {
      return InitFailure(
         INIT_PARAMETERS_INCORRECT,
         "inputs",
         "MT5_POSITION_LIFECYCLE_UNSUPPORTED",
         "MetafxHQ MT5: MT5_POSITION_LIFECYCLE_UNSUPPORTED"
      );
   }
   if(GatewayMode == GATEWAY_LIVE && IsDemo())
   {
      return InitFailure(
         INIT_PARAMETERS_INCORRECT,
         "account_mode",
         "LIVE_MODE_REQUIRES_NON_DEMO_ACCOUNT",
         "MetafxHQ MT5: LIVE requires a real trading account. Use DEMO mode for demo accounts."
      );
   }
   if(!IsHedgingAccount())
   {
      return InitFailure(
         INIT_FAILED,
         "account_mode",
         "MT5_HEDGING_ACCOUNT_REQUIRED",
         "MetafxHQ MT5: MT5_HEDGING_ACCOUNT_REQUIRED"
      );
   }

   string supplied_pin = Trimmed(TrustedSigningKeyId);
   if(StringLen(supplied_pin) > 0 &&
      !IsSigningKeyId(g_trusted_signing_key_id))
   {
      if(GatewayMode == GATEWAY_LIVE && LiveArmed &&
         SingleHostLiveAcknowledged)
      {
         return InitFailure(
            INIT_PARAMETERS_INCORRECT,
            "signing",
            "LIVE_SIGNING_KEY_PIN_INVALID",
            "MetafxHQ MT5: LIVE_SIGNING_KEY_PIN_INVALID"
         );
      }
      g_trusted_signing_key_id = "";
   }

   g_crypto_self_test_ok = CryptoSelfTest();
   if(!g_crypto_self_test_ok)
   {
      return InitFailure(
         INIT_FAILED,
         "crypto",
         "CRYPTO_SELF_TEST_FAILED",
         "MetafxHQ MT5: CRYPTO_SELF_TEST_FAILED"
      );
   }

   if(PollIntervalSeconds != 1 ||
      SnapshotIntervalSeconds < 2 ||
      SnapshotIntervalSeconds > 60 ||
      SnapshotBars < 20 || SnapshotBars > 1000 ||
      MaxCommandBytes < 256 || MaxCommandBytes > 65536 ||
      MaxCommandTtlSeconds < 1 ||
      MaxCommandTtlSeconds > 120 ||
      MaxHeartbeatTtlSeconds < 1 ||
      MaxHeartbeatTtlSeconds > 60 ||
      MaxClockSkewSeconds < 0 ||
      MaxSpreadPoints <= 0 ||
      MaxSpreadPoints > MAX_SAFE_SPREAD_POINTS ||
      SlippagePoints < 0 ||
      SlippagePoints > MAX_SAFE_SLIPPAGE_POINTS ||
      MagicNumber <= 0 ||
      MaxSnapshotAgeSeconds < 5 ||
      MaxSnapshotAgeSeconds > 900 ||
      MaxSignalDriftPoints <= 0 ||
      MaxSignalDriftPoints > MAX_SAFE_SIGNAL_DRIFT_POINTS ||
      MaxQuoteAgeSeconds < 1 ||
      MaxQuoteAgeSeconds > 120 ||
      MaxManagedOpenPositions < 1 ||
      !MathIsValidNumber(MaxManagedTotalLots) ||
      MaxManagedTotalLots <= 0.0 ||
       (MoneyManagementMode == MONEY_MANAGEMENT_FIXED_LOT &&
        FixedLot > MaxManagedTotalLots) ||
      MaxTradesPerBrokerDay < 1 ||
      !MathIsValidNumber(MaxLossPerTradePercent) ||
      MaxLossPerTradePercent <= 0.0 ||
      MaxLossPerTradePercent > 100.0 ||
      !MathIsValidNumber(MaxDailyLossPercent) ||
      MaxDailyLossPercent <= 0.0 ||
      MaxDailyLossPercent > 100.0 ||
      !MathIsValidNumber(MaxManagedWeeklyLossPercent) ||
      MaxManagedWeeklyLossPercent <= 0.0 ||
      MaxManagedWeeklyLossPercent > 100.0 ||
      MaxConsecutiveManagedLosses < 1 ||
      MaxConsecutiveManagedLosses > 100 ||
      ConsecutiveLossCooldownMinutes < 1 ||
      ConsecutiveLossCooldownMinutes > 10080 ||
      !MathIsValidNumber(MaxAccountEquityDrawdownPercent) ||
      MaxAccountEquityDrawdownPercent <= 0.0 ||
      MaxAccountEquityDrawdownPercent > 100.0 ||
      !MathIsValidNumber(MinRewardRiskRatio) ||
      MinRewardRiskRatio <= 0.0 ||
      !MathIsValidNumber(MinProjectedMarginLevelPercent) ||
      MinProjectedMarginLevelPercent < 100.0 ||
      (GatewayMode != GATEWAY_SHADOW && !RequireHeartbeat))
   {
      return InitFailure(
         INIT_PARAMETERS_INCORRECT,
         "inputs",
         "GATEWAY_INPUT_CONFIGURATION_INVALID",
         "MetafxHQ MT5: GATEWAY_INPUT_CONFIGURATION_INVALID"
      );
   }

   string normalized_symbols = "";
   string normalized_timeframes = "";
   if(!NormalizeAllowedSymbolsCsv(
         AllowedSymbols,
         normalized_symbols
      ) ||
      !NormalizeAllowedTimeframesCsv(
         AllowedTimeframes,
         normalized_timeframes
       ))
   {
      return InitFailure(
         INIT_PARAMETERS_INCORRECT,
         "inputs",
         "ALLOWED_CHART_LIST_INVALID",
         "MetafxHQ MT5: AllowedSymbols or AllowedTimeframes is invalid."
      );
   }

   if(GatewayMode == GATEWAY_LIVE &&
      !LiveSymbolExactAllowlistConfirmed())
   {
      return InitFailure(
         INIT_PARAMETERS_INCORRECT,
         "chart",
         "LIVE_SYMBOL_REQUIRES_EXACT_ALLOWLIST",
         "MetafxHQ MT5: Live AllowedSymbols must include the exact attached broker _Symbol token."
      );
   }

   if(CurrentTimeframeName() == "UNSUPPORTED" ||
      !IsAllowedBrokerSymbol(AllowedSymbols, _Symbol) ||
      !CsvContains(
         AllowedTimeframes,
         CurrentTimeframeName()
      ))
   {
      return InitFailure(
         INIT_PARAMETERS_INCORRECT,
         "chart",
         "SYMBOL_OR_TIMEFRAME_NOT_ALLOWED",
         "MetafxHQ MT5: SYMBOL_OR_TIMEFRAME_NOT_ALLOWED"
      );
   }

   string reason = "";
   if(!ValidateMoneyManagementConfiguration(reason))
   {
      return InitFailure(
         INIT_PARAMETERS_INCORRECT,
         "money_management",
         reason,
         "MetafxHQ MT5: " + reason
      );
   }
   if(!ValidateManagedMagicConfiguration(reason))
   {
      return InitFailure(
         INIT_PARAMETERS_INCORRECT,
         "managed_magic_numbers",
         reason,
         "MetafxHQ MT5: " + reason
      );
   }

   EnsureFolders();
   string signing_reason = "";
   bool signing_ready =
      RefreshSigningReadiness(signing_reason);
   if(GatewayMode == GATEWAY_LIVE && LiveArmed &&
      SingleHostLiveAcknowledged && !signing_ready)
   {
      return InitFailure(
         INIT_PARAMETERS_INCORRECT,
         "signing",
         signing_reason,
         "MetafxHQ MT5: LIVE_SIGNING_CONFIGURATION_INVALID " + signing_reason
      );
   }

   if(!AcquireChannelLock())
   {
      Print("MetafxHQ MT5: SNAPSHOT_CHANNEL_ALREADY_OWNED");
      return INIT_FAILED;
   }
   string live_owner_reason = "";
   if(!AcquireLiveAccountOwnerLock(live_owner_reason))
   {
      int init_result = InitFailure(
         INIT_FAILED,
         "live_account_owner_lock",
         live_owner_reason,
         "MetafxHQ MT5: LIVE account owner lock unavailable. Another compatible LIVE gateway may already own this account on this Windows host."
      );
      ReleaseChannelLock();
      return init_result;
   }
   InvalidatePublishedRuntimeState();

   string account_lock_path = "";
   if(!AccountExecutionLockPath(account_lock_path) ||
      !AcquireAccountExecutionLock())
   {
      int init_result = InitFailure(
         INIT_FAILED,
         "account_execution_lock",
         "ACCOUNT_EXECUTION_LOCK_UNAVAILABLE",
         "MetafxHQ MT5: ACCOUNT_EXECUTION_LOCK_UNAVAILABLE"
      );
      ReleaseLiveAccountOwnerLock();
      ReleaseChannelLock();
      return init_result;
   }
   string portfolio_reason = "";
   bool portfolio_ready =
      AcquirePortfolioPolicyLease(portfolio_reason);
   ReleaseAccountExecutionLock();
   if(!portfolio_ready)
   {
      int init_result = InitFailure(
         INIT_FAILED,
         "portfolio_policy",
         portfolio_reason,
         "MetafxHQ MT5: " + portfolio_reason
      );
      ReleasePortfolioPolicyLease();
      ReleaseLiveAccountOwnerLock();
      ReleaseChannelLock();
      return init_result;
   }

   if(!EventSetTimer(1))
   {
      int init_result = InitFailure(
         INIT_FAILED,
         "timer",
         "GATEWAY_TIMER_START_FAILED",
         "MetafxHQ MT5: GATEWAY_TIMER_START_FAILED"
      );
      ReleasePortfolioPolicyLease();
      ReleaseLiveAccountOwnerLock();
      ReleaseChannelLock();
      return init_result;
   }

   PublishSnapshotIfDue(true);
   if(!g_last_snapshot_write_ok)
   {
      int init_result = InitFailure(
         INIT_FAILED,
         "snapshot",
         "INITIAL_SNAPSHOT_WRITE_FAILED",
         "MetafxHQ MT5: INITIAL_SNAPSHOT_WRITE_FAILED"
      );
      EventKillTimer();
      InvalidatePublishedRuntimeState();
      ReleasePortfolioPolicyLease();
      ReleaseLiveAccountOwnerLock();
      ReleaseChannelLock();
      return init_result;
   }
   if(!WriteCapabilitiesSnapshot())
   {
      int init_result = InitFailure(
         INIT_FAILED,
         "capabilities",
         "INITIAL_CAPABILITIES_WRITE_FAILED",
         "MetafxHQ MT5: INITIAL_CAPABILITIES_WRITE_FAILED"
      );
      EventKillTimer();
      InvalidatePublishedRuntimeState();
      ReleasePortfolioPolicyLease();
      ReleaseLiveAccountOwnerLock();
      ReleaseChannelLock();
      return init_result;
   }

   UpdateRiskTelemetry(true);
   if(!WriteStatusSnapshot())
   {
      int init_result = InitFailure(
         INIT_FAILED,
         "status",
         "INITIAL_STATUS_WRITE_FAILED",
         "MetafxHQ MT5: INITIAL_STATUS_WRITE_FAILED"
      );
      EventKillTimer();
      InvalidatePublishedRuntimeState();
      ReleasePortfolioPolicyLease();
      ReleaseLiveAccountOwnerLock();
      ReleaseChannelLock();
      return init_result;
   }
   AppendAudit(
      BuildSystemAckJson(
         "INIT_CONFIG",
         "UNIFIED_MT5_GATEWAY_STARTED"
      )
   );
   RecordInitDiagnostic("info", "ready", "INIT_SUCCEEDED", INIT_SUCCEEDED);
   UpdateChartStatus();
   return INIT_SUCCEEDED;
}


void OnDeinit(const int reason)
{
   EventKillTimer();
   AppendAudit(
      BuildSystemAckJson(
         "FAIL_SAFE",
         "GATEWAY_STOPPED_" + IntegerToString(reason)
      )
   );
   InvalidatePublishedRuntimeState();
   ReleaseAccountExecutionLock();
   ReleasePortfolioPolicyLease();
   ReleaseLiveAccountOwnerLock();
   ReleaseChannelLock();
   Comment("");
}


void OnTick()
{
   g_last_tick_millis = GetTickCount();
}


void OnTimer()
{
   PublishSnapshotIfDue(false);
   ProcessCommandFile();
   UpdateRiskTelemetry(false);
   WriteCapabilitiesSnapshot();
   WriteStatusSnapshot();
   UpdateChartStatus();
}
