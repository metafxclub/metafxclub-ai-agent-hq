#property strict
#property version   "2.16"
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

input string SnapshotChannel = "mtc-set-from-hq";
input ENUM_GATEWAY_MODE GatewayMode = GATEWAY_SHADOW;
input bool LiveArmed = false;
input string TrustedSigningKeyId = "";
input double FixedLot = 0.01;
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
string EA_VERSION = "2.16";
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


string DailyLossLockPath()
{
   return BasePath() + "\\state\\daily-loss-" +
      TimeToString(BrokerDayStart(), TIME_DATE) + ".lock";
}


datetime BrokerWeekStart()
{
   datetime day_start = BrokerDayStart();
   int day_of_week = TimeDayOfWeek(day_start);
   int days_since_monday = (day_of_week + 6) % 7;
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


string ModeName()
{
   if(GatewayMode == GATEWAY_DEMO)
      return "demo";
   if(GatewayMode == GATEWAY_LIVE)
      return "live";
   return "shadow";
}


string AccountModeName()
{
   if(IsDemo())
      return "demo";
   return "live";
}


string JsonBoolean(const bool value)
{
   if(value)
      return "true";
   return "false";
}


string LifecycleModeName()
{
   if(PositionLifecycleMode == LIFECYCLE_MAX_HOLDING)
      return "MAX_HOLDING";
   if(PositionLifecycleMode == LIFECYCLE_SESSION_CLOSE)
      return "SESSION_CLOSE";
   if(PositionLifecycleMode == LIFECYCLE_MAX_HOLDING_AND_SESSION_CLOSE)
      return "MAX_HOLDING_AND_SESSION_CLOSE";
   return "SLTP_ONLY";
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
   bool live_ready = GatewayMode == GATEWAY_LIVE &&
      !demo_account && signed_ready && explicit_live_pin && LiveArmed;
   string live_block_reason = "";
   if(demo_account)
      live_block_reason = "LIVE_MODE_REQUIRES_NON_DEMO_ACCOUNT";
   else if(GatewayMode != GATEWAY_LIVE)
      live_block_reason = "LIVE_MODE_NOT_SELECTED";
   else if(!signed_ready)
      live_block_reason = signing_reason;
   else if(!explicit_live_pin)
      live_block_reason = "LIVE_SIGNING_KEY_NOT_PINNED";
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


int LotDigits()
{
   double step = MarketInfo(Symbol(), MODE_LOTSTEP);
   if(step <= 0.0)
      return 2;
   int digits = 0;
   double scaled = step;
   while(digits < 8 && MathAbs(scaled - MathRound(scaled)) > 0.00000001)
   {
      scaled *= 10.0;
      digits++;
   }
   return digits;
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
   payload += "\"fixedLot\":" + DoubleToString(FixedLot, LotDigits()) + ",";
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

      // A six-character base such as EURUSD or XAUUSD may match a short
      // broker suffix (for example EURUSD.m, EURUSD#, XAUUSDpro or XAUUSD-ECN).
      // The command must still name the exact chart Symbol(), so this never
      // permits a command to cross from one attached broker symbol to another.
      int base_length = StringLen(allowed);
      int actual_length = StringLen(normalized_candidate);
      int suffix_length = actual_length - base_length;
      if(base_length < 6 || suffix_length < 1 || suffix_length > 8 ||
         StringSubstr(normalized_candidate, 0, base_length) != allowed)
         continue;
      bool suffix_valid = true;
      for(int suffix_index = base_length;
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


bool ValidateFixedLot(string &reason)
{
   double minimum = MarketInfo(Symbol(), MODE_MINLOT);
   double maximum = MarketInfo(Symbol(), MODE_MAXLOT);
   double step = MarketInfo(Symbol(), MODE_LOTSTEP);
   if(FixedLot <= 0.0 || minimum <= 0.0 || maximum <= 0.0 || step <= 0.0)
   {
      reason = "FIXED_LOT_CONFIGURATION_INVALID";
      return false;
   }
   if(FixedLot < minimum - 0.00000001 || FixedLot > maximum + 0.00000001)
   {
      reason = "FIXED_LOT_OUTSIDE_BROKER_RANGE";
      return false;
   }
   double steps = MathRound((FixedLot - minimum) / step);
   double normalized = NormalizeDouble(minimum + steps * step, LotDigits());
   if(MathAbs(normalized - FixedLot) > 0.00000001)
   {
      reason = "FIXED_LOT_NOT_ON_BROKER_STEP";
      return false;
   }
   return true;
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


void ReadManagedOpenState(int &positions, double &lots, double &floating_pnl)
{
   positions = 0;
   lots = 0.0;
   floating_pnl = 0.0;
   for(int index = OrdersTotal() - 1; index >= 0; index--)
   {
      if(!OrderSelect(index, SELECT_BY_POS, MODE_TRADES))
         continue;
      if(!IsManagedMarketOrderSelected())
         continue;
      positions++;
      lots += OrderLots();
      floating_pnl += OrderProfit() + OrderSwap() + OrderCommission();
   }
}


int CountManagedTradesToday()
{
   datetime day_start = BrokerDayStart();
   int count = 0;
   for(int index = OrdersHistoryTotal() - 1; index >= 0; index--)
   {
      if(!OrderSelect(index, SELECT_BY_POS, MODE_HISTORY))
         continue;
      if(IsManagedMarketOrderSelected() && OrderOpenTime() >= day_start)
         count++;
   }
   for(int open_index = OrdersTotal() - 1; open_index >= 0; open_index--)
   {
      if(!OrderSelect(open_index, SELECT_BY_POS, MODE_TRADES))
         continue;
      if(IsManagedMarketOrderSelected() && OrderOpenTime() >= day_start)
         count++;
   }
   return count;
}


double ManagedDailyPnl()
{
   datetime day_start = BrokerDayStart();
   double pnl = 0.0;
   for(int index = OrdersHistoryTotal() - 1; index >= 0; index--)
   {
      if(!OrderSelect(index, SELECT_BY_POS, MODE_HISTORY))
         continue;
      if(IsManagedMarketOrderSelected() && OrderCloseTime() >= day_start)
         pnl += OrderProfit() + OrderSwap() + OrderCommission();
   }
   for(int open_index = OrdersTotal() - 1; open_index >= 0; open_index--)
   {
      if(!OrderSelect(open_index, SELECT_BY_POS, MODE_TRADES))
         continue;
      if(IsManagedMarketOrderSelected())
         pnl += OrderProfit() + OrderSwap() + OrderCommission();
   }
   return pnl;
}


double ManagedWeeklyPnl()
{
   datetime week_start = BrokerWeekStart();
   double pnl = 0.0;
   for(int index = OrdersHistoryTotal() - 1; index >= 0; index--)
   {
      if(!OrderSelect(index, SELECT_BY_POS, MODE_HISTORY))
         continue;
      if(IsManagedMarketOrderSelected() && OrderCloseTime() >= week_start)
         pnl += OrderProfit() + OrderSwap() + OrderCommission();
   }
   for(int open_index = OrdersTotal() - 1; open_index >= 0; open_index--)
   {
      if(!OrderSelect(open_index, SELECT_BY_POS, MODE_TRADES))
         continue;
      if(IsManagedMarketOrderSelected())
         pnl += OrderProfit() + OrderSwap() + OrderCommission();
   }
   return pnl;
}


void ReadManagedLossStreak(int &loss_count, int &cooldown_until)
{
   loss_count = 0;
   cooldown_until = 0;
   int history_total = OrdersHistoryTotal();
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
         if(!OrderSelect(index, SELECT_BY_POS, MODE_HISTORY) ||
            !IsManagedMarketOrderSelected() || OrderCloseTime() <= 0)
            continue;
         datetime closed_at = OrderCloseTime();
         int ticket = OrderTicket();
         bool before_cursor = closed_at < before_time ||
            (closed_at == before_time && ticket < before_ticket);
         bool newer_than_best = closed_at > newest_time ||
            (closed_at == newest_time && ticket > newest_ticket);
         if(before_cursor && newer_than_best)
         {
            found = true;
            newest_time = closed_at;
            newest_ticket = ticket;
            newest_result = OrderProfit() + OrderSwap() + OrderCommission();
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


bool LatchDailyLoss()
{
   if(FileIsExist(DailyLossLockPath(), FILE_COMMON))
      return true;
   return WriteCommonTextAtomic(
      DailyLossLockPath(),
      "DAILY_LOSS_LIMIT_LATCHED|" + IntegerToString(NowUtc())
   );
}


bool LatchWeeklyLoss()
{
   if(FileIsExist(WeeklyLossLockPath(), FILE_COMMON))
      return true;
   return WriteCommonTextAtomic(
      WeeklyLossLockPath(),
      "WEEKLY_LOSS_LIMIT_LATCHED|" + IntegerToString(NowUtc())
   );
}


bool ValidateCurrentRiskState(string &reason)
{
   int positions = 0;
   double lots = 0.0;
   double floating_pnl = 0.0;
   ReadManagedOpenState(positions, lots, floating_pnl);
   if(positions >= MaxManagedOpenPositions)
   {
      reason = "MAX_MANAGED_POSITIONS_REACHED";
      return false;
   }
   if(lots + FixedLot > MaxManagedTotalLots + 0.00000001)
   {
      reason = "MAX_MANAGED_LOTS_EXCEEDED";
      return false;
   }
   if(CountManagedTradesToday() >= MaxTradesPerBrokerDay)
   {
      reason = "MAX_TRADES_PER_DAY_REACHED";
      return false;
   }
   if(FileIsExist(DailyLossLockPath(), FILE_COMMON))
   {
      reason = "DAILY_LOSS_LIMIT_LATCHED";
      return false;
   }
   double daily_pnl = ManagedDailyPnl();
   double daily_loss_limit = AccountBalance() * MaxDailyLossPercent / 100.0;
   if(AccountBalance() <= 0.0 || daily_pnl <= -daily_loss_limit)
   {
      LatchDailyLoss();
      reason = "DAILY_LOSS_LIMIT_REACHED";
      return false;
   }
   if(FileIsExist(WeeklyLossLockPath(), FILE_COMMON))
   {
      reason = "WEEKLY_LOSS_LIMIT_LATCHED";
      return false;
   }
   double weekly_pnl = ManagedWeeklyPnl();
   double weekly_loss_limit = AccountBalance() * MaxManagedWeeklyLossPercent / 100.0;
   if(AccountBalance() <= 0.0 || weekly_pnl <= -weekly_loss_limit)
   {
      LatchWeeklyLoss();
      reason = "WEEKLY_LOSS_LIMIT_REACHED";
      return false;
   }
   int consecutive_losses = 0;
   int cooldown_until = 0;
   ReadManagedLossStreak(consecutive_losses, cooldown_until);
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


bool EstimateStopLossMoney(
   const CommandPayload &command,
   double &loss_money,
   double &reward_risk,
   string &reason
)
{
   RefreshRates();
   double entry_price = command.action == "BUY" ? Ask : Bid;
   double stop_loss = NormalizeSymbolPrice(command.stop_loss);
   double take_profit = NormalizeSymbolPrice(command.take_profit);
   double risk_distance = MathAbs(entry_price - stop_loss);
   double reward_distance = MathAbs(take_profit - entry_price);
   double tick_value = MarketInfo(Symbol(), MODE_TICKVALUE);
   double tick_size_raw = MarketInfo(Symbol(), MODE_TICKSIZE);
   double point = MarketInfo(Symbol(), MODE_POINT);
   // MetaTrader documents MODE_TICKSIZE as points, but some CFD brokers
   // expose the price-sized value (for example 0.01 for XAUUSD).  A positive
   // value below one point cannot be a valid count of displayed points, so
   // treat it as price units; otherwise convert documented points to price.
   double tick_size_price = tick_size_raw < 1.0
      ? tick_size_raw
      : tick_size_raw * point;
   if(entry_price <= 0.0 || risk_distance <= 0.0 || reward_distance <= 0.0 ||
      tick_value <= 0.0 || tick_size_price <= 0.0)
   {
      reason = "BROKER_RISK_METADATA_INVALID";
      return false;
   }
   loss_money = risk_distance / tick_size_price * tick_value * FixedLot;
   reward_risk = reward_distance / risk_distance;
   if(!MathIsValidNumber(loss_money) || !MathIsValidNumber(reward_risk))
   {
      reason = "RISK_ESTIMATE_INVALID";
      return false;
   }
   return true;
}


bool ValidateRiskEnvelope(const CommandPayload &command, string &reason)
{
   if(!ValidateCurrentRiskState(reason))
      return false;
   double loss_money = 0.0;
   double reward_risk = 0.0;
   if(!EstimateStopLossMoney(command, loss_money, reward_risk, reason))
      return false;
   double balance = AccountBalance();
   if(balance <= 0.0 || loss_money / balance * 100.0 > MaxLossPerTradePercent)
   {
      reason = "MAX_LOSS_PER_TRADE_EXCEEDED";
      return false;
   }
   if(reward_risk + 0.00000001 < MinRewardRiskRatio)
   {
      reason = "MIN_REWARD_RISK_NOT_MET";
      return false;
   }
   return true;
}


bool ValidateMarginPreflight(const CommandPayload &command, string &reason)
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
   double free_after = AccountFreeMarginCheck(Symbol(), order_type, FixedLot);
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
   double margin_per_lot = MarketInfo(Symbol(), MODE_MARGINREQUIRED);
   if(margin_per_lot <= 0.0 || AccountEquity() <= 0.0)
   {
      reason = "BROKER_MARGIN_METADATA_INVALID";
      return false;
   }
   double projected_margin = AccountMargin() + margin_per_lot * FixedLot;
   double projected_level = projected_margin > 0.0
      ? AccountEquity() / projected_margin * 100.0
      : 999999.0;
   if(projected_level < MinProjectedMarginLevelPercent)
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
   if(!ValidateFixedLot(reason))
      return false;
   if(!ValidateCurrentRiskState(reason))
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
   if(!SignedCommandVerificationAvailable())
   {
      reason = "SIGNED_COMMAND_VERIFICATION_NOT_READY";
      return false;
   }
   if(GatewayMode == GATEWAY_DEMO && !IsDemo())
   {
      reason = "DEMO_MODE_REQUIRES_DEMO_ACCOUNT";
      return false;
   }
   if(GatewayMode == GATEWAY_LIVE && IsDemo())
   {
      reason = "LIVE_MODE_REQUIRES_NON_DEMO_ACCOUNT";
      return false;
   }
   if(GatewayMode == GATEWAY_LIVE && !LiveArmed)
   {
      reason = "LIVE_NOT_ARMED";
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
   double floating_pnl = 0.0;
   ReadManagedOpenState(
      g_cached_managed_positions,
      g_cached_managed_lots,
      floating_pnl
   );
   g_cached_trades_today = CountManagedTradesToday();
   g_cached_managed_daily_pnl = ManagedDailyPnl();
   g_cached_managed_weekly_pnl = ManagedWeeklyPnl();
   ReadManagedLossStreak(
      g_cached_consecutive_losses,
      g_cached_cooldown_until
   );
   g_cached_account_drawdown_percent = CurrentAccountDrawdownPercent();
   g_cached_margin_level_percent = CurrentMarginLevelPercent();
   string reason = "";
   g_cached_execution_guard_ready = EvaluateExecutionGuard(reason);
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
   string &reason
)
{
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
   if(!IsAllowedBrokerSymbol(AllowedSymbols, command.symbol) ||
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
   if(!ValidateFixedLot(reason))
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
   if(!ValidateRiskEnvelope(command, reason))
      return false;
   if(!ValidateMarginPreflight(command, reason))
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
   if(GatewayMode == GATEWAY_DEMO && !IsDemo())
   {
      reason = "DEMO_MODE_REQUIRES_DEMO_ACCOUNT";
      return false;
   }
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
   const int ticket
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
   payload += "\"lots\":" + JsonNumber(FixedLot, LotDigits()) + ",";
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


bool CaptureSelectedOrderEvidence(
   const CommandPayload &command,
   const int ticket,
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
   double lot_tolerance = MathMax(0.00000001, MarketInfo(command.symbol, MODE_LOTSTEP) / 2.0);
   double price_tolerance = MathMax(0.00000001, point / 2.0);
   bool slippage_observed = point > 0.0 && submitted_price > 0.0;
   bool slippage_within_limit = !slippage_observed ||
      g_ack_filled_slippage_points <= (double)SlippagePoints + 0.001;
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
      MathAbs(OrderLots() - FixedLot) <= lot_tolerance &&
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
   g_ack_verification_status = is_closed ? "VERIFIED_CLOSED" : "VERIFIED_OPEN";
   WriteSelectedOrderOutcome(command.command_id);
   reason = slippage_within_limit
      ? "ORDER_ACCEPTED"
      : "ORDER_ACCEPTED_WITH_SLIPPAGE_WARNING";
   return true;
}


int FindManagedCommandTicket(const CommandPayload &command, int &match_count)
{
   match_count = 0;
   int matched_ticket = -1;
   for(int index = OrdersTotal() - 1; index >= 0; index--)
   {
      if(!OrderSelect(index, SELECT_BY_POS, MODE_TRADES))
         continue;
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
         continue;
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


void ReconcileExecutingCommand(const CommandPayload &command)
{
   int match_count = 0;
   int ticket = FindManagedCommandTicket(command, match_count);
   if(match_count == 1 && ticket >= 0)
   {
      if(!WriteTicketCommandMap(command, ticket))
      {
         FinalizeCommand(
            command,
            "EXECUTION_UNKNOWN",
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
   FinalizeCommand(
      command,
      "EXECUTION_UNKNOWN",
      match_count > 1
         ? "MULTIPLE_RECOVERY_MATCHES"
         : "RESTART_RECONCILIATION_REQUIRED",
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
   const string signed_raw
)
{
   string reason = "";
   if(!ReverifyCommandEnvelope(signed_raw, command, reason))
   {
      FinalizeCommand(command, "REJECTED", reason, -1, 0);
      return;
   }
   if(!ValidateRuntime(command, reason))
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
      if(!ValidateRuntime(command, reason))
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
         !ValidateRiskEnvelope(command, reason) ||
         !ValidateMarginPreflight(command, reason))
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
      double price = order_type == OP_BUY ? Ask : Bid;
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
      ResetLastError();
      int ticket = OrderSend(
         Symbol(),
         order_type,
         FixedLot,
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
      if(!WriteTicketCommandMap(command, ticket))
      {
         int ticket_map_error = GetLastError();
         // OrderSend has succeeded, but missing durable identity must remain
         // uncertain. No automatic retry is ever attempted.
         string ignored_verification_reason = "";
         CaptureSelectedOrderEvidence(
            command,
            ticket,
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

   if(!ValidateRuntime(command, reason))
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
   ExecuteCommand(command, raw);
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


void ApplyOptionalPositionLifecycle()
{
   if(PositionLifecycleMode == LIFECYCLE_SLTP_ONLY ||
      GatewayMode == GATEWAY_SHADOW || IsTesting() || IsOptimization() ||
      !IsConnected() || !IsTradeAllowed() || IsTradeContextBusy() ||
      FileIsExist(KillMarkerPath(), FILE_COMMON) ||
      (GatewayMode == GATEWAY_LIVE &&
       (!LiveArmed || !SignedCommandVerificationAvailable())))
      return;
   datetime broker_now = TimeCurrent();
   int lifecycle_observed_at = NowUtc();
   bool session_due = LifecycleUsesSessionClose() && SessionCloseIsDue();
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
      if(!WriteCommonTextAtomic(
         LifecycleAttemptPath(ticket),
         trigger + "|" + IntegerToString(lifecycle_observed_at)
      ))
         continue;
      string order_symbol = OrderSymbol();
      int order_type = OrderType();
      double close_price = order_type == OP_BUY
         ? MarketInfo(order_symbol, MODE_BID)
         : MarketInfo(order_symbol, MODE_ASK);
      double lots = OrderLots();
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
       "Fixed Lot: ", DoubleToString(FixedLot, LotDigits()), "\n",
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
   if(StringLen(supplied_signing_key_id) > 0 &&
      !IsSigningKeyId(g_trusted_signing_key_id))
   {
      if(GatewayMode == GATEWAY_LIVE)
      {
         return InitFailure(
            INIT_PARAMETERS_INCORRECT,
            "signing",
            "LIVE_SIGNING_KEY_PIN_INVALID",
            "MetafxHQ: Live TrustedSigningKeyId must be hk- plus 64 hex characters."
         );
      }
      g_trusted_signing_key_id = "";
      InitWarning(
         "signing",
         "OPTIONAL_SIGNING_KEY_PIN_INVALID_IGNORED",
         "MetafxHQ: Optional Demo/Shadow signing-key pin is invalid and was ignored; the backend active key will be used."
      );
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
      MaxManagedTotalLots <= 0.0 || FixedLot > MaxManagedTotalLots ||
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
   string lot_reason = "";
   if(!ValidateFixedLot(lot_reason))
   {
      return InitFailure(
         INIT_PARAMETERS_INCORRECT,
         "fixed_lot",
         lot_reason,
         "MetafxHQ: " + lot_reason
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
   if(GatewayMode == GATEWAY_LIVE && !signing_ready)
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
   else if(GatewayMode != GATEWAY_LIVE && !signing_ready)
   {
      InitWarning(
         "signing",
         "OPTIONAL_SIGNING_NOT_READY_" + signing_reason,
         "MetafxHQ: Signing is not ready in Demo/Shadow: " + signing_reason
      );
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
