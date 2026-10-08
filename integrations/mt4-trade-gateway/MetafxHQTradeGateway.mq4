#property strict
#property version   "2.19"
#property description "Metafxclub AI Agent HQ Unified MT4 Gateway"
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
input string TrustedSigningKeyId = "";
input ENUM_MONEY_MANAGEMENT_MODE MoneyManagementMode = MONEY_MANAGEMENT_FIXED_LOT;
input double FixedLot = 0.01;
input double RiskPercent = 1.0;
input ENUM_RISK_CAPITAL_BASE RiskCapitalBase = RISK_CAPITAL_EQUITY;
// Conservative round-trip commission for 1.0 lot in native account currency.
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
string EA_PROFILE = "special";
string EA_VERSION = "2.19";
const int ATOMIC_WRITE_MAX_ATTEMPTS = 3;
const int ATOMIC_WRITE_BACKOFF_MILLIS = 25;
const int LEGACY_BACKFILL_MAX_ACKS = 256;
const int LEGACY_LOSS_LATCH_SCAN_MAX_ENTRIES = 256;
const int FILE_ERROR_IS_DIRECTORY = 5019;
const int FILE_ERROR_NOT_EXIST = 5020;
const int FILE_ERROR_DIRECTORY_NOT_EXIST = 5023;
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
int g_portfolio_policy_lease_handle = INVALID_HANDLE;
string g_portfolio_policy_lease_path = "";
string g_portfolio_policy_digest = "";
int g_portfolio_policy_lease_open_error = 0;
int g_portfolio_policy_lease_scan_error = 0;
int g_portfolio_policy_lease_expanded_path_length = 0;
bool g_legacy_loss_latch_migration_ready = false;
int g_legacy_loss_latch_scan_error = 0;
int g_legacy_loss_latch_scan_entries = 0;
int g_legacy_loss_latch_scan_channels = 0;
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
bool g_daily_loss_latched_in_memory = false;
bool g_weekly_loss_latched_in_memory = false;
int g_daily_loss_latch_period = 0;
int g_weekly_loss_latch_period = 0;
int g_last_outcome_refresh_at = 0;
bool g_ack_has_execution_evidence = false;
bool g_ack_has_sizing_evidence = false;
double g_ack_requested_lots = 0.0;
string g_ack_position_sizing_mode = "";
double g_ack_risk_percent = 0.0;
string g_ack_risk_capital_base = "";
double g_ack_estimated_commission_per_lot = 0.0;
double g_ack_risk_capital_amount = 0.0;
double g_ack_estimated_risk_money = 0.0;
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
   int ticket;
   int magic_number;
   int observed_at;
   double fixed_lot;
   double filled_price;
   double filled_slippage_points;
   double stop_loss;
   double take_profit;
};


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
          normalized == "RISK_PERCENT";
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
   string server = Uppercase(Trimmed(AccountServer()));
   if(AccountNumber() <= 0 || StringLen(server) < 1)
      return false;
   string identity = "MT4|" + IntegerToString(AccountNumber()) + "|" + server;
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


bool AccountExecutionLockPath(string &path)
{
   path = "";
   string account_digest = "";
   if(!AccountIdentityDigest(account_digest))
      return false;
   path = "MetafxHQ\\locks\\account-execution-" + account_digest + ".lock";
   return true;
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


bool AccountLossLatchDirectoryPath(string &path)
{
   path = "";
   string policy_directory = "";
   if(!AccountPortfolioPolicyDirectoryPath(policy_directory))
      return false;
   path = policy_directory + "\\risk-latches";
   return true;
}


string LegacyDailyLossLockFileNameForPeriod(const datetime period_start)
{
   return "daily-loss-" + TimeToString(period_start, TIME_DATE) +
      ".lock";
}


string LegacyDailyLossLockFileName()
{
   return LegacyDailyLossLockFileNameForPeriod(BrokerDayStart());
}


string LegacyDailyLossLockPath()
{
   return BasePath() + "\\state\\" + LegacyDailyLossLockFileName();
}


bool DailyLossLockPath(string &path)
{
   path = "";
   datetime day_start = BrokerDayStart();
   string directory = "";
   if(day_start <= 0 || !AccountLossLatchDirectoryPath(directory))
      return false;
   path = directory + "\\daily-loss-" +
      IntegerToString((int)day_start) + ".lock";
   return true;
}


datetime BrokerWeekStartForDay(const datetime day_start)
{
   if(day_start <= 0)
      return 0;
   int day_of_week = TimeDayOfWeek(day_start);
   int days_since_monday = (day_of_week + 6) % 7;
   return day_start - days_since_monday * 86400;
}


datetime BrokerWeekStart()
{
   return BrokerWeekStartForDay(BrokerDayStart());
}


string LegacyWeeklyLossLockFileNameForPeriod(const datetime period_start)
{
   return "weekly-loss-" + IntegerToString((int)period_start) +
      ".lock";
}


string LegacyWeeklyLossLockFileName()
{
   return LegacyWeeklyLossLockFileNameForPeriod(BrokerWeekStart());
}


string LegacyWeeklyLossLockPath()
{
   return BasePath() + "\\state\\" + LegacyWeeklyLossLockFileName();
}


bool WeeklyLossLockPath(string &path)
{
   path = "";
   datetime week_start = BrokerWeekStart();
   string directory = "";
   if(week_start <= 0 || !AccountLossLatchDirectoryPath(directory))
      return false;
   path = directory + "\\weekly-loss-" +
      IntegerToString((int)week_start) + ".lock";
   return true;
}


string OutcomePath(const string command_id)
{
   return BasePath() + "\\outcomes\\" + command_id + ".json";
}


string TicketMapPath(const int ticket)
{
   return BasePath() + "\\tickets\\" + IntegerToString(ticket) + ".json";
}


string LifecycleAttemptPath(const int ticket)
{
   return BasePath() + "\\state\\lifecycle-close-" +
      IntegerToString(ticket) + ".lock";
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
   string account_loss_latch_directory = "";
   if(AccountLossLatchDirectoryPath(account_loss_latch_directory))
      EnsureFolder(account_loss_latch_directory);
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
   // signed-envelope preimage used by the HQ local runner.
   uchar secret_key[];
   ArrayResize(secret_key, 32);
   for(int index = 0; index < 32; index++)
      secret_key[index] = (uchar)index;
   string key_id = "hk-630dcd2966c4336691125448bbb25b4ff412a49c732db2c8abc1b8581bd710dd";
   string payload_hex = "7b22736368656d6156657273696f6e223a226d65746166782d68712d6d74342d636f6d6d616e642d7632227d";
   string preimage = "METAFXHQ|MT4|COMMAND|HMAC-SHA256|V1\n" +
      key_id + "\nmtc-demo-01\n" + payload_hex;
   uchar message[];
   uchar digest[];
   bool ok = StringToAsciiBytes(preimage, message) &&
      HmacSha256(secret_key, message, digest) &&
      ConstantTimeHexEquals(
         "cb256044ef860dd92296c6018b97cead345a0df428268da402624bb9e6eeb478",
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

   string preimage = "METAFXHQ|MT4|" + normalized_kind +
      "|HMAC-SHA256|V1\n" + key_id + "\n" +
      SnapshotChannel + "\n" + payload_hex;
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
   // This account-wide policy is shared with the MT5 gateway through
   // FILE_COMMON.  Keep both the fields and their byte order identical to the
   // MT5 canonical payload so equal policies can coexist on the same broker
   // account while any real sizing mismatch still fails closed.
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
   return CsvContains(AllowedSymbols, Symbol());
}


bool PositionLifecycleModeIsValid()
{
   return PositionLifecycleMode == LIFECYCLE_SLTP_ONLY ||
      PositionLifecycleMode == LIFECYCLE_MAX_HOLDING ||
      PositionLifecycleMode == LIFECYCLE_SESSION_CLOSE ||
      PositionLifecycleMode == LIFECYCLE_MAX_HOLDING_AND_SESSION_CLOSE;
}


bool MoneyManagementModeIsValid()
{
   return MoneyManagementMode == MONEY_MANAGEMENT_FIXED_LOT ||
      MoneyManagementMode == MONEY_MANAGEMENT_RISK_PERCENT;
}


bool RiskCapitalBaseIsValid()
{
   return RiskCapitalBase == RISK_CAPITAL_EQUITY ||
      RiskCapitalBase == RISK_CAPITAL_BALANCE;
}


double EffectiveRiskPercent()
{
   // RiskPercent is part of persisted/ACK evidence with eight decimal places.
   // Use that exact normalized value for sizing too, so restart/backend budget
   // reconstruction can never differ from the value that authorized the lot.
   return NormalizeDouble(RiskPercent, 8);
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
   if(!MoneyManagementModeIsValid())
   {
      reason = "MONEY_MANAGEMENT_MODE_INVALID";
      return false;
   }
   if(!RiskCapitalBaseIsValid())
   {
      reason = "RISK_CAPITAL_BASE_INVALID";
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
   if(IsNonRealAccount())
      return "demo";
   return "live";
}


bool IsNonRealAccount()
{
   // IsDemo() does not distinguish every non-real account type consistently
   // across MT4 builds.  Contest and unknown modes must never enter the armed
   // Live path, so only ACCOUNT_TRADE_MODE_REAL is treated as live.
   ENUM_ACCOUNT_TRADE_MODE mode =
      (ENUM_ACCOUNT_TRADE_MODE)AccountInfoInteger(ACCOUNT_TRADE_MODE);
   return mode != ACCOUNT_TRADE_MODE_REAL;
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
   bool demo_account = IsNonRealAccount();
   bool demo_ready = GatewayMode == GATEWAY_DEMO &&
      demo_account && signed_ready;
   bool explicit_live_pin = StringLen(g_trusted_signing_key_id) > 0 &&
      g_trusted_signing_key_id == g_active_signing_key_id;
   bool live_commission_policy_confirmed = LiveCommissionPolicyConfirmed();
   bool live_symbol_exact_allowlist_confirmed =
      LiveSymbolExactAllowlistConfirmed();
   bool live_ready = GatewayMode == GATEWAY_LIVE &&
      !demo_account && signed_ready && explicit_live_pin &&
      live_commission_policy_confirmed &&
      live_symbol_exact_allowlist_confirmed && LiveArmed;
   string live_block_reason = "";
   if(demo_account)
      live_block_reason = "LIVE_MODE_REQUIRES_NON_DEMO_ACCOUNT";
   else if(GatewayMode != GATEWAY_LIVE)
      live_block_reason = "LIVE_MODE_NOT_SELECTED";
   else if(!signed_ready)
      live_block_reason = signing_reason;
   else if(!explicit_live_pin)
      live_block_reason = "LIVE_SIGNING_KEY_NOT_PINNED";
   else if(!live_commission_policy_confirmed)
      live_block_reason = "LIVE_COMMISSION_POLICY_UNCONFIRMED";
   else if(!live_symbol_exact_allowlist_confirmed)
      live_block_reason = "LIVE_SYMBOL_REQUIRES_EXACT_ALLOWLIST";
   else if(!LiveArmed)
      live_block_reason = "LIVE_NOT_ARMED";
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
   payload += "\"liveExecutionAvailable\":" + JsonBoolean(live_ready) + ",";
   payload += "\"liveBlockReason\":" + JsonString(live_block_reason) + ",";
   payload += "\"portfolioGuardScope\":\"MANAGED_MAGIC_NUMBERS_ACCOUNT_WIDE\",";
   payload += "\"historyScope\":\"MT4_LOADED_ACCOUNT_HISTORY\",";
   payload += "\"managedMagicNumbers\":" + JsonString(ManagedMagicNumbers) + ",";
   payload += "\"positionLifecycleMode\":" + JsonString(LifecycleModeName()) + ",";
   payload += "\"outcomeTracking\":true,";
   payload += "\"postOrderVerification\":true,";
   payload += "\"executionUnknownRecovery\":\"EA_RECONCILE_OR_BACKEND_QUARANTINE\"";
   payload += "}";
   return payload;
}


bool WriteCapabilitiesSnapshot()
{
   return WriteCommonTextAtomic(CapabilitiesPath(), BuildCapabilitiesJson());
}


void ResetAckSizingEvidence()
{
   g_ack_has_sizing_evidence = false;
   g_ack_requested_lots = 0.0;
   g_ack_position_sizing_mode = "";
   g_ack_risk_percent = 0.0;
   g_ack_risk_capital_base = "";
   g_ack_estimated_commission_per_lot = 0.0;
   g_ack_risk_capital_amount = 0.0;
   g_ack_estimated_risk_money = 0.0;
}


void SetAckSizingEvidence(
   const double requested_lots,
   const string sizing_mode,
   const double risk_percent,
   const string capital_base,
   const double estimated_commission_per_lot,
   const double capital_amount,
   const double estimated_risk_money
)
{
   g_ack_has_sizing_evidence = true;
   g_ack_requested_lots = requested_lots;
   g_ack_position_sizing_mode = sizing_mode;
   g_ack_risk_percent = risk_percent;
   g_ack_risk_capital_base = capital_base;
   g_ack_estimated_commission_per_lot = estimated_commission_per_lot;
   g_ack_risk_capital_amount = capital_amount;
   g_ack_estimated_risk_money = estimated_risk_money;
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
}


string BuildStatusJson()
{
   UpdateRiskTelemetry(false);
   bool signed_ready = SignedCommandVerificationAvailable();
   bool demo_account = IsNonRealAccount();
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
   double broker_volume_minimum = MarketInfo(Symbol(), MODE_MINLOT);
   double broker_volume_maximum = MarketInfo(Symbol(), MODE_MAXLOT);
   double broker_volume_step = MarketInfo(Symbol(), MODE_LOTSTEP);
   string payload = "{";
   payload += "\"schemaVersion\":" + JsonString(STATUS_SCHEMA) + ",";
   payload += "\"eaVersion\":" + JsonString(EA_VERSION) + ",";
   payload += "\"channelId\":" + JsonString(SnapshotChannel) + ",";
   payload += "\"profile\":" + JsonString(EA_PROFILE) + ",";
   payload += "\"mode\":" + JsonString(ModeName()) + ",";
   payload += "\"demoAccount\":" + JsonBoolean(demo_account) + ",";
   payload += "\"accountMode\":" + JsonString(AccountModeName()) + ",";
   payload += "\"liveArmed\":" + JsonBoolean(LiveArmed) + ",";
   payload += "\"fixedLot\":" + DoubleToString(FixedLot, LotDigits()) + ",";
   payload += "\"positionSizingMode\":" + JsonString(PositionSizingModeName()) + ",";
   payload += "\"riskPercent\":" + JsonNumber(EffectiveRiskPercent(), 8) + ",";
   payload += "\"riskCapitalBase\":" + JsonString(RiskCapitalBaseName()) + ",";
   payload += "\"estimatedCommissionPerLot\":" +
      JsonNumber(EffectiveEstimatedCommissionPerLot(), 8) + ",";
   payload += "\"commissionFreeAccountConfirmed\":" +
      JsonBoolean(CommissionFreeAccountConfirmed) + ",";
   payload += "\"brokerVolumeMin\":" +
      JsonNumber(broker_volume_minimum, LotDigits()) + ",";
   payload += "\"brokerVolumeMax\":" +
      JsonNumber(broker_volume_maximum, LotDigits()) + ",";
   payload += "\"brokerVolumeStep\":" +
      JsonNumber(broker_volume_step, LotDigits()) + ",";
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
   if(RiskCapitalBase == RISK_CAPITAL_EQUITY)
      return "EQUITY";
   if(RiskCapitalBase == RISK_CAPITAL_BALANCE)
      return "BALANCE";
   return "INVALID";
}


double RiskCapitalAmount()
{
   if(RiskCapitalBase == RISK_CAPITAL_EQUITY)
      return AccountEquity();
   if(RiskCapitalBase == RISK_CAPITAL_BALANCE)
      return AccountBalance();
   return 0.0;
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


int DecimalDigitsForValue(const double value)
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
   double step = MarketInfo(Symbol(), MODE_LOTSTEP);
   if(!MathIsValidNumber(step) || step <= 0.0)
      return 2;
   double minimum = MarketInfo(Symbol(), MODE_MINLOT);
   return (int)MathMax(
      DecimalDigitsForValue(step),
      DecimalDigitsForValue(minimum)
   );
}


int SymbolPriceDigits()
{
   int digits = (int)MarketInfo(Symbol(), MODE_DIGITS);
   if(digits < 0 || digits > 8)
      return Digits;
   return digits;
}


double NormalizeSymbolPrice(const double value)
{
   return NormalizeDouble(value, SymbolPriceDigits());
}


string BuildAckJson(
   const CommandPayload &command,
   const string status,
   const string reason_code,
   const int ticket,
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
   // bid/ask midpoint with one more decimal than the broker display Digits.
   payload += "\"referencePrice\":" + JsonNumber(command.reference_price, 8) + ",";
   payload += "\"eaClosedBarTime\":" + IntegerToString((int)iTime(Symbol(), Period(), 1)) + ",";
   payload += "\"status\":" + JsonString(status) + ",";
   payload += "\"reasonCode\":" + JsonString(reason_code) + ",";
   payload += "\"mode\":" + JsonString(ModeName()) + ",";
   payload += "\"action\":" + JsonString(command.action) + ",";
   payload += "\"symbol\":" + JsonString(command.symbol) + ",";
   payload += "\"timeframe\":" + JsonString(command.timeframe) + ",";
   payload += "\"fixedLot\":" + JsonNumber(
      g_ack_has_sizing_evidence ? g_ack_requested_lots : 0.0,
      LotDigits()
   ) + ",";
   payload += "\"positionSizingMode\":" + JsonString(
      g_ack_has_sizing_evidence
         ? g_ack_position_sizing_mode
         : PositionSizingModeName()
   ) + ",";
   payload += "\"riskPercent\":" + JsonNumber(
      g_ack_has_sizing_evidence ? g_ack_risk_percent : EffectiveRiskPercent(),
       8
   ) + ",";
   payload += "\"riskCapitalBase\":" + JsonString(
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
   if(ticket >= 0)
      payload += "\"ticket\":" + IntegerToString(ticket) + ",";
   else
      payload += "\"ticket\":null,";
   if(g_ack_has_execution_evidence)
   {
      payload += "\"filledPrice\":" + JsonNumber(g_ack_filled_price, Digits) + ",";
      payload += "\"filledSlippagePoints\":" + JsonNumber(g_ack_filled_slippage_points, 2) + ",";
      payload += "\"actualStopLoss\":" + JsonNumber(g_ack_actual_stop_loss, Digits) + ",";
      payload += "\"actualTakeProfit\":" + JsonNumber(g_ack_actual_take_profit, Digits) + ",";
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


void FinalizeCommand(
   const CommandPayload &command,
   const string status,
   const string reason_code,
   const int ticket,
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


bool IsManagedMarketOrderSelected()
{
   int order_type = OrderType();
   return (order_type == OP_BUY || order_type == OP_SELL) &&
      IsManagedMagic(OrderMagicNumber());
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
   if(Period() == PERIOD_M5)
      return "M5";
   if(Period() == PERIOD_M15)
      return "M15";
   if(Period() == PERIOD_M30)
      return "M30";
   if(Period() == PERIOD_H1)
      return "H1";
   if(Period() == PERIOD_H4)
      return "H4";
   if(Period() == PERIOD_D1)
      return "D1";
   if(Period() == PERIOD_W1)
      return "W1";
   if(Period() == PERIOD_MN1)
      return "MN1";
   return "UNSUPPORTED";
}


datetime BrokerDayStart()
{
   return StrToTime(TimeToString(TimeCurrent(), TIME_DATE));
}


string BuildSnapshotBarsJson()
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


void ReadSnapshotDailySummary(
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


void ReadSnapshotPositionSummary(
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


bool SnapshotMarketOpen()
{
   if(!IsConnected() || MarketInfo(Symbol(), MODE_TRADEALLOWED) <= 0.0 ||
      Bid <= 0.0 || Ask <= 0.0 || Ask < Bid || g_last_tick_millis == 0)
      return false;
   uint elapsed = GetTickCount() - g_last_tick_millis;
   return elapsed <= (uint)MaxQuoteAgeSeconds * 1000;
}


string BuildSnapshotJson()
{
   UpdateRiskTelemetry(false);
   RefreshRates();
   double realized_profit;
   int trades_closed;
   int wins;
   int losses;
   ReadSnapshotDailySummary(realized_profit, trades_closed, wins, losses);

   int position_count;
   int buy_count;
   int sell_count;
   double total_lots;
   double floating_profit;
   ReadSnapshotPositionSummary(
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
   // The snapshot contract remains read-only even when the separate gateway
   // command path is operating in Demo or Live mode.
   payload += "\"mode\":\"read_only\",";
   payload += "\"chart\":{";
   payload += "\"symbol\":" + JsonString(Symbol()) + ",";
   payload += "\"timeframe\":" + JsonString(CurrentTimeframeName()) + ",";
   payload += "\"bid\":" + JsonNumber(Bid, Digits) + ",";
   payload += "\"ask\":" + JsonNumber(Ask, Digits) + ",";
   payload += "\"spreadPoints\":" + JsonNumber(spread_points, 2) + ",";
   bool market_open = SnapshotMarketOpen();
   payload += "\"marketOpen\":" + JsonBoolean(market_open) + ",";
   payload += "\"marketSession\":" +
      JsonString(market_open ? "BROKER_FEED_ACTIVE" : "BROKER_FEED_INACTIVE") + ",";
   payload += "\"bars\":" + BuildSnapshotBarsJson();
   payload += "},";
   payload += "\"daily\":{";
   payload += "\"scope\":\"ACCOUNT_WIDE\",";
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
   payload += "\"scope\":\"ACCOUNT_WIDE\",";
   payload += "\"count\":" + IntegerToString(position_count) + ",";
   payload += "\"buyCount\":" + IntegerToString(buy_count) + ",";
   payload += "\"sellCount\":" + IntegerToString(sell_count) + ",";
   payload += "\"totalLots\":" + JsonNumber(total_lots, 2) + ",";
   payload += "\"floatingProfit\":" + JsonNumber(floating_profit, 2);
   payload += "},";
   payload += "\"managedSummary\":{";
   payload += "\"scope\":\"MANAGED_MAGIC_NUMBERS_ACCOUNT_WIDE\",";
   payload += "\"managedMagicNumbers\":" + JsonString(ManagedMagicNumbers) + ",";
   payload += "\"positionCount\":" + IntegerToString(g_cached_managed_positions) + ",";
   payload += "\"totalLots\":" + JsonNumber(g_cached_managed_lots, LotDigits()) + ",";
   payload += "\"dailyPnl\":" + JsonNumber(g_cached_managed_daily_pnl, 2) + ",";
   payload += "\"weeklyPnl\":" + JsonNumber(g_cached_managed_weekly_pnl, 2) + ",";
   payload += "\"consecutiveLosses\":" + IntegerToString(g_cached_consecutive_losses) + ",";
   payload += "\"cooldownUntil\":" + IntegerToString(g_cached_cooldown_until) + ",";
   payload += "\"lifecycleMode\":" + JsonString(LifecycleModeName());
   payload += "}";
   payload += "}";
   return payload;
}


bool WriteSnapshot()
{
   string temporary_path = "MetafxHQ\\" + SnapshotChannel + "\\snapshot.tmp";
   string final_path = SnapshotPath();
   return WriteCommonTextAtomicWithTemporary(
      final_path,
      temporary_path,
      BuildSnapshotJson()
   );
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
   string values[];
   ArrayResize(values, count);
   for(int index = 0; index < count; index++)
   {
      string token = Uppercase(Trimmed(parts[index]));
      int length = StringLen(token);
      if(length < 2 || length > 24)
         return false;
      for(int character_index = 0;
          character_index < length;
          character_index++)
      {
         if(!IsBrokerSuffixCharacter(
            StringGetCharacter(token, character_index)
         ))
            return false;
      }
      for(int prior = 0; prior < index; prior++)
      {
         if(values[prior] == token)
            return false;
      }
      values[index] = token;
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
   string values[];
   ArrayResize(values, count);
   for(int index = 0; index < count; index++)
   {
      string token = Uppercase(Trimmed(parts[index]));
      if(TimeframeToPeriod(token) <= 0)
         return false;
      for(int prior = 0; prior < index; prior++)
      {
         if(values[prior] == token)
            return false;
      }
      values[index] = token;
      if(index > 0)
         normalized += ",";
      normalized += token;
   }
   return StringLen(normalized) > 0;
}


bool IsSnapshotDue(const int now_utc)
{
   if(g_last_snapshot_attempt_at <= 0 || now_utc < g_last_snapshot_attempt_at)
      return true;
   return now_utc - g_last_snapshot_attempt_at >= SnapshotIntervalSeconds;
}


void PublishSnapshotIfDue(const bool force)
{
   int now_utc = NowUtc();
   if(!force && !IsSnapshotDue(now_utc))
      return;
   g_last_snapshot_attempt_at = now_utc;
   g_last_snapshot_write_ok = WriteSnapshot();
   if(g_last_snapshot_write_ok)
      g_last_snapshot_success_at = now_utc;
   else
      Print(
         "MetafxHQ: Unable to write snapshot.json; GetLastError=",
         IntegerToString(g_last_atomic_write_error),
         " consecutiveFailures=",
         IntegerToString(g_consecutive_atomic_write_failures)
      );
}


bool ReadBrokerVolumeMetadata(
   double &minimum,
   double &maximum,
   double &step,
   string &reason
)
{
   minimum = MarketInfo(Symbol(), MODE_MINLOT);
   maximum = MarketInfo(Symbol(), MODE_MAXLOT);
   step = MarketInfo(Symbol(), MODE_LOTSTEP);
   if(!MathIsValidNumber(minimum) ||
      !MathIsValidNumber(maximum) ||
      !MathIsValidNumber(step) ||
      minimum <= 0.0 || maximum < minimum || step <= 0.0 || step > maximum)
   {
      reason = "BROKER_VOLUME_LIMITS_UNAVAILABLE";
      return false;
   }
   return true;
}


bool VolumeIsOnBrokerStep(
   const double lots,
   const double minimum,
   const double step
)
{
   if(!MathIsValidNumber(lots) || !MathIsValidNumber(minimum) ||
      lots <= 0.0 || minimum <= 0.0 || step <= 0.0)
      return false;
   double step_count = MathRound((lots - minimum) / step);
   double normalized = NormalizeDouble(
      minimum + step_count * step,
      LotDigits()
   );
   return MathAbs(normalized - lots) <= 0.00000001;
}


bool ValidateResolvedVolume(const double lots, string &reason)
{
   double minimum = 0.0;
   double maximum = 0.0;
   double step = 0.0;
   if(!ReadBrokerVolumeMetadata(minimum, maximum, step, reason))
      return false;
   if(!MathIsValidNumber(lots) || lots <= 0.0 ||
      lots < minimum - 0.00000001 || lots > maximum + 0.00000001)
   {
      reason = "ORDER_VOLUME_OUTSIDE_BROKER_LIMITS";
      return false;
   }
   if(!VolumeIsOnBrokerStep(lots, minimum, step))
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
   if(!ReadBrokerVolumeMetadata(minimum, maximum, step, reason))
      return false;
   if(!MathIsValidNumber(FixedLot) || FixedLot <= 0.0)
   {
      reason = "FIXED_LOT_CONFIGURATION_INVALID";
      return false;
   }
   if(FixedLot < minimum - 0.00000001 || FixedLot > maximum + 0.00000001)
   {
      reason = "FIXED_LOT_OUTSIDE_BROKER_LIMITS";
      return false;
   }
   if(!VolumeIsOnBrokerStep(FixedLot, minimum, step))
   {
      reason = "FIXED_LOT_NOT_ON_BROKER_STEP";
      return false;
   }
   return true;
}


bool NormalizeRiskVolumeDown(
   const double raw_lots,
   const double portfolio_ceiling,
   double &normalized_lots,
   string &reason
)
{
   normalized_lots = 0.0;
   double minimum = 0.0;
   double maximum = 0.0;
   double step = 0.0;
   if(!ReadBrokerVolumeMetadata(minimum, maximum, step, reason))
      return false;
   if(!MathIsValidNumber(raw_lots) || !MathIsValidNumber(portfolio_ceiling) ||
      raw_lots <= 0.0 || portfolio_ceiling <= 0.0)
   {
      reason = "RISK_LOT_CALCULATION_INVALID";
      return false;
   }
   double capped_lots = MathMin(raw_lots, MathMin(maximum, portfolio_ceiling));
   if(capped_lots < minimum)
   {
      reason = "RISK_VOLUME_BELOW_BROKER_MINIMUM";
      return false;
   }
   double step_count = MathFloor(
      (capped_lots - minimum) / step + 0.0000000001
   );
   normalized_lots = NormalizeDouble(
      minimum + MathMax(0.0, step_count) * step,
      LotDigits()
   );
   while(normalized_lots > capped_lots + 0.00000001 &&
      normalized_lots - step >= minimum - 0.00000001)
      normalized_lots = NormalizeDouble(normalized_lots - step, LotDigits());
   if(normalized_lots < minimum ||
      normalized_lots > maximum ||
      normalized_lots > portfolio_ceiling ||
      !VolumeIsOnBrokerStep(normalized_lots, minimum, step))
   {
      normalized_lots = 0.0;
      reason = "RISK_VOLUME_BELOW_BROKER_MINIMUM";
      return false;
   }
   return true;
}


bool ValidateMoneyManagementConfiguration(string &reason)
{
   if(!MoneyManagementModeIsValid())
   {
      reason = "MONEY_MANAGEMENT_MODE_INVALID";
      return false;
   }
   if(!RiskCapitalBaseIsValid())
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
   double effective_risk_percent = EffectiveRiskPercent();
   if(MoneyManagementMode == MONEY_MANAGEMENT_RISK_PERCENT &&
      (effective_risk_percent < 0.00000001 ||
       effective_risk_percent > MaxLossPerTradePercent))
   {
      reason = "RISK_PERCENT_INVALID_OR_ABOVE_HARD_CAP";
      return false;
   }
   if(MoneyManagementMode == MONEY_MANAGEMENT_FIXED_LOT)
      return ValidateFixedLot(reason);
   double minimum = 0.0;
   double maximum = 0.0;
   double step = 0.0;
   if(!ReadBrokerVolumeMetadata(minimum, maximum, step, reason))
      return false;
   double tick_value = 0.0;
   double tick_size_price = 0.0;
   return ReadBrokerRiskMetadata(tick_value, tick_size_price, reason);
}


bool ValidateStops(
   const CommandPayload &command,
   string &reason
)
{
   if(!MathIsValidNumber(command.stop_loss) ||
      !MathIsValidNumber(command.take_profit) ||
      command.stop_loss <= 0.0 || command.take_profit <= 0.0)
   {
      reason = "SL_TP_REQUIRED";
      return false;
   }
   RefreshRates();
   double point = MarketInfo(Symbol(), MODE_POINT);
   double stop_level_points = MarketInfo(Symbol(), MODE_STOPLEVEL);
   if(point <= 0.0 || stop_level_points < 0.0)
   {
      reason = "BROKER_STOP_METADATA_INVALID";
      return false;
   }
   double stop_loss = NormalizeSymbolPrice(command.stop_loss);
   double take_profit = NormalizeSymbolPrice(command.take_profit);
   double minimum_distance = stop_level_points * point;
   if(command.action == "BUY")
   {
      // A BUY closes on Bid.  Keep SL below Bid and TP above the entry Ask;
      // broker stop-distance checks are measured from the executable Bid.
      if(stop_loss >= Bid || take_profit <= Ask)
      {
         reason = "BUY_SL_TP_DIRECTION_INVALID";
         return false;
      }
      if((Bid - stop_loss) + point * 0.1 < minimum_distance ||
         (take_profit - Bid) + point * 0.1 < minimum_distance)
      {
         reason = "BUY_SL_TP_TOO_CLOSE";
         return false;
      }
   }
   else if(command.action == "SELL")
   {
      // A SELL closes on Ask.  Keep SL above Ask and TP below the entry Bid;
      // broker stop-distance checks are measured from the executable Ask.
      if(stop_loss <= Ask || take_profit >= Bid)
      {
         reason = "SELL_SL_TP_DIRECTION_INVALID";
         return false;
      }
      if((stop_loss - Ask) + point * 0.1 < minimum_distance ||
         (Ask - take_profit) + point * 0.1 < minimum_distance)
      {
         reason = "SELL_SL_TP_TOO_CLOSE";
         return false;
      }
   }
   return true;
}


bool ValidateQuoteFreshness(string &reason)
{
   if(g_last_tick_millis == 0)
   {
      reason = "QUOTE_NOT_OBSERVED";
      return false;
   }
   uint elapsed = GetTickCount() - g_last_tick_millis;
   if(elapsed > (uint)MaxQuoteAgeSeconds * 1000)
   {
      reason = "QUOTE_STALE";
      return false;
   }
   RefreshRates();
   if(Bid <= 0.0 || Ask <= 0.0 || Ask < Bid)
   {
      reason = "QUOTE_INVALID";
      return false;
   }
   datetime quote_time = (datetime)MarketInfo(Symbol(), MODE_TIME);
   datetime server_time = TimeCurrent();
   if(quote_time <= 0 || server_time <= 0 ||
      (server_time > quote_time &&
       server_time - quote_time > MaxQuoteAgeSeconds))
   {
      reason = "BROKER_QUOTE_TIME_STALE";
      return false;
   }
   return true;
}


bool ReadManagedOpenState(int &positions, double &lots, double &floating_pnl)
{
   positions = 0;
   lots = 0.0;
   floating_pnl = 0.0;
   int total = OrdersTotal();
   if(total < 0)
      return false;
   for(int index = total - 1; index >= 0; index--)
   {
      if(!OrderSelect(index, SELECT_BY_POS, MODE_TRADES))
         return false;
      if(!IsManagedMarketOrderSelected())
         continue;
      double order_lots = OrderLots();
      double order_profit = OrderProfit();
      double order_swap = OrderSwap();
      double order_commission = OrderCommission();
      if(!MathIsValidNumber(order_lots) || order_lots <= 0.0 ||
         !MathIsValidNumber(order_profit) ||
         !MathIsValidNumber(order_swap) ||
         !MathIsValidNumber(order_commission))
         return false;
      positions++;
      lots += order_lots;
      floating_pnl += order_profit + order_swap + order_commission;
      if(!MathIsValidNumber(lots) || !MathIsValidNumber(floating_pnl))
         return false;
   }
   return true;
}


bool CountManagedTradesToday(int &count)
{
   datetime day_start = BrokerDayStart();
   count = 0;
   int history_total = OrdersHistoryTotal();
   int open_total = OrdersTotal();
   if(day_start <= 0 || history_total < 0 || open_total < 0)
      return false;
   for(int index = history_total - 1; index >= 0; index--)
   {
      if(!OrderSelect(index, SELECT_BY_POS, MODE_HISTORY))
         return false;
      if(!IsManagedMarketOrderSelected())
         continue;
      datetime opened_at = OrderOpenTime();
      if(opened_at <= 0)
         return false;
      if(opened_at >= day_start)
         count++;
   }
   for(int open_index = open_total - 1; open_index >= 0; open_index--)
   {
      if(!OrderSelect(open_index, SELECT_BY_POS, MODE_TRADES))
         return false;
      if(!IsManagedMarketOrderSelected())
         continue;
      datetime opened_at = OrderOpenTime();
      if(opened_at <= 0)
         return false;
      if(opened_at >= day_start)
         count++;
   }
   return count >= 0;
}


bool ManagedDailyPnl(double &pnl)
{
   datetime day_start = BrokerDayStart();
   pnl = 0.0;
   int history_total = OrdersHistoryTotal();
   if(day_start <= 0 || history_total < 0)
      return false;
   for(int index = history_total - 1; index >= 0; index--)
   {
      if(!OrderSelect(index, SELECT_BY_POS, MODE_HISTORY))
         return false;
      if(!IsManagedMarketOrderSelected())
         continue;
      datetime closed_at = OrderCloseTime();
      if(closed_at <= 0)
         return false;
      if(closed_at < day_start)
         continue;
      double result = OrderProfit() + OrderSwap() + OrderCommission();
      if(!MathIsValidNumber(result))
         return false;
      pnl += result;
      if(!MathIsValidNumber(pnl))
         return false;
   }
   return true;
}


bool ManagedWeeklyPnl(double &pnl)
{
   datetime week_start = BrokerWeekStart();
   pnl = 0.0;
   int history_total = OrdersHistoryTotal();
   if(week_start <= 0 || history_total < 0)
      return false;
   for(int index = history_total - 1; index >= 0; index--)
   {
      if(!OrderSelect(index, SELECT_BY_POS, MODE_HISTORY))
         return false;
      if(!IsManagedMarketOrderSelected())
         continue;
      datetime closed_at = OrderCloseTime();
      if(closed_at <= 0)
         return false;
      if(closed_at < week_start)
         continue;
      double result = OrderProfit() + OrderSwap() + OrderCommission();
      if(!MathIsValidNumber(result))
         return false;
      pnl += result;
      if(!MathIsValidNumber(pnl))
         return false;
   }
   return true;
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
   // Open managed losses consume daily and weekly loss budgets. Floating
   // profit is not realized and must never relax either fail-closed guard.
   risk_pnl = realized_pnl + MathMin(0.0, floating_pnl);
   return MathIsValidNumber(risk_pnl);
}


bool ReadManagedLossStreak(int &loss_count, int &cooldown_until)
{
   loss_count = 0;
   cooldown_until = 0;
   int history_total = OrdersHistoryTotal();
   if(history_total < 0)
      return false;
   datetime before_time = (datetime)2147483647;
   int before_ticket = 2147483647;
   int maximum_rows = MathMin(history_total, MaxConsecutiveManagedLosses + 1);
   for(int ordered = 0; ordered < maximum_rows; ordered++)
   {
      bool found = false;
      datetime newest_time = 0;
      int newest_ticket = -1;
      double newest_result = 0.0;
      for(int index = 0; index < history_total; index++)
      {
         if(!OrderSelect(index, SELECT_BY_POS, MODE_HISTORY))
            return false;
         if(!IsManagedMarketOrderSelected())
            continue;
         datetime closed_at = OrderCloseTime();
         int ticket = OrderTicket();
         double result = OrderProfit() + OrderSwap() + OrderCommission();
         if(closed_at <= 0 || ticket <= 0 || !MathIsValidNumber(result))
            return false;
         bool before_cursor = closed_at < before_time ||
            (closed_at == before_time && ticket < before_ticket);
         bool newer_than_best = closed_at > newest_time ||
            (closed_at == newest_time && ticket > newest_ticket);
         if(before_cursor && newer_than_best)
         {
            found = true;
            newest_time = closed_at;
            newest_ticket = ticket;
            newest_result = result;
         }
      }
      if(!found || newest_result >= 0.0)
         break;
      loss_count++;
      if(loss_count == 1)
         cooldown_until = (int)newest_time + ConsecutiveLossCooldownMinutes * 60;
      before_time = newest_time;
      before_ticket = newest_ticket;
   }
   return true;
}


double CurrentAccountDrawdownPercent()
{
   double balance = AccountBalance();
   if(balance <= 0.0)
      return 100.0;
   return MathMax(0.0, (balance - AccountEquity()) / balance * 100.0);
}


double CurrentMarginLevelPercent()
{
   double margin = AccountMargin();
   if(margin <= 0.0)
      return 999999.0;
   return MathMax(0.0, AccountEquity() / margin * 100.0);
}


bool LossLatchGlobalName(
   const string period_kind,
   const int period_start,
   string &name
)
{
   name = "";
   string account_digest = "";
   if(period_start <= 0 || !AccountIdentityDigest(account_digest))
      return false;
   // Terminal global variables bridge every chart/channel in this terminal
   // while the FILE_COMMON account marker is being retried.  The full digest
   // remains in the authoritative file path; 128 bits are enough to keep this
   // secondary name below MT4's 63-character global-variable limit.
   name = "MFXHQ_" + period_kind + "_" +
      StringSubstr(account_digest, 0, 32) + "_" +
      IntegerToString(period_start);
   return StringLen(name) <= 63;
}


bool DailyLossLatchContext(
   int &period_start,
   string &shared_path,
   string &global_name
)
{
   period_start = (int)BrokerDayStart();
   shared_path = "";
   global_name = "";
   return period_start > 0 &&
      DailyLossLockPath(shared_path) &&
      LossLatchGlobalName("DL", period_start, global_name);
}


bool WeeklyLossLatchContext(
   int &period_start,
   string &shared_path,
   string &global_name
)
{
   period_start = (int)BrokerWeekStart();
   shared_path = "";
   global_name = "";
   return period_start > 0 &&
      WeeklyLossLockPath(shared_path) &&
      LossLatchGlobalName("WL", period_start, global_name);
}


bool PersistDailyLossLatchContext(
   const int period_start,
   const string shared_path,
   const string global_name,
   string &reason
)
{
   // Set process-local state first: even if every persistence mechanism fails,
   // this EA cannot reopen trading merely because floating P/L later recovers.
   g_daily_loss_latched_in_memory = true;
   if(period_start <= 0 || StringLen(shared_path) < 1 ||
      StringLen(global_name) < 1)
   {
      if(period_start > 0)
         g_daily_loss_latch_period = period_start;
      reason = "DAILY_LOSS_LATCH_PATH_UNAVAILABLE";
      return false;
   }
   g_daily_loss_latch_period = period_start;
   bool terminal_latch_written = GlobalVariableSet(global_name, 1.0) > 0;
   if(terminal_latch_written)
      GlobalVariablesFlush();
   if(FileIsExist(shared_path, FILE_COMMON))
      return true;
   if(WriteCommonTextAtomic(
         shared_path,
         "DAILY_LOSS_LIMIT_LATCHED|" + IntegerToString(NowUtc())
      ))
      return true;
   reason = terminal_latch_written
      ? "DAILY_LOSS_LATCH_ACCOUNT_PERSISTENCE_FAILED"
      : "DAILY_LOSS_LATCH_PERSISTENCE_FAILED";
   return false;
}


bool ActivateDailyLossLatch(string &reason)
{
   int period_start = 0;
   string shared_path = "";
   string global_name = "";
   if(!DailyLossLatchContext(period_start, shared_path, global_name))
   {
      g_daily_loss_latched_in_memory = true;
      if(period_start > 0)
         g_daily_loss_latch_period = period_start;
      reason = "DAILY_LOSS_LATCH_PATH_UNAVAILABLE";
      return false;
   }
   return PersistDailyLossLatchContext(
      period_start,
      shared_path,
      global_name,
      reason
   );
}


bool PersistWeeklyLossLatchContext(
   const int period_start,
   const string shared_path,
   const string global_name,
   string &reason
)
{
   g_weekly_loss_latched_in_memory = true;
   if(period_start <= 0 || StringLen(shared_path) < 1 ||
      StringLen(global_name) < 1)
   {
      if(period_start > 0)
         g_weekly_loss_latch_period = period_start;
      reason = "WEEKLY_LOSS_LATCH_PATH_UNAVAILABLE";
      return false;
   }
   g_weekly_loss_latch_period = period_start;
   bool terminal_latch_written = GlobalVariableSet(global_name, 1.0) > 0;
   if(terminal_latch_written)
      GlobalVariablesFlush();
   if(FileIsExist(shared_path, FILE_COMMON))
      return true;
   if(WriteCommonTextAtomic(
         shared_path,
         "WEEKLY_LOSS_LIMIT_LATCHED|" + IntegerToString(NowUtc())
      ))
      return true;
   reason = terminal_latch_written
      ? "WEEKLY_LOSS_LATCH_ACCOUNT_PERSISTENCE_FAILED"
      : "WEEKLY_LOSS_LATCH_PERSISTENCE_FAILED";
   return false;
}


bool ActivateWeeklyLossLatch(string &reason)
{
   int period_start = 0;
   string shared_path = "";
   string global_name = "";
   if(!WeeklyLossLatchContext(period_start, shared_path, global_name))
   {
      g_weekly_loss_latched_in_memory = true;
      if(period_start > 0)
         g_weekly_loss_latch_period = period_start;
      reason = "WEEKLY_LOSS_LATCH_PATH_UNAVAILABLE";
      return false;
   }
   return PersistWeeklyLossLatchContext(
      period_start,
      shared_path,
      global_name,
      reason
   );
}


bool DailyLossLatchAllowsTrading(string &reason)
{
   int period_start = 0;
   string shared_path = "";
   string global_name = "";
   if(!DailyLossLatchContext(period_start, shared_path, global_name))
   {
      g_daily_loss_latched_in_memory = true;
      if(period_start > 0)
         g_daily_loss_latch_period = period_start;
      reason = "DAILY_LOSS_LATCH_PATH_UNAVAILABLE";
      return false;
   }
   if(g_daily_loss_latch_period != period_start)
   {
      g_daily_loss_latch_period = period_start;
      g_daily_loss_latched_in_memory = false;
   }
   bool shared_latched = FileIsExist(shared_path, FILE_COMMON);
   bool legacy_latched = FileIsExist(
      LegacyDailyLossLockPath(),
      FILE_COMMON
   );
   bool terminal_latched = GlobalVariableCheck(global_name);
   if(!shared_latched && !legacy_latched && !terminal_latched &&
      !g_daily_loss_latched_in_memory)
      return true;
   g_daily_loss_latched_in_memory = true;
   if(!ActivateDailyLossLatch(reason))
   {
      if(legacy_latched)
         reason = "DAILY_LOSS_LATCH_MIGRATION_FAILED";
      return false;
   }
   reason = "DAILY_LOSS_LIMIT_LATCHED";
   return false;
}


bool WeeklyLossLatchAllowsTrading(string &reason)
{
   int period_start = 0;
   string shared_path = "";
   string global_name = "";
   if(!WeeklyLossLatchContext(period_start, shared_path, global_name))
   {
      g_weekly_loss_latched_in_memory = true;
      if(period_start > 0)
         g_weekly_loss_latch_period = period_start;
      reason = "WEEKLY_LOSS_LATCH_PATH_UNAVAILABLE";
      return false;
   }
   if(g_weekly_loss_latch_period != period_start)
   {
      g_weekly_loss_latch_period = period_start;
      g_weekly_loss_latched_in_memory = false;
   }
   bool shared_latched = FileIsExist(shared_path, FILE_COMMON);
   bool legacy_latched = FileIsExist(
      LegacyWeeklyLossLockPath(),
      FILE_COMMON
   );
   bool terminal_latched = GlobalVariableCheck(global_name);
   if(!shared_latched && !legacy_latched && !terminal_latched &&
      !g_weekly_loss_latched_in_memory)
      return true;
   g_weekly_loss_latched_in_memory = true;
   if(!ActivateWeeklyLossLatch(reason))
   {
      if(legacy_latched)
         reason = "WEEKLY_LOSS_LATCH_MIGRATION_FAILED";
      return false;
   }
   reason = "WEEKLY_LOSS_LIMIT_LATCHED";
   return false;
}


bool ProbeLegacyLossLatchMarker(
   const string path,
   bool &exists,
   string &reason
)
{
   exists = false;
   ResetLastError();
   if(FileIsExist(path, FILE_COMMON))
   {
      exists = true;
      return true;
   }
   int probe_error = GetLastError();
   if(probe_error == 0 || probe_error == FILE_ERROR_NOT_EXIST ||
      probe_error == FILE_ERROR_DIRECTORY_NOT_EXIST)
      return true;
   g_legacy_loss_latch_scan_error = probe_error;
   reason = "LEGACY_LOSS_LATCH_MARKER_PROBE_FAILED";
   return false;
}


bool ClassifyLegacyLossLatchRootEntry(
   const string entry_name,
   bool &is_channel_directory,
   string &reason
)
{
   is_channel_directory = false;
   // These are current account-wide infrastructure directories, never legacy
   // channel directories.  IsSafeChannel also rejects them, but keep the
   // exclusion explicit so future naming changes cannot broaden the scan.
   if(entry_name == "locks" || entry_name == "account-policies")
      return true;
   if(!IsSafeChannel(entry_name))
      return true;

   string root_entry_path = "MetafxHQ\\" + entry_name;
   ResetLastError();
   bool is_regular_file = FileIsExist(root_entry_path, FILE_COMMON);
   int probe_error = GetLastError();
   if(!is_regular_file && probe_error == FILE_ERROR_IS_DIRECTORY)
   {
      is_channel_directory = true;
      return true;
   }

   // A safe mtc-* name returned by enumeration must be provably a directory.
   // A regular file, a vanished/racing entry, or any other probe error is
   // ambiguous and therefore blocks startup rather than hiding a latch.
   g_legacy_loss_latch_scan_error = probe_error;
   reason = "LEGACY_LOSS_LATCH_ENUMERATION_AMBIGUOUS";
   return false;
}


bool EnsureLegacyLossLatchScanAnchor(string &reason)
{
   string anchor_path = "MetafxHQ\\legacy-loss-latch-scan-anchor-v1.txt";
   string expected = "MetafxHQLegacyLossLatchScanAnchorV1";
   ResetLastError();
   bool anchor_exists = FileIsExist(anchor_path, FILE_COMMON);
   int probe_error = GetLastError();
   if(!anchor_exists)
   {
      if(probe_error != 0 && probe_error != FILE_ERROR_NOT_EXIST &&
         probe_error != FILE_ERROR_DIRECTORY_NOT_EXIST)
      {
         g_legacy_loss_latch_scan_error = probe_error;
         reason = "LEGACY_LOSS_LATCH_SCAN_ANCHOR_INVALID";
         return false;
      }
      if(!WriteCommonTextAtomic(anchor_path, expected))
      {
         reason = "LEGACY_LOSS_LATCH_SCAN_ANCHOR_WRITE_FAILED";
         return false;
      }
   }
   string observed = "";
   if(!ReadCommonText(anchor_path, 128, observed) ||
      Trimmed(observed) != expected)
   {
      reason = "LEGACY_LOSS_LATCH_SCAN_ANCHOR_INVALID";
      return false;
   }
   return true;
}


void SortStringsAscending(string &values[])
{
   for(int left = 0; left < ArraySize(values) - 1; left++)
   {
      for(int right = left + 1; right < ArraySize(values); right++)
      {
         if(StringCompare(values[right], values[left]) < 0)
         {
            string temporary = values[left];
            values[left] = values[right];
            values[right] = temporary;
         }
      }
   }
}


bool SameStringArrays(const string &left[], const string &right[])
{
   if(ArraySize(left) != ArraySize(right))
      return false;
   for(int index = 0; index < ArraySize(left); index++)
   {
      if(left[index] != right[index])
         return false;
   }
   return true;
}


bool ScanLegacyLossLatchesAcrossChannels(
   const string daily_file_name,
   const string weekly_file_name,
   string &channels[],
   bool &daily_found,
   bool &weekly_found,
   int &entry_count,
   string &reason
)
{
   ArrayResize(channels, 0);
   daily_found = false;
   weekly_found = false;
   entry_count = 0;
   string entry_name = "";
   ResetLastError();
   long search_handle = FileFindFirst(
      "MetafxHQ\\*",
      entry_name,
      FILE_COMMON
   );
   if(search_handle == INVALID_HANDLE)
   {
      g_legacy_loss_latch_scan_error = GetLastError();
      reason = "LEGACY_LOSS_LATCH_ENUMERATION_FAILED";
      return false;
   }

   while(true)
   {
      entry_count++;
      if(entry_count > LEGACY_LOSS_LATCH_SCAN_MAX_ENTRIES)
      {
         FileFindClose(search_handle);
         reason = "LEGACY_LOSS_LATCH_ENUMERATION_LIMIT_EXCEEDED";
         return false;
      }

      bool is_channel_directory = false;
      if(entry_name != "legacy-loss-latch-scan-anchor-v1.txt" &&
         !ClassifyLegacyLossLatchRootEntry(
            entry_name,
            is_channel_directory,
            reason
         ))
      {
         FileFindClose(search_handle);
         return false;
      }
      if(is_channel_directory)
      {
         int channel_count = ArraySize(channels);
         ArrayResize(channels, channel_count + 1);
         channels[channel_count] = entry_name;
         string legacy_state_path = "MetafxHQ\\" + entry_name +
            "\\trade-gateway\\state\\";
         bool marker_exists = false;
         if(!ProbeLegacyLossLatchMarker(
               legacy_state_path + daily_file_name,
               marker_exists,
               reason
            ))
         {
            FileFindClose(search_handle);
            return false;
         }
         if(marker_exists)
            daily_found = true;
         if(!ProbeLegacyLossLatchMarker(
               legacy_state_path + weekly_file_name,
               marker_exists,
               reason
            ))
         {
            FileFindClose(search_handle);
            return false;
         }
         if(marker_exists)
            weekly_found = true;
      }

      ResetLastError();
      bool has_next = FileFindNext(search_handle, entry_name);
      int find_next_error = GetLastError();
      if(has_next)
         continue;
      FileFindClose(search_handle);
      if(find_next_error != 0)
      {
         g_legacy_loss_latch_scan_error = find_next_error;
         reason = "LEGACY_LOSS_LATCH_ENUMERATION_FAILED";
         return false;
      }
      break;
   }

   SortStringsAscending(channels);
   return true;
}


bool MigrateLegacyLossLatchesAcrossChannels(string &reason)
{
   reason = "";
   g_legacy_loss_latch_migration_ready = false;
   g_legacy_loss_latch_scan_error = 0;
   g_legacy_loss_latch_scan_entries = 0;
   g_legacy_loss_latch_scan_channels = 0;
   if(g_account_execution_lock_handle == INVALID_HANDLE)
   {
      reason = "LEGACY_LOSS_LATCH_MIGRATION_LOCK_REQUIRED";
      return false;
   }

   datetime captured_day_start = BrokerDayStart();
   datetime captured_week_start = BrokerWeekStartForDay(captured_day_start);
   int daily_period = (int)captured_day_start;
   int weekly_period = (int)captured_week_start;
   string daily_account_path = "";
   string weekly_account_path = "";
   string daily_global_name = "";
   string weekly_global_name = "";
   string account_latch_directory = "";
   if(daily_period <= 0 || weekly_period <= 0 ||
      !AccountLossLatchDirectoryPath(account_latch_directory) ||
      !LossLatchGlobalName("DL", daily_period, daily_global_name) ||
      !LossLatchGlobalName("WL", weekly_period, weekly_global_name))
   {
      reason = "LEGACY_LOSS_LATCH_ACCOUNT_CONTEXT_INVALID";
      return false;
   }
   daily_account_path = account_latch_directory + "\\daily-loss-" +
      IntegerToString(daily_period) + ".lock";
   weekly_account_path = account_latch_directory + "\\weekly-loss-" +
      IntegerToString(weekly_period) + ".lock";

   // The legacy source names and canonical account targets must describe one
   // immutable broker-period snapshot. Recomputing either name mid-scan could
   // silently mix two days or weeks at midnight/Monday rollover.
   string daily_file_name = LegacyDailyLossLockFileNameForPeriod(
      captured_day_start
   );
   string weekly_file_name = LegacyWeeklyLossLockFileNameForPeriod(
      captured_week_start
   );
   if(StringLen(daily_file_name) < 1 || StringLen(weekly_file_name) < 1)
   {
      reason = "LEGACY_LOSS_LATCH_PERIOD_INVALID";
      return false;
   }
   if(!EnsureLegacyLossLatchScanAnchor(reason))
      return false;

   string first_channels[];
   string second_channels[];
   bool first_daily_found = false;
   bool first_weekly_found = false;
   bool second_daily_found = false;
   bool second_weekly_found = false;
   int first_entry_count = 0;
   int second_entry_count = 0;
   if(!ScanLegacyLossLatchesAcrossChannels(
         daily_file_name,
         weekly_file_name,
         first_channels,
         first_daily_found,
         first_weekly_found,
         first_entry_count,
         reason
      ) ||
      !ScanLegacyLossLatchesAcrossChannels(
         daily_file_name,
         weekly_file_name,
         second_channels,
         second_daily_found,
         second_weekly_found,
         second_entry_count,
         reason
      ))
      return false;

   g_legacy_loss_latch_scan_entries = first_entry_count > second_entry_count
      ? first_entry_count
      : second_entry_count;
   g_legacy_loss_latch_scan_channels = ArraySize(second_channels);
   if(!SameStringArrays(first_channels, second_channels))
   {
      reason = "LEGACY_LOSS_LATCH_CHANNEL_SET_CHANGED";
      return false;
   }

   datetime observed_day_start = BrokerDayStart();
   datetime observed_week_start = BrokerWeekStartForDay(observed_day_start);
   if(observed_day_start != captured_day_start ||
      observed_week_start != captured_week_start)
   {
      reason = "LEGACY_LOSS_LATCH_PERIOD_CHANGED";
      return false;
   }

   bool daily_found = first_daily_found || second_daily_found;
   bool weekly_found = first_weekly_found || second_weekly_found;
   // Legacy latch files did not carry account identity. If any safe channel
   // contains a current-period marker in either pass, conservatively attribute
   // it to this account. This can over-block after an account switch, but it
   // can never bypass a loss limit.
   // Upgrade contract: stop every pre-account-latch gateway before starting
   // this build. A legacy gateway does not honor the account execution lock
   // and could create new foreign-channel evidence after this bounded barrier.
   if(daily_found && !PersistDailyLossLatchContext(
         daily_period,
         daily_account_path,
         daily_global_name,
         reason
      ))
      return false;
   if(weekly_found && !PersistWeeklyLossLatchContext(
         weekly_period,
         weekly_account_path,
         weekly_global_name,
         reason
      ))
      return false;
   observed_day_start = BrokerDayStart();
   observed_week_start = BrokerWeekStartForDay(observed_day_start);
   if(observed_day_start != captured_day_start ||
      observed_week_start != captured_week_start)
   {
      reason = "LEGACY_LOSS_LATCH_PERIOD_CHANGED";
      return false;
   }
   g_legacy_loss_latch_migration_ready = true;
   return true;
}


bool LossLatchesAllowTrading(string &reason)
{
   if(!g_legacy_loss_latch_migration_ready)
   {
      reason = "LEGACY_LOSS_LATCH_MIGRATION_NOT_READY";
      return false;
   }
   // Probe both periods on every guard pass.  This makes persistence retries
   // independent of other portfolio blockers and prevents a daily latch from
   // starving repair of an already-active weekly latch (or vice versa).
   string daily_reason = "";
   string weekly_reason = "";
   bool daily_allows = DailyLossLatchAllowsTrading(daily_reason);
   bool weekly_allows = WeeklyLossLatchAllowsTrading(weekly_reason);
   if(!daily_allows)
   {
      reason = daily_reason;
      return false;
   }
   if(!weekly_allows)
   {
      reason = weekly_reason;
      return false;
   }
   return true;
}


bool ValidateCurrentRiskState(
   const double proposed_lots,
   string &reason
)
{
   // Latch state has priority over transient telemetry/limit reasons.  Once a
   // loss limit trips, status stays truthful and every guard pass retries the
   // account-wide durable marker before any later order can be considered.
   if(!LossLatchesAllowTrading(reason))
      return false;
   int positions = 0;
   double lots = 0.0;
   double floating_pnl = 0.0;
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
   if(!MathIsValidNumber(proposed_lots) || proposed_lots < 0.0)
   {
      reason = "PROPOSED_LOT_INVALID";
      return false;
   }
   if(lots + proposed_lots > MaxManagedTotalLots + 0.00000001)
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
   double daily_loss_limit = AccountBalance() * MaxDailyLossPercent / 100.0;
   if(AccountBalance() <= 0.0 || daily_risk_pnl <= -daily_loss_limit)
   {
      if(!ActivateDailyLossLatch(reason))
         return false;
      reason = "DAILY_LOSS_LIMIT_REACHED";
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
   double weekly_loss_limit = AccountBalance() * MaxManagedWeeklyLossPercent / 100.0;
   if(AccountBalance() <= 0.0 || weekly_risk_pnl <= -weekly_loss_limit)
   {
      if(!ActivateWeeklyLossLatch(reason))
         return false;
      reason = "WEEKLY_LOSS_LIMIT_REACHED";
      return false;
   }
   int consecutive_losses = 0;
   int cooldown_until = 0;
   if(!ReadManagedLossStreak(consecutive_losses, cooldown_until))
   {
      reason = "HISTORY_TELEMETRY_UNAVAILABLE";
      return false;
   }
   int broker_now = (int)TimeCurrent();
   if(consecutive_losses >= MaxConsecutiveManagedLosses &&
      broker_now < cooldown_until)
   {
      reason = "CONSECUTIVE_LOSS_COOLDOWN_ACTIVE";
      return false;
   }
   if(CurrentAccountDrawdownPercent() >= MaxAccountEquityDrawdownPercent)
   {
      reason = "ACCOUNT_EQUITY_DRAWDOWN_LIMIT_REACHED";
      return false;
   }
   return true;
}


bool ValidateClosedBarBinding(const CommandPayload &command, string &reason)
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
   int ea_closed_bar = (int)iTime(Symbol(), Period(), 1);
   int current_open_bar = (int)iTime(Symbol(), Period(), 0);
   if(ea_closed_bar <= 0 || current_open_bar <= 0 ||
      command.bar_time != ea_closed_bar ||
      command.bar_time >= current_open_bar)
   {
      reason = "CLOSED_BAR_IDENTITY_MISMATCH";
      return false;
   }
   if(command.reference_price <= 0.0)
   {
      reason = "REFERENCE_PRICE_INVALID";
      return false;
   }
   RefreshRates();
   double entry_price = command.action == "BUY" ? Ask : Bid;
   double point = MarketInfo(Symbol(), MODE_POINT);
   if(point <= 0.0 ||
      MathAbs(entry_price - command.reference_price) / point > MaxSignalDriftPoints)
   {
      reason = "SIGNAL_PRICE_DRIFT_EXCEEDED";
      return false;
   }
   return true;
}


bool ReadBrokerRiskMetadata(
   double &tick_value,
   double &tick_size_price,
   string &reason
)
{
   RefreshRates();
   tick_value = MarketInfo(Symbol(), MODE_TICKVALUE);
   double tick_size_points = MarketInfo(Symbol(), MODE_TICKSIZE);
   double point = MarketInfo(Symbol(), MODE_POINT);
   // MT4 MODE_TICKSIZE is expressed in points. MODE_TICKVALUE and account
   // equity/balance are already in the broker account's own currency units.
   // This intentionally needs no broker-name detection and no cent/pro-cent
   // x100 scaling: the account-unit scale cancels in risk-percent sizing.
   tick_size_price = tick_size_points * point;
   if(!MathIsValidNumber(tick_value) ||
      !MathIsValidNumber(tick_size_points) ||
      !MathIsValidNumber(point) ||
      !MathIsValidNumber(tick_size_price) ||
      tick_value <= 0.0 || tick_size_points <= 0.0 ||
      point <= 0.0 || tick_size_price <= 0.0)
   {
      reason = "BROKER_RISK_METADATA_INVALID";
      return false;
   }
   return true;
}


bool EstimateStopLossMoneyAtEntry(
   const CommandPayload &command,
   const double lots,
   const double entry_price,
   double &loss_money,
   double &reward_risk,
   string &reason
)
{
   loss_money = 0.0;
   reward_risk = 0.0;
   if(!MathIsValidNumber(lots) || lots <= 0.0)
   {
      reason = "RESOLVED_LOT_INVALID";
      return false;
   }
   double tick_value = 0.0;
   double tick_size_price = 0.0;
   if(!ReadBrokerRiskMetadata(tick_value, tick_size_price, reason))
      return false;
   double point = MarketInfo(Symbol(), MODE_POINT);
   double adverse_entry_price = command.action == "BUY"
      ? entry_price + SlippagePoints * point
      : entry_price - SlippagePoints * point;
   double stop_loss = NormalizeSymbolPrice(command.stop_loss);
   double take_profit = NormalizeSymbolPrice(command.take_profit);
   double risk_distance = command.action == "BUY"
      ? adverse_entry_price - stop_loss
      : stop_loss - adverse_entry_price;
   double reward_distance = command.action == "BUY"
      ? take_profit - adverse_entry_price
      : adverse_entry_price - take_profit;
   if(entry_price <= 0.0 || adverse_entry_price <= 0.0 ||
      risk_distance <= 0.0 || reward_distance <= 0.0)
   {
      reason = "RISK_PRICE_GEOMETRY_INVALID";
      return false;
   }
   double gross_loss_per_lot =
      risk_distance / tick_size_price * tick_value;
   double gross_reward_per_lot =
      reward_distance / tick_size_price * tick_value;
   double effective_commission = EffectiveEstimatedCommissionPerLot();
   double loss_per_lot = gross_loss_per_lot + effective_commission;
   double net_reward_per_lot =
      gross_reward_per_lot - effective_commission;
   loss_money = loss_per_lot * lots;
   reward_risk = net_reward_per_lot / loss_per_lot;
   if(!MathIsValidNumber(loss_per_lot) || loss_per_lot <= 0.0 ||
      !MathIsValidNumber(net_reward_per_lot) || net_reward_per_lot <= 0.0 ||
      !MathIsValidNumber(loss_money) || loss_money <= 0.0 ||
      !MathIsValidNumber(reward_risk) || reward_risk <= 0.0)
   {
      reason = "RISK_ESTIMATE_INVALID";
      return false;
   }
   return true;
}


bool EstimateStopLossMoney(
   const CommandPayload &command,
   const double lots,
   double &loss_money,
   double &reward_risk,
   string &reason
)
{
   RefreshRates();
   double entry_price = command.action == "BUY" ? Ask : Bid;
   return EstimateStopLossMoneyAtEntry(
      command,
      lots,
      entry_price,
      loss_money,
      reward_risk,
      reason
   );
}


bool ResolvePositionSize(
   const CommandPayload &command,
   double &resolved_lots,
   double &risk_capital_amount,
   double &estimated_risk_money,
   double &reward_risk,
   string &reason
)
{
   resolved_lots = 0.0;
   risk_capital_amount = 0.0;
   estimated_risk_money = 0.0;
   reward_risk = 0.0;
   if(!ValidateMoneyManagementConfiguration(reason))
      return false;
   if(command.action != "BUY" && command.action != "SELL")
   {
      reason = "ACTION_NOT_ALLOWED";
      return false;
   }
   if(Uppercase(Symbol()) != command.symbol)
   {
      reason = "SYMBOL_NOT_ALLOWED_OR_NOT_ATTACHED";
      return false;
   }
   risk_capital_amount = RiskCapitalAmount();
   if(!MathIsValidNumber(risk_capital_amount) || risk_capital_amount <= 0.0)
   {
      reason = "RISK_CAPITAL_UNAVAILABLE";
      return false;
   }
   if(MoneyManagementMode == MONEY_MANAGEMENT_FIXED_LOT)
   {
      resolved_lots = FixedLot;
      if(!EstimateStopLossMoney(
            command,
            resolved_lots,
            estimated_risk_money,
            reward_risk,
            reason
         ))
         return false;
      if(!MathIsValidNumber(estimated_risk_money) ||
         estimated_risk_money < 0.00000001)
      {
         reason = "RISK_ESTIMATE_BELOW_WIRE_MINIMUM";
         return false;
      }
      return true;
   }
   if(!MathIsValidNumber(command.stop_loss) || command.stop_loss <= 0.0)
   {
      reason = "RISK_STOP_LOSS_CALCULATION_FAILED";
      return false;
   }

   double loss_per_lot = 0.0;
   if(!EstimateStopLossMoney(
         command,
         1.0,
         loss_per_lot,
         reward_risk,
         reason
      ))
      return false;
   double requested_risk_budget =
      risk_capital_amount * EffectiveRiskPercent() / 100.0;
   double balance_risk_cap = AccountBalance() * MaxLossPerTradePercent / 100.0;
   double risk_budget = MathMin(requested_risk_budget, balance_risk_cap);
   if(!MathIsValidNumber(risk_budget) || risk_budget < 0.00000001 ||
      !MathIsValidNumber(loss_per_lot) || loss_per_lot <= 0.0)
   {
      reason = "RISK_BUDGET_INVALID";
      return false;
   }
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
   double remaining_portfolio_lots = MaxManagedTotalLots - managed_lots;
   if(remaining_portfolio_lots <= 0.0)
   {
      reason = "MAX_MANAGED_LOTS_EXCEEDED";
      return false;
   }
   double raw_lots = risk_budget / loss_per_lot;
   if(!NormalizeRiskVolumeDown(
         raw_lots,
         remaining_portfolio_lots,
         resolved_lots,
         reason
      ))
      return false;

   double minimum = 0.0;
   double maximum = 0.0;
   double step = 0.0;
   if(!ReadBrokerVolumeMetadata(minimum, maximum, step, reason))
      return false;
   if(!EstimateStopLossMoney(
         command,
         resolved_lots,
         estimated_risk_money,
         reward_risk,
         reason
      ))
      return false;
   while(estimated_risk_money > risk_budget)
   {
      resolved_lots = NormalizeDouble(resolved_lots - step, LotDigits());
      if(resolved_lots < minimum)
      {
         resolved_lots = 0.0;
         estimated_risk_money = 0.0;
         reason = "RISK_VOLUME_BELOW_BROKER_MINIMUM";
         return false;
      }
      if(!EstimateStopLossMoney(
            command,
            resolved_lots,
            estimated_risk_money,
            reward_risk,
            reason
         ))
         return false;
   }
   if(!MathIsValidNumber(estimated_risk_money) ||
      estimated_risk_money < 0.00000001)
   {
      reason = "RISK_ESTIMATE_BELOW_WIRE_MINIMUM";
      return false;
   }
   return ValidateResolvedVolume(resolved_lots, reason);
}


bool ValidateRiskEnvelopeAtEntry(
   const CommandPayload &command,
   const double proposed_lots,
   const double entry_price,
   double &final_estimated_risk_money,
   string &reason
)
{
   final_estimated_risk_money = 0.0;
   if(!ValidateCurrentRiskState(proposed_lots, reason))
      return false;
   double loss_money = 0.0;
   double reward_risk = 0.0;
   if(!EstimateStopLossMoneyAtEntry(
         command,
         proposed_lots,
         entry_price,
         loss_money,
         reward_risk,
         reason
      ))
      return false;
   if(!MathIsValidNumber(loss_money) || loss_money < 0.00000001)
   {
      reason = "RISK_ESTIMATE_BELOW_WIRE_MINIMUM";
      return false;
   }
   double balance = AccountBalance();
   if(!MathIsValidNumber(balance) || balance <= 0.0 ||
      loss_money / balance * 100.0 > MaxLossPerTradePercent)
   {
      reason = "MAX_LOSS_PER_TRADE_EXCEEDED";
      return false;
   }
   if(MoneyManagementMode == MONEY_MANAGEMENT_RISK_PERCENT)
   {
      double risk_capital = RiskCapitalAmount();
      if(!MathIsValidNumber(risk_capital) || risk_capital <= 0.0)
      {
         reason = "RISK_CAPITAL_UNAVAILABLE";
         return false;
      }
      double risk_budget =
         risk_capital * EffectiveRiskPercent() / 100.0;
      // The backend validates the final estimate against the already-declared
      // sizing capital. Equity can move between the sizing tick and this final
      // under-lock tick, so enforce the lower of the live and persisted budgets
      // to keep the durable ACK both safe and contract-valid.
      if(g_ack_has_sizing_evidence &&
         g_ack_position_sizing_mode == "RISK_PERCENT" &&
         MathIsValidNumber(g_ack_risk_capital_amount) &&
         g_ack_risk_capital_amount > 0.0 &&
         MathIsValidNumber(g_ack_risk_percent) &&
         g_ack_risk_percent >= 0.00000001)
      {
         double persisted_risk_budget =
            g_ack_risk_capital_amount * g_ack_risk_percent / 100.0;
         if(!MathIsValidNumber(persisted_risk_budget) ||
            persisted_risk_budget < 0.00000001)
         {
            reason = "RISK_BUDGET_INVALID";
            return false;
         }
         risk_budget = MathMin(risk_budget, persisted_risk_budget);
      }
      double tolerance = risk_budget * 0.000000001;
      if(!MathIsValidNumber(risk_budget) || risk_budget < 0.00000001 ||
         loss_money > risk_budget + tolerance)
      {
         reason = "RISK_PERCENT_BUDGET_EXCEEDED";
         return false;
      }
   }
   if(reward_risk + 0.00000001 < MinRewardRiskRatio)
   {
      reason = "MIN_REWARD_RISK_NOT_MET";
      return false;
   }
   final_estimated_risk_money = loss_money;
   return true;
}


bool ValidateRiskEnvelope(
   const CommandPayload &command,
   const double proposed_lots,
   string &reason
)
{
   RefreshRates();
   double entry_price = command.action == "BUY" ? Ask : Bid;
   double ignored_estimated_risk_money = 0.0;
   return ValidateRiskEnvelopeAtEntry(
      command,
      proposed_lots,
      entry_price,
      ignored_estimated_risk_money,
      reason
   );
}


bool ValidateMarginPreflight(
   const CommandPayload &command,
   const double proposed_lots,
   string &reason
)
{
   if(MarketInfo(Symbol(), MODE_TRADEALLOWED) <= 0.0)
   {
      reason = "SYMBOL_TRADING_DISABLED";
      return false;
   }
   datetime broker_time = TimeCurrent();
   if(broker_time <= 0 || !IsTradeAllowed(Symbol(), broker_time))
   {
      reason = "BROKER_SESSION_OR_SYMBOL_CLOSED";
      return false;
   }
   int order_type = command.action == "BUY" ? OP_BUY : OP_SELL;
   ResetLastError();
   double free_after = AccountFreeMarginCheck(
      Symbol(),
      order_type,
      proposed_lots
   );
   int margin_error = GetLastError();
   if(margin_error != 0 || free_after <= 0.0)
   {
      if(margin_error == 132)
         reason = "BROKER_MARKET_CLOSED";
      else if(margin_error == 133)
         reason = "BROKER_TRADE_DISABLED";
      else if(margin_error == 134)
         reason = "NOT_ENOUGH_FREE_MARGIN";
      else
         reason = "FREE_MARGIN_CHECK_FAILED";
      return false;
   }
   // AccountFreeMarginCheck is direction-aware and applies the broker's actual
   // hedge/asymmetric margin rules for this BUY or SELL.  MODE_MARGINREQUIRED
   // is documented as the margin for one lot BUY and can understate a SELL or
   // hedged order, so derive the projected margin from the broker's returned
   // free-margin delta instead.
   double current_free_margin = AccountFreeMargin();
   double current_margin = AccountMargin();
   double current_equity = AccountEquity();
   if(!MathIsValidNumber(current_free_margin) ||
      !MathIsValidNumber(current_margin) ||
      !MathIsValidNumber(current_equity) ||
      current_free_margin < 0.0 || current_margin < 0.0 ||
      current_equity <= 0.0)
   {
      reason = "BROKER_MARGIN_METADATA_INVALID";
      return false;
   }
   double incremental_margin = current_free_margin - free_after;
   double projected_margin = current_margin + incremental_margin;
   if(!MathIsValidNumber(incremental_margin) ||
      !MathIsValidNumber(projected_margin) || projected_margin < -0.00000001)
   {
      reason = "BROKER_MARGIN_METADATA_INVALID";
      return false;
   }
   if(projected_margin < 0.0)
      projected_margin = 0.0;
   double projected_level = projected_margin > 0.00000001
      ? current_equity / projected_margin * 100.0
      : 999999.0;
   if(!MathIsValidNumber(projected_level) ||
      projected_level < MinProjectedMarginLevelPercent)
   {
      reason = "PROJECTED_MARGIN_LEVEL_TOO_LOW";
      return false;
   }
   return true;
}


bool IsRolloverEntryWindow()
{
   if(!EnableRolloverEntryBlock)
      return false;
   int hour = TimeHour(TimeCurrent());
   if(RolloverStartHourBroker == RolloverEndHourBroker)
      return true;
   if(RolloverStartHourBroker < RolloverEndHourBroker)
      return hour >= RolloverStartHourBroker && hour < RolloverEndHourBroker;
   return hour >= RolloverStartHourBroker || hour < RolloverEndHourBroker;
}


bool EvaluateExecutionGuard(string &reason)
{
   if(!ValidateConfiguredModes(reason))
      return false;
   if(FileIsExist(KillMarkerPath(), FILE_COMMON))
   {
      reason = "KILL_SWITCH_ACTIVE";
      return false;
   }
   if(!IsConnected())
   {
      reason = "TERMINAL_NOT_CONNECTED";
      return false;
   }
   if(!ValidateQuoteFreshness(reason))
      return false;
   if(!ValidateMoneyManagementConfiguration(reason))
      return false;
   double guard_probe_lots = FixedLot;
   if(MoneyManagementMode == MONEY_MANAGEMENT_RISK_PERCENT)
   {
      double broker_maximum = 0.0;
      double broker_step = 0.0;
      if(!ReadBrokerVolumeMetadata(
            guard_probe_lots,
            broker_maximum,
            broker_step,
            reason
         ))
         return false;
   }
   if(!ValidateCurrentRiskState(guard_probe_lots, reason))
      return false;
   if(IsRolloverEntryWindow())
   {
      reason = "ROLLOVER_ENTRY_WINDOW_BLOCKED";
      return false;
   }
   if(LifecycleUsesSessionClose() && SessionCloseIsDue())
   {
      reason = "SESSION_CLOSE_ENTRY_WINDOW_BLOCKED";
      return false;
   }
   if(GatewayMode == GATEWAY_DEMO && !IsNonRealAccount())
   {
      reason = "DEMO_MODE_REQUIRES_DEMO_ACCOUNT";
      return false;
   }
   if(GatewayMode == GATEWAY_LIVE && IsNonRealAccount())
   {
      reason = "LIVE_MODE_REQUIRES_NON_DEMO_ACCOUNT";
      return false;
   }
   if(GatewayMode == GATEWAY_LIVE && !LiveArmed)
   {
      reason = "LIVE_NOT_ARMED";
      return false;
   }
   if(!SignedCommandVerificationAvailable())
   {
      reason = "SIGNED_COMMAND_VERIFICATION_NOT_READY";
      return false;
   }
   if(GatewayMode != GATEWAY_SHADOW && !IsTradeAllowed())
   {
      reason = "EA_TRADING_NOT_ALLOWED";
      return false;
   }
   reason = "READY";
   return true;
}


void UpdateRiskTelemetry(const bool force)
{
   int now = NowUtc();
   if(!force && g_risk_cache_at > 0 && now >= g_risk_cache_at && now - g_risk_cache_at < 5)
      return;
   int managed_positions = 0;
   double managed_lots = 0.0;
   double floating_pnl = 0.0;
   int trades_today = 0;
   double daily_pnl = 0.0;
   double weekly_pnl = 0.0;
   int consecutive_losses = 0;
   int cooldown_until = 0;
   bool position_telemetry_ready = ReadManagedOpenState(
      managed_positions,
      managed_lots,
      floating_pnl
   );
   bool history_telemetry_ready =
      CountManagedTradesToday(trades_today) &&
      ManagedDailyPnl(daily_pnl) &&
      ManagedWeeklyPnl(weekly_pnl) &&
      ReadManagedLossStreak(consecutive_losses, cooldown_until);
   if(position_telemetry_ready)
   {
      g_cached_managed_positions = managed_positions;
      g_cached_managed_lots = managed_lots;
   }
   else
   {
      g_cached_managed_positions = 0;
      g_cached_managed_lots = 0.0;
   }
   if(history_telemetry_ready)
   {
      g_cached_trades_today = trades_today;
      g_cached_managed_daily_pnl = daily_pnl;
      g_cached_managed_weekly_pnl = weekly_pnl;
      g_cached_consecutive_losses = consecutive_losses;
      g_cached_cooldown_until = cooldown_until;
   }
   else
   {
      g_cached_trades_today = 0;
      g_cached_managed_daily_pnl = 0.0;
      g_cached_managed_weekly_pnl = 0.0;
      g_cached_consecutive_losses = 0;
      g_cached_cooldown_until = 0;
   }
   g_cached_account_drawdown_percent = CurrentAccountDrawdownPercent();
   g_cached_margin_level_percent = CurrentMarginLevelPercent();
   string reason = "";
   if(!position_telemetry_ready)
   {
      g_cached_execution_guard_ready = false;
      reason = "POSITION_TELEMETRY_UNAVAILABLE";
   }
   else if(!history_telemetry_ready)
   {
      g_cached_execution_guard_ready = false;
      reason = "HISTORY_TELEMETRY_UNAVAILABLE";
   }
   else
   {
      g_cached_execution_guard_ready = EvaluateExecutionGuard(reason);
   }
   g_cached_execution_guard_reason = reason;
   g_risk_cache_at = now;
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
      Uppercase(parts[2]) != Uppercase(Symbol()) ||
      Uppercase(parts[3]) != CurrentTimeframeName() ||
      !IsIntegerToken(parts[4]))
      return false;
   bar_time = (int)StringToInteger(parts[4]);
   if(bar_time < 946684800)
      return false;
   return true;
}


bool WriteLastOrderBar(const int bar_time)
{
   if(bar_time < 946684800)
      return false;
   return WriteCommonTextAtomic(
      LastOrderBarPath(),
      "v2|" + SnapshotChannel + "|" + Uppercase(Symbol()) + "|" +
      CurrentTimeframeName() + "|" + IntegerToString(bar_time)
   );
}


bool MigrateLegacyLastOrderBarState()
{
   string legacy_raw = "";
   string legacy_path = LegacyLastOrderBarPath();
   bool legacy_exists = FileIsExist(legacy_path, FILE_COMMON);
   if(!ReadCommonText(legacy_path, 64, legacy_raw))
      return !legacy_exists;
   legacy_raw = Trimmed(legacy_raw);
   if(!IsIntegerToken(legacy_raw))
      return false;
   int legacy_bar_time = (int)StringToInteger(legacy_raw);
   if(legacy_bar_time < 946684800)
      return false;

   int current_bar_time = 0;
   string current_raw = "";
   string current_path = LastOrderBarPath();
   bool current_exists = FileIsExist(current_path, FILE_COMMON);
   if(ReadCommonText(current_path, 256, current_raw))
   {
      if(!ReadLastOrderBar(current_bar_time))
         return false;
   }
   else if(current_exists)
      return false;
   else if(!WriteLastOrderBar(legacy_bar_time))
      return false;

   // Delete only after the stream-scoped state is durably written.  If the
   // process crashes earlier, startup repeats the conservative migration.
   ResetLastError();
   if(!FileDelete(LegacyLastOrderBarPath(), FILE_COMMON) &&
      FileIsExist(LegacyLastOrderBarPath(), FILE_COMMON))
      return false;
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
   if(!ReadRequiredString(keys, values, quoted, "schemaVersion", schema, reason) ||
      !ReadRequiredString(keys, values, quoted, "channelId", channel, reason) ||
      !ReadRequiredString(keys, values, quoted, "heartbeatId", heartbeat_id, reason) ||
      !ReadRequiredInteger(keys, values, quoted, "issuedAt", issued_at, reason) ||
      !ReadRequiredInteger(keys, values, quoted, "expiresAt", expires_at, reason))
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
   if(channel != SnapshotChannel || heartbeat_id != command.heartbeat_id)
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


bool ValidateRuntime(
   const CommandPayload &command,
   const double proposed_lots,
   string &reason
)
{
   if(!ValidateConfiguredModes(reason))
      return false;
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
      Uppercase(Symbol()) != command.symbol)
   {
      reason = "SYMBOL_NOT_ALLOWED_OR_NOT_ATTACHED";
      return false;
   }
   int command_period = TimeframeToPeriod(command.timeframe);
   if(command_period < PERIOD_M5 ||
      !CsvContains(AllowedTimeframes, command.timeframe) ||
      command_period != Period())
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
   if(!ValidateResolvedVolume(proposed_lots, reason))
      return false;
   if(!IsConnected())
   {
      reason = "TERMINAL_NOT_CONNECTED";
      return false;
   }
   if(!ValidateQuoteFreshness(reason))
      return false;
   if(!ValidateClosedBarBinding(command, reason))
      return false;
   if(MaxSpreadPoints <= 0 ||
      (int)MarketInfo(Symbol(), MODE_SPREAD) > MaxSpreadPoints)
   {
      reason = "SPREAD_LIMIT_EXCEEDED";
      return false;
   }
   if(!ValidateStops(command, reason))
      return false;
   if(!ValidateRiskEnvelope(command, proposed_lots, reason))
      return false;
   if(!ValidateMarginPreflight(command, proposed_lots, reason))
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
   if(IsRolloverEntryWindow())
   {
      reason = "ROLLOVER_ENTRY_WINDOW_BLOCKED";
      return false;
   }
   if(LifecycleUsesSessionClose() && SessionCloseIsDue())
   {
      reason = "SESSION_CLOSE_ENTRY_WINDOW_BLOCKED";
      return false;
   }
   if(GatewayMode == GATEWAY_LIVE && !LiveArmed)
   {
      reason = "LIVE_NOT_ARMED";
      return false;
   }
   if(!SignedCommandVerificationAvailable())
   {
      reason = "SIGNED_COMMAND_VERIFICATION_NOT_READY";
      return false;
   }

   if(GatewayMode == GATEWAY_SHADOW)
      return true;
   if(IsTesting() || IsOptimization())
   {
      reason = "TESTER_EXECUTION_DISABLED";
      return false;
   }
   if(GatewayMode == GATEWAY_DEMO && !IsNonRealAccount())
   {
      reason = "DEMO_MODE_REQUIRES_DEMO_ACCOUNT";
      return false;
   }
   if(GatewayMode == GATEWAY_LIVE)
   {
      if(IsNonRealAccount())
      {
         reason = "LIVE_MODE_REQUIRES_NON_DEMO_ACCOUNT";
         return false;
      }
   }
   if(IsTradeContextBusy())
   {
      reason = "TRADE_CONTEXT_BUSY";
      return false;
   }
   if(!IsTradeAllowed())
   {
      reason = "EA_TRADING_NOT_ALLOWED";
      return false;
   }

   return true;
}


void WriteDuplicateAck(
   const CommandPayload &command,
   const string reason_code
)
{
   string first_payload = BuildAckJson(
      command,
      "DUPLICATE",
      reason_code,
      -1,
      0,
      true
   );
   // Preserve the original idempotency ledger.  A different commandId that
   // reuses an old idempotencyKey is recorded only in its command ledger and
   // ACK; it must never overwrite the first command's durable identity.
   bool state_persisted = WriteCommonTextAtomic(
      CommandLedgerPath(command.command_id),
      first_payload
   );
   string payload = BuildAckJson(
      command,
      "DUPLICATE",
      reason_code,
      -1,
      0,
      state_persisted
   );
   if(state_persisted)
      WriteCommonTextAtomic(CommandLedgerPath(command.command_id), payload);
   WriteCommonTextAtomic(AckPath(command.command_id), payload);
   AppendAudit(payload);
   Print(
      "MetafxHQ Trade Gateway DUPLICATE ",
      reason_code,
      " command=",
      command.command_id
   );
}


bool RepairAckFromLedger(const CommandPayload &command)
{
   string payload = "";
   if(!ReadCommonText(CommandLedgerPath(command.command_id), MaxCommandBytes, payload))
      return false;
   if(!WriteCommonTextAtomic(AckPath(command.command_id), payload))
      return false;
   AppendAudit(payload);
   Print("MetafxHQ Trade Gateway repaired ACK command=", command.command_id);
   return true;
}


bool ReadProcessedCommandStatus(
   const CommandPayload &command,
   string &status
)
{
   status = "";
   string payload = "";
   if(!ReadCommonText(CommandLedgerPath(command.command_id), MaxCommandBytes, payload))
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


bool ReadPersistedSizingState(
   const CommandPayload &command,
   double &expected_lots,
   string &reason
)
{
   expected_lots = 0.0;
   string payload = "";
   if(!ReadCommonText(CommandLedgerPath(command.command_id), MaxCommandBytes, payload))
   {
      reason = "PERSISTED_SIZING_STATE_UNAVAILABLE";
      return false;
   }
   string keys[];
   string values[];
   int quoted[];
   if(!ParseFlatJson(payload, keys, values, quoted, reason))
   {
      reason = "PERSISTED_SIZING_STATE_INVALID";
      return false;
   }
   string stored_command_id = "";
   string stored_channel_id = "";
   string sizing_mode = "";
   string capital_base = "";
   double risk_percent = 0.0;
   double estimated_commission_per_lot = 0.0;
   double capital_amount = 0.0;
   double estimated_risk_money = 0.0;
   if(!ReadRequiredString(
         keys, values, quoted, "commandId", stored_command_id, reason
      ) ||
      !ReadRequiredString(
         keys, values, quoted, "channelId", stored_channel_id, reason
      ) ||
      !ReadRequiredDouble(
         keys, values, quoted, "fixedLot", expected_lots, reason
      ) ||
      !ReadRequiredString(
         keys, values, quoted, "positionSizingMode", sizing_mode, reason
      ) ||
      !ReadRequiredDouble(
         keys, values, quoted, "riskPercent", risk_percent, reason
      ) ||
       !ReadRequiredString(
          keys, values, quoted, "riskCapitalBase", capital_base, reason
       ) ||
       !ReadRequiredDouble(
          keys,
          values,
          quoted,
          "estimatedCommissionPerLot",
          estimated_commission_per_lot,
          reason
       ) ||
       !ReadRequiredDouble(
         keys, values, quoted, "riskCapitalAmount", capital_amount, reason
      ) ||
      !ReadRequiredDouble(
         keys, values, quoted, "estimatedRiskMoney", estimated_risk_money, reason
      ))
   {
      reason = "PERSISTED_SIZING_STATE_INVALID";
      return false;
   }
   if(stored_command_id != command.command_id ||
      stored_channel_id != SnapshotChannel ||
       (sizing_mode != "FIXED_LOT" && sizing_mode != "RISK_PERCENT") ||
       (capital_base != "EQUITY" && capital_base != "BALANCE") ||
       !MathIsValidNumber(expected_lots) || expected_lots <= 0.0 ||
       !MathIsValidNumber(risk_percent) ||
       risk_percent < 0.0 || risk_percent > 100.0 ||
       (sizing_mode == "RISK_PERCENT" && risk_percent <= 0.0) ||
       !MathIsValidNumber(estimated_commission_per_lot) ||
       estimated_commission_per_lot < 0.0 ||
       estimated_commission_per_lot > 1000000.0 ||
       !MathIsValidNumber(capital_amount) || capital_amount <= 0.0 ||
      !MathIsValidNumber(estimated_risk_money) || estimated_risk_money <= 0.0)
   {
      reason = "PERSISTED_SIZING_STATE_INVALID";
      return false;
   }
   SetAckSizingEvidence(
      expected_lots,
      sizing_mode,
      risk_percent,
      capital_base,
      estimated_commission_per_lot,
      capital_amount,
      estimated_risk_money
   );
   reason = "READY";
   return true;
}


bool IsGatewayOrderComment(const string comment, string &command_id)
{
   command_id = "";
   if(StringFind(comment, "HQ:", 0) != 0)
      return false;
   command_id = StringSubstr(comment, 3);
   return StringLen(command_id) == 28 &&
      StringSubstr(command_id, 0, 4) == "cmd-" &&
      IsSafeIdentifier(command_id);
}


bool CurrentChannelOwnsCommandId(const string command_id)
{
   if(!IsCommandIdentifier(command_id))
      return false;
   string raw = "";
   if(!ReadCommonText(CommandLedgerPath(command_id), MaxCommandBytes, raw))
      return false;
   string keys[];
   string values[];
   int quoted[];
   string reason = "";
   if(!ParseFlatJson(raw, keys, values, quoted, reason))
      return false;
   string stored_channel_id = "";
   string stored_command_id = "";
   if(!ReadRequiredString(
         keys,
         values,
         quoted,
         "channelId",
         stored_channel_id,
         reason
      ) ||
      !ReadRequiredString(
         keys,
         values,
         quoted,
         "commandId",
         stored_command_id,
         reason
      ))
      return false;
   return stored_channel_id == SnapshotChannel &&
      stored_command_id == command_id;
}


bool IsBrokerClosedGatewayComment(
   const string comment,
   const string command_id
)
{
   string expected = "HQ:" + command_id;
   if(comment == expected)
      return true;
   string suffixes[2];
   suffixes[0] = "[tp]";
   suffixes[1] = "[sl]";
   for(int index = 0; index < 2; index++)
   {
      string suffix = suffixes[index];
      int prefix_length = StringLen(comment) - StringLen(suffix);
      if(prefix_length < StringLen("HQ:cmd-") + 16 ||
         StringSubstr(comment, prefix_length) != suffix)
         continue;
      string prefix = StringSubstr(comment, 0, prefix_length);
      return StringFind(expected, prefix, 0) == 0;
   }
   return false;
}


bool IsAllowedTicketMapKey(const string key)
{
   return key == "schemaVersion" ||
      key == "channelId" ||
      key == "commandId" ||
      key == "ticket" ||
      key == "symbol" ||
      key == "action" ||
      key == "lots" ||
      key == "stopLoss" ||
      key == "takeProfit" ||
      key == "magicNumber" ||
      key == "createdAt";
}


bool WriteTicketCommandMap(
   const CommandPayload &command,
   const int ticket,
   const double expected_lots
)
{
   if(ticket <= 0 || !IsCommandIdentifier(command.command_id))
      return false;
   string payload = "{";
   payload += "\"schemaVersion\":\"metafx-hq-mt4-ticket-map-v1\",";
   payload += "\"channelId\":" + JsonString(SnapshotChannel) + ",";
   payload += "\"commandId\":" + JsonString(command.command_id) + ",";
   payload += "\"ticket\":" + IntegerToString(ticket) + ",";
   payload += "\"symbol\":" + JsonString(command.symbol) + ",";
   payload += "\"action\":" + JsonString(command.action) + ",";
   payload += "\"lots\":" + JsonNumber(expected_lots, LotDigits()) + ",";
   payload += "\"stopLoss\":" +
      JsonNumber(NormalizeSymbolPrice(command.stop_loss), SymbolPriceDigits()) + ",";
   payload += "\"takeProfit\":" +
      JsonNumber(NormalizeSymbolPrice(command.take_profit), SymbolPriceDigits()) + ",";
   payload += "\"magicNumber\":" + IntegerToString(MagicNumber) + ",";
   payload += "\"createdAt\":" + IntegerToString(NowUtc());
   payload += "}";
   return WriteCommonTextAtomic(TicketMapPath(ticket), payload);
}


bool ReadSelectedOrderTicketMap(string &command_id)
{
   command_id = "";
   int selected_ticket = OrderTicket();
   if(selected_ticket <= 0)
      return false;
   string raw = "";
   if(!ReadCommonText(TicketMapPath(selected_ticket), 2048, raw))
      return false;
   string keys[];
   string values[];
   int quoted[];
   string reason = "";
   if(!ParseFlatJson(raw, keys, values, quoted, reason) ||
      ArraySize(keys) != 11)
      return false;
   for(int key_index = 0; key_index < ArraySize(keys); key_index++)
   {
      if(!IsAllowedTicketMapKey(keys[key_index]))
         return false;
   }
   string schema_version = "";
   string channel_id = "";
   string mapped_command_id = "";
   string symbol = "";
   string action = "";
   int ticket = 0;
   int magic_number = 0;
   int created_at = 0;
   double lots = 0.0;
   double stop_loss = 0.0;
   double take_profit = 0.0;
   if(!ReadRequiredString(keys, values, quoted, "schemaVersion", schema_version, reason) ||
      !ReadRequiredString(keys, values, quoted, "channelId", channel_id, reason) ||
      !ReadRequiredString(keys, values, quoted, "commandId", mapped_command_id, reason) ||
      !ReadRequiredInteger(keys, values, quoted, "ticket", ticket, reason) ||
      !ReadRequiredString(keys, values, quoted, "symbol", symbol, reason) ||
      !ReadRequiredString(keys, values, quoted, "action", action, reason) ||
      !ReadRequiredDouble(keys, values, quoted, "lots", lots, reason) ||
      !ReadRequiredDouble(keys, values, quoted, "stopLoss", stop_loss, reason) ||
      !ReadRequiredDouble(keys, values, quoted, "takeProfit", take_profit, reason) ||
      !ReadRequiredInteger(keys, values, quoted, "magicNumber", magic_number, reason) ||
      !ReadRequiredInteger(keys, values, quoted, "createdAt", created_at, reason))
      return false;
   if(schema_version != "metafx-hq-mt4-ticket-map-v1" ||
      channel_id != SnapshotChannel ||
      !IsCommandIdentifier(mapped_command_id) ||
      ticket != selected_ticket ||
      created_at < 946684800 ||
      Uppercase(symbol) != Uppercase(OrderSymbol()) ||
      Uppercase(action) != (OrderType() == OP_BUY ? "BUY" : "SELL") ||
      magic_number != OrderMagicNumber())
      return false;
   double point = MarketInfo(OrderSymbol(), MODE_POINT);
   double lot_tolerance = MathMax(
      0.00000001,
      MarketInfo(OrderSymbol(), MODE_LOTSTEP) / 2.0
   );
   double price_tolerance = MathMax(0.00000001, point / 2.0);
   if(MathAbs(lots - OrderLots()) > lot_tolerance ||
      MathAbs(stop_loss - OrderStopLoss()) > price_tolerance ||
      MathAbs(take_profit - OrderTakeProfit()) > price_tolerance)
      return false;
   string exact_comment_command_id = "";
   bool comment_matches =
      IsGatewayOrderComment(OrderComment(), exact_comment_command_id) &&
      exact_comment_command_id == mapped_command_id;
   if(!comment_matches && OrderCloseTime() > 0)
      comment_matches = IsBrokerClosedGatewayComment(
         OrderComment(),
         mapped_command_id
      );
   if(!comment_matches)
      return false;
   command_id = mapped_command_id;
   return true;
}


bool ResolveSelectedOrderCommandId(string &command_id)
{
   if(ReadSelectedOrderTicketMap(command_id))
      return CurrentChannelOwnsCommandId(command_id);
   if(!IsGatewayOrderComment(OrderComment(), command_id))
      return false;
   // A MagicNumber can intentionally be shared by several HQ channels.  A
   // bare HQ comment is therefore only a recovery hint; the durable command
   // ledger under this exact channel must independently prove ownership.
   return CurrentChannelOwnsCommandId(command_id);
}


bool WriteSelectedOrderOutcome(const string command_id)
{
   if(!IsCommandIdentifier(command_id) ||
      !CurrentChannelOwnsCommandId(command_id) ||
      !IsManagedMarketOrderSelected())
      return false;
   int order_digits = (int)MarketInfo(OrderSymbol(), MODE_DIGITS);
   if(order_digits < 0 || order_digits > 8)
      order_digits = Digits;
   bool is_closed = OrderCloseTime() > 0;
   int outcome_observed_at = is_closed
      ? (int)OrderCloseTime()
      : NowUtc();
   string payload = "{";
   payload += "\"schemaVersion\":\"metafx-hq-mt4-outcome-v1\",";
   payload += "\"channelId\":" + JsonString(SnapshotChannel) + ",";
   payload += "\"commandId\":" + JsonString(command_id) + ",";
   payload += "\"executionState\":" +
      JsonString(is_closed ? "CLOSED" : "OPEN") + ",";
   // CLOSED outcomes are immutable.  Using the broker close time makes the
   // serialized payload stable so the five-second refresh does not rewrite
   // the same file forever.
   payload += "\"observedAt\":" + IntegerToString(outcome_observed_at) + ",";
   payload += "\"ticket\":" + IntegerToString(OrderTicket()) + ",";
   payload += "\"symbol\":" + JsonString(OrderSymbol()) + ",";
   payload += "\"action\":" + JsonString(OrderType() == OP_BUY ? "BUY" : "SELL") + ",";
   payload += "\"openedAt\":" + IntegerToString((int)OrderOpenTime()) + ",";
   payload += "\"closedAt\":" +
      (is_closed ? IntegerToString((int)OrderCloseTime()) : "null") + ",";
   payload += "\"openPrice\":" + JsonNumber(OrderOpenPrice(), order_digits) + ",";
   payload += "\"stopLoss\":" + JsonNumber(OrderStopLoss(), order_digits) + ",";
   payload += "\"takeProfit\":" + JsonNumber(OrderTakeProfit(), order_digits) + ",";
   payload += "\"lots\":" + JsonNumber(OrderLots(), LotDigits()) + ",";
   payload += "\"magicNumber\":" + IntegerToString(OrderMagicNumber()) + ",";
   // Keep the contract identity canonical even when a broker replaces the
   // tail of Account History comments with [tp] or [sl].  Resolution above is
   // independently bound to the durable ticket map and selected order fields.
   payload += "\"comment\":" + JsonString("HQ:" + command_id) + ",";
   payload += "\"closedPnl\":" +
      (is_closed
         ? JsonNumber(OrderProfit() + OrderSwap() + OrderCommission(), 2)
         : "null");
   payload += "}";
   if(is_closed)
   {
      string existing_payload = "";
      if(ReadCommonText(
         OutcomePath(command_id),
         MaxCommandBytes,
         existing_payload
      ) && Trimmed(existing_payload) == payload)
         return true;
   }
   return WriteCommonTextAtomic(OutcomePath(command_id), payload);
}


void ResetLegacyExecutedAck(LegacyExecutedAck &ack)
{
   ack.command_id = "";
   ack.symbol = "";
   ack.action = "";
   ack.actual_comment = "";
   ack.ticket = 0;
   ack.magic_number = 0;
   ack.observed_at = 0;
   ack.fixed_lot = 0.0;
   ack.filled_price = 0.0;
   ack.filled_slippage_points = 0.0;
   ack.stop_loss = 0.0;
   ack.take_profit = 0.0;
}


bool ParseLegacyExecutedAck(
   const string raw,
   LegacyExecutedAck &ack,
   string &reason
)
{
   ResetLegacyExecutedAck(ack);
   string keys[];
   string values[];
   int quoted[];
   if(!ParseFlatJson(raw, keys, values, quoted, reason))
      return false;
   string schema_version = "";
   string channel_id = "";
   string status = "";
   string verification_status = "";
   string execution_state = "";
   string signature_status = "";
   if(!ReadRequiredString(keys, values, quoted, "schemaVersion", schema_version, reason) ||
      !ReadRequiredString(keys, values, quoted, "channelId", channel_id, reason) ||
      !ReadRequiredString(keys, values, quoted, "commandId", ack.command_id, reason) ||
      !ReadRequiredString(keys, values, quoted, "status", status, reason))
      return false;
   if(Uppercase(status) != "EXECUTED")
   {
      reason = "NOT_EXECUTED";
      return false;
   }
   if(!ReadRequiredString(keys, values, quoted, "action", ack.action, reason) ||
      !ReadRequiredString(keys, values, quoted, "symbol", ack.symbol, reason) ||
      !ReadRequiredString(keys, values, quoted, "actualComment", ack.actual_comment, reason) ||
      !ReadRequiredString(keys, values, quoted, "verificationStatus", verification_status, reason) ||
      !ReadRequiredString(keys, values, quoted, "executionState", execution_state, reason) ||
      !ReadRequiredString(keys, values, quoted, "signatureVerificationStatus", signature_status, reason) ||
      !ReadRequiredInteger(keys, values, quoted, "ticket", ack.ticket, reason) ||
      !ReadRequiredInteger(keys, values, quoted, "actualMagicNumber", ack.magic_number, reason) ||
      !ReadRequiredInteger(keys, values, quoted, "observedAt", ack.observed_at, reason) ||
      !ReadRequiredDouble(keys, values, quoted, "fixedLot", ack.fixed_lot, reason) ||
      !ReadRequiredDouble(keys, values, quoted, "filledPrice", ack.filled_price, reason) ||
      !ReadRequiredDouble(keys, values, quoted, "filledSlippagePoints", ack.filled_slippage_points, reason) ||
      !ReadRequiredDouble(keys, values, quoted, "actualStopLoss", ack.stop_loss, reason) ||
      !ReadRequiredDouble(keys, values, quoted, "actualTakeProfit", ack.take_profit, reason))
      return false;
   int persisted_index = FindKey(keys, "statePersisted");
   bool state_persisted = persisted_index >= 0 &&
      quoted[persisted_index] == 0 &&
      Lowercase(values[persisted_index]) == "true";
   ack.action = Uppercase(ack.action);
   ack.symbol = Uppercase(ack.symbol);
   verification_status = Uppercase(verification_status);
   execution_state = Uppercase(execution_state);
   signature_status = Uppercase(signature_status);
   if(schema_version != ACK_SCHEMA ||
      channel_id != SnapshotChannel ||
      !IsCommandIdentifier(ack.command_id) ||
      (ack.action != "BUY" && ack.action != "SELL") ||
      ack.ticket <= 0 ||
       !IsManagedMagic(ack.magic_number) ||
      ack.observed_at < 946684800 ||
      ack.fixed_lot <= 0.0 ||
      ack.filled_price <= 0.0 ||
      ack.filled_slippage_points < 0.0 ||
      ack.stop_loss <= 0.0 ||
      ack.take_profit <= 0.0 ||
      !state_persisted ||
      signature_status != "VERIFIED" ||
      (verification_status != "VERIFIED_OPEN" &&
       verification_status != "VERIFIED_CLOSED") ||
      (execution_state != "OPEN" && execution_state != "CLOSED") ||
      !IsBrokerClosedGatewayComment(
         ack.actual_comment,
         ack.command_id
      ))
   {
      reason = "EXECUTED_ACK_IDENTITY_INVALID";
      return false;
   }
   return true;
}


bool SelectedOrderMatchesLegacyExecutedAck(
   const LegacyExecutedAck &ack
)
{
   if(OrderTicket() != ack.ticket ||
      OrderMagicNumber() != ack.magic_number ||
      Uppercase(OrderSymbol()) != ack.symbol)
      return false;
   int expected_type = ack.action == "BUY" ? OP_BUY : OP_SELL;
   if(OrderType() != expected_type)
      return false;
   double point = MarketInfo(OrderSymbol(), MODE_POINT);
   double lot_tolerance = MathMax(
      0.00000001,
      MarketInfo(OrderSymbol(), MODE_LOTSTEP) / 2.0
   );
   double price_tolerance = MathMax(0.00000001, point / 2.0);
   if(MathAbs(OrderLots() - ack.fixed_lot) > lot_tolerance ||
      MathAbs(OrderOpenPrice() - ack.filled_price) > price_tolerance ||
      MathAbs(OrderStopLoss() - ack.stop_loss) > price_tolerance ||
      MathAbs(OrderTakeProfit() - ack.take_profit) > price_tolerance)
      return false;
   return IsBrokerClosedGatewayComment(
      OrderComment(),
      ack.command_id
   );
}


bool WriteSelectedOrderLegacyTicketMap(const LegacyExecutedAck &ack)
{
   if(!SelectedOrderMatchesLegacyExecutedAck(ack))
      return false;
   int order_digits = (int)MarketInfo(OrderSymbol(), MODE_DIGITS);
   if(order_digits < 0 || order_digits > 8)
      order_digits = Digits;
   string payload = "{";
   payload += "\"schemaVersion\":\"metafx-hq-mt4-ticket-map-v1\",";
   payload += "\"channelId\":" + JsonString(SnapshotChannel) + ",";
   payload += "\"commandId\":" + JsonString(ack.command_id) + ",";
   payload += "\"ticket\":" + IntegerToString(ack.ticket) + ",";
   payload += "\"symbol\":" + JsonString(OrderSymbol()) + ",";
   payload += "\"action\":" + JsonString(ack.action) + ",";
   payload += "\"lots\":" + JsonNumber(OrderLots(), LotDigits()) + ",";
   payload += "\"stopLoss\":" + JsonNumber(OrderStopLoss(), order_digits) + ",";
   payload += "\"takeProfit\":" + JsonNumber(OrderTakeProfit(), order_digits) + ",";
   payload += "\"magicNumber\":" + IntegerToString(OrderMagicNumber()) + ",";
   payload += "\"createdAt\":" + IntegerToString(ack.observed_at);
   payload += "}";
   return WriteCommonTextAtomic(TicketMapPath(ack.ticket), payload);
}


bool LegacyBackfillTicketIsAmbiguous(
   LegacyExecutedAck &candidates[],
   const int candidate_index
)
{
   for(int index = 0; index < ArraySize(candidates); index++)
   {
      if(index == candidate_index)
         continue;
      if(candidates[index].ticket == candidates[candidate_index].ticket &&
         candidates[index].command_id != candidates[candidate_index].command_id)
         return true;
   }
   return false;
}


void BackfillLegacyExecutionMapsAndOutcomes()
{
   g_legacy_backfill_scanned = 0;
   g_legacy_backfill_recovered = 0;
   g_legacy_backfill_skipped = 0;
   g_legacy_backfill_ambiguous = 0;
   LegacyExecutedAck candidates[];
   ArrayResize(candidates, 0);
   string file_name = "";
   long search_handle = FileFindFirst(
      BasePath() + "\\processed\\commands\\*.json",
      file_name,
      FILE_COMMON
   );
   if(search_handle != INVALID_HANDLE)
   {
      do
      {
         if(g_legacy_backfill_scanned >= LEGACY_BACKFILL_MAX_ACKS)
            break;
         g_legacy_backfill_scanned++;
         string raw = "";
         if(!ReadCommonText(
            BasePath() + "\\processed\\commands\\" + file_name,
            MaxCommandBytes,
            raw
         ))
         {
            g_legacy_backfill_skipped++;
            continue;
         }
         LegacyExecutedAck candidate;
         string reason = "";
         if(!ParseLegacyExecutedAck(raw, candidate, reason))
         {
            if(reason != "NOT_EXECUTED")
               g_legacy_backfill_skipped++;
            continue;
         }
         int candidate_count = ArraySize(candidates);
         ArrayResize(candidates, candidate_count + 1);
         candidates[candidate_count] = candidate;
      }
      while(FileFindNext(search_handle, file_name));
      FileFindClose(search_handle);
   }

   for(int candidate_index = 0;
      candidate_index < ArraySize(candidates);
      candidate_index++)
   {
      LegacyExecutedAck candidate = candidates[candidate_index];
      if(LegacyBackfillTicketIsAmbiguous(candidates, candidate_index))
      {
         g_legacy_backfill_ambiguous++;
         continue;
      }
      if(!OrderSelect(candidate.ticket, SELECT_BY_TICKET) ||
         !IsManagedMarketOrderSelected() ||
         !SelectedOrderMatchesLegacyExecutedAck(candidate))
      {
         g_legacy_backfill_skipped++;
         continue;
      }
      bool map_exists = FileIsExist(
         TicketMapPath(candidate.ticket),
         FILE_COMMON
      );
      if(map_exists)
      {
         string mapped_command_id = "";
         if(!ReadSelectedOrderTicketMap(mapped_command_id) ||
            mapped_command_id != candidate.command_id)
         {
            // A corrupt or conflicting existing map is never overwritten.
            g_legacy_backfill_ambiguous++;
            continue;
         }
      }
      else if(!WriteSelectedOrderLegacyTicketMap(candidate))
      {
         g_legacy_backfill_skipped++;
         continue;
      }
      if(!WriteSelectedOrderOutcome(candidate.command_id))
      {
         g_legacy_backfill_skipped++;
         continue;
      }
      g_legacy_backfill_recovered++;
   }

   string event_json = "{";
   event_json += "\"type\":\"mt4_gateway.legacy_execution_backfill\",";
   event_json += "\"channelId\":" + JsonString(SnapshotChannel) + ",";
   event_json += "\"boundedLimit\":" + IntegerToString(LEGACY_BACKFILL_MAX_ACKS) + ",";
   event_json += "\"scanned\":" + IntegerToString(g_legacy_backfill_scanned) + ",";
   event_json += "\"recovered\":" + IntegerToString(g_legacy_backfill_recovered) + ",";
   event_json += "\"skipped\":" + IntegerToString(g_legacy_backfill_skipped) + ",";
   event_json += "\"ambiguous\":" + IntegerToString(g_legacy_backfill_ambiguous) + ",";
   event_json += "\"automaticRetry\":false,";
   event_json += "\"observedAt\":" + IntegerToString(NowUtc());
   event_json += "}";
   AppendAudit(event_json);
   Print(
      "MetafxHQ: Legacy execution backfill scanned=",
      IntegerToString(g_legacy_backfill_scanned),
      " recovered=", IntegerToString(g_legacy_backfill_recovered),
      " skipped=", IntegerToString(g_legacy_backfill_skipped),
      " ambiguous=", IntegerToString(g_legacy_backfill_ambiguous),
      " automaticRetry=false"
   );
}


void RefreshManagedOutcomeFiles(const bool force)
{
   int now = NowUtc();
   if(!force && g_last_outcome_refresh_at > 0 &&
      now >= g_last_outcome_refresh_at && now - g_last_outcome_refresh_at < 5)
      return;
   g_last_outcome_refresh_at = now;
   for(int index = OrdersTotal() - 1; index >= 0; index--)
   {
      if(!OrderSelect(index, SELECT_BY_POS, MODE_TRADES) ||
         !IsManagedMarketOrderSelected())
         continue;
      string command_id = "";
      if(ResolveSelectedOrderCommandId(command_id))
         WriteSelectedOrderOutcome(command_id);
   }
   int history_start = MathMax(0, OrdersHistoryTotal() - 200);
   for(int history_index = OrdersHistoryTotal() - 1;
      history_index >= history_start;
      history_index--)
   {
      if(!OrderSelect(history_index, SELECT_BY_POS, MODE_HISTORY) ||
         !IsManagedMarketOrderSelected())
         continue;
      string history_command_id = "";
      if(ResolveSelectedOrderCommandId(history_command_id))
         WriteSelectedOrderOutcome(history_command_id);
   }
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

   double tick_value = 0.0;
   double tick_size_price = 0.0;
   string metadata_reason = "";
   if(!ReadBrokerRiskMetadata(
         tick_value,
         tick_size_price,
         metadata_reason
      ))
      return "RISK_UNAVAILABLE";

   double normalized_stop = NormalizeSymbolPrice(stop_loss);
   double risk_distance = action == "BUY"
      ? filled_entry - normalized_stop
      : normalized_stop - filled_entry;
   if(!MathIsValidNumber(risk_distance) || risk_distance <= 0.0)
      return "RISK_UNAVAILABLE";

   double actual_risk =
      (risk_distance / tick_size_price * tick_value +
       estimated_commission_per_lot) * volume;
   if(!MathIsValidNumber(actual_risk) || actual_risk < 0.00000001)
      return "RISK_UNAVAILABLE";

   bool slippage_reserve_exceeded = false;
   double point = MarketInfo(Symbol(), MODE_POINT);
   if(MathIsValidNumber(requested_entry) && requested_entry > 0.0 &&
      MathIsValidNumber(point) && point > 0.0)
   {
      double adverse_slippage_points = action == "BUY"
         ? MathMax(0.0, filled_entry - requested_entry) / point
         : MathMax(0.0, requested_entry - filled_entry) / point;
      if(adverse_slippage_points >
         (double)SlippagePoints + 0.00000001)
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


bool CaptureSelectedOrderEvidence(
   const CommandPayload &command,
   const int ticket,
   const double expected_lots,
   const double submitted_price,
   string &reason
)
{
   ResetAckExecutionEvidence();
   ResetLastError();
   if(!OrderSelect(ticket, SELECT_BY_TICKET, MODE_TRADES))
   {
      g_ack_verification_status = "SELECT_FAILED";
      g_ack_execution_state = "UNKNOWN";
      reason = "ORDER_POST_SEND_SELECT_FAILED";
      return false;
   }
   g_ack_has_execution_evidence = true;
   g_ack_filled_price = OrderOpenPrice();
   double point = MarketInfo(command.symbol, MODE_POINT);
   g_ack_filled_slippage_points = point > 0.0 && submitted_price > 0.0
      ? MathAbs(OrderOpenPrice() - submitted_price) / point
      : 0.0;
   g_ack_actual_stop_loss = OrderStopLoss();
   g_ack_actual_take_profit = OrderTakeProfit();
   g_ack_actual_magic_number = OrderMagicNumber();
   g_ack_actual_comment = OrderComment();
   bool is_closed = OrderCloseTime() > 0;
   g_ack_execution_state = is_closed ? "CLOSED" : "OPEN";
   if(is_closed)
   {
      g_ack_closed_at = (int)OrderCloseTime();
      g_ack_closed_pnl = OrderProfit() + OrderSwap() + OrderCommission();
      g_ack_has_closed_pnl = true;
   }
   int expected_type = command.action == "BUY" ? OP_BUY : OP_SELL;
   string expected_comment = "HQ:" + command.command_id;
   double lot_tolerance = 0.00000001;
   double price_tolerance = MathMax(0.00000001, point / 2.0);
   bool comment_matches = OrderComment() == expected_comment;
   if(!comment_matches && is_closed)
      comment_matches = IsBrokerClosedGatewayComment(
         OrderComment(),
         command.command_id
      );
   // Slippage is execution quality telemetry, not order identity. OrderSend
   // returning a ticket plus exact immutable fields proves execution even when
   // the broker fills outside the requested deviation.
   bool identity_matches = OrderTicket() == ticket &&
      Uppercase(OrderSymbol()) == command.symbol &&
      OrderType() == expected_type &&
      MathAbs(OrderLots() - expected_lots) <= lot_tolerance &&
      OrderMagicNumber() == MagicNumber &&
      comment_matches &&
      MathAbs(OrderStopLoss() - NormalizeSymbolPrice(command.stop_loss)) <= price_tolerance &&
      MathAbs(OrderTakeProfit() - NormalizeSymbolPrice(command.take_profit)) <= price_tolerance;
   if(!identity_matches)
   {
      g_ack_verification_status = "MISMATCH";
      reason = "ORDER_POST_SEND_VERIFICATION_MISMATCH";
      WriteSelectedOrderOutcome(command.command_id);
      return false;
   }
   string risk_assessment = FilledRiskAssessmentCode(
      command.action,
      expected_lots,
      submitted_price,
      OrderOpenPrice(),
      OrderStopLoss(),
      g_ack_estimated_commission_per_lot,
      g_ack_estimated_risk_money
   );
   string verified_prefix = is_closed
      ? "ORDER_VERIFIED_CLOSED"
      : "ORDER_VERIFIED_OPEN";
   g_ack_verification_status = is_closed ? "VERIFIED_CLOSED" : "VERIFIED_OPEN";
   WriteSelectedOrderOutcome(command.command_id);
   if(risk_assessment ==
      "SLIPPAGE_RESERVE_AND_RISK_ESTIMATE_EXCEEDED")
   {
      reason = verified_prefix +
         "_SLIPPAGE_RESERVE_AND_RISK_ESTIMATE_EXCEEDED";
   }
   else if(risk_assessment == "RISK_ESTIMATE_EXCEEDED")
   {
      reason = verified_prefix + "_RISK_ESTIMATE_EXCEEDED";
   }
   else if(risk_assessment == "SLIPPAGE_RESERVE_EXCEEDED")
   {
      reason = verified_prefix + "_SLIPPAGE_RESERVE_EXCEEDED";
   }
   else if(risk_assessment == "RISK_UNAVAILABLE")
   {
      reason = verified_prefix + "_RISK_UNAVAILABLE";
   }
   else
   {
      reason = verified_prefix;
   }
   return true;
}


int FindManagedCommandTicket(const CommandPayload &command, int &match_count)
{
   match_count = 0;
   int matched_ticket = -1;
   for(int index = OrdersTotal() - 1; index >= 0; index--)
   {
      if(!OrderSelect(index, SELECT_BY_POS, MODE_TRADES))
      {
         match_count = -1;
         return -1;
      }
      int order_type = OrderType();
      string resolved_command_id = "";
      bool command_reference_matches =
         ResolveSelectedOrderCommandId(resolved_command_id) &&
         resolved_command_id == command.command_id;
      if((order_type == OP_BUY || order_type == OP_SELL) &&
         IsManagedMagic(OrderMagicNumber()) &&
         Uppercase(OrderSymbol()) == command.symbol &&
         command_reference_matches)
      {
         match_count++;
         matched_ticket = OrderTicket();
      }
   }
   for(int history_index = OrdersHistoryTotal() - 1; history_index >= 0; history_index--)
   {
      if(!OrderSelect(history_index, SELECT_BY_POS, MODE_HISTORY))
      {
         match_count = -1;
         return -1;
      }
      int history_type = OrderType();
      string history_command_id = "";
      bool history_reference_matches =
         ResolveSelectedOrderCommandId(history_command_id) &&
         history_command_id == command.command_id;
      if(!history_reference_matches && OrderCloseTime() > 0 &&
         CurrentChannelOwnsCommandId(command.command_id))
         history_reference_matches = IsBrokerClosedGatewayComment(
            OrderComment(),
            command.command_id
         );
      if((history_type == OP_BUY || history_type == OP_SELL) &&
         IsManagedMagic(OrderMagicNumber()) &&
         Uppercase(OrderSymbol()) == command.symbol &&
         history_reference_matches)
      {
         match_count++;
         matched_ticket = OrderTicket();
      }
   }
   return matched_ticket;
}


void MarkRecoveryUnknown(
   const CommandPayload &command,
   const string reason,
   const int ticket,
   const int error_code
)
{
   ResetAckExecutionEvidence();
   g_ack_verification_status = "SELECT_FAILED";
   g_ack_execution_state = "UNKNOWN";
   FinalizeCommand(
      command,
      "EXECUTION_UNKNOWN",
      reason,
      ticket,
      error_code
   );
}


void ReconcileExecutingCommand(const CommandPayload &command)
{
   double expected_lots = 0.0;
   string sizing_reason = "";
   if(!ReadPersistedSizingState(command, expected_lots, sizing_reason))
   {
      MarkRecoveryUnknown(command, sizing_reason, -1, 0);
      return;
   }
   int match_count = 0;
   int ticket = FindManagedCommandTicket(command, match_count);
   if(match_count == 1 && ticket >= 0)
   {
      if(!WriteTicketCommandMap(command, ticket, expected_lots))
      {
         MarkRecoveryUnknown(
            command,
            "TICKET_COMMAND_MAP_WRITE_FAILED",
            ticket,
            GetLastError()
         );
         return;
      }
      string verification_reason = "";
      if(!CaptureSelectedOrderEvidence(
         command,
         ticket,
         expected_lots,
         0.0,
         verification_reason
      ))
      {
         FinalizeCommand(
            command,
            "EXECUTION_UNKNOWN",
            verification_reason,
            ticket,
            GetLastError()
         );
         return;
      }
      FinalizeCommand(
         command,
         "EXECUTED",
         "RECOVERED_ORDER_FOUND",
         ticket,
         0
      );
      return;
   }
   MarkRecoveryUnknown(
      command,
      match_count < 0
         ? "RECOVERY_TELEMETRY_UNAVAILABLE"
         : (match_count > 1
            ? "MULTIPLE_RECOVERY_MATCHES"
            : "RESTART_RECONCILIATION_REQUIRED"),
      -1,
      0
   );
}


string BrokerSendFailureReason(const int error_code)
{
   if(error_code == 129)
      return "ORDER_SEND_INVALID_PRICE_NO_RETRY";
   if(error_code == 130)
      return "ORDER_SEND_INVALID_STOPS_NO_RETRY";
   if(error_code == 131)
      return "ORDER_SEND_INVALID_VOLUME_NO_RETRY";
   if(error_code == 132)
      return "ORDER_SEND_MARKET_CLOSED_NO_RETRY";
   if(error_code == 133)
      return "ORDER_SEND_TRADE_DISABLED_NO_RETRY";
   if(error_code == 134)
      return "ORDER_SEND_NOT_ENOUGH_MONEY_NO_RETRY";
   if(error_code == 135)
      return "ORDER_SEND_PRICE_CHANGED_NO_RETRY";
   if(error_code == 136)
      return "ORDER_SEND_OFF_QUOTES_NO_RETRY";
   if(error_code == 138)
      return "ORDER_SEND_REQUOTE_NO_RETRY";
   if(error_code == 146)
      return "ORDER_SEND_TRADE_CONTEXT_BUSY_NO_RETRY";
   return "ORDER_SEND_FAILED_NO_AUTOMATIC_RETRY";
}


void ExecuteCommand(
   const CommandPayload &command,
   const string signed_raw,
   const double expected_lots
)
{
   string reason = "";
   if(!ReverifyCommandEnvelope(signed_raw, command, reason))
   {
      FinalizeCommand(command, "REJECTED", reason, -1, 0);
      return;
   }
      if(!ValidateRuntime(command, expected_lots, reason))
   {
      FinalizeCommand(command, "REJECTED", reason, -1, 0);
      return;
   }

   string executing_payload = BuildAckJson(
      command,
      "EXECUTING",
      "EXECUTION_STARTED",
      -1,
      0,
      true
   );
   if(!WriteExecutionMarkers(command, executing_payload))
   {
      string failed_payload = BuildAckJson(
         command,
         "FAILED_FINAL",
         "IDEMPOTENCY_STATE_WRITE_FAILED",
         -1,
         0,
         false
      );
      WriteCommonTextAtomic(AckPath(command.command_id), failed_payload);
      AppendAudit(failed_payload);
      return;
   }
   WriteCommonTextAtomic(AckPath(command.command_id), executing_payload);
   AppendAudit(executing_payload);

   // Serialize the complete mutable-guard + claim + OrderSend boundary across
   // every HQ channel and terminal using this broker account. File handles are
   // released by the OS after a crash, so this cannot leave a stale lock file
   // that silently deadlocks later execution.
   if(!AcquireAccountExecutionLock())
   {
      FinalizeCommand(
         command,
         "REJECTED",
         "ACCOUNT_EXECUTION_LOCK_UNAVAILABLE",
         -1,
         GetLastError()
      );
      return;
   }

   do
   {
      // Re-run every mutable guard while the account lock is held. There is no
      // automatic retry: uncertainty always stops this command.
       if(!ValidateRuntime(command, expected_lots, reason))
      {
         FinalizeCommand(command, "REJECTED", reason, -1, 0);
         break;
      }
      if(FileIsExist(KillMarkerPath(), FILE_COMMON))
      {
         FinalizeCommand(command, "REJECTED", "KILL_SWITCH_ACTIVE", -1, 0);
         break;
      }
      if(command.expires_at < NowUtc())
      {
         FinalizeCommand(command, "REJECTED", "COMMAND_EXPIRED", -1, 0);
         break;
      }
      if(!ValidateHeartbeat(command, reason) ||
         !ValidateQuoteFreshness(reason) ||
         !ValidateClosedBarBinding(command, reason) ||
         !ValidateStops(command, reason) ||
         !ValidateRiskEnvelope(command, expected_lots, reason) ||
         !ValidateMarginPreflight(command, expected_lots, reason))
      {
         FinalizeCommand(command, "REJECTED", reason, -1, 0);
         break;
      }

      RefreshRates();
      if((int)MarketInfo(Symbol(), MODE_SPREAD) > MaxSpreadPoints)
      {
         FinalizeCommand(
            command,
            "REJECTED",
            "SPREAD_LIMIT_EXCEEDED",
            -1,
            0
         );
         break;
      }
      int order_type = command.action == "BUY" ? OP_BUY : OP_SELL;
      double price = 0.0;
      double stop_loss = NormalizeSymbolPrice(command.stop_loss);
      double take_profit = NormalizeSymbolPrice(command.take_profit);
      // commandId is 28 ASCII characters; the HQ: prefix keeps the MT4 comment
      // at exactly 31 characters so restart/outcome reconciliation is lossless.
      string comment = "HQ:" + command.command_id;

      // Recompute HMAC and compare the complete decoded command one final time
      // at the irreversible execution boundary. Demo and Live share this path.
      if(!ReverifyCommandEnvelope(signed_raw, command, reason))
      {
         FinalizeCommand(command, "REJECTED", reason, -1, 0);
         break;
      }
      // Capture one final quote and use the exact same requested entry for the
      // risk envelope and OrderSend. Allowed broker slippage is already added
      // adversely inside EstimateStopLossMoneyAtEntry().
      RefreshRates();
      price = order_type == OP_BUY ? Ask : Bid;
      if(!MathIsValidNumber(price) || price <= 0.0)
      {
         FinalizeCommand(command, "REJECTED", "QUOTE_UNAVAILABLE", -1, 0);
         break;
      }
      if((int)MarketInfo(Symbol(), MODE_SPREAD) > MaxSpreadPoints)
      {
         FinalizeCommand(
            command,
            "REJECTED",
            "SPREAD_LIMIT_EXCEEDED",
            -1,
            0
         );
         break;
      }
      // Reprice the risk and margin envelopes with the persisted lot at the
      // irreversible boundary. The lot itself is never recalculated here.
      double final_estimated_risk_money = 0.0;
      if(!ValidateRiskEnvelopeAtEntry(
            command,
            expected_lots,
            price,
            final_estimated_risk_money,
            reason
         ) ||
         !ValidateMarginPreflight(command, expected_lots, reason))
      {
         FinalizeCommand(command, "REJECTED", reason, -1, 0);
         break;
      }
      // Persist the exact estimate validated against this submitted quote.
      // Recovery and the backend must never observe the earlier sizing-tick
      // estimate after execution has crossed this final under-lock gate.
      g_ack_estimated_risk_money = final_estimated_risk_money;
      string final_executing_payload = BuildAckJson(
         command,
         "EXECUTING",
         "FINAL_RISK_VALIDATED",
         -1,
         0,
         true
      );
      if(!WriteExecutionMarkers(command, final_executing_payload))
      {
         FinalizeCommand(
            command,
            "FAILED_FINAL",
            "FINAL_RISK_STATE_WRITE_FAILED",
            -1,
            GetLastError()
         );
         break;
      }
      WriteCommonTextAtomic(
         AckPath(command.command_id),
         final_executing_payload
      );
      AppendAudit(final_executing_payload);
      // Claim only this channel + symbol + timeframe stream after every
      // pre-send check, but before OrderSend, so crash recovery cannot resend.
      if(!WriteLastOrderBar(command.bar_time))
      {
         FinalizeCommand(
            command,
            "FAILED_FINAL",
            "ORDER_BAR_STATE_WRITE_FAILED",
            -1,
            0
         );
         break;
      }
      // A final kill/expiry read happens after the durable claim. If it changes,
      // the claim remains consumed deliberately rather than risking duplication.
      if(FileIsExist(KillMarkerPath(), FILE_COMMON))
      {
         FinalizeCommand(command, "REJECTED", "KILL_SWITCH_ACTIVE", -1, 0);
         break;
      }
      if(command.expires_at < NowUtc())
      {
         FinalizeCommand(command, "REJECTED", "COMMAND_EXPIRED", -1, 0);
         break;
      }
      // Input enum values can also arrive from edited SET files. Revalidate at
      // the final irreversible boundary even though OnInit/runtime gates have
      // already passed, so an unknown value can never reach OrderSend().
      if(!ValidateConfiguredModes(reason))
      {
         FinalizeCommand(command, "REJECTED", reason, -1, 0);
         break;
      }
      ResetLastError();
      int ticket = OrderSend(
         Symbol(),
         order_type,
         expected_lots,
         price,
         SlippagePoints,
         stop_loss,
         take_profit,
         comment,
         MagicNumber,
         0,
         clrNONE
      );
      int error_code = GetLastError();
      if(ticket < 0)
      {
         FinalizeCommand(
            command,
            "FAILED_FINAL",
            BrokerSendFailureReason(error_code),
            -1,
            error_code
         );
         break;
      }
      if(!WriteTicketCommandMap(command, ticket, expected_lots))
      {
         int ticket_map_error = GetLastError();
         // OrderSend has succeeded, but missing durable identity must remain
         // uncertain. No automatic retry is ever attempted.
         string ignored_verification_reason = "";
         CaptureSelectedOrderEvidence(
             command,
             ticket,
             expected_lots,
             price,
            ignored_verification_reason
         );
         FinalizeCommand(
            command,
            "EXECUTION_UNKNOWN",
            "TICKET_COMMAND_MAP_WRITE_FAILED",
            ticket,
            ticket_map_error
         );
         break;
      }
      string verification_reason = "";
      if(!CaptureSelectedOrderEvidence(
         command,
         ticket,
         expected_lots,
         price,
         verification_reason
      ))
      {
         FinalizeCommand(
            command,
            "EXECUTION_UNKNOWN",
            verification_reason,
            ticket,
            GetLastError()
         );
         break;
      }
      UpdateRiskTelemetry(true);
      FinalizeCommand(
         command,
         "EXECUTED",
         verification_reason,
         ticket,
         0
      );
   }
   while(false);

   ReleaseAccountExecutionLock();
}


void ProcessCommandFile()
{
   ResetAckExecutionEvidence();
   ResetAckSizingEvidence();
   string raw = "";
   if(!ReadCommonText(CommandPath(), MaxCommandBytes, raw))
      return;
   raw = Trimmed(raw);

   CommandPayload command;
   string reason = "";
   if(!ParseCommand(raw, command, reason))
   {
      if(IsSafeIdentifier(command.command_id) &&
         IsSafeIdentifier(command.idempotency_key))
      {
         FinalizeCommand(command, "REJECTED", reason, -1, 0);
      }
      else
      {
         PublishSystemAck("REJECTED", reason);
      }
      return;
   }

   if(FileIsExist(CommandLedgerPath(command.command_id), FILE_COMMON))
   {
      string processed_status = "";
      if(ReadProcessedCommandStatus(command, processed_status) &&
         (processed_status == "EXECUTING" ||
          processed_status == "EXECUTION_UNKNOWN"))
      {
         ReconcileExecutingCommand(command);
         return;
      }
      if(!FileIsExist(AckPath(command.command_id), FILE_COMMON))
         RepairAckFromLedger(command);
      return;
   }
   if(FileIsExist(IdempotencyLedgerPath(command.idempotency_key), FILE_COMMON))
   {
      WriteDuplicateAck(command, "IDEMPOTENCY_KEY_ALREADY_SEEN");
      return;
   }

   double resolved_lots = 0.0;
   double risk_capital_amount = 0.0;
   double estimated_risk_money = 0.0;
   double reward_risk = 0.0;
   if(!ResolvePositionSize(
         command,
         resolved_lots,
         risk_capital_amount,
         estimated_risk_money,
         reward_risk,
         reason
      ))
   {
      FinalizeCommand(command, "REJECTED", reason, -1, 0);
      return;
   }
   SetAckSizingEvidence(
      resolved_lots,
      PositionSizingModeName(),
      EffectiveRiskPercent(),
      RiskCapitalBaseName(),
      EffectiveEstimatedCommissionPerLot(),
      risk_capital_amount,
      estimated_risk_money
   );
   if(!ValidateRuntime(command, resolved_lots, reason))
   {
      FinalizeCommand(command, "REJECTED", reason, -1, 0);
      return;
   }
   if(GatewayMode == GATEWAY_SHADOW)
   {
      FinalizeCommand(
         command,
         "SHADOWED",
         "VALIDATED_WITHOUT_ORDER_SEND",
         -1,
         0
      );
      return;
   }
   ExecuteCommand(command, raw, resolved_lots);
}


bool LifecycleUsesMaxHolding()
{
   return PositionLifecycleMode == LIFECYCLE_MAX_HOLDING ||
      PositionLifecycleMode == LIFECYCLE_MAX_HOLDING_AND_SESSION_CLOSE;
}


bool LifecycleUsesSessionClose()
{
   return PositionLifecycleMode == LIFECYCLE_SESSION_CLOSE ||
      PositionLifecycleMode == LIFECYCLE_MAX_HOLDING_AND_SESSION_CLOSE;
}


bool SessionCloseIsDue()
{
   int hour = TimeHour(TimeCurrent());
   int minute = TimeMinute(TimeCurrent());
   return hour > SessionCloseHourBroker ||
      (hour == SessionCloseHourBroker && minute >= SessionCloseMinuteBroker);
}


bool LifecycleCloseGuard(string &reason)
{
   if(!ValidateConfiguredModes(reason))
      return false;
   if(PositionLifecycleMode == LIFECYCLE_SLTP_ONLY)
   {
      reason = "POSITION_LIFECYCLE_DISABLED";
      return false;
   }
   if(GatewayMode == GATEWAY_SHADOW)
   {
      reason = "SHADOW_EXECUTION_DISABLED";
      return false;
   }
   if(IsTesting() || IsOptimization())
   {
      reason = "TESTER_EXECUTION_DISABLED";
      return false;
   }
   if(GatewayMode == GATEWAY_DEMO && !IsNonRealAccount())
   {
      reason = "DEMO_MODE_REQUIRES_DEMO_ACCOUNT";
      return false;
   }
   if(GatewayMode == GATEWAY_LIVE)
   {
      if(IsNonRealAccount())
      {
         reason = "LIVE_MODE_REQUIRES_NON_DEMO_ACCOUNT";
         return false;
      }
      if(!LiveArmed)
      {
         reason = "LIVE_NOT_ARMED";
         return false;
      }
   }
   // Optional closes use the same signed control-plane readiness as opens.
   // This check intentionally applies to both Demo and armed Live modes.
   if(!SignedCommandVerificationAvailable())
   {
      reason = "SIGNED_COMMAND_VERIFICATION_NOT_READY";
      return false;
   }
   if(!IsConnected())
   {
      reason = "TERMINAL_NOT_CONNECTED";
      return false;
   }
   if(FileIsExist(KillMarkerPath(), FILE_COMMON))
   {
      reason = "KILL_SWITCH_ACTIVE";
      return false;
   }
   if(!IsTradeAllowed())
   {
      reason = "EA_TRADING_NOT_ALLOWED";
      return false;
   }
   if(IsTradeContextBusy())
   {
      reason = "TRADE_CONTEXT_BUSY";
      return false;
   }
   reason = "READY";
   return true;
}


bool LifecycleCloseCandidateExists(
   const datetime broker_now,
   const bool session_due
)
{
   for(int index = OrdersTotal() - 1; index >= 0; index--)
   {
      if(!OrderSelect(index, SELECT_BY_POS, MODE_TRADES) ||
         OrderMagicNumber() != MagicNumber || !IsManagedMarketOrderSelected())
         continue;
      string command_id = "";
      if(!ResolveSelectedOrderCommandId(command_id))
         continue;
      bool holding_due = LifecycleUsesMaxHolding() && MaxHoldingMinutes > 0 &&
         broker_now >= OrderOpenTime() + MaxHoldingMinutes * 60;
      if(!holding_due && !session_due)
         continue;
      if(!FileIsExist(LifecycleAttemptPath(OrderTicket()), FILE_COMMON))
         return true;
   }
   return false;
}


void ApplyOptionalPositionLifecycle()
{
   string lifecycle_guard_reason = "";
   if(!LifecycleCloseGuard(lifecycle_guard_reason))
      return;
   datetime broker_now = TimeCurrent();
   bool session_due = LifecycleUsesSessionClose() && SessionCloseIsDue();
   // The read-only probe avoids taking the account-wide execution lock on
   // every timer tick when this EA has no eligible lifecycle close.
   if(!LifecycleCloseCandidateExists(broker_now, session_due))
      return;
   if(!AcquireAccountExecutionLock())
      return;

   do
   {
      if(!LifecycleCloseGuard(lifecycle_guard_reason))
         break;
      broker_now = TimeCurrent();
      int lifecycle_observed_at = NowUtc();
      session_due = LifecycleUsesSessionClose() && SessionCloseIsDue();
      for(int index = OrdersTotal() - 1; index >= 0; index--)
      {
         if(!OrderSelect(index, SELECT_BY_POS, MODE_TRADES) ||
            OrderMagicNumber() != MagicNumber || !IsManagedMarketOrderSelected())
            continue;
         string command_id = "";
         if(!ResolveSelectedOrderCommandId(command_id))
            continue;
         bool holding_due = LifecycleUsesMaxHolding() && MaxHoldingMinutes > 0 &&
            broker_now >= OrderOpenTime() + MaxHoldingMinutes * 60;
         if(!holding_due && !session_due)
            continue;
         int ticket = OrderTicket();
         if(FileIsExist(LifecycleAttemptPath(ticket), FILE_COMMON))
            continue;
         string trigger = holding_due ? "MAX_HOLDING" : "SESSION_CLOSE";
         // Recheck the enum explicitly before preparing the one-shot marker.
         string mode_reason = "";
         if(!ValidateConfiguredModes(mode_reason))
            break;
         string order_symbol = OrderSymbol();
         int order_type = OrderType();
         double close_price = order_type == OP_BUY
            ? MarketInfo(order_symbol, MODE_BID)
            : MarketInfo(order_symbol, MODE_ASK);
         double lots = OrderLots();
         // Account type, mode enums, signing readiness, LiveArmed and all
         // execution guards are mutable runtime state. Re-evaluate them while
         // holding the account lock at the irreversible close boundary.
         if(!LifecycleCloseGuard(lifecycle_guard_reason))
            break;
         if(!WriteCommonTextAtomic(
            LifecycleAttemptPath(ticket),
            trigger + "|" + IntegerToString(lifecycle_observed_at)
         ))
            continue;
         ResetLastError();
         bool closed = close_price > 0.0 && OrderClose(
            ticket,
            lots,
            close_price,
            SlippagePoints,
            clrNONE
         );
         int close_error = GetLastError();
         string event_json = "{";
         event_json += "\"schemaVersion\":\"metafx-hq-mt4-lifecycle-event-v1\",";
         event_json += "\"channelId\":" + JsonString(SnapshotChannel) + ",";
         event_json += "\"commandId\":" + JsonString(command_id) + ",";
         event_json += "\"ticket\":" + IntegerToString(ticket) + ",";
         event_json += "\"trigger\":" + JsonString(trigger) + ",";
         event_json += "\"closed\":" + JsonBoolean(closed) + ",";
         event_json += "\"errorCode\":" + IntegerToString(close_error) + ",";
         event_json += "\"automaticRetry\":false,";
         event_json += "\"observedAt\":" + IntegerToString(NowUtc());
         event_json += "}";
         AppendAudit(event_json);
         if(OrderSelect(ticket, SELECT_BY_TICKET, MODE_HISTORY))
            WriteSelectedOrderOutcome(command_id);
      }
   }
   while(false);

   ReleaseAccountExecutionLock();
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


void InitWarning(
   const string stage,
   const string reason_code,
   const string message
)
{
   g_init_warning_code = reason_code;
   Print(message);
   RecordInitDiagnostic("warning", stage, reason_code, INIT_SUCCEEDED);
}


void UpdateChartStatus()
{
   UpdateRiskTelemetry(false);
   string state = "READY";
   if(FileIsExist(KillMarkerPath(), FILE_COMMON))
      state = "KILL SWITCH ACTIVE";
   string snapshot_state = "WAITING";
   if(g_last_snapshot_success_at > 0 && g_last_snapshot_write_ok)
      snapshot_state = "READY " +
         TimeToString((datetime)g_last_snapshot_success_at, TIME_SECONDS) +
         " UTC";
   else if(g_last_snapshot_attempt_at > 0)
      snapshot_state = "WRITE ERROR";
   string write_health = "READY";
   if(g_consecutive_atomic_write_failures > 0)
      write_health = "ERROR x" +
         IntegerToString(g_consecutive_atomic_write_failures) +
         " code=" + IntegerToString(g_last_atomic_write_error) +
         " at=" + TimeToString(
            (datetime)g_last_atomic_write_failure_at,
            TIME_SECONDS
         );
   Comment(
      "MetafxHQ Unified Snapshot + Trade Gateway\n",
      "Profile: ", EA_PROFILE, "\n",
      "Mode: ", ModeName(), "\n",
      "Channel: ", SnapshotChannel, "\n",
      "Chart: ", Symbol(), " ", CurrentTimeframeName(), "\n",
      "Snapshot: ", snapshot_state,
      " / every ", IntegerToString(SnapshotIntervalSeconds), " sec\n",
       "Command + heartbeat poll: every 1 sec\n",
       "Money Management: ", PositionSizingModeName(), "\n",
       "Fixed Lot / Risk %: ", DoubleToString(FixedLot, LotDigits()),
        " / ", DoubleToString(EffectiveRiskPercent(), 8), "% ",
       RiskCapitalBaseName(), "\n",
       "Risk Guard: ", g_cached_execution_guard_reason, "\n",
       "Atomic Write: ", write_health, "\n",
       "Legacy Recovery: scanned ",
       IntegerToString(g_legacy_backfill_scanned),
       ", restored ", IntegerToString(g_legacy_backfill_recovered),
       ", skipped ", IntegerToString(g_legacy_backfill_skipped),
       ", ambiguous ", IntegerToString(g_legacy_backfill_ambiguous), "\n",
       "Managed: ", IntegerToString(g_cached_managed_positions), "/",
       IntegerToString(MaxManagedOpenPositions), " positions, ",
       DoubleToString(g_cached_managed_lots, LotDigits()), "/",
       DoubleToString(MaxManagedTotalLots, LotDigits()), " lots\n",
       "State: ", state
   );
}


int OnInit()
{
   g_init_warning_code = "";
   g_legacy_loss_latch_migration_ready = false;
   g_trusted_signing_key_id = NormalizeSigningKeyId(TrustedSigningKeyId);
   string supplied_signing_key_id = Trimmed(TrustedSigningKeyId);
   if(!IsSafeChannel(SnapshotChannel))
   {
      return InitFailure(
         INIT_PARAMETERS_INCORRECT,
         "channel",
         "SNAPSHOT_CHANNEL_INVALID",
         "MetafxHQ: SnapshotChannel must start with mtc- and use safe ASCII characters."
      );
   }
   string configured_mode_reason = "";
   if(!ValidateConfiguredModes(configured_mode_reason))
   {
      return InitFailure(
         INIT_PARAMETERS_INCORRECT,
         "inputs",
         configured_mode_reason,
         "MetafxHQ: Gateway, lifecycle, money-management, or risk-capital mode is outside the supported enum range."
      );
   }
   if(StringLen(supplied_signing_key_id) > 0 &&
      !IsSigningKeyId(g_trusted_signing_key_id))
   {
      // Live + disarmed is a staging state.  Keep the EA attached so it can
      // publish the exact readiness diagnostic; only armed Live may fail
      // initialization for an invalid signing-key pin.
      if(GatewayMode == GATEWAY_LIVE && LiveArmed)
      {
         return InitFailure(
            INIT_PARAMETERS_INCORRECT,
            "signing",
            "LIVE_SIGNING_KEY_PIN_INVALID",
            "MetafxHQ: Live TrustedSigningKeyId must be hk- plus 64 hex characters."
         );
      }
      g_trusted_signing_key_id = "";
      if(GatewayMode == GATEWAY_LIVE)
      {
         InitWarning(
            "signing",
            "NON_EXECUTING_SIGNING_KEY_PIN_INVALID_IGNORED",
            "MetafxHQ: Live signing-key pin is invalid but LiveArmed is false, so the EA remains attached and trading stays blocked."
         );
      }
      else
      {
         InitWarning(
            "signing",
            "OPTIONAL_SIGNING_KEY_PIN_INVALID_IGNORED",
            "MetafxHQ: Optional Demo/Shadow signing-key pin is invalid and was ignored."
         );
      }
   }
   g_crypto_self_test_ok = CryptoSelfTest();
   if(!g_crypto_self_test_ok)
   {
      return InitFailure(
         INIT_FAILED,
         "crypto",
         "CRYPTO_SELF_TEST_FAILED",
         "MetafxHQ: HMAC-SHA256 self-test failed; stopping fail-closed."
      );
   }
   if(PollIntervalSeconds != 1 ||
      SnapshotIntervalSeconds < 2 || SnapshotIntervalSeconds > 60 ||
      SnapshotBars < 20 || SnapshotBars > 1000 ||
      MaxCommandBytes < 256 || MaxCommandBytes > 65536 ||
      MaxCommandTtlSeconds < 1 || MaxCommandTtlSeconds > 120 ||
      MaxHeartbeatTtlSeconds < 1 || MaxHeartbeatTtlSeconds > 60 ||
      MaxClockSkewSeconds < 0 ||
      MaxSpreadPoints <= 0 ||
      SlippagePoints < 0 ||
      MagicNumber <= 0 ||
      MaxSnapshotAgeSeconds < 5 || MaxSnapshotAgeSeconds > 900 ||
      MaxSignalDriftPoints <= 0 ||
       MaxQuoteAgeSeconds < 1 || MaxQuoteAgeSeconds > 120 ||
       MaxManagedOpenPositions < 1 ||
       !MathIsValidNumber(FixedLot) ||
       !MathIsValidNumber(RiskPercent) ||
       !MathIsValidNumber(EstimatedCommissionPerLot) ||
       !MathIsValidNumber(MaxManagedTotalLots) ||
       !MathIsValidNumber(MaxLossPerTradePercent) ||
       !MathIsValidNumber(MaxDailyLossPercent) ||
       !MathIsValidNumber(MaxManagedWeeklyLossPercent) ||
       !MathIsValidNumber(MaxAccountEquityDrawdownPercent) ||
       !MathIsValidNumber(MinRewardRiskRatio) ||
       !MathIsValidNumber(MinProjectedMarginLevelPercent) ||
       MaxManagedTotalLots <= 0.0 ||
        (MoneyManagementMode == MONEY_MANAGEMENT_FIXED_LOT &&
         FixedLot > MaxManagedTotalLots) ||
       MaxTradesPerBrokerDay < 1 ||
       MaxLossPerTradePercent <= 0.0 || MaxLossPerTradePercent > 100.0 ||
       MaxDailyLossPercent <= 0.0 || MaxDailyLossPercent > 100.0 ||
       MaxManagedWeeklyLossPercent <= 0.0 || MaxManagedWeeklyLossPercent > 100.0 ||
       MaxConsecutiveManagedLosses < 1 || MaxConsecutiveManagedLosses > 100 ||
       ConsecutiveLossCooldownMinutes < 1 || ConsecutiveLossCooldownMinutes > 10080 ||
       MaxAccountEquityDrawdownPercent <= 0.0 ||
       MaxAccountEquityDrawdownPercent > 100.0 ||
       MinRewardRiskRatio <= 0.0 ||
       MinProjectedMarginLevelPercent < 100.0 ||
       MaxHoldingMinutes < 0 ||
       (LifecycleUsesMaxHolding() && MaxHoldingMinutes < 1) ||
       SessionCloseHourBroker < 0 || SessionCloseHourBroker > 23 ||
       SessionCloseMinuteBroker < 0 || SessionCloseMinuteBroker > 59 ||
       RolloverStartHourBroker < 0 || RolloverStartHourBroker > 23 ||
       RolloverEndHourBroker < 0 || RolloverEndHourBroker > 23 ||
       (GatewayMode != GATEWAY_SHADOW && !RequireHeartbeat))
   {
      return InitFailure(
         INIT_PARAMETERS_INCORRECT,
         "inputs",
         "GATEWAY_INPUT_CONFIGURATION_INVALID",
         "MetafxHQ: Gateway input configuration is invalid. PollIntervalSeconds must be 1."
      );
   }
   string normalized_allowed_symbols = "";
   string normalized_allowed_timeframes = "";
   if(!NormalizeAllowedSymbolsCsv(
         AllowedSymbols,
         normalized_allowed_symbols
      ) ||
      !NormalizeAllowedTimeframesCsv(
         AllowedTimeframes,
         normalized_allowed_timeframes
      ))
   {
      return InitFailure(
         INIT_PARAMETERS_INCORRECT,
         "inputs",
         "ALLOWED_CHART_LIST_INVALID",
         "MetafxHQ: AllowedSymbols or AllowedTimeframes is invalid."
      );
   }
   if(GatewayMode == GATEWAY_LIVE &&
      !LiveSymbolExactAllowlistConfirmed())
   {
      return InitFailure(
         INIT_PARAMETERS_INCORRECT,
         "chart",
         "LIVE_SYMBOL_REQUIRES_EXACT_ALLOWLIST",
         "MetafxHQ: Live AllowedSymbols must include the exact attached broker Symbol() token."
      );
   }
   if(Period() < PERIOD_M5 ||
      !IsAllowedBrokerSymbol(AllowedSymbols, Symbol()) ||
      !CsvContains(AllowedTimeframes, CurrentTimeframeName()))
   {
      return InitFailure(
         INIT_PARAMETERS_INCORRECT,
         "chart",
         "SYMBOL_OR_TIMEFRAME_NOT_ALLOWED",
         "MetafxHQ: Attach the EA to an allowed symbol and timeframe M5 or higher."
      );
   }
   string money_management_reason = "";
   if(!ValidateMoneyManagementConfiguration(money_management_reason))
   {
      return InitFailure(
         INIT_PARAMETERS_INCORRECT,
         "money_management",
         money_management_reason,
         "MetafxHQ: " + money_management_reason
      );
   }
   string managed_magic_reason = "";
   if(!ValidateManagedMagicConfiguration(managed_magic_reason))
   {
      return InitFailure(
         INIT_PARAMETERS_INCORRECT,
         "managed_magic_numbers",
         managed_magic_reason,
         "MetafxHQ: " + managed_magic_reason
      );
   }

   EnsureFolders();
   string signing_reason = "";
   bool signing_ready = RefreshSigningReadiness(signing_reason);
   if(GatewayMode == GATEWAY_LIVE && LiveArmed && !signing_ready)
   {
      return InitFailure(
         INIT_PARAMETERS_INCORRECT,
         "signing",
         signing_reason,
         "MetafxHQ: Live signing configuration invalid: " + signing_reason
      );
   }
   if(GatewayMode != GATEWAY_LIVE && signing_ready &&
      StringLen(g_trusted_signing_key_id) > 0 && !g_signing_key_pinned)
   {
      InitWarning(
         "signing",
         "OPTIONAL_SIGNING_KEY_PIN_MISMATCH_IGNORED",
         "MetafxHQ: Optional Demo/Shadow signing-key pin does not match the backend active key and was ignored."
      );
   }
   else if(!signing_ready && StringLen(g_init_warning_code) == 0)
   {
      if(GatewayMode == GATEWAY_LIVE)
      {
         InitWarning(
            "signing",
            "LIVE_DISARMED_SIGNING_NOT_READY_" + signing_reason,
            "MetafxHQ: Live is selected but disarmed; signing is not ready and execution remains blocked: " + signing_reason
         );
      }
      else
      {
         InitWarning(
            "signing",
            "OPTIONAL_SIGNING_NOT_READY_" + signing_reason,
            "MetafxHQ: Signing is not ready in Demo/Shadow: " + signing_reason
         );
      }
   }
   if(!AcquireChannelLock())
   {
      return InitFailure(
         INIT_FAILED,
         "channel_lock",
         "SNAPSHOT_CHANNEL_ALREADY_OWNED",
         "MetafxHQ: Another EA instance already owns this SnapshotChannel."
      );
   }
   InvalidatePublishedRuntimeState();
   string account_execution_lock_path = "";
   if(!AccountExecutionLockPath(account_execution_lock_path))
   {
      InitFailure(
         INIT_FAILED,
         "account_lock",
         "ACCOUNT_EXECUTION_LOCK_IDENTITY_INVALID",
         "MetafxHQ: Unable to derive the broker-account execution lock."
      );
      ReleaseChannelLock();
      return INIT_FAILED;
   }
   if(!AcquireAccountExecutionLock())
   {
      InitFailure(
         INIT_FAILED,
         "portfolio_policy",
         "ACCOUNT_EXECUTION_LOCK_UNAVAILABLE",
         "MetafxHQ: Unable to lock the broker account for portfolio-policy validation."
      );
      ReleaseChannelLock();
      return INIT_FAILED;
   }
   string portfolio_policy_reason = "";
   bool portfolio_policy_ready = AcquirePortfolioPolicyLease(
      portfolio_policy_reason
   );
   string legacy_loss_latch_migration_reason = "";
   bool legacy_loss_latch_migration_ready = false;
   if(portfolio_policy_ready)
   {
      legacy_loss_latch_migration_ready =
         MigrateLegacyLossLatchesAcrossChannels(
            legacy_loss_latch_migration_reason
         );
   }
   ReleaseAccountExecutionLock();
   if(!portfolio_policy_ready)
   {
      InitFailure(
         INIT_FAILED,
         "portfolio_policy",
         portfolio_policy_reason,
         "MetafxHQ: Account portfolio policy is inconsistent: " +
         portfolio_policy_reason
      );
      ReleasePortfolioPolicyLease();
      ReleaseChannelLock();
      return INIT_FAILED;
   }
   if(!legacy_loss_latch_migration_ready)
   {
      InitFailure(
         INIT_FAILED,
         "loss_latch_migration",
         legacy_loss_latch_migration_reason,
         "MetafxHQ: Legacy account loss-latch migration stopped fail-closed: " +
         legacy_loss_latch_migration_reason
      );
      ReleasePortfolioPolicyLease();
      ReleaseChannelLock();
      return INIT_FAILED;
   }
   if(!MigrateLegacyLastOrderBarState())
   {
      InitFailure(
         INIT_FAILED,
         "bar_state",
         "LEGACY_ORDER_BAR_STATE_MIGRATION_FAILED",
         "MetafxHQ: Legacy one-order-per-bar state could not be migrated safely."
      );
      ReleasePortfolioPolicyLease();
      ReleaseChannelLock();
      return INIT_FAILED;
   }
   // Read-only, bounded recovery of v2.14 and earlier EXECUTED ledgers.  This
   // creates only ticket maps and outcome files after exact broker-order
   // identity checks; it never publishes, resends, modifies, or closes an
   // order.  Ambiguous or mismatched evidence remains unresolved fail-closed.
   BackfillLegacyExecutionMapsAndOutcomes();
   if(!EventSetTimer(1))
   {
      InitFailure(
         INIT_FAILED,
         "timer",
         "GATEWAY_TIMER_START_FAILED",
         "MetafxHQ: Unable to start the one-second gateway timer."
      );
      ReleasePortfolioPolicyLease();
      ReleaseChannelLock();
      return INIT_FAILED;
   }
   PublishSnapshotIfDue(true);
   if(!g_last_snapshot_write_ok)
   {
      InitFailure(
         INIT_FAILED,
         "snapshot",
         "INITIAL_SNAPSHOT_WRITE_FAILED",
         "MetafxHQ: Initial snapshot write failed; stopping fail-closed."
      );
      EventKillTimer();
      InvalidatePublishedRuntimeState();
      ReleasePortfolioPolicyLease();
      ReleaseChannelLock();
      return INIT_FAILED;
   }
   UpdateRiskTelemetry(true);
   if(!WriteCapabilitiesSnapshot())
   {
      InitFailure(
         INIT_FAILED,
         "capabilities",
         "INITIAL_CAPABILITIES_WRITE_FAILED",
         "MetafxHQ: Initial capabilities write failed; stopping fail-closed."
      );
      EventKillTimer();
      InvalidatePublishedRuntimeState();
      ReleasePortfolioPolicyLease();
      ReleaseChannelLock();
      return INIT_FAILED;
   }
   string event_json = BuildSystemAckJson("INIT_CONFIG", "UNIFIED_GATEWAY_STARTED");
   AppendAudit(event_json);
   UpdateChartStatus();
   if(!WriteStatusSnapshot())
   {
      InitFailure(
         INIT_FAILED,
         "status",
         "INITIAL_STATUS_WRITE_FAILED",
         "MetafxHQ: Initial status write failed; stopping fail-closed."
      );
      EventKillTimer();
      InvalidatePublishedRuntimeState();
      ReleasePortfolioPolicyLease();
      ReleaseChannelLock();
      return INIT_FAILED;
   }
   RecordInitDiagnostic("info", "ready", "INIT_SUCCEEDED", INIT_SUCCEEDED);
   return INIT_SUCCEEDED;
}


void OnDeinit(const int reason)
{
   EventKillTimer();
   string event_json = BuildSystemAckJson(
      "FAIL_SAFE",
      "GATEWAY_STOPPED_" + IntegerToString(reason)
   );
   AppendAudit(event_json);
   RecordInitDiagnostic(
      "info",
      "deinit",
      "GATEWAY_STOPPED_" + IntegerToString(reason),
      reason
   );
   InvalidatePublishedRuntimeState();
   ReleaseAccountExecutionLock();
   ReleasePortfolioPolicyLease();
   ReleaseChannelLock();
   Comment("");
}


void OnTick()
{
   g_last_tick_millis = GetTickCount();
}


void OnTimer()
{
   ApplyOptionalPositionLifecycle();
   ProcessCommandFile();
   RefreshManagedOutcomeFiles(false);
   if(!WriteCapabilitiesSnapshot())
      Print("MetafxHQ: Unable to update capabilities.json.");
   if(!WriteStatusSnapshot())
      Print("MetafxHQ: Unable to update status.json.");
   PublishSnapshotIfDue(false);
   UpdateChartStatus();
}
