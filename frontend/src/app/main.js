const PROJECT_ASSET_ROOT = "./frontend/public/assets";
const MANAGER_EXEC_ASSET_ROOT = `${PROJECT_ASSET_ROOT}/agents/agent-manager-exec-v001`;
const MALE_ROSTER_ASSET_ROOT = `${PROJECT_ASSET_ROOT}/agents/male-roster-set-a-core-command-operators-v001`;
const AGENT_ASSET_VERSION = "20260612-multi-agent-roster-v001";
const MANAGER_STATIC_FRAME = `${MALE_ROSTER_ASSET_ROOT}/characters/02-hq-manager-male-static-v001.png`;
const SESSION_STORAGE_KEY = "metafx-ai-agent-hq-session-v001";
const OFFICE_LAYOUT_VERSION = 2;
const SIGNAL_DASHBOARD_VERSION = 6;
const SIGNAL_CHART_DISPLAY_BAR_OPTIONS = [40, 60, 120, 240, 500, 1000];
const SIGNAL_ANALYSIS_BAR_OPTIONS = [120, 180, 240, 300, 500, 1000];
const SIGNAL_CHART_DEFAULT_DISPLAY_BARS = 120;
const SIGNAL_DEFAULT_ANALYSIS_BARS = 120;
const SIGNAL_CHART_OVERLAY_LIMIT = 5;
const SIGNAL_CHART_DEFAULT_OVERLAYS = ["ema20", "ema50"];
const SIGNAL_CHART_OVERLAY_DEFINITIONS = [
  { id: "ema20", label: "EMA20", group: "average", color: "#f6ad25" },
  { id: "ema50", label: "EMA50", group: "average", color: "#27d4ff" },
  { id: "ema200", label: "EMA200", group: "average", color: "#b692ff" },
  { id: "sma20", label: "SMA20", group: "average", color: "#ffd76a" },
  { id: "sma50", label: "SMA50", group: "average", color: "#5ce6ee" },
  { id: "sma200", label: "SMA200", group: "average", color: "#c9a9ff" },
  { id: "bollinger", label: "Bollinger Bands", group: "average", color: "#65a9ff" },
  { id: "supportResistance", label: "แนวรับ–แนวต้าน", group: "price_action", color: "#5ae89c" },
  { id: "trendlines", label: "Trendline", group: "price_action", color: "#ffca58" },
  { id: "fibonacci", label: "Fibonacci", group: "price_action", color: "#d98cff" },
  { id: "rsiDivergence", label: "RSI Divergence", group: "price_action", color: "#55e0ff" },
  { id: "macdDivergence", label: "MACD Divergence", group: "price_action", color: "#ff7ca5" },
];
const SIGNAL_CORE20_MODULES = [
  { id: "sma", group: "technical", label: "SMA", keys: ["sma20", "sma50", "sma200"] },
  { id: "ema", group: "technical", label: "EMA", keys: ["ema9", "ema20", "ema50", "ema200"] },
  { id: "rsi", group: "technical", label: "RSI14", keys: ["rsi14"] },
  { id: "macd", group: "technical", label: "MACD", keys: ["macdLine", "macdSignal", "macdHistogram"] },
  { id: "stochastic", group: "technical", label: "Stochastic", keys: ["stochasticK", "stochasticD"] },
  { id: "atr", group: "technical", label: "ATR14", keys: ["atr14"] },
  { id: "bollinger", group: "technical", label: "Bollinger Bands", keys: ["bollingerMiddle", "bollingerUpper", "bollingerLower"] },
  { id: "adx", group: "technical", label: "ADX / DI", keys: ["adx14", "plusDI14", "minusDI14"] },
  { id: "cci", group: "technical", label: "CCI20", keys: ["cci20"] },
  { id: "williams", group: "technical", label: "Williams %R", keys: ["williamsR14"] },
  { id: "roc", group: "technical", label: "ROC12", keys: ["roc12"] },
  { id: "momentum", group: "technical", label: "Momentum10", keys: ["momentum10"] },
  { id: "obv", group: "technical", label: "OBV", keys: ["obv"] },
  { id: "mfi", group: "technical", label: "MFI14", keys: ["mfi14"] },
  { id: "swings", group: "price_action", label: "Swing High / Low", feature: "swings" },
  { id: "support_resistance", group: "price_action", label: "แนวรับ–แนวต้าน", feature: "supportResistance" },
  { id: "trendlines", group: "price_action", label: "Trendline", feature: "trendlines" },
  { id: "fibonacci", group: "price_action", label: "Fibonacci", feature: "fibonacci" },
  { id: "rsi_divergence", group: "price_action", label: "RSI Divergence", feature: "rsiDivergence" },
  { id: "macd_divergence", group: "price_action", label: "MACD Divergence", feature: "macdDivergence" },
];
const OFFICE_AGENT_OVERLAP_X = 4.2;
const OFFICE_AGENT_OVERLAP_Y = 2.5;
const UI_SESSION_ENDPOINT = "/api/ui-session";
const AGENT_EVENTS_ENDPOINT = "/api/agent-events";
const AGENT_CHAT_ENDPOINT = "/api/agents/chat";
const MEMORY_ENDPOINT = "/api/memory";
const MEMORY_SEARCH_ENDPOINT = "/api/memory/search";
const MEETINGS_ENDPOINT = "/api/meetings";
const CODEX_RATE_LIMIT_ENDPOINT = "/api/codex/rate-limits";
const OPERATOR_MODE_ENDPOINT = "/api/operator-mode";
const AI_TRADE_COUNCIL_DEEP_ANALYSIS_ENDPOINT = "/api/ai-trade-council/deep-analysis";
const AI_TRADE_COUNCIL_DEEP_PACKAGE_ENDPOINT = "/api/ai-trade-council/deep-analysis/package";
const AGENT_COLLABORATION_ENDPOINT = "/api/collaboration/schedule";
const AGENT_COLLABORATION_RUN_ENDPOINT = "/api/collaboration/run-now";
const CODEX_RATE_LIMIT_POLL_MS = 60000;
const CODEX_RATE_LIMIT_FETCH_TIMEOUT_MS = 25000;
const CODEX_RATE_LIMIT_STALE_MAX_MS = 15 * 60 * 1000;
const OPERATOR_MODE_POLL_MS = 30000;
const AGENT_COLLABORATION_POLL_MS = 15000;
const MISSION_POLL_MS = 12000;
const OFFICE_AUTONOMY_MS = 7800;
const ROOM_CONTRACT_PATH = "./contracts/rooms/command-room.json?v=32";
const AGENT_CONTRACT_PATH = "./contracts/agents/agents.json?v=10";
const EXPECTED_OFFICE_AGENT_COUNT = 10;
const DEFAULT_FETCH_TIMEOUT_MS = 6000;

const STATUS_LABELS = {
  queued: "รอเริ่มงาน",
  running: "กำลังทำงาน",
  waiting_approval: "รออนุมัติ",
  blocked: "ติดขัด",
  completed: "เสร็จแล้ว",
  failed: "ไม่สำเร็จ",
  archived: "เก็บเข้าคลังแล้ว",
  ready: "พร้อมใช้งาน",
  shadow: "โหมดตรวจสอบ โดยไม่ส่งคำสั่งซื้อขาย",
  demo_ready: "พร้อมส่งคำสั่งบัญชี Demo",
  live_ready: "พร้อมส่งคำสั่งบัญชีจริง",
  awaiting_ea: "รอเชื่อม EA",
  waiting_snapshot: "รอข้อมูลกราฟรอบใหม่",
  awaiting_snapshot: "รอ Snapshot แรกจาก EA",
  execution_guard_blocked: "ระบบป้องกันของ EA ยังไม่พร้อม",
  active: "กำลังใช้งาน",
  online: "ออนไลน์",
  offline: "ออฟไลน์",
  connected: "เชื่อมต่อแล้ว",
  detected: "ตรวจพบแล้ว",
  configured: "ตั้งค่าแล้ว",
  not_connected: "ยังไม่เชื่อม",
  not_checked: "ยังไม่ได้ตรวจ",
  not_configured: "ยังไม่ได้ตั้งค่า",
  not_found: "ยังไม่พบ",
  needs_attention: "ต้องตรวจสอบ",
  coming_soon: "Coming Soon",
  partial: "เชื่อมต่อบางส่วน",
  manual: "สั่งทำงานเอง",
  ai_every_2h: "AI ตรวจทุก 2 ชั่วโมง",
  enabled: "เปิดใช้งานแล้ว",
  disabled: "ยังไม่เปิดใช้งาน",
  guarded: "มีระบบป้องกัน",
  read_only: "ดูข้อมูลอย่างเดียว",
  analysis_only: "วิเคราะห์ข้อมูลเท่านั้น",
  verified: "มีหลักฐานยืนยันแล้ว",
  workspace_analysis_only: "วิเคราะห์ใน Workspace เท่านั้น",
  codex_workspace_only: "สร้างหรือแก้ไฟล์ใน Workspace เท่านั้น",
  capability_unavailable: "ยังไม่มีตัวเชื่อมสำหรับงานจริง",
  workflow_contract_only_adapter_missing: "มีขั้นตอนงานแล้ว แต่ยังไม่มีตัวเชื่อมโปรแกรม",
  logging: "กำลังบันทึก",
  watching: "กำลังเฝ้าดู",
  monitoring: "กำลังตรวจสอบ",
  stable: "ทำงานปกติ",
  unknown: "ยังไม่ทราบสถานะ",
  empty: "ยังไม่มีข้อมูล",
  property_role: "หน้าที่ของอุปกรณ์",
  display_contract: "ขอบเขตการแสดงผล",
  data_sources: "แหล่งข้อมูล",
  guardrail: "ขอบเขตความปลอดภัย",
  transcript: "บันทึกบทสนทนา",
  finding: "สิ่งที่พบ",
  metric: "ตัวชี้วัด",
  risk: "ความเสี่ยง",
  next_action: "ขั้นตอนถัดไป",
  report: "รายงาน",
  meeting: "การประชุม",
  memory: "Memory",
  available: "พร้อมใช้งาน",
  kanban: "ภาพรวม Task",
  event: "เหตุการณ์",
  success: "สำเร็จ",
  error: "มีข้อผิดพลาด",
  idle: "พร้อมรับงาน",
  working: "กำลังทำงาน",
  auth_required: "ต้อง Login Codex",
  config_error: "Codex Config มีปัญหา",
  timeout: "หมดเวลารอ",
  missing: "ไม่พบระบบที่ต้องใช้",
  unavailable: "ยังไม่พร้อมใช้งาน",
  mock: "โหมด Demo",
  checking: "กำลังตรวจสอบ",
  planning: "กำลังวางแผน",
  config_present: "พบ Config แล้ว",
  implemented_guarded: "เชื่อมระบบแล้วและมีการป้องกัน",
  read_only_diagnostic: "ตรวจข้อมูลแบบไม่แก้ไข",
  auto_guarded: "อัตโนมัติ — Workspace + Web Search",
  manual_guarded: "ตรวจสอบก่อนเริ่มงาน",
  role_default: "ใช้ค่าตามหน้าที่ Agent",
  ai_report: "รายงานจาก AI",
  build_log: "บันทึกการพัฒนา",
  contract: "ข้อตกลงระบบ",
  bridge_status_report: "รายงานสถานะ Bridge",
  archive_report: "รายงานจากคลังงาน",
  vps_report: "รายงานสถานะ VPS",
  backtest_report: "รายงาน Backtest",
  optimization_report: "รายงาน Optimization",
  ea_build_report: "รายงานการพัฒนา EA",
  telegram_alert_report: "รายงาน Telegram",
  risk_review: "รายงานตรวจความเสี่ยง",
  auto_trading_status_report: "รายงานสถานะ Auto Trading",
  ops_overview_report: "รายงานภาพรวม HQ",
};

const CAPABILITY_DISPLAY = {
  codex_cli_task: "งาน Codex จริงแบบมีระบบป้องกัน",
  codex_status: "ตรวจสถานะ Codex",
  mcp_tool_run: "เรียกใช้ MCP Tool แบบมีระบบป้องกัน",
  python_task: "งาน Python ผ่าน Local Runner",
  mt4_task: "งาน MT4 ผ่าน Local Runner",
  mt5_task: "งาน MT5 ผ่าน Local Runner",
  telegram_send: "ส่ง Telegram หลังได้รับอนุมัติ",
};

const DASHBOARD_FIELD_LABELS = {
  diagnosticstatus: "สถานะการตรวจ",
  connectioncount: "จำนวนรายการเชื่อมต่อ",
  readycount: "รายการที่พร้อม",
  comingsooncount: "รายการ Coming Soon",
  mt4installedcount: "MT4 ที่ตรวจพบ",
  mt4runningcount: "MT4 ที่กำลังทำงาน",
  mt5installedcount: "MT5 ที่ตรวจพบ",
  mt5runningcount: "MT5 ที่กำลังทำงาน",
  candidatecount: "จำนวน Terminal ที่พบ",
  usedpercent: "ใช้โควตาแล้ว",
  remainingpercent: "โควตาคงเหลือ",
  windowdurationminutes: "รอบโควตา (นาที)",
  outputchars: "ความยาวผลลัพธ์",
  timeoutseconds: "เวลารอสูงสุด (วินาที)",
  outputlimitchars: "ขีดจำกัดผลลัพธ์",
  secretredacted: "มีการปกปิดข้อมูลลับ",
};

function dashboardFieldLabel(value) {
  const raw = String(value || "").trim();
  const compact = raw.toLowerCase().replace(/[^a-z0-9]/g, "");
  if (DASHBOARD_FIELD_LABELS[compact]) return DASHBOARD_FIELD_LABELS[compact];
  return raw
    .replace(/[_-]+/g, " ")
    .replace(/([a-z0-9])([A-Z])/g, "$1 $2")
    .trim() || "ข้อมูลเพิ่มเติม";
}

function dashboardMetricValue(name, value) {
  const compact = String(name || "").toLowerCase().replace(/[^a-z0-9]/g, "");
  if (compact.endsWith("status") && typeof value === "string") return displayStatus(value);
  if (typeof value === "boolean") return value ? "ใช่" : "ไม่ใช่";
  return formatDashboardValue(value);
}

const RISK_LABELS = {
  low: "ต่ำ",
  medium: "ปานกลาง",
  high: "สูง",
  critical: "สูงมาก",
};

const APPROVAL_LABELS = {
  not_required: "ไม่ต้องขออนุมัติ",
  pending: "กำลังรออนุมัติ",
  requested: "ส่งคำขออนุมัติแล้ว",
  approved: "อนุมัติแล้ว",
  consumed: "อนุมัติและดำเนินการแล้ว",
  rejected: "ไม่อนุมัติ",
  expired: "คำอนุมัติหมดอายุ",
  invalidated: "คำอนุมัติถูกยกเลิก",
};

const AI_TRADE_COUNCIL_PUBLIC_NAMES = Object.freeze({
  optimization_agent: "Technical Consultant",
  backtest_analyst: "Price Action Consultant",
  codex_mcp_operator: "News Consultant",
});

const AI_TRADE_COUNCIL_LEGACY_NAMES = Object.freeze({
  optimization_agent: "Optimization Agent",
  backtest_analyst: "Backtest Analyst",
  codex_mcp_operator: "Codex MCP Operator",
});

const AGENT_DISPLAY = {
  manager: {
    name: "Manager Agent",
    role: "หัวหน้าทีมและผู้แจกงาน",
    summary: "รับเป้าหมายจาก CEO แบ่งเป็น Task ให้ Agent ที่เหมาะสม ติดตามผล และสรุปรายงานกลับมา",
    status: "พร้อมรับคำสั่ง",
  },
  ceo: {
    name: "CEO",
    role: "เจ้าของเป้าหมายและผู้อนุมัติ",
    summary: "กำหนดเป้าหมายธุรกิจ อนุมัติงานที่มีความเสี่ยง และรับรายงานสรุประดับผู้บริหาร",
    status: "กำลังตรวจภาพรวม HQ",
  },
  ea_developer: {
    name: "EA Developer",
    role: "ผู้พัฒนา EA สำหรับ MT4/MT5",
    summary: "เขียน แก้ไข และอธิบาย EA หรือ Indicator สำหรับ MT4/MT5 รวมถึงตรวจผล Compile",
    status: "พร้อมพัฒนา EA",
  },
  backtest_analyst: {
    name: AI_TRADE_COUNCIL_PUBLIC_NAMES.backtest_analyst,
    role: "ที่ปรึกษากราฟเปล่าและ Price Action • สมาชิกสภา AI ชั้นสูง",
    summary: "เชี่ยวชาญกราฟเปล่า โครงสร้างราคา Trendline แนวรับแนวต้าน Liquidity, SMC/HMC/ICT พร้อมอ่านผล Backtest, Equity และ Drawdown",
    status: "พร้อมวิเคราะห์กราฟเปล่าและอธิบายเหตุผล",
  },
  optimization_agent: {
    name: AI_TRADE_COUNCIL_PUBLIC_NAMES.optimization_agent,
    role: "ที่ปรึกษา Technical Analysis และ Indicator • สมาชิกสภา AI ชั้นสูง",
    summary: "เชี่ยวชาญแนวโน้ม โมเมนตัม ความผันผวน และสัญญาณจาก Indicator พร้อมดู Parameter และเตือนความเสี่ยงจาก Overfit",
    status: "พร้อมวิเคราะห์ Technical และอธิบายเหตุผล",
  },
  vps_watch: {
    name: "VPS Watch",
    role: "ผู้ดูแลโครงสร้างพื้นฐาน",
    summary: "ตรวจ Latency, Uptime, CPU/RAM, พื้นที่ดิสก์ และสถานะ Terminal",
    status: "กำลังเฝ้าดู VPS",
  },
  telegram_ops: {
    name: "Telegram Ops",
    role: "ผู้ดูแลการแจ้งเตือน",
    summary: "เตรียมกฎแจ้งเตือนและข้อความสรุป โดยการส่งจริงต้องผ่านการอนุมัติก่อน",
    status: "กำลังเตรียมข้อความแจ้งเตือน",
  },
  risk_guard: {
    name: "Risk Guard",
    role: "ผู้ตรวจความเสี่ยงและการอนุมัติ",
    summary: "ตรวจคำสั่งเสี่ยง การเปิดเผยความลับ งาน Live Trading และเงื่อนไขด้านความปลอดภัย",
    status: "กำลังเฝ้าประตูอนุมัติ",
  },
  codex_mcp_operator: {
    name: AI_TRADE_COUNCIL_PUBLIC_NAMES.codex_mcp_operator,
    role: "ที่ปรึกษาข่าวและบริบทตลาด • สมาชิกสภา AI ชั้นสูง",
    summary: "เชี่ยวชาญข่าวและสถานการณ์ตลาดระยะสั้น กลาง และยาว พร้อมตรวจความพร้อมของ Codex, MCP และ Local Runner โดยไม่เปิดเผยข้อมูลลับ",
    status: "พร้อมวิเคราะห์ข่าวและอธิบายแหล่งข้อมูล",
  },
  mission_archivist: {
    name: "Mission Archivist",
    role: "ผู้ดูแลคลัง Mission และ Memory",
    summary: "ค้น Mission เก่า บันทึกการประชุม และชุดรายงานเพื่อนำกลับมาใช้ในงานใหม่",
    status: "กำลังจัดทำดัชนี Memory",
  },
};

const AGENT_STATUS_PRIORITY = Object.freeze([
  "ceo",
  "manager",
  "ea_developer",
  "backtest_analyst",
  "optimization_agent",
  "vps_watch",
  "telegram_ops",
  "risk_guard",
  "codex_mcp_operator",
  "mission_archivist",
]);

function getAgentStatusPriorityOrder(agents) {
  const priority = new Map(AGENT_STATUS_PRIORITY.map((agentId, index) => [agentId, index]));
  return [...(Array.isArray(agents) ? agents : [])].sort((left, right) => {
    const leftPriority = priority.get(left?.id) ?? Number.MAX_SAFE_INTEGER;
    const rightPriority = priority.get(right?.id) ?? Number.MAX_SAFE_INTEGER;
    return leftPriority - rightPriority;
  });
}

const PROP_DISPLAY = {
  codex_mcp_portal: "เรดาร์ระบบเทรดโลก",
  left_server_racks: "คลังวิจัยระบบเทรด",
  right_server_racks: "โรงงานสร้าง EA และ Indicator",
  left_analytics_console: "สภา AI Trade",
  right_tool_console: "ห้องทดลอง EA",
  mission_strategy_table: "โต๊ะวางแผน Mission",
  terminal_workstation: "EA Development Studio",
  left_audit_crystals: "Indicator Scout",
  left_signal_cube: "ข่าวรายวันและแนวโน้ม Forex",
  right_status_crystals: "สถานะ VPS/HQ และตั้งค่า Agent",
  front_entry_gate: "จุดเข้า Agent",
};

const WORKFLOW_DASHBOARD_PROP_IDS = Object.freeze([
  "codex_mcp_portal",
  "left_server_racks",
  "right_server_racks",
  "right_tool_console",
  "left_audit_crystals",
  "left_signal_cube",
  "terminal_workstation",
  "right_status_crystals",
]);

const WORKFLOW_DASHBOARD_IDENTITIES = Object.freeze({
  codex_mcp_portal: {
    id: "world-radar",
    mark: "R1",
    labelTh: "WORLD RADAR",
    eyebrowTh: "ศูนย์ค้นหาระบบเทรดและ EA ใหม่ทั่วโลก",
    handoffAgentId: "mission_archivist",
  },
  left_server_racks: {
    id: "research-vault",
    mark: "RV",
    labelTh: "RESEARCH VAULT",
    eyebrowTh: "คลังวิจัยเชิงลึกและตรวจหลักฐาน",
    handoffAgentId: "ea_developer",
  },
  right_server_racks: {
    id: "ea-factory",
    mark: "EA",
    labelTh: "EA FACTORY",
    eyebrowTh: "โรงงานสร้าง EA และ Indicator",
    handoffAgentId: "backtest_analyst",
  },
  right_tool_console: {
    id: "experiment-lab",
    mark: "LAB",
    labelTh: "EXPERIMENT LAB",
    eyebrowTh: "ห้องทดลอง Backtest, Optimization และ Discovery",
    handoffAgentId: "manager",
  },
  left_audit_crystals: {
    id: "indicator-scout",
    mark: "IS",
    labelTh: "INDICATOR SCOUT",
    eyebrowTh: "หน่วยค้นหาและตรวจข้อมูล Indicator",
    handoffAgentId: "ea_developer",
  },
  left_signal_cube: {
    id: "market-news-bias",
    mark: "FX",
    labelTh: "MARKET NEWS",
    eyebrowTh: "ศูนย์ข่าวรายวันและแนวโน้ม Forex",
    handoffAgentId: "manager",
  },
  terminal_workstation: {
    id: "ea-dev-desk",
    mark: "DEV",
    labelTh: "EA DEV DESK",
    eyebrowTh: "โต๊ะพัฒนา Source และวางเป้าหมาย EA",
    handoffAgentId: "backtest_analyst",
  },
  right_status_crystals: {
    id: "hq-vps-settings",
    mark: "HQ",
    labelTh: "HQ / VPS",
    eyebrowTh: "ศูนย์สถานะ HQ, VPS และตั้งค่า Agent",
    handoffAgentId: "manager",
  },
});

const WORKFLOW_DASHBOARD_PRIMARY_TABS = Object.freeze({
  codex_mcp_portal: {
    labelTh: "อัปเดตระบบวันนี้",
    descriptionTh: "ค้นหาระบบเทรดใหม่และดูผลที่ Agent ส่งกลับมาวันนี้",
    overviewTitleTh: "ระบบเทรดที่ค้นพบวันนี้",
    emptyMessageTh: "วันนี้ยังไม่มีระบบเทรดใหม่จาก Local Runner",
  },
  left_server_racks: {
    labelTh: "งานวิจัยวันนี้",
    descriptionTh: "ตรวจคิววิจัยหลักและผลตรวจแหล่งอ้างอิงล่าสุด",
    overviewTitleTh: "งานวิจัยเชิงลึกล่าสุด",
    emptyMessageTh: "ยังไม่มีระบบที่ส่งเข้ามาวิจัยเชิงลึก",
  },
  right_server_racks: {
    labelTh: "งานสร้างวันนี้",
    descriptionTh: "เริ่มงานสร้าง EA หรือ Indicator และติดตามไฟล์ที่ส่งกลับมา",
    overviewTitleTh: "EA และ Indicator ที่กำลังสร้าง",
    emptyMessageTh: "ยังไม่มีงานสร้าง EA หรือ Indicator ในวันนี้",
  },
  right_tool_console: {
    labelTh: "งานทดลองวันนี้",
    descriptionTh: "เริ่มแผน Backtest และดูสถานะการทดลองล่าสุด",
    overviewTitleTh: "ผลทดลอง EA ล่าสุด",
    emptyMessageTh: "ยังไม่มีผล Backtest หรือ Optimization ในวันนี้",
  },
  left_audit_crystals: {
    labelTh: "Indicator วันนี้",
    descriptionTh: "ดู Indicator ที่ค้นพบใหม่พร้อมสถานะหลักฐานล่าสุด",
    overviewTitleTh: "Indicator ที่ค้นพบวันนี้",
    emptyMessageTh: "วันนี้ยังไม่มี Indicator ใหม่จาก Local Runner",
  },
  left_signal_cube: {
    labelTh: "ข่าวและ Bias วันนี้",
    descriptionTh: "ดูข่าวสำคัญและมุมมองตลาดที่อัปเดตวันนี้",
    overviewTitleTh: "ข่าวสำคัญและ Bias ล่าสุด",
    emptyMessageTh: "ยังไม่มีข่าวจริงและ Bias ที่ยืนยันจาก Backend",
  },
  terminal_workstation: {
    labelTh: "งานพัฒนาวันนี้",
    descriptionTh: "เลือก Source และติดตามงานพัฒนา EA ล่าสุด",
    overviewTitleTh: "งานพัฒนา EA ล่าสุด",
    emptyMessageTh: "ยังไม่มี Source หรืองานพัฒนา EA ที่พร้อมใช้งาน",
  },
  right_status_crystals: {
    labelTh: "สถานะระบบวันนี้",
    descriptionTh: "ดูความพร้อมของ VPS, HQ และ Local Runner ล่าสุด",
    overviewTitleTh: "สถานะระบบล่าสุด",
    emptyMessageTh: "ยังไม่มีผลตรวจระบบจริงจาก Backend",
  },
});

const WORKFLOW_DASHBOARD_SETTING_ACTION_IDS = new Set([
  "save_discovery_schedule",
  "save_indicator_scout_schedule",
  "save_news_bias_schedule",
  "save_agent_preferences",
]);

const WORKFLOW_DASHBOARD_SETTING_TAB_IDS = new Set(["schedule", "agent_settings"]);

const WORKFLOW_DASHBOARD_HISTORY_TAB_IDS = new Set([
  "evidence",
  "outputs",
  "history",
  "archive",
  "schedule_history",
  "activity_history",
]);

const WORKFLOW_DASHBOARD_PRIMARY_REPORT_TYPES = Object.freeze({
  codex_mcp_portal: ["trading_system_discovery_report", "ea_discovery_report"],
  left_server_racks: ["trading_system_research_report"],
  right_server_racks: ["ea_build_report", "ea_compile_report", "ea_development_report", "code_change_report"],
  right_tool_console: ["ea_experiment_report", "backtest_report", "optimization_report", "ea_discovery_report"],
  left_audit_crystals: ["indicator_scout_report"],
  left_signal_cube: ["fx_news_bias_report"],
  terminal_workstation: ["ea_development_report", "ea_build_report", "ea_compile_report", "code_change_report"],
  right_status_crystals: ["ops_overview_report", "vps_report", "bridge_status_report"],
});

const WORKFLOW_REPORT_TRANSFER_READY_STATUSES = new Set(["ready", "completed", "verified", "published"]);

// Mirrors the Backend allow-list. The browser uses this only to hide invalid choices;
// the Local Runner remains authoritative and validates the report, Mission binding,
// destination action, platform and idempotency key again before recording a transfer.
const WORKFLOW_REPORT_TRANSFER_ROUTES = Object.freeze([
  {
    actionId: "deep_research_system",
    targetPropId: "left_server_racks",
    agentId: "mission_archivist",
    sourcePropIds: ["codex_mcp_portal"],
    reportTypes: ["trading_system_discovery_report", "ea_discovery_report"],
  },
  {
    actionId: "build_strategy_code",
    targetPropId: "right_server_racks",
    agentId: "ea_developer",
    sourcePropIds: ["codex_mcp_portal", "left_server_racks"],
    reportTypes: ["trading_system_discovery_report", "ea_discovery_report", "trading_system_research_report"],
  },
  {
    actionId: "review_source_code",
    targetPropId: "right_server_racks",
    agentId: "ea_developer",
    sourcePropIds: ["right_server_racks"],
    reportTypes: ["ea_build_report", "ea_compile_report"],
  },
  {
    actionId: "prepare_backtest_plan",
    targetPropId: "right_tool_console",
    agentId: "backtest_analyst",
    sourcePropIds: ["right_server_racks"],
    reportTypes: ["ea_build_report", "ea_compile_report"],
  },
  {
    actionId: "prepare_optimization_plan",
    targetPropId: "right_tool_console",
    agentId: "optimization_agent",
    sourcePropIds: ["right_server_racks"],
    reportTypes: ["ea_build_report", "ea_compile_report"],
  },
  {
    actionId: "prepare_ea_discovery_plan",
    targetPropId: "right_tool_console",
    agentId: "ea_developer",
    sourcePropIds: ["codex_mcp_portal", "left_server_racks", "right_server_racks"],
    reportTypes: [
      "trading_system_discovery_report",
      "ea_discovery_report",
      "trading_system_research_report",
      "ea_build_report",
      "ea_compile_report",
    ],
  },
  {
    actionId: "build_fx_pair_bias",
    targetPropId: "left_signal_cube",
    agentId: "codex_mcp_operator",
    sourcePropIds: ["left_signal_cube"],
    reportTypes: ["fx_news_bias_report"],
  },
  {
    actionId: "inspect_ea_source",
    targetPropId: "terminal_workstation",
    agentId: "ea_developer",
    sourcePropIds: ["right_server_racks", "terminal_workstation"],
    reportTypes: ["ea_build_report", "ea_compile_report", "ea_development_report", "code_change_report"],
    platforms: ["mt4", "mt5", "mql4", "mql5"],
  },
  {
    actionId: "develop_ea_source",
    targetPropId: "terminal_workstation",
    agentId: "ea_developer",
    sourcePropIds: ["right_server_racks", "terminal_workstation"],
    reportTypes: ["ea_build_report", "ea_compile_report", "ea_development_report", "code_change_report"],
    platforms: ["mt4", "mt5", "mql4", "mql5"],
  },
  {
    actionId: "propose_ea_performance_improvements",
    targetPropId: "terminal_workstation",
    agentId: "ea_developer",
    sourcePropIds: ["right_server_racks", "terminal_workstation"],
    reportTypes: ["ea_build_report", "ea_compile_report", "ea_development_report", "code_change_report"],
    platforms: ["mt4", "mt5", "mql4", "mql5"],
  },
]);

const FX_BIAS_PAIR_UNIVERSE = Object.freeze([
  "AUDCAD", "AUDCHF", "AUDJPY", "AUDNZD", "AUDUSD",
  "CADCHF", "CADJPY", "CHFJPY",
  "EURAUD", "EURCAD", "EURCHF", "EURGBP", "EURJPY", "EURNZD", "EURUSD",
  "GBPAUD", "GBPCAD", "GBPCHF", "GBPJPY", "GBPNZD", "GBPUSD",
  "NZDCAD", "NZDCHF", "NZDJPY", "NZDUSD",
  "USDCAD", "USDCHF", "USDJPY",
]);

const WORKFLOW_DISCOVERY_SHEET_COLUMNS = Object.freeze([
  "discovery_id",
  "record_type",
  "discovered_at",
  "last_verified_at",
  "system_name",
  "trader_or_author",
  "source_title",
  "source_url",
  "source_published_at",
  "source_country",
  "source_language",
  "market",
  "symbols",
  "timeframe",
  "entry_rules",
  "exit_rules",
  "recovery_or_averaging_rules",
  "stop_loss",
  "take_profit",
  "special_conditions",
  "suitable_for",
  "evidence_status",
  "deduplication_key",
  "research_status",
  "position_sizing",
  "indicators",
  "price_action_concepts",
  "expected_trade_frequency",
  "claimed_performance",
  "verification_status",
  "normalized_source_url",
  "duplicate_status",
  "duplicate_of_discovery_id",
  "risks_and_limitations",
  "application_notes",
  "research_priority",
  "linked_mission_id",
  "linked_report_id",
  "target_platform",
  "license_or_usage_terms",
  "tags",
  "notes",
]);

const WORKFLOW_DISCOVERY_DEDUPLICATION_FIELDS = Object.freeze([
  "source_url",
  "system_name",
  "market",
  "timeframe",
]);

const WORKFLOW_DASHBOARD_FALLBACKS = Object.freeze({
  codex_mcp_portal: {
    titleTh: "เรดาร์ระบบเทรดโลก",
    summaryTh: "ค้นหาระบบเทรดและ EA จากแหล่งข้อมูลสากล ตรวจรายการซ้ำ และเก็บเป็นรายการตั้งต้นสำหรับงานวิจัยต่อ",
    tabs: [
      { id: "systems", labelTh: "ระบบเทรดใหม่", descriptionTh: "ค้นหาแนวคิด กลยุทธ์ และกติกาการเทรดใหม่แบบไม่ซ้ำกับข้อมูลเดิม", actionIds: ["discover_trading_systems"] },
      { id: "ea_updates", labelTh: "EA และเครื่องมือใหม่", descriptionTh: "ติดตาม EA, Indicator และงานวิจัยระบบอัตโนมัติที่เพิ่งเผยแพร่", actionIds: ["discover_ea_updates"] },
      { id: "schedule", labelTh: "เวลาอัปเดตรายวัน", descriptionTh: "บันทึกช่วงเวลาที่ต้องการให้งานค้นหาทำงานเมื่อระบบตั้งเวลาเชื่อมพร้อม", actionIds: ["save_discovery_schedule"] },
      {
        id: "catalog",
        labelTh: "คลังและแบบฟอร์มข้อมูล",
        descriptionTh: "ดูรูปแบบข้อมูลสำหรับจัดเก็บรายการที่ค้นพบ ส่วนการเชื่อม Google Sheets ยังเป็น Coming Soon",
        emptyMessageTh: "แบบฟอร์มข้อมูล: ชื่อระบบ, แหล่งที่มา, ผู้เผยแพร่, ตลาด, Timeframe, Entry, Exit, SL/TP, การแก้ไม้, เงื่อนไขพิเศษ และผู้ที่เหมาะสม • Google Sheets Connector: Coming Soon",
        actionIds: [],
      },
    ],
    actions: [
      {
        id: "discover_trading_systems",
        tabId: "systems",
        labelTh: "เริ่มค้นหาระบบเทรด",
        descriptionTh: "สร้าง Mission ให้ Agent ค้นหา ตรวจแหล่งที่มา และคัดรายการที่ไม่ซ้ำ",
        availability: { status: "configuration_required" },
        formFields: [
          { id: "query", labelTh: "หัวข้อที่ต้องการค้นหา", type: "textarea", required: true },
          { id: "market", labelTh: "ตลาด", type: "select", required: true, options: ["Forex", "Gold", "Indices", "Crypto", "Multi-asset"] },
          { id: "timeframe", labelTh: "กรอบเวลาที่สนใจ", type: "select", required: false, options: ["ไม่จำกัด", "M5-M30", "H1-H4", "D1 ขึ้นไป"] },
        ],
      },
      {
        id: "discover_ea_updates",
        tabId: "ea_updates",
        labelTh: "ค้นหา EA และเครื่องมือใหม่",
        descriptionTh: "สร้าง Mission สำหรับติดตาม EA, Indicator และแนวคิดระบบอัตโนมัติจากแหล่งข้อมูลสากล",
        availability: { status: "configuration_required" },
        formFields: [
          { id: "query", labelTh: "โจทย์หรือหัวข้อ", type: "textarea", required: true },
          { id: "platform", labelTh: "แพลตฟอร์ม", type: "select", required: true, options: ["MT4", "MT5", "TradingView", "ไม่จำกัด"] },
        ],
      },
      {
        id: "save_discovery_schedule",
        tabId: "schedule",
        labelTh: "บันทึกเวลาค้นหารายวัน",
        descriptionTh: "บันทึกความต้องการไว้ที่ Local Runner การทำงานอัตโนมัติจะเริ่มเมื่อ Scheduler ฝั่งหลังบ้านพร้อมเท่านั้น",
        availability: { status: "ready" },
        formFields: [
          { id: "enabled", labelTh: "เปิดใช้ตารางเวลาเมื่อระบบพร้อม", type: "checkbox", required: false },
          { id: "times", labelTh: "เวลาที่ต้องการ เช่น 08:00, 18:00", type: "list", required: true },
          { id: "timezone", labelTh: "เขตเวลา", type: "select", required: true, options: ["Asia/Bangkok", "UTC"] },
        ],
      },
    ],
  },
  left_server_racks: {
    titleTh: "คลังวิจัยระบบเทรด",
    summaryTh: "รับระบบที่เลือกจากเรดาร์มาขยายกติกา ตรวจความน่าเชื่อถือ และสรุปแนวทางประยุกต์ใช้พร้อมหลักฐาน",
    tabs: [
      { id: "research_queue", labelTh: "คิววิจัยเชิงลึก", descriptionTh: "เลือกรายงานตั้งต้นแล้วส่งให้ Agent ตรวจรายละเอียดและแหล่งอ้างอิง", actionIds: ["deep_research_system"] },
      { id: "verified_archive", labelTh: "คลังที่ตรวจสอบแล้ว", descriptionTh: "เปิดรายงานฉบับเต็มของระบบที่วิจัยและตรวจหลักฐานแล้ว", actionIds: [] },
      { id: "application", labelTh: "แนวทางประยุกต์ใช้", descriptionTh: "ดูข้อสรุปว่าระบบเหมาะกับตลาด กรอบเวลา และผู้ใช้งานแบบใด", actionIds: [] },
      { id: "evidence", labelTh: "หลักฐานและแหล่งอ้างอิง", descriptionTh: "รวมแหล่งข้อมูลและหลักฐานที่ Agent ตรวจสอบแล้วเพื่อเปิดดูย้อนหลัง", actionIds: [] },
    ],
    actions: [
      {
        id: "deep_research_system",
        tabId: "research_queue",
        labelTh: "ส่งเข้าวิจัยเชิงลึก",
        descriptionTh: "Agent จะตรวจ Entry, Exit, SL/TP, การแก้ไม้ เงื่อนไขพิเศษ ตลาด กรอบเวลา และความเหมาะสม",
        sourceRequired: true,
        availability: { status: "configuration_required" },
        formFields: [
          { id: "sourceReportId", labelTh: "ระบบต้นทางจากเรดาร์", type: "source", required: true },
          { id: "brief", labelTh: "ประเด็นที่ต้องการให้เน้น", type: "textarea", required: false },
        ],
      },
    ],
  },
  right_server_racks: {
    titleTh: "โรงงานสร้าง EA และ Indicator",
    summaryTh: "นำงานค้นพบหรืองานวิจัยมาแปลงเป็น MQL4, MQL5 หรือ Pine Script พร้อมตรวจโค้ดและรายงานตำแหน่งไฟล์",
    tabs: [
      { id: "builder", labelTh: "สร้าง EA / Indicator", descriptionTh: "เลือกต้นแบบ แพลตฟอร์ม และข้อกำหนดก่อนสร้าง Mission", actionIds: ["build_strategy_code"] },
      { id: "code_review", labelTh: "ตรวจ Source Code", descriptionTh: "ตรวจความครบถ้วนและข้อผิดพลาดเชิงโครงสร้างของ Source Code", actionIds: ["review_source_code"] },
      {
        id: "compile",
        labelTh: "Compile (Coming Soon)",
        descriptionTh: "ดูสถานะและหลักฐานจาก Local Runner เท่านั้น ขณะนี้ MetaEditor/Compiler Adapter ยังเป็น Coming Soon",
        emptyMessageTh: "ยังไม่มีผล Compile ที่ยืนยันได้ • MetaEditor/Compiler Adapter: Coming Soon • ระบบจะไม่แสดงว่าผ่านจนกว่าจะมีหลักฐานจาก Local Runner",
        actionIds: [],
      },
      { id: "outputs", labelTh: "ไฟล์ผลลัพธ์", descriptionTh: "ดูรายงานที่เสร็จแล้วและตำแหน่งไฟล์ที่ Local Runner ส่งกลับมา", actionIds: [] },
    ],
    actions: [
      {
        id: "build_strategy_code",
        tabId: "builder",
        labelTh: "สร้าง Mission เขียนระบบ",
        descriptionTh: "ส่งข้อกำหนดให้ EA Developer สร้างไฟล์ใน Workspace โดยไม่ส่งข้อมูลลับมาที่หน้าเว็บ",
        sourceRequired: true,
        availability: { status: "configuration_required" },
        formFields: [
          { id: "sourceReportId", labelTh: "ระบบต้นทาง", type: "source", required: true },
          { id: "platform", labelTh: "แพลตฟอร์ม", type: "select", required: true, options: ["MT4 / MQL4", "MT5 / MQL5", "TradingView / Pine Script"] },
          { id: "brief", labelTh: "ข้อกำหนดเพิ่มเติม", type: "textarea", required: false },
        ],
      },
      {
        id: "review_source_code",
        tabId: "code_review",
        labelTh: "ตรวจ Source Code",
        descriptionTh: "สร้าง Mission ตรวจโครงสร้างและความพร้อมของไฟล์ โดยไม่อ้างว่า Compile สำเร็จ; MetaEditor/Compiler Adapter ยังเป็น Coming Soon",
        sourceRequired: true,
        availability: { status: "configuration_required" },
        formFields: [
          { id: "sourceReportId", labelTh: "ไฟล์หรืองานสร้างที่ต้องการตรวจ", type: "source", required: true },
          { id: "brief", labelTh: "สิ่งที่ต้องการตรวจเพิ่ม", type: "textarea", required: false },
        ],
      },
    ],
  },
  right_tool_console: {
    titleTh: "ห้องทดลอง EA",
    summaryTh: "เตรียมแผน Backtest, Optimization และ EA Discovery จากไฟล์หรืองานวิจัยที่เลือก พร้อมรายงานผลกลับมาเป็นขั้นตอน",
    tabs: [
      { id: "backtest", labelTh: "Auto Backtest", descriptionTh: "กำหนดระบบ ตลาด และกรอบเวลาก่อนส่งแผนทดสอบ", actionIds: ["prepare_backtest_plan"] },
      { id: "optimization", labelTh: "Auto Optimization", descriptionTh: "กำหนดเป้าหมายและข้อจำกัดเพื่อเตรียมแผนหาค่าที่เหมาะสม", actionIds: ["prepare_optimization_plan"] },
      { id: "ea_discovery", labelTh: "EA Discovery", descriptionTh: "ใช้ระบบต้นแบบและเป้าหมายผลลัพธ์เป็นโจทย์สร้างแผนค้นหา EA", actionIds: ["prepare_ea_discovery_plan"] },
      { id: "history", labelTh: "ประวัติการทดลอง", descriptionTh: "ดู Mission และรายงาน Backtest, Optimization และ EA Discovery ที่เคยส่งกลับมา", actionIds: [] },
    ],
    actions: [
      {
        id: "prepare_backtest_plan",
        tabId: "backtest",
        labelTh: "เตรียมแผน Auto Backtest",
        descriptionTh: "สร้าง Mission วางแผนการทดสอบก่อนเชื่อม Adapter ของ MetaTrader",
        sourceRequired: true,
        availability: { status: "configuration_required" },
        formFields: [
          { id: "sourceReportId", labelTh: "EA หรือระบบต้นทาง", type: "source", required: true },
          { id: "platform", labelTh: "แพลตฟอร์ม", type: "select", required: true, options: ["MT4", "MT5"] },
          { id: "market", labelTh: "คู่เงินหรือสัญลักษณ์", type: "text", required: true },
          { id: "timeframe", labelTh: "กรอบเวลา", type: "select", required: true, options: ["M5", "M15", "M30", "H1", "H4", "D1"] },
        ],
      },
      {
        id: "prepare_optimization_plan",
        tabId: "optimization",
        labelTh: "เตรียมแผน Auto Optimization",
        descriptionTh: "สร้าง Mission วางช่วงค่า เป้าหมาย และหลักเกณฑ์กัน Overfit ก่อนรันจริง",
        sourceRequired: true,
        availability: { status: "configuration_required" },
        formFields: [
          { id: "sourceReportId", labelTh: "EA ต้นทาง", type: "source", required: true },
          { id: "platform", labelTh: "แพลตฟอร์ม", type: "select", required: true, options: ["MT4", "MT5"] },
          { id: "targetProfitPercent", labelTh: "เป้าหมายกำไร (%)", type: "number", required: false },
          { id: "maxDrawdownPercent", labelTh: "Drawdown สูงสุด (%)", type: "number", required: true },
        ],
      },
      {
        id: "prepare_ea_discovery_plan",
        tabId: "ea_discovery",
        labelTh: "เตรียมแผน EA Discovery",
        descriptionTh: "สร้าง Mission จากระบบแรงบันดาลใจ พร้อมเป้าหมายกำไร Drawdown และจำนวนการเทรด",
        sourceRequired: true,
        availability: { status: "configuration_required" },
        formFields: [
          { id: "sourceReportId", labelTh: "ระบบแรงบันดาลใจ", type: "source", required: true },
          { id: "platform", labelTh: "แพลตฟอร์ม", type: "select", required: true, options: ["MT4", "MT5"] },
          { id: "targetProfitPercent", labelTh: "เป้าหมายกำไร (%)", type: "number", required: true },
          { id: "maxDrawdownPercent", labelTh: "Drawdown สูงสุด (%)", type: "number", required: true },
          { id: "targetTrades", labelTh: "จำนวนการเทรดเป้าหมาย", type: "number", required: false },
        ],
      },
    ],
  },
  left_audit_crystals: {
    titleTh: "Indicator Scout",
    summaryTh: "ค้นหา Indicator ใหม่จากแหล่งสาธารณะ เก็บ URL วันที่ และผลตรวจรายการซ้ำ โดยยังไม่ดาวน์โหลดหรือติดตั้งไฟล์อัตโนมัติ",
    tabs: [
      { id: "discoveries", labelTh: "Indicator ที่ค้นพบ", descriptionTh: "ดูรายการใหม่ แหล่งต้นทาง วันที่ค้นพบ และสถานะตรวจซ้ำ", actionIds: ["discover_new_indicators"] },
      {
        id: "evidence",
        labelTh: "ภาพและหลักฐาน",
        descriptionTh: "เปิด URL และหลักฐานที่ Backend ตรวจแล้ว ส่วน Screenshot Adapter ยังเป็น Coming Soon",
        emptyMessageTh: "แสดงเฉพาะ URL และหลักฐานจาก Backend • Screenshot Adapter: Coming Soon • ไม่มีภาพจำลอง",
        actionIds: [],
      },
      { id: "schedule", labelTh: "รอบค้นหารายวัน", descriptionTh: "บันทึกเวลาที่ต้องการไว้ โดยจะไม่อ้างว่ารันอัตโนมัติจนกว่า Scheduler พร้อม", actionIds: ["save_indicator_scout_schedule"] },
      { id: "archive", labelTh: "คลังย้อนหลัง", descriptionTh: "ดู Mission และรายงาน Indicator ที่เคยส่งกลับมาที่อุปกรณ์นี้", actionIds: [] },
    ],
    actions: [
      {
        id: "discover_new_indicators",
        tabId: "discoveries",
        labelTh: "ค้นหา Indicator ใหม่",
        descriptionTh: "สร้าง Mission ค้นข้อมูลสาธารณะแบบอ่านอย่างเดียว พร้อม URL วันที่ และการตรวจรายการซ้ำ",
        availability: { status: "configuration_required" },
        formFields: [
          { id: "query", labelTh: "หัวข้อหรือ Indicator ที่สนใจ", type: "textarea", required: true },
          { id: "platform", labelTh: "แพลตฟอร์ม", type: "select", required: true, options: ["MT4", "MT5", "TradingView", "ไม่จำกัด"] },
          { id: "categories", labelTh: "หมวดที่สนใจ", type: "list", required: false, placeholderTh: "Trend, Momentum, Volume, Price Action" },
        ],
      },
      {
        id: "save_indicator_scout_schedule",
        tabId: "schedule",
        labelTh: "บันทึกรอบค้นหา",
        descriptionTh: "ส่ง Intent บันทึกเวลาเท่านั้น งานอัตโนมัติจะเริ่มเมื่อ Backend Scheduler รายงานว่าพร้อม",
        availability: { status: "configuration_required" },
        formFields: [
          { id: "enabled", labelTh: "เปิดใช้เมื่อ Scheduler พร้อม", type: "checkbox", required: false },
          { id: "times", labelTh: "เวลาที่ต้องการ เช่น 08:00, 18:00", type: "list", required: true },
          { id: "timezone", labelTh: "เขตเวลา", type: "select", required: true, options: ["Asia/Bangkok", "UTC"] },
        ],
      },
    ],
  },
  left_signal_cube: {
    titleTh: "ข่าวรายวันและแนวโน้ม Forex",
    summaryTh: "สรุปข่าวผลกระทบสูง ช่วงเวลาที่ EA ควรระวัง และแนวโน้มคู่เงิน 28 คู่จากข้อมูลจริงที่ Backend ส่งมาเท่านั้น",
    tabs: [
      { id: "today", labelTh: "ข่าวสำคัญวันนี้", descriptionTh: "ข่าวผลกระทบสูงและช่วงเวลาที่ EA ควรระวัง พร้อมลิงก์แหล่งข้อมูล", actionIds: ["analyze_daily_market_news"] },
      { id: "pair_bias", labelTh: "แนวโน้ม 28 คู่เงิน", descriptionTh: "ดู Bullish, Bearish หรือ Sideway ของคู่เงินมาตรฐาน 28 คู่ โดยไม่เติมข้อมูลจำลอง", actionIds: ["build_fx_pair_bias"] },
      { id: "horizons", labelTh: "มุมมองสั้น กลาง ยาว", descriptionTh: "เปรียบเทียบแนวโน้มระยะสั้น ระยะกลาง และระยะยาวจากข้อมูลที่มีหลักฐาน", actionIds: [] },
      { id: "schedule_history", labelTh: "เวลาอัปเดตและย้อนหลัง", descriptionTh: "บันทึกเวลาที่ต้องการและเปิดรายงานข่าวหรือ FX Bias ย้อนหลัง", actionIds: ["save_news_bias_schedule"] },
    ],
    actions: [
      {
        id: "analyze_daily_market_news",
        tabId: "today",
        labelTh: "วิเคราะห์ข่าวตลาดวันนี้",
        descriptionTh: "สร้าง Mission อ่านข่าวจากแหล่งสาธารณะและสรุปช่วงอันตรายสำหรับ EA โดยไม่ส่งคำสั่งเทรด",
        availability: { status: "configuration_required" },
        formFields: [
          { id: "currencies", labelTh: "สกุลเงินที่ต้องการเน้น", type: "list", required: false, placeholderTh: "USD, EUR, GBP, JPY" },
          { id: "brief", labelTh: "ประเด็นที่ต้องการให้เน้น", type: "textarea", required: false },
        ],
      },
      {
        id: "build_fx_pair_bias",
        tabId: "pair_bias",
        labelTh: "สร้างตารางแนวโน้ม 28 คู่เงิน",
        descriptionTh: "สร้าง Mission ประเมินแนวโน้มจากข่าวและหลักฐานล่าสุด ผลลัพธ์ที่ไม่มีข้อมูลจะคงสถานะรอข้อมูล",
        availability: { status: "configuration_required" },
        formFields: [
          { id: "horizon", labelTh: "ระยะที่ต้องการเน้น", type: "select", required: true, options: ["สั้น", "กลาง", "ยาว", "ครบทุกระยะ"] },
          { id: "brief", labelTh: "เงื่อนไขเพิ่มเติม", type: "textarea", required: false },
        ],
      },
      {
        id: "save_news_bias_schedule",
        tabId: "schedule_history",
        labelTh: "บันทึกเวลาอัปเดตข่าว",
        descriptionTh: "ส่ง Intent บันทึกเวลาเท่านั้น ไม่สร้างข่าวหรือค่า Bias จำลองเมื่อแหล่งข้อมูลยังไม่พร้อม",
        availability: { status: "configuration_required" },
        formFields: [
          { id: "enabled", labelTh: "เปิดใช้เมื่อ Scheduler พร้อม", type: "checkbox", required: false },
          { id: "times", labelTh: "เวลาที่ต้องการ เช่น 07:00, 13:00, 19:00", type: "list", required: true },
          { id: "timezone", labelTh: "เขตเวลา", type: "select", required: true, options: ["Asia/Bangkok", "UTC"] },
        ],
      },
    ],
  },
  terminal_workstation: {
    titleTh: "EA Development Studio",
    summaryTh: "เลือก Source ที่ Backend อนุญาต สร้าง Brief ด้วยข้อความหรือไมโครโฟน และติดตามไฟล์ผลลัพธ์โดยไม่ส่ง Path หรือข้อมูลลับจาก Frontend",
    tabs: [
      { id: "source", labelTh: "เลือก Source", descriptionTh: "เลือกเฉพาะรายงานหรือไฟล์ Workspace ที่ Backend ส่งมาในรายการที่เชื่อถือได้", actionIds: ["inspect_ea_source"] },
      { id: "development_brief", labelTh: "โจทย์พัฒนา EA", descriptionTh: "เขียนหรือพูดโจทย์สำหรับ MQL4, MQL5 หรือ Pine Script แล้วส่งเป็น Intent", actionIds: ["develop_ea_source"] },
      { id: "performance_goals", labelTh: "เป้าหมายและไอเดีย", descriptionTh: "กำหนดเป้าหมายเชิงทดลองเพื่อให้ Agent เสนอแนวทางปรับปรุง โดยไม่รับประกันผลกำไร", actionIds: ["propose_ea_performance_improvements"] },
      { id: "outputs", labelTh: "ผลงาน ดาวน์โหลด และย้อนหลัง", descriptionTh: "เปิดรายงานและดาวน์โหลดเฉพาะ Artifact ที่ Backend ยืนยันและให้ลิงก์แบบปลอดภัย", actionIds: [] },
    ],
    actions: [
      {
        id: "inspect_ea_source",
        tabId: "source",
        labelTh: "ตรวจ Source ที่เลือก",
        descriptionTh: "สร้าง Mission ตรวจข้อมูลจากรายการต้นทางที่ Backend อนุญาตเท่านั้น ไม่รับ Path จากการพิมพ์เอง",
        sourceRequired: true,
        availability: { status: "configuration_required" },
        formFields: [
          { id: "sourceReportId", labelTh: "Source จาก Workspace หรือรายงานต้นทาง", type: "source", required: true },
          { id: "platform", labelTh: "แพลตฟอร์ม", type: "select", required: true, options: ["MT4 / MQL4", "MT5 / MQL5", "TradingView / Pine Script"] },
        ],
      },
      {
        id: "develop_ea_source",
        tabId: "development_brief",
        labelTh: "ส่งโจทย์พัฒนา",
        descriptionTh: "ส่ง Brief ไปยัง Local Runner เพื่อสร้าง Mission; ไมโครโฟนใช้แปลงเสียงเป็นข้อความในเบราว์เซอร์เท่านั้น",
        sourceRequired: true,
        availability: { status: "configuration_required" },
        formFields: [
          { id: "sourceReportId", labelTh: "Source ที่เชื่อถือได้", type: "source", required: true },
          { id: "platform", labelTh: "แพลตฟอร์ม", type: "select", required: true, options: ["MT4 / MQL4", "MT5 / MQL5", "TradingView / Pine Script"] },
          { id: "brief", labelTh: "โจทย์การพัฒนา", type: "textarea", required: true, voiceDictation: true, placeholderTh: "อธิบาย Entry, Exit, SL/TP, Money Management และเงื่อนไขพิเศษ" },
        ],
      },
      {
        id: "propose_ea_performance_improvements",
        tabId: "performance_goals",
        labelTh: "ขอแนวทางปรับปรุง EA",
        descriptionTh: "ให้ Agent เสนอแนวคิดและแผนทดสอบตามเป้าหมาย โดยยังไม่อ้างผล Backtest หรือ Optimization ที่ไม่ได้รันจริง",
        sourceRequired: true,
        availability: { status: "configuration_required" },
        formFields: [
          { id: "sourceReportId", labelTh: "EA หรือระบบต้นทาง", type: "source", required: true },
          { id: "targetProfitPercent", labelTh: "เป้าหมายกำไรเพื่อการทดลอง (%)", type: "number", required: false },
          { id: "maxDrawdownPercent", labelTh: "Drawdown สูงสุดที่ต้องการ (%)", type: "number", required: false },
          { id: "minimumTrades", labelTh: "จำนวน Trade ขั้นต่ำสำหรับการประเมิน", type: "number", required: false },
          { id: "brief", labelTh: "ไอเดียหรือข้อจำกัดเพิ่มเติม", type: "textarea", required: false, voiceDictation: true },
        ],
      },
    ],
  },
  right_status_crystals: {
    titleTh: "สถานะ VPS/HQ และตั้งค่า Agent",
    summaryTh: "ดูข้อมูล VPS, Bridge และคิวงานจาก Backend พร้อมตั้งค่าการแสดงผลของ Agent ที่ปลอดภัย โดยไม่รับ Secret หรือสิทธิ์ระบบจากหน้าเว็บ",
    tabs: [
      { id: "vps", labelTh: "สถานะ VPS", descriptionTh: "ดู Uptime, Latency, CPU และ RAM เฉพาะค่าที่ Backend ตรวจพบจริง", actionIds: ["refresh_vps_hq_status"] },
      { id: "hq_bridge", labelTh: "HQ และ Bridge", descriptionTh: "ดูสถานะ Local Runner, Codex และคิวงาน โดยไม่แสดง Process ID หรือข้อมูลลับ", actionIds: [] },
      { id: "agent_settings", labelTh: "ตั้งค่า Agent แบบปลอดภัย", descriptionTh: "ตั้งภาษา ระดับการประมวลผล งบงาน เวลา และขนาดรายงาน โดยไม่รับ Provider Model ID, สิทธิ์ Tool หรือ Credential", actionIds: ["save_agent_preferences"] },
      { id: "activity_history", labelTh: "ประวัติการเปลี่ยนแปลง", descriptionTh: "เปิด Mission รายงาน และเหตุการณ์ตั้งค่าที่ Backend ส่งกลับมา", actionIds: [] },
    ],
    actions: [
      {
        id: "refresh_vps_hq_status",
        tabId: "vps",
        labelTh: "ขอตรวจสถานะใหม่",
        descriptionTh: "ส่ง Intent ให้ Local Runner ตรวจสถานะที่อนุญาต ไม่สั่ง Restart, Deploy หรือแก้เครื่อง",
        availability: { status: "configuration_required" },
        formFields: [
          { id: "scope", labelTh: "ขอบเขตที่ต้องการตรวจ", type: "select", required: true, options: ["VPS", "HQ / Bridge", "ทั้งหมด"] },
        ],
      },
      {
        id: "save_agent_preferences",
        tabId: "agent_settings",
        labelTh: "บันทึกการตั้งค่า Agent",
        descriptionTh: "บันทึกเฉพาะระดับโมเดลและขอบเขตการใช้งานที่ Backend อนุญาต ไม่รับ Provider Model ID, Password, API Key หรือการเปลี่ยนสิทธิ์ Tool",
        availability: { status: "configuration_required" },
        formFields: [
          { id: "language", labelTh: "ภาษาหลัก", type: "select", required: false, options: ["th", "en"] },
          { id: "modelTier", labelTh: "ระดับโมเดล", type: "select", required: false, options: ["manager_quality", "risk_quality", "specialist_balanced", "specialist_fast"] },
          { id: "tokenBudget", labelTh: "งบ Token ต่อภารกิจ", type: "integer", required: false },
          { id: "timeoutSeconds", labelTh: "เวลาสูงสุดต่อภารกิจ (วินาที)", type: "integer", required: false },
          { id: "outputLimitChars", labelTh: "ขนาดผลลัพธ์สูงสุด (ตัวอักษร)", type: "integer", required: false },
          { id: "rateReservePercent", labelTh: "Rate Limit สำรอง (%)", type: "integer", required: false },
        ],
      },
    ],
  },
});

const WORKFLOW_FIELD_DENY_PATTERN = /(secret|password|cookie|credential|auth|api[_-]?key|(?:provider[_-]?)?model[_-]?id|tool(?:[_-]?(?:id|permission|access))?|token(?!budget))/i;

const WORKFLOW_NUMERIC_FIELD_BOUNDS = Object.freeze({
  tokenBudget: { min: 256, max: 100000, step: 1 },
  timeoutSeconds: { min: 15, max: 1800, step: 1 },
  outputLimitChars: { min: 1000, max: 100000, step: 1 },
  rateReservePercent: { min: 0, max: 90, step: 1 },
});

const LAYER_DISPLAY = {
  background: ["ฉากหลัง", "ฉากปราสาทและพื้นที่ด้านนอก"],
  floor: ["พื้นสำหรับเดิน", "พื้นที่เดิน ประชุม และวางตำแหน่ง Agent"],
  walls_back: ["กำแพงปราสาท", "กำแพง ป้าย และโครงสร้างรอบห้อง"],
  server_bridge: ["โซน Server และ Bridge", "ประตูกลางและตู้ Server"],
  workstations: ["จุดทำงาน", "โต๊ะ Mission จอวิเคราะห์ และ Tool Console"],
  fx_nodes: ["จุดสัญญาณ", "คริสตัล ไฟคิว และจุดตรวจความเสี่ยง"],
  ui_overlay: ["เลเยอร์อุปกรณ์ที่กดได้", "อุปกรณ์โปร่งใสที่วางตรงกับฉากเดิม"],
};

function displayStatus(value) {
  const normalized = String(value || "unknown").trim().toLowerCase().replace(/[ -]+/g, "_");
  return STATUS_LABELS[normalized] || String(value || STATUS_LABELS.unknown);
}

function displayRisk(value) {
  const normalized = String(value || "low").trim().toLowerCase();
  return RISK_LABELS[normalized] || String(value || RISK_LABELS.low);
}

function displayApproval(value) {
  const normalized = String(value || "not_required").trim().toLowerCase();
  return APPROVAL_LABELS[normalized] || String(value || APPROVAL_LABELS.not_required);
}

function displayAgentName(value, fallback = "Agent") {
  const id = String(value || "").trim().toLowerCase();
  const matchedId = AGENT_DISPLAY[id] ? id : getAgentIdFromOwner(value);
  return AGENT_DISPLAY[matchedId]?.name || getOfficeAgent(matchedId || id)?.name || value || fallback;
}

function displayPropName(id, fallback = "จุดแสดงผล") {
  return PROP_DISPLAY[id] || fallback || id;
}

function displayBridgeValue(value) {
  const text = String(value || "").trim();
  const normalized = text.toLowerCase().replace(/[ -]+/g, "_");
  const known = {
    codex_runner_ready: "Codex Runner พร้อมใช้งาน",
    runner_ready: "Runner พร้อมใช้งาน",
    bridge_not_checked: "ยังไม่ได้ตรวจ Bridge",
    backend_offline: "Backend ออฟไลน์",
    guarded_request_rejected: "คำขอถูกหยุดโดยระบบป้องกัน",
    runner_blocked: "Runner ถูกหยุดไว้",
    submitting_approved_mission: "กำลังส่ง Mission ที่อนุมัติแล้ว",
  };
  return known[normalized] || STATUS_LABELS[normalized] || text || "ยังไม่ทราบสถานะ";
}

function formatThaiDateTime(value, fallback = "ยังไม่มีเวลาอัปเดต") {
  const date = value ? new Date(value) : null;
  if (!date || Number.isNaN(date.getTime())) return fallback;
  return date.toLocaleString("th-TH", { dateStyle: "medium", timeStyle: "short" });
}

function formatBrokerBarTime(value, fallback = "ยังไม่มีข้อมูลแท่ง") {
  const numeric = Number(value);
  const normalized = Number.isFinite(numeric) && numeric > 0 && numeric < 100_000_000_000
    ? numeric * 1000
    : value;
  return formatThaiDateTime(normalized, fallback);
}

function reportBootResourceFailure(failedResource, error, { blocking = false } = {}) {
  const detail = error?.name === "AbortError"
    ? `โหลด ${failedResource} ไม่สำเร็จภายในเวลาที่กำหนด`
    : (error?.message || `ไม่สามารถโหลด ${failedResource} ได้`);
  window.MetafxHqBoot?.reportFailure({ failedResource, detail, blocking });
  console.warn(`[Visual Office boot] ${failedResource}`, error);
}

function createFallbackRoomData() {
  return {
    room: {
      id: "codex_mcp_agent_workroom_fallback",
      name: "ห้องทำงาน Codex/MCP Agent",
      version: "frontend-fallback-v001",
      image: `${PROJECT_ASSET_ROOT}/maps/command-room/metafx-aihq-room-codex-mcp-agent-workroom-wide-symmetric-v002.png`,
    },
    navigation: {
      maskMode: "fallback",
      blockerMode: "mask-only",
      blockers: [],
      grid: { columns: 72, rows: 40 },
    },
    layers: [],
    hotspots: [],
    props: [],
    defaultSelection: null,
  };
}

const state = {
  data: null,
  agentRoster: [],
  activeObject: null,
  panelObject: null,
  selectedAgentId: "manager",
  visibleLayers: new Set(),
  fitMode: "contain",
  restoredSession: null,
  bridgeEvents: [],
  officeAgents: [],
  officeEventLog: [],
  meetingTranscript: [],
  memoryCards: [],
  meetingRecords: [],
  memoryStatus: "ยังไม่ได้ตรวจ Memory",
  taskDetailMissionId: null,
  taskDetailSource: null,
  modal: {
    open: false,
    type: null,
    id: null,
    activeTab: "chat",
    signalTab: "daily_summary",
    signalLiveTab: "chart_overview",
    signalChartDisplayBars: SIGNAL_CHART_DEFAULT_DISPLAY_BARS,
    signalChartOffsetBars: 0,
    signalChartOverlays: [...SIGNAL_CHART_DEFAULT_OVERLAYS],
    signalOverlayPickerOpen: false,
    signalIndicatorFilter: "all",
    signalDeepTechnicalQuery: "",
    signalDeepTechnicalIndicator: "all",
    signalDeepTechnicalRange: "300",
    signalHistoryQuery: "",
    signalHistoryType: "all",
    signalHistoryStatus: "all",
    workflowTabs: {},
    workflowAction: {
      inFlight: false,
      propId: null,
      actionId: null,
      idempotencyKey: "",
      formSignature: "",
      message: "",
      tone: "neutral",
    },
    workflowHandoff: {
      inFlight: false,
      propId: null,
      reportId: "",
      targetPropId: "",
      actionId: "",
      idempotencyKey: "",
      formSignature: "",
      message: "",
      tone: "neutral",
    },
    workflowVoice: {
      status: "idle",
      propId: null,
      actionId: null,
      fieldId: null,
      message: "",
      recognition: null,
    },
    lastPrompt: "",
    selectedMissionId: null,
    showArchived: false,
    searchText: "",
    kanbanScrollTop: {},
    pendingRun: null,
    runInFlight: false,
    approvalInFlight: false,
    executionInFlight: false,
  },
  chatLog: [],
  agentChat: {
    inFlight: false,
    agentId: null,
    sessionIds: {},
    message: "พร้อมคุยกับ Codex ผ่าน Local Runner",
    tone: "neutral",
  },
  lastAutonomyMeetingAt: 0,
  agentRouteIndex: 0,
  agentMoveTimer: null,
  agentMoveFrame: null,
  agentSpriteTimer: null,
  officeAutonomyTimer: null,
  codexRate: {
    status: "loading",
    snapshot: null,
    lastGood: null,
    inFlight: false,
    timer: null,
    visibilityHandlerBound: false,
  },
  operatorMode: {
    mode: "unknown",
    labelTh: "กำลังตรวจสอบ Backend...",
    autoExecute: false,
    backendAvailable: false,
    fallback: false,
    guardrails: {
      autoEligibleTools: [],
      maxRisk: null,
      alwaysRequireHumanApprovalFor: [],
    },
    updatedAt: null,
    inFlight: false,
    timer: null,
    visibilityHandlerBound: false,
  },
  agentCollaboration: {
    status: "loading",
    enabled: false,
    topic: "",
    timezone: "Asia/Bangkok",
    startTime: "09:00",
    endTime: "18:00",
    intervalMinutes: 120,
    maxTurns: 3,
    maxDailyRuns: 3,
    dailyRunCount: 0,
    minRemainingPercent: 30,
    participants: [],
    nextRunAt: null,
    pausedReason: null,
    messageTh: "กำลังตรวจสอบตารางประชุม",
    activeMeetingId: null,
    activeMissionId: null,
    lastMeetingId: null,
    backendAvailable: false,
    editing: false,
    inFlight: false,
    timer: null,
    visibilityHandlerBound: false,
    lastVisualMeetingId: null,
    activeVisualParticipantIds: [],
  },
  missionSync: {
    inFlight: false,
    timer: null,
    visibilityHandlerBound: false,
    lastUpdatedAt: null,
    signature: "",
  },
  todayWorkView: {
    dateKey: "",
    runningLimit: 12,
    completedLimit: 12,
  },
  managerCommandInFlight: false,
  connectionAction: {
    inFlight: false,
    propId: null,
    message: "",
    tone: "neutral",
  },
  aiTradeCouncilAnalysis: {
    inFlight: false,
    message: "",
    tone: "neutral",
  },
  aiTradeCouncilAutomation: {
    inFlight: false,
    message: "",
    tone: "neutral",
    pendingAnalysisBarCount: null,
  },
  aiTradeCouncilConsensusPolicy: {
    inFlight: false,
    message: "",
    tone: "neutral",
    pendingRequiredVotes: null,
  },
  aiTradeCouncilDeepAnalysis: {
    data: null,
    inFlight: false,
    packageInFlight: false,
    requestKey: "",
    message: "เปิดแท็บเพื่อโหลดข้อมูลวิเคราะห์เชิงลึกจาก Local Runner",
    tone: "neutral",
  },
  metatraderCandidateChoice: {},
  supportMoveTimers: new Map(),
  supportMoveFrames: new Map(),
  supportSpriteTimers: new Map(),
  pathClearTimer: null,
  sessionSaveTimer: null,
  propReports: {},
  propHitTargets: new Map(),
  hoveredPropId: null,
  navigation: {
    mask: null,
    blockers: [],
    clickBlockers: [],
    grid: { columns: 72, rows: 40 },
    alphaThreshold: 20,
    maskMode: "strict",
    agentFootprint: {
      xRadius: 0.45,
      yRadius: 0.55,
    },
    agentBlockerFootprint: {
      xRadius: 2.4,
      yBackRadius: 0.55,
      yFrontRadius: 0.8,
    },
    walkSpeed: null,
  },
  missions: [
    {
      id: "visual-intake",
      title: "รอรับเป้าหมายจาก CEO",
      detail: "Manager Agent พร้อมรับเป้าหมาย แล้วแบ่งเป็น Task ให้ Agent ที่เหมาะสม",
      owner: "manager",
      status: "queued",
      targetId: "mission_strategy_table",
    },
  ],
  bridge: {
    mode: "กำลังตรวจสอบ",
    status: "ยังไม่ได้ตรวจ Bridge",
    lastRun: "ยังไม่ได้เรียก Local Runner",
    apiOnline: false,
    codex: {
      status: "unknown",
      message: "ยังไม่ได้ตรวจ",
    },
    mcp: {
      status: "unknown",
      message: "ยังไม่ได้ตรวจ",
    },
  },
  agent: {
    id: "manager",
    name: "Manager Agent",
    role: "หัวหน้าทีมและผู้แจกงาน",
    assetPackage: "male-roster-set-a-core-command-operators-v001",
    animationMapPath: null,
    frameImage: MANAGER_STATIC_FRAME,
    x: 35.0,
    y: 73.0,
    w: 6.8,
    direction: "down",
    speedMs: 1,
    status: "พร้อมรับคำสั่ง",
    sprite: {
      type: "frames",
      animationMap: null,
      currentFrames: [],
      mode: "status",
      columns: 1,
      rows: 1,
      frame: 0,
      row: 0,
      rowsByPose: {
        idle_down: 0,
        idle_left: 1,
        idle_right: 2,
        idle_up: 3,
        walk_down: 0,
        walk_left: 1,
        walk_right: 2,
        walk_up: 3,
      },
    },
  },
};

const PROP_HIT_ALPHA_THRESHOLD = 42;
const DEFAULT_WALK_SPEED = {
  msPerDistanceUnit: 50,
  minSegmentMs: 40,
  maxSegmentMs: 2000,
};
const NAVIGATION_LINE_SAMPLE_STEP = 0.22;
const NAVIGATION_MAX_STEP_DISTANCE = 0.45;
const AGENT_WALK_SETTLE_MS = 80;

const els = {
  stage: document.getElementById("roomStage"),
  propLayer: document.getElementById("propLayer"),
  pathLayer: document.getElementById("pathLayer"),
  agentLayer: document.getElementById("agentLayer"),
  agentStatusPanel: document.getElementById("agentStatusPanel"),
  agentStatusList: document.getElementById("agentStatusList"),
  todayWorkPanel: document.getElementById("todayWorkPanel"),
  todayWorkDate: document.getElementById("todayWorkDate"),
  todayRunningList: document.getElementById("todayRunningList"),
  todayRunningCount: document.getElementById("todayRunningCount"),
  todayCompletedList: document.getElementById("todayCompletedList"),
  todayCompletedCount: document.getElementById("todayCompletedCount"),
  layerList: document.getElementById("layerList"),
  selectedLayer: document.getElementById("selectedLayer"),
  reportTitle: document.getElementById("reportTitle"),
  reportSummary: document.getElementById("reportSummary"),
  metricGrid: document.getElementById("metricGrid"),
  missionList: document.getElementById("missionList"),
  hotspotCountPill: document.getElementById("hotspotCountPill"),
  roomImage: document.getElementById("roomImage"),
  codexRateWidget: document.getElementById("codexRateWidget"),
  codexRateSummary: document.getElementById("codexRateSummary"),
  codexRateProgressTrack: document.getElementById("codexRateProgressTrack"),
  codexRateProgress: document.getElementById("codexRateProgress"),
  codexRateReset: document.getElementById("codexRateReset"),
  codexRateFreshness: document.getElementById("codexRateFreshness"),
  codexRateRefreshButton: document.getElementById("codexRateRefreshButton"),
  codexRateSecondary: document.getElementById("codexRateSecondary"),
  codexRateSecondaryLabel: document.getElementById("codexRateSecondaryLabel"),
  codexRateSecondarySummary: document.getElementById("codexRateSecondarySummary"),
  codexRateSecondaryTrack: document.getElementById("codexRateSecondaryTrack"),
  codexRateSecondaryProgress: document.getElementById("codexRateSecondaryProgress"),
  agentCollabControl: document.getElementById("agentCollabControl"),
  agentCollabButton: document.getElementById("agentCollabButton"),
  agentCollabLabel: document.getElementById("agentCollabLabel"),
  agentCollabPanel: document.getElementById("agentCollabPanel"),
  agentCollabPanelTitle: document.getElementById("agentCollabPanelTitle"),
  agentCollabStateBadge: document.getElementById("agentCollabStateBadge"),
  agentCollabMessage: document.getElementById("agentCollabMessage"),
  agentCollabTopic: document.getElementById("agentCollabTopic"),
  agentCollabStartTime: document.getElementById("agentCollabStartTime"),
  agentCollabEndTime: document.getElementById("agentCollabEndTime"),
  agentCollabInterval: document.getElementById("agentCollabInterval"),
  agentCollabMaxTurns: document.getElementById("agentCollabMaxTurns"),
  agentCollabMaxDailyRuns: document.getElementById("agentCollabMaxDailyRuns"),
  agentCollabMinRemaining: document.getElementById("agentCollabMinRemaining"),
  agentCollabUsage: document.getElementById("agentCollabUsage"),
  agentCollabNextRun: document.getElementById("agentCollabNextRun"),
  agentCollabSave: document.getElementById("agentCollabSave"),
  agentCollabRunNow: document.getElementById("agentCollabRunNow"),
  agentCollabToggle: document.getElementById("agentCollabToggle"),
  operatorModeControl: document.getElementById("operatorModeControl"),
  operatorModeButton: document.getElementById("operatorModeButton"),
  operatorModeLabel: document.getElementById("operatorModeLabel"),
  operatorModePanel: document.getElementById("operatorModePanel"),
  operatorModePanelTitle: document.getElementById("operatorModePanelTitle"),
  operatorModeDescription: document.getElementById("operatorModeDescription"),
  operatorModePolicy: document.getElementById("operatorModePolicy"),
  operatorModeToggle: document.getElementById("operatorModeToggle"),
  bridgeModeLabel: document.getElementById("bridgeModeLabel"),
  bridgeStatusPill: document.getElementById("bridgeStatusPill"),
  bridgeStatusText: document.getElementById("bridgeStatusText"),
  codexStatusText: document.getElementById("codexStatusText"),
  mcpStatusText: document.getElementById("mcpStatusText"),
  managerCommandInput: document.getElementById("managerCommandInput"),
  openAgentButton: document.getElementById("openAgentButton"),
  openCeoButton: document.getElementById("openCeoButton"),
  openMissionTableButton: document.getElementById("openMissionTableButton"),
  runCommandButton: document.getElementById("runCommandButton"),
  bridgeEventList: document.getElementById("bridgeEventList"),
  openBridgeButton: document.getElementById("openBridgeButton"),
  decisionLog: document.getElementById("decisionLog"),
  gameModal: document.getElementById("gameModal"),
  gameModalBackdrop: document.getElementById("gameModalBackdrop"),
  modalCloseButton: document.getElementById("modalCloseButton"),
  modalPortraitPanel: document.getElementById("modalPortraitPanel"),
  modalPortrait: document.getElementById("modalPortrait"),
  modalKind: document.getElementById("modalKind"),
  modalTitle: document.getElementById("modalTitle"),
  modalSubtitle: document.getElementById("modalSubtitle"),
  modalStatusGrid: document.getElementById("modalStatusGrid"),
  modalSpeaker: document.getElementById("modalSpeaker"),
  modalDialogue: document.getElementById("modalDialogue"),
  modalTabs: document.getElementById("modalTabs"),
  modalChatLog: document.getElementById("modalChatLog"),
  modalCommandInput: document.getElementById("modalCommandInput"),
  modalSendButton: document.getElementById("modalSendButton"),
  modalAssignButton: document.getElementById("modalAssignButton"),
  modalMeetingButton: document.getElementById("modalMeetingButton"),
  modalDelegateButton: document.getElementById("modalDelegateButton"),
  modalAgentComposer: document.getElementById("modalAgentComposer"),
  modalComposerLabel: document.getElementById("modalComposerLabel"),
  modalChatStatus: document.getElementById("modalChatStatus"),
  modalChatUsageNote: document.getElementById("modalChatUsageNote"),
  modalTaskBoard: document.getElementById("modalTaskBoard"),
  modalDashboardConnectionRail: document.getElementById("modalDashboardConnectionRail"),
  modalGenericDashboardWorkspace: document.getElementById("modalGenericDashboardWorkspace"),
  modalWorkflowDashboardWorkspace: document.getElementById("modalWorkflowDashboardWorkspace"),
  workflowSettingsRail: document.getElementById("workflowSettingsRail"),
  workflowSettingsRailContent: document.getElementById("workflowSettingsRailContent"),
  workflowAgentHandoffRail: document.getElementById("workflowAgentHandoffRail"),
  workflowHandoffReport: document.getElementById("workflowHandoffReport"),
  workflowHandoffTarget: document.getElementById("workflowHandoffTarget"),
  workflowHandoffAction: document.getElementById("workflowHandoffAction"),
  workflowHandoffButton: document.getElementById("workflowHandoffButton"),
  workflowHandoffStatus: document.getElementById("workflowHandoffStatus"),
  workflowDashboardTabs: document.getElementById("workflowDashboardTabs"),
  workflowDashboardContent: document.getElementById("workflowDashboardContent"),
  workflowResultsPanel: document.getElementById("workflowResultsPanel"),
  workflowResultsEyebrow: document.getElementById("workflowResultsEyebrow"),
  workflowResultsTitle: document.getElementById("workflowResultsTitle"),
  workflowResultsCopy: document.getElementById("workflowResultsCopy"),
  workflowRunningList: document.getElementById("workflowRunningList"),
  workflowCompletedList: document.getElementById("workflowCompletedList"),
  workflowBlockedList: document.getElementById("workflowBlockedList"),
  workflowRunningCount: document.getElementById("workflowRunningCount"),
  workflowCompletedCount: document.getElementById("workflowCompletedCount"),
  workflowBlockedCount: document.getElementById("workflowBlockedCount"),
  workflowResultSummary: document.getElementById("workflowResultSummary"),
  workflowActionStatus: document.getElementById("workflowActionStatus"),
  modalSignalConsensusWorkspace: document.getElementById("modalSignalConsensusWorkspace"),
  signalConsensusTabs: document.getElementById("signalConsensusTabs"),
  signalConsensusDailyContent: document.getElementById("signalConsensusDailyContent"),
  signalConsensusLiveContent: document.getElementById("signalConsensusLiveContent"),
  signalConsensusLiveTabs: document.getElementById("signalConsensusLiveTabs"),
  signalConsensusLiveOverviewContent: document.getElementById("signalConsensusLiveOverviewContent"),
  signalConsensusPriceActionContent: document.getElementById("signalConsensusPriceActionContent"),
  signalConsensusTechnicalContent: document.getElementById("signalConsensusTechnicalContent"),
  signalConsensusNewsContent: document.getElementById("signalConsensusNewsContent"),
  signalConsensusDecisionContent: document.getElementById("signalConsensusDecisionContent"),
  signalConsensusHistoryContent: document.getElementById("signalConsensusHistoryContent"),
  modalDashboardRunning: document.getElementById("modalDashboardRunning"),
  modalDashboardCompleted: document.getElementById("modalDashboardCompleted"),
  modalDashboardBlocked: document.getElementById("modalDashboardBlocked"),
  modalDashboardRunningCount: document.getElementById("modalDashboardRunningCount"),
  modalDashboardCompletedCount: document.getElementById("modalDashboardCompletedCount"),
  modalDashboardBlockedCount: document.getElementById("modalDashboardBlockedCount"),
  modalDashboardWorkCount: document.getElementById("modalDashboardWorkCount"),
  modalDashboardFreshness: document.getElementById("modalDashboardFreshness"),
  modalDashboardConnectionList: document.getElementById("modalDashboardConnectionList"),
  modalDashboardConnectionOverall: document.getElementById("modalDashboardConnectionOverall"),
  modalDashboardConnectionCheckedAt: document.getElementById("modalDashboardConnectionCheckedAt"),
  modalDashboardModuleName: document.getElementById("modalDashboardModuleName"),
  modalDashboardModuleAvailability: document.getElementById("modalDashboardModuleAvailability"),
  modalDashboardOperationMode: document.getElementById("modalDashboardOperationMode"),
  modalDashboardScheduleStatus: document.getElementById("modalDashboardScheduleStatus"),
  modalDashboardRefreshConnections: document.getElementById("modalDashboardRefreshConnections"),
  modalDashboardDiscoverMetatrader: document.getElementById("modalDashboardDiscoverMetatrader"),
  modalDashboardConnectionActionStatus: document.getElementById("modalDashboardConnectionActionStatus"),
  modalDashboardMetatraderSelection: document.getElementById("modalDashboardMetatraderSelection"),
  modalDashboardMetatraderSummary: document.getElementById("modalDashboardMetatraderSummary"),
  modalDashboardMetatraderCandidates: document.getElementById("modalDashboardMetatraderCandidates"),
  modalDashboardConfirmMetatrader: document.getElementById("modalDashboardConfirmMetatrader"),
  modalKanbanSearch: document.getElementById("modalKanbanSearch"),
  modalKanbanArchiveToggle: document.getElementById("modalKanbanArchiveToggle"),
  modalKanbanRefresh: document.getElementById("modalKanbanRefresh"),
  modalKanbanBoard: document.getElementById("modalKanbanBoard"),
  modalKanbanDetail: document.getElementById("modalKanbanDetail"),
  modalKanbanDetailTitle: document.getElementById("modalKanbanDetailTitle"),
  modalKanbanDetailBody: document.getElementById("modalKanbanDetailBody"),
  modalKanbanCloseDetail: document.getElementById("modalKanbanCloseDetail"),
  modalKanbanApprove: document.getElementById("modalKanbanApprove"),
  modalKanbanReject: document.getElementById("modalKanbanReject"),
  modalKanbanExecuteConfirmation: document.getElementById("modalKanbanExecuteConfirmation"),
  modalKanbanExecuteMissionId: document.getElementById("modalKanbanExecuteMissionId"),
  modalKanbanExecuteStatus: document.getElementById("modalKanbanExecuteStatus"),
  modalKanbanExecute: document.getElementById("modalKanbanExecute"),
  modalKanbanOpenOwnerAgent: document.getElementById("modalKanbanOpenOwnerAgent"),
  modalKanbanOpenTargetProp: document.getElementById("modalKanbanOpenTargetProp"),
  taskDetailDialog: document.getElementById("taskDetailDialog"),
  dashboardResultDialog: document.getElementById("dashboardResultDialog"),
  dashboardResultDetailTitle: document.getElementById("dashboardResultDetailTitle"),
  dashboardResultDetailBody: document.getElementById("dashboardResultDetailBody"),
  dashboardResultDetailClose: document.getElementById("dashboardResultDetailClose"),
};

let taskDetailReturnFocus = null;
let taskDetailShouldRestoreFocus = true;
let taskDetailReturnMissionId = null;
let taskDetailReturnContainerId = null;
let dashboardResultReturnFocus = null;
let dashboardResultShouldRestoreFocus = true;

const agentWaypoints = {
  front_entry_gate: { x: 35.0, y: 73.0, label: "จุดเข้า Agent" },
  mission_strategy_table: { x: 43.5, y: 67.2, label: "หน้าโต๊ะวางแผน Mission" },
  codex_mcp_portal: { x: 42.0, y: 46.0, label: "เรดาร์ระบบเทรดโลก" },
  left_analytics_console: { x: 27.0, y: 58.0, label: "สภา AI Trade" },
  right_tool_console: { x: 73.0, y: 58.0, label: "ห้องทดลอง EA" },
  terminal_workstation: { x: 72.5, y: 70.0, label: "โต๊ะพัฒนา EA สำหรับ MT4/MT5" },
  left_server_racks: { x: 28.0, y: 46.0, label: "คลังวิจัยระบบเทรด" },
  right_server_racks: { x: 70.0, y: 46.0, label: "โรงงานสร้าง EA และ Indicator" },
  left_audit_crystals: { x: 22.0, y: 72.0, label: "Indicator Scout" },
  left_signal_cube: { x: 24.2, y: 66.0, label: "ข่าวรายวันและแนวโน้ม Forex" },
  right_status_crystals: { x: 77.0, y: 59.0, label: "คริสตัลสถานะ VPS และภาพรวม HQ" },
};

const agentRoute = [
  "codex_mcp_portal",
  "right_tool_console",
  "terminal_workstation",
  "left_analytics_console",
  "mission_strategy_table",
];

const officeAgentDefinitions = [
  {
    id: "manager",
    name: AGENT_DISPLAY.manager.name,
    role: AGENT_DISPLAY.manager.role,
    summary: AGENT_DISPLAY.manager.summary,
    image: `${MALE_ROSTER_ASSET_ROOT}/characters/02-hq-manager-male-static-v001.png`,
    defaultTarget: "mission_strategy_table",
    homeTarget: "front_entry_gate",
    tools: ["mission_strategy_table", "codex_mcp_portal", "right_tool_console"],
    status: AGENT_DISPLAY.manager.status,
    x: 35.0,
    y: 73.0,
    w: 6.8,
    isManager: true,
  },
  {
    id: "ceo",
    name: AGENT_DISPLAY.ceo.name,
    role: AGENT_DISPLAY.ceo.role,
    summary: AGENT_DISPLAY.ceo.summary,
    image: `${MALE_ROSTER_ASSET_ROOT}/characters/01-ceo-male-static-v001.png`,
    defaultTarget: "mission_strategy_table",
    homeTarget: "front_entry_gate",
    tools: ["approval_gate", "executive_report", "mission_strategy_table"],
    status: AGENT_DISPLAY.ceo.status,
    x: 41.0,
    y: 76.0,
    w: 6.7,
  },
  {
    id: "ea_developer",
    name: AGENT_DISPLAY.ea_developer.name,
    role: AGENT_DISPLAY.ea_developer.role,
    summary: AGENT_DISPLAY.ea_developer.summary,
    image: `${MALE_ROSTER_ASSET_ROOT}/characters/06-ea-developer-male-static-v001.png`,
    defaultTarget: "right_server_racks",
    homeTarget: "right_server_racks",
    tools: ["right_server_racks", "terminal_workstation", "code_workspace", "compile_log"],
    status: AGENT_DISPLAY.ea_developer.status,
    x: 68.0,
    y: 74.5,
    w: 6.3,
  },
  {
    id: "backtest_analyst",
    name: AGENT_DISPLAY.backtest_analyst.name,
    role: AGENT_DISPLAY.backtest_analyst.role,
    summary: AGENT_DISPLAY.backtest_analyst.summary,
    image: `${MALE_ROSTER_ASSET_ROOT}/characters/03-backtest-analyst-male-static-v001.png`,
    defaultTarget: "left_analytics_console",
    homeTarget: "left_analytics_console",
    tools: ["left_analytics_console", "right_tool_console", "left_report_board", "report_archive"],
    status: AGENT_DISPLAY.backtest_analyst.status,
    x: 32.0,
    y: 66.0,
    w: 6.5,
  },
  {
    id: "optimization_agent",
    name: AGENT_DISPLAY.optimization_agent.name,
    role: AGENT_DISPLAY.optimization_agent.role,
    summary: AGENT_DISPLAY.optimization_agent.summary,
    image: `${MALE_ROSTER_ASSET_ROOT}/characters/05-optimization-agent-male-static-v001.png`,
    defaultTarget: "right_tool_console",
    homeTarget: "right_tool_console",
    tools: ["right_tool_console", "left_analytics_console", "mission_strategy_table"],
    status: AGENT_DISPLAY.optimization_agent.status,
    x: 55.5,
    y: 73.0,
    w: 6.2,
  },
  {
    id: "vps_watch",
    name: AGENT_DISPLAY.vps_watch.name,
    role: AGENT_DISPLAY.vps_watch.role,
    summary: AGENT_DISPLAY.vps_watch.summary,
    image: `${MALE_ROSTER_ASSET_ROOT}/characters/08-vps-watch-male-static-v001.png`,
    defaultTarget: "right_status_crystals",
    homeTarget: "right_status_crystals",
    tools: ["right_status_crystals"],
    status: AGENT_DISPLAY.vps_watch.status,
    x: 70.0,
    y: 61.5,
    w: 6.0,
  },
  {
    id: "telegram_ops",
    name: AGENT_DISPLAY.telegram_ops.name,
    role: AGENT_DISPLAY.telegram_ops.role,
    summary: AGENT_DISPLAY.telegram_ops.summary,
    image: `${MALE_ROSTER_ASSET_ROOT}/characters/04-telegram-ops-male-static-v001.png`,
    defaultTarget: "mission_strategy_table",
    homeTarget: "mission_strategy_table",
    tools: ["mission_strategy_table"],
    status: AGENT_DISPLAY.telegram_ops.status,
    x: 76.0,
    y: 68.5,
    w: 6.0,
  },
  {
    id: "risk_guard",
    name: AGENT_DISPLAY.risk_guard.name,
    role: AGENT_DISPLAY.risk_guard.role,
    summary: AGENT_DISPLAY.risk_guard.summary,
    image: `${MALE_ROSTER_ASSET_ROOT}/characters/09-risk-guard-male-static-v001.png`,
    defaultTarget: "mission_strategy_table",
    homeTarget: "mission_strategy_table",
    tools: ["mission_strategy_table"],
    status: AGENT_DISPLAY.risk_guard.status,
    x: 24.2,
    y: 73.0,
    w: 6.6,
  },
  {
    id: "codex_mcp_operator",
    name: AGENT_DISPLAY.codex_mcp_operator.name,
    role: AGENT_DISPLAY.codex_mcp_operator.role,
    summary: AGENT_DISPLAY.codex_mcp_operator.summary,
    image: `${MALE_ROSTER_ASSET_ROOT}/characters/07-codex-mcp-operator-male-static-v001.png`,
    defaultTarget: "codex_mcp_portal",
    homeTarget: "codex_mcp_portal",
    tools: ["codex_mcp_portal", "left_audit_crystals", "left_signal_cube", "left_server_racks", "left_analytics_console", "mission_strategy_table"],
    status: AGENT_DISPLAY.codex_mcp_operator.status,
    x: 43.0,
    y: 51.0,
    w: 6.1,
  },
  {
    id: "mission_archivist",
    name: AGENT_DISPLAY.mission_archivist.name,
    role: AGENT_DISPLAY.mission_archivist.role,
    summary: AGENT_DISPLAY.mission_archivist.summary,
    image: `${MALE_ROSTER_ASSET_ROOT}/characters/10-mission-archivist-male-static-v001.png`,
    defaultTarget: "left_server_racks",
    homeTarget: "left_server_racks",
    tools: ["left_audit_crystals", "left_report_board", "mission_strategy_table", "report_archive"],
    status: AGENT_DISPLAY.mission_archivist.status,
    x: 28.0,
    y: 52.0,
    w: 6.0,
  },
];

const meetingSeats = {
  manager: { x: 43.5, y: 67.2, label: "ที่นั่ง Manager Agent" },
  ceo: { x: 47.2, y: 69.0, label: "ที่นั่ง CEO" },
  ea_developer: { x: 55.5, y: 68.2, label: "ที่นั่ง EA Developer" },
  backtest_analyst: { x: 38.7, y: 66.8, label: `ที่นั่ง ${AI_TRADE_COUNCIL_PUBLIC_NAMES.backtest_analyst}` },
  optimization_agent: { x: 51.8, y: 72.2, label: `ที่นั่ง ${AI_TRADE_COUNCIL_PUBLIC_NAMES.optimization_agent}` },
  vps_watch: { x: 58.6, y: 72.6, label: "ที่นั่ง VPS Watch" },
  telegram_ops: { x: 45.1, y: 73.0, label: "ที่นั่ง Telegram Ops" },
  risk_guard: { x: 35.7, y: 70.8, label: "ที่นั่ง Risk Guard" },
  codex_mcp_operator: { x: 49.2, y: 65.8, label: `ที่นั่ง ${AI_TRADE_COUNCIL_PUBLIC_NAMES.codex_mcp_operator}` },
  mission_archivist: { x: 40.8, y: 72.9, label: "ที่นั่ง Mission Archivist" },
};

const sharedWorkstationSeats = {
  left_analytics_console: {
    backtest_analyst: { x: 21.5, y: 61.0, label: `จุดวิเคราะห์กราฟของ ${AI_TRADE_COUNCIL_PUBLIC_NAMES.backtest_analyst}` },
    optimization_agent: { x: 27.5, y: 66.0, label: `จุดวิเคราะห์เทคนิคของ ${AI_TRADE_COUNCIL_PUBLIC_NAMES.optimization_agent}` },
    codex_mcp_operator: { x: 33.5, y: 61.0, label: `จุดวิเคราะห์ข่าวของ ${AI_TRADE_COUNCIL_PUBLIC_NAMES.codex_mcp_operator}` },
  },
};

async function init() {
  const [roomResult, agentResult] = await Promise.allSettled([
    fetchJson(ROOM_CONTRACT_PATH, { timeoutMs: 5000 }),
    fetchJson(AGENT_CONTRACT_PATH, { timeoutMs: 3000 }),
  ]);

  if (roomResult.status === "fulfilled" && roomResult.value?.room && Array.isArray(roomResult.value.layers)) {
    state.data = roomResult.value;
  } else {
    const roomError = roomResult.status === "rejected"
      ? roomResult.reason
      : new Error("ข้อมูลห้องไม่ครบ จึงกำลังใช้ฉากสำรอง");
    reportBootResourceFailure(ROOM_CONTRACT_PATH, roomError);
    state.data = createFallbackRoomData();
  }

  if (agentResult.status === "fulfilled" && Array.isArray(agentResult.value?.agents)) {
    state.agentRoster = agentResult.value.agents;
  } else {
    const agentError = agentResult.status === "rejected"
      ? agentResult.reason
      : new Error("ข้อมูล Agent ไม่ครบ จึงกำลังใช้รายชื่อสำรอง");
    reportBootResourceFailure(AGENT_CONTRACT_PATH, agentError);
    state.agentRoster = [];
  }

  const loadedSession = await loadSessionSnapshot();
  const sessionLayout = migrateOfficeSessionLayout(loadedSession);
  const savedSession = sessionLayout.snapshot;
  state.restoredSession = savedSession;

  els.roomImage.src = resolveProjectAssetPath(state.data.room.image);
  els.hotspotCountPill.textContent = `${getInteractiveObjects().length} อุปกรณ์ที่กดได้`;
  updateBridgeLabel();
  updateDecisionLog("CEO → Manager Agent: พร้อมรับ Mission ถัดไป");

  state.data.layers.forEach((layer) => {
    if (layer.defaultVisible) state.visibleLayers.add(layer.id);
  });
  applySessionSnapshot(savedSession);
  initializeOfficeAgents(savedSession);
  if (sessionLayout.migrated) saveSessionSnapshot();
  renderAgentSelector();

  renderLayers();
  renderProps();
  renderAgent();
  renderOperationalSidebars();
  const renderedAgentCount = els.agentLayer.querySelectorAll(".agent-unit").length;
  if (officeAgentDefinitions.length !== EXPECTED_OFFICE_AGENT_COUNT) {
    reportBootResourceFailure(
      "รายชื่อ Agent สำรอง",
      new Error(`พบ Agent ${officeAgentDefinitions.length}/${EXPECTED_OFFICE_AGENT_COUNT} ตัว`),
      { blocking: true },
    );
  }
  window.MetafxHqBoot?.markReady({ agentCount: renderedAgentCount });
  window.setTimeout(startCodexRateLimitPolling, 0);
  window.setTimeout(startOperatorModePolling, 0);
  window.setTimeout(startAgentCollaborationPolling, 0);
  window.setTimeout(startMissionPolling, 0);

  loadAgentAnimationMap().then(() => {
    const managerFrame = document.getElementById("agentFrameImage");
    if (managerFrame && state.agent.frameImage) {
      managerFrame.src = withAgentAssetVersion(state.agent.frameImage);
    }
  });

  loadNavigationMask(state.data.navigation).catch((error) => {
    state.navigation.mask = null;
    reportBootResourceFailure(state.data.navigation?.walkableMask || "พื้นที่เดินของ Agent", error);
  });

  restoreActivePanel(savedSession);
  restoreSessionUi(savedSession);
  refreshBridgeStatus({
    recordEvent: !savedSession,
    preserveDecisionLog: Boolean(savedSession),
  });
  loadBridgeMissions({ replaceEvents: !savedSession });
  loadMemoryStatus({ recordEvent: !savedSession });
  startOfficeAutonomy();
}

async function fetchJson(path, { timeoutMs = DEFAULT_FETCH_TIMEOUT_MS } = {}) {
  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(path, {
      cache: "no-store",
      signal: controller.signal,
    });
    if (!response.ok) throw new Error(`โหลดข้อมูล ${path} ไม่สำเร็จ (HTTP ${response.status})`);
    return await response.json();
  } finally {
    window.clearTimeout(timeoutId);
  }
}

function normalizeCodexRateTimestamp(value) {
  if (value === null || value === undefined || value === "") return null;
  const numericValue = typeof value === "number" || /^\d+(?:\.\d+)?$/.test(String(value).trim())
    ? Number(value)
    : null;
  const milliseconds = Number.isFinite(numericValue)
    ? (numericValue < 1_000_000_000_000 ? numericValue * 1000 : numericValue)
    : value;
  const date = new Date(milliseconds);
  return Number.isFinite(date.getTime()) ? date.toISOString() : null;
}

function normalizeCodexRateWindow(value) {
  if (!value || typeof value !== "object" || Array.isArray(value)) return null;
  const rawUsed = Number(value.usedPercent);
  const rawRemaining = Number(value.remainingPercent);
  if (!Number.isFinite(rawUsed) && !Number.isFinite(rawRemaining)) return null;
  const usedPercent = clamp(Number.isFinite(rawUsed) ? rawUsed : 100 - rawRemaining, 0, 100);
  const durationValue = Number(value.windowDurationMinutes ?? value.windowDurationMins);
  return {
    usedPercent,
    remainingPercent: clamp(100 - usedPercent, 0, 100),
    windowDurationMinutes: Number.isFinite(durationValue) && durationValue > 0
      ? Math.round(durationValue)
      : null,
    resetsAt: normalizeCodexRateTimestamp(value.resetsAt),
  };
}

function codexRateLimitWasReached(value) {
  if (value === true) return true;
  if (typeof value !== "string") return false;
  const normalized = value.trim().toLowerCase();
  return Boolean(normalized && !["none", "null", "false", "available"].includes(normalized));
}

function normalizeCodexRatePayload(payload) {
  if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
    return { status: "unavailable", primary: null, secondary: null };
  }

  const buckets = Array.isArray(payload.buckets) ? payload.buckets : [];
  const canonicalBucket = buckets.find((item) => String(item?.id || item?.limitId || "").toLowerCase() === "codex")
    || buckets[0]
    || null;
  const nestedSnapshot = canonicalBucket
    || payload.rateLimit
    || payload.rateLimits
    || payload.snapshot
    || payload;
  const windows = nestedSnapshot?.windows && typeof nestedSnapshot.windows === "object"
    ? nestedSnapshot.windows
    : nestedSnapshot;
  const primary = normalizeCodexRateWindow(windows?.primary);
  const secondary = normalizeCodexRateWindow(windows?.secondary);
  const rawStatus = String(payload.status || nestedSnapshot?.status || "").trim().toLowerCase();
  const stale = Boolean(payload.stale || nestedSnapshot?.stale || rawStatus === "stale");
  const reachedValue = nestedSnapshot?.limitReached
    ?? nestedSnapshot?.rateLimitReached
    ?? nestedSnapshot?.rateLimitReachedType;

  return {
    status: primary
      ? (stale ? "stale" : "ready")
      : (["auth_required", "config_error", "timeout", "missing", "unavailable"].includes(rawStatus) ? rawStatus : "unavailable"),
    source: "codex_app_server",
    meter: "codex",
    primary,
    secondary,
    limitReached: codexRateLimitWasReached(reachedValue),
    checkedAt: normalizeCodexRateTimestamp(
      payload.capturedAt
      || payload.checkedAt
      || payload.updatedAt
      || nestedSnapshot?.capturedAt
      || new Date().toISOString(),
    ),
  };
}

function formatCodexRatePercent(value) {
  return `${Math.round(clamp(Number(value) || 0, 0, 100))}%`;
}

function formatCodexRateWindow(durationMinutes) {
  const minutes = Number(durationMinutes);
  if (!Number.isFinite(minutes) || minutes <= 0) return "รอบโควตา";
  if (minutes % 1440 === 0) return `รอบ ${minutes / 1440} วัน`;
  if (minutes % 60 === 0) return `รอบ ${minutes / 60} ชม.`;
  return `รอบ ${Math.round(minutes)} นาที`;
}

function formatCodexRateReset(resetsAt) {
  const date = resetsAt ? new Date(resetsAt) : null;
  if (!date || !Number.isFinite(date.getTime())) return "ยังไม่มีเวลารีเซ็ต";
  const formatted = new Intl.DateTimeFormat("th-TH", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
  return `รีเซ็ต ${formatted}`;
}

function formatCodexRateCheckedAt(checkedAt) {
  const date = checkedAt ? new Date(checkedAt) : null;
  if (!date || !Number.isFinite(date.getTime())) return "ยังไม่เคยตรวจ";
  return new Intl.DateTimeFormat("th-TH", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  }).format(date);
}

function updateCodexRateProgress(track, progress, windowData, label) {
  if (!track || !progress) return;
  if (!windowData) {
    progress.style.width = "0%";
    track.removeAttribute("aria-valuenow");
    track.setAttribute("aria-valuetext", "ไม่มีข้อมูล");
    return;
  }
  const usedPercent = clamp(Number(windowData.usedPercent) || 0, 0, 100);
  progress.style.width = `${usedPercent}%`;
  track.setAttribute("aria-valuenow", String(Math.round(usedPercent)));
  track.setAttribute("aria-valuetext", `${label} ใช้แล้ว ${formatCodexRatePercent(usedPercent)}`);
}

function getCodexRateDisplayState(snapshot) {
  if (!snapshot?.primary) return snapshot?.status === "loading" ? "loading" : "unavailable";
  if (snapshot.status === "stale") return "stale";
  return getCodexRateSeverity(snapshot);
}

function getCodexRateSeverity(snapshot) {
  if (!snapshot?.primary) return "unavailable";
  const usedPercent = Math.max(
    Number(snapshot.primary?.usedPercent) || 0,
    Number(snapshot.secondary?.usedPercent) || 0,
  );
  if (snapshot.limitReached || usedPercent >= 90) return "critical";
  if (usedPercent >= 70) return "warning";
  return "ready";
}

function renderCodexRateLimit(snapshot = state.codexRate.snapshot) {
  if (!els.codexRateWidget) return;
  const displayState = getCodexRateDisplayState(snapshot);
  els.codexRateWidget.dataset.state = displayState;
  els.codexRateWidget.dataset.severity = getCodexRateSeverity(snapshot);
  els.codexRateRefreshButton.disabled = state.codexRate.inFlight;
  els.codexRateRefreshButton.classList.toggle("refreshing", state.codexRate.inFlight);

  if (!snapshot?.primary) {
    const loading = displayState === "loading";
    const failureCopy = {
      auth_required: ["กรุณา Login Codex", "บัญชี Codex ยังไม่ได้เข้าสู่ระบบ", "ต้อง Login"],
      config_error: ["Codex Config มีปัญหา", "แก้ Config แล้วกดตรวจสอบอีกครั้ง", "Config ผิดพลาด"],
      timeout: ["อ่านโควตาไม่ทันเวลา", "Codex ตอบกลับช้ากว่าที่กำหนด", "หมดเวลารอ"],
      missing: ["ไม่พบ Codex Runtime", "ตรวจสอบ Local Runner ของโปรเจกต์", "ไม่พบ Runtime"],
      unavailable: ["ไม่สามารถอ่านโควตาได้", "Bridge หรือ Codex ยังไม่พร้อม", "ยังไม่มีข้อมูล"],
    };
    const copy = failureCopy[snapshot?.status] || failureCopy.unavailable;
    els.codexRateSummary.textContent = loading ? "กำลังตรวจสอบโควตา..." : copy[0];
    els.codexRateReset.textContent = loading ? "กำลังเชื่อม Codex account" : copy[1];
    els.codexRateFreshness.textContent = loading ? "กำลังตรวจ" : copy[2];
    updateCodexRateProgress(els.codexRateProgressTrack, els.codexRateProgress, null, "Codex");
    els.codexRateSecondary.hidden = true;
    refreshOpenDashboardConnectionPanel();
    return;
  }

  const primary = snapshot.primary;
  els.codexRateSummary.textContent = `เหลือ ${formatCodexRatePercent(primary.remainingPercent)} • ใช้แล้ว ${formatCodexRatePercent(primary.usedPercent)}`;
  els.codexRateReset.textContent = `${formatCodexRateWindow(primary.windowDurationMinutes)} • ${formatCodexRateReset(primary.resetsAt)}`;
  const checkedLabel = formatCodexRateCheckedAt(snapshot.checkedAt);
  els.codexRateFreshness.textContent = displayState === "stale" ? `ข้อมูลเดิม • ${checkedLabel}` : `ข้อมูลล่าสุด • ${checkedLabel}`;
  updateCodexRateProgress(els.codexRateProgressTrack, els.codexRateProgress, primary, "Codex");

  if (snapshot.secondary) {
    els.codexRateSecondary.hidden = false;
    els.codexRateSecondaryLabel.textContent = formatCodexRateWindow(snapshot.secondary.windowDurationMinutes);
    els.codexRateSecondarySummary.textContent = `เหลือ ${formatCodexRatePercent(snapshot.secondary.remainingPercent)}`;
    updateCodexRateProgress(
      els.codexRateSecondaryTrack,
      els.codexRateSecondaryProgress,
      snapshot.secondary,
      "Codex secondary",
    );
  } else {
    els.codexRateSecondary.hidden = true;
    updateCodexRateProgress(els.codexRateSecondaryTrack, els.codexRateSecondaryProgress, null, "Codex secondary");
  }
  refreshOpenDashboardConnectionPanel();
}

async function fetchCodexRateLimitPayload({ manual = false } = {}) {
  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => controller.abort(), CODEX_RATE_LIMIT_FETCH_TIMEOUT_MS);
  try {
    const endpoint = manual ? `${CODEX_RATE_LIMIT_ENDPOINT}?refresh=1` : CODEX_RATE_LIMIT_ENDPOINT;
    const response = await fetch(endpoint, {
      cache: "no-store",
      signal: controller.signal,
    });
    const payload = await response.json().catch(() => null);
    if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
      throw new Error("ยังไม่ได้รับข้อมูล Rate Limit จาก Codex");
    }
    if (!response.ok && payload.ok !== false && !payload.status && !payload.stale) {
      throw new Error(`ขอข้อมูล Rate Limit จาก Codex ไม่สำเร็จ (HTTP ${response.status})`);
    }
    return payload;
  } finally {
    window.clearTimeout(timeoutId);
  }
}

async function refreshCodexRateLimits({ manual = false } = {}) {
  if (!els.codexRateWidget || state.codexRate.inFlight) return null;
  if (!manual && document.visibilityState !== "visible") return null;

  state.codexRate.inFlight = true;
  if (!state.codexRate.lastGood) {
    state.codexRate.snapshot = { status: "loading", primary: null, secondary: null };
  } else if (els.codexRateFreshness) {
    els.codexRateFreshness.textContent = "กำลังอัปเดต";
  }
  renderCodexRateLimit();

  let failureStatus = "unavailable";
  try {
    const payload = await fetchCodexRateLimitPayload({ manual });
    const snapshot = normalizeCodexRatePayload(payload);
    failureStatus = snapshot.status;
    if (!snapshot.primary) {
      if (["auth_required", "config_error", "missing"].includes(snapshot.status)) {
        state.codexRate.lastGood = null;
        state.codexRate.snapshot = snapshot;
        state.codexRate.status = snapshot.status;
        return null;
      }
      throw new Error("ข้อมูล Rate Limit ของ Codex ยังไม่มีรอบโควตาที่ใช้ได้");
    }
    state.codexRate.snapshot = snapshot;
    state.codexRate.status = snapshot.status;
    state.codexRate.lastGood = {
      ...snapshot,
      primary: { ...snapshot.primary },
      secondary: snapshot.secondary ? { ...snapshot.secondary } : null,
    };
    return snapshot;
  } catch {
    const lastGoodTime = state.codexRate.lastGood?.checkedAt
      ? new Date(state.codexRate.lastGood.checkedAt).getTime()
      : 0;
    const lastGoodAge = Number.isFinite(lastGoodTime) ? Date.now() - lastGoodTime : Number.POSITIVE_INFINITY;
    const canServeLocalStale = state.codexRate.lastGood
      && !["auth_required", "config_error", "missing"].includes(failureStatus)
      && lastGoodAge >= 0
      && lastGoodAge <= CODEX_RATE_LIMIT_STALE_MAX_MS;
    if (canServeLocalStale) {
      state.codexRate.snapshot = {
        ...state.codexRate.lastGood,
        status: "stale",
        primary: { ...state.codexRate.lastGood.primary },
        secondary: state.codexRate.lastGood.secondary ? { ...state.codexRate.lastGood.secondary } : null,
      };
      state.codexRate.status = "stale";
    } else {
      state.codexRate.lastGood = null;
      state.codexRate.snapshot = { status: failureStatus, primary: null, secondary: null };
      state.codexRate.status = failureStatus;
    }
    return null;
  } finally {
    state.codexRate.inFlight = false;
    renderCodexRateLimit();
  }
}

function startCodexRateLimitPolling() {
  if (!els.codexRateWidget) return;
  renderCodexRateLimit(state.codexRate.snapshot || { status: "loading", primary: null, secondary: null });
  void refreshCodexRateLimits();

  if (!state.codexRate.timer) {
    state.codexRate.timer = window.setInterval(() => {
      if (document.visibilityState === "visible") void refreshCodexRateLimits();
    }, CODEX_RATE_LIMIT_POLL_MS);
  }

  if (!state.codexRate.visibilityHandlerBound) {
    document.addEventListener("visibilitychange", () => {
      if (document.visibilityState !== "visible") return;
      const checkedAt = state.codexRate.snapshot?.checkedAt
        ? new Date(state.codexRate.snapshot.checkedAt).getTime()
        : 0;
      if (!Number.isFinite(checkedAt) || Date.now() - checkedAt >= CODEX_RATE_LIMIT_POLL_MS) {
        void refreshCodexRateLimits();
      }
    });
    state.codexRate.visibilityHandlerBound = true;
  }
}

async function postJson(path, payload = {}) {
  const response = await fetch(path, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = new Error(body.message || body.error || `ส่งข้อมูลไปยัง ${path} ไม่สำเร็จ`);
    error.status = response.status;
    error.body = body;
    throw error;
  }
  return body;
}

function normalizeOperatorModePayload(payload) {
  if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
    throw new Error("invalid_operator_mode_response");
  }
  const mode = String(payload.mode || "").trim().toLowerCase();
  if (!["auto_guarded", "manual_guarded"].includes(mode)) {
    throw new Error("invalid_operator_mode_response");
  }
  const guardrails = payload.guardrails && typeof payload.guardrails === "object" && !Array.isArray(payload.guardrails)
    ? payload.guardrails
    : {};
  const safeList = (value) => (
    Array.isArray(value)
      ? value.filter((item) => typeof item === "string" && item.trim()).map((item) => item.trim().slice(0, 100)).slice(0, 40)
      : []
  );
  return {
    mode,
    labelTh: safeDashboardDisplayText(
      payload.labelTh,
      mode === "auto_guarded" ? "อัตโนมัติ — Workspace + Web Search" : "ตรวจสอบก่อนเริ่มงาน",
    ),
    autoExecute: payload.autoExecute === true,
    backendAvailable: true,
    fallback: false,
    guardrails: {
      autoEligibleTools: safeList(guardrails.autoEligibleTools),
      maxRisk: typeof guardrails.maxRisk === "string" ? guardrails.maxRisk.slice(0, 40) : null,
      alwaysRequireHumanApprovalFor: safeList(guardrails.alwaysRequireHumanApprovalFor),
    },
    updatedAt: typeof payload.updatedAt === "string" ? payload.updatedAt : null,
  };
}

function renderOperatorModeControl() {
  if (!els.operatorModeControl) return;
  const operatorMode = state.operatorMode;
  const isAutoMode = operatorMode.mode === "auto_guarded";
  const autoExecutionActive = isAutoMode && operatorMode.autoExecute === true;
  const visibleMode = operatorMode.inFlight ? "setting" : operatorMode.mode;
  const label = isAutoMode
    ? "Full Access"
    : operatorMode.mode === "manual_guarded"
      ? "จำกัดสิทธิ์"
      : "กำลังตรวจสอบสิทธิ์...";

  els.operatorModeControl.dataset.mode = visibleMode;
  if (els.operatorModeLabel) els.operatorModeLabel.textContent = label;
  if (els.operatorModePanelTitle) {
    els.operatorModePanelTitle.textContent = operatorMode.fallback
      ? "จำกัดสิทธิ์ — Backend ยังไม่พร้อม"
      : label;
  }
  if (els.operatorModeDescription) {
    els.operatorModeDescription.textContent = autoExecutionActive
      ? "งานที่ Backend อนุญาตทำในโฟลเดอร์โปรเจกต์และค้นเว็บสาธารณะแบบอ่านอย่างเดียวได้อัตโนมัติ แล้วส่งรายงานพร้อมแหล่งข้อมูลกลับอุปกรณ์โดยไม่ต้องกดอนุมัติซ้ำ"
      : operatorMode.backendAvailable
        ? "ระบบจะตรวจ Mission และสิทธิ์กับ Backend ก่อนเริ่มงานจริงทุกครั้ง"
        : "ยังอ่านโหมดจาก Backend ไม่ได้ จึงใช้ค่าปลอดภัยแบบตรวจสอบก่อนเริ่มงาน และไม่เปิดสิทธิ์จาก Frontend";
  }
  if (els.operatorModePolicy) {
    const toolCount = operatorMode.guardrails.autoEligibleTools.length;
    const riskText = operatorMode.guardrails.maxRisk ? displayRisk(operatorMode.guardrails.maxRisk) : "ตามที่ Backend กำหนด";
    els.operatorModePolicy.textContent = autoExecutionActive
      ? `Backend ยืนยันงานอัตโนมัติ ${toolCount} เครื่องมือ • ระดับความเสี่ยงสูงสุด ${riskText} • ทุกงานมี Mission, Audit และ Report`
      : "Frontend ไม่จัดประเภทเครื่องมือและไม่ข้าม Approval Gate สิทธิ์ทั้งหมดตัดสินโดย Backend";
  }
  if (els.operatorModeToggle) {
    els.operatorModeToggle.disabled = operatorMode.inFlight || !operatorMode.backendAvailable;
    els.operatorModeToggle.textContent = operatorMode.inFlight
      ? "กำลังบันทึกที่ Backend..."
      : isAutoMode
        ? "เปลี่ยนเป็นโหมดจำกัดสิทธิ์"
        : operatorMode.backendAvailable
          ? "เปิด Full Access"
          : "รอการเชื่อมต่อ Backend";
  }
}

function setOperatorModePanelOpen(open) {
  if (!els.operatorModePanel || !els.operatorModeButton) return;
  const nextOpen = Boolean(open);
  els.operatorModePanel.hidden = !nextOpen;
  els.operatorModeButton.setAttribute("aria-expanded", String(nextOpen));
  if (nextOpen) setAgentCollaborationPanelOpen(false);
}

async function refreshOperatorMode() {
  if (state.operatorMode.inFlight) return null;
  state.operatorMode.inFlight = true;
  renderOperatorModeControl();
  try {
    const payload = await fetchJson(OPERATOR_MODE_ENDPOINT);
    const normalized = normalizeOperatorModePayload(payload);
    state.operatorMode = {
      ...state.operatorMode,
      ...normalized,
      inFlight: false,
      timer: state.operatorMode.timer,
      visibilityHandlerBound: state.operatorMode.visibilityHandlerBound,
    };
    return normalized;
  } catch {
    state.operatorMode = {
      ...state.operatorMode,
      mode: "manual_guarded",
      labelTh: "ตรวจสอบก่อนเริ่มงาน",
      autoExecute: false,
      backendAvailable: false,
      fallback: true,
      inFlight: false,
    };
    return null;
  } finally {
    state.operatorMode.inFlight = false;
    renderOperatorModeControl();
  }
}

async function setOperatorMode(mode) {
  if (!["auto_guarded", "manual_guarded"].includes(mode) || state.operatorMode.inFlight) return null;
  state.operatorMode.inFlight = true;
  renderOperatorModeControl();
  try {
    const payload = await postJson(OPERATOR_MODE_ENDPOINT, { mode });
    const normalized = normalizeOperatorModePayload(payload);
    state.operatorMode = {
      ...state.operatorMode,
      ...normalized,
      inFlight: false,
      timer: state.operatorMode.timer,
      visibilityHandlerBound: state.operatorMode.visibilityHandlerBound,
    };
    addBridgeEvent("เปลี่ยนโหมด Agent แล้ว", normalized.mode === "auto_guarded"
      ? "Backend เปิดงานอัตโนมัติที่ผ่านเกณฑ์ใน Workspace โดยยังคงระบบป้องกันงานนอกขอบเขตและงานเสี่ยง"
      : "Backend เปลี่ยนเป็นตรวจสอบก่อนเริ่มงาน");
    updateDecisionLog(normalized.mode === "auto_guarded"
      ? "เปิดโหมดอัตโนมัติใน Workspace แล้ว สิทธิ์จริงยังคงถูกตรวจโดย Backend"
      : "เปลี่ยนเป็นโหมดตรวจสอบก่อนเริ่มงานแล้ว");
    await loadBridgeMissions({ replaceEvents: false, persist: false });
    return normalized;
  } catch (error) {
    addBridgeEvent("เปลี่ยนโหมดไม่สำเร็จ", error.message || "Backend ไม่รับการเปลี่ยนโหมด");
    updateDecisionLog("Backend ไม่รับการเปลี่ยนโหมด จึงคงค่าปลอดภัยเดิมไว้");
    return null;
  } finally {
    state.operatorMode.inFlight = false;
    renderOperatorModeControl();
  }
}

function startOperatorModePolling() {
  renderOperatorModeControl();
  void refreshOperatorMode();
  if (!state.operatorMode.timer) {
    state.operatorMode.timer = window.setInterval(() => {
      if (document.visibilityState === "visible") void refreshOperatorMode();
    }, OPERATOR_MODE_POLL_MS);
  }
  if (!state.operatorMode.visibilityHandlerBound) {
    document.addEventListener("visibilitychange", () => {
      if (document.visibilityState === "visible") void refreshOperatorMode();
    });
    state.operatorMode.visibilityHandlerBound = true;
  }
}

function normalizeAgentCollaborationPayload(payload) {
  const source = payload?.collaboration && typeof payload.collaboration === "object"
    ? payload.collaboration
    : payload;
  if (!source || typeof source !== "object" || Array.isArray(source)) {
    throw new Error("invalid_agent_collaboration_response");
  }
  const statusValue = String(source.status || "disabled").trim().toLowerCase();
  const status = ["loading", "disabled", "scheduled", "paused", "starting", "running"].includes(statusValue)
    ? statusValue
    : "paused";
  const boundedInteger = (value, fallback, minimum, maximum) => {
    const numeric = Number(value);
    return Number.isFinite(numeric)
      ? Math.max(minimum, Math.min(maximum, Math.trunc(numeric)))
      : fallback;
  };
  const safeTime = (value, fallback) => (
    /^(?:[01]\d|2[0-3]):[0-5]\d$/.test(String(value || "")) ? String(value) : fallback
  );
  return {
    status,
    enabled: source.enabled === true,
    topic: safeDashboardDisplayText(source.topic, ""),
    timezone: "Asia/Bangkok",
    startTime: safeTime(source.startTime, "09:00"),
    endTime: safeTime(source.endTime, "18:00"),
    intervalMinutes: boundedInteger(source.intervalMinutes, 120, 30, 1440),
    maxTurns: boundedInteger(source.maxTurns, 3, 2, 4),
    maxDailyRuns: boundedInteger(source.maxDailyRuns, 3, 1, 6),
    dailyRunCount: boundedInteger(source.dailyRunCount, 0, 0, 1000),
    minRemainingPercent: boundedInteger(source.minRemainingPercent, 30, 10, 80),
    participants: Array.isArray(source.participants)
      ? source.participants.filter((item) => typeof item === "string" && /^[a-z0-9_]{2,80}$/.test(item)).slice(0, 4)
      : [],
    nextRunAt: typeof source.nextRunAt === "string" ? source.nextRunAt : null,
    pausedReason: typeof source.pausedReason === "string" ? source.pausedReason.slice(0, 80) : null,
    messageTh: safeDashboardDisplayText(source.messageTh, "รอสถานะจาก Backend"),
    remainingPercent: Number.isFinite(Number(source.remainingPercent))
      ? Math.max(0, Math.min(100, Number(source.remainingPercent)))
      : null,
    activeMeetingId: typeof source.activeMeetingId === "string" ? source.activeMeetingId : null,
    activeMissionId: typeof source.activeMissionId === "string" ? source.activeMissionId : null,
    lastMeetingId: typeof source.lastMeetingId === "string" ? source.lastMeetingId : null,
    lastRunAt: typeof source.lastRunAt === "string" ? source.lastRunAt : null,
    lastCompletedAt: typeof source.lastCompletedAt === "string" ? source.lastCompletedAt : null,
    lastStatus: typeof source.lastStatus === "string" ? source.lastStatus.slice(0, 40) : null,
    backendAvailable: true,
  };
}

function setCollaborationSelectValue(select, value, label) {
  if (!select) return;
  const stringValue = String(value);
  if (![...select.options].some((option) => option.value === stringValue)) {
    const option = document.createElement("option");
    option.value = stringValue;
    option.textContent = label;
    select.appendChild(option);
  }
  select.value = stringValue;
}

function renderAgentCollaborationControl() {
  if (!els.agentCollabControl) return;
  const collaboration = state.agentCollaboration;
  const visualState = collaboration.inFlight ? "working" : collaboration.status;
  const labels = {
    loading: "กำลังตรวจสอบ...",
    disabled: "ปิดอยู่",
    scheduled: "เปิดตามเวลา",
    paused: "พักอัตโนมัติ",
    starting: "กำลังเริ่มประชุม",
    running: "กำลังประชุม",
    working: "กำลังบันทึก...",
  };
  const statusLabels = {
    disabled: "ปิด",
    scheduled: "พร้อมตามเวลา",
    paused: "พักไว้ก่อน",
    starting: "กำลังเริ่ม",
    running: "กำลังคุย",
    loading: "กำลังตรวจ",
    working: "กำลังบันทึก",
  };
  els.agentCollabControl.dataset.state = visualState;
  if (els.agentCollabLabel) els.agentCollabLabel.textContent = labels[visualState] || "พักอัตโนมัติ";
  if (els.agentCollabPanelTitle) {
    els.agentCollabPanelTitle.textContent = collaboration.enabled
      ? `ช่วง ${collaboration.startTime}-${collaboration.endTime} น.`
      : "ยังไม่เปิดการประชุมอัตโนมัติ";
  }
  if (els.agentCollabStateBadge) {
    els.agentCollabStateBadge.dataset.state = visualState;
    els.agentCollabStateBadge.textContent = statusLabels[visualState] || "พักไว้ก่อน";
  }
  if (els.agentCollabMessage) {
    els.agentCollabMessage.textContent = collaboration.messageTh || "รอสถานะจาก Backend";
  }
  if (!collaboration.editing) {
    if (els.agentCollabTopic) els.agentCollabTopic.value = collaboration.topic;
    if (els.agentCollabStartTime) els.agentCollabStartTime.value = collaboration.startTime;
    if (els.agentCollabEndTime) els.agentCollabEndTime.value = collaboration.endTime;
    setCollaborationSelectValue(
      els.agentCollabInterval,
      collaboration.intervalMinutes,
      `ทุก ${collaboration.intervalMinutes} นาที`,
    );
    setCollaborationSelectValue(els.agentCollabMaxTurns, collaboration.maxTurns, `${collaboration.maxTurns} รอบ`);
    setCollaborationSelectValue(els.agentCollabMaxDailyRuns, collaboration.maxDailyRuns, `${collaboration.maxDailyRuns} ครั้ง`);
    setCollaborationSelectValue(
      els.agentCollabMinRemaining,
      collaboration.minRemainingPercent,
      `อย่างน้อย ${collaboration.minRemainingPercent}%`,
    );
  }
  if (els.agentCollabUsage) {
    els.agentCollabUsage.textContent = `วันนี้ ${collaboration.dailyRunCount}/${collaboration.maxDailyRuns} ครั้ง`;
  }
  if (els.agentCollabNextRun) {
    els.agentCollabNextRun.textContent = collaboration.nextRunAt
      ? `รอบถัดไป ${formatThaiDateTime(collaboration.nextRunAt)}`
      : collaboration.enabled
        ? "รอ Backend คำนวณรอบถัดไป"
        : "ยังไม่เปิดตาราง";
  }
  const disabled = collaboration.inFlight || !collaboration.backendAvailable;
  if (els.agentCollabSave) els.agentCollabSave.disabled = disabled;
  if (els.agentCollabRunNow) {
    els.agentCollabRunNow.disabled = disabled || ["starting", "running"].includes(collaboration.status);
    els.agentCollabRunNow.textContent = collaboration.status === "running" ? "กำลังประชุม..." : "ประชุมตอนนี้";
  }
  if (els.agentCollabToggle) {
    els.agentCollabToggle.disabled = disabled;
    els.agentCollabToggle.textContent = collaboration.enabled ? "ปิดอัตโนมัติ" : "เปิดอัตโนมัติ";
  }
}

function setAgentCollaborationPanelOpen(open) {
  if (!els.agentCollabPanel || !els.agentCollabButton) return;
  const nextOpen = Boolean(open);
  els.agentCollabPanel.hidden = !nextOpen;
  els.agentCollabButton.setAttribute("aria-expanded", String(nextOpen));
  if (nextOpen) setOperatorModePanelOpen(false);
}

function collaborationOwnsOfficeVisuals() {
  const collaboration = state.agentCollaboration;
  return Boolean(
    collaboration.enabled
    || collaboration.inFlight
    || collaboration.activeMeetingId
    || collaboration.lastVisualMeetingId
    || ["loading", "starting", "running"].includes(collaboration.status)
  );
}

function syncAgentCollaborationVisual(previous, current) {
  const meetingId = current.activeMeetingId;
  if (current.status === "running" && meetingId && state.agentCollaboration.lastVisualMeetingId !== meetingId) {
    state.agentCollaboration.lastVisualMeetingId = meetingId;
    const participants = [...new Set(["manager", ...current.participants])].filter((agentId) => getOfficeAgent(agentId));
    state.agentCollaboration.activeVisualParticipantIds = participants;
    participants.forEach((agentId) => {
      routeAgentToTargetId(agentId, getAgentMeetingSeatTargetId(agentId), "กำลังประชุมผ่าน Codex", {
        persist: false,
        select: false,
      });
      setAgentSpeech(agentId, "กำลังร่วมประชุมผ่าน Codex เพื่อช่วยกันปรับผลลัพธ์ครับ", "meeting");
    });
    addBridgeEvent("Agent เริ่มประชุมกันแล้ว", "การประชุมนี้ใช้ Codex จริงแบบปิด Tool และมี Rate Guard");
  }
  const confirmedMeetingEnded = Boolean(
    current.backendAvailable
    && !current.activeMeetingId
    && !["starting", "running"].includes(current.status)
    && state.agentCollaboration.lastVisualMeetingId
  );
  if (confirmedMeetingEnded) {
    const participants = state.agentCollaboration.activeVisualParticipantIds.length
      ? state.agentCollaboration.activeVisualParticipantIds
      : [...new Set(["manager", ...current.participants])].filter((agentId) => getOfficeAgent(agentId));
    participants.forEach((agentId) => {
      const agent = getOfficeAgent(agentId);
      const targetId = agent?.homeTarget || agent?.defaultTarget || "mission_strategy_table";
      routeAgentToTargetId(agentId, targetId, agentId === "manager" ? "กำลังส่งสรุปไปโต๊ะ Mission" : "กลับจุดทำงาน", {
        persist: false,
        select: false,
      });
    });
    state.agentCollaboration.lastVisualMeetingId = null;
    state.agentCollaboration.activeVisualParticipantIds = [];
    void loadBridgeMissions({ replaceEvents: false, persist: false });
    void loadMemoryStatus({ recordEvent: false });
  }
}

async function refreshAgentCollaboration() {
  if (state.agentCollaboration.inFlight) return null;
  try {
    const payload = await fetchJson(AGENT_COLLABORATION_ENDPOINT);
    const normalized = normalizeAgentCollaborationPayload(payload);
    const previous = { ...state.agentCollaboration };
    state.agentCollaboration = {
      ...state.agentCollaboration,
      ...normalized,
      inFlight: false,
      timer: state.agentCollaboration.timer,
      visibilityHandlerBound: state.agentCollaboration.visibilityHandlerBound,
      editing: state.agentCollaboration.editing,
      lastVisualMeetingId: state.agentCollaboration.lastVisualMeetingId,
      activeVisualParticipantIds: state.agentCollaboration.activeVisualParticipantIds,
    };
    renderAgentCollaborationControl();
    syncAgentCollaborationVisual(previous, state.agentCollaboration);
    return normalized;
  } catch {
    const activeStatus = ["starting", "running"].includes(state.agentCollaboration.status)
      ? state.agentCollaboration.status
      : null;
    state.agentCollaboration = {
      ...state.agentCollaboration,
      status: activeStatus || "paused",
      backendAvailable: false,
      messageTh: activeStatus
        ? "การเชื่อมต่อสถานะสะดุดชั่วคราว กำลังรักษาตำแหน่งประชุมไว้จนกว่า Backend จะยืนยัน"
        : "ยังอ่านตารางประชุมจาก Backend ไม่ได้",
    };
    renderAgentCollaborationControl();
    return null;
  }
}

function collaborationFormPayload() {
  return {
    topic: String(els.agentCollabTopic?.value || "").trim(),
    startTime: String(els.agentCollabStartTime?.value || ""),
    endTime: String(els.agentCollabEndTime?.value || ""),
    intervalMinutes: Number(els.agentCollabInterval?.value || 120),
    maxTurns: Number(els.agentCollabMaxTurns?.value || 3),
    maxDailyRuns: Number(els.agentCollabMaxDailyRuns?.value || 3),
    minRemainingPercent: Number(els.agentCollabMinRemaining?.value || 30),
  };
}

async function saveAgentCollaborationSchedule(payload) {
  if (state.agentCollaboration.inFlight) return null;
  state.agentCollaboration.inFlight = true;
  renderAgentCollaborationControl();
  try {
    const response = await postJson(AGENT_COLLABORATION_ENDPOINT, payload);
    const normalized = normalizeAgentCollaborationPayload(response);
    state.agentCollaboration = {
      ...state.agentCollaboration,
      ...normalized,
      editing: false,
      inFlight: false,
    };
    renderAgentCollaborationControl();
    addBridgeEvent("บันทึกเวลาประชุม Agent แล้ว", "Backend จะตรวจ Full Access, ช่วงเวลา และ Rate Limit ก่อนทุกครั้ง");
    return normalized;
  } catch (error) {
    state.agentCollaboration.messageTh = safeDashboardDisplayText(
      error?.body?.messageTh || error?.message,
      "บันทึกตารางประชุมไม่สำเร็จ",
    );
    return null;
  } finally {
    state.agentCollaboration.inFlight = false;
    renderAgentCollaborationControl();
  }
}

async function runAgentCollaborationNow() {
  if (state.agentCollaboration.inFlight) return null;
  state.agentCollaboration.inFlight = true;
  state.agentCollaboration.messageTh = "กำลังให้ Backend ตรวจ Rate Limit และคิว Codex";
  renderAgentCollaborationControl();
  try {
    const response = await postJson(AGENT_COLLABORATION_RUN_ENDPOINT, {});
    const normalized = normalizeAgentCollaborationPayload(response);
    state.agentCollaboration = {
      ...state.agentCollaboration,
      ...normalized,
      inFlight: false,
    };
    addBridgeEvent("ส่งคำขอประชุม Agent แล้ว", safeDashboardDisplayText(response.messageTh, "Backend รับคำขอแล้ว"));
    window.setTimeout(() => void refreshAgentCollaboration(), 1200);
    return normalized;
  } catch (error) {
    state.agentCollaboration.messageTh = safeDashboardDisplayText(
      error?.body?.messageTh || error?.message,
      "ยังเริ่มประชุมไม่ได้",
    );
    state.agentCollaboration.status = "paused";
    return null;
  } finally {
    state.agentCollaboration.inFlight = false;
    renderAgentCollaborationControl();
  }
}

function startAgentCollaborationPolling() {
  renderAgentCollaborationControl();
  void refreshAgentCollaboration();
  if (!state.agentCollaboration.timer) {
    state.agentCollaboration.timer = window.setInterval(() => {
      if (document.visibilityState === "visible" && !state.agentCollaboration.editing) {
        void refreshAgentCollaboration();
      }
    }, AGENT_COLLABORATION_POLL_MS);
  }
  if (!state.agentCollaboration.visibilityHandlerBound) {
    document.addEventListener("visibilitychange", () => {
      if (document.visibilityState === "visible" && !state.agentCollaboration.editing) {
        void refreshAgentCollaboration();
      }
    });
    state.agentCollaboration.visibilityHandlerBound = true;
  }
}

const potentialSecretPatterns = [
  /\b(?:api[_ -]?key|token|password|passwd|secret|authorization|cookie|bot[_ -]?token|broker[_ -]?password|database[_ -]?url|connection[_ -]?string|private[_ -]?key|aws[_ -]?secret[_ -]?access[_ -]?key|github[_ -]?token)\b["']?\s*[:=]\s*["']?[^\s,;}"']{4,}/i,
  /\bbearer\s+[a-z0-9._~+/-]{12,}/i,
  /\bsk-[a-z0-9_-]{16,}\b/i,
  /\b\d{6,12}:[a-z0-9_-]{20,}\b/i,
  /\beyJ[a-z0-9_-]{12,}\.[a-z0-9_-]{12,}\.[a-z0-9_-]{8,}\b/i,
  /\b(?:gh[pousr]_[a-z0-9]{20,}|xox[baprs]-[a-z0-9-]{16,})\b/i,
];

function containsPotentialSecret(value = "") {
  return potentialSecretPatterns.some((pattern) => pattern.test(String(value || "")));
}

function blockSecretIntent(prompt, scopeType = "agent", scopeId = "risk_guard") {
  if (!containsPotentialSecret(prompt)) return false;
  state.modal.lastPrompt = "";
  if (els.modalCommandInput) els.modalCommandInput.value = "";
  if (els.managerCommandInput) els.managerCommandInput.value = "";
  pushChatLine({
    scopeType,
    scopeId,
    speaker: "Risk Guard",
    text: "ตรวจพบข้อความที่อาจมี Token รหัสผ่าน หรือข้อมูลลับ จึงไม่บันทึกและไม่ส่งไปยัง Backend กรุณาส่งเฉพาะคำสั่งที่ไม่มีข้อมูลลับครับ",
    side: "agent",
  });
  updateDecisionLog("Risk Guard หยุดข้อความที่อาจมีข้อมูลลับก่อนบันทึก");
  addBridgeEvent("Risk Guard ป้องกันข้อมูลลับ", "ข้อความที่อาจมีรหัสผ่านหรือข้อมูลยืนยันตัวตนถูกหยุดก่อนส่งไป Backend");
  return true;
}

function loadLocalSessionSnapshot() {
  try {
    const raw = window.localStorage.getItem(SESSION_STORAGE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

function selectNewestSessionSnapshot(localSession, backendSession) {
  if (!backendSession) return localSession;
  if (!localSession) return backendSession;
  const localDashboardVersion = Number(localSession.modal?.signalDashboardVersion);
  const backendDashboardVersion = Number(backendSession.modal?.signalDashboardVersion);
  if (
    Number.isFinite(localDashboardVersion)
    && Number.isFinite(backendDashboardVersion)
    && localDashboardVersion !== backendDashboardVersion
  ) {
    return localDashboardVersion > backendDashboardVersion ? localSession : backendSession;
  }
  const localSavedAt = Date.parse(localSession.savedAt || "");
  const backendSavedAt = Date.parse(backendSession.savedAt || "");
  if (Number.isFinite(localSavedAt) && !Number.isFinite(backendSavedAt)) return localSession;
  if (Number.isFinite(localSavedAt) && localSavedAt > backendSavedAt) return localSession;
  return backendSession;
}

async function loadSessionSnapshot() {
  const localSession = loadLocalSessionSnapshot();
  try {
    const payload = await fetchJson(UI_SESSION_ENDPOINT, { timeoutMs: 1500 });
    return selectNewestSessionSnapshot(localSession, payload.session);
  } catch (error) {
    reportBootResourceFailure(UI_SESSION_ENDPOINT, error);
    return localSession;
  }
}

function savedOfficeAgentsOverlap(snapshot) {
  if (!snapshot || !Array.isArray(snapshot.officeAgents)) return false;
  const restored = new Map(
    snapshot.officeAgents
      .filter((agent) => agent?.id)
      .map((agent) => [agent.id, agent]),
  );
  const points = officeAgentDefinitions
    .map((definition) => {
      const saved = restored.get(definition.id);
      const source = saved || (definition.id === state.agent.id ? snapshot.agent : null);
      const x = Number(source?.x);
      const y = Number(source?.y);
      return Number.isFinite(x) && Number.isFinite(y)
        ? { id: definition.id, x, y }
        : null;
    })
    .filter(Boolean);

  return points.some((point, index) => (
    points.slice(index + 1).some((candidate) => (
      Math.abs(point.x - candidate.x) < OFFICE_AGENT_OVERLAP_X
      && Math.abs(point.y - candidate.y) < OFFICE_AGENT_OVERLAP_Y
    ))
  ));
}

function migrateOfficeSessionLayout(snapshot) {
  if (!snapshot || typeof snapshot !== "object" || Array.isArray(snapshot)) {
    return { snapshot, migrated: false };
  }
  const staleLayout = Number(snapshot.officeLayoutVersion) !== OFFICE_LAYOUT_VERSION;
  const overlappingLayout = savedOfficeAgentsOverlap(snapshot);
  const staleSignalDashboard = (
    Number(snapshot.modal?.signalDashboardVersion) !== SIGNAL_DASHBOARD_VERSION
  );
  const migrateOfficeLayout = staleLayout || overlappingLayout;
  if (!migrateOfficeLayout && !staleSignalDashboard) {
    return { snapshot, migrated: false };
  }

  const migratedAgent = snapshot.agent && typeof snapshot.agent === "object"
    ? { ...snapshot.agent }
    : snapshot.agent;
  if (migrateOfficeLayout && migratedAgent) {
    delete migratedAgent.x;
    delete migratedAgent.y;
  }
  const migratedOfficeAgents = migrateOfficeLayout && Array.isArray(snapshot.officeAgents)
    ? snapshot.officeAgents.map((agent) => {
        if (!agent || typeof agent !== "object") return agent;
        const migrated = { ...agent };
        delete migrated.x;
        delete migrated.y;
        delete migrated.currentTarget;
        return migrated;
      })
    : snapshot.officeAgents;
  const migratedModal = snapshot.modal && typeof snapshot.modal === "object"
    ? { ...snapshot.modal }
    : {};
  if (staleSignalDashboard) {
    const legacySignalTab = String(migratedModal.signalTab || "");
    const legacyDeepTab = SIGNAL_DEEP_ANALYSIS_TABS.includes(legacySignalTab)
      ? legacySignalTab
      : null;
    migratedModal.signalDashboardVersion = SIGNAL_DASHBOARD_VERSION;
    migratedModal.signalTab = legacyDeepTab
      ? "live_analysis"
      : (SIGNAL_CONSENSUS_TABS.includes(legacySignalTab) ? legacySignalTab : "daily_summary");
    migratedModal.signalLiveTab = legacyDeepTab || (
      SIGNAL_LIVE_ANALYSIS_TABS.includes(migratedModal.signalLiveTab)
        ? migratedModal.signalLiveTab
        : "chart_overview"
    );
    migratedModal.signalChartDisplayBars = SIGNAL_CHART_DEFAULT_DISPLAY_BARS;
    migratedModal.signalChartOffsetBars = 0;
    migratedModal.signalChartOverlays = [...SIGNAL_CHART_DEFAULT_OVERLAYS];
    migratedModal.signalOverlayPickerOpen = false;
    migratedModal.signalIndicatorFilter = "all";
    migratedModal.signalDeepTechnicalQuery = "";
    migratedModal.signalDeepTechnicalIndicator = "all";
    migratedModal.signalDeepTechnicalRange = "300";
  }

  return {
    snapshot: {
      ...snapshot,
      officeLayoutVersion: OFFICE_LAYOUT_VERSION,
      agent: migratedAgent,
      officeAgents: migratedOfficeAgents,
      modal: migratedModal,
    },
    migrated: true,
  };
}

function saveSessionSnapshot() {
  if (!state.data) return;
  try {
    const snapshot = {
      savedAt: new Date().toISOString(),
      officeLayoutVersion: OFFICE_LAYOUT_VERSION,
      activeObject: state.activeObject,
      panelObject: state.panelObject,
      fitMode: state.fitMode,
      visibleLayers: [...state.visibleLayers],
      selectedAgentId: state.selectedAgentId,
      agent: {
        x: state.agent.x,
        y: state.agent.y,
        direction: state.agent.direction,
      },
      officeAgents: state.officeAgents.map((agent) => ({
        id: agent.id,
        x: agent.x,
        y: agent.y,
        direction: agent.direction,
        currentTarget: agent.currentTarget,
      })),
      modal: {
        type: state.modal.type,
        id: state.modal.id,
        activeTab: state.modal.activeTab,
        signalDashboardVersion: SIGNAL_DASHBOARD_VERSION,
        signalTab: state.modal.signalTab,
        signalLiveTab: state.modal.signalLiveTab,
        signalChartDisplayBars: state.modal.signalChartDisplayBars,
        signalChartOffsetBars: state.modal.signalChartOffsetBars,
        signalChartOverlays: [...state.modal.signalChartOverlays],
        signalOverlayPickerOpen: state.modal.signalOverlayPickerOpen,
        signalIndicatorFilter: state.modal.signalIndicatorFilter,
        signalDeepTechnicalQuery: state.modal.signalDeepTechnicalQuery,
        signalDeepTechnicalIndicator: state.modal.signalDeepTechnicalIndicator,
        signalDeepTechnicalRange: state.modal.signalDeepTechnicalRange,
        signalHistoryQuery: state.modal.signalHistoryQuery,
        signalHistoryType: state.modal.signalHistoryType,
        signalHistoryStatus: state.modal.signalHistoryStatus,
        workflowTabs: { ...state.modal.workflowTabs },
        selectedMissionId: state.modal.selectedMissionId,
        showArchived: state.modal.showArchived,
        searchText: state.modal.searchText,
        pendingRun: state.modal.pendingRun ? {
          missionId: state.modal.pendingRun.missionId || null,
          agentId: state.modal.pendingRun.agentId || null,
          toolId: state.modal.pendingRun.toolId || null,
        } : null,
      },
      agentChatSessions: { ...state.agentChat.sessionIds },
      memoryStatus: state.memoryStatus,
      bridge: state.bridge,
    };
    try {
      window.localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(snapshot));
    } catch {
      // The backend session endpoint is the durable fallback when local storage is unavailable.
    }
    window.clearTimeout(state.sessionSaveTimer);
    state.sessionSaveTimer = window.setTimeout(() => {
      postJson(UI_SESSION_ENDPOINT, { session: snapshot }).catch(() => {});
    }, 220);
  } catch {
    // Session persistence is a convenience layer; the dashboard must still work without it.
  }
}

function clearSessionSnapshot() {
  try {
    window.localStorage.removeItem(SESSION_STORAGE_KEY);
  } catch {
    // Ignore storage errors.
  }
}

function applySessionSnapshot(snapshot) {
  if (!snapshot) return;

  if (Array.isArray(snapshot.visibleLayers)) {
    const knownLayerIds = new Set(state.data.layers.map((layer) => layer.id));
    const restoredLayers = snapshot.visibleLayers.filter((layerId) => knownLayerIds.has(layerId));
    if (restoredLayers.length) state.visibleLayers = new Set(restoredLayers);
  }

  if (snapshot.fitMode === "cover") {
    state.fitMode = "cover";
    els.stage.classList.add("cover");
  } else {
    state.fitMode = "contain";
    els.stage.classList.remove("cover");
  }

  if (snapshot.bridge) {
    state.bridge = {
      ...state.bridge,
      ...snapshot.bridge,
      codex: {
        ...state.bridge.codex,
        ...(snapshot.bridge.codex || {}),
      },
      mcp: {
        ...state.bridge.mcp,
        ...(snapshot.bridge.mcp || {}),
      },
    };
  }

  if (snapshot.agent) {
    state.agent.x = Number(snapshot.agent.x ?? state.agent.x);
    state.agent.y = Number(snapshot.agent.y ?? state.agent.y);
    state.agent.direction = snapshot.agent.direction || state.agent.direction;
  }

  state.bridgeEvents = [];
  state.officeEventLog = [];
  state.meetingTranscript = [];
  state.chatLog = [];
  if (snapshot.agentChatSessions && typeof snapshot.agentChatSessions === "object" && !Array.isArray(snapshot.agentChatSessions)) {
    const knownAgentIds = new Set(officeAgentDefinitions.map((definition) => definition.id));
    state.agentChat.sessionIds = Object.fromEntries(
      Object.entries(snapshot.agentChatSessions)
        .filter(([agentId, sessionId]) => (
          knownAgentIds.has(agentId)
          && typeof sessionId === "string"
          && /^[a-zA-Z0-9][a-zA-Z0-9._:-]{0,159}$/.test(sessionId)
        ))
        .slice(0, EXPECTED_OFFICE_AGENT_COUNT),
    );
  }
  if (snapshot.modal) {
    state.modal = {
      ...state.modal,
      type: snapshot.modal.type || null,
      id: snapshot.modal.id || null,
      activeTab: snapshot.modal.activeTab || "chat",
      signalTab: Number(snapshot.modal.signalDashboardVersion) === SIGNAL_DASHBOARD_VERSION
        && SIGNAL_CONSENSUS_TABS.includes(snapshot.modal.signalTab)
        ? snapshot.modal.signalTab
        : "daily_summary",
      signalLiveTab: Number(snapshot.modal.signalDashboardVersion) === SIGNAL_DASHBOARD_VERSION
        && SIGNAL_LIVE_ANALYSIS_TABS.includes(snapshot.modal.signalLiveTab)
        ? snapshot.modal.signalLiveTab
        : "chart_overview",
      signalChartDisplayBars: SIGNAL_CHART_DISPLAY_BAR_OPTIONS.includes(
        Number(snapshot.modal.signalChartDisplayBars),
      )
        ? Number(snapshot.modal.signalChartDisplayBars)
        : SIGNAL_CHART_DEFAULT_DISPLAY_BARS,
      signalChartOffsetBars: Math.max(0, Math.floor(Number(snapshot.modal.signalChartOffsetBars) || 0)),
      signalChartOverlays: Array.isArray(snapshot.modal.signalChartOverlays)
        ? snapshot.modal.signalChartOverlays
          .filter((id) => SIGNAL_CHART_OVERLAY_DEFINITIONS.some((definition) => definition.id === id))
          .slice(0, SIGNAL_CHART_OVERLAY_LIMIT)
        : [...SIGNAL_CHART_DEFAULT_OVERLAYS],
      signalOverlayPickerOpen: snapshot.modal.signalOverlayPickerOpen === true,
      signalIndicatorFilter: ["all", "technical", "price_action"].includes(snapshot.modal.signalIndicatorFilter)
        ? snapshot.modal.signalIndicatorFilter
        : "all",
      signalDeepTechnicalQuery: String(snapshot.modal.signalDeepTechnicalQuery || "").slice(0, 100),
      signalDeepTechnicalIndicator: String(snapshot.modal.signalDeepTechnicalIndicator || "all").slice(0, 80),
      signalDeepTechnicalRange: ["60", "120", "180", "300", "all"].includes(
        String(snapshot.modal.signalDeepTechnicalRange || "300"),
      )
        ? String(snapshot.modal.signalDeepTechnicalRange || "300")
        : "300",
      signalHistoryQuery: String(snapshot.modal.signalHistoryQuery || ""),
      signalHistoryType: ["all", "mission", "report"].includes(snapshot.modal.signalHistoryType)
        ? snapshot.modal.signalHistoryType
        : "all",
      signalHistoryStatus: ["all", "active", "completed", "blocked"].includes(snapshot.modal.signalHistoryStatus)
        ? snapshot.modal.signalHistoryStatus
        : "all",
      workflowTabs: Object.fromEntries(
        Object.entries(snapshot.modal.workflowTabs || {})
          .filter(([propId, tabId]) => (
            WORKFLOW_DASHBOARD_PROP_IDS.includes(propId)
            && typeof tabId === "string"
            && /^[a-z0-9_-]{1,60}$/i.test(tabId)
          )),
      ),
      lastPrompt: "",
      selectedMissionId: snapshot.modal.selectedMissionId || null,
      showArchived: Boolean(snapshot.modal.showArchived),
      searchText: String(snapshot.modal.searchText || ""),
      pendingRun: snapshot.modal.pendingRun?.missionId ? {
        missionId: snapshot.modal.pendingRun.missionId,
        agentId: snapshot.modal.pendingRun.agentId || null,
        toolId: snapshot.modal.pendingRun.toolId || null,
      } : null,
    };
  }
  state.memoryStatus = snapshot.memoryStatus || state.memoryStatus;
  state.selectedAgentId = snapshot.selectedAgentId || state.selectedAgentId;
}

function restoreActivePanel(snapshot) {
  const requestedObject = snapshot?.panelObject || snapshot?.activeObject || state.data.defaultSelection || getInteractiveObjects()[0]?.id;
  if (isOfficeAgentId(requestedObject)) {
    showAgentPanel(requestedObject);
    return;
  }

  const hasObject = getInteractiveObjects().some((item) => item.id === requestedObject);
  selectObject(hasObject ? requestedObject : state.data.defaultSelection || getInteractiveObjects()[0]?.id);
}

function restoreSessionUi(snapshot) {
  if (!snapshot) return;
  if (state.bridgeEvents.length) {
    renderBridgeEvents(state.bridgeEvents, { persist: false });
  }
  updateBridgeLabel();
}

function resolveProjectAssetPath(path) {
  if (!path) return path;
  if (/^(https?:|data:|blob:|\/)/.test(path)) return path;

  const normalized = path.replace(/^\.?\//, "");
  if (!normalized.startsWith("assets/")) return path;

  const assetPath = normalized.replace(/^assets\//, "");
  if (assetPath.startsWith("custom-props") || assetPath.startsWith("prop-sheets")) {
    return `${PROJECT_ASSET_ROOT}/props/${assetPath}`;
  }
  if (assetPath.startsWith("navigation/")) {
    return `${PROJECT_ASSET_ROOT}/maps/command-room/${assetPath}`;
  }
  if (assetPath.startsWith("exact-scene-layers")) {
    return `${PROJECT_ASSET_ROOT}/maps/command-room/layers/${assetPath}`;
  }
  if (assetPath.startsWith("agents/")) {
    return `${PROJECT_ASSET_ROOT}/agents/legacy-prototype-agents/${assetPath.replace(/^agents\//, "")}`;
  }
  return `${PROJECT_ASSET_ROOT}/maps/command-room/${assetPath}`;
}

function resolveAgentPackagePath(path) {
  if (!path) return path;
  if (/^(https?:|data:|blob:|\/)/.test(path)) return path;
  return `${MANAGER_EXEC_ASSET_ROOT}/${path.replace(/^\.?\//, "")}`;
}

function withAgentAssetVersion(path) {
  if (!path || /^(data:|blob:)/.test(path)) return path;
  const joiner = path.includes("?") ? "&" : "?";
  return `${path}${joiner}asset=${encodeURIComponent(AGENT_ASSET_VERSION)}`;
}

async function loadAgentAnimationMap() {
  if (!state.agent.animationMapPath) return;
  try {
    const animationMap = await fetchJson(`${state.agent.animationMapPath}?v=${encodeURIComponent(AGENT_ASSET_VERSION)}`);
    state.agent.sprite.animationMap = animationMap;
    state.agent.frameImage = getResolvedAnimationFrame(animationMap, "status", "down", "idle") || MANAGER_STATIC_FRAME;
  } catch (error) {
    reportBootResourceFailure(state.agent.animationMapPath, error);
    console.warn("Manager animation map unavailable; using idle frame fallback.", error);
  }
}

function createAgentSpriteState() {
  return {
    type: "frames",
    animationMap: state.agent.sprite.animationMap,
    currentFrames: [],
    mode: "status",
    frame: 0,
    row: 0,
  };
}

function initializeOfficeAgents(snapshot = null) {
  const restored = new Map(
    (snapshot?.officeAgents || [])
      .filter((agent) => agent?.id)
      .map((agent) => [agent.id, agent]),
  );

  state.officeAgents = officeAgentDefinitions.map((definition) => {
    const saved = restored.get(definition.id) || {};
    const contract = state.agentRoster.find((item) => item.id === definition.id) || {};
    const display = AGENT_DISPLAY[definition.id] || {};
    const allowedSurfaces = Array.isArray(contract.allowed_surfaces)
      ? contract.allowed_surfaces
      : (Array.isArray(contract.allowed_tools) ? contract.allowed_tools : definition.tools);
    return {
      ...definition,
      name: display.name || contract.name || definition.name,
      role: display.role || contract.role || definition.role,
      summary: display.summary || contract.goal || definition.summary,
      contractName: contract.name || definition.name,
      legacyName: contract.legacy_name
        || AI_TRADE_COUNCIL_LEGACY_NAMES[definition.id]
        || definition.name,
      contractRole: contract.role || definition.role,
      allowedSurfaces,
      tools: allowedSurfaces,
      blockedActions: contract.blocked_actions || [],
      approvalRequiredActions: contract.approval_required_actions || [],
      creditBudget: contract.credit_budget || null,
      outputFormat: contract.output_format || null,
      x: Number(saved.x ?? definition.x),
      y: Number(saved.y ?? definition.y),
      w: Number(definition.w || 6.4),
      direction: saved.direction || "down",
      speedMs: 1,
      status: display.status || definition.status || "พร้อมรับคำสั่ง",
      currentTarget: saved.currentTarget || definition.homeTarget || definition.defaultTarget,
      visualState: "idle",
      image: definition.image,
      sprite: createAgentSpriteState(),
    };
  });

  const manager = getOfficeAgent(state.agent.id);
  if (manager) {
    syncManagerOfficeAgent(manager);
  }
  if (!isOfficeAgentId(state.selectedAgentId)) state.selectedAgentId = state.agent.id;
}

function syncManagerOfficeAgent(manager = getOfficeAgent(state.agent.id)) {
  if (!manager) return;
  manager.x = state.agent.x;
  manager.y = state.agent.y;
  manager.w = state.agent.w;
  manager.direction = state.agent.direction;
  manager.status = state.agent.status;
  manager.image = state.agent.frameImage;
}

function getOfficeAgent(agentId = state.selectedAgentId) {
  return state.officeAgents.find((agent) => agent.id === agentId) || null;
}

function isOfficeAgentId(id) {
  return Boolean(id && getOfficeAgent(id));
}

function getAgentNodeId(agentId) {
  return agentId === state.agent.id ? "hqManagerAgent" : `officeAgent-${agentId}`;
}

function getSelectedAgent() {
  return getOfficeAgent(state.selectedAgentId) || getOfficeAgent(state.agent.id);
}

function renderAgentSelector() {
  if (!els.agentSelector) return;
  els.agentSelector.innerHTML = "";
  state.officeAgents.forEach((agent) => {
    const option = document.createElement("option");
    option.value = agent.id;
    option.textContent = `${agent.name} - ${agent.role}`;
    els.agentSelector.appendChild(option);
  });
  els.agentSelector.value = state.selectedAgentId;
}

function setSelectedAgent(agentId) {
  if (!isOfficeAgentId(agentId)) return getSelectedAgent();
  state.selectedAgentId = agentId;
  if (els.agentSelector && els.agentSelector.value !== agentId) els.agentSelector.value = agentId;
  [...els.agentLayer.querySelectorAll(".agent-unit")].forEach((node) => {
    node.classList.toggle("active", node.dataset.agentId === agentId);
  });
  saveSessionSnapshot();
  return getOfficeAgent(agentId);
}

function updateAgentNodeState(agent) {
  const node = document.getElementById(getAgentNodeId(agent.id));
  if (!node) return;
  node.style.setProperty("--agent-x", agent.x.toFixed(3));
  node.style.setProperty("--agent-y", agent.y.toFixed(3));
  node.style.setProperty("--agent-w", agent.w.toFixed(3));
  node.style.setProperty("--agent-z", getDepthZ(agent.y));
  node.style.setProperty("--agent-speed", `${agent.speedMs || 1}ms`);
  node.dataset.status = agent.visualState || "idle";
  node.classList.remove("idle", "walking", "talking", "meeting", "working", "reporting");
  node.classList.add(agent.visualState || "idle");
  const bubble = node.querySelector(".agent-bubble");
  if (bubble) bubble.textContent = agent.status;
}

function recordOfficeEvent(title, detail, options = {}) {
  const event = {
    time: new Date().toISOString(),
    title,
    detail,
    agentId: options.agentId || state.selectedAgentId || state.agent.id,
    kind: options.kind || "office",
    missionId: options.missionId || null,
    targetId: options.targetId || null,
  };
  state.officeEventLog = [event, ...state.officeEventLog].slice(0, 30);
  if (options.persist !== false) postJson(AGENT_EVENTS_ENDPOINT, event).catch(() => {});
  if (options.bridgeEvent !== false) addBridgeEvent(title, detail);
  if (options.persist !== false) saveSessionSnapshot();
  return event;
}

const agentThaiSpeech = {
  manager: {
    idle: "ผมพร้อมรับเป้าหมายครับ เดี๋ยวผมแตกงานและเลือกคนที่เหมาะให้",
    task: "รับทราบครับ ผมจะแยกงานให้ Agent ผู้เชี่ยวชาญ แล้วติดตามผลกลับมา",
    meeting: "ผมกำลังเรียกประชุมที่โต๊ะวางแผนครับ",
    backend: "ถ้าจะรันงานจริง ผมจะส่งผ่าน Local Runner และรอการอนุมัติตามกฎครับ",
  },
  ceo: {
    idle: "ผมจะดูภาพรวมและอนุมัติงานที่มีความเสี่ยงเท่านั้น",
    task: "ขอดูเป้าหมายและความเสี่ยงก่อนอนุมัติครับ",
    meeting: "เชิญทีมสรุปแผนและข้อจำกัดมาได้เลย",
    backend: "งานที่แตะระบบจริงต้องมีเหตุผลและบันทึกตรวจสอบที่ชัดเจนครับ",
  },
  ea_developer: {
    idle: "ผมพร้อมดู EA, Indicator, MT4/MT5 และ compile log ครับ",
    task: "รับงานแล้วครับ ผมจะไปที่โรงงานสร้าง EA และ Indicator เพื่อดู Logic โค้ด และผล Compile",
    meeting: "ผมเข้าประชุมเพื่อรับสเปก EA ครับ",
    backend: "ถ้าต้องแก้ไฟล์จริง ให้ Manager Agent ส่งงานผ่าน Bridge และให้ Risk Guard ตรวจด้วยครับ",
  },
  backtest_analyst: {
    idle: "ผมคือ Price Action Consultant ครับ ถามได้เลยว่าทำไมผมจึงมองแนวโน้ม แนวรับแนวต้าน Liquidity หรือ SMC/HMC/ICT แบบนั้น",
    task: "รับงานแล้วครับ ผมจะอ่านแท่งเทียนที่ปิดแล้ว โครงสร้างราคา Trendline แนวรับแนวต้าน และหลักฐานบนกราฟเปล่าก่อนสรุป",
    meeting: "ผมจะนำมุมมอง Price Action พร้อมเหตุผลจากกราฟเปล่า และผล Backtest ที่เกี่ยวข้องเข้าประชุมครับ",
    backend: "ข้อมูลกราฟและไฟล์ Backtest ต้องผ่าน Backend ก่อนครับ จากนั้นผมจะอธิบายเหตุผลและจุดที่ควรระวังให้ตรวจสอบได้",
  },
  optimization_agent: {
    idle: "ผมคือ Technical Consultant ครับ ถามได้เลยว่าทำไมสัญญาณ แนวโน้ม โมเมนตัม หรือความผันผวนจึงสนับสนุนมุมมองนั้น",
    task: "รับงานแล้วครับ ผมจะตรวจ Indicator และค่าที่คำนวณจากแท่งปิด โดยแยกหลักฐาน Technical ออกจากความเห็นให้ชัดเจน",
    meeting: "ผมจะเข้าประชุมพร้อมมุมมอง Technical เหตุผลจาก Indicator และข้อควรระวังเรื่อง Parameter หรือ Overfit ครับ",
    backend: "ข้อมูล Technical และงาน Optimization ต้องผ่าน Backend ครับ ผมจะอธิบายที่มาของสัญญาณและบันทึกผลให้ตรวจสอบย้อนหลังได้",
  },
  vps_watch: {
    idle: "ผมกำลังเฝ้าดู VPS, latency, uptime, CPU/RAM และ terminal status ครับ",
    task: "รับงานตรวจระบบแล้วครับ ผมจะไปที่ Server Racks",
    meeting: "ผมจะรายงานสถานะ VPS และ Server ให้ทีมครับ",
    backend: "คำสั่ง Restart หรือเปลี่ยน Config ต้องรอการอนุมัติก่อนเสมอครับ",
  },
  telegram_ops: {
    idle: "ผมพร้อมเตรียมการแจ้งเตือนและข้อความสรุปสำหรับ Telegram ครับ",
    task: "รับงานแจ้งเตือนแล้วครับ ผมจะส่งสถานะกลับมาที่โต๊ะวางแผน Mission",
    meeting: "ผมจะเข้าประชุมพร้อมข้อความสรุปก่อนส่งจริงครับ",
    backend: "การส่งข้อความจริงต้องผ่านการอนุมัติ และห้ามเก็บ Token ไว้บนหน้าเว็บครับ",
  },
  risk_guard: {
    idle: "ผมกำลังดูแลข้อมูลลับ งาน Live Trading ข้อกำกับ และประตูอนุมัติครับ",
    task: "รับงานตรวจความเสี่ยงแล้วครับ ผมจะเช็คก่อนอนุมัติ",
    meeting: "ผมจะเข้าประชุมเพื่อดูจุดเสี่ยงและข้อห้ามครับ",
    backend: "งานเสี่ยงต้องผ่านผมก่อน และห้ามข้ามขั้นตอนอนุมัติครับ",
  },
  codex_mcp_operator: {
    idle: "ผมคือ News Consultant ครับ ถามได้เลยว่าข่าวไหนส่งผลระยะสั้น กลาง หรือยาว และเหตุใดแหล่งข้อมูลนั้นจึงเกี่ยวข้อง",
    task: "รับงานแล้วครับ ผมจะตรวจข่าวล่าสุด เวลาเผยแพร่ แหล่งอ้างอิง และแยกผลกระทบระยะสั้น กลาง และยาวให้ชัดเจน",
    meeting: "ผมจะนำสถานการณ์ล่าสุด แหล่งข้อมูล และข้อจำกัดของข่าวที่ยังยืนยันไม่ได้เข้าประชุมครับ",
    backend: "การค้นข่าวและเรียก Codex/MCP จะเกิดที่ Backend เท่านั้นครับ ผมจะอ้างอิงแหล่งข้อมูลและไม่สร้างข่าวสมมุติ",
  },
  mission_archivist: {
    idle: "ผมพร้อมค้น Memory บันทึกบทสนทนา และรายงานเก่า แล้วสรุปกลับเข้าประชุมครับ",
    task: "รับงานค้นคลังแล้วครับ ผมจะไปที่ตู้ข้อมูลย้อนหลังและเปิดดัชนี Memory",
    meeting: "ผมจะนำสรุปงานเก่าที่เกี่ยวข้องเข้าประชุมครับ",
    backend: "ผมค้นได้เฉพาะข้อมูลที่ไม่ใช่ข้อมูลลับ และจะสรุปก่อนนำกลับมาใช้ครับ",
  },
};

function getAgentSpeech(agentId, mode = "idle", fallback = "") {
  return agentThaiSpeech[agentId]?.[mode] || fallback || "พร้อมทำงานครับ สั่งงานมาได้เลย";
}

function setAgentSpeech(agentId, message, visualState = null) {
  const agent = getOfficeAgent(agentId);
  if (!agent) return;
  agent.status = message;
  if (visualState) agent.visualState = visualState;
  updateAgentNodeState(agent);
  if (agent.id === state.agent.id) {
    state.agent.status = message;
    if (visualState) state.agent.visualState = visualState;
    applyAgentPosition(false);
  }
  if (state.modal.open && state.modal.type === "agent" && state.modal.id === agent.id) renderGameModal();
}

function pushChatLine({ scopeType = state.modal.type || "agent", scopeId = state.modal.id || state.agent.id, speaker = "ระบบ", text = "", side = "agent", persist = true } = {}) {
  if (!text) return null;
  const line = {
    id: `chat-${Date.now()}-${Math.round(Math.random() * 1000)}`,
    time: new Date().toISOString(),
    scopeType,
    scopeId,
    speaker,
    text,
    side,
  };
  state.chatLog = [line, ...state.chatLog].slice(0, 100);
  if (persist) saveSessionSnapshot();
  return line;
}

function persistModalTurn(title, summary, participants = []) {
  if (containsPotentialSecret(`${title} ${summary}`)) return;
  postJson(`${MEETINGS_ENDPOINT}/turn`, {
    title,
    participants,
    summary,
    messages: state.chatLog
      .filter((line) => line.scopeType === state.modal.type && line.scopeId === state.modal.id)
      .slice(0, 10),
    source: "frontend.gameModal",
  }).then(() => loadMemoryStatus({ recordEvent: false })).catch(() => {});
}

function getModalSubject() {
  if (state.modal.type === "agent") return getOfficeAgent(state.modal.id);
  if (state.modal.type === "prop") return getInteractiveObjects().find((item) => item.id === state.modal.id);
  return null;
}

function getSubjectImage(subject, type) {
  if (!subject) return "";
  if (type === "agent") return withAgentAssetVersion(subject.id === state.agent.id ? state.agent.frameImage : subject.image);
  return resolveProjectAssetPath(subject.asset || subject.image || state.data?.room?.image);
}

function getPropertyRole(subject) {
  if (!subject?.id) return null;
  return state.propReports[subject.id]?.propertyRole || null;
}

function listText(items, fallback = "-") {
  return Array.isArray(items) && items.length ? items.join(", ") : fallback;
}

function propertyRoleToMissionItems(role) {
  if (!role) return [];
  const cards = [];
  if (role.purpose) {
    cards.push({
      title: `หน้าที่: ${role.displayTitle || role.functionName || "จุดทำงาน"}`,
      detail: role.purpose,
      owner: (role.ownerAgents || []).map((id) => displayAgentName(id)).join(", ") || displayAgentName("manager"),
      status: role.reportType || "property_role",
    });
  }
  if (Array.isArray(role.shows) && role.shows.length) {
    cards.push({
      title: "ข้อมูลที่แสดงบนอุปกรณ์นี้",
      detail: role.purpose || `กำหนดข้อมูลไว้ ${role.shows.length} หมวด`,
      owner: (role.ownerAgents || []).map((id) => displayAgentName(id)).join(", ") || displayAgentName("manager"),
      status: "display_contract",
    });
  }
  if (Array.isArray(role.dataSources) && role.dataSources.length) {
    cards.push({
      title: "แหล่งข้อมูลของ Dashboard",
      detail: `ใช้ข้อมูลในเครื่องผ่าน Local Runner และคลังรายงาน ${role.dataSources.length} แหล่ง`,
      owner: "Local Runner",
      status: "data_sources",
    });
  }
  if (Array.isArray(role.doNotShow) && role.doNotShow.length) {
    cards.push({
      title: "ข้อมูลที่ห้ามแสดง",
      detail: "ไม่แสดง Token, Cookie, รหัสผ่าน หรือข้อมูลลับบนหน้าเว็บ",
      owner: displayAgentName("risk_guard"),
      status: "guardrail",
    });
  }
  return cards;
}

function getRelevantMissionsForSubject(subject, type) {
  if (!subject) return [];
  if (type === "agent") {
    return state.missions
      .filter((mission) => getAgentIdFromOwner(mission.owner) === subject.id);
  }
  return state.missions
    .filter((mission) => mission.targetId === subject.id || mission.linkedPropId === subject.id);
}

function getRelevantReportsForSubject(subject, type) {
  if (!subject) return [];
  if (type === "agent") {
    const memoryItems = memoryCardsToMissionItems(
      getRelevantMemoryCards(`${subject.id} ${subject.name} ${subject.role} ${(subject.tools || []).join(" ")}`, 5),
      subject.name,
    );
    const transcriptItems = state.meetingTranscript
      .filter((line) => (
        line.simulation !== true
        && (line.from === subject.id || line.to === subject.id || line.participants?.includes(subject.id))
      ))
      .slice(0, 5)
      .map((line) => ({
        title: "บันทึกบทสนทนา",
        detail: `${line.label || line.from || "การประชุม"}: ${line.message || line.summary || ""}`,
        status: "transcript",
      }));
    return [...transcriptItems, ...memoryItems];
  }

  const report = state.propReports[subject.id];
  const propertyRole = getPropertyRole(subject);
  return [
    ...propertyRoleToMissionItems(propertyRole),
    ...propReportToMissionItems(report),
    ...memoryCardsToMissionItems(getRelevantMemoryCards(`${subject.id} ${subject.label} ${subject.summary} ${subject.layer}`, 5), "mission_archivist"),
  ];
}

function createBoardCard(item = {}) {
  const card = document.createElement("div");
  card.className = `board-card ${item.status || ""}`;
  const title = document.createElement("strong");
  const rawTitle = safeDashboardDisplayText(item.title || item.id || "ยังไม่มีชื่อ");
  const rawDetail = safeDashboardDisplayText(item.detail || item.result || item.summary || "ยังไม่มีรายละเอียด");
  const originalTitleHidden = isPredominantlyEnglishText(rawTitle);
  title.textContent = item.status
    ? `[${displayStatus(item.status)}] ${originalTitleHidden ? `รายงานจาก ${displayAgentName(item.owner, "ระบบ")}` : rawTitle}`
    : (originalTitleHidden ? "ข้อมูลจากระบบเดิม" : rawTitle);
  card.appendChild(title);

  if (looksLikeTechnicalText(rawDetail) || isPredominantlyEnglishText(rawDetail) || originalTitleHidden) {
    const note = document.createElement("span");
    const disclosure = document.createElement("details");
    const summary = document.createElement("summary");
    const original = document.createElement("span");
    note.textContent = looksLikeTechnicalText(rawDetail)
      ? "มีรายละเอียดแบบเทคนิค กดเปิดเมื่อต้องการตรวจ"
      : "รายละเอียดนี้มาจากข้อมูลเดิม กดเพื่อดูข้อความต้นฉบับ";
    summary.textContent = looksLikeTechnicalText(rawDetail) ? "ดูรายละเอียดแบบเทคนิค" : "ดูรายละเอียดต้นฉบับ";
    original.textContent = originalTitleHidden ? `${rawTitle}\n${rawDetail}` : rawDetail;
    disclosure.className = "board-card-disclosure";
    disclosure.append(summary, original);
    card.append(note, disclosure);
  } else {
    const detail = document.createElement("span");
    detail.textContent = rawDetail;
    card.appendChild(detail);
  }
  return card;
}

function renderCardList(container, items, emptyText) {
  if (!container) return;
  container.innerHTML = "";
  if (!items.length) {
    container.appendChild(createBoardCard({ title: "ยังไม่มีข้อมูล", detail: emptyText, status: "empty" }));
    return;
  }
  items.forEach((item) => {
    const card = createBoardCard(item);
    const hint = document.createElement("span");
    card.classList.add("dashboard-result-card");
    card.tabIndex = 0;
    card.setAttribute("role", "button");
    card.setAttribute("aria-haspopup", "dialog");
    card.setAttribute("aria-label", `เปิดรายละเอียด ${safeDashboardDisplayText(item?.title, "ผลลัพธ์งาน")}`);
    hint.className = "dashboard-result-open-hint";
    hint.textContent = "กดเพื่อดูรายละเอียด";
    card.appendChild(hint);
    card.addEventListener("click", (event) => {
      if (event.target.closest("details")) return;
      openDashboardResultDetail(item, card);
    });
    card.addEventListener("keydown", (event) => {
      if (!["Enter", " "].includes(event.key) || event.target.closest("details")) return;
      event.preventDefault();
      openDashboardResultDetail(item, card);
    });
    container.appendChild(card);
  });
}

function appendDashboardResultFact(container, label, value) {
  const term = document.createElement("dt");
  const detail = document.createElement("dd");
  term.textContent = label;
  detail.textContent = safeDashboardDisplayText(value, "-");
  container.append(term, detail);
}

function appendDashboardDetailList(container, titleText, values, className = "") {
  const items = Array.isArray(values) ? values.filter((value) => value !== null && value !== undefined && value !== "") : [];
  if (!items.length) return;
  const section = document.createElement("section");
  const title = document.createElement("h3");
  const list = document.createElement("ul");
  section.className = `dashboard-result-section ${className}`.trim();
  title.textContent = titleText;
  items.slice(0, 30).forEach((value) => {
    const row = document.createElement("li");
    row.textContent = safeDashboardDisplayText(formatDashboardValue(value), "-");
    list.appendChild(row);
  });
  section.append(title, list);
  container.appendChild(section);
}

function appendDashboardMetricSection(container, metrics) {
  if (!metrics || typeof metrics !== "object" || Array.isArray(metrics) || !Object.keys(metrics).length) return;
  const section = document.createElement("section");
  const title = document.createElement("h3");
  const grid = document.createElement("div");
  section.className = "dashboard-result-section dashboard-result-metrics";
  title.textContent = "ตัวเลขสำคัญ";
  grid.className = "dashboard-result-metric-grid";
  Object.entries(metrics).slice(0, 24).forEach(([name, value]) => {
    const card = document.createElement("div");
    const label = document.createElement("span");
    const metric = document.createElement("strong");
    label.textContent = safeDashboardDisplayText(dashboardFieldLabel(name), name);
    metric.textContent = safeDashboardDisplayText(dashboardMetricValue(name, value), "-");
    card.append(label, metric);
    grid.appendChild(card);
  });
  section.append(title, grid);
  container.appendChild(section);
}

function getSafeReportImageUrl(value) {
  const raw = String(value || "").trim();
  if (!raw) return "";
  try {
    const parsed = new URL(raw, window.location.href);
    if (parsed.origin !== window.location.origin) return "";
    if (
      !/^\/api\/reports\/[a-zA-Z0-9._-]+\/attachments\/[a-zA-Z0-9._-]+$/.test(parsed.pathname)
    ) return "";
    return parsed.href;
  } catch {
    return "";
  }
}

function getSafeReportArtifactUrl(value) {
  const raw = String(value || "").trim();
  if (!raw) return "";
  try {
    const parsed = new URL(raw, window.location.href);
    if (parsed.origin !== window.location.origin || parsed.username || parsed.password) return "";
    if (parsed.search || parsed.hash) return "";
    if (!/^\/api\/reports\/[a-zA-Z0-9._-]+\/(?:attachments|artifacts|downloads)\/[a-zA-Z0-9._-]+$/.test(parsed.pathname)) return "";
    return parsed.href;
  } catch {
    return "";
  }
}

function appendDashboardArtifactLinks(container, artifacts) {
  const safeArtifacts = (Array.isArray(artifacts) ? artifacts : [])
    .slice(0, 20)
    .map((item) => {
      if (!item || typeof item !== "object" || item.available !== true) return null;
      const safeUrl = getSafeReportArtifactUrl(item.url);
      if (!safeUrl) return null;
      return {
        safeUrl,
        kind: safeDashboardDisplayText(item.kind, "artifact"),
        fileName: safeDashboardDisplayText(item.fileName || item.label, "ไฟล์จาก Backend"),
        contentType: safeDashboardDisplayText(item.contentType || item.mimeType || item.mediaType, "ไม่ระบุชนิดไฟล์"),
      };
    })
    .filter(Boolean);
  if (!safeArtifacts.length) return false;
  const section = document.createElement("section");
  const title = document.createElement("h3");
  const list = document.createElement("ul");
  section.className = "dashboard-result-section dashboard-result-downloads";
  title.textContent = "ไฟล์ที่ Backend อนุญาตให้ดาวน์โหลด";
  list.className = "dashboard-result-download-list";
  safeArtifacts.forEach((artifact) => {
    const row = document.createElement("li");
    const link = document.createElement("a");
    const meta = document.createElement("span");
    link.href = artifact.safeUrl;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    link.textContent = artifact.fileName;
    meta.textContent = `${artifact.kind} • ${artifact.contentType}`;
    row.append(link, meta);
    list.appendChild(row);
  });
  section.append(title, list);
  container.appendChild(section);
  return true;
}

function appendDashboardVisualEvidence(container, visualEvidence) {
  const items = Array.isArray(visualEvidence) ? visualEvidence.slice(0, 12) : [];
  const safeItems = items
    .map((item) => ({ ...item, safeUrl: getSafeReportImageUrl(item?.url) }))
    .filter((item) => item.safeUrl);
  if (!safeItems.length) return;
  const section = document.createElement("section");
  const title = document.createElement("h3");
  const gallery = document.createElement("div");
  section.className = "dashboard-result-section dashboard-result-evidence";
  title.textContent = "รูปหลักฐาน";
  gallery.className = "dashboard-result-gallery";
  safeItems.forEach((item, index) => {
    const figure = document.createElement("figure");
    const link = document.createElement("a");
    const image = document.createElement("img");
    const caption = document.createElement("figcaption");
    link.href = item.safeUrl;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    link.setAttribute("aria-label", `เปิดภาพเต็มขนาด ${safeDashboardDisplayText(item?.label, `ภาพที่ ${index + 1}`)}`);
    image.src = item.safeUrl;
    image.alt = safeDashboardDisplayText(item?.label, `ภาพหลักฐานที่ ${index + 1}`);
    image.loading = "lazy";
    caption.textContent = safeDashboardDisplayText(item?.label, `ภาพหลักฐานที่ ${index + 1}`);
    image.addEventListener("error", () => {
      figure.dataset.state = "error";
      caption.textContent = "โหลดภาพหลักฐานไม่สำเร็จ ให้ตรวจไฟล์จาก Local Runner";
      image.remove();
    });
    link.appendChild(image);
    figure.append(link, caption);
    gallery.appendChild(figure);
  });
  section.append(title, gallery);
  container.appendChild(section);
}

function appendDashboardSourceLinks(container, evidence) {
  if (!Array.isArray(evidence) || !evidence.length) return;
  const section = document.createElement("section");
  const title = document.createElement("h3");
  const list = document.createElement("ul");
  section.className = "dashboard-result-section dashboard-result-sources";
  title.textContent = "แหล่งข้อมูล";
  evidence.slice(0, 20).forEach((item) => {
    const rawUrl = String(item?.url || "").trim();
    let parsed;
    try {
      parsed = new URL(rawUrl, window.location.href);
    } catch {
      return;
    }
    if (!["http:", "https:"].includes(parsed.protocol) || parsed.username || parsed.password) return;
    const row = document.createElement("li");
    const link = document.createElement("a");
    const note = document.createElement("span");
    link.href = parsed.href;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    link.textContent = safeDashboardDisplayText(item?.label, parsed.hostname);
    note.textContent = safeDashboardDisplayText(item?.note, parsed.hostname);
    row.append(link, note);
    list.appendChild(row);
  });
  if (!list.children.length) return;
  section.append(title, list);
  container.appendChild(section);
}

function openDashboardResultDetail(item, trigger = null) {
  if (!item || !els.dashboardResultDialog || !els.dashboardResultDetailBody) return;
  const title = safeDashboardDisplayText(item.title, "รายงานผล Task");
  const summary = safeDashboardDisplayText(
    item.summary || item.detail || item.result,
    "ยังไม่มีรายละเอียดเพิ่มเติมจาก Local Runner",
  );
  const facts = document.createElement("dl");
  const summaryText = document.createElement("p");
  dashboardResultShouldRestoreFocus = true;
  dashboardResultReturnFocus = trigger instanceof HTMLElement ? trigger : document.activeElement;
  if (els.dashboardResultDetailTitle) els.dashboardResultDetailTitle.textContent = title;
  els.dashboardResultDetailBody.innerHTML = "";
  summaryText.className = "dashboard-result-detail-summary";
  summaryText.textContent = summary;
  facts.className = "kanban-detail-grid";
  appendDashboardResultFact(facts, "สถานะ", displayStatus(item.status || "ready"));
  appendDashboardResultFact(
    facts,
    "ผู้รับผิดชอบ",
    item.ownerAgentId || item.owner
      ? displayAgentName(getAgentIdFromOwner(item.ownerAgentId || item.owner) || item.ownerAgentId || item.owner, item.ownerAgentId || item.owner)
      : "ยังไม่ได้ระบุ",
  );
  appendDashboardResultFact(facts, "อัปเดตล่าสุด", formatThaiDateTime(item.updatedAt || item.createdAt));
  appendDashboardResultFact(facts, "แหล่งข้อมูล", "Backend/Local Runner ปกปิดข้อมูลลับก่อนส่งมาหน้านี้");
  const executionScope = reportExecutionScope(item);
  if (executionScope) {
    appendDashboardResultFact(facts, "ขอบเขตผลลัพธ์", executionScope.label);
  }
  els.dashboardResultDetailBody.append(summaryText, facts);
  appendDashboardMetricSection(els.dashboardResultDetailBody, item.metrics);
  appendDashboardDetailList(els.dashboardResultDetailBody, "สิ่งที่พบ", item.findings, "findings");
  appendDashboardDetailList(els.dashboardResultDetailBody, "ความเสี่ยงหรือข้อควรระวัง", item.risks, "risks");
  appendDashboardDetailList(els.dashboardResultDetailBody, "ขั้นตอนถัดไป", item.nextActions, "next-actions");
  appendDashboardVisualEvidence(
    els.dashboardResultDetailBody,
    Array.isArray(item.attachments) ? item.attachments : item.visualEvidence,
  );
  appendDashboardSourceLinks(els.dashboardResultDetailBody, item.evidence);
  appendDashboardArtifactLinks(
    els.dashboardResultDetailBody,
    item.safeAttachments || item.downloads || item.artifacts || item.attachments,
  );
  if (
    Number(item.artifactCount || 0) > 0
    && !(Array.isArray(item.attachments) ? item.attachments : item.visualEvidence)?.length
  ) {
    const note = document.createElement("p");
    note.className = "dashboard-result-artifact-note";
    note.textContent = `งานนี้มีไฟล์ผลลัพธ์ ${Number(item.artifactCount)} รายการ แต่ยังไม่มีรูปที่ Backend อนุญาตให้แสดงบน Dashboard`;
    els.dashboardResultDetailBody.appendChild(note);
  }
  if (!els.dashboardResultDialog.open) els.dashboardResultDialog.showModal();
}

function getDashboardWorkState(item, kind = "mission") {
  const status = kind === "mission"
    ? getMissionPresentationStatus(item)
    : String(item?.status || "ready").trim().toLowerCase().replace(/[ -]+/g, "_");
  if (["completed", "archived", "ready", "published"].includes(status)) return "completed";
  if (["waiting_approval", "needs_approval", "blocked", "failed", "error"].includes(status)) return "blocked";
  return "running";
}

function getDashboardItemTime(item = {}) {
  const value = item.updatedAt || item.completedAt || item.createdAt || "";
  const parsed = value ? new Date(value).getTime() : Number.NaN;
  return Number.isFinite(parsed) ? parsed : 0;
}

function createDashboardReportCard(report = {}) {
  const card = document.createElement("button");
  const topline = document.createElement("span");
  const badge = document.createElement("span");
  const owner = document.createElement("span");
  const title = document.createElement("strong");
  const summary = document.createElement("span");
  const footer = document.createElement("span");
  const workState = getDashboardWorkState(report, "report");
  const visualEvidence = Array.isArray(report.attachments) ? report.attachments : report.visualEvidence;
  const evidenceCount = Array.isArray(visualEvidence) ? visualEvidence.length : 0;
  const executionScope = reportExecutionScope(report);

  card.type = "button";
  card.className = `dashboard-report-card ${workState}`;
  card.setAttribute("aria-haspopup", "dialog");
  card.setAttribute("aria-label", `เปิดรายงาน ${safeDashboardDisplayText(report.title, "ผลลัพธ์งาน")}`);
  topline.className = "dashboard-report-card-topline";
  badge.className = "task-status-badge";
  badge.textContent = displayStatus(report.status || (workState === "completed" ? "ready" : workState));
  owner.className = "task-card-meta";
  owner.textContent = displayAgentName(report.ownerAgentId || report.owner, "ระบบ");
  topline.append(badge, owner);
  title.textContent = safeDashboardDisplayText(report.title, "รายงานผล Task");
  summary.textContent = safeDashboardDisplayText(report.summary || report.detail, "กดเพื่อเปิดรายงานฉบับเต็ม");
  footer.className = "dashboard-report-card-footer";
  footer.textContent = [
    executionScope ? (executionScope.verified ? "ยืนยันการรัน MT4/MT5 แล้ว" : "ยังไม่ได้ยืนยันการรัน MT4/MT5") : "",
    evidenceCount ? `มีรูปหลักฐาน ${evidenceCount} ภาพ` : "",
    "เปิดรายงานฉบับเต็ม",
  ].filter(Boolean).join(" • ");
  card.append(topline, title, summary, footer);
  card.addEventListener("click", () => openDashboardResultDetail(report, card));
  return card;
}

function renderDashboardWorkColumn(container, entries, emptyText) {
  if (!container) return;
  container.innerHTML = "";
  if (!entries.length) {
    const empty = document.createElement("div");
    empty.className = "dashboard-work-empty";
    empty.textContent = emptyText;
    container.appendChild(empty);
    return;
  }
  entries
    .sort((left, right) => getDashboardItemTime(right.item) - getDashboardItemTime(left.item))
    .forEach(({ kind, item }) => {
      container.appendChild(kind === "mission"
        ? createTaskCard(item, { variant: "dashboard-task-card", source: "dashboard" })
        : createDashboardReportCard(item));
    });
}

function closeDashboardResultDetail({ restoreFocus = true } = {}) {
  dashboardResultShouldRestoreFocus = restoreFocus;
  if (els.dashboardResultDialog?.open) {
    els.dashboardResultDialog.close();
    return;
  }
  if (restoreFocus) dashboardResultReturnFocus?.focus?.();
  dashboardResultReturnFocus = null;
}

function createTaskCard(mission = {}, options = {}) {
  const { variant = "board-card", source = "list" } = options;
  const status = getMissionPresentationStatus(mission);
  const autoEligible = isBackendAutoEligibleMission(mission);
  const card = document.createElement("button");
  const topline = document.createElement("span");
  const badge = document.createElement("span");
  const owner = document.createElement("span");
  const title = document.createElement("strong");
  const destination = document.createElement("span");
  const hint = document.createElement("span");

  card.type = "button";
  card.className = `task-card ${variant} ${status}`;
  card.classList.toggle("auto-eligible", autoEligible);
  card.dataset.taskMissionId = mission.id || "";
  card.setAttribute("aria-haspopup", "dialog");
  card.setAttribute("aria-label", `เปิดรายละเอียด Task ${mission.title || mission.id || "ที่เลือก"}`);
  if (source === "kanban") {
    card.dataset.missionId = mission.id || "";
    card.classList.toggle("selected", state.modal.selectedMissionId === mission.id);
  }

  topline.className = "task-card-topline";
  badge.className = "task-status-badge";
  badge.textContent = displayStatus(status);
  owner.className = "task-card-meta";
  owner.textContent = `ผู้รับผิดชอบ: ${displayAgentName(getAgentIdFromOwner(mission.owner) || mission.owner, "ยังไม่ได้มอบหมาย")}`;
  topline.append(badge, owner);

  title.className = "task-card-title";
  title.textContent = mission.title || mission.id || "Task ที่ยังไม่มีชื่อ";
  destination.className = "task-card-destination";
  destination.textContent = `รายงานที่: ${displayPropName(mission.targetId || "mission_strategy_table")}`;
  hint.className = "task-card-summary";
  hint.textContent = status === "completed"
    ? (autoEligible ? "งานอัตโนมัติเสร็จแล้ว • เปิดดูรายงาน" : "เปิดดูผลลัพธ์และรายงาน")
    : ["blocked", "failed"].includes(status)
      ? "เปิดดูสาเหตุและรายละเอียด"
      : autoEligible
        ? "Backend ดูแลงานนี้อัตโนมัติ"
        : "กดเพื่อดูรายละเอียด";
  card.append(topline, title);
  if (source === "kanban") card.appendChild(destination);
  card.appendChild(hint);
  card.addEventListener("click", () => openTaskDetail(mission.id, card, { source }));
  return card;
}

function renderTaskList(container, missions, emptyText = "ยังไม่มี Task ในส่วนนี้") {
  if (!container) return;
  container.innerHTML = "";
  if (!missions.length) {
    container.appendChild(createBoardCard({ title: "ยังไม่มี Task", detail: emptyText, status: "empty" }));
    return;
  }
  missions.forEach((mission) => container.appendChild(createTaskCard(mission)));
}

function renderStatusGrid(items) {
  if (!els.modalStatusGrid) return;
  els.modalStatusGrid.innerHTML = "";
  items.forEach(([label, value]) => {
    const row = document.createElement("div");
    row.className = "modal-status-item";
    const name = document.createElement("span");
    const text = document.createElement("span");
    name.textContent = label;
    text.textContent = value || "-";
    row.append(name, text);
    els.modalStatusGrid.appendChild(row);
  });
}

function renderChatLog(subject, type) {
  if (!els.modalChatLog) return;
  const scoped = state.chatLog
    .filter((line) => line.scopeType === type && line.scopeId === subject?.id)
    .slice(0, 16)
    .reverse();
  const transcript = type === "agent"
    ? state.meetingTranscript
      .filter((line) => (
        line.simulation !== true
        && (line.from === subject.id || line.to === subject.id || line.participants?.includes(subject.id))
      ))
      .slice(0, 4)
      .map((line) => ({
        speaker: line.label || "Agent Transcript",
        text: line.message || line.summary || "",
        side: "agent",
      }))
    : [];
  const lines = [...scoped, ...transcript];
  els.modalChatLog.innerHTML = "";
  if (!lines.length) {
    const welcome = document.createElement("div");
    welcome.className = "chat-line agent";
    const speaker = document.createElement("strong");
    const message = document.createElement("span");
    speaker.textContent = type === "agent" ? subject.name : "รายงาน Mission";
    message.textContent = type === "agent" ? getAgentSpeech(subject.id) : "กดดู Task หรือรายงาน หรือสั่งให้ Agent เดินมาตรวจอุปกรณ์นี้ได้เลยครับ";
    welcome.append(speaker, message);
    els.modalChatLog.appendChild(welcome);
    return;
  }
  lines.forEach((line) => {
    const item = document.createElement("div");
    item.className = `chat-line ${line.side || "agent"}`;
    const speaker = document.createElement("strong");
    const text = document.createElement("span");
    speaker.textContent = line.speaker || "Agent";
    text.textContent = line.text || "";
    item.append(speaker, text);
    els.modalChatLog.appendChild(item);
  });
  els.modalChatLog.scrollTop = els.modalChatLog.scrollHeight;
}

const MISSION_KANBAN_COLUMNS = [
  { id: "queued", label: "รอเริ่มงาน" },
  { id: "running", label: "กำลังทำงาน" },
  { id: "waiting_approval", label: "รออนุมัติ" },
  { id: "blocked", label: "ติดขัด" },
  { id: "completed", label: "เสร็จแล้ว" },
  { id: "failed", label: "ไม่สำเร็จ" },
];

function getModalSurface(type = state.modal.type, id = state.modal.id) {
  if (type === "agent") return "agent";
  const prop = type === "prop" ? getInteractiveObjects().find((item) => item.id === id) : null;
  const interactionMode = prop ? getPropertyRole(prop)?.interactionMode : null;
  if (type === "prop" && (interactionMode === "kanban" || id === "mission_strategy_table")) return "kanban";
  return "dashboard";
}

function isManagerWorkspace(subject) {
  return Boolean(subject && ["manager", "ceo"].includes(subject.id));
}

function normalizeMissionStatus(status = "queued") {
  const normalized = String(status || "queued").trim().toLowerCase().replace(/[ -]+/g, "_");
  if (["approval_required", "pending_approval"].includes(normalized)) return "waiting_approval";
  if (["queued", "running", "waiting_approval", "blocked", "completed", "failed", "archived"].includes(normalized)) {
    return normalized;
  }
  return "queued";
}

function getMissionPresentationStatus(mission = {}) {
  const storedStatus = normalizeMissionStatus(mission.status);
  const counts = mission?.delegation?.subtaskStatusCounts;
  const hasDelegatedChildren = (
    Array.isArray(mission.subtaskIds) && mission.subtaskIds.length > 0
  ) || Number(mission?.delegation?.subtaskCount || 0) > 0;
  if (!hasDelegatedChildren || !counts || typeof counts !== "object" || Array.isArray(counts)) {
    return storedStatus;
  }
  const count = (status) => Math.max(0, Number(counts[status]) || 0);
  if (count("running") > 0) return "running";
  if (count("waiting_approval") > 0) return "waiting_approval";
  if (count("queued") > 0) return "queued";
  if (count("failed") > 0) return "failed";
  if (count("blocked") > 0) return "blocked";
  const terminalSuccess = count("completed") + count("archived");
  const subtaskCount = Math.max(0, Number(mission?.delegation?.subtaskCount || mission.subtaskIds?.length) || 0);
  if (subtaskCount > 0 && terminalSuccess >= subtaskCount) return "completed";
  return storedStatus;
}

function isBackendAutoEligibleMission(mission) {
  const directlyAutoEligible = Boolean(
    mission?.executionMode === "auto_guarded"
    && mission?.autoEligible === true
    && mission?.requiresHumanApproval === false
  );
  if (directlyAutoEligible) return true;
  if (mission?.toolId !== "manager_delegate" || mission?.requiresHumanApproval === true) return false;
  const childIds = Array.isArray(mission?.subtaskIds) ? mission.subtaskIds.filter(Boolean) : [];
  if (!childIds.length) return false;
  const childMissions = childIds
    .map((id) => state.missions.find((item) => item.id === id))
    .filter(Boolean);
  return Boolean(
    childMissions.length === childIds.length
    && childMissions.every((child) => (
      child.executionMode === "auto_guarded"
      && child.autoEligible === true
      && child.requiresHumanApproval === false
    ))
  );
}

function getAgentIdFromOwner(owner) {
  const ownerText = String(owner || "").trim().toLowerCase();
  if (!ownerText) return null;
  const direct = getOfficeAgent(ownerText);
  if (direct) return direct.id;
  const matched = state.officeAgents.find((agent) => (
    agent.name?.toLowerCase() === ownerText
    || agent.legacyName?.toLowerCase() === ownerText
    || agent.role?.toLowerCase() === ownerText
    || agent.contractName?.toLowerCase() === ownerText
    || agent.contractRole?.toLowerCase() === ownerText
  ));
  return matched?.id || null;
}

function getPropOwnerAgentId(subject) {
  const role = getPropertyRole(subject);
  const candidates = [
    role?.primaryOwnerAgentId,
    ...(Array.isArray(role?.ownerAgents) ? role.ownerAgents : []),
  ].filter(Boolean);
  return candidates.map(getAgentIdFromOwner).find(Boolean) || null;
}

function formatDashboardValue(value) {
  if (Array.isArray(value)) return value.join(", ");
  if (value && typeof value === "object") {
    return Object.entries(value)
      .slice(0, 8)
      .map(([name, detail]) => `${name}: ${detail && typeof detail === "object" ? "มีข้อมูลรายละเอียด" : detail}`)
      .join(" • ");
  }
  return String(value ?? "-");
}

function safeDashboardDisplayText(value, fallback = "-") {
  const text = String(value ?? fallback).replace(/\s+/g, " ").trim() || fallback;
  return text
    .replace(/\b(?:pid|process[_ -]?id)\b\s*["']?\s*[:=#-]?\s*\d+\b/gi, "PID [ปกปิด]")
    .replace(/\bbearer\s+[^\s,;|]+/gi, "Bearer [ปกปิด]")
    .replace(/\b((?:api[_ .-]?key|token|password|passwd|secret|authorization|cookie|bot[_ .-]?token|broker[_ .-]?password|account(?:[_ .-]?(?:number|id|login))?|broker[_ .-]?server|terminal[_ .-]?path|process[_ .-]?id|pid))\b\s*["']?\s*[:=]\s*(?:"[^"]*"|'[^']*'|[^,;|•]+)/gi, "$1: [ปกปิด]")
    .replace(/\b[A-Za-z]:\\[^,\n;|]+/g, "[ปกปิดตำแหน่งไฟล์]")
    .replace(/\\\\[^,\n;|]+/g, "[ปกปิดตำแหน่งไฟล์]")
    .replace(/(^|\s)\/(?:Users|home|root|var|etc|tmp|opt|srv)\/[^,\n;|]+/gi, "$1[ปกปิดตำแหน่งไฟล์]")
    .slice(0, 600);
}

function safeAgentChatReplyText(value, fallback = "Agent ยังไม่ส่งคำตอบกลับมา") {
  const text = String(value ?? fallback)
    .replace(/\u0000/g, "")
    .replace(/\r\n?/g, "\n")
    .trim() || fallback;
  return text
    .replace(/\b(?:pid|process[_ -]?id)\b\s*["']?\s*[:=#-]?\s*\d+\b/gi, "PID [ปกปิด]")
    .replace(/\bbearer\s+[^\s,;|]+/gi, "Bearer [ปกปิด]")
    .replace(/\b((?:api[_ .-]?key|token|password|passwd|secret|authorization|cookie|bot[_ .-]?token|broker[_ .-]?password|account(?:[_ .-]?(?:number|id|login))?|broker[_ .-]?server|terminal[_ .-]?path|process[_ .-]?id|pid))\b\s*["']?\s*[:=]\s*(?:"[^"]*"|'[^']*'|[^,;|•\n]+)/gi, "$1: [ปกปิด]")
    .replace(/\b[A-Za-z]:\\[^,\n;|]+/g, "[ปกปิดตำแหน่งไฟล์]")
    .replace(/\\\\[^,\n;|]+/g, "[ปกปิดตำแหน่งไฟล์]")
    .replace(/(^|\s)\/(?:Users|home|root|var|etc|tmp|opt|srv)\/[^,\n;|]+/gi, "$1[ปกปิดตำแหน่งไฟล์]")
    .slice(0, 5000);
}

function normalizeConnectionStatus(value = "not_connected") {
  const normalized = String(value || "not_connected").trim().toLowerCase().replace(/[ -]+/g, "_");
  if (["connected", "online", "ready", "available", "active", "enabled", "healthy", "ok", "detected", "configured"].includes(normalized)) {
    return "connected";
  }
  if (["coming_soon", "planned", "unimplemented", "not_implemented", "disabled_unimplemented"].includes(normalized)) {
    return "coming_soon";
  }
  if (["partial", "degraded", "warning", "needs_attention"].includes(normalized)) return "partial";
  if (["checking", "loading", "running", "not_checked"].includes(normalized)) return "checking";
  if (["error", "failed", "blocked", "config_error", "auth_required", "needs_login", "not_configured", "not_found", "unavailable"].includes(normalized)) return "error";
  return "not_connected";
}

function connectionStatusLabel(value, fallback = "ยังไม่เชื่อม") {
  const normalized = String(value || "not_connected").trim().toLowerCase().replace(/[ -]+/g, "_");
  const labels = {
    connected: "เชื่อมแล้ว",
    online: "เชื่อมแล้ว",
    ready: "พร้อมใช้งาน",
    available: "พร้อมใช้งาน",
    active: "กำลังใช้งาน",
    enabled: "เปิดใช้งานแล้ว",
    healthy: "ทำงานปกติ",
    ok: "ทำงานปกติ",
    detected: "ตรวจพบแล้ว",
    configured: "ตั้งค่าแล้ว",
    not_connected: "ยังไม่เชื่อม",
    disconnected: "ยังไม่เชื่อม",
    offline: "ออฟไลน์",
    unavailable: "ยังไม่พร้อมใช้งาน",
    not_found: "ยังไม่พบระบบ",
    not_configured: "ยังไม่ได้ตั้งค่า",
    not_checked: "ยังไม่ได้ตรวจ",
    needs_login: "ต้องเข้าสู่ระบบก่อน",
    needs_attention: "ต้องตรวจสอบ",
    not_required: "ไม่จำเป็นสำหรับ Dashboard นี้",
    missing: "ยังไม่พบระบบ",
    disabled: "ยังไม่เปิดใช้งาน",
    coming_soon: "Coming Soon",
    planned: "Coming Soon",
    unimplemented: "Coming Soon",
    not_implemented: "Coming Soon",
    disabled_unimplemented: "Coming Soon",
    partial: "เชื่อมต่อบางส่วน",
    degraded: "เชื่อมต่อบางส่วน",
    warning: "ควรตรวจสอบ",
    checking: "กำลังตรวจสอบ",
    loading: "กำลังตรวจสอบ",
    running: "กำลังทำงาน",
    error: "ตรวจไม่สำเร็จ",
    failed: "ตรวจไม่สำเร็จ",
    blocked: "ถูกระงับไว้",
    auth_required: "ต้อง Login Codex",
    config_error: "Codex Config มีปัญหา",
  };
  return labels[normalized] || STATUS_LABELS[normalized] || fallback;
}

function getDashboardDataAvailability(profile, hasReport = false) {
  const availability = profile?.availability;
  const dataAvailability = availability && typeof availability === "object" && !Array.isArray(availability)
    ? availability.data
    : availability;
  const status = dataAvailability && typeof dataAvailability === "object" && !Array.isArray(dataAvailability)
    ? (dataAvailability.status || dataAvailability.value || dataAvailability.state)
    : dataAvailability;
  const label = dataAvailability && typeof dataAvailability === "object" && !Array.isArray(dataAvailability)
    ? (dataAvailability.labelTh || dataAvailability.label)
    : "";
  const safeStatus = typeof status === "string" && status.trim()
    ? status
    : (hasReport ? "available" : "checking");
  return {
    status: safeStatus,
    label: label || profile?.labelTh || connectionStatusLabel(safeStatus, "กำลังตรวจสอบ"),
  };
}

function setConnectionBadge(element, status, label = "") {
  if (!element) return;
  const displayState = normalizeConnectionStatus(status);
  element.dataset.status = displayState;
  element.textContent = safeDashboardDisplayText(label || connectionStatusLabel(status));
}

function formatConnectionInterval(minutes) {
  const value = Number(minutes);
  if (!Number.isFinite(value) || value <= 0) return "";
  if (value % 60 === 0) return `ทุก ${value / 60} ชั่วโมง`;
  return `ทุก ${Math.round(value)} นาที`;
}

function dashboardUsesCodex(report, items = []) {
  const capabilities = Array.isArray(report?.capabilities) ? report.capabilities : [];
  return capabilities.some((item) => /^codex(?:_|$)/i.test(String(item?.id || "")))
    || items.some((item) => /codex/i.test(`${item?.id || ""} ${item?.labelTh || ""}`));
}

function codexQuotaConnectionItem(codexUsage = {}) {
  const snapshot = state.codexRate.snapshot;
  const activityLabel = codexUsage?.activeNow
    ? "Dashboard นี้มีงาน Codex กำลังทำงานอยู่"
    : "ขณะนี้ Dashboard นี้ไม่ได้กำลังใช้ Codex";
  if (!snapshot?.primary) {
    return {
      id: "codex_account_quota",
      labelTh: "โควตาบัญชี Codex",
      status: snapshot?.status === "loading" ? "checking" : (snapshot?.status || "not_connected"),
      detailTh: snapshot?.status === "auth_required"
        ? "ต้อง Login Codex ในเครื่องก่อน จึงจะอ่านโควตาได้"
        : snapshot?.status === "config_error"
          ? "Codex Config มีปัญหา จึงยังอ่านโควตาไม่ได้"
          : "ยังไม่ได้รับข้อมูลโควตาจาก Local Runner",
      required: false,
      action: null,
    };
  }
  return {
    id: "codex_account_quota",
    labelTh: "โควตาบัญชี Codex",
    status: snapshot.limitReached ? "blocked" : "connected",
    detailTh: `${activityLabel} • ข้อมูลรวมของบัญชี: เหลือ ${formatCodexRatePercent(snapshot.primary.remainingPercent)} • ใช้แล้ว ${formatCodexRatePercent(snapshot.primary.usedPercent)} • ${formatCodexRateReset(snapshot.primary.resetsAt)}`,
    required: false,
    action: null,
  };
}

function createConnectionChecklistRow(item = {}) {
  const row = document.createElement("div");
  const heading = document.createElement("div");
  const label = document.createElement("strong");
  const badges = document.createElement("div");
  const status = document.createElement("span");
  const detail = document.createElement("p");
  const normalizedStatus = normalizeConnectionStatus(item.status);

  row.className = "connection-check-item";
  row.dataset.status = normalizedStatus;
  heading.className = "connection-check-heading";
  label.textContent = safeDashboardDisplayText(item.labelTh, "รายการเชื่อมต่อ");
  badges.className = "connection-check-badges";
  status.className = "connection-badge";
  setConnectionBadge(status, item.status);
  badges.appendChild(status);

  if (item.required === true) {
    const required = document.createElement("span");
    required.className = "connection-required-badge";
    required.textContent = "จำเป็น";
    badges.appendChild(required);
  }

  heading.append(label, badges);
  detail.textContent = safeDashboardDisplayText(item.detailTh, normalizedStatus === "coming_soon" ? "ส่วนนี้ยังเป็น Coming Soon" : "ยังไม่มีรายละเอียดจาก Local Runner");
  row.append(heading, detail);
  return row;
}

function normalizeMetatraderCandidate(candidate) {
  if (!candidate || typeof candidate !== "object" || Array.isArray(candidate)) return null;
  const candidateId = String(candidate.candidateId || "").trim();
  if (!/^[a-zA-Z0-9][a-zA-Z0-9._:-]{0,159}$/.test(candidateId)) return null;
  const platformValue = String(candidate.platform || "").trim().toUpperCase();
  if (!["MT4", "MT5"].includes(platformValue)) return null;
  const runningStateValue = String(candidate.runningState || "unknown").trim().toLowerCase();
  const runningState = ["unknown", "platform_running_detected", "not_running_detected"].includes(runningStateValue)
    ? runningStateValue
    : "unknown";
  const safeLabel = safeDashboardDisplayText(candidate.labelTh || `${platformValue} Terminal ที่ตรวจพบ`);
  return {
    candidateId,
    platform: platformValue,
    labelTh: safeLabel.includes("[ปกปิด") ? `${platformValue} Terminal ที่ตรวจพบ` : safeLabel,
    detected: candidate.detected === true,
    runningState,
  };
}

function getMetatraderSelectionModel(checklist) {
  const rawSelection = checklist?.metatraderSelection && typeof checklist.metatraderSelection === "object"
    ? checklist.metatraderSelection
    : {};
  const candidates = [];
  const seenIds = new Set();
  const appendCandidate = (value) => {
    const candidate = normalizeMetatraderCandidate(value);
    if (!candidate || seenIds.has(candidate.candidateId)) return;
    seenIds.add(candidate.candidateId);
    candidates.push(candidate);
  };
  (Array.isArray(rawSelection.candidates) ? rawSelection.candidates : []).slice(0, 24).forEach(appendCandidate);
  appendCandidate(rawSelection.selectedCandidate);
  const selectedCandidate = normalizeMetatraderCandidate(rawSelection.selectedCandidate);
  const declaredCount = Number(rawSelection.candidateCount);
  return {
    candidates,
    selectedCandidate,
    candidateCount: Number.isFinite(declaredCount)
      ? Math.max(candidates.length, Math.min(1000, Math.max(0, Math.trunc(declaredCount))))
      : candidates.length,
    canSelect: rawSelection.canSelect !== false && candidates.length > 0,
    adapterReady: rawSelection.adapterReady === true,
    adapterConnection: safeDashboardDisplayText(rawSelection.adapterConnection, ""),
    detailTh: safeDashboardDisplayText(rawSelection.detailTh || "เลือก Terminal เป้าหมายได้เมื่อ Local Runner ตรวจพบรายการแบบอ่านอย่างเดียว"),
  };
}

function renderMetatraderSelection(subject, checklist, canDiscoverMetatrader, report = null) {
  if (!els.modalDashboardMetatraderSelection || !els.modalDashboardMetatraderCandidates) return;
  els.modalDashboardMetatraderSelection.hidden = !canDiscoverMetatrader;
  if (!canDiscoverMetatrader) {
    els.modalDashboardMetatraderCandidates.innerHTML = "";
    if (els.modalDashboardConfirmMetatrader) els.modalDashboardConfirmMetatrader.disabled = true;
    return;
  }

  const selection = getMetatraderSelectionModel(checklist);
  const backendSelectedId = selection.selectedCandidate?.candidateId || "";
  const council = signalCouncilModel(report || {});
  const gateway = council.tradeGateway && typeof council.tradeGateway === "object"
    ? council.tradeGateway
    : {};
  const gatewayCandidateId = safeDashboardDisplayText(gateway.selectedCandidateId, "");
  const connectedGatewayCandidateId = gateway.connected === true ? gatewayCandidateId : "";
  const authoritativeSelectedId = connectedGatewayCandidateId || backendSelectedId;
  const selectionConflict = Boolean(
    connectedGatewayCandidateId
    && backendSelectedId
    && connectedGatewayCandidateId !== backendSelectedId,
  );
  const snapshotChannel = signalSnapshotChannel(report || {});
  const snapshotAvailable = council?.chartSnapshot?.available === true;
  let chosenId = String(state.metatraderCandidateChoice[subject.id] || "");
  if (!selection.candidates.some((candidate) => candidate.candidateId === chosenId)) {
    chosenId = authoritativeSelectedId;
    if (chosenId) state.metatraderCandidateChoice[subject.id] = chosenId;
    else delete state.metatraderCandidateChoice[subject.id];
  }
  const chosenCandidate = selection.candidates.find((candidate) => candidate.candidateId === chosenId) || null;

  if (els.modalDashboardMetatraderSummary) {
    const connectedCandidate = selection.candidates.find((candidate) => (
      candidate.candidateId === connectedGatewayCandidateId
    ));
    const connectedCandidateMissing = Boolean(connectedGatewayCandidateId && !connectedCandidate);
    els.modalDashboardMetatraderSummary.textContent = selectionConflict
      ? "ข้อมูล Terminal ที่เลือกกับ EA Gateway ไม่ตรงกัน • กดตรวจข้อมูล MT4 ใหม่ก่อนเปลี่ยน Terminal"
      : connectedCandidate
        ? `เชื่อมแล้ว: ${connectedCandidate.labelTh} (${connectedCandidate.platform}) ผ่าน EA Gateway และ Local Runner`
        : connectedCandidateMissing
          ? "EA Gateway เชื่อมแล้ว แต่ Terminal นี้ไม่อยู่ในผลค้นหาล่าสุด • กดตรวจข้อมูล MT4 ใหม่ก่อนเลือกหรือเปลี่ยน Terminal"
        : selection.selectedCandidate
          ? `เลือกแล้ว: ${selection.selectedCandidate.labelTh} (${selection.selectedCandidate.platform})${selection.selectedCandidate.detected ? "" : " • ไม่พบในการตรวจล่าสุด"}`
          : chosenCandidate
            ? `พบแล้ว ${selection.candidateCount} รายการ • เลือกไว้ ${chosenCandidate.labelTh} กรุณากดยืนยัน`
            : selection.candidateCount
              ? `พบแล้ว ${selection.candidateCount} รายการ • กรุณาเลือก Terminal เป้าหมาย`
              : "พบแล้ว 0 รายการ • กด ‘ค้นหา MT4 / MT5’ เพื่ออัปเดต";
  }

  els.modalDashboardMetatraderCandidates.innerHTML = "";
  if (!selection.candidates.length) {
    const empty = document.createElement("p");
    empty.className = "metatrader-candidates-empty";
    empty.textContent = selection.detailTh;
    els.modalDashboardMetatraderCandidates.appendChild(empty);
  } else {
    selection.candidates.forEach((candidate, index) => {
      const card = document.createElement("label");
      const input = document.createElement("input");
      const copy = document.createElement("span");
      const title = document.createElement("strong");
      const detail = document.createElement("span");
      const badges = document.createElement("span");
      const platform = document.createElement("span");
      const status = document.createElement("span");
      const isBackendSelected = candidate.candidateId === authoritativeSelectedId;
      const gatewayConnected = gateway.connected === true
        && Boolean(gatewayCandidateId)
        && candidate.candidateId === gatewayCandidateId;
      const snapshotConnected = snapshotAvailable
        && Boolean(snapshotChannel)
        && candidate.candidateId === snapshotChannel;

      card.className = "metatrader-candidate-card";
      card.classList.toggle("selected", candidate.candidateId === chosenId);
      input.type = "radio";
      input.name = `metatrader-candidate-${subject.id}`;
      input.value = candidate.candidateId;
      input.checked = candidate.candidateId === chosenId;
      input.disabled = state.connectionAction.inFlight || !selection.canSelect || !candidate.detected;
      input.setAttribute("aria-label", `${candidate.labelTh} ${candidate.platform}`);
      input.addEventListener("change", () => {
        state.metatraderCandidateChoice[subject.id] = candidate.candidateId;
        renderMetatraderSelection(subject, checklist, canDiscoverMetatrader, report);
      });

      copy.className = "metatrader-candidate-copy";
      title.textContent = candidate.labelTh;
      detail.textContent = !candidate.detected
        ? "ไม่พบรายการนี้ในการตรวจล่าสุด และยังไม่ได้เชื่อม Adapter"
        : gatewayConnected && snapshotConnected
          ? "EA Gateway และข้อมูล Snapshot ของ Terminal นี้เชื่อมกับ Local Runner แล้ว"
          : gatewayConnected
            ? "EA Gateway ของ Terminal นี้เชื่อมแล้ว แต่ยังรอ Snapshot ที่ยืนยันจาก Channel เดียวกัน"
        : candidate.runningState === "platform_running_detected"
          ? "พบโปรแกรมกำลังทำงาน แต่ยังไม่ได้เชื่อม Adapter"
          : candidate.runningState === "not_running_detected"
            ? "พบการติดตั้ง แต่ยังไม่พบว่ากำลังทำงาน และยังไม่ได้เชื่อม Adapter"
            : "ระบบตรวจพบรายการนี้แบบอ่านอย่างเดียว ยังไม่ได้เชื่อม Adapter";
      copy.append(title, detail);

      badges.className = "metatrader-candidate-badges";
      platform.className = "metatrader-platform-badge";
      platform.textContent = candidate.platform;
      status.className = "connection-badge";
      setConnectionBadge(
        status,
        gatewayConnected && snapshotConnected
          ? "connected"
          : isBackendSelected
            ? "configured"
            : candidate.detected
              ? "detected"
              : "not_found",
        gatewayConnected && snapshotConnected
          ? "เชื่อมแล้ว"
          : gatewayConnected
            ? "Gateway เชื่อมแล้ว"
            : isBackendSelected
              ? "เลือกแล้ว"
              : candidate.detected
                ? "พบแล้ว"
                : "ไม่พบล่าสุด",
      );
      badges.append(platform, status);
      card.append(input, copy, badges);
      els.modalDashboardMetatraderCandidates.appendChild(card);
    });
  }

  if (els.modalDashboardConfirmMetatrader) {
    els.modalDashboardConfirmMetatrader.disabled = state.connectionAction.inFlight
      || !selection.canSelect
      || !chosenId
      || !chosenCandidate?.detected
      || chosenId === authoritativeSelectedId
      || selectionConflict;
  }
}

function renderDashboardConnectionPanel(subject, propertyRole = null) {
  if (!subject || !els.modalDashboardConnectionList) return;
  const report = state.propReports[subject.id] || null;
  const rawChecklist = report?.connectionChecklist;
  const checklist = rawChecklist && (!rawChecklist.dashboardId || rawChecklist.dashboardId === subject.id)
    ? rawChecklist
    : null;
  const profile = report?.dashboardProfile || null;
  const operationMode = checklist?.operationMode || {};
  const aiSchedule = operationMode?.autoAnalysis || operationMode?.aiEveryTwoHours || {};
  const backendItems = Array.isArray(checklist?.items) ? checklist.items.slice(0, 20) : [];
  const items = [...backendItems];
  const codexUsage = checklist?.codexUsage || {};
  const codexDependency = String(codexUsage?.dependency || "").trim().toLowerCase();
  const shouldShowCodexQuota = codexDependency
    ? codexDependency !== "none"
    : dashboardUsesCodex(report, backendItems);

  if (shouldShowCodexQuota && !items.some((item) => ["codex_account_quota", "codex_quota"].includes(item?.id))) {
    items.push(codexQuotaConnectionItem(codexUsage));
  }

  const moduleName = profile?.moduleNameTh || propertyRole?.displayTitle || displayPropName(subject.id, subject.label);
  const dataAvailability = getDashboardDataAvailability(profile, Boolean(report));
  if (els.modalDashboardModuleName) els.modalDashboardModuleName.textContent = safeDashboardDisplayText(moduleName, "โมดูลของอุปกรณ์");
  setConnectionBadge(els.modalDashboardModuleAvailability, dataAvailability.status, dataAvailability.label);

  const currentMode = operationMode?.current || "manual";
  const currentModeLabel = operationMode?.labelTh
    || (currentMode === "auto_on_new_closed_bar"
      ? "อัตโนมัติเมื่อแท่งใหม่ปิด"
      : (currentMode === "ai_every_2h" ? "AI ตรวจทุก 2 ชั่วโมง" : "สั่งทำงานเอง"));
  if (els.modalDashboardOperationMode) {
    els.modalDashboardOperationMode.textContent = safeDashboardDisplayText(currentModeLabel, "สั่งทำงานเอง");
  }

  const scheduleInterval = aiSchedule?.pollSeconds
    ? `ตรวจ Snapshot ทุก ${Number(aiSchedule.pollSeconds)} วินาที`
    : formatConnectionInterval(aiSchedule?.intervalMinutes);
  const scheduleLabel = aiSchedule?.labelTh || connectionStatusLabel(aiSchedule?.status || "disabled", "ยังไม่เปิดใช้งาน");
  if (els.modalDashboardScheduleStatus) {
    els.modalDashboardScheduleStatus.textContent = safeDashboardDisplayText(
      [scheduleLabel, scheduleInterval].filter(Boolean).join(" • "),
      "ยังไม่เปิดใช้งาน",
    );
  }

  const overallStatus = checklist?.overallStatus || (normalizeConnectionStatus(dataAvailability.status) === "coming_soon" ? "coming_soon" : (report ? "not_connected" : "checking"));
  setConnectionBadge(els.modalDashboardConnectionOverall, overallStatus);
  if (els.modalDashboardConnectionCheckedAt) {
    els.modalDashboardConnectionCheckedAt.textContent = checklist?.checkedAt
      ? `ตรวจล่าสุด ${formatThaiDateTime(checklist.checkedAt)}`
      : "รอการตรวจจาก Local Runner";
  }

  els.modalDashboardConnectionList.innerHTML = "";
  if (!items.length) {
    const emptyStatus = normalizeConnectionStatus(dataAvailability.status) === "coming_soon" ? "coming_soon" : "not_connected";
    els.modalDashboardConnectionList.appendChild(createConnectionChecklistRow({
      labelTh: emptyStatus === "coming_soon" ? "โมดูลนี้ยังไม่เปิดใช้งาน" : "ยังไม่มีผลตรวจการเชื่อมต่อ",
      status: emptyStatus,
      detailTh: emptyStatus === "coming_soon"
        ? "Coming Soon — ระบบจะแสดง Checklist เมื่อโมดูลพร้อมเชื่อมต่อ"
        : "กด ‘ตรวจการเชื่อมต่อใหม่’ เพื่อขอข้อมูลจาก Local Runner",
      required: false,
    }));
  } else {
    items.forEach((item) => els.modalDashboardConnectionList.appendChild(createConnectionChecklistRow(item)));
  }

  const canDiscoverMetatrader = backendItems.some((item) => item?.action === "discover_metatrader");
  renderMetatraderSelection(subject, checklist, canDiscoverMetatrader, report);
  const actionMatches = state.connectionAction.propId === subject.id;
  if (els.modalDashboardRefreshConnections) {
    els.modalDashboardRefreshConnections.disabled = state.connectionAction.inFlight;
  }
  if (els.modalDashboardDiscoverMetatrader) {
    els.modalDashboardDiscoverMetatrader.hidden = !canDiscoverMetatrader;
    els.modalDashboardDiscoverMetatrader.disabled = state.connectionAction.inFlight;
  }
  if (els.modalDashboardConnectionActionStatus) {
    els.modalDashboardConnectionActionStatus.dataset.tone = actionMatches ? state.connectionAction.tone : "neutral";
    els.modalDashboardConnectionActionStatus.textContent = actionMatches && state.connectionAction.message
      ? safeDashboardDisplayText(state.connectionAction.message)
      : "ปุ่มนี้ส่งคำขอแบบอ่านอย่างเดียวไปยัง Local Runner และไม่เปิดเผย Path, PID หรือข้อมูลลับ";
  }
}

function refreshOpenDashboardConnectionPanel() {
  if (!state.modal.open || state.modal.type !== "prop") return;
  const subject = getModalSubject();
  if (!subject || getModalSurface("prop", subject.id) !== "dashboard") return;
  renderDashboardConnectionPanel(subject, getPropertyRole(subject));
}

function structuredDashboardItems(value, section, status, owner) {
  if (value === null || value === undefined || value === "") return [];
  const rows = Array.isArray(value)
    ? value
    : (value && typeof value === "object" ? Object.entries(value).map(([name, detail]) => ({ name, detail })) : [value]);
  return rows.slice(0, 8).map((row, index) => {
    if (row && typeof row === "object" && !Array.isArray(row)) {
      const rawRowTitle = row.title || row.label || row.name || row.id || `${section} ${index + 1}`;
      const rowTitle = section === "ตัวชี้วัด" ? dashboardFieldLabel(rawRowTitle) : rawRowTitle;
      const rowDetail = row.detail ?? row.summary ?? row.message ?? row.value ?? row.finding ?? row.action ?? row.risk ?? row;
      return {
        title: safeDashboardDisplayText(`${section}: ${rowTitle}`),
        detail: safeDashboardDisplayText(section === "ตัวชี้วัด" ? dashboardMetricValue(rawRowTitle, rowDetail) : formatDashboardValue(rowDetail)),
        status: row.status || status,
        owner: row.ownerAgentId || row.owner || owner,
      };
    }
    return {
      title: `${section} ${index + 1}`,
      detail: safeDashboardDisplayText(formatDashboardValue(row)),
      status,
      owner,
    };
  });
}

function reportExecutionScope(item) {
  const executionTypes = new Set([
    "code_change_report",
    "backtest_report",
    "backtest_optimization_report",
    "optimization_report",
  ]);
  if (!executionTypes.has(String(item?.type || ""))) return null;
  const evidence = item?.executionEvidence && typeof item.executionEvidence === "object"
    ? item.executionEvidence
    : {};
  const verified = evidence.mtExecutionVerified === true;
  return {
    verified,
    label: safeDashboardDisplayText(
      evidence.scopeLabelTh,
      verified
        ? "ยืนยันผลจาก MT4/MT5 แบบมองเห็นโปรแกรม"
        : "วิเคราะห์โค้ดหรือรายงานที่มีอยู่ ยังไม่ได้ยืนยันการรัน MT4/MT5 จริง",
    ),
  };
}

function structuredReportItems(item) {
  const owner = item?.ownerAgentId || item?.owner || "mission_archivist";
  const executionScope = reportExecutionScope(item);
  return [
    {
      title: safeDashboardDisplayText(item?.title || item?.id || "รายงานแบบมีโครงสร้าง"),
      detail: safeDashboardDisplayText(item?.summary || displayStatus(item?.status) || "รายงานนี้ถูกส่งมาที่ Dashboard แล้ว"),
      status: item?.status || "ready",
      owner,
    },
    ...(executionScope ? [{
      title: "ขอบเขตของผลลัพธ์",
      detail: executionScope.label,
      status: executionScope.verified ? "verified" : "analysis_only",
      owner: "Local Runner",
    }] : []),
    ...structuredDashboardItems(item?.findings, "สิ่งที่พบ", "finding", owner),
    ...structuredDashboardItems(item?.metrics, "ตัวชี้วัด", "metric", owner),
    ...structuredDashboardItems(item?.risks, "ความเสี่ยง", "risk", owner),
    ...structuredDashboardItems(item?.nextActions, "ขั้นตอนถัดไป", "next_action", owner),
  ];
}

function capabilityDashboardItems(capabilities) {
  if (!Array.isArray(capabilities)) return [];
  return capabilities.slice(0, 12).map((capability, index) => {
    const label = CAPABILITY_DISPLAY[capability?.id] || capability?.label || capability?.id || `ความสามารถ ${index + 1}`;
    const detail = [
      capability?.message,
      capability?.runtimeStatus ? `สถานะระบบ ${displayStatus(capability.runtimeStatus)}` : "",
      capability?.adapterStatus ? `ตัวเชื่อม ${displayStatus(capability.adapterStatus)}` : "",
      capability?.defaultMode ? `โหมด ${displayStatus(capability.defaultMode)}` : "",
      capability?.risk ? `ความเสี่ยง ${displayRisk(capability.risk)}` : "",
      capability?.approvalRequired ? "ต้องขออนุมัติ" : "",
      capability?.runtimeReady === true ? "ระบบพร้อม" : "ระบบยังไม่พร้อม",
      capability?.realExecutionAvailable === true ? "งานจริงอยู่หลังระบบป้องกันของ Backend" : "หน้าดูข้อมูลหรือ Demo เท่านั้น",
    ].filter(Boolean).join(" | ");
    return {
      title: `ความสามารถ: ${label}`,
      detail: detail || "สถานะนี้มาจาก Local Bridge",
      status: capability?.runtimeStatus || capability?.adapterStatus || capability?.status || capability?.defaultMode || "unknown",
      owner: capability?.ownerAgentId || "Local Runner",
    };
  });
}

function bridgeDashboardItems(bridge) {
  if (!bridge || typeof bridge !== "object") return [];
  const rows = [];
  if (bridge.status || bridge.mode) {
    rows.push({
      title: "ความพร้อมของ Bridge",
      detail: `โหมด ${displayBridgeValue(bridge.mode)} • สถานะ ${displayBridgeValue(bridge.status)}`,
      status: bridge.status || "unknown",
      owner: "codex_mcp_operator",
    });
  }
  ["codex", "mcp"].forEach((id) => {
    const value = bridge[id];
    if (!value || typeof value !== "object") return;
    rows.push({
      title: `สถานะ ${id.toUpperCase()}`,
      detail: `สถานะ ${displayBridgeValue(value.status)}`,
      status: value.status || "unknown",
      owner: "codex_mcp_operator",
    });
  });
  return rows;
}

function meetingDashboardItems(meetings) {
  const rows = Array.isArray(meetings)
    ? meetings
    : (Array.isArray(meetings?.items) ? meetings.items : (Array.isArray(meetings?.meetings) ? meetings.meetings : []));
  return rows.slice(0, 5).map((meeting, index) => ({
    title: `การประชุม: ${meeting?.title || meeting?.id || index + 1}`,
    detail: meeting?.summary || meeting?.agenda || meeting?.message || "บันทึกการประชุมนี้ถูกส่งมาที่ Dashboard แล้ว",
    status: meeting?.status || meeting?.kind || "meeting",
    owner: meeting?.ownerAgentId || meeting?.hostAgentId || "manager",
  }));
}

function renderDashboardKpis(subject, report, missions) {
  if (!els.modalDashboardKpis) return;
  els.modalDashboardKpis.innerHTML = "";
  const openStatuses = new Set(["queued", "running", "waiting_approval", "blocked"]);
  const openCount = missions.filter((mission) => openStatuses.has(getMissionPresentationStatus(mission))).length;
  const latestReport = Array.isArray(report?.reports) ? report.reports[0] : null;
  const reportMetrics = Object.entries(latestReport?.metrics || {}).slice(0, 3);
  const capabilitySummary = report?.capabilitySummary || null;
  const kpis = [
    ["งานที่ยังเปิดอยู่", String(openCount), openCount ? "active" : "calm"],
    ["รายงาน", String(report?.reports?.length || 0), "report"],
    ["สถานะจุดทำงาน", displayStatus(subject.status || "ready"), "status"],
    ["Bridge", state.bridge.apiOnline ? displayBridgeValue(state.bridge.mode) : "ออฟไลน์", state.bridge.apiOnline ? "online" : "offline"],
    ...(capabilitySummary ? [
      ["ความสามารถ", String(capabilitySummary.total || 0), "status"],
      ["ระบบพร้อม", `${capabilitySummary.runtimeReady || 0}/${capabilitySummary.total || 0}`, "online"],
      ["ต้องผ่านการอนุมัติ", String(capabilitySummary.approvalGated || 0), "active"],
    ] : []),
    ...reportMetrics.map(([name, value]) => [safeDashboardDisplayText(dashboardFieldLabel(name)), safeDashboardDisplayText(dashboardMetricValue(name, value)), "metric"]),
  ];
  kpis.forEach(([label, value, tone]) => {
    const card = document.createElement("div");
    const name = document.createElement("span");
    const metric = document.createElement("strong");
    card.className = `dashboard-kpi ${tone}`;
    name.textContent = safeDashboardDisplayText(label);
    metric.textContent = safeDashboardDisplayText(value);
    card.append(name, metric);
    els.modalDashboardKpis.appendChild(card);
  });
}

const AI_TRADE_COUNCIL_PROP_ID = "left_analytics_console";
const SIGNAL_DEEP_ANALYSIS_TABS = ["price_action", "technical_deep", "news_context"];
const SIGNAL_CONSENSUS_TABS = ["daily_summary", "live_analysis", "decision_pipeline", "history"];
const SIGNAL_LIVE_ANALYSIS_TABS = ["chart_overview", ...SIGNAL_DEEP_ANALYSIS_TABS];
const SIGNAL_DEEP_TAB_DEFINITIONS = Object.freeze([
  {
    id: "price_action",
    tabId: "signalConsensusPriceActionTab",
    panelId: "signalConsensusPriceActionPanel",
    contentId: "signalConsensusPriceActionContent",
    label: "กราฟเปล่าและโครงสร้างราคา",
  },
  {
    id: "technical_deep",
    tabId: "signalConsensusTechnicalTab",
    panelId: "signalConsensusTechnicalPanel",
    contentId: "signalConsensusTechnicalContent",
    label: "Technical ย้อนหลัง",
  },
  {
    id: "news_context",
    tabId: "signalConsensusNewsTab",
    panelId: "signalConsensusNewsPanel",
    contentId: "signalConsensusNewsContent",
    label: "ข่าวและบริบทตลาด",
  },
]);
const AI_TRADE_COUNCIL_AGENT_IDS = [
  "optimization_agent",
  "backtest_analyst",
  "codex_mcp_operator",
];
const signalChartDataByCanvas = new WeakMap();

function ensureSignalLiveAnalysisTabs() {
  els.signalConsensusLiveTabs = document.getElementById("signalConsensusLiveTabs");
  els.signalConsensusLiveOverviewContent = document.getElementById("signalConsensusLiveOverviewContent");
  SIGNAL_DEEP_TAB_DEFINITIONS.forEach((definition) => {
    const elementKey = definition.id === "price_action"
      ? "signalConsensusPriceActionContent"
      : definition.id === "technical_deep"
        ? "signalConsensusTechnicalContent"
        : "signalConsensusNewsContent";
    els[elementKey] = document.getElementById(definition.contentId);
  });

  if (!els.signalConsensusTabs) return;
  const numberByTab = new Map(SIGNAL_CONSENSUS_TABS.map((tabName, index) => [tabName, index + 1]));
  [...els.signalConsensusTabs.querySelectorAll("[data-signal-tab]")].forEach((tab) => {
    const number = tab.querySelector("span[aria-hidden='true']");
    if (number) number.textContent = String(numberByTab.get(tab.dataset.signalTab) || "");
  });
}

function normalizeSignalDisplayBars(value) {
  const parsed = Number(value);
  return SIGNAL_CHART_DISPLAY_BAR_OPTIONS.includes(parsed)
    ? parsed
    : SIGNAL_CHART_DEFAULT_DISPLAY_BARS;
}

function normalizeSignalAnalysisBars(value) {
  const parsed = Number(value);
  return SIGNAL_ANALYSIS_BAR_OPTIONS.includes(parsed)
    ? parsed
    : SIGNAL_DEFAULT_ANALYSIS_BARS;
}

function normalizeSignalRequiredVotes(value) {
  const parsed = Math.trunc(Number(value));
  return [1, 2, 3].includes(parsed) ? parsed : 3;
}

function signalCouncilModel(report = {}) {
  return report?.aiTradeCouncil && typeof report.aiTradeCouncil === "object"
    ? report.aiTradeCouncil
    : {};
}

function signalSnapshotChannel(report = {}) {
  const council = signalCouncilModel(report);
  const values = [
    report?.metatraderReadOnly?.installPreparation?.snapshotChannel,
    council?.tradeGateway?.selectedCandidateId,
    report?.metatraderReadOnly?.selectedCandidateId,
    report?.connectionChecklist?.metatraderSelection?.selectedCandidate?.candidateId,
  ];
  for (const value of values) {
    const channel = safeDashboardDisplayText(value, "").trim();
    if (/^mtc-[A-Za-z0-9_-]{1,116}$/.test(channel)) return channel;
  }
  return "";
}

function signalConnectionItem(report = {}, itemId = "") {
  const items = Array.isArray(report?.connectionChecklist?.items)
    ? report.connectionChecklist.items
    : [];
  return items.find((item) => item?.id === itemId) || null;
}

function signalConnectionIsReady(item = null) {
  const status = String(item?.status || "").trim().toLowerCase();
  const adapterStatus = String(item?.adapterStatus || "").trim().toLowerCase();
  return ["ready", "connected", "configured", "implemented"].includes(status)
    && !["disabled", "coming_soon", "contract_only"].includes(adapterStatus);
}

function signalGatewayInitStatusMessage(initStatus = {}) {
  if (!initStatus || initStatus.available !== true) return null;
  const severity = String(initStatus.severity || "").toLowerCase();
  const warningCode = String(initStatus.warningCode || "").toUpperCase();
  const reasonCode = String(initStatus.reasonCode || "").toUpperCase();
  const superseded = initStatus.supersededByLiveStatus === true;
  const stale = initStatus.stale === true;
  if ((stale && superseded) || (severity === "error" && superseded)) return null;
  if (!["error", "warning"].includes(severity) && !warningCode) return null;
  const code = warningCode || reasonCode;
  const labels = {
    SNAPSHOT_CHANNEL_INVALID: "Channel ID ไม่ถูกต้อง",
    LIVE_SIGNING_KEY_PIN_INVALID: "Key ID สำหรับโหมด Live มีรูปแบบไม่ถูกต้อง",
    OPTIONAL_SIGNING_KEY_PIN_INVALID_IGNORED: "Key ID ที่ใส่ใน Demo หรือ Shadow ไม่ถูกต้อง ระบบจึงไม่ใช้ค่านี้",
    OPTIONAL_SIGNING_KEY_PIN_MISMATCH_IGNORED: "Key ID ที่ใส่ใน Demo หรือ Shadow ไม่ตรงกับ Backend ระบบจึงใช้ค่าจาก Backend",
    CRYPTO_SELF_TEST_FAILED: "การตรวจระบบลายเซ็น HMAC-SHA256 ไม่ผ่าน",
    GATEWAY_INPUT_CONFIGURATION_INVALID: "ค่าตั้งต้นของ EA ไม่ผ่านการตรวจสอบ",
    SYMBOL_OR_TIMEFRAME_NOT_ALLOWED: "คู่เงินหรือ Timeframe ของกราฟไม่อยู่ในรายการที่อนุญาต",
    SNAPSHOT_CHANNEL_ALREADY_OWNED: "มี EA อีกตัวใช้ Channel ID นี้อยู่แล้ว",
    GATEWAY_TIMER_START_FAILED: "EA เริ่มตัวจับเวลาเบื้องหลังไม่สำเร็จ",
    INITIAL_SNAPSHOT_WRITE_FAILED: "EA เขียน Snapshot แรกไม่สำเร็จ",
    INITIAL_CAPABILITIES_WRITE_FAILED: "EA เขียนข้อมูลความสามารถเริ่มต้นไม่สำเร็จ",
    INITIAL_STATUS_WRITE_FAILED: "EA เขียนสถานะเริ่มต้นไม่สำเร็จ",
  };
  const detail = labels[code] || "การเริ่มทำงานของ EA มีรายการที่ต้องตรวจสอบ";
  const oldData = stale ? " ข้อมูลนี้เก่าและใช้เพื่อช่วยวินิจฉัยเท่านั้น" : "";
  return {
    tone: severity === "error" ? "error" : "warning",
    text: severity === "error"
      ? `EA เริ่มทำงานไม่สำเร็จ: ${detail}.${oldData}`.trim()
      : `EA เริ่มทำงานแล้ว แต่มีคำเตือน: ${detail}.${oldData}`.trim(),
  };
}

function signalCommandMatchesCurrentRound(command = null, context = {}) {
  if (!command || typeof command !== "object" || context.current !== true) return false;
  const expectedMissionId = String(context.missionId || "");
  const commandMissionId = String(command.sourceMissionId || command.missionId || "");
  if (!expectedMissionId || !commandMissionId || commandMissionId !== expectedMissionId) return false;
  const expectedSnapshotId = String(context.snapshotId || "");
  const commandSnapshotId = String(command.snapshotId || "");
  return Boolean(expectedSnapshotId)
    && Boolean(commandSnapshotId)
    && commandSnapshotId === expectedSnapshotId;
}

function getSignalRuntimeTruth(report = {}) {
  const council = signalCouncilModel(report);
  const supplied = council.runtimeTruth || {};
  const gateway = council.tradeGateway && typeof council.tradeGateway === "object"
    ? council.tradeGateway
    : (supplied.tradeGateway && typeof supplied.tradeGateway === "object" ? supplied.tradeGateway : {});
  const run = signalCouncilRunModel(report);
  const consensusSelection = signalCurrentConsensusSource(report, run);
  const currentConsensus = consensusSelection.current ? consensusSelection.source : {};
  const consensusGateway = currentConsensus?.tradeGateway && typeof currentConsensus.tradeGateway === "object"
    ? currentConsensus.tradeGateway
    : {};
  const commandCorrelation = {
    current: consensusSelection.current,
    missionId: String(currentConsensus?.sourceMissionId || run.parent?.id || ""),
    snapshotId: String(currentConsensus?.snapshotId || run.snapshotId || ""),
  };
  const activeCommand = gateway.activeCommand && typeof gateway.activeCommand === "object"
    ? gateway.activeCommand
    : null;
  const consensusCommand = consensusGateway.command && typeof consensusGateway.command === "object"
    ? consensusGateway.command
    : null;
  const latestCommand = gateway.latestCommand && typeof gateway.latestCommand === "object"
    ? gateway.latestCommand
    : null;
  const gatewayCommand = [activeCommand, consensusCommand, latestCommand]
    .find((command) => signalCommandMatchesCurrentRound(command, commandCorrelation)) || null;
  const gatewayLastAck = gatewayCommand?.ack && typeof gatewayCommand.ack === "object"
    ? gatewayCommand.ack
    : (consensusGateway.ackStatus
      ? {
        status: consensusGateway.ackStatus,
        reasonCode: consensusGateway.reasonCode,
      }
      : null);
  const suppliedTerminal = supplied?.terminalDetection || {};
  const suppliedTradingState = supplied?.tradingStateAdapter || {};
  const suppliedEnsemble = supplied?.ensemble || {};
  const checklist = report?.connectionChecklist || {};
  const selection = checklist?.metatraderSelection || {};
  const checklistSelectedCandidateId = safeDashboardDisplayText(
    selection?.selectedCandidate?.candidateId,
    "",
  );
  const gatewaySelectedCandidateId = gateway.connected === true
    ? safeDashboardDisplayText(gateway.selectedCandidateId, "")
    : "";
  const tradingStateItem = signalConnectionItem(report, "trading_state_adapter");
  const ensembleItem = signalConnectionItem(report, "ai_trader_ensemble");
  const riskPolicyItem = signalConnectionItem(report, "risk_policy");
  const killSwitchItem = signalConnectionItem(report, "kill_switch_adapter");
  const liveTradingItem = signalConnectionItem(report, "live_trading");
  const terminalDetected = Boolean(
    Number(selection?.candidateCount || 0) > 0
    || supplied?.terminalDetected === true
    || suppliedTerminal?.detected === true
    || suppliedTerminal?.processDetected === true
    || suppliedTerminal?.adapterReady === true
    || gateway.connected === true,
  );
  const terminalSelected = Boolean(
    (checklistSelectedCandidateId || gatewaySelectedCandidateId)
    && supplied?.terminalSelected !== false
    && suppliedTerminal?.selected !== false,
  );
  const tradingStateAvailable = (supplied?.tradingStateAvailable === true || suppliedTradingState?.available === true)
    && signalConnectionIsReady(tradingStateItem);
  const ensembleAvailable = (supplied?.ensembleAvailable === true || suppliedEnsemble?.available === true)
    && signalConnectionIsReady(ensembleItem);
  const gatewayConnected = gateway.connected === true;
  const gatewayMode = safeDashboardDisplayText(gateway.mode, "not_observed").toLowerCase();
  const gatewayExecutionGuardReason = safeDashboardDisplayText(
    gateway.executionGuardReason,
    "ยังไม่ได้รับสถานะจาก EA",
  );
  const gatewayAccount = gateway.account && typeof gateway.account === "object"
    ? gateway.account
    : {};
  const explicitDemoFlag = [
    gateway.isDemoAccount,
    gateway.accountIsDemo,
    gateway.demoAccount,
    gatewayAccount.isDemo,
    gatewayAccount.demo,
  ].find((value) => typeof value === "boolean");
  const gatewayAccountTypeRaw = safeDashboardDisplayText(
    gateway.accountType
      || gateway.accountMode
      || gateway.accountEnvironment
      || gatewayAccount.type
      || gatewayAccount.mode
      || gatewayAccount.environment,
    "",
  ).toLowerCase();
  const gatewayIsDemoAccount = typeof explicitDemoFlag === "boolean"
    ? explicitDemoFlag
    : gatewayAccountTypeRaw.includes("demo")
      ? true
      : ["real", "live", "production"].some((name) => gatewayAccountTypeRaw.includes(name))
        ? false
        : null;
  const gatewayModeAccountMismatchReason = [
    "LIVE_MODE_REQUIRES_NON_DEMO_ACCOUNT",
    "DEMO_MODE_REQUIRES_DEMO_ACCOUNT",
  ].includes(gatewayExecutionGuardReason.toUpperCase())
    ? gatewayExecutionGuardReason.toUpperCase()
    : gatewayMode === "live" && gatewayIsDemoAccount === true
      ? "LIVE_MODE_REQUIRES_NON_DEMO_ACCOUNT"
      : gatewayMode === "demo" && gatewayIsDemoAccount === false
        ? "DEMO_MODE_REQUIRES_DEMO_ACCOUNT"
        : "";
  const gatewayBackend = gateway?.backend && typeof gateway.backend === "object"
    ? gateway.backend
    : {};
  const gatewayInit = gateway?.initStatus && typeof gateway.initStatus === "object"
    ? gateway.initStatus
    : {};
  const killSwitchActive = gateway.killSwitchActive === true;
  const tradingKillSwitchAvailable = gateway.killSwitchAvailable === true
    || supplied?.tradingKillSwitchAvailable === true
    || signalConnectionIsReady(killSwitchItem);
  const liveTradingEnabled = gateway.liveOrderExecutionAvailable === true;
  const gatewayNumber = (name) => {
    const value = gateway?.[name];
    if (value === null || value === undefined || value === "" || typeof value === "boolean") return null;
    return Number.isFinite(Number(value)) ? Number(value) : null;
  };

  return {
    scope: safeDashboardDisplayText(supplied?.scope, "terminal_detection_only"),
    terminalDetected,
    terminalSelected,
    selectedCandidateId: gatewaySelectedCandidateId || checklistSelectedCandidateId,
    tradingStateAvailable,
    positionsAvailable: tradingStateAvailable && supplied?.positionsAvailable === true,
    latestSignalAvailable: tradingStateAvailable && supplied?.latestSignalAvailable === true,
    ensembleAvailable,
    missionRiskGuardAvailable: supplied?.missionRiskGuardAvailable === true
      || signalConnectionIsReady(riskPolicyItem),
    tradingKillSwitchAvailable,
    killSwitchActive,
    gatewayConnected,
    gatewayMode,
    gatewayLiveArmed: gateway.liveArmed === true,
    signedCommandRequiredForLive: gatewayBackend.signedCommandRequiredForLive === true,
    backendSignedCommandVerificationAvailable: gatewayBackend.signedCommandVerificationAvailable === true,
    signedCommandVerificationAvailable: gateway.signedCommandVerificationAvailable === true,
    activeSigningKeyId: safeDashboardDisplayText(gateway.activeSigningKeyId, ""),
    backendSigningKeyId: safeDashboardDisplayText(gatewayBackend.activeSigningKeyId, ""),
    signingKeyPinned: gateway.signingKeyPinned === true,
    signingKeyMatch: gateway.signingKeyMatch === true,
    signatureAlgorithm: safeDashboardDisplayText(
      gateway.signatureAlgorithm || gatewayBackend.signatureAlgorithm,
      "",
    ),
    lastSignatureVerificationStatus: safeDashboardDisplayText(
      gateway.lastSignatureVerificationStatus,
      "",
    ),
    liveExecutionAvailable: gatewayBackend.liveExecutionAvailable === true,
    liveBlockReason: safeDashboardDisplayText(
      gatewayBackend.liveBlockReason || gateway.liveBlockReason,
      "",
    ),
    gatewayStatus: safeDashboardDisplayText(gateway.status, gatewayConnected ? "connected" : "not_connected"),
    gatewayInitStatus: {
      available: gatewayInit.available === true,
      readStatus: safeDashboardDisplayText(gatewayInit.readStatus, "not_observed"),
      eaVersion: safeDashboardDisplayText(gatewayInit.eaVersion, ""),
      severity: safeDashboardDisplayText(gatewayInit.severity, ""),
      stage: safeDashboardDisplayText(gatewayInit.stage, ""),
      reasonCode: safeDashboardDisplayText(gatewayInit.reasonCode, ""),
      warningCode: safeDashboardDisplayText(gatewayInit.warningCode, ""),
      observedAt: safeDashboardDisplayText(gatewayInit.observedAt, ""),
      ageSeconds: Number.isFinite(Number(gatewayInit.ageSeconds)) ? Number(gatewayInit.ageSeconds) : null,
      stale: gatewayInit.stale === true,
      supersededByLiveStatus: gatewayInit.supersededByLiveStatus === true,
    },
    gatewayAccountType: gatewayAccountTypeRaw,
    gatewayIsDemoAccount,
    gatewayModeAccountMismatch: Boolean(gatewayModeAccountMismatchReason),
    gatewayModeAccountMismatchReason,
    gatewayFixedLot: Number.isFinite(Number(gateway.fixedLot)) ? Number(gateway.fixedLot) : null,
    gatewayExecutionGuardReady: gateway.executionGuardReady === true,
    gatewayExecutionGuardReason,
    gatewayRiskTelemetry: {
      maxManagedPositions: gatewayNumber("maxManagedPositions"),
      currentManagedPositions: gatewayNumber("currentManagedPositions"),
      maxManagedLots: gatewayNumber("maxManagedLots"),
      currentManagedLots: gatewayNumber("currentManagedLots"),
      maxTradesToday: gatewayNumber("maxTradesToday"),
      currentTradesToday: gatewayNumber("currentTradesToday"),
      maxLossPerTradePercent: gatewayNumber("maxLossPerTradePercent"),
      maxDailyLossPercent: gatewayNumber("maxDailyLossPercent"),
      managedDailyPnl: gatewayNumber("managedDailyPnl"),
      maxAccountEquityDrawdownPercent: gatewayNumber("maxAccountEquityDrawdownPercent"),
      currentAccountEquityDrawdownPercent: gatewayNumber("currentAccountEquityDrawdownPercent"),
      minRewardRiskRatio: gatewayNumber("minRewardRiskRatio"),
      minProjectedMarginLevelPercent: gatewayNumber("minProjectedMarginLevelPercent"),
      currentMarginLevelPercent: gatewayNumber("currentMarginLevelPercent"),
      maxSnapshotAgeSeconds: gatewayNumber("maxSnapshotAgeSeconds"),
      maxSignalDriftPoints: gatewayNumber("maxSignalDriftPoints"),
      maxQuoteAgeSeconds: gatewayNumber("maxQuoteAgeSeconds"),
    },
    gatewayCommand,
    gatewayLatestHistoricalCommand: latestCommand,
    gatewayCommandMatchesCurrentRound: Boolean(gatewayCommand),
    gatewayCommandStatus: safeDashboardDisplayText(
      gatewayCommand?.status || consensusGateway.status,
      gatewayConnected
        ? gateway.executionGuardReady === true
          ? "พร้อมรับคำสั่งรอบใหม่"
          : signalExecutionGuardReasonLabel(gatewayExecutionGuardReason)
        : "ยังไม่เชื่อม EA",
    ),
    gatewayCommandPublished: consensusGateway.commandPublished === true
      || Boolean(gatewayCommand?.commandId),
    gatewayLastAck,
    liveTradingEnabled,
    orderSubmissionAvailable: gatewayConnected
      && !killSwitchActive
      && (gatewayMode === "shadow" || gateway.executionGuardReady === true),
    demoOrderExecutionAvailable: gateway.demoOrderExecutionAvailable === true,
    shadowValidationAvailable: gateway.shadowValidationAvailable === true,
    liveOrderExecutionAvailable: gateway.liveOrderExecutionAvailable === true,
    summaryTh: safeDashboardDisplayText(
      supplied?.summaryTh || supplied?.messageTh,
      terminalDetected
        ? "ตรวจพบโปรแกรม MT4/MT5 แบบอ่านอย่างเดียว แต่ยังไม่มีข้อมูลกราฟหรือผลโหวตจาก Adapter"
        : "ยังไม่พบข้อมูลจาก MT4/MT5 และยังไม่เริ่มการวิเคราะห์",
    ),
  };
}

function signalMarketModel(report = {}) {
  const council = signalCouncilModel(report);
  const live = council.liveAnalysis || {};
  const market = live.market && typeof live.market === "object" ? live.market : {};
  const chartSnapshot = council.chartSnapshot && typeof council.chartSnapshot === "object"
    ? council.chartSnapshot
    : {};
  const selection = report?.connectionChecklist?.metatraderSelection || {};
  const selectedCandidate = selection?.selectedCandidate || null;
  const observedAt = market.observedAt || live.observedAt || chartSnapshot.observedAt || null;
  return {
    terminal: selectedCandidate?.labelTh || selectedCandidate?.platform?.toUpperCase?.() || "ยังไม่ได้เลือก",
    symbol: safeDashboardDisplayText(market.symbol || chartSnapshot.symbol, "ยังไม่มีข้อมูล"),
    timeframe: safeDashboardDisplayText(market.timeframe || chartSnapshot.timeframe, "ยังไม่มีข้อมูล"),
    observedAt,
    freshnessMinutes: Number.isFinite(Number(market.freshnessMinutes))
      ? Number(market.freshnessMinutes)
      : Number.isFinite(Number(chartSnapshot.ageSeconds))
        ? Math.round((Number(chartSnapshot.ageSeconds) / 60) * 10) / 10
        : null,
    spread: firstFiniteSignalNumber(market.spread, market.spreadPoints, chartSnapshot.spreadPoints),
    snapshotId: safeDashboardDisplayText(live.snapshotId || market.snapshotId || chartSnapshot.snapshotId, ""),
    available: market.available === true || chartSnapshot.available === true,
  };
}

function firstFiniteSignalNumber(...values) {
  for (const value of values) {
    if (value === null || value === undefined || value === "") continue;
    const number = Number(value);
    if (Number.isFinite(number)) return number;
  }
  return null;
}

function formatSignalNumber(value, { signed = false, suffix = "" } = {}) {
  if (!Number.isFinite(value)) return "ยังไม่มีข้อมูล";
  const sign = signed && value > 0 ? "+" : "";
  return `${sign}${value.toLocaleString("th-TH", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}${suffix}`;
}

function signalDailySummaryModel(report = {}) {
  const council = signalCouncilModel(report);
  const source = council.dailySummary && typeof council.dailySummary === "object"
    ? council.dailySummary
    : {};
  const chartSnapshot = council.chartSnapshot && typeof council.chartSnapshot === "object"
    ? council.chartSnapshot
    : {};
  const account = source.account && typeof source.account === "object"
    ? source.account
    : (chartSnapshot.account && typeof chartSnapshot.account === "object" ? chartSnapshot.account : {});
  const activity = source.activity && typeof source.activity === "object" ? source.activity : source;
  const realized = firstFiniteSignalNumber(
    source.realizedProfitToday,
    source.realizedToday,
    source.realizedProfit,
    source.closedProfitToday,
    activity.realizedProfitToday,
  );
  const floating = firstFiniteSignalNumber(
    source.floatingProfit,
    source.openProfit,
    account.floatingProfit,
  );
  const suppliedNet = firstFiniteSignalNumber(source.netProfitToday, source.netPnl, source.profitToday);
  const net = suppliedNet ?? (
    realized !== null && floating !== null ? realized + floating : null
  );
  const trades = firstFiniteSignalNumber(source.tradesToday, source.tradesClosed, activity.tradeCount, activity.trades);
  const wins = firstFiniteSignalNumber(source.winsToday, activity.wins);
  const losses = firstFiniteSignalNumber(source.lossesToday, activity.losses);
  const suppliedWinRate = firstFiniteSignalNumber(source.winRate, activity.winRate);
  const winRate = suppliedWinRate ?? (
    wins !== null && losses !== null && wins + losses > 0
      ? (wins / (wins + losses)) * 100
      : null
  );
  const readiness = council.analysisReadiness && typeof council.analysisReadiness === "object"
    ? council.analysisReadiness
    : {};
  const available = source.available === true;
  return {
    available,
    status: safeDashboardDisplayText(source.status, available ? "ready" : "adapter_missing"),
    observedAt: source.observedAt || chartSnapshot.observedAt || null,
    tradingDate: source.tradingDate || source.serverDay || null,
    currency: safeDashboardDisplayText(source.currency || account.currency, ""),
    net,
    realized,
    floating,
    balance: firstFiniteSignalNumber(source.balance, account.balance),
    equity: firstFiniteSignalNumber(source.equity, account.equity),
    drawdownPercent: firstFiniteSignalNumber(
      source.drawdownPercent,
      source.maxDrawdownPercentToday,
      account.drawdownPercent,
    ),
    trades,
    wins,
    losses,
    winRate,
    openPositions: firstFiniteSignalNumber(
      source.openPositions,
      source.positionsCount,
      chartSnapshot?.positionsSummary?.count,
    ),
    snapshotId: safeDashboardDisplayText(
      source.snapshotId || chartSnapshot.snapshotId || chartSnapshot.id,
      "",
    ),
    analysisReady: readiness.ready === true
      || (readiness.available === true && readiness.status === "ready")
      || (chartSnapshot.available === true && ["ready", "fresh"].includes(chartSnapshot.status)),
    readinessMessage: safeDashboardDisplayText(
      readiness.messageTh || source.messageTh,
      available
        ? "ได้รับข้อมูลจริงจาก MT4 ผ่าน Local Runner แล้ว"
        : "ยังไม่มีข้อมูลบัญชีจากตัวอ่าน MT4 แบบ Read-only",
    ),
  };
}

function signalCouncilAutomationModel(report = {}) {
  const council = signalCouncilModel(report);
  const supplied = council.autoAnalysis && typeof council.autoAnalysis === "object"
    ? council.autoAnalysis
    : (council.automation && typeof council.automation === "object" ? council.automation : {});
  const config = supplied.config && typeof supplied.config === "object" ? supplied.config : supplied;
  const runtimeState = supplied.state && typeof supplied.state === "object" ? supplied.state : supplied;
  const supported = Array.isArray(config.supportedTimeframes)
    ? config.supportedTimeframes.map((item) => String(item || "").toUpperCase()).filter(Boolean)
    : ["M5", "M15", "M30", "H1", "H4", "D1", "W1", "MN1"];
  const status = safeDashboardDisplayText(
    runtimeState.status || runtimeState.lastStatus || supplied.status,
    config.enabled ? "watching" : "disabled",
  ).toLowerCase();
  const reason = safeDashboardDisplayText(
    runtimeState.reason || runtimeState.lastReason || supplied.reason,
    "",
  );
  const reasonLabels = {
    automation_disabled: "ปิดการวิเคราะห์อัตโนมัติอยู่",
    baseline_required: "กำลังตั้งแท่งปัจจุบันเป็นจุดเริ่ม โดยจะไม่เรียกงานย้อนหลัง",
    baseline_set: "ตั้งจุดเริ่มแล้ว และกำลังรอแท่งปิดถัดไป",
    waiting_new_bar: "ยังเป็นแท่งเดิม จึงยังไม่เรียก Codex",
    unsupported_timeframe: "กรอบเวลานี้ใช้ปุ่มวิเคราะห์เองเพื่อป้องกันการใช้ Rate Limit ถี่เกินไป",
    full_access_required: "เปิด Full Access ก่อน ระบบจึงจะสร้าง Mission อัตโนมัติได้",
    terminal_not_selected: "กรุณาเลือก MT4 เป้าหมายก่อน",
    snapshot_missing: "ยังไม่พบ Snapshot จาก MT4",
    snapshot_not_ready: "Snapshot ยังไม่พร้อมสำหรับการวิเคราะห์",
    snapshot_stale: "Snapshot เก่าเกินกำหนด กำลังรอข้อมูลใหม่จาก MT4",
    closed_bar_identity_unavailable: "ยังอ่านเวลาแท่งปิดล่าสุดไม่ได้",
    codex_auth_required: "Codex ต้อง Login ก่อน",
    codex_runner_unavailable: "Codex Runner ยังไม่พร้อม",
    rate_limit_unavailable: "ยังอ่าน Rate Limit ของ Codex ไม่ได้ จึงพักไว้ก่อน",
    rate_limit_reached: "Rate Limit เต็มแล้ว จึงพักการวิเคราะห์อัตโนมัติ",
    quota_reserve: "Rate Limit คงเหลือต่ำกว่าค่าสำรองที่กำหนด",
    daily_cap_reached: "ครบจำนวนรอบวิเคราะห์อัตโนมัติของวันนี้แล้ว",
    mission_running: "กำลังรอ Council รอบก่อนหน้าทำเสร็จ",
    council_round_already_active: "กำลังรอ Council รอบก่อนหน้าทำเสร็จ",
    settle_window: "พบแท่งปิดใหม่แล้ว กำลังรอ Snapshot ให้นิ่งก่อนส่งวิเคราะห์",
    waiting_for_snapshot_settle: "พบแท่งปิดใหม่แล้ว กำลังรอ Snapshot ให้นิ่งก่อนส่งวิเคราะห์",
    codex_runner_not_ready: "Codex Runner ยังไม่พร้อม",
    remaining_percent_below_reserve: "Rate Limit คงเหลือต่ำกว่าค่าสำรองที่กำหนด",
    daily_round_limit_reached: "ครบจำนวนรอบวิเคราะห์อัตโนมัติของวันนี้แล้ว",
  };
  const currentTimeframe = safeDashboardDisplayText(
    runtimeState.timeframe || runtimeState.currentTimeframe || supplied.timeframe,
    "",
  ).toUpperCase();
  const currentSymbol = safeDashboardDisplayText(
    runtimeState.symbol || runtimeState.currentSymbol || supplied.symbol,
    "",
  );
  const enabled = config.enabled === true;
  const timeframeSupported = !currentTimeframe || supported.includes(currentTimeframe);
  const statusLabels = {
    disabled: "ปิดอยู่",
    idle: enabled ? "กำลังรอข้อมูล MT4" : "ปิดอยู่",
    baseline: "ตั้งจุดเริ่มแล้ว • รอแท่งใหม่",
    watching: "กำลังเฝ้าดูแท่งใหม่",
    pending: "พบแท่งใหม่ • รอข้อมูลนิ่ง",
    pending_settle: "พบแท่งใหม่ • รอข้อมูลนิ่ง",
    dispatching: "กำลังสร้างรอบวิเคราะห์",
    queued: "ส่งให้ Specialist 3 ตัวแล้ว",
    active_round: "รอรอบก่อนหน้าทำเสร็จ",
    unsupported_timeframe: "กรอบเวลานี้ใช้ปุ่มวิเคราะห์เอง",
    quota_guard: "พักเพื่อสำรอง Rate Limit",
    quota_unavailable: "พักเพราะยังอ่าน Rate Limit ไม่ได้",
    daily_limit: "ครบจำนวนรอบอัตโนมัติวันนี้",
    operator_mode: "พักจนกว่าจะเปิด Full Access",
    snapshot_unavailable: "รอ Snapshot จาก MT4",
    snapshot_stale: "รอ Snapshot ที่สด",
    error: "ระบบเฝ้าดูมีปัญหา",
  };
  return {
    available: supplied.available !== false,
    enabled,
    status,
    statusLabel: statusLabels[status] || (enabled ? "กำลังเฝ้าดูแท่งใหม่" : "ปิดอยู่"),
    reason,
    reasonMessage: reasonLabels[reason] || "",
    supported,
    currentTimeframe,
    currentSymbol,
    timeframeSupported,
    pollSeconds: Number(config.pollSeconds || supplied.pollSeconds || 5),
    settleSeconds: Number(config.settleSeconds || supplied.settleSeconds || 10),
    maxDailyRounds: Number(config.maxDailyRounds || config.maxDailyRuns || supplied.maxDailyRounds || 24),
    minRemainingPercent: Number(config.minRemainingPercent || supplied.minRemainingPercent || 30),
    analysisBarCount: normalizeSignalAnalysisBars(
      config.analysisBarCount || supplied.analysisBarCount,
    ),
    dailyRunCount: Number(runtimeState.dailyRunCount || supplied.dailyRunCount || 0),
    lastObservedClosedBarTime: runtimeState.lastObservedClosedBarTime || supplied.lastObservedClosedBarTime || null,
    lastAnalyzedClosedBarTime: runtimeState.lastAnalyzedClosedBarTime
      || runtimeState.lastQueuedClosedBarTime
      || supplied.lastAnalyzedClosedBarTime
      || null,
  };
}

function signalCouncilConsensusPolicyModel(report = {}) {
  const council = signalCouncilModel(report);
  const suppliedAutomation = council.autoAnalysis && typeof council.autoAnalysis === "object"
    ? council.autoAnalysis
    : (council.automation && typeof council.automation === "object" ? council.automation : {});
  const automationConfig = suppliedAutomation.config && typeof suppliedAutomation.config === "object"
    ? suppliedAutomation.config
    : suppliedAutomation;
  const policyCandidates = [
    council.consensusPolicy,
    automationConfig.consensusPolicy,
    council.decisionPipeline?.consensus?.policy,
    council.liveAnalysis?.consensus?.policy,
  ].filter((item) => item && typeof item === "object");
  const policy = policyCandidates[0] || {};
  const requiredVotes = normalizeSignalRequiredVotes(
    state.aiTradeCouncilConsensusPolicy.pendingRequiredVotes
      ?? automationConfig.requiredVotes
      ?? policy.requiredVotes
      ?? council.decisionPipeline?.consensus?.requiredVotes
      ?? council.liveAnalysis?.consensus?.requiredVotes,
  );
  const ruleByVotes = {
    1: "มี BUY หรือ SELL อย่างน้อย 1 เสียง และไม่มีเสียงฝั่งตรงข้าม ก็ผ่านด่านคะแนน โดย HOLD ไม่นับเป็นเสียงค้าน",
    2: "ต้องมี BUY หรือ SELL อย่างน้อย 2 เสียง และไม่มีเสียงฝั่งตรงข้าม จึงผ่านด่านคะแนน",
    3: "ต้องมี BUY หรือ SELL ตรงกันครบทั้ง 3 เสียง จึงผ่านด่านคะแนน",
  };
  return {
    requiredVotes,
    conflictVeto: policy.conflictVeto !== false
      && policy.oppositeDirectionVeto !== false
      && automationConfig.conflictVeto !== false,
    ruleText: ruleByVotes[requiredVotes],
  };
}

function createSignalDailyMetric(label, value, { tone = "neutral", detail = "" } = {}) {
  const card = document.createElement("article");
  const name = document.createElement("span");
  const metric = document.createElement("strong");
  const note = document.createElement("small");
  card.className = "signal-daily-metric";
  card.dataset.tone = tone;
  name.textContent = label;
  metric.textContent = value;
  note.textContent = detail;
  card.append(name, metric, note);
  return card;
}

function signalCouncilTeamViews() {
  return [
    {
      id: "optimization_agent",
      name: AI_TRADE_COUNCIL_PUBLIC_NAMES.optimization_agent,
      role: "ที่ปรึกษา Technical Analysis และ Indicator",
      promptSummary: "อ่านแนวโน้ม โมเมนตัม ความผันผวน และสภาวะตลาดจาก Snapshot เดียวกัน",
      number: "1",
    },
    {
      id: "backtest_analyst",
      name: AI_TRADE_COUNCIL_PUBLIC_NAMES.backtest_analyst,
      role: "ที่ปรึกษากราฟเปล่า Price Action และ HMC/ICT",
      promptSummary: "อ่านโครงสร้างราคา Trendline แนวรับแนวต้าน Liquidity และ HMC/ICT จากแท่งที่ปิดแล้ว",
      number: "2",
    },
    {
      id: "codex_mcp_operator",
      name: AI_TRADE_COUNCIL_PUBLIC_NAMES.codex_mcp_operator,
      role: "ที่ปรึกษาข่าวและสถานการณ์ระยะสั้น กลาง และยาว",
      promptSummary: "ค้นข่าวล่าสุดพร้อมเวลาและแหล่งอ้างอิง แล้วแยกผลกระทบระยะสั้น กลาง และยาว",
      number: "3",
    },
  ];
}

function signalAgentTone(view = {}) {
  if (view.state === "blocked") return "blocked";
  if (view.state === "running") return "working";
  if (view.direction === "BUY") return "buy";
  if (view.direction === "SELL") return "sell";
  if (view.direction === "HOLD") return "hold";
  if (view.state === "completed" || view.available) return "completed";
  return "waiting";
}

function signalAgentWorkStatus(view = {}) {
  const tone = signalAgentTone(view);
  return {
    tone,
    label: tone === "blocked"
      ? "ติดขัด"
      : tone === "working"
        ? "กำลังวิเคราะห์"
        : ["completed", "buy", "hold", "sell"].includes(tone)
          ? "เสร็จ"
          : "รอข้อมูล",
  };
}

function signalVoteLabel(value, fallback = "ยังไม่เริ่ม") {
  const normalized = String(value || "").trim().toUpperCase();
  if (normalized === "HOLD") return "งดออกเสียง";
  if (normalized === "NO_DATA") return "ข้อมูลไม่ครบ";
  if (normalized === "NO_TRADE" || normalized === "NO TRADE") return "ไม่เปิด Order";
  return normalized || fallback;
}

function signalGatewayModeAccountStatus(runtime = {}) {
  const mode = String(runtime.gatewayMode || "").trim().toLowerCase();
  const observed = runtime.gatewayIsDemoAccount !== null
    || Boolean(runtime.gatewayAccountType)
    || runtime.gatewayModeAccountMismatch === true;
  const accountLabel = runtime.gatewayIsDemoAccount === true
    ? "บัญชี Demo"
    : runtime.gatewayIsDemoAccount === false
      ? "บัญชีจริง"
      : runtime.gatewayAccountType
        ? `บัญชี ${String(runtime.gatewayAccountType).toUpperCase()}`
        : "ยังไม่ทราบประเภทบัญชี";
  const mismatch = runtime.gatewayModeAccountMismatch === true;
  return {
    observed,
    mismatch,
    ready: observed && !mismatch,
    accountLabel,
    value: mismatch
      ? `${mode.toUpperCase() || "EA"} ไม่ตรงกับ ${accountLabel}`
      : `${mode.toUpperCase() || "EA"} • ${accountLabel}`,
    detail: mismatch
      ? signalExecutionGuardReasonLabel(runtime.gatewayModeAccountMismatchReason)
      : "โหมด EA ตรงกับประเภทบัญชีที่ Backend ตรวจพบ",
  };
}

function signalAgentImagePath(agentId) {
  const liveAgent = getOfficeAgent(agentId);
  const definition = officeAgentDefinitions.find((agent) => agent.id === agentId);
  return liveAgent?.image || definition?.image || "";
}

function createSignalAgentSprite(view, { number = "" } = {}) {
  const workStatus = signalAgentWorkStatus(view);
  const button = document.createElement("button");
  const spriteWindow = document.createElement("span");
  const image = document.createElement("img");
  const fallback = document.createElement("span");
  const index = document.createElement("span");
  const imagePath = signalAgentImagePath(view.agentId);
  const initials = String(view.name || "AI")
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0])
    .join("")
    .toUpperCase() || "AI";

  button.type = "button";
  button.className = "signal-agent-sprite-button";
  button.dataset.workState = workStatus.tone;
  button.setAttribute("aria-label", `เปิดหน้าคุยกับ ${view.name}`);
  button.title = `คุยกับ ${view.name}`;
  spriteWindow.className = "signal-agent-sprite-window";
  image.className = "signal-agent-sprite-image";
  image.alt = "";
  image.draggable = false;
  fallback.className = "signal-agent-sprite-fallback";
  fallback.textContent = initials;
  fallback.hidden = Boolean(imagePath);
  index.className = "signal-agent-sprite-index";
  index.textContent = number;
  index.hidden = !number;

  image.addEventListener("error", () => {
    image.hidden = true;
    fallback.hidden = false;
    spriteWindow.classList.add("asset-unavailable");
  }, { once: true });
  if (imagePath) image.src = withAgentAssetVersion(imagePath);
  else image.hidden = true;

  spriteWindow.append(image, fallback, index);
  button.appendChild(spriteWindow);
  button.addEventListener("click", () => openAgentDialog(view.agentId));
  return button;
}

function createSignalAgentChatButton(view) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "signal-agent-chat-action";
  button.textContent = "คุยและถามเหตุผล";
  button.setAttribute("aria-label", `คุยและถามเหตุผลกับ ${view.name}`);
  button.addEventListener("click", () => openAgentDialog(view.agentId));
  return button;
}

function renderSignalDailyPanel(report = {}) {
  const container = els.signalConsensusDailyContent;
  if (!container) return;
  const runtime = getSignalRuntimeTruth(report);
  const daily = signalDailySummaryModel(report);
  const currencySuffix = daily.currency ? ` ${daily.currency}` : "";
  const netTone = daily.net === null ? "muted" : daily.net > 0 ? "positive" : daily.net < 0 ? "negative" : "neutral";
  const statusTone = daily.available ? "ready" : runtime.terminalSelected ? "warning" : "blocked";
  const snapshotChannel = signalSnapshotChannel(report);
  const councilRun = signalCouncilRunModel(report);
  const activeCouncilRound = councilRun.hasActiveRound;
  const analysisBusy = state.aiTradeCouncilAnalysis.inFlight || activeCouncilRound;
  const automation = signalCouncilAutomationModel(report);
  const automationBusy = state.aiTradeCouncilAutomation.inFlight;
  const automationTone = automation.enabled
    ? (automation.timeframeSupported ? "ready" : "warning")
    : "muted";
  const automationMessage = state.aiTradeCouncilAutomation.message
    || automation.reasonMessage
    || (
      automation.enabled
        ? "Snapshot ยังอัปเดตทุก 5 วินาที แต่ Codex จะถูกเรียกเมื่อแท่งปิดใหม่เท่านั้น"
        : "เปิดเมื่อต้องการให้ Agent วิเคราะห์อัตโนมัติทุกครั้งที่เกิดแท่งปิดใหม่"
    );
  const initDiagnostic = signalGatewayInitStatusMessage(runtime.gatewayInitStatus);
  const managed = runtime.gatewayRiskTelemetry || {};
  const managedValuesAvailable = [
    managed.currentManagedPositions,
    managed.currentManagedLots,
    managed.currentTradesToday,
    managed.managedDailyPnl,
  ].some((value) => value !== null && value !== undefined);
  const managedScopeSummary = managedValuesAvailable
    ? `Position ${managed.currentManagedPositions ?? "รอข้อมูล"} • Lot ${managed.currentManagedLots ?? "รอข้อมูล"} • รายการวันนี้ ${managed.currentTradesToday ?? "รอข้อมูล"}`
    : "รอสถานะเฉพาะออเดอร์ที่ EA ของ Council ดูแล";
  const managedScopeDetail = managed.managedDailyPnl === null || managed.managedDailyPnl === undefined
    ? "ยังไม่มีค่า P/L เฉพาะ Council จาก EA"
    : `P/L ที่ EA รายงาน ${formatSignalNumber(managed.managedDailyPnl, { signed: true, suffix: currencySuffix })}`;
  container.innerHTML = `
    <section class="signal-daily-hero" data-tone="${statusTone}">
      <div>
        <span>Daily Trading Dashboard</span>
        <h3>ภาพรวมการเทรดวันนี้</h3>
        <p data-signal-daily-message></p>
      </div>
      <div class="signal-daily-observed">
        <span>ข้อมูลล่าสุด</span>
        <strong data-signal-daily-observed></strong>
        <small data-signal-daily-snapshot></small>
      </div>
    </section>
    <div class="signal-daily-metrics" data-signal-daily-metrics></div>
    <section class="signal-metric-scope" aria-label="ขอบเขตของตัวเลขการเทรด">
      <article data-tone="account">
        <span>ขอบเขตการ์ดด้านบน</span>
        <strong>ทั้งบัญชี MT4 (Account-wide)</strong>
        <p>Balance, Equity, กำไร และจำนวน Position มาจาก Snapshot ของทั้งบัญชี ไม่ได้หมายถึงผลงานของ AI Council เพียงระบบเดียว</p>
      </article>
      <article data-tone="managed">
        <span>เฉพาะ AI Council (Council-managed)</span>
        <strong>${managedScopeSummary}</strong>
        <p>${managedScopeDetail}</p>
      </article>
    </section>
    <div class="signal-daily-layout">
      <section class="signal-daily-team">
        <div class="signal-section-heading">
          <div>
            <span>ทีมวิเคราะห์ของสภา AI Trade</span>
            <strong>Specialist 3 ตัว ลงคะแนนจากข้อมูลรอบเดียวกัน (ไม่ใช่การอนุมัติ 3 ชั้น)</strong>
          </div>
          <span class="signal-state-badge ${daily.analysisReady ? "ready" : "warning"}">
            ${activeCouncilRound ? "รอรอบปัจจุบันทำเสร็จ" : daily.analysisReady ? "พร้อมเริ่มวิเคราะห์" : "รอ Snapshot ที่สด"}
          </span>
        </div>
        <div
          class="signal-daily-team-grid signal-council-overview-grid signal-daily-team-grid--hero"
          data-signal-daily-team
        ></div>
      </section>
      <aside class="signal-daily-actions">
        <div>
          <span>สถานะข้อมูลจริง</span>
          <strong>${daily.available ? "เชื่อมข้อมูล MT4 แล้ว" : "ยังรอตัวอ่าน MT4"}</strong>
          <p>Frontend แสดงเฉพาะข้อมูลที่ Local Runner ตรวจแล้ว และไม่รับรหัสบัญชี รหัสผ่าน หรือ Secret ใด ๆ</p>
          <p class="signal-execution-guard-summary" data-tone="${runtime.gatewayExecutionGuardReady ? "ready" : "warning"}">
            ${signalExecutionGuardSummary(runtime)}
          </p>
          <p class="signal-init-diagnostic" data-signal-init-diagnostic hidden></p>
        </div>
        <section class="signal-auto-analysis-card" data-tone="${automationTone}">
          <div class="signal-auto-analysis-heading">
            <div>
              <span>การวิเคราะห์อัตโนมัติ</span>
              <strong>${automation.statusLabel}</strong>
            </div>
            <label class="signal-auto-switch">
              <input
                type="checkbox"
                data-signal-auto-toggle
                ${automation.enabled ? "checked" : ""}
                ${automationBusy ? "disabled" : ""}
              >
              <span aria-hidden="true"></span>
              <b>${automation.enabled ? "เปิด" : "ปิด"}</b>
            </label>
          </div>
          <p data-signal-auto-message aria-live="polite"></p>
          <dl>
            <div>
              <dt>กราฟที่เฝ้าดู</dt>
              <dd>${automation.currentSymbol || "รอข้อมูล"} ${automation.currentTimeframe || ""}</dd>
            </div>
            <div>
              <dt>รอบวันนี้</dt>
              <dd>${automation.dailyRunCount}/${automation.maxDailyRounds}</dd>
            </div>
            <div>
              <dt>Rate Limit สำรอง</dt>
              <dd>${automation.minRemainingPercent}%</dd>
            </div>
            <div>
              <dt>แท่งที่วิเคราะห์ล่าสุด</dt>
              <dd data-signal-auto-last-bar></dd>
            </div>
          </dl>
          <small>
            อัตโนมัติ: ${automation.supported.join(", ")} • M1 ปิดอัตโนมัติ โดย M5 เป็น Timeframe ต่ำสุด
          </small>
        </section>
        <button type="button" class="signal-secondary-action" data-signal-refresh>
          ตรวจข้อมูล MT4 ใหม่
        </button>
        <button type="button" class="signal-primary-action" data-signal-run-analysis ${daily.analysisReady && !analysisBusy ? "" : "disabled"}>
          ${activeCouncilRound ? "Specialist กำลังวิเคราะห์รอบปัจจุบัน" : analysisBusy ? "กำลังส่งงานให้ Specialist..." : "ให้ Specialist 3 ตัวลงคะแนนรอบนี้"}
        </button>
        <section class="signal-channel-card" data-tone="${snapshotChannel ? "ready" : "warning"}">
          <div class="signal-channel-heading">
            <div>
              <span>CHANNEL ID สำหรับ EA</span>
              <strong>${snapshotChannel ? "พร้อมนำไปใส่ใน SnapshotChannel" : "ยังไม่มี Channel ID"}</strong>
            </div>
            <span class="signal-state-badge ${snapshotChannel ? "ready" : "warning"}">
              ${snapshotChannel ? "พร้อมคัดลอก" : "เลือก MT4 ก่อน"}
            </span>
          </div>
          <code data-signal-channel-code tabindex="0"></code>
          <button type="button" data-signal-copy-channel ${snapshotChannel ? "" : "disabled"}>
            ${snapshotChannel ? "คัดลอก Channel ID" : "กดค้นหาและเลือก MT4 ก่อน"}
          </button>
          <p>เลข Port ใช้เปิดหน้า Dashboard ส่วน Channel ID คือรหัสที่ต้องใส่ในช่อง <b>SnapshotChannel</b> ของ EA โดยทั้งสองอย่างไม่ใช่รหัสบัญชีหรือ Secret</p>
          <details class="signal-adapter-guide" ${daily.available ? "" : "open"}>
            <summary>ดูขั้นตอนติดตั้งหรือเปลี่ยน EA</summary>
            <ol>
              <li>ใน MT4 เปิด File → Open Data Folder</li>
              <li>นำไฟล์ MetafxHQTradeGateway.mq4 ไปไว้ใน MQL4 → Experts → Metafxclub → TradeGateway แล้ว Compile</li>
              <li>ลาก EA ลงกราฟ แล้ววาง Channel ID ในช่อง SnapshotChannel</li>
              <li>เริ่มด้วย GatewayMode = Shadow และ LiveArmed = false</li>
            </ol>
          </details>
        </section>
        <p class="signal-analysis-status" data-signal-analysis-status></p>
      </aside>
    </div>
  `;
  container.querySelector("[data-signal-daily-message]").textContent = daily.readinessMessage;
  container.querySelector("[data-signal-daily-observed]").textContent = daily.observedAt
    ? formatThaiDateTime(daily.observedAt)
    : "ยังไม่มีข้อมูลจาก MT4";
  container.querySelector("[data-signal-daily-snapshot]").textContent = daily.snapshotId
    ? `Snapshot ${daily.snapshotId}`
    : "ยังไม่มี Snapshot ที่ยืนยันโดย Backend";
  const automationMessageNode = container.querySelector("[data-signal-auto-message]");
  if (automationMessageNode) automationMessageNode.textContent = automationMessage;
  const initDiagnosticNode = container.querySelector("[data-signal-init-diagnostic]");
  if (initDiagnosticNode && initDiagnostic) {
    initDiagnosticNode.hidden = false;
    initDiagnosticNode.dataset.tone = initDiagnostic.tone;
    initDiagnosticNode.textContent = initDiagnostic.text;
  }
  const automationLastBar = container.querySelector("[data-signal-auto-last-bar]");
  if (automationLastBar) {
    automationLastBar.textContent = automation.lastAnalyzedClosedBarTime
      ? formatBrokerBarTime(automation.lastAnalyzedClosedBarTime)
      : "ยังไม่มีรอบอัตโนมัติ";
  }
  const metrics = container.querySelector("[data-signal-daily-metrics]");
  [
    ["กำไรสุทธิวันนี้", formatSignalNumber(daily.net, { signed: true, suffix: currencySuffix }), netTone, "กำไรปิดแล้วรวมกำไรลอยตัว"],
    ["กำไรที่ปิดแล้ว", formatSignalNumber(daily.realized, { signed: true, suffix: currencySuffix }), daily.realized > 0 ? "positive" : daily.realized < 0 ? "negative" : "neutral", "เฉพาะออเดอร์ที่ปิดวันนี้"],
    ["กำไรลอยตัว", formatSignalNumber(daily.floating, { signed: true, suffix: currencySuffix }), daily.floating > 0 ? "positive" : daily.floating < 0 ? "negative" : "neutral", "จาก Position ที่ยังเปิดอยู่"],
    ["Balance / Equity", daily.balance === null && daily.equity === null
      ? "ยังไม่มีข้อมูล"
      : `${formatSignalNumber(daily.balance)} / ${formatSignalNumber(daily.equity)}`, "neutral", daily.currency || "สกุลเงินจากบัญชี MT4"],
    ["จำนวนการเทรดวันนี้", daily.trades === null ? "ยังไม่มีข้อมูล" : `${Math.trunc(daily.trades)} ครั้ง`, "neutral", daily.wins === null || daily.losses === null ? "รอข้อมูลชนะและแพ้" : `ชนะ ${Math.trunc(daily.wins)} • แพ้ ${Math.trunc(daily.losses)}`],
    ["Win Rate วันนี้", daily.winRate === null ? "ยังไม่มีข้อมูล" : `${daily.winRate.toFixed(1)}%`, "neutral", "คำนวณจากออเดอร์ที่ปิดวันนี้"],
    ["Drawdown วันนี้", daily.drawdownPercent === null ? "ยังไม่มีข้อมูล" : `${daily.drawdownPercent.toFixed(2)}%`, daily.drawdownPercent > 5 ? "negative" : "neutral", "ค่าที่ Local Runner อ่านและตรวจสอบได้"],
    ["Position ที่เปิดอยู่", daily.openPositions === null ? "ยังไม่มีข้อมูล" : `${Math.trunc(daily.openPositions)} รายการ`, "neutral", "แสดงเฉพาะจำนวน ไม่แสดง Ticket หรือเลขบัญชี"],
  ].forEach(([label, value, tone, detail]) => {
    metrics?.appendChild(createSignalDailyMetric(label, value, { tone, detail }));
  });
  const team = container.querySelector("[data-signal-daily-team]");
  const liveTeamState = new Map(
    signalAgentViews(report, runtime).map((view) => [view.agentId, view]),
  );
  signalCouncilTeamViews().forEach((profile) => {
    const view = {
      ...profile,
      ...(liveTeamState.get(profile.id) || {}),
      agentId: profile.id,
      name: profile.name,
      roleTh: profile.role,
    };
    team?.appendChild(createSignalCouncilOverviewCard(view));
  });
  const status = container.querySelector("[data-signal-analysis-status]");
  status.textContent = state.aiTradeCouncilAnalysis.message
    || (daily.analysisReady
      ? "พร้อมส่งงานผ่าน Local Runner โดยใช้ Codex ตาม Rate Limit ของเครื่องนี้"
      : "ระบบจะไม่หัก Rate Limit จนกว่าจะมี Snapshot ที่สดและกดเริ่มวิเคราะห์");
  status.dataset.tone = state.aiTradeCouncilAnalysis.tone;
  const channelCode = container.querySelector("[data-signal-channel-code]");
  if (channelCode) channelCode.textContent = snapshotChannel || "ยังไม่มี Channel ID จาก Local Runner";
  container.querySelector("[data-signal-copy-channel]")?.addEventListener("click", async (event) => {
    const button = event.currentTarget;
    if (!snapshotChannel) return;
    try {
      await navigator.clipboard.writeText(snapshotChannel);
      button.textContent = "คัดลอกแล้ว";
    } catch {
      button.textContent = "เลือก Channel ID แล้วกด Ctrl+C";
      if (channelCode) {
        const range = document.createRange();
        const selection = window.getSelection();
        range.selectNodeContents(channelCode);
        selection?.removeAllRanges();
        selection?.addRange(range);
        channelCode.focus();
      }
    }
  });
  container.querySelector("[data-signal-refresh]")?.addEventListener("click", async () => {
    await refreshDashboardConnections(AI_TRADE_COUNCIL_PROP_ID);
    const latest = await loadPropReport(AI_TRADE_COUNCIL_PROP_ID);
    if (latest && state.modal.open && state.modal.id === AI_TRADE_COUNCIL_PROP_ID) {
      renderSignalConsensusDashboard(getModalSubject(), getPropertyRole(getModalSubject()), latest);
    }
  });
  container.querySelector("[data-signal-auto-toggle]")?.addEventListener("change", (event) => {
    void setAiTradeCouncilAutomation(event.currentTarget.checked);
  });
  container.querySelector("[data-signal-run-analysis]")?.addEventListener("click", () => {
    void runAiTradeCouncilAnalysis(daily.snapshotId);
  });
}

async function setAiTradeCouncilAutomation(enabled, configOverrides = {}) {
  if (state.aiTradeCouncilAutomation.inFlight) return null;
  const report = state.propReports[AI_TRADE_COUNCIL_PROP_ID] || {};
  const currentConfig = signalCouncilAutomationModel(report);
  const consensusPolicy = signalCouncilConsensusPolicyModel(report);
  const analysisBarCount = normalizeSignalAnalysisBars(
    configOverrides.analysisBarCount ?? currentConfig.analysisBarCount,
  );
  const analysisCountChanged = analysisBarCount !== currentConfig.analysisBarCount;
  state.aiTradeCouncilAutomation = {
    inFlight: true,
    message: analysisCountChanged
      ? `กำลังตั้งให้ AI ใช้ ${analysisBarCount} แท่งปิดในรอบถัดไป`
      : enabled
        ? "กำลังเปิดระบบเฝ้าดูแท่งปิดใหม่ผ่าน Local Runner"
        : "กำลังปิดการเรียก AI อัตโนมัติ",
    tone: "working",
    pendingAnalysisBarCount: analysisCountChanged ? analysisBarCount : null,
  };
  renderSignalConsensusPanel(state.modal.signalTab, report);
  try {
    const response = await postJson("/api/ai-trade-council/automation", {
      enabled: Boolean(enabled),
      maxDailyRounds: Math.trunc(currentConfig.maxDailyRounds),
      minRemainingPercent: Math.trunc(currentConfig.minRemainingPercent),
      analysisBarCount,
      requiredVotes: consensusPolicy.requiredVotes,
    });
    state.aiTradeCouncilAutomation.message = analysisCountChanged
      ? `บันทึกแล้ว • AI จะใช้ ${analysisBarCount} แท่งปิดตั้งแต่รอบวิเคราะห์ถัดไป`
      : enabled
        ? "เปิดแล้ว • ระบบจะตั้งแท่งปัจจุบันเป็นจุดเริ่ม และวิเคราะห์เมื่อแท่งถัดไปปิด"
        : "ปิดแล้ว • Snapshot จาก MT4 ยังอัปเดตตามปกติ แต่จะไม่เรียก Codex อัตโนมัติ";
    state.aiTradeCouncilAutomation.tone = "success";
    addBridgeEvent(
      analysisCountChanged
        ? "เปลี่ยนจำนวนแท่งสำหรับ AI"
        : enabled
          ? "เปิดวิเคราะห์เมื่อแท่งใหม่"
          : "ปิดวิเคราะห์เมื่อแท่งใหม่",
      analysisCountChanged
        ? `Local Runner จะส่ง ${analysisBarCount} แท่งปิดล่าสุดให้ Specialist ในรอบถัดไป`
        : enabled
          ? "Local Runner จะตรวจแท่งปิดใหม่และคุม Rate Limit ก่อนส่งให้ Specialist 3 ตัว"
          : "การอ่าน Snapshot ทุก 5 วินาทียังคงทำงานตามเดิม",
    );
    const latest = await loadPropReport(AI_TRADE_COUNCIL_PROP_ID);
    return latest || response;
  } catch (error) {
    state.aiTradeCouncilAutomation.message = safeDashboardDisplayText(
      error?.body?.messageTh || error?.message,
      analysisCountChanged
        ? "เปลี่ยนจำนวนแท่งวิเคราะห์ไม่สำเร็จ กรุณาตรวจ Local Runner"
        : "เปลี่ยนโหมดอัตโนมัติไม่สำเร็จ กรุณาตรวจ Local Runner",
    );
    state.aiTradeCouncilAutomation.tone = "error";
    return null;
  } finally {
    state.aiTradeCouncilAutomation.inFlight = false;
    if (state.modal.open && state.modal.id === AI_TRADE_COUNCIL_PROP_ID) {
      renderSignalConsensusDashboard(
        getModalSubject(),
        getPropertyRole(getModalSubject()),
        state.propReports[AI_TRADE_COUNCIL_PROP_ID] || {},
      );
    }
  }
}

async function setAiTradeCouncilRequiredVotes(requiredVotes) {
  if (
    state.aiTradeCouncilConsensusPolicy.inFlight
    || state.aiTradeCouncilAutomation.inFlight
  ) return null;
  const nextRequiredVotes = normalizeSignalRequiredVotes(requiredVotes);
  const report = state.propReports[AI_TRADE_COUNCIL_PROP_ID] || {};
  const currentPolicy = signalCouncilConsensusPolicyModel(report);
  if (nextRequiredVotes === currentPolicy.requiredVotes) return report;
  const currentConfig = signalCouncilAutomationModel(report);
  state.aiTradeCouncilConsensusPolicy = {
    inFlight: true,
    message: `กำลังบันทึกเกณฑ์ ${nextRequiredVotes} ใน 3`,
    tone: "working",
    pendingRequiredVotes: nextRequiredVotes,
  };
  renderSignalLivePanel(report);
  try {
    const response = await postJson("/api/ai-trade-council/automation", {
      enabled: Boolean(currentConfig.enabled),
      maxDailyRounds: Math.trunc(currentConfig.maxDailyRounds),
      minRemainingPercent: Math.trunc(currentConfig.minRemainingPercent),
      analysisBarCount: normalizeSignalAnalysisBars(currentConfig.analysisBarCount),
      requiredVotes: nextRequiredVotes,
    });
    state.aiTradeCouncilConsensusPolicy.message = `บันทึกแล้ว • ใช้เกณฑ์ ${nextRequiredVotes} ใน 3 ตั้งแต่รอบวิเคราะห์ถัดไป`;
    state.aiTradeCouncilConsensusPolicy.tone = "success";
    addBridgeEvent(
      "เปลี่ยนจำนวนเสียงของสภา AI",
      `ใช้เสียง ${nextRequiredVotes} ใน 3 ตั้งแต่รอบวิเคราะห์ถัดไป • หากมีทั้ง BUY และ SELL ระบบจะไม่เทรด`,
    );
    const latest = await loadPropReport(AI_TRADE_COUNCIL_PROP_ID);
    return latest || response;
  } catch (error) {
    state.aiTradeCouncilConsensusPolicy.message = safeDashboardDisplayText(
      error?.body?.messageTh || error?.message,
      "บันทึกจำนวนเสียงไม่สำเร็จ กรุณาตรวจ Local Runner",
    );
    state.aiTradeCouncilConsensusPolicy.tone = "error";
    return null;
  } finally {
    state.aiTradeCouncilConsensusPolicy.inFlight = false;
    state.aiTradeCouncilConsensusPolicy.pendingRequiredVotes = null;
    if (state.modal.open && state.modal.id === AI_TRADE_COUNCIL_PROP_ID) {
      renderSignalConsensusDashboard(
        getModalSubject(),
        getPropertyRole(getModalSubject()),
        state.propReports[AI_TRADE_COUNCIL_PROP_ID] || {},
      );
    }
  }
}

async function runAiTradeCouncilAnalysis(snapshotId = "") {
  if (state.aiTradeCouncilAnalysis.inFlight) return null;
  state.aiTradeCouncilAnalysis = {
    inFlight: true,
    message: "กำลังส่ง Snapshot เดียวกันให้ Specialist ทั้ง 3 ตัวผ่าน Local Runner",
    tone: "working",
  };
  renderSignalDailyPanel(state.propReports[AI_TRADE_COUNCIL_PROP_ID] || {});
  try {
    const refreshedReport = await loadPropReport(AI_TRADE_COUNCIL_PROP_ID);
    if (refreshedReport && signalCouncilRunModel(refreshedReport).hasActiveRound) {
      throw new Error("มีรอบวิเคราะห์ของ Specialist 3 ตัวกำลังทำงานอยู่ กรุณารอให้รอบนี้จบก่อนเริ่มรอบใหม่");
    }
    const refreshedSnapshotId = refreshedReport
      ? signalDailySummaryModel(refreshedReport).snapshotId
      : "";
    const boundSnapshotId = refreshedSnapshotId || snapshotId;
    const response = await postJson("/api/ai-trade-council/analyze", {
      propId: AI_TRADE_COUNCIL_PROP_ID,
      ...(boundSnapshotId ? { snapshotId: boundSnapshotId } : {}),
    });
    const parentSource = response?.parent || response?.manager;
    const parent = parentSource && typeof parentSource === "object" ? parentSource : null;
    const subtasks = Array.isArray(response?.subtasks)
      ? response.subtasks.filter((mission) => mission && typeof mission === "object")
      : [];
    if (!parent || subtasks.length !== AI_TRADE_COUNCIL_AGENT_IDS.length) {
      throw new Error("Local Runner ยังส่ง Mission วิเคราะห์กลับมาไม่ครบ 3 Specialist");
    }
    mergeBackendMission(parent);
    subtasks.forEach((mission) => {
      mergeBackendMission(mission);
      if (AI_TRADE_COUNCIL_AGENT_IDS.includes(mission.owner)) {
        routeAgentToTargetId(
          mission.owner,
          AI_TRADE_COUNCIL_PROP_ID,
          "กำลังวิเคราะห์ข้อมูลรอบเดียวกัน",
          { select: false },
        );
        setAgentSpeech(
          mission.owner,
          `กำลังทำหน้าที่ ${safeDashboardDisplayText(mission.title, "วิเคราะห์สภา AI Trade")}`,
          "working",
        );
      }
    });
    state.aiTradeCouncilAnalysis.message = "ส่งงานให้ Specialist 3 ตัวแล้ว ดูความคืบหน้าได้ที่แท็บขั้นตอนตัดสินใจ";
    state.aiTradeCouncilAnalysis.tone = "success";
    addBridgeEvent(
      "เริ่มวิเคราะห์สภา AI Trade",
      `Specialist 3 ตัวใช้ Snapshot ${safeDashboardDisplayText(response?.snapshotId || boundSnapshotId, "ล่าสุด")} ร่วมกัน`,
    );
    await loadBridgeMissions({ replaceEvents: false, persist: false });
    const latestReport = await loadPropReport(AI_TRADE_COUNCIL_PROP_ID);
    if (latestReport && state.modal.open && state.modal.id === AI_TRADE_COUNCIL_PROP_ID) {
      renderSignalConsensusDashboard(getModalSubject(), getPropertyRole(getModalSubject()), latestReport);
    }
    return response;
  } catch (error) {
    state.aiTradeCouncilAnalysis.message = safeDashboardDisplayText(
      error?.body?.messageTh || error?.message,
      "ยังเริ่มวิเคราะห์ไม่ได้ กรุณาตรวจการเชื่อมต่อ MT4 และ Snapshot ก่อน",
    );
    state.aiTradeCouncilAnalysis.tone = "error";
    return null;
  } finally {
    state.aiTradeCouncilAnalysis.inFlight = false;
    if (state.modal.open && state.modal.id === AI_TRADE_COUNCIL_PROP_ID) {
      renderSignalConsensusDashboard(
        getModalSubject(),
        getPropertyRole(getModalSubject()),
        state.propReports[AI_TRADE_COUNCIL_PROP_ID] || {},
      );
    }
  }
}

function renderSignalMarketStrip(container, report, runtime) {
  if (!container) return;
  const market = signalMarketModel(report);
  const stale = report?.connectionChecklist?.stale === true;
  const modeAccount = signalGatewayModeAccountStatus(runtime);
  const items = [
    ["MT4 / MT5 ที่เลือก", market.terminal, runtime.terminalSelected ? "ready" : "warning"],
    ["สัญลักษณ์", market.symbol, market.available ? "ready" : "muted"],
    ["กรอบเวลา", market.timeframe, market.available ? "ready" : "muted"],
    ["แท่งเทียนล่าสุด", market.observedAt ? formatThaiDateTime(market.observedAt) : "รอ Adapter", market.observedAt ? "ready" : "warning"],
    [
      "ความสดของข้อมูล",
      market.freshnessMinutes === null
        ? (stale ? "ผลตรวจการเชื่อมต่อเก่า" : "ยังไม่มีข้อมูล")
        : `${market.freshnessMinutes} นาที`,
      market.freshnessMinutes !== null && market.freshnessMinutes <= 5 ? "ready" : "warning",
    ],
    ["Spread ปัจจุบัน", market.spread === null ? "ยังไม่มีข้อมูล" : String(market.spread), market.spread === null ? "muted" : "ready"],
    ["สถานะ Gateway", displayStatus(runtime.gatewayStatus), runtime.gatewayConnected ? "info" : "warning"],
    [
      "สิทธิ์ส่ง Order",
      runtime.gatewayExecutionGuardReady
        ? "Execution Guard พร้อม"
        : signalExecutionGuardReasonLabel(runtime.gatewayExecutionGuardReason),
      runtime.gatewayExecutionGuardReady ? "ready" : "warning",
    ],
    [
      "โหมด Gateway",
      runtime.gatewayConnected
        ? (modeAccount.observed ? modeAccount.value : runtime.gatewayMode.toUpperCase())
        : "ยังไม่เชื่อม EA",
      runtime.gatewayConnected && !modeAccount.mismatch ? "info" : "warning",
    ],
    ["Fixed Lot", runtime.gatewayFixedLot === null ? "ตั้งค่าที่ EA" : String(runtime.gatewayFixedLot), runtime.gatewayFixedLot === null ? "muted" : "ready"],
  ];
  container.innerHTML = "";
  items.forEach(([label, value, tone]) => {
    const item = document.createElement("div");
    const name = document.createElement("span");
    const detail = document.createElement("strong");
    item.className = "signal-market-stat";
    item.dataset.tone = tone;
    name.textContent = label;
    detail.textContent = safeDashboardDisplayText(value, "ยังไม่มีข้อมูล");
    item.append(name, detail);
    container.appendChild(item);
  });
}

function signalMissionStatusValue(mission = {}) {
  const raw = String(
    mission?.status
    || mission?.workStatus
    || mission?.dispatchState
    || "",
  ).trim().toLowerCase().replace(/[ -]+/g, "_");
  if (raw === "archived") {
    return String(mission?.archivedFromStatus || "archived")
      .trim()
      .toLowerCase()
      .replace(/[ -]+/g, "_");
  }
  return raw || "unknown";
}

function signalMissionUiState(mission = null) {
  if (!mission) return "idle";
  const status = signalMissionStatusValue(mission);
  if (status === "completed") return "completed";
  if (["blocked", "failed", "error", "invalid_council_output"].includes(status)) return "blocked";
  if (["queued", "running", "waiting_approval"].includes(status)) return "running";
  return "idle";
}

function signalMissionStatusLabel(mission = null) {
  if (!mission) return "ยังไม่เริ่ม";
  const status = signalMissionStatusValue(mission);
  return {
    queued: "รอเริ่ม",
    running: "กำลังทำ",
    waiting_approval: "รอระบบป้องกัน",
    completed: "สำเร็จ",
    blocked: "ติดขัด",
    failed: "ไม่สำเร็จ",
    error: "เกิดข้อผิดพลาด",
    invalid_council_output: "ผลลัพธ์ไม่ผ่านรูปแบบ",
  }[status] || displayStatus(status);
}

function signalMissionReason(mission = null, fallback = "ยังไม่มีรายละเอียดจาก Backend") {
  if (!mission) return fallback;
  const blocker = signalMissionBlockerModel(mission);
  if (blocker?.active) return blocker.causeTh || blocker.titleTh || fallback;
  const status = signalMissionStatusValue(mission);
  const blockedCapability = String(mission?.blockedCapability || "").trim();
  const capabilityReasons = {
    local_file_read_without_terminal: "Agent ข่าวเปิดอ่าน Snapshot ในเครื่องไม่ได้ จึงหยุดงานไว้ก่อนโดยไม่เดาข้อมูลตลาด",
    web_search_unavailable: "Agent ข่าวเชื่อม Web Search ไม่สำเร็จ จึงหยุดงานไว้ก่อนโดยไม่สร้างข่าวจำลอง",
    codex_auth_required: "Codex ในเครื่องยังต้องเข้าสู่ระบบก่อน จึงยังเริ่มงานนี้ไม่ได้",
    codex_rate_limited: "Codex ถึง Rate Limit ของรอบนี้แล้ว งานจึงหยุดรอรอบถัดไป",
    "Native Codex Web Search verification": "ตัวค้นข่าวทำงานแล้ว แต่ระบบหลังบ้านยังยืนยันบันทึก Web Search ไม่ได้ จึงไม่นำผลข่าวรอบนี้ไปโหวตหรือส่งคำสั่งซื้อขาย",
  };
  if (blockedCapability && capabilityReasons[blockedCapability]) {
    return capabilityReasons[blockedCapability];
  }
  if (mission?.result) {
    const resultText = safeDashboardDisplayText(mission.result, "");
    if (resultText && resultText !== "[TRUNCATED]") return resultText;
    if (resultText === "[TRUNCATED]") {
      return "รายละเอียดถูกตัดในรายงานย่อ • เปิดรายละเอียด Task เพื่อดูข้อมูลฉบับเต็ม";
    }
  }
  if (status === "invalid_council_output" || mission?.workStatus === "invalid_council_output") {
    return "ผลจาก Agent ไม่ผ่านรูปแบบคำตอบของสภา หรือไม่ตรงกับ Snapshot และบทบาทที่กำหนด";
  }
  if (status === "queued") return "งานอยู่ในคิวของ Local Runner และยังไม่เริ่มใช้ Codex";
  if (status === "running") return "Agent กำลังวิเคราะห์ข้อมูลผ่าน Local Runner";
  if (status === "waiting_approval") return "งานกำลังรอระบบป้องกันตรวจสิทธิ์อัตโนมัติ";
  if (status === "completed") return "Agent ส่งผลลัพธ์กลับมายัง Local Runner แล้ว";
  return safeDashboardDisplayText(mission?.workStatus || mission?.phase, fallback);
}

function signalMissionBlockerModel(mission = null) {
  if (!mission || signalMissionUiState(mission) !== "blocked") return null;
  const supplied = mission?.blocker && typeof mission.blocker === "object"
    ? mission.blocker
    : {};
  const rootCauseCode = safeDashboardDisplayText(
    supplied.rootCauseCode
      || mission?.runnerStatus
      || mission?.blockedCapability
      || mission?.reasonCode
      || mission?.phase,
    "blocked",
  ).toLowerCase();
  const reasonCode = safeDashboardDisplayText(
    supplied.reasonCode || mission?.reasonCode || mission?.phase || "blocked",
    "blocked",
  ).toLowerCase();
  let titleTh = safeDashboardDisplayText(
    supplied.titleTh,
    "Agent ยังทำงานรอบนี้ไม่สำเร็จ",
  );
  let causeTh = safeDashboardDisplayText(
    supplied.causeTh,
    "Local Runner หยุดงานนี้ไว้เพื่อไม่ให้นำผลที่ไม่ครบไปใช้งานต่อ",
  );
  const flatSteps = [
    supplied.resolutionStep1Th,
    supplied.resolutionStep2Th,
    supplied.resolutionStep3Th,
    supplied.resolutionStep4Th,
  ].map((item) => safeDashboardDisplayText(item, ""))
    .filter((item) => item && item !== "[TRUNCATED]");
  let steps = flatSteps.length
    ? flatSteps
    : (Array.isArray(supplied.resolutionStepsTh)
      ? supplied.resolutionStepsTh
        .map((item) => safeDashboardDisplayText(item, ""))
        .filter((item) => item && item !== "[TRUNCATED]")
      : []);
  if (!supplied.titleTh && rootCauseCode === "local_rate_limited") {
    titleTh = "คิวงานของ Agent ตัวนี้เต็มในช่วงเวลานั้น";
    causeTh = "Local Runner เลื่อนงานเพราะจำนวนรอบต่อชั่วโมงเต็ม งานยังไม่ได้เปิด Codex และหมดเวลาร่วมของสภาก่อนเริ่ม";
    steps = [
      "รอให้รอบจำกัดต่อชั่วโมงคืน หรือรอแท่งเทียนใหม่",
      "กดตรวจสถานะใหม่ แล้วเริ่ม Specialist ทั้ง 3 ตัวพร้อมกัน",
      "ไม่ต้องรัน Agent ตัวเดียว เพราะทั้ง 3 ตัวต้องใช้ Snapshot เดียวกัน",
    ];
  } else if (!supplied.titleTh && [
    "council_round_deadline_expired",
    "council_round_deadline_insufficient",
    "council_rate_limit_exceeds_round_deadline",
  ].includes(reasonCode)) {
    titleTh = "เวลาร่วมของสภา AI หมดก่อนวิเคราะห์ครบ";
    causeTh = "Agent ทำงานไม่ครบภายในเวลาของ Snapshot เดียวกัน ระบบจึงยกเลิกรอบนี้และไม่ส่งคำสั่งไป MT4";
    steps = [
      "กดตรวจสถานะใหม่เพื่อยืนยันว่า Local Runner พร้อม",
      "รอ Snapshot ใหม่ แล้วเริ่ม Specialist ทั้ง 3 ตัวพร้อมกันอีกครั้ง",
    ];
  }
  if (!steps.length) {
    steps = [
      "กดตรวจสถานะใหม่เพื่ออ่านข้อมูลล่าสุดจาก Local Runner",
      "เมื่อมี Snapshot ใหม่ ให้เริ่ม Specialist ทั้ง 3 ตัวพร้อมกันอีกครั้ง",
    ];
  }
  return {
    active: true,
    titleTh,
    causeTh,
    resolutionStepsTh: steps.slice(0, 4),
    reasonCode,
    rootCauseCode,
    retryLabelTh: safeDashboardDisplayText(supplied.retryLabelTh, "ตรวจสถานะใหม่"),
    retryAction: safeDashboardDisplayText(supplied.retryAction, "refresh_status"),
    processStarted: supplied.processStarted === true,
    deferralCount: Number.isFinite(Number(supplied.deferralCount))
      ? Math.max(0, Math.trunc(Number(supplied.deferralCount)))
      : 0,
    retryAt: supplied.retryAt || mission?.nextAttemptAt || null,
    roundDeadlineAt: supplied.roundDeadlineAt || null,
    snapshotId: safeDashboardDisplayText(
      supplied.snapshotId || mission?.delegation?.snapshotId,
      "",
    ),
    missionId: safeDashboardDisplayText(mission?.id, ""),
    terminalActionBlocked: supplied.terminalActionBlocked !== false,
  };
}

function signalMissionCreatedTime(mission = {}) {
  const value = mission?.createdAt || mission?.startedAt || mission?.updatedAt;
  const timestamp = value ? new Date(value).getTime() : 0;
  return Number.isFinite(timestamp) ? timestamp : 0;
}

function signalSnapshotLabel(snapshotId = "") {
  const value = safeDashboardDisplayText(snapshotId, "");
  if (!value) return "ยังไม่มี Snapshot";
  return value.length > 22 ? `${value.slice(0, 10)}…${value.slice(-8)}` : value;
}

function signalSnapshotComparisonText(analyzedSnapshotId = "", currentSnapshotId = "") {
  const analyzed = safeDashboardDisplayText(analyzedSnapshotId, "");
  const current = safeDashboardDisplayText(currentSnapshotId, "");
  if (analyzed && current && analyzed === current) {
    return `ผลรอบนี้ตรงกับ Snapshot ปัจจุบัน ${signalSnapshotLabel(analyzed)}`;
  }
  if (analyzed && current) {
    return `ผลนี้วิเคราะห์จาก ${signalSnapshotLabel(analyzed)} • กราฟปัจจุบัน ${signalSnapshotLabel(current)} • เป็นข้อมูลคนละรอบ`;
  }
  if (analyzed) {
    return `ผลนี้วิเคราะห์จาก Snapshot ${signalSnapshotLabel(analyzed)} • ขณะนี้ยังไม่มี Snapshot ปัจจุบัน`;
  }
  if (current) {
    return `กราฟปัจจุบันคือ ${signalSnapshotLabel(current)} • ยังไม่มี Snapshot ที่ Agent วิเคราะห์ครบ`;
  }
  return "ยังไม่มี Snapshot จาก Backend";
}

function signalCouncilRunModel(report = {}) {
  const pipeline = signalCouncilModel(report).decisionPipeline || {};
  const items = Array.isArray(pipeline.items)
    ? pipeline.items.filter((item) => item && typeof item === "object")
    : [];
  const parents = items
    .filter((item) => (
      item.reportType === "ai_trade_council_report"
      || item?.delegation?.mode === "ai_trade_council_read_only"
    ))
    .sort((left, right) => signalMissionCreatedTime(right) - signalMissionCreatedTime(left));
  const parent = parents[0] || null;
  const activeParent = parents.find((item) => signalMissionUiState(item) === "running") || null;
  const parentId = String(parent?.id || "");
  const childIds = new Set(Array.isArray(parent?.subtaskIds) ? parent.subtaskIds : []);
  const childPool = items
    .filter((item) => (
      AI_TRADE_COUNCIL_AGENT_IDS.includes(item?.owner)
      && (
        (parentId && item?.parentMissionId === parentId)
        || childIds.has(item?.id)
      )
    ))
    .sort((left, right) => signalMissionCreatedTime(right) - signalMissionCreatedTime(left));
  const children = AI_TRADE_COUNCIL_AGENT_IDS
    .map((agentId) => childPool.find((item) => item.owner === agentId) || null)
    .filter(Boolean);
  const byAgent = new Map(children.map((item) => [item.owner, item]));
  const counts = {
    running: 0,
    completed: 0,
    blocked: 0,
  };
  children.forEach((mission) => {
    const stateName = signalMissionUiState(mission);
    if (Object.prototype.hasOwnProperty.call(counts, stateName)) counts[stateName] += 1;
  });
  const parentState = signalMissionUiState(parent);
  const stateName = parentState !== "idle"
    ? parentState
    : counts.blocked > 0
      ? "blocked"
      : counts.running > 0
        ? "running"
        : children.length === AI_TRADE_COUNCIL_AGENT_IDS.length && counts.completed === children.length
          ? "completed"
          : "idle";
  return {
    parent,
    activeParent,
    hasActiveRound: Boolean(activeParent),
    children,
    byAgent,
    counts,
    state: stateName,
    statusLabel: signalMissionStatusLabel(parent),
    reason: signalMissionReason(parent, "ยังไม่มี Mission วิเคราะห์จาก Backend"),
    snapshotId: safeDashboardDisplayText(parent?.delegation?.snapshotId, ""),
  };
}

function signalCurrentConsensusSource(report = {}, run = signalCouncilRunModel(report)) {
  const council = signalCouncilModel(report);
  const live = council.liveAnalysis || {};
  const pipeline = council.decisionPipeline || {};
  const candidates = [live.consensus, pipeline.consensus]
    .filter((item) => item && typeof item === "object")
    .filter((item) => (
      item.available === true
      || item.ready === true
      || Array.isArray(item.votes)
      || Boolean(item.sourceMissionId)
    ));
  if (!run.parent || !run.snapshotId) return { source: {}, current: false, run };
  const parentId = String(run.parent.id || "");
  const runSnapshotId = safeDashboardDisplayText(run.snapshotId, "");
  const source = candidates.find((item) => {
    const sourceMissionId = String(item?.sourceMissionId || "");
    const sourceSnapshotId = safeDashboardDisplayText(item?.snapshotId, "");
    return Boolean(sourceMissionId)
      && sourceMissionId === parentId
      && Boolean(sourceSnapshotId)
      && sourceSnapshotId === runSnapshotId;
  });
  return { source: source || {}, current: Boolean(source), run };
}

function signalAgentViews(report = {}, runtime = getSignalRuntimeTruth(report)) {
  const run = signalCouncilRunModel(report);
  const consensusSelection = signalCurrentConsensusSource(report, run);
  const sourceVotes = Array.isArray(consensusSelection.source?.votes)
    ? consensusSelection.source.votes
    : [];
  const supplied = consensusSelection.current ? sourceVotes : [];
  const defaults = [
    {
      id: "technical",
      agentId: "optimization_agent",
      name: AI_TRADE_COUNCIL_PUBLIC_NAMES.optimization_agent,
      roleTh: "Indicator และ Technical Signal",
      waitingReason: "รอข้อมูลราคาและ Indicator จาก Snapshot ที่ Backend ยืนยัน",
    },
    {
      id: "price_action",
      agentId: "backtest_analyst",
      name: AI_TRADE_COUNCIL_PUBLIC_NAMES.backtest_analyst,
      roleTh: "กราฟเปล่า, Price Action, Trendline, S/R และ HMC/ICT",
      waitingReason: "รอแท่งเทียนที่ปิดแล้วและโครงสร้างราคาจาก Adapter",
    },
    {
      id: "news",
      agentId: "codex_mcp_operator",
      name: AI_TRADE_COUNCIL_PUBLIC_NAMES.codex_mcp_operator,
      roleTh: "ข่าวและสถานการณ์ระยะสั้น กลาง และยาว",
      waitingReason: "รอข้อมูลข่าวล่าสุดที่มีเวลาและแหล่งอ้างอิง",
    },
  ];
  return defaults.map((definition) => {
    const mission = run.byAgent.get(definition.agentId) || null;
    const view = supplied.find((item) => (
      String(item?.id || item?.agentId || item?.role || "").toLowerCase() === definition.id
      || String(item?.agentId || "").toLowerCase() === definition.agentId
      || String(item?.name || "").toLowerCase().includes(definition.id.replace("_", " "))
    )) || {};
    const rawDirection = String(view.decision || view.direction || view.vote || "").trim().toUpperCase();
    const direction = ["BUY", "HOLD", "SELL", "NO_DATA"].includes(rawDirection) ? rawDirection : null;
    const hasCurrentVote = consensusSelection.current && Boolean(direction) && (
      view.available === true
      || view.readOnly === true
      || Boolean(view.snapshotId)
      || Boolean(view.agentId)
    );
    const confidence = Number.isFinite(Number(view.confidence)) ? Number(view.confidence) : null;
    const reasons = Array.isArray(view.observations)
      ? view.observations
      : (Array.isArray(view.reasons)
      ? view.reasons
      : (Array.isArray(view.findings) ? view.findings : []));
    const normalizedReasons = reasons
      .map((reason) => safeDashboardDisplayText(reason, ""))
      .filter((reason) => reason && reason !== "[TRUNCATED]");
    const readableReasons = normalizedReasons.length
      ? normalizedReasons
      : reasons.some((reason) => safeDashboardDisplayText(reason, "") === "[TRUNCATED]")
        ? ["คำอธิบายถูกตัดในรายงานย่อ — เปิดรายละเอียด Mission เพื่อดูข้อมูลฉบับเต็ม"]
        : [];
    const evidenceObservedAt = Array.isArray(view.evidence)
      ? view.evidence.find((item) => item?.observedAt)?.observedAt
      : null;
    const missionState = signalMissionUiState(mission);
    const missionWins = ["blocked", "running"].includes(missionState);
    const available = hasCurrentVote && !missionWins;
    const blocker = missionState === "blocked" ? signalMissionBlockerModel(mission) : null;
    return {
      ...definition,
      available,
      missionId: mission?.id || null,
      state: missionWins
        ? missionState
        : available
          ? (direction === "NO_DATA" ? "blocked" : "completed")
          : missionState,
      statusLabel: missionWins
        ? signalMissionStatusLabel(mission)
        : available
        ? signalVoteLabel(direction)
        : signalMissionStatusLabel(mission),
      direction: available ? direction : null,
      confidence: available ? confidence : null,
      stopLossPrice: available && Number.isFinite(Number(view.stopLossPrice))
        ? Number(view.stopLossPrice)
        : null,
      takeProfitPrice: available && Number.isFinite(Number(view.takeProfitPrice))
        ? Number(view.takeProfitPrice)
        : null,
      reasons: missionWins
        ? [mission ? signalMissionReason(mission) : definition.waitingReason]
        : available
        ? readableReasons.slice(0, 3)
        : [mission ? signalMissionReason(mission) : definition.waitingReason],
      observedAt: available
        ? (view.observedAt || evidenceObservedAt || mission?.completedAt || mission?.createdAt || null)
        : (mission?.completedAt || mission?.updatedAt || mission?.createdAt || null),
      blocker,
    };
  });
}

function createSignalAgentBlockerPanel(view) {
  const blocker = view?.blocker;
  if (!blocker?.active) return null;
  const panel = document.createElement("section");
  const issueRow = document.createElement("div");
  const causeRow = document.createElement("div");
  const stepsRow = document.createElement("div");
  const issueLabel = document.createElement("strong");
  const issueValue = document.createElement("span");
  const causeLabel = document.createElement("strong");
  const causeValue = document.createElement("span");
  const stepsLabel = document.createElement("strong");
  const steps = document.createElement("ol");
  const details = document.createElement("details");
  const summary = document.createElement("summary");
  const technical = document.createElement("dl");
  const actions = document.createElement("div");

  panel.className = "signal-agent-blocker";
  issueRow.className = "signal-agent-blocker-row";
  causeRow.className = "signal-agent-blocker-row";
  stepsRow.className = "signal-agent-blocker-row signal-agent-blocker-steps";
  issueLabel.textContent = "ติดอะไร";
  issueValue.textContent = blocker.titleTh;
  causeLabel.textContent = "สาเหตุ";
  causeValue.textContent = blocker.causeTh;
  stepsLabel.textContent = "วิธีแก้";
  blocker.resolutionStepsTh.forEach((text) => {
    const item = document.createElement("li");
    item.textContent = text;
    steps.appendChild(item);
  });
  issueRow.append(issueLabel, issueValue);
  causeRow.append(causeLabel, causeValue);
  stepsRow.append(stepsLabel, steps);

  details.className = "signal-agent-blocker-technical";
  summary.textContent = "ดูรายละเอียดระบบ";
  const technicalRows = [
    ["รหัสสาเหตุ", blocker.reasonCode],
    ["ต้นเหตุ", blocker.rootCauseCode],
    ["Codex เริ่มทำงานหรือยัง", blocker.processStarted ? "เริ่มแล้ว" : "ยังไม่ได้เริ่ม"],
    ["จำนวนครั้งที่เลื่อน", String(blocker.deferralCount || 0)],
    ["กำหนดเวลารอบ", blocker.roundDeadlineAt ? formatThaiDateTime(blocker.roundDeadlineAt) : "ไม่มีข้อมูล"],
    ["เวลาที่เคยนัดลองใหม่", blocker.retryAt ? formatThaiDateTime(blocker.retryAt) : "ไม่มีข้อมูล"],
    ["Mission", blocker.missionId],
    ["Snapshot", blocker.snapshotId ? signalSnapshotLabel(blocker.snapshotId) : "ไม่มีข้อมูล"],
    ["ส่งคำสั่ง MT4", blocker.terminalActionBlocked ? "ไม่ได้ส่ง" : "ตรวจจาก Backend อีกครั้ง"],
  ];
  technicalRows.forEach(([label, value]) => {
    const term = document.createElement("dt");
    const description = document.createElement("dd");
    term.textContent = label;
    description.textContent = safeDashboardDisplayText(value, "ไม่มีข้อมูล");
    technical.append(term, description);
  });
  details.append(summary, technical);

  actions.className = "signal-agent-blocker-actions";
  if (blocker.retryAction === "refresh_status") {
    const refresh = document.createElement("button");
    refresh.type = "button";
    refresh.textContent = blocker.retryLabelTh || "ตรวจสถานะใหม่";
    refresh.addEventListener("click", async () => {
      if (refresh.disabled) return;
      refresh.disabled = true;
      refresh.textContent = "กำลังตรวจจาก Local Runner…";
      const report = await loadPropReport(AI_TRADE_COUNCIL_PROP_ID);
      if (!report) {
        refresh.disabled = false;
        refresh.textContent = "ตรวจไม่สำเร็จ • ลองใหม่";
        return;
      }
      if (state.modal.open && state.modal.id === AI_TRADE_COUNCIL_PROP_ID) {
        renderSignalConsensusDashboard(
          getModalSubject(),
          getPropertyRole(getModalSubject()),
          report,
        );
      }
    });
    actions.appendChild(refresh);
  }
  panel.append(issueRow, causeRow, stepsRow, details);
  if (actions.childElementCount) panel.appendChild(actions);
  return panel;
}

function createSignalAgentCard(view, { compact = false } = {}) {
  const card = document.createElement("article");
  const heading = document.createElement("div");
  const name = document.createElement("strong");
  const role = document.createElement("small");
  const status = document.createElement("span");
  const decision = document.createElement("div");
  const direction = document.createElement("b");
  const confidence = document.createElement("span");
  const protectivePrices = document.createElement("small");
  const reasons = document.createElement("ul");
  const footer = document.createElement("small");
  const order = { technical: "1", price_action: "2", news: "3" }[view.id] || "•";
  const workStatus = signalAgentWorkStatus(view);
  const tone = workStatus.tone;

  card.className = `signal-agent-card ${tone}${compact ? " compact" : ""}`;
  heading.className = "signal-agent-card-heading";
  name.textContent = view.name;
  role.textContent = view.roleTh || "";
  const identity = document.createElement("div");
  status.className = "signal-agent-work-status";
  status.dataset.tone = tone;
  status.textContent = workStatus.label;
  identity.append(name, role);
  heading.append(createSignalAgentSprite(view, { number: order }), identity, status);
  decision.className = "signal-agent-decision";
  direction.textContent = signalVoteLabel(view.direction, view.statusLabel || "ยังไม่เริ่ม");
  confidence.textContent = view.confidence === null
    ? (view.state === "blocked"
      ? "ดูสาเหตุด้านล่าง"
      : view.state === "running"
        ? "ติดตามจาก Local Runner"
        : view.state === "completed"
          ? "ส่งผลกลับแล้ว"
          : "ยังไม่มีคะแนนความเชื่อมั่น")
    : `ความเชื่อมั่น ${Math.round(view.confidence)}%`;
  decision.append(direction, confidence);
  protectivePrices.className = "signal-agent-protective-prices";
  protectivePrices.textContent = (
    view.direction && ["BUY", "SELL"].includes(view.direction)
    && view.stopLossPrice !== null
    && view.takeProfitPrice !== null
  )
    ? `SL ${formatSignalNumber(view.stopLossPrice)} • TP ${formatSignalNumber(view.takeProfitPrice)}`
    : "SL / TP จะมีเมื่อ Agent เลือก BUY หรือ SELL";
  view.reasons.forEach((reason) => {
    const item = document.createElement("li");
    item.textContent = safeDashboardDisplayText(reason);
    reasons.appendChild(item);
  });
  footer.textContent = view.observedAt
    ? `อัปเดตล่าสุด ${formatThaiDateTime(view.observedAt)}`
    : "ยังไม่มี Snapshot ที่ยืนยันโดย Backend";
  card.dataset.workState = view.state || "idle";
  card.append(heading, decision, protectivePrices);
  const blockerPanel = createSignalAgentBlockerPanel(view);
  if (blockerPanel) {
    card.appendChild(blockerPanel);
  } else {
    card.appendChild(reasons);
  }
  card.append(footer, createSignalAgentChatButton(view));
  return card;
}

function createSignalCouncilOverviewCard(view) {
  const card = document.createElement("article");
  const portrait = document.createElement("div");
  const identity = document.createElement("header");
  const identityCopy = document.createElement("div");
  const name = document.createElement("strong");
  const role = document.createElement("span");
  const status = document.createElement("span");
  const metrics = document.createElement("div");
  const reason = document.createElement("p");
  const footer = document.createElement("small");
  const order = { technical: "1", price_action: "2", news: "3" }[view.id] || "•";
  const workStatus = signalAgentWorkStatus(view);
  const vote = signalVoteLabel(view.direction, "รอผลโหวต");
  const confidence = view.confidence === null
    ? "รอคะแนน"
    : `${Math.round(view.confidence)}%`;
  const createMetric = (label, value, tone = "neutral") => {
    const item = document.createElement("div");
    const metricLabel = document.createElement("span");
    const metricValue = document.createElement("strong");
    item.dataset.tone = tone;
    metricLabel.textContent = label;
    metricValue.textContent = value;
    item.append(metricLabel, metricValue);
    return item;
  };

  card.className = `signal-council-agent-card ${workStatus.tone}`;
  card.dataset.workState = view.state || "idle";
  portrait.className = "signal-council-agent-portrait";
  portrait.appendChild(createSignalAgentSprite(view, { number: order }));
  identity.className = "signal-council-agent-identity";
  name.textContent = view.name;
  role.textContent = view.roleTh || "ผู้เชี่ยวชาญสภา AI";
  status.className = "signal-agent-work-status";
  status.dataset.tone = workStatus.tone;
  status.textContent = workStatus.label;
  identityCopy.append(name, role);
  identity.append(identityCopy, status);
  metrics.className = "signal-council-agent-metrics";
  metrics.append(
    createMetric("สถานะ", workStatus.label, workStatus.tone),
    createMetric("ผลโหวต", vote, String(view.direction || "waiting").toLowerCase()),
    createMetric("ความเชื่อมั่น", confidence, view.confidence === null ? "waiting" : "ready"),
  );
  reason.className = "signal-council-agent-reason";
  reason.textContent = safeDashboardDisplayText(
    view.reasons?.[0],
    "ยังไม่มีเหตุผลจาก Local Runner",
  );
  footer.textContent = view.observedAt
    ? `อัปเดตล่าสุด ${formatThaiDateTime(view.observedAt)}`
    : "ยังไม่มี Snapshot ที่ยืนยันโดย Backend";
  const chatButton = createSignalAgentChatButton(view);
  chatButton.textContent = "คุย";
  card.append(portrait, identity, metrics);
  const blockerPanel = createSignalAgentBlockerPanel(view);
  if (blockerPanel) {
    card.appendChild(blockerPanel);
  } else {
    card.appendChild(reason);
  }
  card.append(footer, chatButton);
  return card;
}

function signalConsensusModel(report = {}, runtime = getSignalRuntimeTruth(report)) {
  const consensusPolicy = signalCouncilConsensusPolicyModel(report);
  const run = signalCouncilRunModel(report);
  const consensusSelection = signalCurrentConsensusSource(report, run);
  const source = consensusSelection.source || {};
  const votes = Array.isArray(source.votes) ? source.votes : [];
  const suppliedVoteCount = Number(source.voteCount);
  const voteCount = Number.isFinite(suppliedVoteCount)
    ? Math.max(0, Math.trunc(suppliedVoteCount))
    : votes.length;
  const rawDecision = String(source.finalDecision || source.decision || "")
    .trim()
    .toUpperCase()
    .replaceAll("_", " ");
  const available = (
    consensusSelection.current
    &&
    (source.available === true || source.ready === true || votes.length > 0)
    && voteCount === AI_TRADE_COUNCIL_AGENT_IDS.length
    && rawDecision !== "NO DATA"
  );
  const count = (name) => {
    const fromVotes = votes.filter((vote) => (
      String(vote?.decision || vote?.direction || vote?.vote || "").trim().toUpperCase() === name.toUpperCase()
    )).length;
    const value = Number(
      votes.length
        ? fromVotes
        : (source?.votes?.[name] ?? source?.[`${name}Count`]),
    );
    return available && Number.isFinite(value) ? Math.max(0, Math.trunc(value)) : null;
  };
  const displayDecision = rawDecision === "NO DATA"
    ? "ข้อมูลไม่ครบ"
    : (["BUY", "HOLD", "SELL", "NO TRADE"].includes(rawDecision) ? rawDecision : "NO TRADE");
  const sourceReason = source.reason || source.reasonTh;
  const market = signalMarketModel(report);
  const analyzedSnapshotId = safeDashboardDisplayText(source.snapshotId, "");
  const currentSnapshotId = safeDashboardDisplayText(
    source.currentSnapshotId || market.snapshotId,
    "",
  );
  const matchesCurrentSnapshot = source.matchesCurrentSnapshot === true
    || Boolean(
      analyzedSnapshotId
      && currentSnapshotId
      && analyzedSnapshotId === currentSnapshotId,
    );
  const sourceMissionId = safeDashboardDisplayText(source.sourceMissionId, "");
  const averageConfidence = firstFiniteSignalNumber(source.averageConfidence, source.confidence);
  const tradePlan = source.tradePlan && typeof source.tradePlan === "object"
    ? source.tradePlan
    : {};
  const qualityGate = source.qualityGate && typeof source.qualityGate === "object"
    ? source.qualityGate
    : {};
  const decisionProvenance = source.decisionProvenance && typeof source.decisionProvenance === "object"
    ? source.decisionProvenance
    : {};
  const protectivePlanProvenance = tradePlan.protectivePlanProvenance
    && typeof tradePlan.protectivePlanProvenance === "object"
    ? tradePlan.protectivePlanProvenance
    : {};
  const protectivePlanSource = safeDashboardDisplayText(
    tradePlan.protectivePlanSource
      || protectivePlanProvenance.source
      || decisionProvenance.protectivePlanSource
      || (qualityGate.protectivePlanFallbackUsed === true
        ? "backend_deterministic_fallback"
        : ""),
    tradePlan.available === true ? "price_action_agent" : "unavailable",
  ).toLowerCase();
  const protectivePlanReasonCode = safeDashboardDisplayText(
    tradePlan.protectivePlanReasonCode
      || protectivePlanProvenance.reasonCode
      || qualityGate.protectivePlanReasonCode
      || decisionProvenance.protectivePlanReasonCode,
    tradePlan.available === true ? "price_action_directional_plan" : "consensus_not_trade_eligible",
  ).toLowerCase();
  const protectivePriceOwnerRole = safeDashboardDisplayText(
    tradePlan.protectivePriceOwnerRole
      || decisionProvenance.protectivePriceOwnerRole
      || qualityGate.protectivePriceOwnerRole,
    protectivePlanSource === "backend_deterministic_fallback"
      ? "backend_deterministic_guard"
      : "price_action",
  ).toLowerCase();
  const stopLossPrice = Number.isFinite(Number(tradePlan.stopLossPrice))
    ? Number(tradePlan.stopLossPrice)
    : null;
  const takeProfitPrice = Number.isFinite(Number(tradePlan.takeProfitPrice))
    ? Number(tradePlan.takeProfitPrice)
    : null;
  const buyCount = count("buy") ?? 0;
  const sellCount = count("sell") ?? 0;
  const hasDirectionalConflict = source.conflictingDirections === true
    || source.directionConflict === true
    || (buyCount > 0 && sellCount > 0);
  const requiredVotes = normalizeSignalRequiredVotes(
    source.requiredVotes ?? source?.policy?.requiredVotes ?? consensusPolicy.requiredVotes,
  );
  const matchingDirectionalVotes = rawDecision === "BUY"
    ? buyCount
    : rawDecision === "SELL"
      ? sellCount
      : 0;
  const directionalAgreementMet = source.directionalAgreementMet === true
    || source.agreementMet === true
    || (
      ["BUY", "SELL"].includes(rawDecision)
      && matchingDirectionalVotes >= requiredVotes
      && !hasDirectionalConflict
    );
  const directionalPlanReady = ["BUY", "SELL"].includes(rawDecision)
    && voteCount === AI_TRADE_COUNCIL_AGENT_IDS.length
    && directionalAgreementMet
    && !hasDirectionalConflict
    && tradePlan.available === true
    && stopLossPrice !== null
    && takeProfitPrice !== null;
  const safeDisplayDecision = ["BUY", "SELL"].includes(displayDecision) && !directionalPlanReady
    ? "NO TRADE"
    : displayDecision;
  const belongsToLatestRun = consensusSelection.current;
  const fallbackReason = !available && run.state === "blocked"
    ? run.reason
    : !available
      ? "ผลวิเคราะห์ยังไม่ครบ 3 Specialist จึงไม่มีมติของรอบนี้"
    : directionalPlanReady
      ? `คะแนนผ่านเกณฑ์ ${requiredVotes} ใน 3 และกำหนด SL/TP ครบแล้ว ระบบจะส่งต่อเมื่อ MetafxHQ AI Council EA เชื่อมอยู่`
      : hasDirectionalConflict
        ? "พบทั้ง BUY และ SELL ในรอบเดียวกัน ระบบจึงสรุป NO TRADE และไม่ส่ง Order"
        : `คะแนนยังไม่ถึงเกณฑ์ ${requiredVotes} ใน 3 หรือแผนยังไม่ครบ ระบบจึงสรุป NO TRADE และไม่ส่ง Order`;
  return {
    available,
    buy: count("buy"),
    hold: count("hold"),
    sell: count("sell"),
    decision: available ? safeDisplayDecision : (run.state === "blocked" ? "ติดขัด" : "ข้อมูลไม่ครบ"),
    voteCount,
    votes,
    averageConfidence,
    unanimous: source.unanimous === true,
    requiredVotes,
    matchingDirectionalVotes,
    directionalAgreementMet,
    hasDirectionalConflict,
    snapshotId: analyzedSnapshotId,
    currentSnapshotId,
    matchesCurrentSnapshot,
    sourceMissionId,
    belongsToLatestRun,
    tradePlan: {
      available: directionalPlanReady,
      direction: safeDashboardDisplayText(tradePlan.direction, ""),
      stopLossPrice,
      takeProfitPrice,
      protectivePlanSource,
      protectivePlanReasonCode,
      protectivePlanProvenance,
      protectivePriceOwnerRole,
    },
    tradeGateway: source.tradeGateway && typeof source.tradeGateway === "object"
      ? source.tradeGateway
      : null,
    riskGuard: source.riskGuard && typeof source.riskGuard === "object"
      ? source.riskGuard
      : null,
    reason: safeDashboardDisplayText(
      sourceReason,
      fallbackReason,
    ),
    run,
  };
}

function signalCouncilQualityModel(report = {}, consensus = {}, market = signalMarketModel(report)) {
  const council = signalCouncilModel(report);
  const pipeline = council.decisionPipeline && typeof council.decisionPipeline === "object"
    ? council.decisionPipeline
    : {};
  const chart = council.chartSnapshot && typeof council.chartSnapshot === "object"
    ? council.chartSnapshot
    : {};
  const readiness = council.analysisReadiness && typeof council.analysisReadiness === "object"
    ? council.analysisReadiness
    : {};
  const run = consensus.run || signalCouncilRunModel(report);
  const currentConsensusSelection = signalCurrentConsensusSource(report, run);
  const consensusSource = currentConsensusSelection.current
    ? currentConsensusSelection.source
    : {};
  const expectedMissionId = String(run?.parent?.id || "");
  const expectedSnapshotId = safeDashboardDisplayText(run?.snapshotId, "");
  const gateMatchesCurrentRun = (gate, owner = {}) => {
    if (!gate || typeof gate !== "object" || !expectedMissionId || !expectedSnapshotId) return false;
    const missionId = String(
      gate.sourceMissionId
        || gate.missionId
        || gate.parentMissionId
        || owner.sourceMissionId
        || owner.missionId
        || owner.parentMissionId
        || "",
    );
    const snapshotId = safeDashboardDisplayText(
      gate.snapshotId
        || gate.sourceSnapshotId
        || owner.snapshotId
        || owner.sourceSnapshotId
        || owner.currentId,
      "",
    );
    return missionId === expectedMissionId && snapshotId === expectedSnapshotId;
  };
  const gateCandidates = [
    [consensusSource.qualityGate, consensusSource],
    [council.liveAnalysis?.qualityGate, council.liveAnalysis],
    [pipeline.qualityGate, pipeline],
    [pipeline.snapshot?.qualityGate, pipeline.snapshot],
    [council.councilQualityGate, council],
    [council.qualityGate, council],
    [chart.councilQualityGate, chart],
    [chart.qualityGate, chart],
  ];
  const observedGate = gateCandidates
    .find(([gate, owner]) => gateMatchesCurrentRun(gate, owner))?.[0] || null;
  const policyGate = [
    observedGate?.policy,
    council.qualityPolicy,
    council.sharedPolicy?.qualityGate,
    pipeline.qualityPolicy,
    pipeline.policy?.qualityGate,
    consensusSource.qualityPolicy,
  ].find((value) => value && typeof value === "object") || observedGate;
  const observedReasonCodes = Array.isArray(observedGate?.reasonCodes)
    ? observedGate.reasonCodes.map((value) => String(value || "").trim()).filter(Boolean)
    : [];
  const localizedReasonCodes = observedReasonCodes
    .map((value) => signalCouncilQualityReasonLabel(value))
    .filter(Boolean);
  const localizedGateReason = localizedReasonCodes.length
    ? localizedReasonCodes.join(" • ")
    : observedReasonCodes.length
      ? "Backend ระบุว่ามีเงื่อนไขที่ยังไม่ผ่าน กรุณาเริ่มรอบวิเคราะห์ใหม่หรือตรวจรายละเอียด Mission"
      : "";
  const votes = Array.isArray(consensus.votes) ? consensus.votes : [];
  const horizons = [...new Set(votes.map((vote) => (
    safeDashboardDisplayText(vote?.horizon || vote?.horizonBars, "")
  )).filter(Boolean))];
  const confidences = votes
    .map((vote) => firstFiniteSignalNumber(vote?.confidence))
    .filter((value) => value !== null);
  const observedAverageConfidence = consensus.averageConfidence !== null
    && consensus.averageConfidence !== undefined
    ? Number(consensus.averageConfidence)
    : confidences.length
      ? confidences.reduce((sum, value) => sum + value, 0) / confidences.length
      : null;
  const defaultConfidenceFloor = firstFiniteSignalNumber(
    policyGate?.confidenceFloorDefault,
    policyGate?.minimumConfidence,
    policyGate?.minimumConfidencePercent,
    policyGate?.minConfidence,
  );
  const roleFloors = policyGate?.confidenceFloorByRole && typeof policyGate.confidenceFloorByRole === "object"
    ? policyGate.confidenceFloorByRole
    : null;
  const confidenceFloorAvailable = defaultConfidenceFloor !== null || Boolean(roleFloors);
  const confidenceFloorPassed = confidenceFloorAvailable
    && votes.length === AI_TRADE_COUNCIL_AGENT_IDS.length
    && votes.every((vote) => {
      const confidence = firstFiniteSignalNumber(vote?.confidence);
      const floor = firstFiniteSignalNumber(roleFloors?.[vote?.roleId], defaultConfidenceFloor);
      return confidence !== null && floor !== null && confidence >= floor;
    });
  const eventRisk = safeDashboardDisplayText(
    observedGate?.eventRisk
      || consensusSource?.eventRisk
      || votes.find((vote) => vote?.roleId === "news")?.eventRisk
      || votes.find((vote) => String(vote?.agentId || "") === "codex_mcp_operator")?.eventRisk,
    "",
  ).toUpperCase();
  const eventRiskVeto = eventRisk === "VETO";
  const newsBlackout = observedGate?.newsBlackout && typeof observedGate.newsBlackout === "object"
    ? observedGate.newsBlackout
    : null;
  const snapshotAgeSeconds = Number.isFinite(Number(chart.ageSeconds))
    ? Number(chart.ageSeconds)
    : Number.isFinite(Number(market.freshnessMinutes))
      ? Math.round(Number(market.freshnessMinutes) * 60)
      : null;
  const maximumSnapshotAgeSeconds = firstFiniteSignalNumber(
    policyGate?.maximumSnapshotAgeSeconds,
    policyGate?.maxSnapshotAgeSeconds,
  );
  const observedStatus = String(observedGate?.status || "").toLowerCase();
  const explicitlyPassed = observedGate?.passed === true
    || observedGate?.ready === true
    || ["passed", "ready", "complete"].includes(observedStatus);
  const explicitlyBlocked = observedGate?.passed === false
    || observedGate?.ready === false
    || ["blocked", "failed", "rejected"].includes(observedStatus);
  const gateState = !observedGate
    ? "unavailable"
    : explicitlyPassed
      ? "complete"
      : explicitlyBlocked
        ? "blocked"
        : "waiting";
  const rows = [
    {
      label: "ความสดของ Snapshot",
      state: !market.available || snapshotAgeSeconds === null
        ? "waiting"
        : maximumSnapshotAgeSeconds !== null && snapshotAgeSeconds > maximumSnapshotAgeSeconds
          ? "blocked"
          : "complete",
      value: snapshotAgeSeconds === null ? "รอข้อมูลจาก Backend" : `${snapshotAgeSeconds} วินาที`,
      detail: maximumSnapshotAgeSeconds === null
        ? "ยังไม่มีเกณฑ์อายุสูงสุดจาก Quality Gate"
        : `เกณฑ์ไม่เกิน ${maximumSnapshotAgeSeconds} วินาที`,
    },
    {
      label: "คุณภาพข้อมูลราคา",
      state: observedGate
        ? (explicitlyBlocked ? "blocked" : explicitlyPassed ? "complete" : "waiting")
        : readiness.available === true || chart.available === true
          ? "complete"
          : "waiting",
      value: observedGate
        ? `${firstFiniteSignalNumber(observedGate.observedBars) ?? "รอ"} / ${firstFiniteSignalNumber(observedGate.minimumBars) ?? "รอ"} แท่ง`
        : readiness.available === true || chart.available === true
          ? "Backend ยืนยัน Snapshot แล้ว"
          : "รอ Snapshot ที่ตรวจแล้ว",
      detail: observedGate ? "แสดงผลตรวจ OHLC/Quote จาก Backend" : "ยังไม่มีผล Council Quality Gate แยกต่างหาก",
    },
    {
      label: "ขอบเขตเวลาของมุมมอง",
      state: votes.length < AI_TRADE_COUNCIL_AGENT_IDS.length
        ? "waiting"
        : horizons.length === 1
          ? "complete"
          : "blocked",
      value: votes.length < AI_TRADE_COUNCIL_AGENT_IDS.length
        ? `ได้รับ ${votes.length}/3 คะแนน`
        : horizons.length === 1
          ? `ตรงกัน: ${horizons[0]}`
          : horizons.length
            ? `ไม่ตรงกัน: ${horizons.join(" / ")}`
            : "Specialist ไม่ได้ส่ง Horizon",
      detail: "Horizon ต้องมาจากผลตอบกลับของ Specialist รอบเดียวกัน",
    },
    {
      label: "Confidence ขั้นต่ำ",
      state: !confidenceFloorAvailable
        ? "unavailable"
        : confidenceFloorPassed
          ? "complete"
          : votes.length < AI_TRADE_COUNCIL_AGENT_IDS.length
            ? "waiting"
            : "blocked",
      value: !confidenceFloorAvailable
        ? "ยังไม่มีเกณฑ์จาก Backend"
        : confidences.length
          ? `ต่ำสุด ${Math.min(...confidences).toFixed(0)}% • เฉลี่ย ${observedAverageConfidence.toFixed(1)}%`
          : "รอคะแนน Confidence",
      detail: defaultConfidenceFloor === null
        ? (roleFloors ? "ใช้ Floor แยกตามบทบาทจาก Backend" : "Backend ยังไม่ส่งค่า Floor กลาง")
        : `Floor กลาง ${defaultConfidenceFloor}%${roleFloors ? " • อาจแยกตามบทบาท" : ""}`,
    },
    {
      label: "ข่าวสำคัญ / Event Risk",
      state: eventRiskVeto
        ? "blocked"
        : eventRisk === "ALLOW"
          ? "complete"
          : eventRisk === "HOLD"
            ? "skipped"
            : "unavailable",
      value: eventRiskVeto
        ? "หยุดเพราะข่าว (VETO)"
        : eventRisk === "HOLD"
          ? "งดออกเสียง • ไม่หยุดรอบ"
          : eventRisk === "ALLOW"
            ? "อนุญาตให้รวมคะแนน"
            : "ยังไม่มีข้อมูลจาก Backend",
      detail: eventRiskVeto
        ? (newsBlackout?.reasonTh || newsBlackout?.reason || "News Consultant พบความเสี่ยงข่าวที่ต้องหยุดทั้งรอบ")
        : eventRisk === "HOLD"
          ? "News Consultant ไม่เลือก BUY/SELL ในรอบนี้ แต่เสียงที่ผ่านเกณฑ์ของ Specialist ตัวอื่นยังไปต่อได้"
          : eventRisk === "ALLOW"
            ? "News จะเลือก BUY/SELL ได้เมื่อมีข่าวสดจากอย่างน้อย 2 โดเมนสาธารณะที่ต่างกัน"
            : "ไม่อนุมาน Event Risk เมื่อ Backend ไม่ได้ส่งค่า",
    },
  ];
  return {
    available: Boolean(observedGate),
    state: gateState,
    statusLabel: gateState === "complete"
      ? "ผ่าน Council Quality Gate"
      : gateState === "blocked"
        ? (eventRiskVeto ? "หยุดเพราะข่าว (VETO)" : "Quality Gate หยุดรอบนี้")
        : gateState === "waiting"
          ? "กำลังรอผล Quality Gate"
          : "ยังไม่มีผล Quality Gate จาก Backend",
    reason: [
      safeDashboardDisplayText(
        observedGate?.reasonTh || localizedGateReason || observedGate?.reason,
        "Frontend จะแสดงเพียงสถานะที่ Backend ยืนยัน และไม่ถือว่าผ่านเอง",
      ),
      eventRiskVeto
        ? "News Consultant ส่ง VETO จึงหยุดทั้งรอบ"
        : eventRisk === "HOLD"
          ? "HOLD คือการงดออกเสียง ไม่ใช่การหยุด Order; หาก Gate ยังไม่ผ่านให้ดูเงื่อนไขอื่นหรือเริ่มรอบใหม่"
          : "",
    ].filter(Boolean).join(" • "),
    rows,
  };
}

function signalTradeOperationsModel(report = {}, runtime = {}, consensus = {}) {
  const gateway = consensus.tradeGateway && typeof consensus.tradeGateway === "object"
    ? consensus.tradeGateway
    : {};
  const command = runtime.gatewayCommand || (gateway.command && typeof gateway.command === "object" ? gateway.command : null);
  const ack = runtime.gatewayLastAck || (command?.ack && typeof command.ack === "object" ? command.ack : null);
  const commandPublished = runtime.gatewayCommandPublished === true || gateway.commandPublished === true;
  const commandStatus = safeDashboardDisplayText(command?.status || gateway.status || runtime.gatewayCommandStatus, "");
  const ackStatus = safeDashboardDisplayText(ack?.status || gateway.ackStatus, "").toUpperCase();
  const verifiedAckFill = ackStatus === "EXECUTED"
    && safeDashboardDisplayText(ack?.verificationStatus, "").toUpperCase() === "VERIFIED"
    && Number.isFinite(Number(ack?.ticket))
    && Number(ack?.ticket) > 0
    && Number.isFinite(Number(ack?.filledPrice))
    && Number(ack?.filledPrice) > 0
    ? {
        verified: true,
        ticket: Number(ack.ticket),
        filledPrice: Number(ack.filledPrice),
        slippagePoints: Number.isFinite(Number(ack.filledSlippagePoints))
          ? Number(ack.filledSlippagePoints)
          : null,
        stopLoss: Number.isFinite(Number(ack.actualStopLoss)) ? Number(ack.actualStopLoss) : null,
        takeProfit: Number.isFinite(Number(ack.actualTakeProfit)) ? Number(ack.actualTakeProfit) : null,
      }
    : null;
  const fill = [command?.fill, ack?.fill, gateway.fill, verifiedAckFill]
    .find((value) => value && typeof value === "object") || null;
  const fillVerified = fill?.verified === true || gateway.fillVerified === true;
  const recoveryIncident = ackStatus === "EXECUTION_UNKNOWN"
    || ["expired_waiting_ack", "recovery_required", "incident"].includes(commandStatus.toLowerCase())
    || gateway.status === "waiting_previous_ack";
  const noTrade = consensus.available && !consensus.tradePlan.available;
  const commandState = commandPublished
    ? "complete"
    : noTrade
      ? "skipped"
      : consensus.tradePlan.available
        ? (runtime.gatewayConnected ? "waiting" : "blocked")
        : "unavailable";
  const ackState = recoveryIncident
    ? "blocked"
    : ackStatus
      ? (["EXECUTED", "SHADOWED", "REJECTED", "DUPLICATE", "FAILED_FINAL"].includes(ackStatus) ? "complete" : "waiting")
      : commandPublished
        ? "waiting"
        : noTrade
          ? "skipped"
          : "unavailable";
  const fillState = recoveryIncident
    ? "blocked"
    : fillVerified
      ? "complete"
      : ackStatus === "EXECUTED"
        ? "unavailable"
        : noTrade || ["SHADOWED", "REJECTED", "DUPLICATE", "FAILED_FINAL"].includes(ackStatus)
          ? "skipped"
          : commandPublished
            ? "waiting"
            : "unavailable";
  return {
    commandState,
    ackState,
    fillState,
    incident: recoveryIncident,
    rows: [
      {
        label: "Command",
        state: commandState,
        value: commandPublished ? `ส่งแล้ว • ${safeDashboardDisplayText(command?.commandId, "มี Command ID")}` : noTrade ? "ข้าม: มติ NO TRADE" : "ยังไม่ส่ง",
        detail: commandStatus || "รอสถานะจาก Trade Gateway",
      },
      {
        label: "ACK จาก EA",
        state: ackState,
        value: ackStatus || (commandPublished ? "กำลังรอ ACK" : "ยังไม่มี ACK"),
        detail: signalExecutionGuardReasonLabel(ack?.reasonCode || gateway.reasonCode),
      },
      {
        label: "Fill / Order จริง",
        state: fillState,
        value: fillVerified
          ? "Backend ยืนยัน Fill แล้ว"
          : ackStatus === "EXECUTED"
            ? "EA ส่ง ACK EXECUTED"
            : fillState === "skipped"
              ? "ไม่มี Fill ในรอบนี้"
              : "ยังไม่มีข้อมูล Fill",
        detail: fillVerified
          ? safeDashboardDisplayText(fill?.ticket || fill?.orderId, "ยืนยันโดย Backend")
          : ackStatus === "EXECUTED"
            ? "ยังไม่มีข้อมูลตรวจ Fill แยกจาก Backend"
            : "Frontend จะไม่เดาสถานะการจับคู่คำสั่ง",
      },
      {
        label: "Recovery / Incident",
        state: recoveryIncident ? "blocked" : commandPublished || ackStatus ? "complete" : "unavailable",
        value: recoveryIncident ? "ต้องตรวจสถานะกับ EA ก่อนส่งซ้ำ" : commandPublished || ackStatus ? "ยังไม่พบ Incident" : "ยังไม่มีรอบคำสั่ง",
        detail: recoveryIncident ? (ackStatus || commandStatus || "สถานะไม่ชัดเจน") : "ไม่ Retry คำสั่งเดิมจาก Frontend",
      },
    ],
  };
}

function signalRoundHealthModel(report = {}, automation = signalCouncilAutomationModel(report), run = signalCouncilRunModel(report)) {
  const council = signalCouncilModel(report);
  const pipeline = council.decisionPipeline && typeof council.decisionPipeline === "object"
    ? council.decisionPipeline
    : {};
  const qualityPolicy = [
    council.qualityPolicy,
    pipeline.qualityPolicy,
    council.councilQualityGate?.policy,
  ].find((value) => value && typeof value === "object") || {};
  const suppliedAutomation = council.autoAnalysis && typeof council.autoAnalysis === "object"
    ? council.autoAnalysis
    : (council.automation && typeof council.automation === "object" ? council.automation : {});
  const automationConfig = suppliedAutomation.config && typeof suppliedAutomation.config === "object"
    ? suppliedAutomation.config
    : suppliedAutomation;
  const automationState = suppliedAutomation.state && typeof suppliedAutomation.state === "object"
    ? suppliedAutomation.state
    : suppliedAutomation;
  const dailyQuotaAvailable = ["maxDailyRounds", "maxDailyRuns"].some((key) => (
    Object.prototype.hasOwnProperty.call(automationConfig, key)
    || Object.prototype.hasOwnProperty.call(suppliedAutomation, key)
  )) && ["dailyRunCount"].some((key) => (
    Object.prototype.hasOwnProperty.call(automationState, key)
    || Object.prototype.hasOwnProperty.call(suppliedAutomation, key)
  ));
  const reserveAvailable = Object.prototype.hasOwnProperty.call(automationConfig, "minRemainingPercent")
    || Object.prototype.hasOwnProperty.call(suppliedAutomation, "minRemainingPercent");
  const createdAt = run.parent?.createdAt ? new Date(run.parent.createdAt).getTime() : null;
  const explicitDeadline = run.parent?.deadlineAt
    || run.parent?.expiresAt
    || run.parent?.delegation?.deadlineAt
    || null;
  const roundDeadlineSeconds = firstFiniteSignalNumber(
    run.parent?.delegation?.roundDeadlineSeconds,
    qualityPolicy.roundDeadlineSeconds,
  );
  const derivedDeadline = !explicitDeadline && createdAt && roundDeadlineSeconds !== null
    ? new Date(createdAt + (roundDeadlineSeconds * 1000)).toISOString()
    : explicitDeadline;
  const completedAt = run.parent?.completedAt || (run.state === "completed" || run.state === "blocked" ? run.parent?.updatedAt : null);
  const completedTime = completedAt ? new Date(completedAt).getTime() : null;
  const roundAgeSeconds = createdAt
    ? Math.max(0, Math.round(((Number.isFinite(completedTime) ? completedTime : Date.now()) - createdAt) / 1000))
    : null;
  const remainingPercent = firstFiniteSignalNumber(state.codexRate.snapshot?.primary?.remainingPercent);
  return {
    rows: [
      {
        label: "Lag ของรอบ",
        state: run.parent ? (run.state === "blocked" ? "blocked" : run.state === "running" ? "waiting" : "complete") : "unavailable",
        value: roundAgeSeconds === null ? "ยังไม่มีรอบจาก Backend" : `${roundAgeSeconds} วินาที`,
        detail: run.parent ? run.statusLabel : "เริ่มนับเมื่อ Backend สร้าง Mission",
      },
      {
        label: "Deadline",
        state: derivedDeadline ? (Date.now() > new Date(derivedDeadline).getTime() && run.state === "running" ? "blocked" : "complete") : "unavailable",
        value: derivedDeadline ? formatThaiDateTime(derivedDeadline) : "ยังไม่มี Deadline จาก Backend",
        detail: roundDeadlineSeconds === null ? "ไม่สร้างเวลาเส้นตายใน Frontend" : `นโยบาย ${roundDeadlineSeconds} วินาที`,
      },
      {
        label: "Quota วันนี้",
        state: !dailyQuotaAvailable ? "unavailable" : automation.dailyRunCount >= automation.maxDailyRounds ? "blocked" : "complete",
        value: dailyQuotaAvailable ? `${automation.dailyRunCount}/${automation.maxDailyRounds} รอบ` : "ยังไม่มีข้อมูลรอบจาก Backend",
        detail: reserveAvailable ? `สำรอง Rate Limit อย่างน้อย ${automation.minRemainingPercent}%` : "ยังไม่มีเกณฑ์สำรองจาก Backend",
      },
      {
        label: "Codex คงเหลือ",
        state: remainingPercent === null
          ? "unavailable"
          : reserveAvailable && remainingPercent < automation.minRemainingPercent
            ? "blocked"
            : "complete",
        value: remainingPercent === null ? "ยังอ่าน Rate Limit ไม่ได้" : `${remainingPercent.toFixed(0)}%`,
        detail: reserveAvailable
          ? (automation.reasonMessage || `เกณฑ์สำรอง ${automation.minRemainingPercent}%`)
          : "แสดงยอดคงเหลือเท่านั้น เพราะ Backend ยังไม่ส่งเกณฑ์สำรอง",
      },
    ],
  };
}

function renderSignalAssuranceRows(container, rows = []) {
  if (!container) return;
  container.innerHTML = "";
  rows.forEach((item) => {
    const row = document.createElement("div");
    const icon = document.createElement("span");
    const copy = document.createElement("div");
    const label = document.createElement("strong");
    const detail = document.createElement("small");
    const value = document.createElement("b");
    row.className = "signal-assurance-row";
    row.dataset.state = item.state || "unavailable";
    icon.textContent = item.state === "complete" ? "✓" : item.state === "blocked" ? "!" : item.state === "skipped" ? "–" : "○";
    label.textContent = item.label;
    detail.textContent = item.detail;
    value.textContent = item.value;
    copy.append(label, detail);
    row.append(icon, copy, value);
    container.appendChild(row);
  });
}

function renderSignalVoteSummary(container, consensus) {
  if (!container) return;
  const values = [
    ["BUY", consensus.buy, "buy"],
    ["งดออกเสียง", consensus.hold, "hold"],
    ["SELL", consensus.sell, "sell"],
  ];
  container.innerHTML = "";
  values.forEach(([label, value, tone]) => {
    const item = document.createElement("div");
    const number = document.createElement("strong");
    const name = document.createElement("span");
    item.className = `signal-vote-count ${tone}`;
    number.textContent = value === null ? "—" : String(value);
    name.textContent = label;
    item.append(number, name);
    container.appendChild(item);
  });
}

function signalProtectivePlanReasonLabel(value) {
  const code = String(value || "").trim().toLowerCase();
  const labels = {
    price_action_directional_plan: "Price Action Consultant เลือกทิศทางและเสนอ SL/TP ที่ผ่านการตรวจ",
    price_action_hold_consensus_fallback: "Price Action งดออกเสียง แต่เสียงทิศทางผ่านเกณฑ์ Backend จึงสร้าง SL/TP สำรองแบบตายตัว",
    fallback_snapshot_missing: "หยุดรอบนี้: ไม่พบ Snapshot สำหรับคำนวณ SL/TP สำรอง",
    fallback_snapshot_mismatch: "หยุดรอบนี้: Snapshot ของผลโหวตกับข้อมูลคำนวณ SL/TP ไม่ตรงกัน",
    fallback_snapshot_digest_missing: "หยุดรอบนี้: ไม่พบลายนิ้วมือดิจิทัลของ Snapshot จึงยืนยันข้อมูลสำหรับ SL/TP สำรองไม่ได้",
    fallback_snapshot_digest_mismatch: "หยุดรอบนี้: ลายนิ้วมือดิจิทัลของ Snapshot ไม่ตรงกัน จึงไม่ใช้ข้อมูลนั้นสร้าง SL/TP สำรอง",
    fallback_closed_bar_mismatch: "หยุดรอบนี้: ข้อมูลแท่งปิดสำหรับ SL/TP สำรองไม่ตรงกับรอบวิเคราะห์",
    fallback_inputs_unavailable: "หยุดรอบนี้: ข้อมูลโครงสร้างราคาและ ATR ไม่ครบสำหรับคำนวณ SL/TP สำรอง",
    fallback_plan_invalid: "หยุดรอบนี้: SL/TP สำรองไม่ผ่านกฎทิศทางหรืออัตราผลตอบแทนต่อความเสี่ยง",
    consensus_not_trade_eligible: "ยังไม่มีทิศทางที่ผ่านเกณฑ์ จึงไม่สร้าง SL/TP",
    price_action_protective_plan_failed: "หยุดรอบนี้: SL/TP จาก Price Action ไม่ผ่าน และ Backend สร้างแผนสำรองที่ปลอดภัยไม่ได้",
  };
  return labels[code] || "";
}

function signalCouncilQualityReasonLabel(value) {
  const code = String(value || "").trim().toLowerCase();
  const protective = signalProtectivePlanReasonLabel(code);
  if (protective) return protective;
  if (code.startsWith("confidence_below_floor:")) {
    const role = code.split(":")[1];
    const roleLabel = {
      technical: "Technical Consultant",
      price_action: "Price Action Consultant",
      news: "News Consultant",
    }[role] || "Specialist";
    return `หยุดรอบนี้: คะแนนความเชื่อมั่นของ ${roleLabel} ต่ำกว่าเกณฑ์`;
  }
  const labels = {
    incomplete_or_mismatched_votes: "หยุดรอบนี้: ผลจาก Specialist ไม่ครบ หรือมาจากคนละ Snapshot",
    input_quality_gate_not_passed: "หยุดรอบนี้: ข้อมูลตลาดไม่ผ่านการตรวจคุณภาพ",
    round_deadline_unavailable: "หยุดรอบนี้: Backend ไม่พบเวลาสิ้นสุดของรอบวิเคราะห์",
    round_deadline_expired: "หยุดรอบนี้: ผลวิเคราะห์มาถึงหลังหมดเวลาของรอบ",
    decision_horizon_expired: "หยุดรอบนี้: อายุของผลวิเคราะห์หมดแล้ว",
    technical_deterministic_validation_failed: "หยุดรอบนี้: ผล Technical ไม่ตรงกับค่าที่ Backend คำนวณตรวจสอบ",
    news_event_veto: "หยุดรอบนี้: News Consultant พบข่าวที่ต้องระงับการเทรด",
    news_evidence_gate_failed: "หยุดรอบนี้: หลักฐานข่าวไม่สดหรือมีแหล่งข้อมูลไม่ครบ",
    news_vote_unavailable: "หยุดรอบนี้: ยังไม่มีผลจาก News Consultant ที่ตรวจสอบได้",
    direction_conflict_buy_sell: "หยุดรอบนี้: พบทั้ง BUY และ SELL ในรอบเดียวกัน",
    directional_votes_below_threshold: "ยังมีเสียง BUY หรือ SELL ไม่ถึงเกณฑ์ที่ตั้งไว้",
    quality_gate_blocked: "หยุดรอบนี้: Council Quality Gate ไม่ผ่าน",
    snapshot_mismatch: "หยุดรอบนี้: ผลวิเคราะห์มาจากคนละ Snapshot",
    snapshot_stale: "หยุดรอบนี้: Snapshot เก่าเกินเกณฑ์",
    quote_or_spread_invalid: "หยุดรอบนี้: ราคาหรือ Spread ไม่ผ่านเกณฑ์",
  };
  return labels[code] || "";
}

function signalProtectivePlanViewModel(consensus = {}) {
  const plan = consensus.tradePlan && typeof consensus.tradePlan === "object"
    ? consensus.tradePlan
    : {};
  const source = String(plan.protectivePlanSource || "unavailable").trim().toLowerCase();
  const reasonCode = String(plan.protectivePlanReasonCode || "").trim().toLowerCase();
  const reason = signalProtectivePlanReasonLabel(reasonCode);
  if (source === "price_action_agent") {
    return {
      state: "price_action_agent",
      label: "SL/TP จาก Price Action AI",
      detail: reason || "Price Action Consultant เสนอระดับ SL/TP จากโครงสร้างราคาใน Snapshot เดียวกัน",
    };
  }
  if (source === "backend_deterministic_fallback") {
    return {
      state: "backend_deterministic_fallback",
      label: "SL/TP สำรองจาก Backend",
      detail: reason || "Backend คำนวณแบบตายตัวจากแท่งปิดและ Snapshot เดียวกัน ไม่ใช่การเดาราคาใหม่ของ AI",
    };
  }
  const blocked = reasonCode.startsWith("fallback_")
    || reasonCode === "price_action_protective_plan_failed";
  return {
    state: blocked ? "blocked" : "unavailable",
    label: "ยังไม่มี SL/TP ที่ส่งคำสั่งได้",
    detail: reason || "รอ Backend ยืนยันแผน SL/TP ของรอบนี้",
  };
}

function renderSignalProtectivePlanProvenance(container, consensus) {
  if (!container) return;
  const view = signalProtectivePlanViewModel(consensus);
  container.dataset.state = view.state;
  const source = container.querySelector("[data-signal-plan-source]");
  const detail = container.querySelector("[data-signal-plan-source-detail]");
  if (source) source.textContent = view.label;
  if (detail) detail.textContent = view.detail;
}

function signalExecutionGuardReasonLabel(value) {
  const code = String(value || "").trim().toUpperCase();
  const labels = {
    READY: "ผ่านการตรวจความพร้อม",
    STARTING: "EA กำลังเริ่มระบบ",
    KILL_SWITCH_ACTIVE: "Kill Switch กำลังหยุดระบบ",
    TERMINAL_NOT_CONNECTED: "MT4 ยังไม่เชื่อมต่อกับ Broker",
    QUOTE_NOT_AVAILABLE: "ยังไม่มีราคาล่าสุด",
    QUOTE_NOT_OBSERVED: "EA ยังไม่ส่งราคา Bid/Ask ที่ตรวจสอบได้",
    QUOTE_STALE: "ราคาล่าสุดเก่าเกินกำหนด",
    FIXED_LOT_CONFIGURATION_INVALID: "ค่า Fixed Lot ไม่ถูกต้อง",
    MANAGED_POSITION_LIMIT_REACHED: "จำนวน Position ถึงขีดจำกัด",
    MAX_MANAGED_POSITIONS_REACHED: "จำนวน Position ถึงขีดจำกัด",
    MANAGED_LOT_LIMIT_REACHED: "ปริมาณ Lot ถึงขีดจำกัด",
    MAX_MANAGED_LOTS_EXCEEDED: "ปริมาณ Lot ถึงขีดจำกัด",
    DAILY_TRADE_LIMIT_REACHED: "จำนวนรายการวันนี้ถึงขีดจำกัด",
    MAX_TRADES_PER_DAY_REACHED: "จำนวนรายการวันนี้ถึงขีดจำกัด",
    DAILY_LOSS_LIMIT_REACHED: "ขาดทุนวันนี้ถึงขีดจำกัด",
    DAILY_LOSS_LIMIT_LATCHED: "ขาดทุนวันนี้ถึงขีดจำกัดและ EA ล็อกการส่งคำสั่งแล้ว",
    ACCOUNT_DRAWDOWN_LIMIT_REACHED: "Drawdown ของบัญชีถึงขีดจำกัด",
    ACCOUNT_EQUITY_DRAWDOWN_LIMIT_REACHED: "Drawdown ของบัญชีถึงขีดจำกัด",
    LIVE_NOT_ARMED: "ยังไม่ได้เปิด Live Armed ที่ EA",
    LIVE_MODE_REQUIRES_NON_DEMO_ACCOUNT: "EA อยู่โหมด LIVE แต่ MT4 เป็นบัญชี Demo ให้เปลี่ยน EA เป็น DEMO หรือใช้บัญชีจริง",
    DEMO_MODE_REQUIRES_DEMO_ACCOUNT: "EA อยู่โหมด DEMO แต่ MT4 เป็นบัญชีจริง ให้เปลี่ยน EA เป็น LIVE/SHADOW หรือใช้บัญชี Demo",
    ACCOUNT_IDENTITY_UNAVAILABLE: "EA รุ่นเดิมยังไม่รายงานประเภทบัญชี กรุณา Refresh หรือถอดแล้วลาก MetafxHQTradeGateway v2.11 ลงกราฟใหม่",
    GATEWAY_STATUS_ACCOUNT_IDENTITY_UNAVAILABLE: "EA รุ่นเดิมยังไม่รายงานประเภทบัญชี กรุณา Refresh หรือถอดแล้วลาก MetafxHQTradeGateway v2.11 ลงกราฟใหม่",
    SIGNING_KEY_NOT_READY: "EA ยังเปิดใช้ Key สำหรับตรวจลายเซ็นไม่ได้",
    LIVE_SIGNING_KEY_NOT_PINNED: "โหมด Live ยังไม่ได้ปักหมุด Key ID ที่เชื่อถือใน EA",
    SIGNING_KEY_MISMATCH: "Key ID ของ Backend และ EA ไม่ตรงกัน",
    SIGNATURE_MISSING: "คำสั่งไม่มีลายเซ็น จึงถูก EA ปฏิเสธ",
    SIGNATURE_INVALID: "ลายเซ็นคำสั่งไม่ถูกต้อง จึงถูก EA ปฏิเสธ",
    SIGNATURE_VERIFICATION_FAILED: "EA ตรวจลายเซ็นคำสั่งไม่ผ่าน",
    SIGNED_ENVELOPE_INVALID: "ซองคำสั่งที่ลงลายเซ็นมีรูปแบบไม่ถูกต้อง",
    EA_TRADING_NOT_ALLOWED: "MT4 ยังไม่อนุญาตให้ EA ส่งคำสั่ง",
    EXECUTION_UNKNOWN: "EA ยังยืนยันผลการส่งคำสั่งไม่ได้ ต้องตรวจและกู้สถานะก่อนส่งซ้ำ",
    ACK_TIMEOUT: "หมดเวลารอ ACK จาก EA",
    PREVIOUS_COMMAND_UNRESOLVED: "คำสั่งก่อนหน้ายังไม่ทราบผล ระบบไม่ส่งซ้ำ",
    DECISION_DISPATCH_WINDOW_EXPIRED: "รอบวิเคราะห์นี้เก่าเกินเวลาส่ง Order แล้ว ระบบจะรอข้อมูลแท่งใหม่และไม่ส่งคำสั่งย้อนหลัง",
    NO_TRADE: "มติ NO TRADE จึงไม่มีคำสั่งไปยัง EA",
  };
  return labels[code]
    || (code ? `ระบบป้องกันของ EA ยังไม่อนุญาตให้ส่ง Order (${code})` : "ยังไม่ได้รับสถานะจาก EA");
}

function signalExecutionGuardRecoveryLabel(value) {
  const code = String(value || "").trim().toUpperCase();
  const recovery = {
    READY: "ไม่ต้องแก้ไข EA พร้อมตรวจคำสั่งรอบใหม่",
    STARTING: "รอให้ EA เขียน Snapshot และสถานะรอบแรก แล้วกดตรวจข้อมูล MT4 ใหม่",
    TERMINAL_NOT_CONNECTED: "เข้าสู่ระบบ Broker ให้สำเร็จ และตรวจว่าราคาใน Market Watch เคลื่อนไหว",
    QUOTE_NOT_AVAILABLE: "เปิด Market Watch ให้มีราคา Bid/Ask แล้วรอ Snapshot รอบใหม่",
    QUOTE_NOT_OBSERVED: "หากตลาดปิดให้รอ Tick แรกหลังตลาดเปิด หากตลาดเปิดอยู่ให้ตรวจ Market Watch ว่าราคาเคลื่อนไหว และตรวจว่า EA อยู่บนกราฟ Symbol กับ Timeframe ที่อนุญาต แล้วรอ Snapshot รอบใหม่",
    QUOTE_STALE: "ตรวจอินเทอร์เน็ตและการเชื่อมต่อ Broker แล้วรอราคาและ Snapshot รอบใหม่",
    KILL_SWITCH_ACTIVE: "ตรวจสาเหตุที่เปิด Kill Switch ก่อน แล้วจึงปลดจาก EA เมื่อปลอดภัย",
    FIXED_LOT_CONFIGURATION_INVALID: "แก้ FixedLot ใน EA ให้มากกว่า 0 และไม่เกินเพดาน Lot ที่กำหนด",
    EA_TRADING_NOT_ALLOWED: "เปิด AutoTrading และ Allow live trading ในคุณสมบัติ EA",
    LIVE_NOT_ARMED: "เปิด LiveArmed ที่ EA เฉพาะเมื่อใช้บัญชีจริงและตรวจความเสี่ยงครบแล้ว",
    SIGNING_KEY_NOT_READY: "คัดลอก Key ID จาก Local Runner ไปใส่ TrustedSigningKeyId แล้วลาก EA ใหม่",
    LIVE_SIGNING_KEY_NOT_PINNED: "คัดลอก Key ID จาก Local Runner ไปใส่ TrustedSigningKeyId ของ EA",
    SIGNING_KEY_MISMATCH: "คัดลอก Key ID ล่าสุดจาก Local Runner ไปใส่ EA ให้ตรงกัน",
    ACK_TIMEOUT: "ตรวจแท็บ Experts และ Journal ของ MT4 ก่อนสั่งรอบใหม่",
    PREVIOUS_COMMAND_UNRESOLVED: "ตรวจ ACK หรือสถานะ Order ของคำสั่งก่อนหน้าให้จบก่อนเริ่มรอบใหม่",
  };
  return recovery[code]
    || "กดตรวจข้อมูล MT4 ใหม่ แล้วเปิดรายละเอียด EA หรือ Journal เพื่อดูสาเหตุล่าสุดก่อนเริ่มรอบใหม่";
}

function signalExecutionGuardSummary(runtime = {}) {
  if (runtime.gatewayConnected !== true) {
    return "ยังไม่เชื่อม EA • วิธีแก้: ใส่ Channel ID ให้ตรงกัน แล้วกดตรวจข้อมูล MT4 ใหม่";
  }
  if (runtime.gatewayExecutionGuardReady === true) {
    return "Execution Guard พร้อมรับคำสั่งจากรอบวิเคราะห์ใหม่";
  }
  return `${signalExecutionGuardReasonLabel(runtime.gatewayExecutionGuardReason)} • วิธีแก้: ${signalExecutionGuardRecoveryLabel(runtime.gatewayExecutionGuardReason)}`;
}

const SIGNAL_SIGNING_KEY_ID_PATTERN = /^hk-[0-9a-f]{64}$/;

function signalSigningKeyCopyState(runtime = {}) {
  const backendSigningKeyId = safeDashboardDisplayText(runtime.backendSigningKeyId, "").trim();
  const eaReportedSigningKeyId = safeDashboardDisplayText(runtime.activeSigningKeyId, "").trim();
  const backendKeyReady = SIGNAL_SIGNING_KEY_ID_PATTERN.test(backendSigningKeyId);
  const eaKeyReady = SIGNAL_SIGNING_KEY_ID_PATTERN.test(eaReportedSigningKeyId);

  if (!backendKeyReady) {
    return {
      ready: false,
      label: "Key ID จาก Backend ยังไม่พร้อม • กรุณาตรวจ Local Runner",
      copyValue: "",
    };
  }

  if (eaReportedSigningKeyId && !eaKeyReady) {
    return {
      ready: false,
      label: "Key ID ที่ EA รายงานมีรูปแบบไม่ถูกต้อง • คัดลอก Key ID จาก Backend ไปใส่ที่ EA",
      copyValue: backendSigningKeyId,
    };
  }

  if (eaKeyReady && eaReportedSigningKeyId !== backendSigningKeyId) {
    return {
      ready: false,
      label: "Key ID ของ EA ไม่ตรงกับ Backend • คัดลอก Key ID จาก Backend ไปใส่ที่ EA",
      copyValue: backendSigningKeyId,
    };
  }

  if (!eaKeyReady || runtime.signingKeyPinned !== true) {
    return {
      ready: true,
      label: "คัดลอก Key ID จาก Backend ไปใส่ที่ TrustedSigningKeyId ของ EA",
      copyValue: backendSigningKeyId,
    };
  }

  if (runtime.signingKeyMatch !== true) {
    return {
      ready: false,
      label: "EA ยังไม่ยืนยันว่า Key ID ตรงกับ Backend • คัดลอก Key ID จาก Backend ไปใส่ใหม่",
      copyValue: backendSigningKeyId,
    };
  }

  return {
    ready: true,
    label: "คัดลอก Key ID จาก Backend",
    copyValue: backendSigningKeyId,
  };
}

function renderSignalRiskList(container, runtime) {
  if (!container) return;
  const telemetry = runtime.gatewayRiskTelemetry || {};
  const currentVsMax = (current, maximum, suffix = "") => (
    current === null || maximum === null
      ? "รอข้อมูลจาก EA"
      : `${current} / ${maximum}${suffix}`
  );
  const guardReady = runtime.gatewayExecutionGuardReady === true;
  const signedCommandReady = runtime.backendSignedCommandVerificationAvailable === true
    && runtime.signedCommandVerificationAvailable === true
    && runtime.signingKeyMatch === true;
  const signedLiveReady = runtime.signedCommandRequiredForLive !== true
    || (signedCommandReady && runtime.signingKeyPinned === true);
  const signingKey = signalSigningKeyCopyState(runtime);
  const modeAccount = signalGatewayModeAccountStatus(runtime);
  const liveAccountStatus = modeAccount.mismatch
    ? modeAccount.value
    : runtime.liveOrderExecutionAvailable && guardReady
    ? "พร้อมส่ง Order บัญชีจริง"
    : !runtime.gatewayConnected
      ? "ยังไม่เชื่อม EA"
      : runtime.gatewayMode === "shadow"
        ? "ยังไม่เทรดจริง • EA อยู่ SHADOW"
        : runtime.gatewayMode === "demo"
          ? "ยังไม่เทรดจริง • EA อยู่ DEMO"
          : runtime.gatewayMode === "live" && !runtime.gatewayLiveArmed
            ? "ยังไม่เทรดจริง • ต้องเปิด LiveArmed ที่ EA"
            : runtime.gatewayMode === "live" && runtime.signingKeyPinned !== true
              ? "ยังไม่เทรดจริง • ต้องปักหมุด Trusted Signing Key ID ที่ EA"
              : runtime.gatewayMode === "live" && runtime.signingKeyMatch !== true
                ? "ยังไม่เทรดจริง • Key ID ของ EA และ Local Runner ไม่ตรงกัน"
                : !signedLiveReady
                  ? "ยังไม่เทรดจริง • ตัวตรวจลายเซ็น Live ยังไม่พร้อม"
                  : "ยังไม่พร้อม • ตรวจระบบป้องกันของ EA";
  const items = [
    ["Risk Guard ของ Mission (ไม่ร่วมโหวต)", runtime.missionRiskGuardAvailable, runtime.missionRiskGuardAvailable ? "พร้อมตรวจ Mission" : "ยังไม่พร้อม"],
    ["ข้อมูลสถานะการเทรด", runtime.tradingStateAvailable, runtime.tradingStateAvailable ? "พร้อมใช้งาน" : "รอ Adapter"],
    ["ระบบหลาย Agent", runtime.ensembleAvailable, runtime.ensembleAvailable ? "พร้อมวิเคราะห์" : "รอ Adapter"],
    ["MetafxHQ AI Council EA", runtime.gatewayConnected, runtime.gatewayConnected ? runtime.gatewayMode.toUpperCase() : "ยังไม่เชื่อม"],
    ...(modeAccount.observed
      ? [["โหมด EA / ประเภทบัญชี", modeAccount.ready, modeAccount.value]]
      : []),
    ["Execution Guard ของ EA", guardReady, signalExecutionGuardSummary(runtime)],
    ["Position ที่ EA ดูแล", telemetry.currentManagedPositions !== null, currentVsMax(telemetry.currentManagedPositions, telemetry.maxManagedPositions)],
    ["Lot รวมที่ EA ดูแล", telemetry.currentManagedLots !== null, currentVsMax(telemetry.currentManagedLots, telemetry.maxManagedLots)],
    ["รายการที่ EA ดูแลวันนี้", telemetry.currentTradesToday !== null, currentVsMax(telemetry.currentTradesToday, telemetry.maxTradesToday)],
    ["กำไร/ขาดทุนของ EA วันนี้", telemetry.managedDailyPnl !== null, telemetry.managedDailyPnl === null ? "รอข้อมูลจาก EA" : String(telemetry.managedDailyPnl)],
    ["Drawdown ของบัญชี", telemetry.currentAccountEquityDrawdownPercent !== null, currentVsMax(telemetry.currentAccountEquityDrawdownPercent, telemetry.maxAccountEquityDrawdownPercent, "%")],
    ["Margin Level", telemetry.currentMarginLevelPercent !== null, telemetry.currentMarginLevelPercent === null ? "รอข้อมูลจาก EA" : `${telemetry.currentMarginLevelPercent}%`],
    ["Kill Switch สำหรับการเทรด", runtime.tradingKillSwitchAvailable, runtime.killSwitchActive ? "กำลังหยุดระบบ" : runtime.tradingKillSwitchAvailable ? "พร้อมหยุด" : "ยังไม่เชื่อม"],
    ["ลายเซ็นคำสั่งจาก Local Runner", signedCommandReady, signedCommandReady ? `ตรวจได้ • ${runtime.signatureAlgorithm || "HMAC-SHA256"}` : "ยังตรวจแบบครบเส้นทางไม่ได้"],
    ["Key ID สำหรับตั้ง Live", signingKey.ready, signingKey.label, signingKey.copyValue],
    ["Key สำหรับบัญชีจริง", runtime.signingKeyPinned === true && runtime.signingKeyMatch === true, runtime.signingKeyPinned === true ? (runtime.signingKeyMatch === true ? "ปักหมุดแล้วและตรงกับ Backend" : "ปักหมุดแล้วแต่ Key ไม่ตรง") : "ยังไม่ปักหมุดใน EA • Live ถูกล็อก"],
    ["บัญชีจริง", runtime.liveOrderExecutionAvailable, liveAccountStatus],
  ];
  container.innerHTML = "";
  items.forEach(([label, ready, value, copyValue]) => {
    const row = document.createElement("div");
    const icon = document.createElement("span");
    const name = document.createElement("span");
    const status = document.createElement(copyValue ? "button" : "strong");
    row.className = "signal-risk-row";
    row.dataset.ready = ready ? "true" : "false";
    icon.textContent = ready ? "✓" : "○";
    name.textContent = label;
    status.textContent = value;
    if (copyValue) {
      status.type = "button";
      status.className = "signal-risk-copy";
      status.title = "คัดลอก Key ID ที่ Backend ใช้จริงไปตั้งค่าใน EA";
      status.setAttribute("aria-label", "คัดลอก Signing Key ID สำหรับตั้งค่า Live ที่ EA (ใช้ค่าจาก Backend)");
      status.addEventListener("click", async () => {
        try {
          await navigator.clipboard.writeText(copyValue);
          status.textContent = "คัดลอก Key ID จาก Backend แล้ว";
        } catch {
          status.textContent = copyValue;
          status.title = "คัดลอกอัตโนมัติไม่สำเร็จ เลือก Key ID จาก Backend ที่แสดงแล้วกด Ctrl+C";
        }
      });
    }
    row.append(icon, name, status);
    container.appendChild(row);
  });
}

function signalChartSnapshotModel(report = {}) {
  const council = signalCouncilModel(report);
  const live = council.liveAnalysis && typeof council.liveAnalysis === "object"
    ? council.liveAnalysis
    : {};
  const chartSnapshot = council.chartSnapshot && typeof council.chartSnapshot === "object"
    ? council.chartSnapshot
    : {};
  const candidates = [
    chartSnapshot.bars,
    chartSnapshot.candles,
    live?.market?.bars,
    live?.market?.candles,
  ];
  const source = candidates.find((value) => Array.isArray(value)) || [];
  const bars = source.map((bar, sourceIndex) => {
    const open = firstFiniteSignalNumber(bar?.open, bar?.o);
    const high = firstFiniteSignalNumber(bar?.high, bar?.h);
    const low = firstFiniteSignalNumber(bar?.low, bar?.l);
    const close = firstFiniteSignalNumber(bar?.close, bar?.c);
    if ([open, high, low, close].some((value) => value === null)) return null;
    if (high < low || high < open || high < close || low > open || low > close) return null;
    return {
      open,
      high,
      low,
      close,
      time: bar?.time ?? bar?.timestamp ?? bar?.observedAt ?? null,
      sourceIndex,
    };
  }).filter(Boolean);
  const suppliedTechnical = chartSnapshot.technicalIndicators
    && typeof chartSnapshot.technicalIndicators === "object"
    ? chartSnapshot.technicalIndicators
    : {};
  const rawSeries = Array.isArray(suppliedTechnical.series)
    ? suppliedTechnical.series
    : [];
  const indicatorKeys = [
    "sma20", "sma50", "sma200", "ema9", "ema20", "ema50", "ema200",
    "rsi14", "macdLine", "macdSignal", "macdHistogram", "stochasticK", "stochasticD",
    "atr14", "bollingerMiddle", "bollingerUpper", "bollingerLower", "adx14", "plusDI14",
    "minusDI14", "cci20", "williamsR14", "roc12", "momentum10", "obv", "mfi14", "volumeMA20",
  ];
  // Backend series is the exact analysis suffix of the full chart bars. Keep
  // time as the primary join key and add a deterministic suffix index fallback
  // for older adapters that omitted time from each indicator row.
  const boundedRawSeries = rawSeries.slice(-bars.length);
  const seriesSourceStart = Math.max(0, bars.length - boundedRawSeries.length);
  const indicatorSeries = boundedRawSeries.map((item, index) => {
    const matchingBar = bars[seriesSourceStart + index] || null;
    return {
      time: item?.time ?? item?.timestamp ?? matchingBar?.time ?? null,
      sourceIndex: firstFiniteSignalNumber(item?.sourceIndex, item?.index, matchingBar?.sourceIndex),
      ...Object.fromEntries(indicatorKeys.map((key) => [key, firstFiniteSignalNumber(item?.[key])])),
    };
  }).filter((item) => item.time !== null || item.sourceIndex !== null);
  const latestSeries = indicatorSeries[indicatorSeries.length - 1] || {};
  const technicalLatest = Object.fromEntries(indicatorKeys.map((key) => [
    key,
    firstFiniteSignalNumber(suppliedTechnical[key], latestSeries[key]),
  ]));
  const priceActionFeatures = chartSnapshot.priceActionFeatures
    && typeof chartSnapshot.priceActionFeatures === "object"
    ? chartSnapshot.priceActionFeatures
    : {};
  return {
    bars,
    technical: {
      available: suppliedTechnical.available === true,
      basis: safeDashboardDisplayText(suppliedTechnical.basis, ""),
      formulaVersion: safeDashboardDisplayText(suppliedTechnical.formulaVersion, ""),
      moduleCount: Number(suppliedTechnical.moduleCount || 0),
      modules: Array.isArray(suppliedTechnical.modules) ? suppliedTechnical.modules : [],
      series: indicatorSeries,
      ...technicalLatest,
    },
    priceAction: {
      available: priceActionFeatures.available === true,
      reasonCode: safeDashboardDisplayText(priceActionFeatures.reasonCode, ""),
      basis: safeDashboardDisplayText(priceActionFeatures.basis, ""),
      formulaVersion: safeDashboardDisplayText(priceActionFeatures.formulaVersion, ""),
      moduleCount: Number(priceActionFeatures.moduleCount || 0),
      modules: Array.isArray(priceActionFeatures.modules) ? priceActionFeatures.modules : [],
      barCount: Number(priceActionFeatures.barCount || 0),
      swings: priceActionFeatures.swings && typeof priceActionFeatures.swings === "object"
        ? priceActionFeatures.swings
        : {},
      supportResistance: priceActionFeatures.supportResistance
        && typeof priceActionFeatures.supportResistance === "object"
        ? priceActionFeatures.supportResistance
        : {},
      trendlines: priceActionFeatures.trendlines && typeof priceActionFeatures.trendlines === "object"
        ? priceActionFeatures.trendlines
        : {},
      fibonacci: priceActionFeatures.fibonacci && typeof priceActionFeatures.fibonacci === "object"
        ? priceActionFeatures.fibonacci
        : {},
      divergences: priceActionFeatures.divergences && typeof priceActionFeatures.divergences === "object"
        ? priceActionFeatures.divergences
        : {},
    },
  };
}

function signalDeepAnalysisPayload(payload = state.aiTradeCouncilDeepAnalysis.data) {
  if (!payload || typeof payload !== "object" || Array.isArray(payload)) return null;
  const nested = payload.deepAnalysis && typeof payload.deepAnalysis === "object"
    ? payload.deepAnalysis
    : (payload.data && typeof payload.data === "object" ? payload.data : payload);
  if (!nested || typeof nested !== "object" || Array.isArray(nested)) return null;
  const snapshot = nested.snapshot && typeof nested.snapshot === "object" && !Array.isArray(nested.snapshot)
    ? nested.snapshot
    : {};
  return {
    ...nested,
    snapshot,
    snapshotId: nested.snapshotId || snapshot.snapshotId || null,
    observedAt: nested.observedAt || snapshot.observedAt || null,
    symbol: nested.symbol || snapshot.symbol || null,
    timeframe: nested.timeframe || snapshot.timeframe || null,
  };
}

function signalDeepLiveSnapshotFallback(
  report = state.propReports[AI_TRADE_COUNCIL_PROP_ID] || {},
) {
  const council = signalCouncilModel(report);
  const chartSnapshot = council.chartSnapshot && typeof council.chartSnapshot === "object"
    && !Array.isArray(council.chartSnapshot)
    ? council.chartSnapshot
    : {};
  const bars = Array.isArray(chartSnapshot.bars)
    ? chartSnapshot.bars
    : (Array.isArray(chartSnapshot.candles) ? chartSnapshot.candles : []);
  if (chartSnapshot.available !== true || !bars.length) return null;
  const technicalIndicators = chartSnapshot.technicalIndicators
    && typeof chartSnapshot.technicalIndicators === "object"
    && !Array.isArray(chartSnapshot.technicalIndicators)
    ? chartSnapshot.technicalIndicators
    : {};
  const priceActionFeatures = chartSnapshot.priceActionFeatures
    && typeof chartSnapshot.priceActionFeatures === "object"
    && !Array.isArray(chartSnapshot.priceActionFeatures)
    ? chartSnapshot.priceActionFeatures
    : {};
  const analysisWindow = chartSnapshot.analysisWindow
    && typeof chartSnapshot.analysisWindow === "object"
    && !Array.isArray(chartSnapshot.analysisWindow)
    ? chartSnapshot.analysisWindow
    : {};
  const sourceBarCount = firstFiniteSignalNumber(chartSnapshot.sourceBarCount, bars.length) || bars.length;
  const analysisBarCount = firstFiniteSignalNumber(
    analysisWindow.usedBars,
    technicalIndicators.analysisBarCount,
    priceActionFeatures.analysisBarCount,
    bars.length,
  ) || bars.length;
  return {
    schemaVersion: "ai-trade-council-live-snapshot-display-v1",
    available: true,
    status: safeDashboardDisplayText(chartSnapshot.status, "ready"),
    reasonCode: safeDashboardDisplayText(chartSnapshot.reasonCode, "ready"),
    snapshotId: chartSnapshot.snapshotId || null,
    observedAt: chartSnapshot.observedAt || null,
    symbol: chartSnapshot.symbol || null,
    timeframe: chartSnapshot.timeframe || null,
    sourceBarCount,
    analysisBarCount,
    analysisWindow,
    bars,
    technicalIndicators,
    priceActionFeatures,
    readOnly: true,
    decisionEligible: false,
    displaySource: "live_chart_snapshot",
  };
}

function signalDeepDisplayContext(
  deepData = signalDeepAnalysisPayload(),
  report = state.propReports[AI_TRADE_COUNCIL_PROP_ID] || {},
) {
  if (deepData?.available === true) {
    return {
      data: deepData,
      deepData,
      fallback: false,
      source: "deep_analysis",
    };
  }
  const liveSnapshot = signalDeepLiveSnapshotFallback(report);
  if (liveSnapshot) {
    return {
      data: liveSnapshot,
      deepData,
      fallback: true,
      source: "live_chart_snapshot",
    };
  }
  return {
    data: deepData,
    deepData,
    fallback: false,
    source: "unavailable",
  };
}

function signalDeepSnapshotId(report = state.propReports[AI_TRADE_COUNCIL_PROP_ID] || {}) {
  const current = signalMarketModel(report).snapshotId
    || signalDailySummaryModel(report).snapshotId
    || signalDeepAnalysisPayload()?.snapshotId;
  return safeDashboardDisplayText(current, "").trim();
}

function signalDeepChartModel(data = signalDeepDisplayContext().data) {
  if (!data) return { bars: [], technical: { series: [] }, priceAction: {} };
  return signalChartSnapshotModel({
    aiTradeCouncil: {
      chartSnapshot: {
        bars: Array.isArray(data.bars) ? data.bars : [],
        technicalIndicators: data.technicalIndicators && typeof data.technicalIndicators === "object"
          ? data.technicalIndicators
          : {},
        priceActionFeatures: data.priceActionFeatures && typeof data.priceActionFeatures === "object"
          ? data.priceActionFeatures
          : {},
      },
    },
  });
}

function signalDeepPackageModel(data = signalDeepAnalysisPayload()) {
  const source = data?.package && typeof data.package === "object" && !Array.isArray(data.package)
    ? data.package
    : null;
  if (!source) return null;
  const files = Array.isArray(source.files)
    ? source.files
        .filter((item) => item && typeof item === "object")
        .map((item) => safeDashboardDisplayText(item.name, ""))
        .filter(Boolean)
        .slice(0, 12)
    : [];
  const directory = safeDashboardDisplayText(source.workspaceRelativeDirectory, "");
  return {
    available: Boolean(directory && files.length),
    status: safeDashboardDisplayText(
      source.status,
      source.created === true ? "created" : (directory && files.length ? "ready" : "not_prepared"),
    ),
    directory,
    files,
    createdAt: source.createdAt || source.updatedAt || null,
    message: safeDashboardDisplayText(source.messageTh || source.message, ""),
  };
}

function signalDeepUnavailableReasonLabel(data = signalDeepAnalysisPayload()) {
  const reasonCode = String(data?.reasonCode || data?.status || "").trim().toLowerCase();
  if (reasonCode === "minimum_500_closed_bars_required") {
    const sourceBarCount = firstFiniteSignalNumber(data?.sourceBarCount);
    return sourceBarCount === null
      ? "ข้อมูลเชิงลึกต้องใช้แท่งปิดอย่างน้อย 500 แท่ง"
      : `ข้อมูลเชิงลึกต้องใช้แท่งปิดอย่างน้อย 500 แท่ง แต่ขณะนี้ได้รับ ${sourceBarCount.toLocaleString("th-TH")} แท่ง`;
  }
  return safeDashboardDisplayText(
    data?.messageTh || data?.message || data?.reasonCode,
    "Backend ยังไม่มี Snapshot ที่พร้อมสำหรับการวิเคราะห์เชิงลึก",
  );
}

function signalDeepDataStatusMessage(context = signalDeepDisplayContext()) {
  const { data, deepData, fallback } = context;
  if (state.aiTradeCouncilDeepAnalysis.inFlight) return "กำลังอ่านข้อมูลเชิงลึกจาก Local Runner โดยยังไม่เรียก Codex";
  if (fallback) {
    const liveBars = Array.isArray(data?.bars) ? data.bars.length : 0;
    const indicatorBars = Array.isArray(data?.technicalIndicators?.series)
      ? data.technicalIndicators.series.length
      : 0;
    const deepReason = signalDeepUnavailableReasonLabel(deepData);
    return `${deepReason} • ขณะนี้แสดง Snapshot ปัจจุบัน ${liveBars.toLocaleString("th-TH")} แท่ง และ Indicator ${indicatorBars.toLocaleString("th-TH")} แท่งแทน ข้อมูลส่วนนี้ดูได้ตามจริง แต่ยังไม่ถือเป็น Deep Analysis 500 แท่ง`;
  }
  if (state.aiTradeCouncilDeepAnalysis.message) return state.aiTradeCouncilDeepAnalysis.message;
  if (!data) return "ยังไม่ได้โหลดข้อมูล กดรีเฟรชหรือเปิดแท็บนี้อีกครั้ง";
  if (data.available !== true) {
    return signalDeepUnavailableReasonLabel(data);
  }
  if (data.fresh !== true) {
    return "โหลด Snapshot เก่าสำหรับตรวจสอบได้ แต่ยังใช้เริ่มรอบวิเคราะห์ AI ใหม่ไม่ได้ กรุณารอข้อมูล MT4 ล่าสุด";
  }
  return "ข้อมูลชุดนี้มาจาก Snapshot ที่ Local Runner ยืนยันแล้ว";
}

function createSignalDeepEmptyState(message, detail = "") {
  const empty = document.createElement("section");
  const title = document.createElement("strong");
  const note = document.createElement("p");
  empty.className = "signal-deep-empty";
  title.textContent = safeDashboardDisplayText(message, "ยังไม่มีข้อมูล");
  note.textContent = safeDashboardDisplayText(detail, "Frontend จะไม่สร้างข้อมูลจำลองแทนข้อมูลจาก Backend");
  empty.append(title, note);
  return empty;
}

function renderSignalDeepPackageSummary(container, data = signalDeepAnalysisPayload()) {
  if (!container) return;
  const packageModel = signalDeepPackageModel(data);
  container.innerHTML = "";
  const label = document.createElement("span");
  const value = document.createElement("strong");
  const detail = document.createElement("small");
  label.textContent = "ไฟล์ข้อมูลสำหรับตรวจสอบ";
  value.textContent = packageModel?.available ? packageModel.directory : "ยังไม่ได้เตรียมไฟล์";
  detail.textContent = packageModel
    ? [
        packageModel.message || displayStatus(packageModel.status),
        packageModel.files.length ? `${packageModel.files.length} ไฟล์: ${packageModel.files.join(", ")}` : "",
        packageModel.createdAt ? formatThaiDateTime(packageModel.createdAt) : "",
      ].filter(Boolean).join(" • ")
    : "ปุ่มเตรียมไฟล์จะให้ Backend สร้างไฟล์ Local จาก Snapshot นี้ โดยไม่เรียก Codex และไม่หัก Rate Limit";
  container.dataset.ready = packageModel?.available ? "true" : "false";
  container.append(label, value, detail);
}

function renderSignalDeepShell(container, { eyebrow, title, description } = {}) {
  if (!container) return null;
  const context = signalDeepDisplayContext();
  const { data, deepData, fallback, source } = context;
  const snapshotId = safeDashboardDisplayText(data?.snapshotId || signalDeepSnapshotId(), "");
  const packageBusy = state.aiTradeCouncilDeepAnalysis.packageInFlight;
  const activeCouncilRound = signalCouncilRunModel(
    state.propReports[AI_TRADE_COUNCIL_PROP_ID] || {},
  ).hasActiveRound;
  const analysisBusy = state.aiTradeCouncilAnalysis.inFlight || activeCouncilRound;
  const canPreparePackage = deepData?.available === true && Boolean(snapshotId);
  const canAnalyze = canPreparePackage && deepData?.decisionEligible === true;
  container.dataset.signalDataSource = source;
  container.innerHTML = `
    <section class="signal-deep-header">
      <div class="signal-deep-heading-copy">
        <span data-signal-deep-eyebrow></span>
        <h3 data-signal-deep-title></h3>
        <p data-signal-deep-description></p>
      </div>
      <div class="signal-deep-actions" aria-label="คำสั่งข้อมูลวิเคราะห์เชิงลึก">
        <button type="button" data-signal-deep-refresh>โหลดข้อมูลล่าสุด</button>
        ${canPreparePackage ? `
          <button type="button" data-signal-deep-package ${packageBusy ? "disabled" : ""}>
            ${packageBusy ? "กำลังเตรียมไฟล์..." : "เตรียมไฟล์ Local"}
          </button>
        ` : ""}
        ${canAnalyze ? `
          <button type="button" class="primary" data-signal-deep-analyze ${analysisBusy ? "disabled" : ""}>
            ${activeCouncilRound ? "รอรอบปัจจุบันทำเสร็จ" : analysisBusy ? "กำลังส่งให้ AI..." : "ให้ AI วิเคราะห์รอบนี้"}
          </button>
        ` : ""}
      </div>
    </section>
    <div class="signal-deep-meta" data-signal-deep-meta aria-label="ขอบเขตข้อมูลจริง"></div>
    <p class="signal-deep-status" data-signal-deep-status aria-live="polite"></p>
    <div class="signal-deep-body" data-signal-deep-body></div>
    ${canPreparePackage ? '<aside class="signal-deep-package" data-signal-deep-package-summary></aside>' : ""}
  `;
  container.querySelector("[data-signal-deep-eyebrow]").textContent = eyebrow || "Deep Analysis จาก Local Runner";
  container.querySelector("[data-signal-deep-title]").textContent = title || "ข้อมูลวิเคราะห์เชิงลึก";
  container.querySelector("[data-signal-deep-description]").textContent = description || "แสดงเฉพาะข้อมูลจริงที่ Backend ส่งกลับมา";
  const status = container.querySelector("[data-signal-deep-status]");
  status.textContent = signalDeepDataStatusMessage(context);
  status.dataset.tone = fallback
    ? "warning"
    : (state.aiTradeCouncilDeepAnalysis.tone || (data?.available === true ? "success" : "neutral"));
  const meta = container.querySelector("[data-signal-deep-meta]");
  const metadata = [
    ["ระดับข้อมูล", fallback ? "Snapshot ปัจจุบัน (ยังไม่ใช่ Deep 500)" : "Deep Analysis"],
    ["สัญลักษณ์", data?.symbol || "ยังไม่มีข้อมูล"],
    ["กรอบเวลา", data?.timeframe || "ยังไม่มีข้อมูล"],
    ["ข้อมูลต้นทาง", Number.isFinite(Number(data?.sourceBarCount)) ? `${Number(data.sourceBarCount)} แท่ง` : "ยังไม่มีข้อมูล"],
    ["กรอบวิเคราะห์", Number.isFinite(Number(data?.analysisBarCount)) ? `${Number(data.analysisBarCount)} แท่ง` : "ยังไม่มีข้อมูล"],
    ["เวลาข้อมูล", data?.observedAt ? formatThaiDateTime(data.observedAt) : "ยังไม่มีข้อมูล"],
    ["Snapshot", snapshotId ? `${snapshotId.slice(0, 12)}…` : "ยังไม่มี Snapshot"],
  ];
  metadata.forEach(([name, rawValue]) => {
    const item = document.createElement("div");
    const label = document.createElement("span");
    const value = document.createElement("strong");
    label.textContent = name;
    value.textContent = safeDashboardDisplayText(rawValue, "-");
    item.append(label, value);
    meta.appendChild(item);
  });
  renderSignalDeepPackageSummary(container.querySelector("[data-signal-deep-package-summary]"), data);
  container.querySelector("[data-signal-deep-refresh]")?.addEventListener("click", () => {
    void loadSignalDeepAnalysis({ force: true });
  });
  container.querySelector("[data-signal-deep-package]")?.addEventListener("click", () => {
    void prepareSignalDeepAnalysisPackage();
  });
  container.querySelector("[data-signal-deep-analyze]")?.addEventListener("click", () => {
    void runAiTradeCouncilAnalysis(snapshotId);
  });
  return {
    body: container.querySelector("[data-signal-deep-body]"),
    data,
    deepData,
    fallback,
    source,
    snapshotId,
  };
}

async function loadSignalDeepAnalysis({ force = false } = {}) {
  if (state.aiTradeCouncilDeepAnalysis.inFlight) return null;
  const report = state.propReports[AI_TRADE_COUNCIL_PROP_ID] || {};
  const expectedSnapshotId = signalDeepSnapshotId(report);
  const requestKey = expectedSnapshotId || "latest";
  const currentData = signalDeepAnalysisPayload();
  const currentSnapshotId = safeDashboardDisplayText(currentData?.snapshotId, "");
  if (
    !force
    && currentData
    && (
      !expectedSnapshotId
      || currentSnapshotId === expectedSnapshotId
      || state.aiTradeCouncilDeepAnalysis.requestKey === requestKey
    )
  ) {
    return currentData;
  }
  state.aiTradeCouncilDeepAnalysis.inFlight = true;
  state.aiTradeCouncilDeepAnalysis.requestKey = requestKey;
  state.aiTradeCouncilDeepAnalysis.message = "กำลังโหลดข้อมูลเชิงลึกจาก Local Runner";
  state.aiTradeCouncilDeepAnalysis.tone = "working";
  renderSignalConsensusPanel(state.modal.signalTab, report);
  try {
    const response = await fetchJson(AI_TRADE_COUNCIL_DEEP_ANALYSIS_ENDPOINT, { timeoutMs: 15000 });
    const data = signalDeepAnalysisPayload(response);
    if (!data) throw new Error("รูปแบบข้อมูล Deep Analysis จาก Backend ไม่ถูกต้อง");
    const latestReport = state.propReports[AI_TRADE_COUNCIL_PROP_ID] || {};
    const latestSnapshotId = signalDeepSnapshotId(latestReport);
    if (
      requestKey !== "latest"
      && latestSnapshotId
      && latestSnapshotId !== requestKey
    ) {
      state.aiTradeCouncilDeepAnalysis.message = "Snapshot เปลี่ยนระหว่างโหลด ระบบยกเลิกผลเก่าและกำลังรอข้อมูลรอบล่าสุด";
      state.aiTradeCouncilDeepAnalysis.tone = "working";
      return null;
    }
    state.aiTradeCouncilDeepAnalysis.data = data;
    state.aiTradeCouncilDeepAnalysis.requestKey = requestKey;
    const analysisBarCount = Number(data.analysisBarCount);
    const loadedScope = Number.isFinite(analysisBarCount) && analysisBarCount > 0
      ? ` • กรอบวิเคราะห์ ${analysisBarCount.toLocaleString("th-TH")} แท่ง`
      : "";
    state.aiTradeCouncilDeepAnalysis.message = data.available === true
      ? (
          data.fresh === true
            ? `โหลดข้อมูลจริงแล้ว${loadedScope}`
            : `โหลด Snapshot เก่าสำหรับตรวจสอบแล้ว${loadedScope} • ยังไม่ใช้เริ่มรอบ AI ใหม่`
        )
      : signalDeepUnavailableReasonLabel(data);
    state.aiTradeCouncilDeepAnalysis.tone = data.available === true && data.fresh === true
      ? "success"
      : "warning";
    return data;
  } catch (error) {
    state.aiTradeCouncilDeepAnalysis.message = safeDashboardDisplayText(
      error?.body?.messageTh || error?.message,
      "โหลดข้อมูล Deep Analysis ไม่สำเร็จ กรุณาตรวจ Local Runner",
    );
    state.aiTradeCouncilDeepAnalysis.tone = "error";
    return null;
  } finally {
    state.aiTradeCouncilDeepAnalysis.inFlight = false;
    if (state.modal.open && state.modal.id === AI_TRADE_COUNCIL_PROP_ID) {
      renderSignalConsensusPanel(
        state.modal.signalTab,
        state.propReports[AI_TRADE_COUNCIL_PROP_ID] || {},
      );
    }
  }
}

async function prepareSignalDeepAnalysisPackage() {
  if (state.aiTradeCouncilDeepAnalysis.packageInFlight) return null;
  const data = signalDeepAnalysisPayload();
  const snapshotId = safeDashboardDisplayText(data?.snapshotId || signalDeepSnapshotId(), "");
  if (data?.available !== true || !snapshotId) return null;
  state.aiTradeCouncilDeepAnalysis.packageInFlight = true;
  state.aiTradeCouncilDeepAnalysis.message = "กำลังให้ Backend เตรียมไฟล์จากข้อมูลที่มีอยู่ โดยไม่เรียก Codex";
  state.aiTradeCouncilDeepAnalysis.tone = "working";
  renderSignalConsensusPanel(
    state.modal.signalTab,
    state.propReports[AI_TRADE_COUNCIL_PROP_ID] || {},
  );
  try {
    const response = await postJson(AI_TRADE_COUNCIL_DEEP_PACKAGE_ENDPOINT, {
      snapshotId,
    });
    const responseData = signalDeepAnalysisPayload(response);
    const responseHasDeepData = Boolean(
      responseData
      && (
        Array.isArray(responseData.bars)
        || responseData.technicalIndicators
        || responseData.priceActionFeatures
        || responseData.news
      )
    );
    const packageData = response?.package
      || responseData?.package
      || response?.result?.package
      || (!responseHasDeepData && response && typeof response === "object" ? response : null);
    state.aiTradeCouncilDeepAnalysis.data = {
      ...(data || {}),
      ...(responseHasDeepData ? responseData : {}),
      ...(packageData && typeof packageData === "object"
        ? { package: { ...packageData, updatedAt: packageData.updatedAt || response?.updatedAt || null } }
        : {}),
    };
    state.aiTradeCouncilDeepAnalysis.message = "Backend เตรียมไฟล์ Local แล้ว • ขั้นตอนนี้ไม่ได้เรียก Codex และไม่ใช้ Rate Limit";
    state.aiTradeCouncilDeepAnalysis.tone = "success";
    addBridgeEvent(
      "เตรียมไฟล์ Deep Analysis",
      `สร้างชุดข้อมูลของ Snapshot ${snapshotId.slice(0, 12)}… ผ่าน Local Runner โดยไม่เรียก Codex`,
    );
    return response;
  } catch (error) {
    state.aiTradeCouncilDeepAnalysis.message = safeDashboardDisplayText(
      error?.body?.messageTh || error?.message,
      "Backend ยังเตรียมไฟล์ Local ไม่สำเร็จ",
    );
    state.aiTradeCouncilDeepAnalysis.tone = "error";
    return null;
  } finally {
    state.aiTradeCouncilDeepAnalysis.packageInFlight = false;
    if (state.modal.open && state.modal.id === AI_TRADE_COUNCIL_PROP_ID) {
      renderSignalConsensusPanel(
        state.modal.signalTab,
        state.propReports[AI_TRADE_COUNCIL_PROP_ID] || {},
      );
    }
  }
}

function signalDeepFeaturePointText(value) {
  if (!value || typeof value !== "object") return "ยังไม่มีข้อมูล";
  const price = signalFeaturePrice(value);
  const parts = [
    price === null ? "" : formatSignalNumber(price),
    Number.isFinite(Number(value.touches)) ? `แตะ ${Number(value.touches)} ครั้ง` : "",
    value.time || value.lastTime ? formatBrokerBarTime(value.time || value.lastTime) : "",
  ].filter(Boolean);
  return parts.join(" • ") || "มีข้อมูลจาก Backend";
}

function appendSignalDeepFeatureCard(container, titleText, detailItems, { tone = "neutral", status = "" } = {}) {
  const card = document.createElement("article");
  const header = document.createElement("header");
  const title = document.createElement("strong");
  const badge = document.createElement("span");
  const list = document.createElement("ul");
  card.className = "signal-deep-feature-card";
  card.dataset.tone = tone;
  title.textContent = titleText;
  badge.textContent = status || (detailItems.length ? "มีข้อมูล" : "ยังไม่มีข้อมูล");
  header.append(title, badge);
  const details = detailItems.length ? detailItems : ["Backend ยังไม่ส่งข้อมูลโมดูลนี้"];
  details.slice(0, 16).forEach((detail) => {
    const row = document.createElement("li");
    row.textContent = safeDashboardDisplayText(detail, "-");
    list.appendChild(row);
  });
  card.append(header, list);
  container.appendChild(card);
  return card;
}

function signalDeepAdvancedPriceActionLines(priceAction = {}) {
  const candidates = [
    ["Market Structure", priceAction.marketStructure],
    ["Liquidity", priceAction.liquidity],
    ["Supply / Demand", priceAction.supplyDemand],
    ["Order Block", priceAction.orderBlocks],
    ["Fair Value Gap", priceAction.fairValueGaps || priceAction.fvg],
    ["SMC", priceAction.smc],
    ["HMC", priceAction.hmc],
    ["ICT", priceAction.ict],
  ];
  return candidates.flatMap(([label, value]) => {
    if (value === null || value === undefined || value === "") return [];
    if (Array.isArray(value)) return value.slice(0, 4).map((item) => `${label}: ${formatDashboardValue(item)}`);
    if (typeof value === "object") {
      return Object.entries(value).slice(0, 6).map(([key, detail]) => `${label} • ${dashboardFieldLabel(key)}: ${formatDashboardValue(detail)}`);
    }
    return [`${label}: ${String(value)}`];
  });
}

function renderSignalPriceActionDeepPanel() {
  const shell = renderSignalDeepShell(els.signalConsensusPriceActionContent, {
    eyebrow: "Price Action Deep Analysis",
    title: "กราฟเปล่าและโครงสร้างราคา",
    description: "ดูแท่งปิดจริง แนวรับ–แนวต้าน Trendline Fibonacci และโมดูล SMC/HMC/ICT ที่ Backend ส่งมาจริง",
  });
  if (!shell?.body) return;
  const { body, data, fallback } = shell;
  if (!data || data.available !== true) {
    body.appendChild(createSignalDeepEmptyState(
      "ยังไม่มีข้อมูลกราฟเชิงลึก",
      "กดโหลดข้อมูลล่าสุด หาก Backend ยังไม่พร้อม ระบบจะแสดงสถานะจริงและจะไม่สร้างเส้นหรือสัญญาณจำลอง",
    ));
    return;
  }
  const chartModel = signalDeepChartModel(data);
  const priceAction = data.priceActionFeatures && typeof data.priceActionFeatures === "object"
    ? data.priceActionFeatures
    : {};
  if (!chartModel.bars.length) {
    body.appendChild(createSignalDeepEmptyState(
      "Snapshot นี้ไม่มีแท่ง OHLC ที่ใช้วาดกราฟ",
      "ตรวจตัวอ่าน MT4 และขอบเขต analysisBarCount ที่ Backend รายงาน",
    ));
  } else {
    const chartCard = document.createElement("section");
    const heading = document.createElement("header");
    const copy = document.createElement("div");
    const title = document.createElement("strong");
    const note = document.createElement("span");
    const badge = document.createElement("b");
    const stage = document.createElement("div");
    const canvas = document.createElement("canvas");
    chartCard.className = "signal-deep-price-chart-card";
    heading.className = "signal-section-heading";
    title.textContent = `${safeDashboardDisplayText(data.symbol, "-")} / ${safeDashboardDisplayText(data.timeframe, "-")}`;
    note.textContent = fallback
      ? "กราฟจาก Snapshot ปัจจุบัน พร้อมโครงสร้างราคาที่ Backend คำนวณแล้ว • ยังไม่ใช่ Deep Analysis 500 แท่ง"
      : "กราฟเปล่าจากแท่งปิด พร้อมเส้นโครงสร้างที่ Backend คำนวณแล้ว";
    badge.textContent = `${chartModel.bars.length} แท่งที่ได้รับ`;
    copy.append(note, title);
    heading.append(copy, badge);
    stage.className = "signal-deep-price-chart-stage";
    canvas.tabIndex = 0;
    canvas.dataset.signalDeepPriceChart = "";
    canvas.setAttribute("aria-label", `กราฟเปล่า ${data.symbol || ""} ${data.timeframe || ""} จำนวน ${chartModel.bars.length} แท่ง`);
    stage.appendChild(canvas);
    chartCard.append(heading, stage);
    body.appendChild(chartCard);
    signalChartDataByCanvas.set(canvas, {
      bars: chartModel.bars,
      indicatorSeries: [],
      overlays: ["supportResistance", "trendlines", "fibonacci", "rsiDivergence", "macdDivergence"],
      priceAction: chartModel.priceAction,
    });
    window.requestAnimationFrame(() => drawSignalChartGrid(canvas));
  }

  const featureGrid = document.createElement("div");
  featureGrid.className = "signal-deep-feature-grid";
  const supports = signalFeatureItems(priceAction?.supportResistance?.supports);
  const resistances = signalFeatureItems(priceAction?.supportResistance?.resistances);
  appendSignalDeepFeatureCard(
    featureGrid,
    "แนวรับและแนวต้าน",
    [
      ...supports.slice(0, 6).map((item) => `แนวรับ ${signalDeepFeaturePointText(item)}`),
      ...resistances.slice(0, 6).map((item) => `แนวต้าน ${signalDeepFeaturePointText(item)}`),
    ],
    { tone: supports.length || resistances.length ? "ready" : "warning", status: `${supports.length} รับ • ${resistances.length} ต้าน` },
  );
  const trendlines = [priceAction?.trendlines?.support, priceAction?.trendlines?.resistance].filter(Boolean);
  appendSignalDeepFeatureCard(
    featureGrid,
    "Trendline",
    trendlines.map((line) => {
      const kind = String(line.kind || "").toLowerCase() === "resistance" ? "แนวต้าน" : "แนวรับ";
      const direction = safeDashboardDisplayText(line.direction, "ยังไม่ระบุทิศทาง");
      const projected = signalFeaturePrice(line);
      return `${kind} • ${direction}${projected === null ? "" : ` • ค่าปัจจุบัน ${formatSignalNumber(projected)}`}`;
    }),
    { tone: trendlines.length ? "ready" : "warning", status: trendlines.length ? `${trendlines.length} เส้น` : "รอ Swing" },
  );
  const fibonacciLevels = signalFeatureItems(priceAction?.fibonacci?.levels);
  appendSignalDeepFeatureCard(
    featureGrid,
    "Fibonacci",
    fibonacciLevels.map((level) => `${safeDashboardDisplayText(level.label, "ระดับ")} • ${signalDeepFeaturePointText(level)}`),
    {
      tone: priceAction?.fibonacci?.available === true ? "ready" : "warning",
      status: priceAction?.fibonacci?.available === true
        ? `${safeDashboardDisplayText(priceAction.fibonacci.direction, "")} • ${fibonacciLevels.length} ระดับ`
        : "ยังไม่มีช่วง Swing",
    },
  );
  const divergenceLines = [
    ...signalDivergenceEntries(priceAction, "rsi").map((entry) => `RSI ${entry.kind} • ${signalDeepFeaturePointText(entry.second)}`),
    ...signalDivergenceEntries(priceAction, "macd").map((entry) => `MACD ${entry.kind} • ${signalDeepFeaturePointText(entry.second)}`),
  ];
  appendSignalDeepFeatureCard(
    featureGrid,
    "Divergence",
    divergenceLines,
    { tone: divergenceLines.length ? "ready" : "neutral", status: divergenceLines.length ? `${divergenceLines.length} จุด` : "ยังไม่พบ" },
  );
  const advancedLines = signalDeepAdvancedPriceActionLines(priceAction);
  appendSignalDeepFeatureCard(
    featureGrid,
    "SMC / HMC / ICT",
    advancedLines,
    {
      tone: advancedLines.length ? "ready" : "coming-soon",
      status: advancedLines.length ? "Backend ส่งข้อมูลแล้ว" : "Coming Soon",
    },
  );
  body.appendChild(featureGrid);
}

function signalDeepRawBars(data = signalDeepDisplayContext().data) {
  return Array.isArray(data?.bars) ? data.bars.filter((item) => item && typeof item === "object") : [];
}

function signalDeepTechnicalSeries(data = signalDeepDisplayContext().data) {
  const source = data?.technicalIndicators?.series;
  return Array.isArray(source) ? source.filter((item) => item && typeof item === "object") : [];
}

function signalDeepTechnicalKeys(series = signalDeepTechnicalSeries()) {
  const excluded = new Set(["time", "timestamp", "barTime", "sourceIndex", "index", "open", "high", "low", "close", "volume", "tickVolume"]);
  const preferred = [
    "sma20", "sma50", "sma200", "ema9", "ema20", "ema50", "ema200", "rsi14",
    "atr14", "macdLine", "macdSignal", "macdHistogram", "stochasticK", "stochasticD",
    "bollingerMiddle", "bollingerUpper", "bollingerLower", "adx14", "plusDI14", "minusDI14",
    "cci20", "williamsR14", "roc12", "momentum10", "obv", "mfi14", "volumeMA20",
  ];
  const discovered = new Set();
  series.forEach((row) => {
    Object.keys(row).forEach((key) => {
      if (!excluded.has(key) && /^[A-Za-z][A-Za-z0-9_]{0,47}$/.test(key)) discovered.add(key);
    });
  });
  return [
    ...preferred.filter((key) => discovered.has(key)),
    ...[...discovered].filter((key) => !preferred.includes(key)).sort(),
  ];
}

function signalDeepTechnicalRows(data = signalDeepAnalysisPayload()) {
  const bars = signalDeepRawBars(data);
  const series = signalDeepTechnicalSeries(data);
  const byTime = new Map(series.map((row) => [String(row.time ?? row.timestamp ?? row.barTime ?? ""), row]));
  const seriesStart = Math.max(0, bars.length - series.length);
  if (bars.length) {
    return bars.map((bar, index) => {
      const time = bar.time ?? bar.timestamp ?? bar.barTime ?? null;
      const indicator = byTime.get(String(time ?? "")) || series[index - seriesStart] || {};
      return { sourceIndex: index, time, bar, indicator };
    });
  }
  return series.map((indicator, index) => ({
    sourceIndex: index,
    time: indicator.time ?? indicator.timestamp ?? indicator.barTime ?? null,
    bar: {},
    indicator,
  }));
}

function formatSignalDeepTableValue(value) {
  if (value === null || value === undefined || value === "") return "—";
  const number = Number(value);
  if (Number.isFinite(number)) {
    return number.toLocaleString("th-TH", {
      minimumFractionDigits: 0,
      maximumFractionDigits: 6,
    });
  }
  return safeDashboardDisplayText(value, "—");
}

function renderSignalTechnicalDeepPanel({ focusSearch = false } = {}) {
  const shell = renderSignalDeepShell(els.signalConsensusTechnicalContent, {
    eyebrow: "Technical Series Audit",
    title: "ตาราง Indicator ย้อนหลังแบบรายแท่ง",
    description: "ค้นหา เลือก Indicator เลือกช่วงข้อมูล และเลื่อนดูค่าที่ Backend ส่งมาจริง โดยไม่คำนวณหรือเติมข้อมูลใน Frontend",
  });
  if (!shell?.body) return;
  const { body, data, fallback } = shell;
  if (!data || data.available !== true) {
    body.appendChild(createSignalDeepEmptyState(
      "ยังไม่มีตาราง Indicator จาก Backend",
      "หาก Backend ส่งเฉพาะค่าล่าสุด ระบบจะแจ้งตามจริงและจะไม่สร้าง series ย้อนหลังขึ้นเอง",
    ));
    return;
  }
  const rows = signalDeepTechnicalRows(data);
  const series = signalDeepTechnicalSeries(data);
  const indicatorKeys = signalDeepTechnicalKeys(series);
  const selectedIndicator = state.modal.signalDeepTechnicalIndicator === "all"
    || indicatorKeys.includes(state.modal.signalDeepTechnicalIndicator)
    ? state.modal.signalDeepTechnicalIndicator
    : "all";
  state.modal.signalDeepTechnicalIndicator = selectedIndicator;
  const rangeValue = ["60", "120", "180", "300", "all"].includes(state.modal.signalDeepTechnicalRange)
    ? state.modal.signalDeepTechnicalRange
    : "300";
  const rangeCount = rangeValue === "all" ? rows.length : Number(rangeValue);
  const rangedRows = rows.slice(-Math.min(rangeCount, rows.length));
  const query = String(state.modal.signalDeepTechnicalQuery || "").trim().toLowerCase();
  const visibleIndicatorKeys = selectedIndicator === "all" ? indicatorKeys : [selectedIndicator];
  const filteredRows = rangedRows.filter((row) => {
    if (!query) return true;
    const searchable = [
      row.sourceIndex + 1,
      row.time,
      row.time ? formatBrokerBarTime(row.time, "") : "",
      row.bar?.open,
      row.bar?.high,
      row.bar?.low,
      row.bar?.close,
      row.bar?.tickVolume ?? row.bar?.volume,
      ...visibleIndicatorKeys.map((key) => row.indicator?.[key]),
    ].join(" ").toLowerCase();
    return searchable.includes(query);
  });

  const toolbar = document.createElement("section");
  const searchLabel = document.createElement("label");
  const searchCaption = document.createElement("span");
  const search = document.createElement("input");
  const indicatorLabel = document.createElement("label");
  const indicatorCaption = document.createElement("span");
  const indicator = document.createElement("select");
  const rangeLabel = document.createElement("label");
  const rangeCaption = document.createElement("span");
  const range = document.createElement("select");
  toolbar.className = "signal-deep-technical-toolbar";
  searchCaption.textContent = "ค้นหาในตาราง";
  search.type = "search";
  search.maxLength = 100;
  search.placeholder = "เวลา ราคา หรือค่า Indicator...";
  search.value = state.modal.signalDeepTechnicalQuery;
  search.dataset.signalDeepTechnicalSearch = "";
  searchLabel.append(searchCaption, search);
  indicatorCaption.textContent = "คอลัมน์ Indicator ที่แสดง";
  indicator.dataset.signalDeepTechnicalIndicator = "";
  const allOption = document.createElement("option");
  allOption.value = "all";
  allOption.textContent = `ทั้งหมด (${indicatorKeys.length})`;
  indicator.appendChild(allOption);
  indicatorKeys.forEach((key) => {
    const option = document.createElement("option");
    option.value = key;
    option.textContent = dashboardFieldLabel(key);
    indicator.appendChild(option);
  });
  indicator.value = selectedIndicator;
  indicatorLabel.append(indicatorCaption, indicator);
  rangeCaption.textContent = "ช่วงข้อมูลล่าสุด";
  range.dataset.signalDeepTechnicalRange = "";
  [["60", "60 แท่ง"], ["120", "120 แท่ง"], ["180", "180 แท่ง"], ["300", "300 แท่ง"], ["all", "ทั้งหมดที่ได้รับ"]].forEach(([value, label]) => {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = label;
    range.appendChild(option);
  });
  range.value = rangeValue;
  rangeLabel.append(rangeCaption, range);
  toolbar.append(searchLabel, indicatorLabel, rangeLabel);
  body.appendChild(toolbar);

  const scope = document.createElement("div");
  const scopeTitle = document.createElement("strong");
  const scopeDetail = document.createElement("span");
  scope.className = "signal-deep-table-scope";
  scopeTitle.textContent = `แสดง ${filteredRows.length.toLocaleString("th-TH")} แถว`;
  const analysisWindowBars = Number(data.analysisBarCount || 0);
  scopeDetail.textContent = fallback
    ? `Snapshot ปัจจุบัน: OHLC ${signalDeepRawBars(data).length} แท่ง • Indicator series ${series.length} แท่ง • รอบ AI ใช้ ${analysisWindowBars || "—"} แท่ง • ${indicatorKeys.length} ฟิลด์`
    : `OHLC ${signalDeepRawBars(data).length}/${Number(data.analysisBarCount || signalDeepRawBars(data).length)} แท่ง • Indicator series ${series.length}/${Number(data.analysisBarCount || rows.length)} แท่ง • ${indicatorKeys.length} ฟิลด์`;
  scope.append(scopeTitle, scopeDetail);
  body.appendChild(scope);

  if (!rows.length || !series.length || !indicatorKeys.length) {
    body.appendChild(createSignalDeepEmptyState(
      "Backend ยังไม่ส่ง Indicator series รายแท่ง",
      data.technicalIndicators
        ? "พบข้อมูลสรุป Technical แต่ยังไม่มี series สำหรับสร้างตารางย้อนหลัง"
        : "Snapshot นี้ยังไม่มี technicalIndicators",
    ));
  } else if (!filteredRows.length) {
    body.appendChild(createSignalDeepEmptyState("ไม่พบแถวที่ตรงกับคำค้นหา", "ลองล้างคำค้นหาหรือเลือกช่วงข้อมูลที่กว้างขึ้น"));
  } else {
    const viewport = document.createElement("div");
    const table = document.createElement("table");
    const head = document.createElement("thead");
    const headRow = document.createElement("tr");
    const tableBody = document.createElement("tbody");
    const baseColumns = [
      ["index", "ลำดับ"],
      ["time", "เวลาแท่งปิด"],
      ["open", "Open"],
      ["high", "High"],
      ["low", "Low"],
      ["close", "Close"],
      ["volume", "Tick Volume"],
    ];
    const columns = [
      ...baseColumns,
      ...visibleIndicatorKeys.map((key) => [key, dashboardFieldLabel(key)]),
    ];
    viewport.className = "signal-deep-table-viewport";
    viewport.tabIndex = 0;
    viewport.setAttribute("aria-label", "ตาราง Indicator ย้อนหลัง เลื่อนได้ทั้งแนวนอนและแนวตั้ง");
    table.style.minWidth = `${Math.max(900, columns.length * 112)}px`;
    columns.forEach(([, label]) => {
      const cell = document.createElement("th");
      cell.scope = "col";
      cell.textContent = label;
      headRow.appendChild(cell);
    });
    filteredRows.forEach((row) => {
      const tr = document.createElement("tr");
      const values = {
        ...row.indicator,
        index: row.sourceIndex + 1,
        time: row.time ? formatBrokerBarTime(row.time) : "—",
        open: row.bar?.open,
        high: row.bar?.high,
        low: row.bar?.low,
        close: row.bar?.close,
        volume: row.bar?.tickVolume ?? row.bar?.volume,
      };
      columns.forEach(([key]) => {
        const cell = document.createElement("td");
        cell.textContent = formatSignalDeepTableValue(values[key]);
        tr.appendChild(cell);
      });
      tableBody.appendChild(tr);
    });
    head.appendChild(headRow);
    table.append(head, tableBody);
    viewport.appendChild(table);
    body.appendChild(viewport);
  }

  search.addEventListener("input", () => {
    state.modal.signalDeepTechnicalQuery = search.value;
    renderSignalTechnicalDeepPanel({ focusSearch: true });
    saveSessionSnapshot();
  });
  indicator.addEventListener("change", () => {
    state.modal.signalDeepTechnicalIndicator = indicator.value;
    renderSignalTechnicalDeepPanel();
    saveSessionSnapshot();
  });
  range.addEventListener("change", () => {
    state.modal.signalDeepTechnicalRange = range.value;
    renderSignalTechnicalDeepPanel();
    saveSessionSnapshot();
  });
  if (focusSearch) {
    const refreshed = els.signalConsensusTechnicalContent?.querySelector("[data-signal-deep-technical-search]");
    refreshed?.focus();
    refreshed?.setSelectionRange(refreshed.value.length, refreshed.value.length);
  }
}

function signalDeepNewsHorizon(news = {}, horizon = "short") {
  const keyMap = {
    short: ["shortTerm", "short_term", "short", "ระยะสั้น"],
    medium: ["mediumTerm", "medium_term", "medium", "midTerm", "ระยะกลาง"],
    long: ["longTerm", "long_term", "long", "ระยะยาว"],
  };
  const containers = [news.horizons, news.outlook, news.context, news];
  for (const container of containers) {
    if (!container || typeof container !== "object") continue;
    for (const key of keyMap[horizon]) {
      const value = container[key];
      if (Array.isArray(value)) return { items: value, supplied: true };
      if (value && typeof value === "object") {
        const items = Array.isArray(value.items) ? value.items : [value];
        return { items, supplied: true };
      }
      if (typeof value === "string" && value.trim()) return { items: [{ summary: value }], supplied: true };
    }
  }
  return { items: [], supplied: false };
}

function signalDeepDirection(value) {
  const normalized = String(value || "").trim().toUpperCase();
  if (["BUY", "BULLISH", "UP", "POSITIVE"].includes(normalized)) return { label: "ขาขึ้น / BUY", tone: "buy" };
  if (["SELL", "BEARISH", "DOWN", "NEGATIVE"].includes(normalized)) return { label: "ขาลง / SELL", tone: "sell" };
  if (["HOLD", "NEUTRAL", "MIXED", "NO_TRADE", "NO TRADE"].includes(normalized)) return { label: "เป็นกลาง / HOLD", tone: "hold" };
  return { label: "ยังไม่ระบุทิศทาง", tone: "neutral" };
}

function signalDeepEvidenceItems(value) {
  if (!value) return [];
  const items = Array.isArray(value) ? value : [value];
  return items
    .map((item) => (typeof item === "string" && item.trim() ? { label: item.trim() } : item))
    .filter((item) => item && typeof item === "object")
    .slice(0, 30);
}

function appendSignalDeepEvidenceList(container, evidence) {
  const items = signalDeepEvidenceItems(evidence);
  if (!items.length) return false;
  const list = document.createElement("ul");
  list.className = "signal-deep-news-evidence";
  items.forEach((item) => {
    const rawUrl = String(item.sourceUrl || item.url || item.link || "").trim();
    let parsed = null;
    try {
      parsed = rawUrl ? new URL(rawUrl) : null;
    } catch {
      parsed = null;
    }
    if (parsed && (!["http:", "https:"].includes(parsed.protocol) || parsed.username || parsed.password)) parsed = null;
    const row = document.createElement("li");
    const label = safeDashboardDisplayText(item.label || item.title || item.name, parsed?.hostname || "หลักฐานจาก Backend");
    const note = document.createElement("span");
    note.textContent = safeDashboardDisplayText(item.note || item.summary || item.detail || item.observedAt, "");
    if (parsed) {
      const link = document.createElement("a");
      link.href = parsed.href;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      link.textContent = label;
      row.append(link, note);
    } else {
      const title = document.createElement("strong");
      title.textContent = label;
      row.append(title, note);
    }
    list.appendChild(row);
  });
  container.appendChild(list);
  return true;
}

function renderSignalNewsHorizonCard(container, news, horizon, label) {
  const model = signalDeepNewsHorizon(news, horizon);
  const card = document.createElement("article");
  const header = document.createElement("header");
  const heading = document.createElement("div");
  const eyebrow = document.createElement("span");
  const title = document.createElement("strong");
  const first = model.items[0] && typeof model.items[0] === "object" ? model.items[0] : {};
  const direction = signalDeepDirection(first.direction || first.decision || first.bias);
  const badge = document.createElement("b");
  const confidence = firstFiniteSignalNumber(first.confidence, first.confidencePercent);
  card.className = "signal-deep-news-card";
  card.dataset.tone = direction.tone;
  eyebrow.textContent = label;
  title.textContent = direction.label;
  badge.textContent = confidence === null ? "ยังไม่มี Confidence" : `Confidence ${Math.round(clamp(confidence, 0, 100))}%`;
  heading.append(eyebrow, title);
  header.append(heading, badge);
  card.appendChild(header);
  if (!model.supplied || !model.items.length) {
    card.appendChild(createSignalDeepEmptyState(
      `ยังไม่มีข่าว${label}`,
      "Backend ยังไม่ส่งบทวิเคราะห์ในช่วงเวลานี้ จึงไม่แสดงทิศทางแทน",
    ));
  } else {
    model.items.slice(0, 8).forEach((item) => {
      const section = document.createElement("section");
      const itemTitle = document.createElement("strong");
      const summary = document.createElement("p");
      itemTitle.textContent = safeDashboardDisplayText(item.title || item.label, "สรุปบริบทตลาด");
      summary.textContent = safeDashboardDisplayText(
        item.summary || item.detail || item.reason || item.outlook || item.message,
        "Backend ยังไม่ได้ส่งข้อความสรุป",
      );
      section.append(itemTitle, summary);
      appendSignalDeepEvidenceList(section, item.evidence || item.sources);
      card.appendChild(section);
    });
  }
  container.appendChild(card);
}

function renderSignalLatestNewsVote(container, news = {}) {
  if (!container || news.available !== true || !news.decision) return false;
  const card = document.createElement("article");
  const header = document.createElement("header");
  const heading = document.createElement("div");
  const eyebrow = document.createElement("span");
  const title = document.createElement("strong");
  const badge = document.createElement("b");
  const direction = signalDeepDirection(news.decision);
  const confidence = firstFiniteSignalNumber(news.confidence);
  card.className = "signal-deep-news-card signal-deep-news-latest";
  card.dataset.tone = direction.tone;
  eyebrow.textContent = "ผลข่าวล่าสุดที่ Backend บันทึก";
  title.textContent = direction.label;
  badge.textContent = confidence === null
    ? "ยังไม่มี Confidence"
    : `Confidence ${Math.round(clamp(confidence, 0, 100))}%`;
  heading.append(eyebrow, title);
  header.append(heading, badge);
  card.appendChild(header);

  const status = document.createElement("p");
  const horizonBars = firstFiniteSignalNumber(news.horizonBars);
  const statusParts = [
    news.usableForCurrentSnapshot === true
      ? "ตรงกับ Snapshot ปัจจุบัน"
      : "เป็นผลจาก Snapshot อื่น จึงใช้ดูบริบทเท่านั้น",
    horizonBars === null ? "" : `ขอบเขต ${horizonBars} แท่ง`,
    news.sourceUpdatedAt ? `อัปเดต ${formatThaiDateTime(news.sourceUpdatedAt)}` : "",
  ].filter(Boolean);
  status.className = "signal-deep-news-snapshot-status";
  status.dataset.current = news.usableForCurrentSnapshot === true ? "true" : "false";
  status.textContent = statusParts.join(" • ");
  card.appendChild(status);

  const groups = [
    ["ข้อสังเกต", news.observations],
    ["ข้อควรระวัง", news.warnings],
  ];
  groups.forEach(([label, values]) => {
    const items = Array.isArray(values) ? values.filter((item) => String(item || "").trim()) : [];
    if (!items.length) return;
    const section = document.createElement("section");
    const sectionTitle = document.createElement("strong");
    const list = document.createElement("ul");
    sectionTitle.textContent = label;
    items.slice(0, 8).forEach((item) => {
      const row = document.createElement("li");
      row.textContent = safeDashboardDisplayText(item, "-");
      list.appendChild(row);
    });
    section.append(sectionTitle, list);
    card.appendChild(section);
  });
  appendSignalDeepEvidenceList(card, news.evidence);
  container.appendChild(card);
  return true;
}

function renderSignalNewsContextPanel() {
  const shell = renderSignalDeepShell(els.signalConsensusNewsContent, {
    eyebrow: "News & Market Context",
    title: "ข่าวและสถานการณ์ระยะสั้น กลาง และยาว",
    description: "แสดงทิศทาง Confidence และลิงก์หลักฐานที่ Backend ส่งมาเท่านั้น หากไม่มีข่าวจะไม่แต่งข้อมูลขึ้นเอง",
  });
  if (!shell?.body) return;
  const { body, data } = shell;
  if (!data || data.available !== true) {
    body.appendChild(createSignalDeepEmptyState(
      "ยังไม่มีข้อมูลข่าวสำหรับ Snapshot นี้",
      "กดโหลดข้อมูลล่าสุด หาก Backend ยังไม่เชื่อมแหล่งข่าว ระบบจะแสดง Coming Soon หรือเหตุผลที่ได้รับจริง",
    ));
    return;
  }
  const news = data.news && typeof data.news === "object" && !Array.isArray(data.news)
    ? data.news
    : {};
  const latest = document.createElement("div");
  latest.className = "signal-deep-news-latest-wrap";
  if (renderSignalLatestNewsVote(latest, news)) {
    body.appendChild(latest);
  }
  const grid = document.createElement("div");
  grid.className = "signal-deep-news-grid";
  renderSignalNewsHorizonCard(grid, news, "short", "ระยะสั้น");
  renderSignalNewsHorizonCard(grid, news, "medium", "ระยะกลาง");
  renderSignalNewsHorizonCard(grid, news, "long", "ระยะยาว");
  body.appendChild(grid);
  const globalEvidence = signalDeepEvidenceItems(news.evidence || news.sources);
  if (globalEvidence.length) {
    const sourceSection = document.createElement("section");
    const title = document.createElement("h4");
    sourceSection.className = "signal-deep-global-sources";
    title.textContent = "แหล่งข้อมูลรวมที่ Backend ยืนยัน";
    sourceSection.appendChild(title);
    appendSignalDeepEvidenceList(sourceSection, globalEvidence);
    body.appendChild(sourceSection);
  } else if (news.available !== true && !Object.keys(news).length) {
    body.appendChild(createSignalDeepEmptyState(
      "โมดูลข่าวยังไม่ส่งข้อมูล",
      "Coming Soon — ต้องเชื่อม Backend กับแหล่งข่าวจริงก่อนจึงจะแสดง Direction, Confidence และ Source Link",
    ));
  } else if (news.available !== true) {
    body.appendChild(createSignalDeepEmptyState(
      "ยังไม่มีผลข่าวที่ใช้กับ Snapshot นี้",
      safeDashboardDisplayText(news.reasonCode || news.status, "Backend ยังไม่ส่งผลวิเคราะห์ข่าว"),
    ));
  }
}

function signalChartBars(report = {}, displayBars = state.modal.signalChartDisplayBars, offsetBars = state.modal.signalChartOffsetBars) {
  const source = signalChartSnapshotModel(report).bars;
  const count = normalizeSignalDisplayBars(displayBars);
  const maximumOffset = Math.max(0, source.length - Math.min(count, source.length));
  const offset = Math.min(maximumOffset, Math.max(0, Math.floor(Number(offsetBars) || 0)));
  const end = Math.max(0, source.length - offset);
  return source.slice(Math.max(0, end - count), end);
}

function signalChartOverlayIds(value = state.modal.signalChartOverlays) {
  const known = new Set(SIGNAL_CHART_OVERLAY_DEFINITIONS.map((definition) => definition.id));
  return [...new Set(Array.isArray(value) ? value : SIGNAL_CHART_DEFAULT_OVERLAYS)]
    .filter((id) => known.has(id))
    .slice(0, SIGNAL_CHART_OVERLAY_LIMIT);
}

function signalFeaturePrice(value) {
  if (typeof value === "number") return Number.isFinite(value) ? value : null;
  if (!value || typeof value !== "object") return null;
  return firstFiniteSignalNumber(value.price, value.value, value.level, value.projectedPrice);
}

function signalFeatureItems(value) {
  if (Array.isArray(value)) return value;
  if (value && typeof value === "object") return [value];
  return [];
}

function signalDivergenceEntries(priceAction = {}, oscillator = "rsi") {
  const source = priceAction?.divergences?.[oscillator] || {};
  return [source?.bullish, source?.bearish]
    .flatMap((value) => signalFeatureItems(value))
    .filter((entry) => (
      entry
      && ["REGULAR_BULLISH", "REGULAR_BEARISH"].includes(String(entry.kind || "").toUpperCase())
      && signalFeaturePrice(entry.first) !== null
      && signalFeaturePrice(entry.second) !== null
    ));
}

function signalPriceActionModuleReady(priceAction = {}, feature = "") {
  const calculationFinished = priceAction?.available === true && Number(priceAction?.barCount || 0) > 0;
  if (feature === "swings") {
    return calculationFinished || signalFeatureItems(priceAction?.swings?.highs).length > 0
      || signalFeatureItems(priceAction?.swings?.lows).length > 0;
  }
  if (feature === "supportResistance") {
    return calculationFinished || signalFeatureItems(priceAction?.supportResistance?.supports).length > 0
      || signalFeatureItems(priceAction?.supportResistance?.resistances).length > 0;
  }
  if (feature === "trendlines") {
    return calculationFinished || Boolean(priceAction?.trendlines?.support || priceAction?.trendlines?.resistance);
  }
  if (feature === "fibonacci") {
    return calculationFinished || (priceAction?.fibonacci?.available === true
      && signalFeatureItems(priceAction?.fibonacci?.levels).length > 0);
  }
  if (feature === "rsiDivergence") return calculationFinished || signalDivergenceEntries(priceAction, "rsi").length > 0;
  if (feature === "macdDivergence") return calculationFinished || signalDivergenceEntries(priceAction, "macd").length > 0;
  return false;
}

function signalCore20ModuleDetail(module, chartModel) {
  if (module.group === "technical") {
    const values = module.keys
      .map((key) => chartModel.technical[key])
      .filter((value) => Number.isFinite(value));
    if (!values.length) return "รอข้อมูลจากแท่งปิด";
    return values.slice(0, 3).map((value) => formatSignalNumber(value)).join(" • ");
  }
  const priceAction = chartModel.priceAction;
  if (module.feature === "swings") {
    const highCount = signalFeatureItems(priceAction?.swings?.highs).length;
    const lowCount = signalFeatureItems(priceAction?.swings?.lows).length;
    return highCount || lowCount ? `จุดสูง ${highCount} • จุดต่ำ ${lowCount}` : "รอจุดกลับตัวที่ยืนยันแล้ว";
  }
  if (module.feature === "supportResistance") {
    const supportCount = signalFeatureItems(priceAction?.supportResistance?.supports).length;
    const resistanceCount = signalFeatureItems(priceAction?.supportResistance?.resistances).length;
    return supportCount || resistanceCount
      ? `แนวรับ ${supportCount} • แนวต้าน ${resistanceCount}`
      : "รอระดับราคาที่ผ่านการยืนยัน";
  }
  if (module.feature === "trendlines") {
    const count = [priceAction?.trendlines?.support, priceAction?.trendlines?.resistance].filter(Boolean).length;
    return count ? `พบ ${count} เส้นที่ยืนยันแล้ว` : "รอ Swing สำหรับสร้างเส้น";
  }
  if (module.feature === "fibonacci") {
    const levels = signalFeatureItems(priceAction?.fibonacci?.levels).length;
    return levels ? `${priceAction.fibonacci.direction === "DOWN" ? "ขาลง" : "ขาขึ้น"} • ${levels} ระดับ` : "รอช่วง Swing ที่สมบูรณ์";
  }
  if (module.feature === "rsiDivergence") {
    const count = signalDivergenceEntries(priceAction, "rsi").length;
    return count ? `พบ Regular Divergence ${count} จุด` : "ยังไม่พบ Divergence ที่ยืนยันแล้ว";
  }
  if (module.feature === "macdDivergence") {
    const count = signalDivergenceEntries(priceAction, "macd").length;
    return count ? `พบ Regular Divergence ${count} จุด` : "ยังไม่พบ Divergence ที่ยืนยันแล้ว";
  }
  return "รอข้อมูล";
}

function signalCore20CardsHtml(chartModel, filter = "all", snapshotFresh = true) {
  const modules = SIGNAL_CORE20_MODULES.filter((module) => filter === "all" || module.group === filter);
  return modules.map((module) => {
    const ready = module.group === "technical"
      ? module.keys.some((key) => Number.isFinite(chartModel.technical[key]))
      : signalPriceActionModuleReady(chartModel.priceAction, module.feature);
    return `
      <article class="signal-core20-card" data-group="${module.group}" data-ready="${ready}" data-fresh="${snapshotFresh}">
        <span>${module.group === "technical" ? "Technical" : "Price Action"}</span>
        <strong>${module.label}</strong>
        <small>${signalCore20ModuleDetail(module, chartModel)}</small>
        <em>${ready ? (snapshotFresh ? "พร้อมอ่าน" : "ข้อมูลเก่า") : "รอข้อมูล"}</em>
      </article>
    `;
  }).join("");
}

function drawSignalChartGrid(canvas) {
  if (!(canvas instanceof HTMLCanvasElement)) return;
  const rect = canvas.getBoundingClientRect();
  if (!rect.width || !rect.height) return;
  const ratio = Math.min(window.devicePixelRatio || 1, 2);
  canvas.width = Math.round(rect.width * ratio);
  canvas.height = Math.round(rect.height * ratio);
  const context = canvas.getContext("2d");
  if (!context) return;
  context.scale(ratio, ratio);
  context.fillStyle = "#020b12";
  context.fillRect(0, 0, rect.width, rect.height);
  context.strokeStyle = "rgba(56, 133, 166, 0.15)";
  context.lineWidth = 1;
  for (let x = 0; x <= rect.width; x += Math.max(56, rect.width / 12)) {
    context.beginPath();
    context.moveTo(x, 0);
    context.lineTo(x, rect.height);
    context.stroke();
  }
  for (let y = 0; y <= rect.height; y += Math.max(42, rect.height / 8)) {
    context.beginPath();
    context.moveTo(0, y);
    context.lineTo(rect.width, y);
    context.stroke();
  }
  context.strokeStyle = "rgba(39, 212, 255, 0.28)";
  context.beginPath();
  context.moveTo(0, rect.height / 2);
  context.lineTo(rect.width, rect.height / 2);
  context.stroke();

  const chartData = signalChartDataByCanvas.get(canvas) || {};
  const bars = Array.isArray(chartData) ? chartData : (chartData.bars || []);
  if (bars.length < 2) return;
  const series = Array.isArray(chartData.indicatorSeries) ? chartData.indicatorSeries : [];
  const seriesByTime = new Map(series.map((item) => [String(item.time), item]));
  const seriesBySourceIndex = new Map(
    series
      .filter((item) => Number.isFinite(item.sourceIndex))
      .map((item) => [item.sourceIndex, item]),
  );
  const seriesForBar = (bar) => (
    seriesByTime.get(String(bar.time))
    || seriesBySourceIndex.get(bar.sourceIndex)
    || null
  );
  const selectedOverlays = signalChartOverlayIds(chartData.overlays);
  const overlayDefinition = (id) => SIGNAL_CHART_OVERLAY_DEFINITIONS.find((item) => item.id === id);
  const seriesOverlayKeys = selectedOverlays.flatMap((id) => {
    if (["ema20", "ema50", "ema200", "sma20", "sma50", "sma200"].includes(id)) {
      return [{ key: id, color: overlayDefinition(id)?.color || "#d9f4ff", group: id }];
    }
    if (id === "bollinger") {
      return [
        { key: "bollingerUpper", color: "#65a9ff", group: id },
        { key: "bollingerMiddle", color: "rgba(101, 169, 255, 0.72)", group: id },
        { key: "bollingerLower", color: "#65a9ff", group: id },
      ];
    }
    return [];
  });
  const overlays = seriesOverlayKeys.map((overlay) => ({
    ...overlay,
    points: bars.map((bar, index) => ({
      index,
      value: firstFiniteSignalNumber(seriesForBar(bar)?.[overlay.key]),
    })).filter((point) => point.value !== null),
  }));
  const priceAction = chartData.priceAction || {};
  const supportLevels = selectedOverlays.includes("supportResistance")
    ? signalFeatureItems(priceAction?.supportResistance?.supports)
      .map((item) => signalFeaturePrice(item)).filter((value) => value !== null)
    : [];
  const resistanceLevels = selectedOverlays.includes("supportResistance")
    ? signalFeatureItems(priceAction?.supportResistance?.resistances)
      .map((item) => signalFeaturePrice(item)).filter((value) => value !== null)
    : [];
  const fibonacciLevels = selectedOverlays.includes("fibonacci") && priceAction?.fibonacci?.available === true
    ? signalFeatureItems(priceAction?.fibonacci?.levels)
      .map((item) => ({ price: signalFeaturePrice(item), label: safeDashboardDisplayText(item?.label, "Fibo") }))
      .filter((item) => item.price !== null)
    : [];
  const trendlines = selectedOverlays.includes("trendlines")
    ? [priceAction?.trendlines?.support, priceAction?.trendlines?.resistance].filter(Boolean)
    : [];
  const divergences = [
    ...(selectedOverlays.includes("rsiDivergence") ? signalDivergenceEntries(priceAction, "rsi") : []),
    ...(selectedOverlays.includes("macdDivergence") ? signalDivergenceEntries(priceAction, "macd") : []),
  ];
  const padding = { top: 18, right: 54, bottom: 22, left: 12 };
  const plotWidth = Math.max(1, rect.width - padding.left - padding.right);
  const plotHeight = Math.max(1, rect.height - padding.top - padding.bottom);
  const overlayValues = overlays.flatMap((overlay) => overlay.points.map((point) => point.value));
  const structuralValues = [
    ...supportLevels,
    ...resistanceLevels,
    ...fibonacciLevels.map((item) => item.price),
    ...trendlines.flatMap((line) => [signalFeaturePrice(line?.first), signalFeaturePrice(line?.second), signalFeaturePrice(line)]),
    ...divergences.flatMap((entry) => [signalFeaturePrice(entry?.first), signalFeaturePrice(entry?.second)]),
  ].filter((value) => value !== null);
  const highest = Math.max(...bars.map((bar) => bar.high), ...overlayValues, ...structuralValues);
  const lowest = Math.min(...bars.map((bar) => bar.low), ...overlayValues, ...structuralValues);
  const range = Math.max(highest - lowest, Math.abs(highest) * 0.00001, 0.00001);
  const priceY = (price) => padding.top + ((highest - price) / range) * plotHeight;
  const slot = plotWidth / bars.length;
  const bodyWidth = Math.max(0.45, Math.min(10, slot * 0.64));
  const pointIndex = (point) => {
    if (!point || typeof point !== "object") return null;
    const pointTime = point.time ?? point.timestamp ?? point.confirmedAtTime;
    if (pointTime !== null && pointTime !== undefined) {
      const matchedIndex = bars.findIndex((bar) => String(bar.time) === String(pointTime));
      if (matchedIndex >= 0) return matchedIndex;
    }
    const sourceIndex = firstFiniteSignalNumber(point.index, point.barIndex);
    if (sourceIndex !== null) {
      const matchedIndex = bars.findIndex((bar) => bar.sourceIndex === sourceIndex);
      if (matchedIndex >= 0) return matchedIndex;
    }
    return null;
  };
  const indexX = (index) => padding.left + slot * index + slot / 2;

  const drawHorizontalLevel = (price, color, label, dash = [5, 4]) => {
    if (!Number.isFinite(price)) return;
    const y = priceY(price);
    context.save();
    context.strokeStyle = color;
    context.fillStyle = color;
    context.lineWidth = 1;
    context.setLineDash(dash);
    context.beginPath();
    context.moveTo(padding.left, y);
    context.lineTo(rect.width - padding.right, y);
    context.stroke();
    context.setLineDash([]);
    context.font = "9px system-ui, sans-serif";
    context.textAlign = "left";
    context.fillText(label, padding.left + 4, Math.max(padding.top + 10, y - 3));
    context.restore();
  };

  supportLevels.slice(-3).forEach((price) => drawHorizontalLevel(price, "rgba(36, 231, 154, 0.82)", "แนวรับ"));
  resistanceLevels.slice(-3).forEach((price) => drawHorizontalLevel(price, "rgba(255, 82, 111, 0.82)", "แนวต้าน"));
  fibonacciLevels.forEach((level) => drawHorizontalLevel(level.price, "rgba(217, 140, 255, 0.58)", level.label, [3, 5]));

  bars.forEach((bar, index) => {
    const x = indexX(index);
    const bullish = bar.close >= bar.open;
    const color = bullish ? "#24e79a" : "#ff526f";
    context.strokeStyle = color;
    context.fillStyle = color;
    context.lineWidth = Math.max(0.55, bodyWidth * 0.16);
    context.beginPath();
    context.moveTo(x, priceY(bar.high));
    context.lineTo(x, priceY(bar.low));
    context.stroke();
    const bodyTop = Math.min(priceY(bar.open), priceY(bar.close));
    const bodyHeight = Math.max(1.5, Math.abs(priceY(bar.open) - priceY(bar.close)));
    context.globalAlpha = bullish ? 0.82 : 0.9;
    context.fillRect(x - bodyWidth / 2, bodyTop, bodyWidth, bodyHeight);
    context.globalAlpha = 1;
  });

  overlays.forEach((overlay) => {
    if (overlay.points.length < 2) return;
    context.save();
    context.strokeStyle = overlay.color;
    context.lineWidth = 1.8;
    context.shadowBlur = 7;
    context.shadowColor = overlay.color;
    context.beginPath();
    overlay.points.forEach((point, pointIndex) => {
      const x = indexX(point.index);
      const y = priceY(point.value);
      if (pointIndex === 0) context.moveTo(x, y);
      else context.lineTo(x, y);
    });
    context.stroke();
    context.restore();
  });

  trendlines.forEach((line) => {
    const firstIndex = pointIndex(line?.first);
    const secondIndex = pointIndex(line?.second);
    const firstPrice = signalFeaturePrice(line?.first);
    const secondPrice = signalFeaturePrice(line?.second);
    if ([firstIndex, secondIndex, firstPrice, secondPrice].some((value) => value === null)) return;
    const color = line.kind === "resistance" ? "#ffca58" : "#5ae89c";
    context.save();
    context.strokeStyle = color;
    context.lineWidth = 1.6;
    context.beginPath();
    context.moveTo(indexX(firstIndex), priceY(firstPrice));
    context.lineTo(indexX(secondIndex), priceY(secondPrice));
    if (Number.isFinite(Number(line.projectedPrice))) {
      context.lineTo(rect.width - padding.right, priceY(Number(line.projectedPrice)));
    }
    context.stroke();
    context.restore();
  });

  divergences.forEach((entry) => {
    const firstIndex = pointIndex(entry?.first);
    const secondIndex = pointIndex(entry?.second);
    const firstPrice = signalFeaturePrice(entry?.first);
    const secondPrice = signalFeaturePrice(entry?.second);
    if ([firstIndex, secondIndex, firstPrice, secondPrice].some((value) => value === null)) return;
    const bullish = String(entry.kind).toUpperCase() === "REGULAR_BULLISH";
    const isRsi = String(entry.oscillator).toUpperCase().includes("RSI");
    const color = isRsi ? "#55e0ff" : "#ff7ca5";
    context.save();
    context.strokeStyle = color;
    context.fillStyle = color;
    context.lineWidth = 2;
    context.setLineDash([5, 3]);
    context.beginPath();
    context.moveTo(indexX(firstIndex), priceY(firstPrice));
    context.lineTo(indexX(secondIndex), priceY(secondPrice));
    context.stroke();
    context.setLineDash([]);
    const markerY = priceY(secondPrice) + (bullish ? 14 : -9);
    context.font = "bold 9px system-ui, sans-serif";
    context.textAlign = "center";
    context.fillText(`${isRsi ? "RSI" : "MACD"} ${bullish ? "ขาขึ้น" : "ขาลง"}`, indexX(secondIndex), markerY);
    context.restore();
  });

  context.fillStyle = "rgba(217, 244, 255, 0.72)";
  context.font = "11px system-ui, sans-serif";
  context.textAlign = "right";
  context.fillText(highest.toFixed(highest >= 100 ? 2 : 5), rect.width - 6, padding.top + 4);
  context.fillText(lowest.toFixed(lowest >= 100 ? 2 : 5), rect.width - 6, rect.height - padding.bottom);
}

function renderSignalLivePanel(report = {}) {
  const container = els.signalConsensusLiveOverviewContent;
  if (!container) return;
  const runtime = getSignalRuntimeTruth(report);
  const market = signalMarketModel(report);
  const views = signalAgentViews(report, runtime);
  const consensus = signalConsensusModel(report, runtime);
  const consensusPolicy = signalCouncilConsensusPolicyModel(report);
  const policyBusy = state.aiTradeCouncilConsensusPolicy.inFlight
    || state.aiTradeCouncilAutomation.inFlight;
  const policyMessage = state.aiTradeCouncilConsensusPolicy.message
    || `เกณฑ์นี้ใช้กับรอบวิเคราะห์ถัดไป • ผลโหวตเก่าจะไม่ถูกนำกลับมาส่ง Order`;
  container.innerHTML = `
    <div class="signal-market-strip" data-signal-market-strip></div>
    <div class="signal-live-layout signal-council-overview-layout">
      <main class="signal-live-main signal-council-overview-main">
        <section class="signal-council-overview" aria-labelledby="signalCouncilOverviewTitle">
          <header class="signal-council-overview-heading">
            <div>
              <span>ผู้เชี่ยวชาญสภา AI</span>
              <h3 id="signalCouncilOverviewTitle">ภาพรวมการวิเคราะห์ของ Agent 3 ตัว</h3>
              <p>แต่ละตัวใช้ข้อมูลจริงจาก Local Runner ในบทบาทของตนเอง และส่งผลโหวตกลับมารวมด้านขวา</p>
            </div>
            <span class="signal-state-badge ${market.available ? "ready" : "warning"}">
              ${market.available ? "Snapshot พร้อมวิเคราะห์" : "รอ Snapshot จาก Backend"}
            </span>
          </header>
          <div
            class="signal-agent-grid signal-council-overview-grid"
            data-signal-agent-grid
            aria-label="ผู้เชี่ยวชาญสภา AI 3 ตัว"
          ></div>
        </section>
      </main>
      <aside class="signal-consensus-rail signal-council-overview-rail" aria-label="ผลลงคะแนนและ Risk EA Gate">
        <section class="signal-council-card signal-vote-summary-card">
          <h4>สรุปคะแนนจากผู้เชี่ยวชาญ 3 ตัว</h4>
          <small class="signal-current-vote-rule">รอบนี้ใช้เกณฑ์ ${consensus.requiredVotes} ใน 3</small>
          <div class="signal-vote-grid" data-signal-votes></div>
          <div class="signal-final-decision">
            <span>มติของสภารอบล่าสุด</span>
            <strong data-signal-final-decision>NO TRADE</strong>
            <p data-signal-final-reason></p>
            <div class="signal-trade-plan" data-signal-trade-plan hidden>
              <span><small>Stop Loss</small><strong data-signal-plan-sl>—</strong></span>
              <span><small>Take Profit</small><strong data-signal-plan-tp>—</strong></span>
              <span><small>Lot</small><strong>ใช้ค่าจาก EA</strong></span>
            </div>
            <div class="signal-protective-plan-provenance" data-signal-plan-provenance data-state="unavailable">
              <span>ที่มา SL/TP</span>
              <strong data-signal-plan-source>ยังไม่มีแผน SL/TP</strong>
              <small data-signal-plan-source-detail>รอผลยืนยันจาก Backend</small>
            </div>
            <small data-signal-consensus-snapshot></small>
          </div>
        </section>
        <section class="signal-council-card signal-consensus-policy-card" aria-labelledby="signalConsensusPolicyTitle">
          <div class="signal-consensus-policy-heading">
            <div>
              <span>จำนวนเสียงที่ใช้เปิด Order</span>
              <h4 id="signalConsensusPolicyTitle">เลือกว่าจะเชื่อผลโหวตกี่ตัว</h4>
            </div>
            <span class="signal-state-badge ${policyBusy ? "working" : "ready"}">
              ${policyBusy ? "กำลังบันทึก" : `${consensusPolicy.requiredVotes} ใน 3`}
            </span>
          </div>
          <div
            class="signal-vote-threshold-options"
            role="radiogroup"
            aria-label="จำนวนเสียงขั้นต่ำที่ใช้เปิด Order"
          >
            ${[1, 2, 3].map((value) => `
              <button
                type="button"
                role="radio"
                aria-checked="${consensusPolicy.requiredVotes === value ? "true" : "false"}"
                data-signal-required-votes="${value}"
                ${policyBusy ? "disabled" : ""}
              >
                <strong>${value}</strong>
                <span>ใน 3</span>
              </button>
            `).join("")}
          </div>
          <p class="signal-consensus-policy-rule">${consensusPolicy.ruleText}</p>
          <div class="signal-direction-conflict-rule">
            <strong>กติกาป้องกันความเห็นขัดกัน</strong>
            <span>ถ้ามีทั้ง BUY และ SELL ในรอบเดียวกัน ระบบจะ NO TRADE เสมอ</span>
          </div>
          <small class="signal-consensus-gate-note">
            จำนวนเสียงไม่ข้าม SL/TP, Council Quality Gate, Risk Guard หรือ EA Gate
          </small>
          <small
            class="signal-consensus-policy-status"
            data-signal-consensus-policy-status
            data-tone="${state.aiTradeCouncilConsensusPolicy.tone}"
            aria-live="polite"
          ></small>
        </section>
        <section class="signal-council-card signal-risk-gate-card">
          <h4>Risk / EA Gate</h4>
          <p class="signal-gate-note">Risk Guard ไม่ร่วมโหวต และสถานะพร้อมเทรดต้องยืนยันจาก EA</p>
          <div class="signal-risk-list" data-signal-risk-list></div>
        </section>
        <section class="signal-council-card signal-order-card">
          <h4>MetafxHQ AI Council EA</h4>
          <button type="button" disabled data-signal-gateway-action>รอเชื่อม EA</button>
          <p data-signal-gateway-detail>Fixed Lot และโหมด Shadow / Demo / Live ตั้งค่าที่ EA เท่านั้น</p>
        </section>
      </aside>
    </div>
  `;
  renderSignalMarketStrip(container.querySelector("[data-signal-market-strip]"), report, runtime);
  const agentGrid = container.querySelector("[data-signal-agent-grid]");
  views.forEach((view) => agentGrid?.appendChild(createSignalCouncilOverviewCard(view)));
  renderSignalVoteSummary(container.querySelector("[data-signal-votes]"), consensus);
  const decision = container.querySelector("[data-signal-final-decision]");
  const reason = container.querySelector("[data-signal-final-reason]");
  const consensusSnapshot = container.querySelector("[data-signal-consensus-snapshot]");
  if (decision) {
    decision.textContent = consensus.decision;
    decision.dataset.decision = String(consensus.decision || "no_trade")
      .toLowerCase()
      .replace(/\s+/g, "_");
  }
  if (reason) reason.textContent = consensus.reason;
  const tradePlan = container.querySelector("[data-signal-trade-plan]");
  if (tradePlan) tradePlan.hidden = !consensus.tradePlan.available;
  const planSl = container.querySelector("[data-signal-plan-sl]");
  const planTp = container.querySelector("[data-signal-plan-tp]");
  if (planSl) planSl.textContent = consensus.tradePlan.stopLossPrice === null
    ? "—"
    : formatSignalNumber(consensus.tradePlan.stopLossPrice);
  if (planTp) planTp.textContent = consensus.tradePlan.takeProfitPrice === null
    ? "—"
    : formatSignalNumber(consensus.tradePlan.takeProfitPrice);
  renderSignalProtectivePlanProvenance(
    container.querySelector("[data-signal-plan-provenance]"),
    consensus,
  );
  if (consensusSnapshot) {
    consensusSnapshot.textContent = signalSnapshotComparisonText(
      consensus.snapshotId,
      consensus.currentSnapshotId || market.snapshotId,
    );
    consensusSnapshot.dataset.current = consensus.matchesCurrentSnapshot ? "true" : "false";
  }
  renderSignalRiskList(container.querySelector("[data-signal-risk-list]"), runtime);
  const policyStatus = container.querySelector("[data-signal-consensus-policy-status]");
  if (policyStatus) policyStatus.textContent = policyMessage;
  container.querySelectorAll("[data-signal-required-votes]").forEach((button) => {
    button.addEventListener("click", () => {
      void setAiTradeCouncilRequiredVotes(button.dataset.signalRequiredVotes);
    });
  });
  const gatewayAction = container.querySelector("[data-signal-gateway-action]");
  const gatewayDetail = container.querySelector("[data-signal-gateway-detail]");
  if (gatewayAction) {
    gatewayAction.textContent = runtime.gatewayExecutionGuardReady
      ? `พร้อมรับคำสั่งรอบใหม่ • ${runtime.gatewayMode.toUpperCase()}`
      : runtime.gatewayConnected
        ? `เชื่อม EA แล้ว • ยังไม่พร้อมส่ง Order`
        : "ยังไม่เชื่อม EA";
    gatewayAction.dataset.ready = runtime.gatewayExecutionGuardReady ? "true" : "false";
  }
  if (gatewayDetail) {
    const fixedLot = runtime.gatewayFixedLot === null
      ? "Fixed Lot ตั้งค่าที่ EA"
      : `Fixed Lot ${runtime.gatewayFixedLot}`;
    const ackStatus = safeDashboardDisplayText(runtime.gatewayLastAck?.status, "ยังไม่มี ACK");
    const modeAccount = signalGatewayModeAccountStatus(runtime);
    gatewayDetail.textContent = `${fixedLot} • ${signalExecutionGuardSummary(runtime)} • ${ackStatus}${modeAccount.mismatch ? ` • ${modeAccount.value}` : ""}`;
  }
}

function renderSignalPipelineSteps(container, states) {
  if (!container) return;
  const steps = [
    ["1", "รับ Snapshot", states.snapshot],
    ["2", "Specialist ลงคะแนน 3 ตัว", states.agents],
    ["3", "รวมคะแนน", states.consensus],
    ["4", "Council Quality Gate", states.quality],
    ["5", "Risk / EA Gate", states.riskEa],
    ["6", "ส่ง Command และรอ ACK", states.command === "complete" ? states.ack : states.command],
    ["7", "ตรวจ Fill / Recovery", states.fill],
  ];
  container.innerHTML = "";
  steps.forEach(([number, label, stateName]) => {
    const item = document.createElement("div");
    const badge = document.createElement("span");
    const text = document.createElement("strong");
    item.className = "signal-pipeline-step";
    item.dataset.state = stateName;
    badge.textContent = number;
    text.textContent = label;
    item.append(badge, text);
    container.appendChild(item);
  });
}

function renderSignalDecisionPanel(report = {}) {
  const container = els.signalConsensusDecisionContent;
  if (!container) return;
  const council = signalCouncilModel(report);
  const pipeline = council.decisionPipeline || {};
  const runtime = getSignalRuntimeTruth(report);
  const market = signalMarketModel(report);
  const views = signalAgentViews(report, runtime);
  const consensus = signalConsensusModel(report, runtime);
  const run = consensus.run || signalCouncilRunModel(report);
  const currentSnapshotId = safeDashboardDisplayText(
    market.snapshotId || pipeline?.snapshot?.currentId,
    "",
  );
  const analyzedSnapshotId = safeDashboardDisplayText(
    run.snapshotId || consensus.snapshotId || pipeline?.snapshot?.id,
    "",
  );
  const snapshotAvailable = Boolean(analyzedSnapshotId)
    && (pipeline?.snapshot?.available === true || Boolean(run.parent));
  const availableAgentCount = views.filter((view) => view.available).length;
  const agentsAvailable = availableAgentCount === AI_TRADE_COUNCIL_AGENT_IDS.length;
  const consensusAvailable = agentsAvailable && consensus.available;
  const riskGuard = consensus.riskGuard || pipeline?.consensus?.riskGuard || {};
  const readOnlyPolicyPassed = consensusAvailable
    && riskGuard.voting === false
    && riskGuard.terminalActions === false
    && ["passed_read_only_policy", "ready"].includes(String(riskGuard.status || ""));
  const runBlocked = run.state === "blocked" || run.counts.blocked > 0;
  const runActive = run.state === "running" || run.counts.running > 0;
  const allRunAgentsCompleted = run.children.length === AI_TRADE_COUNCIL_AGENT_IDS.length
    && run.counts.completed === AI_TRADE_COUNCIL_AGENT_IDS.length;
  const gatewayRun = consensus.tradeGateway || {};
  const gatewayAckStatus = String(
    gatewayRun.ackStatus || gatewayRun?.command?.ack?.status || "",
  ).toUpperCase();
  const gatewayRunStatus = String(gatewayRun.status || "");
  const gatewayRunBlocked = gatewayRunStatus === "blocked";
  const quality = signalCouncilQualityModel(report, consensus, market);
  const operations = signalTradeOperationsModel(report, runtime, consensus);
  const automation = signalCouncilAutomationModel(report);
  const roundHealth = signalRoundHealthModel(report, automation, run);
  const agentsState = agentsAvailable || allRunAgentsCompleted
    ? "complete"
    : runBlocked
      ? "blocked"
      : runActive
        ? "waiting"
        : snapshotAvailable
          ? "waiting"
          : "idle";
  const consensusState = consensusAvailable
    ? "complete"
    : runBlocked
      ? "blocked"
      : runActive || agentsState === "complete"
        ? "waiting"
        : "idle";
  const noTradeRound = consensusAvailable && !consensus.tradePlan.available;
  const riskEaState = noTradeRound
    ? "skipped"
    : consensus.tradePlan.available
      ? runtime.gatewayExecutionGuardReady
        ? "complete"
        : gatewayRunBlocked || runtime.killSwitchActive
          ? "blocked"
          : "waiting"
      : consensusAvailable || runActive
        ? "waiting"
        : "unavailable";
  const states = {
    snapshot: snapshotAvailable ? "complete" : (runtime.terminalSelected ? "waiting" : "blocked"),
    agents: agentsState,
    consensus: consensusState,
    quality: quality.state,
    riskEa: riskEaState,
    command: operations.commandState,
    ack: operations.ackState,
    fill: operations.fillState,
  };
  const gatewayStatusLabel = gatewayAckStatus === "EXECUTED"
    ? "EA ยืนยัน Order แล้ว"
    : gatewayAckStatus === "SHADOWED"
      ? "Shadow ตรวจคำสั่งผ่าน"
      : gatewayRun.commandPublished === true
        ? `ส่งคำสั่งแล้ว • รอ ACK`
        : gatewayRunStatus === "waiting_previous_ack"
          ? "รอ EA ตอบรับคำสั่งก่อนหน้า"
        : consensus.tradePlan.available && runtime.gatewayModeAccountMismatch
          ? signalExecutionGuardReasonLabel(runtime.gatewayModeAccountMismatchReason)
        : consensus.tradePlan.available
          && ["demo", "live"].includes(runtime.gatewayMode)
          && !runtime.gatewayExecutionGuardReady
          ? `ยังไม่ส่ง Order • ${signalExecutionGuardReasonLabel(runtime.gatewayExecutionGuardReason)}`
        : consensus.tradePlan.available && runtime.gatewayConnected
          ? `Execution Guard พร้อม • ${runtime.gatewayMode.toUpperCase()}`
    : consensus.tradePlan.available
      ? "รอเชื่อม MetafxHQ AI Council EA"
      : readOnlyPolicyPassed
        ? "มติ NO TRADE • ไม่ส่งคำสั่ง"
    : riskEaState === "blocked"
      ? "หยุดแบบปลอดภัย"
      : "กำลังตรวจผลวิเคราะห์";
  const runDecision = consensus.belongsToLatestRun
    ? consensus.decision
    : runBlocked
      ? "ติดขัด"
      : runActive
        ? "กำลังวิเคราะห์"
        : "ยังไม่มีมติรอบนี้";
  const runDecisionReason = consensus.belongsToLatestRun
    ? consensus.reason
    : run.reason;
  container.innerHTML = `
    <div class="signal-market-strip" data-signal-market-strip></div>
    <div class="signal-pipeline" data-signal-pipeline aria-label="เจ็ดขั้นตอนตั้งแต่รับข้อมูลจนตรวจสถานะคำสั่ง"></div>
    <section class="signal-run-summary" data-signal-run-summary data-state="idle">
      <div>
        <span>รอบวิเคราะห์ล่าสุด</span>
        <strong data-signal-run-title>ยังไม่มี Mission วิเคราะห์</strong>
      </div>
      <span class="signal-run-status" data-signal-run-status>ยังไม่เริ่ม</span>
      <p data-signal-run-reason>ยังไม่มีรายละเอียดจาก Backend</p>
      <small data-signal-run-meta></small>
      <button type="button" data-signal-run-detail hidden>ดูรายละเอียด Mission</button>
    </section>
    <div class="signal-decision-layout">
      <section class="signal-snapshot-card">
        <div class="signal-snapshot-status">สถานะ Snapshot</div>
        <h4>ข้อมูลรอบวิเคราะห์</h4>
        <strong data-signal-snapshot-id>ยังไม่มี Snapshot</strong>
        <p data-signal-snapshot-note></p>
      </section>
      <section class="signal-decision-agents">
        <h4>คะแนนจาก Specialist 3 ตัว</h4>
        <div data-signal-decision-agents></div>
      </section>
      <section class="signal-decision-consensus">
        <h4>สรุปผลโหวต (ไม่ใช่การอนุมัติ)</h4>
        <div class="signal-vote-grid" data-signal-votes></div>
        <div class="signal-final-decision">
          <span>มติของระบบ • เหตุผล NO TRADE/Trade แสดงด้านล่าง</span>
          <strong data-signal-final-decision>NO TRADE</strong>
          <p data-signal-final-reason></p>
          <div class="signal-trade-plan" data-signal-trade-plan hidden>
            <span><small>Stop Loss</small><strong data-signal-plan-sl>—</strong></span>
            <span><small>Take Profit</small><strong data-signal-plan-tp>—</strong></span>
            <span><small>Lot</small><strong>ใช้ค่าจาก EA</strong></span>
          </div>
          <div class="signal-protective-plan-provenance" data-signal-plan-provenance data-state="unavailable">
            <span>ที่มา SL/TP</span>
            <strong data-signal-plan-source>ยังไม่มีแผน SL/TP</strong>
            <small data-signal-plan-source-detail>รอผลยืนยันจาก Backend</small>
          </div>
          <small data-signal-consensus-snapshot></small>
        </div>
      </section>
      <section class="signal-decision-risk">
        <h4>Risk / EA Gate</h4>
        <p class="signal-gate-note">Risk Guard ไม่ร่วมโหวต หน้าที่คือเช็กข้อจำกัด Mission และสถานะป้องกันจาก EA ก่อนส่งคำสั่ง</p>
        <div class="signal-risk-list" data-signal-risk-list></div>
        <button type="button" disabled>${gatewayStatusLabel}</button>
      </section>
    </div>
    <section class="signal-assurance-grid" aria-label="จุดตรวจคุณภาพและสถานะการส่งคำสั่ง">
      <article class="signal-assurance-card" data-signal-quality-card data-state="unavailable">
        <header>
          <div><span>Gate ก่อนเทรด</span><strong>Council Quality Gate</strong></div>
          <b data-signal-quality-status>รอ Backend</b>
        </header>
        <p data-signal-quality-reason></p>
        <div class="signal-assurance-list" data-signal-quality-rows></div>
      </article>
      <article class="signal-assurance-card" data-state="neutral">
        <header>
          <div><span>สุขภาพของรอบ</span><strong>Lag • Deadline • Quota</strong></div>
          <b>${automation.statusLabel}</b>
        </header>
        <p>ตัวเลขทั้งหมดอ่านจาก Mission, นโยบาย และ Rate Limit ที่ Backend ส่งมา หากไม่มีข้อมูลจะแสดงว่าไม่พร้อมแทนการประมาณเอง</p>
        <div class="signal-assurance-list" data-signal-round-health></div>
      </article>
      <article class="signal-assurance-card" data-signal-operations-card data-state="unavailable">
        <header>
          <div><span>วงจรคำสั่ง</span><strong>Command • ACK • Fill • Recovery</strong></div>
          <b data-signal-operations-status>ยังไม่มีคำสั่ง</b>
        </header>
        <p>ACK EXECUTED ไม่ถูกตีความเป็น Fill ที่ตรวจแล้ว จนกว่า Backend จะส่งหลักฐาน Fill แยกต่างหาก</p>
        <div class="signal-assurance-list" data-signal-operation-rows></div>
      </article>
    </section>
    <section class="signal-timeline">
      <div class="signal-section-heading">
        <div><span>เหตุการณ์ของรอบนี้</span><strong>Decision Trail จาก Backend</strong></div>
      </div>
      <div data-signal-timeline></div>
    </section>
  `;
  renderSignalMarketStrip(container.querySelector("[data-signal-market-strip]"), report, runtime);
  renderSignalPipelineSteps(container.querySelector("[data-signal-pipeline]"), states);
  const qualityCard = container.querySelector("[data-signal-quality-card]");
  const qualityStatus = container.querySelector("[data-signal-quality-status]");
  const qualityReason = container.querySelector("[data-signal-quality-reason]");
  if (qualityCard) qualityCard.dataset.state = quality.state;
  if (qualityStatus) qualityStatus.textContent = quality.statusLabel;
  if (qualityReason) qualityReason.textContent = quality.reason;
  renderSignalAssuranceRows(container.querySelector("[data-signal-quality-rows]"), quality.rows);
  renderSignalAssuranceRows(container.querySelector("[data-signal-round-health]"), roundHealth.rows);
  const operationsCard = container.querySelector("[data-signal-operations-card]");
  const operationsStatus = container.querySelector("[data-signal-operations-status]");
  if (operationsCard) operationsCard.dataset.state = operations.incident
    ? "blocked"
    : operations.fillState === "complete"
      ? "complete"
      : operations.commandState === "skipped"
        ? "skipped"
        : operations.commandState;
  if (operationsStatus) operationsStatus.textContent = operations.incident
    ? "มี Incident ต้องตรวจ"
    : operations.fillState === "complete"
      ? "ยืนยัน Fill แล้ว"
      : operations.commandState === "skipped"
        ? "ข้ามเพราะ NO TRADE"
        : operations.commandState === "complete"
          ? "ส่ง Command แล้ว"
          : "ยังไม่มีคำสั่ง";
  renderSignalAssuranceRows(container.querySelector("[data-signal-operation-rows]"), operations.rows);
  const runSummary = container.querySelector("[data-signal-run-summary]");
  const runTitle = container.querySelector("[data-signal-run-title]");
  const runStatus = container.querySelector("[data-signal-run-status]");
  const runReason = container.querySelector("[data-signal-run-reason]");
  const runMeta = container.querySelector("[data-signal-run-meta]");
  const runDetail = container.querySelector("[data-signal-run-detail]");
  if (runSummary) runSummary.dataset.state = run.state || "idle";
  if (runTitle) runTitle.textContent = safeDashboardDisplayText(
    run.parent?.title,
    "ยังไม่มี Mission วิเคราะห์",
  );
  if (runStatus) runStatus.textContent = run.parent ? run.statusLabel : "ยังไม่เริ่ม";
  if (runReason) runReason.textContent = run.reason;
  if (runMeta) {
    const counts = run.parent
      ? `Specialist สำเร็จ ${run.counts.completed} • กำลังทำ ${run.counts.running} • ติดขัด ${run.counts.blocked}`
      : "ยังไม่มีงานของ Specialist ในรอบนี้";
    runMeta.textContent = `${counts} • ${signalSnapshotComparisonText(analyzedSnapshotId, currentSnapshotId)}`;
  }
  if (runDetail && run.parent?.id && state.missions.some((mission) => mission.id === run.parent.id)) {
    runDetail.hidden = false;
    runDetail.addEventListener("click", () => {
      openTaskDetail(run.parent.id, runDetail, { source: "signal-council" });
    });
  }
  const snapshotId = container.querySelector("[data-signal-snapshot-id]");
  const snapshotNote = container.querySelector("[data-signal-snapshot-note]");
  if (snapshotId) snapshotId.textContent = signalSnapshotLabel(analyzedSnapshotId);
  if (snapshotNote) snapshotNote.textContent = signalSnapshotComparisonText(
    analyzedSnapshotId,
    currentSnapshotId,
  );
  const agents = container.querySelector("[data-signal-decision-agents]");
  views.forEach((view) => agents?.appendChild(createSignalAgentCard(view, { compact: true })));
  renderSignalVoteSummary(container.querySelector("[data-signal-votes]"), consensus);
  const decision = container.querySelector("[data-signal-final-decision]");
  const reason = container.querySelector("[data-signal-final-reason]");
  const consensusSnapshot = container.querySelector("[data-signal-consensus-snapshot]");
  if (decision) decision.textContent = runDecision;
  if (reason) reason.textContent = runDecisionReason;
  const tradePlan = container.querySelector("[data-signal-trade-plan]");
  if (tradePlan) tradePlan.hidden = !consensus.tradePlan.available;
  const planSl = container.querySelector("[data-signal-plan-sl]");
  const planTp = container.querySelector("[data-signal-plan-tp]");
  if (planSl) planSl.textContent = consensus.tradePlan.stopLossPrice === null
    ? "—"
    : formatSignalNumber(consensus.tradePlan.stopLossPrice);
  if (planTp) planTp.textContent = consensus.tradePlan.takeProfitPrice === null
    ? "—"
    : formatSignalNumber(consensus.tradePlan.takeProfitPrice);
  renderSignalProtectivePlanProvenance(
    container.querySelector("[data-signal-plan-provenance]"),
    consensus,
  );
  if (consensusSnapshot) {
    consensusSnapshot.textContent = signalSnapshotComparisonText(
      consensus.snapshotId,
      consensus.currentSnapshotId || currentSnapshotId,
    );
    consensusSnapshot.dataset.current = consensus.matchesCurrentSnapshot ? "true" : "false";
  }
  renderSignalRiskList(container.querySelector("[data-signal-risk-list]"), runtime);
  const timeline = container.querySelector("[data-signal-timeline]");
  const events = run.parent
    ? [run.parent, ...run.children]
    : (Array.isArray(pipeline.events) && pipeline.events.length
      ? pipeline.events
      : (Array.isArray(pipeline.items) ? pipeline.items : []));
  if (!events.length) {
    const empty = document.createElement("div");
    empty.className = "signal-empty-state";
    empty.textContent = "ยังไม่มี Decision Trail จริงจาก Backend";
    timeline?.appendChild(empty);
  } else {
    events.slice(0, 8).forEach((event, index) => {
      const item = document.createElement("div");
      const step = document.createElement("span");
      const copy = document.createElement("div");
      const title = document.createElement("strong");
      const detail = document.createElement("small");
      item.className = "signal-timeline-item";
      item.dataset.state = signalMissionUiState(event);
      step.textContent = String(index + 1);
      title.textContent = safeDashboardDisplayText(event.title, `เหตุการณ์ ${index + 1}`);
      detail.textContent = `${signalMissionStatusLabel(event)} • ${signalMissionReason(
        event,
        safeDashboardDisplayText(event.detail || event.summary, "ยังไม่มีรายละเอียด"),
      )} • ${formatThaiDateTime(event.updatedAt || event.createdAt)}`;
      copy.append(title, detail);
      item.append(step, copy);
      timeline?.appendChild(item);
    });
  }
}

function signalHistoryEntries(report = {}) {
  const council = signalCouncilModel(report);
  const pipeline = council.decisionPipeline && typeof council.decisionPipeline === "object"
    ? council.decisionPipeline
    : {};
  const suppliedReports = Array.isArray(council?.history?.items)
    ? council.history.items
    : (Array.isArray(report?.reports) ? report.reports : []);
  const suppliedMissions = Array.isArray(pipeline.items)
    ? pipeline.items
    : (Array.isArray(report?.missions) ? report.missions : []);
  const normalizedReports = suppliedReports.map((entry) => {
      const rawKind = String(entry?.kind || entry?.itemType || "").toLowerCase();
      const item = entry?.item || entry?.report || entry?.mission || entry;
      const kind = rawKind === "mission" || entry?.mission ? "mission" : "report";
      return { kind, item };
    });
  const normalizedMissions = suppliedMissions.map((entry) => ({
    kind: "mission",
    item: entry?.item || entry?.mission || entry,
  }));
  const seen = new Set();
  return [...normalizedMissions, ...normalizedReports].filter((entry) => {
    const identity = safeDashboardDisplayText(
      entry.item?.id || entry.item?.missionId || entry.item?.reportId,
      `${entry.item?.title || ""}:${entry.item?.createdAt || entry.item?.updatedAt || ""}`,
    );
    const key = `${entry.kind}:${identity}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

function signalHistoryStatusBucket(entry) {
  const workState = getDashboardWorkState(entry.item, entry.kind);
  return workState === "running" ? "active" : workState === "completed" ? "completed" : "blocked";
}

function signalHistoryTypeLabel(entry) {
  if (entry.kind === "mission") return "Mission";
  const reportType = String(entry.item?.reportType || entry.item?.type || "");
  if (reportType === "auto_trading_status_report") return "ผลวิเคราะห์ AI";
  if (reportType === "terminal_discovery_report") return "ตรวจหา MT4/MT5";
  if (reportType === "terminal_selection_report") return "เลือก Terminal";
  if (reportType === "dashboard_connection_report") return "ตรวจการเชื่อมต่อ";
  return "รายงาน";
}

function openSignalHistoryEntry(entry, trigger) {
  if (entry.kind === "mission") {
    const missionId = entry.item?.id;
    if (missionId && state.missions.some((mission) => mission.id === missionId)) {
      openTaskDetail(missionId, trigger, { source: "signal-history" });
      return;
    }
  }
  openDashboardResultDetail(entry.item, trigger);
}

function createSignalHistoryRow(entry) {
  const item = entry.item || {};
  const row = document.createElement("button");
  const time = document.createElement("span");
  const type = document.createElement("span");
  const title = document.createElement("strong");
  const status = document.createElement("span");
  const result = document.createElement("span");
  const detail = document.createElement("span");
  const bucket = signalHistoryStatusBucket(entry);
  row.type = "button";
  row.className = "signal-history-row";
  row.dataset.status = bucket;
  row.setAttribute("aria-label", `เปิดรายละเอียด ${safeDashboardDisplayText(item.title, signalHistoryTypeLabel(entry))}`);
  time.textContent = formatThaiDateTime(item.updatedAt || item.completedAt || item.createdAt);
  type.textContent = signalHistoryTypeLabel(entry);
  title.textContent = safeDashboardDisplayText(item.title, item.id || "รายการจาก Backend");
  status.textContent = displayStatus(item.status || bucket);
  result.textContent = safeDashboardDisplayText(item.result || item.summary || item.detail, "ยังไม่มีข้อความสรุป");
  detail.textContent = "ดูรายละเอียด";
  row.append(time, type, title, status, result, detail);
  row.addEventListener("click", () => openSignalHistoryEntry(entry, row));
  return row;
}

function renderSignalHistoryPanel(report = {}, { focusSearch = false } = {}) {
  const container = els.signalConsensusHistoryContent;
  if (!container) return;
  const council = signalCouncilModel(report);
  const allEntries = signalHistoryEntries(report);
  const query = String(state.modal.signalHistoryQuery || "").trim().toLowerCase();
  const filtered = allEntries.filter((entry) => {
    if (state.modal.signalHistoryType !== "all" && entry.kind !== state.modal.signalHistoryType) return false;
    if (state.modal.signalHistoryStatus !== "all" && signalHistoryStatusBucket(entry) !== state.modal.signalHistoryStatus) return false;
    if (!query) return true;
    const item = entry.item || {};
    return [
      item.id,
      item.title,
      item.summary,
      item.detail,
      item.result,
      item.status,
      item.ownerAgentId,
      item.owner,
      signalHistoryTypeLabel(entry),
    ].join(" ").toLowerCase().includes(query);
  });
  const completed = allEntries.filter((entry) => signalHistoryStatusBucket(entry) === "completed").length;
  const blocked = allEntries.filter((entry) => signalHistoryStatusBucket(entry) === "blocked").length;
  const active = allEntries.filter((entry) => signalHistoryStatusBucket(entry) === "active").length;
  container.innerHTML = `
    <div class="signal-history-heading">
      <div>
        <span>ประวัติจาก Local Runner</span>
        <h3>ประวัติการวิเคราะห์และ Task ล่าสุด</h3>
        <p>แสดง Mission และ Report ล่าสุดที่ผูกกับสภา AI Trade จริง ไม่รวม Memory หรือบทสนทนาทั่วไป</p>
      </div>
      <small data-signal-history-count></small>
    </div>
    <div class="signal-history-toolbar">
      <label>
        <span>ค้นหา</span>
        <input type="search" data-signal-history-search maxlength="160" placeholder="ค้นหา Mission, Report หรือสถานะ..." />
      </label>
      <label>
        <span>ประเภท</span>
        <select data-signal-history-type>
          <option value="all">ทั้งหมด</option>
          <option value="mission">Mission</option>
          <option value="report">Report</option>
        </select>
      </label>
      <label>
        <span>สถานะ</span>
        <select data-signal-history-status>
          <option value="all">ทั้งหมด</option>
          <option value="active">กำลังดำเนินการ</option>
          <option value="completed">สำเร็จ</option>
          <option value="blocked">ติดขัด</option>
        </select>
      </label>
    </div>
    <div class="signal-history-summary" aria-label="สรุปประวัติ">
      <div><span>รายการล่าสุด</span><strong data-signal-history-total></strong></div>
      <div><span>กำลังดำเนินการ</span><strong data-signal-history-active></strong></div>
      <div><span>สำเร็จ</span><strong data-signal-history-completed></strong></div>
      <div><span>ติดขัด</span><strong data-signal-history-blocked></strong></div>
    </div>
    <div class="signal-history-table">
      <div class="signal-history-table-head" aria-hidden="true">
        <span>วันเวลา</span><span>ประเภท</span><span>รายการ</span><span>สถานะ</span><span>ผลสรุป</span><span></span>
      </div>
      <div class="signal-history-list" data-signal-history-list role="list"></div>
    </div>
  `;
  const search = container.querySelector("[data-signal-history-search]");
  const type = container.querySelector("[data-signal-history-type]");
  const status = container.querySelector("[data-signal-history-status]");
  const list = container.querySelector("[data-signal-history-list]");
  search.value = state.modal.signalHistoryQuery;
  type.value = state.modal.signalHistoryType;
  status.value = state.modal.signalHistoryStatus;
  const historyHasMore = council?.history?.hasMore === true
    || council?.decisionPipeline?.hasMore === true;
  container.querySelector("[data-signal-history-count]").textContent = historyHasMore
    ? `แสดง ${filtered.length} จาก ${allEntries.length} รายการล่าสุด • ยังมีรายการเก่ากว่า`
    : `แสดง ${filtered.length} จาก ${allEntries.length} รายการล่าสุด`;
  container.querySelector("[data-signal-history-total]").textContent = String(allEntries.length);
  container.querySelector("[data-signal-history-active]").textContent = String(active);
  container.querySelector("[data-signal-history-completed]").textContent = String(completed);
  container.querySelector("[data-signal-history-blocked]").textContent = String(blocked);
  if (!filtered.length) {
    const empty = document.createElement("div");
    empty.className = "signal-empty-state";
    empty.textContent = allEntries.length
      ? "ไม่พบรายการที่ตรงกับตัวกรอง"
      : "ยังไม่มี Mission หรือ Report จริงของสภา AI Trade";
    list.appendChild(empty);
  } else {
    filtered
      .sort((left, right) => getDashboardItemTime(right.item) - getDashboardItemTime(left.item))
      .forEach((entry) => list.appendChild(createSignalHistoryRow(entry)));
  }
  search.addEventListener("input", () => {
    state.modal.signalHistoryQuery = search.value;
    renderSignalHistoryPanel(report, { focusSearch: true });
    saveSessionSnapshot();
  });
  type.addEventListener("change", () => {
    state.modal.signalHistoryType = type.value;
    renderSignalHistoryPanel(report);
    saveSessionSnapshot();
  });
  status.addEventListener("change", () => {
    state.modal.signalHistoryStatus = status.value;
    renderSignalHistoryPanel(report);
    saveSessionSnapshot();
  });
  if (focusSearch) {
    const refreshed = container.querySelector("[data-signal-history-search]");
    refreshed?.focus();
    refreshed?.setSelectionRange(refreshed.value.length, refreshed.value.length);
  }
}

function signalConsensusPanelContainer(tabName) {
  return {
    daily_summary: els.signalConsensusDailyContent,
    live_analysis: els.signalConsensusLiveContent,
    decision_pipeline: els.signalConsensusDecisionContent,
    history: els.signalConsensusHistoryContent,
  }[tabName] || null;
}

function signalLiveAnalysisPanelContainer(tabName) {
  return {
    chart_overview: els.signalConsensusLiveOverviewContent,
    price_action: els.signalConsensusPriceActionContent,
    technical_deep: els.signalConsensusTechnicalContent,
    news_context: els.signalConsensusNewsContent,
  }[tabName] || null;
}

function renderSignalLiveAnalysisPanel(tabName, report = {}) {
  const selected = SIGNAL_LIVE_ANALYSIS_TABS.includes(tabName)
    ? tabName
    : SIGNAL_LIVE_ANALYSIS_TABS[0];
  if (selected === "chart_overview") renderSignalLivePanel(report);
  if (selected === "price_action") renderSignalPriceActionDeepPanel();
  if (selected === "technical_deep") renderSignalTechnicalDeepPanel();
  if (selected === "news_context") renderSignalNewsContextPanel();
}

function renderSignalConsensusPanel(tabName, report = {}) {
  const selected = SIGNAL_CONSENSUS_TABS.includes(tabName) ? tabName : SIGNAL_CONSENSUS_TABS[0];
  const container = signalConsensusPanelContainer(selected);
  const scrollState = container
    ? {
        panelTop: container.scrollTop,
        panelLeft: container.scrollLeft,
        nested: [...container.querySelectorAll(
          ".signal-history-table, .signal-history-list, .signal-timeline, .signal-live-main, .signal-consensus-rail, .signal-deep-table-viewport",
        )].map((node) => ({
          className: node.className,
          top: node.scrollTop,
          left: node.scrollLeft,
        })),
      }
    : null;
  if (selected === "daily_summary") renderSignalDailyPanel(report);
  if (selected === "live_analysis") {
    ensureSignalLiveAnalysisTabs();
    renderSignalLiveAnalysisPanel(state.modal.signalLiveTab, report);
    setSignalLiveAnalysisTab(state.modal.signalLiveTab, {
      persist: false,
      renderPanel: false,
      loadDeep: false,
    });
  }
  if (selected === "decision_pipeline") renderSignalDecisionPanel(report);
  if (selected === "history") renderSignalHistoryPanel(report);
  if (container && scrollState) {
    container.scrollTop = scrollState.panelTop;
    container.scrollLeft = scrollState.panelLeft;
    scrollState.nested.forEach((saved) => {
      const selector = `.${String(saved.className || "").trim().split(/\s+/).join(".")}`;
      if (selector === ".") return;
      const node = container.querySelector(selector);
      if (!node) return;
      node.scrollTop = saved.top;
      node.scrollLeft = saved.left;
    });
  }
}

function setSignalLiveAnalysisTab(
  tabName,
  { focus = false, persist = true, renderPanel = true, loadDeep = true } = {},
) {
  ensureSignalLiveAnalysisTabs();
  const selected = SIGNAL_LIVE_ANALYSIS_TABS.includes(tabName)
    ? tabName
    : SIGNAL_LIVE_ANALYSIS_TABS[0];
  state.modal.signalLiveTab = selected;
  if (renderPanel) {
    renderSignalLiveAnalysisPanel(
      selected,
      state.propReports[AI_TRADE_COUNCIL_PROP_ID] || {},
    );
  }
  const tabs = els.signalConsensusLiveTabs
    ? [...els.signalConsensusLiveTabs.querySelectorAll("[data-signal-live-tab]")]
    : [];
  tabs.forEach((tab) => {
    const active = tab.dataset.signalLiveTab === selected;
    tab.classList.toggle("active", active);
    tab.setAttribute("aria-selected", active ? "true" : "false");
    tab.tabIndex = active ? 0 : -1;
    if (active && focus) tab.focus();
  });
  if (els.signalConsensusLiveContent) {
    [...els.signalConsensusLiveContent.querySelectorAll("[data-signal-live-panel]")].forEach((panel) => {
      const active = panel.dataset.signalLivePanel === selected;
      panel.hidden = !active;
      panel.classList.toggle("active", active);
    });
  }
  if (selected === "price_action") {
    window.requestAnimationFrame(() => {
      drawSignalChartGrid(els.signalConsensusPriceActionContent?.querySelector("[data-signal-deep-price-chart]"));
    });
  }
  if (loadDeep && SIGNAL_DEEP_ANALYSIS_TABS.includes(selected)) {
    void loadSignalDeepAnalysis();
  }
  if (persist) saveSessionSnapshot();
}

function setSignalConsensusTab(
  tabName,
  { focus = false, persist = true, renderPanel = true, loadNested = true } = {},
) {
  ensureSignalLiveAnalysisTabs();
  const selected = SIGNAL_CONSENSUS_TABS.includes(tabName) ? tabName : SIGNAL_CONSENSUS_TABS[0];
  state.modal.signalTab = selected;
  if (renderPanel) {
    renderSignalConsensusPanel(
      selected,
      state.propReports[AI_TRADE_COUNCIL_PROP_ID] || {},
    );
  }
  const tabs = els.signalConsensusTabs
    ? [...els.signalConsensusTabs.querySelectorAll("[data-signal-tab]")]
    : [];
  tabs.forEach((tab) => {
    const active = tab.dataset.signalTab === selected;
    tab.classList.toggle("active", active);
    tab.setAttribute("aria-selected", active ? "true" : "false");
    tab.tabIndex = active ? 0 : -1;
    if (active && focus) tab.focus();
  });
  if (els.modalSignalConsensusWorkspace) {
    [...els.modalSignalConsensusWorkspace.querySelectorAll("[data-signal-panel]")].forEach((panel) => {
      const active = panel.dataset.signalPanel === selected;
      panel.hidden = !active;
      panel.classList.toggle("active", active);
    });
  }
  if (selected === "live_analysis") {
    setSignalLiveAnalysisTab(state.modal.signalLiveTab, {
      persist: false,
      renderPanel: false,
      loadDeep: loadNested,
    });
  }
  if (persist) saveSessionSnapshot();
}

function renderSignalConsensusDashboard(subject, propertyRole, report = {}) {
  if (!subject || subject.id !== AI_TRADE_COUNCIL_PROP_ID) return;
  ensureSignalLiveAnalysisTabs();
  renderSignalConsensusPanel(state.modal.signalTab, report);
  setSignalConsensusTab(state.modal.signalTab, {
    persist: false,
    renderPanel: false,
    loadNested: (
      state.modal.open
      && state.modal.id === AI_TRADE_COUNCIL_PROP_ID
      && state.modal.signalTab === "live_analysis"
    ),
  });
}

function isWorkflowDashboardPropId(propId) {
  return WORKFLOW_DASHBOARD_PROP_IDS.includes(String(propId || ""));
}

function normalizeWorkflowField(field = {}) {
  const id = String(field?.id || "").trim();
  if (!/^[a-zA-Z0-9_-]{1,60}$/.test(id) || WORKFLOW_FIELD_DENY_PATTERN.test(id)) return null;
  const allowedTypes = ["text", "textarea", "number", "select", "checkbox", "source", "time", "date", "list"];
  const typeAliases = {
    source_report: "source",
    source_catalog: "source",
    workspace_source: "source",
    boolean: "checkbox",
    time_list: "list",
    integer: "number",
  };
  const rawType = String(field?.type || "").trim();
  const requestedType = typeAliases[rawType] || rawType;
  const type = ["sourceId", "workspaceSourceId"].includes(id)
    ? "source"
    : (allowedTypes.includes(requestedType) ? requestedType : "text");
  const sourceKind = rawType === "workspace_source" || ["sourceId", "workspaceSourceId"].includes(id)
    ? "workspace_source"
    : (type === "source" ? "source_report" : "");
  const numericBounds = WORKFLOW_NUMERIC_FIELD_BOUNDS[id] || null;
  const options = Array.isArray(field?.options)
    ? field.options.slice(0, 40).map((option) => {
        if (option && typeof option === "object" && !Array.isArray(option)) {
          return {
            value: safeDashboardDisplayText(option.value ?? option.id ?? option.labelTh, ""),
            labelTh: safeDashboardDisplayText(option.labelTh ?? option.label ?? option.value, ""),
          };
        }
        const value = safeDashboardDisplayText(option, "");
        return { value, labelTh: value };
      }).filter((option) => option.value)
    : [];
  return {
    id,
    labelTh: safeDashboardDisplayText(field?.labelTh || field?.label, id),
    type,
    required: field?.required === true,
    options,
    placeholderTh: safeDashboardDisplayText(field?.placeholderTh || field?.placeholder, ""),
    voiceDictation: field?.voiceDictation === true,
    sourceKind,
    integer: rawType === "integer" || Boolean(numericBounds),
    min: numericBounds?.min ?? null,
    max: numericBounds?.max ?? null,
    step: numericBounds?.step ?? null,
  };
}

function normalizeWorkflowAction(rawAction = {}, fallbackAction = {}) {
  const id = String(rawAction?.id || fallbackAction?.id || "").trim();
  if (!/^[a-z0-9_-]{1,80}$/i.test(id)) return null;
  const rawAvailability = rawAction?.availability && typeof rawAction.availability === "object"
    ? rawAction.availability
    : fallbackAction?.availability || {};
  const status = ["ready", "settings_only", "configuration_required", "coming_soon", "unavailable"].includes(rawAvailability?.status)
    ? rawAvailability.status
    : "configuration_required";
  const rawFields = Array.isArray(rawAction?.formFields)
    ? rawAction.formFields
    : (Array.isArray(fallbackAction?.formFields) ? fallbackAction.formFields : []);
  const fallbackFieldMap = new Map(
    (Array.isArray(fallbackAction?.formFields) ? fallbackAction.formFields : [])
      .map((field) => [String(field?.id || ""), field]),
  );
  return {
    id,
    tabId: String(rawAction?.tabId || fallbackAction?.tabId || "").trim(),
    labelTh: safeDashboardDisplayText(rawAction?.labelTh || fallbackAction?.labelTh, "สร้าง Mission"),
    descriptionTh: safeDashboardDisplayText(
      rawAction?.descriptionTh || fallbackAction?.descriptionTh,
      "ส่งคำขอไปยัง Local Runner และรอรายงานกลับมาที่อุปกรณ์นี้",
    ),
    sourceRequired: rawAction?.sourceRequired === true || fallbackAction?.sourceRequired === true,
    analysisOnly: rawAction?.analysisOnly === true,
    availability: {
      status,
      realToolAvailable: rawAvailability?.realToolAvailable === true,
    },
    formFields: rawFields
      .map((field) => normalizeWorkflowField({
        ...(fallbackFieldMap.get(String(field?.id || "")) || {}),
        ...(field && typeof field === "object" ? field : {}),
      }))
      .filter(Boolean),
  };
}

function normalizeWorkflowSheetTemplate(rawTemplate = {}) {
  const template = rawTemplate && typeof rawTemplate === "object" ? rawTemplate : {};
  const suppliedColumns = Array.isArray(template.columns)
    ? [...new Set(template.columns
        .map((column) => String(column || "").trim())
        .filter((column) => /^[a-z][a-z0-9_]{0,63}$/.test(column)))]
    : [];
  const columns = suppliedColumns.length === WORKFLOW_DISCOVERY_SHEET_COLUMNS.length
    ? suppliedColumns
    : [...WORKFLOW_DISCOVERY_SHEET_COLUMNS];
  const suppliedDeduplicationFields = Array.isArray(template.deduplicationFields)
    ? template.deduplicationFields
        .map((field) => String(field || "").trim())
        .filter((field) => columns.includes(field))
    : [];
  return {
    schemaVersion: safeDashboardDisplayText(template.schemaVersion, "global-trading-system-sheet-v1"),
    columns,
    deduplicationFields: suppliedDeduplicationFields.length
      ? [...new Set(suppliedDeduplicationFields)]
      : [...WORKFLOW_DISCOVERY_DEDUPLICATION_FIELDS],
    templateReference: safeDashboardDisplayText(
      template.templateReference,
      "contracts/research/trading-system-sheet-template.csv",
    ),
    connectionStatus: String(template.connectionStatus || "not_connected").trim().toLowerCase(),
    connectionLabelTh: safeDashboardDisplayText(template.connectionLabelTh, "ยังไม่ได้เชื่อม Google Sheet"),
    credentialsAcceptedByFrontend: false,
  };
}

function normalizeWorkflowDeduplication(rawDeduplication = {}) {
  const deduplication = rawDeduplication && typeof rawDeduplication === "object" ? rawDeduplication : {};
  return {
    backendOwned: deduplication.backendOwned === true,
    localReportCatalogAvailable: deduplication.localReportCatalogAvailable === true,
    googleSheetRowsAvailable: deduplication.googleSheetRowsAvailable === true,
    scopeLabelTh: safeDashboardDisplayText(
      deduplication.scopeLabelTh,
      "รอตรวจสถานะการค้นหารายการซ้ำจาก Local Runner",
    ),
  };
}

function normalizeWorkflowSourceCatalog(rawCatalog) {
  return (Array.isArray(rawCatalog) ? rawCatalog : [])
    .slice(0, 100)
    .map((item) => {
      const sourceId = String(item?.sourceId || item?.id || "").trim();
      if (!/^[a-zA-Z0-9._-]{1,120}$/.test(sourceId)) return null;
      return {
        workspaceSourceId: sourceId,
        sourceId,
        title: safeDashboardDisplayText(item?.title || item?.fileName || item?.displayName || item?.label || item?.name, "Source ใน Workspace"),
        platform: safeDashboardDisplayText(item?.platform || item?.language, "ยังไม่ระบุภาษา"),
        kind: safeDashboardDisplayText(item?.kind || item?.artifactKind, "source"),
        status: safeDashboardDisplayText(item?.status, "ready"),
        updatedAt: item?.updatedAt || null,
      };
    })
    .filter(Boolean);
}

function normalizeWorkflowDashboard(subject, propertyRole, report = {}) {
  const fallback = WORKFLOW_DASHBOARD_FALLBACKS[subject?.id] || {};
  const roleWorkflow = propertyRole?.workflow && typeof propertyRole.workflow === "object"
    ? propertyRole.workflow
    : {};
  const backend = report?.workflowDashboard && typeof report.workflowDashboard === "object"
    ? report.workflowDashboard
    : {};
  const fallbackActionMap = new Map((fallback.actions || []).map((action) => [action.id, action]));
  const rawActions = Array.isArray(backend.actions)
    ? backend.actions
    : (Array.isArray(roleWorkflow.actions) ? roleWorkflow.actions : fallback.actions || []);
  const actions = rawActions
    .map((action) => normalizeWorkflowAction(action, fallbackActionMap.get(action?.id) || {}))
    .filter(Boolean);
  const actionMap = new Map(actions.map((action) => [action.id, action]));
  const suppliedTabs = Array.isArray(backend.tabs)
    ? backend.tabs
    : (Array.isArray(propertyRole?.localTabs) ? propertyRole.localTabs : []);
  const suppliedTabMap = new Map(suppliedTabs.map((tab) => [String(tab?.id || tab), tab]));
  const rawTabs = (fallback.tabs || []).length
    ? fallback.tabs.map((fallbackTab) => {
        const suppliedTab = suppliedTabMap.get(fallbackTab.id);
        if (!suppliedTab || typeof suppliedTab !== "object") return fallbackTab;
        return {
          ...fallbackTab,
          ...suppliedTab,
          actionIds: Array.isArray(suppliedTab.actionIds) ? suppliedTab.actionIds : fallbackTab.actionIds,
        };
      })
    : suppliedTabs;
  const normalizedTabs = rawTabs.map((tab, index) => {
    const fallbackTab = (fallback.tabs || []).find((item) => item.id === (tab?.id || tab)) || {};
    const id = String(tab?.id || tab || `tab-${index + 1}`).trim();
    if (!/^[a-z0-9_-]{1,60}$/i.test(id)) return null;
    const requestedActionIds = Array.isArray(tab?.actionIds)
      ? tab.actionIds
      : (Array.isArray(fallbackTab.actionIds) ? fallbackTab.actionIds : []);
    return {
      id,
      labelTh: safeDashboardDisplayText(tab?.labelTh || tab?.label || fallbackTab.labelTh, `ส่วนที่ ${index + 1}`),
      descriptionTh: safeDashboardDisplayText(tab?.descriptionTh || fallbackTab.descriptionTh, "เลือกเพื่อดูงานและผลลัพธ์"),
      emptyMessageTh: safeDashboardDisplayText(tab?.emptyMessageTh || fallbackTab.emptyMessageTh, ""),
      actionIds: requestedActionIds.filter((actionId) => actionMap.has(actionId)),
    };
  }).filter(Boolean);
  const visibleTabs = normalizedTabs.filter((tab) => !WORKFLOW_DASHBOARD_SETTING_TAB_IDS.has(tab.id));
  if (visibleTabs.length && !WORKFLOW_DASHBOARD_HISTORY_TAB_IDS.has(visibleTabs.at(-1).id)) {
    visibleTabs.push({
      id: "history",
      labelTh: "ประวัติและรายงาน",
      descriptionTh: "ดู Mission, Report และหลักฐานย้อนหลังของอุปกรณ์นี้",
      emptyMessageTh: "",
      actionIds: [],
    });
  }
  const primaryTabCopy = WORKFLOW_DASHBOARD_PRIMARY_TABS[subject?.id] || {};
  const tabs = visibleTabs.map((tab, index, list) => {
    const isPrimary = index === 0;
    const isHistory = index === list.length - 1;
    const isPortalCatalog = subject?.id === "codex_mcp_portal" && tab.id === "catalog";
    return {
      ...tab,
      labelTh: isPrimary
        ? safeDashboardDisplayText(primaryTabCopy.labelTh, tab.labelTh)
        : (isHistory ? "ประวัติและรายงาน" : (isPortalCatalog ? "คลังและแบบฟอร์มข้อมูล" : tab.labelTh)),
      descriptionTh: isPrimary
        ? safeDashboardDisplayText(primaryTabCopy.descriptionTh, tab.descriptionTh)
        : (isHistory
            ? "ดู Mission, Report และหลักฐานย้อนหลังของอุปกรณ์นี้"
            : (isPortalCatalog
                ? "ดูแม่แบบคลังข้อมูลและสถานะการเชื่อมต่อที่ Backend ยืนยัน"
                : tab.descriptionTh)),
      actionIds: tab.actionIds.filter((actionId) => !WORKFLOW_DASHBOARD_SETTING_ACTION_IDS.has(actionId)),
    };
  });
  const deliveredSourceRows = Array.isArray(backend.agentDeliveredSources)
    ? backend.agentDeliveredSources
    : [];
  const agentDeliveredSources = deliveredSourceRows
    .filter((source) => source && typeof source === "object" && source.reportId)
    .slice(0, 100)
    .map((source) => ({
      reportId: String(source.reportId),
      sourcePropId: String(source.sourcePropId || ""),
      title: safeDashboardDisplayText(source.title, "รายงานต้นทาง"),
      summary: safeDashboardDisplayText(source.summary, "เปิดเพื่อดูรายละเอียดก่อนเลือกใช้งาน"),
      type: safeDashboardDisplayText(source.type, "report"),
      ownerAgentId: String(source.ownerAgentId || ""),
      status: String(source.status || "ready"),
      updatedAt: source.updatedAt || null,
    }));
  return {
    titleTh: safeDashboardDisplayText(backend.titleTh || roleWorkflow.titleTh || fallback.titleTh, displayPropName(subject?.id)),
    summaryTh: safeDashboardDisplayText(backend.summaryTh || roleWorkflow.summaryTh || fallback.summaryTh, propertyRole?.purpose || ""),
    tabs: tabs.length ? tabs : fallback.tabs || [],
    actions,
    agentDeliveredSources,
    workspaceSources: normalizeWorkflowSourceCatalog(backend.workspaceSources || backend.sourceCatalog),
    schedule: backend.schedule && typeof backend.schedule === "object" ? backend.schedule : null,
    sheetTemplate: subject?.id === "codex_mcp_portal"
      ? normalizeWorkflowSheetTemplate(backend.sheetTemplate)
      : null,
    deduplication: subject?.id === "codex_mcp_portal"
      ? normalizeWorkflowDeduplication(backend.deduplication)
      : null,
    domainData: normalizeWorkflowDomainData(subject?.id, backend, report),
    guardrails: Array.isArray(backend.guardrails) ? backend.guardrails.slice(0, 8) : [],
  };
}

function getWorkflowSelectedTab(propId, dashboard) {
  const tabs = Array.isArray(dashboard?.tabs) ? dashboard.tabs : [];
  const requested = state.modal.workflowTabs[propId];
  return tabs.find((tab) => tab.id === requested) || tabs[0] || null;
}

function renderWorkflowTabs(propId, dashboard, selectedTab) {
  if (!els.workflowDashboardTabs) return;
  els.workflowDashboardTabs.innerHTML = "";
  dashboard.tabs.forEach((tab) => {
    const button = document.createElement("button");
    const active = tab.id === selectedTab?.id;
    button.type = "button";
    button.className = "workflow-tab";
    button.dataset.workflowTab = tab.id;
    button.setAttribute("role", "tab");
    button.setAttribute("aria-selected", active ? "true" : "false");
    button.setAttribute("aria-controls", "workflowDashboardContent");
    button.tabIndex = active ? 0 : -1;
    button.classList.toggle("active", active);
    button.textContent = tab.labelTh;
    els.workflowDashboardTabs.appendChild(button);
  });
  if (els.workflowDashboardContent && selectedTab) {
    els.workflowDashboardContent.setAttribute("aria-label", selectedTab.labelTh);
  }
}

function workflowAvailabilityCopy(action, hasSources) {
  if (WORKFLOW_DASHBOARD_SETTING_ACTION_IDS.has(action.id)) {
    return action.id === "save_agent_preferences"
      ? {
          tone: "ready",
          label: "บันทึกการตั้งค่าได้",
          detail: "Local Runner จะเก็บเฉพาะค่าการทำงานที่ปลอดภัยและไม่รับ Token, Cookie หรือ Secret",
        }
      : {
          tone: "ready",
          label: "บันทึกเวลาได้",
          detail: "บันทึกเวลาที่ต้องการไว้ใน Local Runner; ระบบตั้งเวลาอัตโนมัติจะทำงานเมื่อ Scheduler พร้อม",
        };
  }
  if (action.sourceRequired && !hasSources) {
    return { tone: "warning", label: "ยังไม่มี Report ที่ส่งต่อมา", detail: "เลือก Report ที่อุปกรณ์ต้นทาง แล้วมอบหมาย Agent ให้ส่งต่อผ่าน Mission ก่อน" };
  }
  if (action.id === "refresh_vps_hq_status") {
    return { tone: "ready", label: "พร้อมตรวจสถานะ", detail: "อ่านสถานะ Local Runner, HQ และ Mission Worker จาก Backend โดยไม่เรียก Codex" };
  }
  if (action.id === "save_agent_preferences") {
    return { tone: "ready", label: "บันทึกค่า Agent แบบปลอดภัยได้", detail: "เก็บเฉพาะภาษา ระดับการประมวลผล งบ เวลา ขนาดรายงาน และ Rate Limit สำรองใน Local Runner" };
  }
  if (action.availability.status === "ready") {
    return action.analysisOnly || !action.availability.realToolAvailable
      ? { tone: "ready", label: "พร้อมสร้าง Mission", detail: "Local Runner จะรับคำขอและรายงานสถานะจริงกลับมา" }
      : { tone: "ready", label: "พร้อมส่งงานหลังบ้าน", detail: "ผลลัพธ์จริงจะกลับมาพร้อม Audit Log" };
  }
  if (action.availability.status === "settings_only") {
    return { tone: "ready", label: "บันทึกการตั้งค่าได้", detail: "บันทึกเวลาที่ต้องการเท่านั้น ระบบตั้งเวลาอัตโนมัติยังไม่ทำงาน" };
  }
  if (action.availability.status === "coming_soon") {
    return { tone: "warning", label: "Coming Soon", detail: "วางหน้าจอไว้แล้ว แต่ระบบหลังบ้านส่วนนี้ยังไม่เปิดใช้งาน" };
  }
  return { tone: "warning", label: "ต้องเชื่อมระบบก่อน", detail: "ตรวจการเชื่อมต่อด้านซ้าย เมื่อพร้อมแล้วปุ่มเริ่มงานจะเปิดใช้งาน" };
}

function createWorkflowSourceSelect(field, sources) {
  const select = document.createElement("select");
  const empty = document.createElement("option");
  select.dataset.workflowField = field.id;
  select.required = field.required;
  empty.value = "";
  const isWorkspaceSource = field.sourceKind === "workspace_source";
  select.dataset.workflowSourceKind = isWorkspaceSource ? "workspace_source" : "source_report";
  empty.textContent = sources.length
    ? (isWorkspaceSource ? "เลือก Source ที่ Backend อนุญาต" : "เลือก Report ที่ Agent ส่งเข้ามา")
    : (isWorkspaceSource ? "ยังไม่มี Source ใน Approved Workspace Catalog" : "ยังไม่มี Report ที่ Agent ส่งเข้ามาผ่าน Mission");
  select.appendChild(empty);
  sources.forEach((source) => {
    const option = document.createElement("option");
    option.value = isWorkspaceSource ? source.workspaceSourceId : source.reportId;
    if (isWorkspaceSource) option.dataset.platform = String(source.platform || "");
    option.textContent = isWorkspaceSource
      ? `${source.title} • ${source.platform} • ${displayStatus(source.status)}`
      : `${source.title} • ${displayPropName(source.sourcePropId, "แหล่งข้อมูลเดิม")}`;
    select.appendChild(option);
  });
  select.disabled = !sources.length;
  return select;
}

function getWorkflowSpeechRecognitionConstructor() {
  return window.SpeechRecognition || window.webkitSpeechRecognition || null;
}

function updateWorkflowVoiceControls() {
  const voice = state.modal.workflowVoice;
  document.querySelectorAll("[data-workflow-dictation]").forEach((button) => {
    const active = voice.status === "listening"
      && button.dataset.workflowProp === voice.propId
      && button.dataset.workflowAction === voice.actionId
      && button.dataset.workflowVoiceField === voice.fieldId;
    button.classList.toggle("active", active);
    button.setAttribute("aria-pressed", active ? "true" : "false");
    button.textContent = active ? "หยุดรับเสียง" : "พูดเพื่อพิมพ์";
  });
  document.querySelectorAll("[data-workflow-voice-status]").forEach((status) => {
    const current = status.dataset.workflowProp === voice.propId
      && status.dataset.workflowAction === voice.actionId
      && status.dataset.workflowVoiceField === voice.fieldId;
    status.dataset.tone = current ? voice.status : "idle";
    status.textContent = current && voice.message
      ? voice.message
      : "เสียงจะถูกแปลงเป็นข้อความในเบราว์เซอร์ และส่งเมื่อคุณกดสร้าง Mission เท่านั้น";
  });
}

function stopWorkflowVoiceDictation({ preserveMessage = false } = {}) {
  const voice = state.modal.workflowVoice;
  const recognition = voice.recognition;
  voice.recognition = null;
  if (recognition) {
    try {
      recognition.onend = null;
      recognition.abort();
    } catch {
      // Recognition may already have ended; UI state remains deterministic.
    }
  }
  voice.status = preserveMessage && voice.status === "error" ? "error" : "idle";
  if (!preserveMessage) voice.message = "หยุดรับเสียงแล้ว คุณแก้ข้อความก่อนส่งได้";
  updateWorkflowVoiceControls();
}

function toggleWorkflowVoiceDictation(button) {
  const propId = String(button?.dataset.workflowProp || "");
  const actionId = String(button?.dataset.workflowAction || "");
  const fieldId = String(button?.dataset.workflowVoiceField || "");
  const form = button?.closest("[data-workflow-action-form]");
  const control = form?.querySelector(`[data-workflow-field="${fieldId}"]`);
  const voice = state.modal.workflowVoice;
  if (!propId || !actionId || !fieldId || !(control instanceof HTMLTextAreaElement)) return;
  const sameTarget = voice.status === "listening"
    && voice.propId === propId
    && voice.actionId === actionId
    && voice.fieldId === fieldId;
  if (sameTarget) {
    stopWorkflowVoiceDictation();
    return;
  }
  if (voice.recognition) stopWorkflowVoiceDictation();
  voice.propId = propId;
  voice.actionId = actionId;
  voice.fieldId = fieldId;
  const Recognition = getWorkflowSpeechRecognitionConstructor();
  if (!Recognition) {
    voice.status = "error";
    voice.message = "เบราว์เซอร์นี้ไม่รองรับการพิมพ์ด้วยเสียง กรุณาพิมพ์โจทย์แทน";
    updateWorkflowVoiceControls();
    return;
  }
  let recognition;
  try {
    recognition = new Recognition();
    recognition.lang = "th-TH";
    recognition.continuous = true;
    recognition.interimResults = true;
  } catch {
    voice.status = "error";
    voice.message = "เปิดระบบรับเสียงไม่สำเร็จ กรุณาพิมพ์โจทย์แทน";
    updateWorkflowVoiceControls();
    return;
  }
  voice.recognition = recognition;
  voice.status = "listening";
  voice.message = "กำลังฟัง... พูดโจทย์ได้เลย แล้วกดหยุดรับเสียงเมื่อเสร็จ";
  recognition.onresult = (event) => {
    let finalTranscript = "";
    let interimTranscript = "";
    for (let index = event.resultIndex; index < event.results.length; index += 1) {
      const transcript = String(event.results[index]?.[0]?.transcript || "").trim();
      if (!transcript) continue;
      if (event.results[index].isFinal) finalTranscript += `${transcript} `;
      else interimTranscript += `${transcript} `;
    }
    if (finalTranscript.trim()) {
      const separator = control.value.trim() ? " " : "";
      control.value = `${control.value.trimEnd()}${separator}${finalTranscript.trim()}`.slice(0, 4000);
      control.dispatchEvent(new Event("input", { bubbles: true }));
    }
    voice.message = interimTranscript.trim()
      ? `กำลังฟัง: ${interimTranscript.trim().slice(0, 120)}`
      : "รับข้อความแล้ว กำลังฟังต่อ...";
    updateWorkflowVoiceControls();
  };
  recognition.onerror = (event) => {
    const error = String(event?.error || "unknown");
    voice.status = "error";
    if (["not-allowed", "service-not-allowed"].includes(error)) {
      voice.message = "ไมโครโฟนยังไม่ได้รับอนุญาต กรุณาอนุญาตสิทธิ์ไมโครโฟนในเบราว์เซอร์แล้วลองใหม่";
    } else if (error === "audio-capture") {
      voice.message = "ไม่พบไมโครโฟนที่ใช้งานได้ กรุณาตรวจอุปกรณ์เสียงแล้วลองใหม่";
    } else if (error === "no-speech") {
      voice.message = "ยังไม่ได้ยินเสียง กรุณากดพูดเพื่อพิมพ์แล้วลองอีกครั้ง";
    } else {
      voice.message = "รับเสียงไม่สำเร็จ กรุณาตรวจการเชื่อมต่อหรือพิมพ์โจทย์แทน";
    }
    voice.recognition = null;
    updateWorkflowVoiceControls();
  };
  recognition.onend = () => {
    if (voice.recognition !== recognition) return;
    voice.recognition = null;
    if (voice.status !== "error") {
      voice.status = "idle";
      voice.message = "หยุดรับเสียงแล้ว คุณแก้ข้อความก่อนส่งได้";
    }
    updateWorkflowVoiceControls();
  };
  try {
    recognition.start();
  } catch {
    voice.recognition = null;
    voice.status = "error";
    voice.message = "เริ่มรับเสียงไม่สำเร็จ กรุณารอสักครู่แล้วลองใหม่";
  }
  updateWorkflowVoiceControls();
}

function createWorkflowField(field, dashboard, actionId) {
  const wrapper = document.createElement("div");
  const label = document.createElement("label");
  let control;
  wrapper.className = `workflow-field workflow-field-${field.type}`;
  const isAgentDeliveredReport = field.type === "source" && field.sourceKind !== "workspace_source";
  label.textContent = `${field.labelTh}${isAgentDeliveredReport ? " • Agent ส่งผ่าน Mission" : ""}${field.required ? " *" : ""}`;
  if (field.type === "source") {
    const sources = field.sourceKind === "workspace_source" ? dashboard.workspaceSources : dashboard.agentDeliveredSources;
    control = createWorkflowSourceSelect(field, sources);
  } else if (field.type === "textarea" || field.type === "list") {
    control = document.createElement("textarea");
    control.rows = field.type === "list" ? 2 : 4;
    control.dataset.workflowField = field.id;
    control.dataset.workflowValueType = field.type;
    control.required = field.required;
  } else if (field.type === "select") {
    control = document.createElement("select");
    control.dataset.workflowField = field.id;
    control.required = field.required;
    const empty = document.createElement("option");
    empty.value = "";
    empty.textContent = "เลือกข้อมูล";
    control.appendChild(empty);
    field.options.forEach((option) => {
      const node = document.createElement("option");
      node.value = option.value;
      node.textContent = option.labelTh;
      control.appendChild(node);
    });
  } else {
    control = document.createElement("input");
    control.type = field.type === "checkbox" ? "checkbox" : field.type;
    control.dataset.workflowField = field.id;
    control.required = field.required;
    if (field.type === "number") {
      control.step = field.step ?? "any";
      if (Number.isFinite(field.min)) control.min = String(field.min);
      if (Number.isFinite(field.max)) control.max = String(field.max);
      control.inputMode = field.integer ? "numeric" : "decimal";
    }
  }
  const controlId = `workflow-${String(state.modal.id || "prop")}-${actionId}-${field.id}`;
  control.id = controlId;
  label.htmlFor = controlId;
  if (field.placeholderTh && "placeholder" in control) control.placeholder = field.placeholderTh;
  const preferenceValue = dashboard.domainData?.vpsHqStatus?.agentPreferences?.[field.id];
  if (preferenceValue !== undefined && preferenceValue !== null) {
    if (control instanceof HTMLSelectElement) {
      const candidate = String(preferenceValue);
      if ([...control.options].some((option) => option.value === candidate)) control.value = candidate;
    } else if (control instanceof HTMLInputElement && control.type === "number" && Number.isFinite(Number(preferenceValue))) {
      control.value = String(preferenceValue);
    }
  }
  wrapper.append(label, control);
  if (field.voiceDictation && control instanceof HTMLTextAreaElement) {
    const toolbar = document.createElement("div");
    const dictate = document.createElement("button");
    const status = document.createElement("span");
    toolbar.className = "workflow-voice-toolbar";
    dictate.type = "button";
    dictate.className = "workflow-dictation-button";
    dictate.dataset.workflowDictation = "true";
    dictate.dataset.workflowProp = String(state.modal.id || "");
    dictate.dataset.workflowAction = actionId;
    dictate.dataset.workflowVoiceField = field.id;
    dictate.setAttribute("aria-controls", controlId);
    dictate.setAttribute("aria-pressed", "false");
    dictate.textContent = "พูดเพื่อพิมพ์";
    status.className = "workflow-voice-status";
    status.dataset.workflowVoiceStatus = "true";
    status.dataset.workflowProp = String(state.modal.id || "");
    status.dataset.workflowAction = actionId;
    status.dataset.workflowVoiceField = field.id;
    status.dataset.tone = "idle";
    status.setAttribute("aria-live", "polite");
    status.textContent = "เสียงจะถูกแปลงเป็นข้อความในเบราว์เซอร์ และส่งเมื่อคุณกดสร้าง Mission เท่านั้น";
    toolbar.append(dictate, status);
    wrapper.appendChild(toolbar);
  }
  return wrapper;
}

function createWorkflowActionCard(action, dashboard) {
  const form = document.createElement("form");
  const heading = document.createElement("div");
  const headingCopy = document.createElement("div");
  const title = document.createElement("h4");
  const description = document.createElement("p");
  const availability = document.createElement("span");
  const fieldGrid = document.createElement("div");
  const footer = document.createElement("footer");
  const truth = document.createElement("p");
  const submit = document.createElement("button");
  const sourceFields = action.formFields.filter((field) => field.type === "source");
  const hasSources = sourceFields.length
    ? sourceFields.some((field) => (
        field.sourceKind === "workspace_source" ? dashboard.workspaceSources.length > 0 : dashboard.agentDeliveredSources.length > 0
      ))
    : dashboard.agentDeliveredSources.length > 0;
  const availabilityCopy = workflowAvailabilityCopy(action, hasSources);
  const inFlight = state.modal.workflowAction.inFlight
    && state.modal.workflowAction.propId === state.modal.id
    && state.modal.workflowAction.actionId === action.id;
  const canSubmit = ["ready", "settings_only"].includes(action.availability.status) && (!action.sourceRequired || hasSources);
  form.className = "workflow-action-card";
  form.dataset.workflowActionForm = action.id;
  form.setAttribute("aria-busy", inFlight ? "true" : "false");
  heading.className = "workflow-action-heading";
  title.textContent = action.labelTh;
  description.textContent = action.descriptionTh;
  availability.className = "workflow-availability";
  availability.dataset.tone = availabilityCopy.tone;
  availability.textContent = availabilityCopy.label;
  headingCopy.append(title, description);
  heading.append(headingCopy, availability);
  fieldGrid.className = "workflow-field-grid";
  action.formFields.forEach((field) => fieldGrid.appendChild(createWorkflowField(field, dashboard, action.id)));
  const sourceSelectors = [...fieldGrid.querySelectorAll("select[data-workflow-source-kind]")];
  sourceSelectors.forEach((selector) => {
    selector.addEventListener("change", () => {
      sourceSelectors.forEach((item) => item.setCustomValidity(""));
      if (!selector.value) return;
      sourceSelectors.forEach((other) => {
        if (other !== selector) other.value = "";
      });
      if (selector.dataset.workflowSourceKind === "workspace_source") {
        const platform = selector.selectedOptions[0]?.dataset.platform;
        const platformControl = fieldGrid.querySelector('[data-workflow-field="platform"]');
        if (platform && platformControl instanceof HTMLSelectElement) {
          platformControl.value = platform;
        }
      }
    });
  });
  footer.className = "workflow-action-footer";
  truth.textContent = availabilityCopy.detail;
  submit.type = "submit";
  submit.className = "modal-action primary workflow-submit";
  submit.disabled = !canSubmit || inFlight;
  const isSettingsAction = WORKFLOW_DASHBOARD_SETTING_ACTION_IDS.has(action.id);
  const idleSubmitLabel = isSettingsAction
    ? (action.id === "save_agent_preferences" ? "บันทึกการตั้งค่า" : "บันทึกเวลา")
    : (action.id === "refresh_vps_hq_status" ? "ตรวจสถานะ" : "สร้าง Mission");
  submit.textContent = inFlight
    ? (isSettingsAction ? "กำลังบันทึก..." : "กำลังส่งคำขอ...")
    : idleSubmitLabel;
  footer.append(truth, submit);
  form.append(heading, fieldGrid, footer);
  return form;
}

function renderWorkflowSourceCards(container, sources) {
  const section = document.createElement("section");
  const heading = document.createElement("div");
  const title = document.createElement("h4");
  const count = document.createElement("span");
  const list = document.createElement("div");
  section.className = "workflow-source-section";
  heading.className = "workflow-source-heading";
  title.textContent = "Report ที่ Agent ส่งเข้ามาผ่าน Mission";
  count.textContent = `${sources.length} รายการ`;
  heading.append(title, count);
  list.className = "workflow-source-list";
  if (!sources.length) {
    const empty = document.createElement("p");
    empty.className = "workflow-empty-message";
    empty.textContent = "ยังไม่มี Report ที่ส่งเข้ามา อุปกรณ์นี้จะไม่ดึงข้อมูลจากจุดอื่นเอง ให้สร้าง Mission ส่งต่อจากอุปกรณ์ต้นทางก่อน";
    list.appendChild(empty);
  } else {
    sources.slice(0, 12).forEach((source) => {
      const card = document.createElement("button");
      const meta = document.createElement("span");
      const titleNode = document.createElement("strong");
      const summary = document.createElement("span");
      card.type = "button";
      card.className = "workflow-source-card";
      meta.textContent = `${displayPropName(source.sourcePropId, "รายงานเดิม")} • ${displayStatus(source.status)}`;
      titleNode.textContent = source.title;
      summary.textContent = source.summary;
      card.append(meta, titleNode, summary);
      card.addEventListener("click", () => openDashboardResultDetail(source, card));
      list.appendChild(card);
    });
  }
  section.append(heading, list);
  container.appendChild(section);
}

function workflowPrimaryReportRows(subject, dashboard, report = {}) {
  const acceptedTypes = new Set(WORKFLOW_DASHBOARD_PRIMARY_REPORT_TYPES[subject?.id] || []);
  const rows = [];
  const seen = new Set();
  const append = (item, kind) => {
    const id = String(item?.id || item?.reportId || "").trim();
    if (!id || seen.has(id)) return;
    const type = String(item?.type || item?.reportType || "").trim();
    const linkedPropId = String(item?.linkedPropId || "").trim();
    if (kind === "report" && acceptedTypes.size && !acceptedTypes.has(type)) return;
    if (kind === "report" && linkedPropId && linkedPropId !== subject.id) return;
    seen.add(id);
    rows.push({
      ...item,
      id,
      reportId: id,
      type,
      _workflowPrimaryKind: kind,
    });
  };
  (Array.isArray(report?.reports) ? report.reports : []).forEach((item) => append(item, "report"));
  (Array.isArray(dashboard?.agentDeliveredSources) ? dashboard.agentDeliveredSources : [])
    .forEach((item) => append(item, "source"));
  const timestamp = (item) => Date.parse(item?.updatedAt || item?.createdAt || "") || 0;
  return rows.sort((left, right) => timestamp(right) - timestamp(left)).slice(0, 8);
}

function renderWorkflowPrimaryOverview(container, subject, dashboard, report, actions) {
  const section = document.createElement("section");
  const heading = document.createElement("div");
  const title = document.createElement("h4");
  const count = document.createElement("span");
  const list = document.createElement("div");
  const rows = workflowPrimaryReportRows(subject, dashboard, report);
  const primaryCopy = WORKFLOW_DASHBOARD_PRIMARY_TABS[subject?.id] || {};
  section.className = "workflow-primary-overview";
  heading.className = "workflow-primary-overview-heading";
  title.textContent = primaryCopy.overviewTitleTh || "ข้อมูลพร้อมทำงานและผลล่าสุด";
  count.textContent = `${rows.length} รายการ`;
  heading.append(title, count);
  list.className = "workflow-primary-report-list";
  if (rows.length) {
    rows.forEach((row) => {
      const card = document.createElement("button");
      const meta = document.createElement("span");
      const titleNode = document.createElement("strong");
      const summary = document.createElement("span");
      card.type = "button";
      card.className = "workflow-primary-report-card";
      meta.textContent = row._workflowPrimaryKind === "source"
        ? `ข้อมูลจาก ${displayPropName(row.sourcePropId, "Agent")} • ${displayStatus(row.status)}`
        : `ผลล่าสุด • ${displayStatus(row.status)}`;
      titleNode.textContent = safeDashboardDisplayText(row.title, "รายงานจาก Agent");
      summary.textContent = safeDashboardDisplayText(row.summary, "กดเพื่อดูรายละเอียดและหลักฐาน");
      card.append(meta, titleNode, summary);
      card.addEventListener("click", () => openDashboardResultDetail(
        findWorkflowCurrentPropReportProjection(row, subject.id),
        card,
      ));
      list.appendChild(card);
    });
  } else {
    const empty = document.createElement("div");
    const copy = document.createElement("p");
    const primaryAction = actions[0] || null;
    empty.className = "workflow-primary-empty";
    copy.textContent = "ยังไม่มีผลล่าสุดจาก Local Runner";
    copy.textContent = primaryCopy.emptyMessageTh || copy.textContent;
    empty.appendChild(copy);
    if (primaryAction) {
      const cta = document.createElement("button");
      cta.type = "button";
      cta.className = "modal-action primary workflow-primary-empty-cta";
      cta.textContent = primaryAction.labelTh;
      cta.addEventListener("click", () => {
        const form = container.querySelector(`[data-workflow-action-form="${primaryAction.id}"]`);
        (form?.querySelector("input, select, textarea, button:not([disabled])") || form)?.focus();
      });
      empty.appendChild(cta);
    }
    list.appendChild(empty);
  }
  section.append(heading, list);
  container.appendChild(section);
  return rows.length > 0;
}

function findWorkflowCurrentPropReportProjection(source = {}, propId = state.modal.id) {
  const reportId = String(source.reportId || source.id || "").trim();
  if (!reportId) return source;
  const reports = Array.isArray(state.propReports?.[propId]?.reports)
    ? state.propReports[propId].reports
    : [];
  return reports.find((report) => String(report?.id || "") === reportId) || source;
}

function getSafeExternalHttpUrl(value) {
  const raw = String(value || "").trim();
  if (!raw) return "";
  try {
    const parsed = new URL(raw, window.location.href);
    if (!["http:", "https:"].includes(parsed.protocol) || parsed.username || parsed.password) return "";
    return parsed.href;
  } catch {
    return "";
  }
}

function workflowDomainObject(...values) {
  return values.find((value) => value && typeof value === "object" && !Array.isArray(value)) || {};
}

function workflowDomainArray(...values) {
  return values.find((value) => Array.isArray(value)) || [];
}

function workflowReportRows(report, types) {
  const accepted = new Set(Array.isArray(types) ? types : [types]);
  return (Array.isArray(report?.reports) ? report.reports : [])
    .filter((item) => item && accepted.has(String(item.type || "")));
}

function normalizeIndicatorScoutDomain(backend = {}, report = {}) {
  const root = workflowDomainObject(
    backend.indicatorScout,
    backend.indicatorScoutData,
    backend.domainData?.indicatorScout,
    report.indicatorScout,
  );
  const reports = workflowReportRows(report, "indicator_scout_report");
  const candidates = [...workflowDomainArray(root.discoveries, root.items, root.indicators)];
  reports.forEach((item) => {
    const structured = workflowDomainArray(item.metrics?.discoveries, item.metrics?.items, item.findings)
      .filter((finding) => finding && typeof finding === "object" && !Array.isArray(finding));
    if (structured.length) candidates.push(...structured.map((finding) => ({ ...finding, reportId: item.id })));
    else candidates.push({
      id: item.id,
      reportId: item.id,
      title: item.title,
      summary: item.summary,
      updatedAt: item.updatedAt || item.createdAt,
      sourceUrl: item.evidence?.[0]?.url,
      sourceLabel: item.evidence?.[0]?.label,
      dedupStatus: item.metrics?.dedupStatus || item.metrics?.duplicateStatus,
    });
  });
  const seen = new Set();
  const discoveries = candidates.slice(0, 100).map((item, index) => {
    const evidence = workflowDomainArray(item?.evidence, item?.sources);
    const sourceUrl = getSafeExternalHttpUrl(item?.sourceUrl || item?.url || evidence[0]?.url);
    const title = safeDashboardDisplayText(item?.title || item?.name || item?.indicatorName, `Indicator รายการที่ ${index + 1}`);
    const key = String(item?.id || item?.discoveryId || sourceUrl || title).trim().toLowerCase();
    if (!key || seen.has(key)) return null;
    seen.add(key);
    return {
      id: safeDashboardDisplayText(item?.id || item?.discoveryId, `indicator-${index + 1}`),
      reportId: String(item?.reportId || ""),
      title,
      summary: safeDashboardDisplayText(item?.summary || item?.description, "ยังไม่มีบทสรุปเพิ่มเติมจาก Backend"),
      sourceUrl,
      sourceLabel: safeDashboardDisplayText(item?.sourceLabel || evidence[0]?.label, sourceUrl ? "เปิดแหล่งต้นทาง" : "ยังไม่มี URL จาก Backend"),
      discoveredAt: item?.discoveredAt || item?.checkedAt || item?.updatedAt || null,
      publishedAt: item?.publishedAt || item?.sourcePublishedAt || null,
      dedupStatus: safeDashboardDisplayText(item?.dedupStatus || item?.duplicateStatus, "รอผลตรวจรายการซ้ำจาก Backend"),
      platform: safeDashboardDisplayText(item?.platform, "ยังไม่ระบุแพลตฟอร์ม"),
    };
  }).filter(Boolean);
  return {
    discoveries,
    reports,
    schedule: workflowDomainObject(root.schedule, backend.schedule),
    screenshotAdapter: {
      status: "coming_soon",
      labelTh: "Screenshot Adapter: Coming Soon",
      detailTh: "ยังไม่มี Adapter จับภาพจริง จึงไม่แสดงภาพจำลองหรืออ้างว่ามี Screenshot แล้ว",
    },
  };
}

function normalizeFxBiasValue(value) {
  const normalized = String(value || "").trim().toLowerCase().replace(/[\s_-]+/g, "");
  if (["bullish", "buy", "up", "positive", "ขาขึ้น"].includes(normalized)) return "bullish";
  if (["bearish", "sell", "down", "negative", "ขาลง"].includes(normalized)) return "bearish";
  if (["sideway", "sideways", "neutral", "hold", "flat", "แกว่งตัว"].includes(normalized)) return "sideway";
  return "unavailable";
}

function normalizeFxNewsBiasDomain(backend = {}, report = {}) {
  const reports = workflowReportRows(report, "fx_news_bias_report");
  const latestMetrics = workflowDomainObject(reports[0]?.metrics);
  const root = workflowDomainObject(
    backend.fxNewsBias,
    backend.marketNewsBias,
    backend.domainData?.fxNewsBias,
    report.fxNewsBias,
    latestMetrics,
  );
  const rawNews = workflowDomainArray(root.news, root.events, root.highImpactNews, latestMetrics.news, latestMetrics.events);
  const news = rawNews.slice(0, 80).map((item, index) => ({
    id: safeDashboardDisplayText(item?.id, `news-${index + 1}`),
    title: safeDashboardDisplayText(item?.title || item?.event || item?.name, `ข่าวรายการที่ ${index + 1}`),
    summary: safeDashboardDisplayText(item?.summary || item?.impactSummary || item?.detail, "ยังไม่มีบทสรุปจาก Backend"),
    impact: safeDashboardDisplayText(item?.impact || item?.importance, "ยังไม่ระบุผลกระทบ"),
    eventAt: item?.eventAt || item?.publishedAt || item?.time || null,
    sourceUrl: getSafeExternalHttpUrl(item?.sourceUrl || item?.url || item?.evidence?.[0]?.url),
    sourceLabel: safeDashboardDisplayText(item?.sourceLabel || item?.source, "เปิดแหล่งข่าว"),
  }));
  const rawDanger = workflowDomainArray(root.dangerWindows, root.eaCautionWindows, root.riskWindows, latestMetrics.dangerWindows);
  const dangerWindows = rawDanger.slice(0, 40).map((item, index) => ({
    id: safeDashboardDisplayText(item?.id, `window-${index + 1}`),
    title: safeDashboardDisplayText(item?.title || item?.label, `ช่วงเฝ้าระวังที่ ${index + 1}`),
    startAt: item?.startAt || item?.start || null,
    endAt: item?.endAt || item?.end || null,
    reason: safeDashboardDisplayText(item?.reason || item?.summary, "รอเหตุผลจาก Backend"),
  }));
  const rawPairs = root.pairBias || root.pairs || latestMetrics.pairBias || latestMetrics.pairs || {};
  const rows = Array.isArray(rawPairs)
    ? rawPairs
    : Object.entries(rawPairs && typeof rawPairs === "object" ? rawPairs : {}).map(([pair, value]) => ({
        pair,
        ...(value && typeof value === "object" ? value : { bias: value }),
      }));
  const pairMap = new Map();
  rows.forEach((item) => {
    const pair = String(item?.pair || item?.symbol || "").trim().toUpperCase();
    if (!FX_BIAS_PAIR_UNIVERSE.includes(pair)) return;
    pairMap.set(pair, {
      pair,
      bias: normalizeFxBiasValue(item?.bias || item?.overall),
      short: normalizeFxBiasValue(item?.short || item?.shortTerm || item?.horizons?.short),
      medium: normalizeFxBiasValue(item?.medium || item?.mediumTerm || item?.horizons?.medium),
      long: normalizeFxBiasValue(item?.long || item?.longTerm || item?.horizons?.long),
      summary: safeDashboardDisplayText(item?.summary || item?.reason, ""),
      updatedAt: item?.updatedAt || item?.observedAt || null,
      sourceUrl: getSafeExternalHttpUrl(item?.sourceUrl || item?.url || item?.evidence?.[0]?.url),
    });
  });
  return {
    news,
    dangerWindows,
    pairBias: FX_BIAS_PAIR_UNIVERSE.map((pair) => pairMap.get(pair) || {
      pair,
      bias: "unavailable",
      short: "unavailable",
      medium: "unavailable",
      long: "unavailable",
      summary: "รอข้อมูลจริงจาก Backend",
      updatedAt: null,
      sourceUrl: "",
    }),
    reports,
    schedule: workflowDomainObject(root.schedule, backend.schedule),
  };
}

function normalizeVpsHqDomain(backend = {}, report = {}) {
  const reports = workflowReportRows(report, ["ops_overview_report", "vps_report"]);
  const latestMetrics = workflowDomainObject(reports[0]?.metrics);
  const root = workflowDomainObject(
    backend.vpsHqStatus,
    backend.opsOverview,
    backend.health,
    backend.domainData?.vpsHqStatus,
    report.vpsHqStatus,
    latestMetrics,
  );
  const rawVps = workflowDomainArray(root.vps, root.servers, root.nodes, latestMetrics.vps, latestMetrics.servers);
  const vps = rawVps.slice(0, 40).map((item, index) => ({
    id: safeDashboardDisplayText(item?.id || item?.name, `vps-${index + 1}`),
    name: safeDashboardDisplayText(item?.name || item?.label, `VPS ${index + 1}`),
    status: safeDashboardDisplayText(item?.status, "ยังไม่ทราบสถานะ"),
    uptime: safeDashboardDisplayText(item?.uptime || item?.uptimePercent, "ยังไม่มีข้อมูล"),
    latency: safeDashboardDisplayText(item?.latency || item?.latencyMs, "ยังไม่มีข้อมูล"),
    cpu: safeDashboardDisplayText(item?.cpu || item?.cpuPercent, "ยังไม่มีข้อมูล"),
    ram: safeDashboardDisplayText(item?.ram || item?.ramPercent || item?.memoryPercent, "ยังไม่มีข้อมูล"),
    checkedAt: item?.checkedAt || item?.updatedAt || null,
  }));
  const bridge = workflowDomainObject(root.hqBridge, root.bridge, report.bridge);
  const agentPreferences = workflowDomainObject(root.agentPreferences, backend.agentPreferences);
  return { vps, bridge, agentPreferences, reports };
}

function normalizeWorkflowDomainData(propId, backend = {}, report = {}) {
  if (propId === "left_audit_crystals") return { indicatorScout: normalizeIndicatorScoutDomain(backend, report) };
  if (propId === "left_signal_cube") return { fxNewsBias: normalizeFxNewsBiasDomain(backend, report) };
  if (propId === "right_status_crystals") return { vpsHqStatus: normalizeVpsHqDomain(backend, report) };
  return {};
}

function createWorkflowExternalSource(url, label = "เปิดแหล่งข้อมูล") {
  const safeUrl = getSafeExternalHttpUrl(url);
  if (!safeUrl) return null;
  const link = document.createElement("a");
  link.className = "workflow-external-link";
  link.href = safeUrl;
  link.target = "_blank";
  link.rel = "noopener noreferrer";
  link.textContent = label;
  return link;
}

function createWorkflowTruthEmpty(message = "ยังไม่มีข้อมูลจริงจาก Backend") {
  const note = document.createElement("p");
  note.className = "workflow-empty-message workflow-truth-empty";
  note.textContent = message;
  return note;
}

function workflowBiasLabel(value) {
  return {
    bullish: "Bullish",
    bearish: "Bearish",
    sideway: "Sideway",
    unavailable: "รอข้อมูล",
  }[value] || "รอข้อมูล";
}

function renderIndicatorScoutPanel(container, tabId, domain) {
  const section = document.createElement("section");
  section.className = "workflow-domain-panel workflow-indicator-scout";
  if (tabId === "discoveries") {
    const grid = document.createElement("div");
    grid.className = "workflow-indicator-grid";
    domain.discoveries.forEach((item) => {
      const card = document.createElement("article");
      const heading = document.createElement("div");
      const title = document.createElement("h5");
      const badge = document.createElement("span");
      const summary = document.createElement("p");
      const meta = document.createElement("dl");
      card.className = "workflow-indicator-card";
      heading.className = "workflow-domain-card-heading";
      title.textContent = item.title;
      badge.textContent = item.platform;
      summary.textContent = item.summary;
      [
        ["วันที่ค้นพบ", item.discoveredAt ? formatThaiDateTime(item.discoveredAt) : "ยังไม่มีวันที่จาก Backend"],
        ["วันที่เผยแพร่", item.publishedAt ? formatThaiDateTime(item.publishedAt) : "ยังไม่ระบุ"],
        ["ตรวจรายการซ้ำ", item.dedupStatus],
      ].forEach(([term, value]) => {
        const dt = document.createElement("dt");
        const dd = document.createElement("dd");
        dt.textContent = term;
        dd.textContent = value;
        meta.append(dt, dd);
      });
      heading.append(title, badge);
      card.append(heading, summary, meta);
      const source = createWorkflowExternalSource(item.sourceUrl, item.sourceLabel);
      if (source) card.appendChild(source);
      else card.appendChild(createWorkflowTruthEmpty("ยังไม่มี URL ต้นทางที่ Backend ส่งมา"));
      if (item.reportId) {
        const detail = document.createElement("button");
        detail.type = "button";
        detail.className = "workflow-card-detail";
        detail.textContent = "เปิดรายงานฉบับเต็ม";
        detail.addEventListener("click", () => openDashboardResultDetail(findWorkflowCurrentPropReportProjection({ reportId: item.reportId, ...item }), detail));
        card.appendChild(detail);
      }
      grid.appendChild(card);
    });
    section.appendChild(domain.discoveries.length ? grid : createWorkflowTruthEmpty());
  } else if (tabId === "evidence") {
    const notice = document.createElement("article");
    const title = document.createElement("h5");
    const detail = document.createElement("p");
    notice.className = "workflow-adapter-notice";
    notice.dataset.tone = "coming-soon";
    title.textContent = domain.screenshotAdapter.labelTh;
    detail.textContent = domain.screenshotAdapter.detailTh;
    notice.append(title, detail);
    section.appendChild(notice);
    const sources = domain.discoveries
      .filter((item) => item.sourceUrl)
      .map((item) => ({ url: item.sourceUrl, label: item.title, note: item.sourceLabel }));
    appendDashboardSourceLinks(section, sources);
    if (!sources.length) section.appendChild(createWorkflowTruthEmpty("ยังไม่มี URL หลักฐานจาก Backend และไม่มีภาพจำลอง"));
  } else if (tabId === "schedule") {
    const note = document.createElement("p");
    note.className = "workflow-schedule-note";
    const times = Array.isArray(domain.schedule?.times) ? domain.schedule.times.join(", ") : "ยังไม่ได้กำหนด";
    note.textContent = `เวลาที่บันทึกไว้: ${times || "ยังไม่ได้กำหนด"} • Scheduler และ Screenshot Adapter ยังไม่ทำงานอัตโนมัติ`;
    section.appendChild(note);
  } else {
    if (!domain.reports.length) section.appendChild(createWorkflowTruthEmpty("ยังไม่มีรายงาน Indicator Scout ย้อนหลัง"));
    else renderWorkflowSourceCards(section, domain.reports.map((item) => ({
      reportId: item.id,
      sourcePropId: item.linkedPropId,
      title: item.title,
      summary: item.summary,
      status: item.status,
    })));
  }
  container.appendChild(section);
}

function renderFxBiasTable(container, rows, { horizons = false } = {}) {
  const scroll = document.createElement("div");
  const table = document.createElement("table");
  const head = document.createElement("thead");
  const body = document.createElement("tbody");
  const headings = horizons
    ? ["คู่เงิน", "ระยะสั้น", "ระยะกลาง", "ระยะยาว", "หลักฐาน"]
    : ["คู่เงิน", "แนวโน้มรวม", "สรุป", "อัปเดต", "หลักฐาน"];
  scroll.className = "workflow-table-scroll";
  table.className = "workflow-domain-table workflow-fx-bias-table";
  const headRow = document.createElement("tr");
  headings.forEach((heading) => {
    const th = document.createElement("th");
    th.scope = "col";
    th.textContent = heading;
    headRow.appendChild(th);
  });
  head.appendChild(headRow);
  rows.forEach((item) => {
    const row = document.createElement("tr");
    const pair = document.createElement("th");
    pair.scope = "row";
    pair.textContent = item.pair;
    row.appendChild(pair);
    if (horizons) {
      [item.short, item.medium, item.long].forEach((bias) => {
        const cell = document.createElement("td");
        const badge = document.createElement("span");
        badge.className = "workflow-bias-badge";
        badge.dataset.bias = bias;
        badge.textContent = workflowBiasLabel(bias);
        cell.appendChild(badge);
        row.appendChild(cell);
      });
    } else {
      const biasCell = document.createElement("td");
      const badge = document.createElement("span");
      const summary = document.createElement("td");
      const updated = document.createElement("td");
      badge.className = "workflow-bias-badge";
      badge.dataset.bias = item.bias;
      badge.textContent = workflowBiasLabel(item.bias);
      biasCell.appendChild(badge);
      summary.textContent = item.summary || "รอข้อมูลจริงจาก Backend";
      updated.textContent = item.updatedAt ? formatThaiDateTime(item.updatedAt) : "รอข้อมูล";
      row.append(biasCell, summary, updated);
    }
    const sourceCell = document.createElement("td");
    const source = createWorkflowExternalSource(item.sourceUrl, "เปิดแหล่งข้อมูล");
    sourceCell.appendChild(source || document.createTextNode("รอข้อมูล"));
    row.appendChild(sourceCell);
    body.appendChild(row);
  });
  table.append(head, body);
  scroll.appendChild(table);
  container.appendChild(scroll);
}

function renderFxNewsBiasPanel(container, tabId, domain) {
  const section = document.createElement("section");
  section.className = "workflow-domain-panel workflow-fx-news-bias";
  if (tabId === "today") {
    const dangerTitle = document.createElement("h5");
    dangerTitle.textContent = "ช่วงเวลาที่ EA ควรระวัง";
    section.appendChild(dangerTitle);
    if (!domain.dangerWindows.length) section.appendChild(createWorkflowTruthEmpty("ยังไม่มีช่วงเวลาเฝ้าระวังจาก Backend"));
    else {
      const dangerGrid = document.createElement("div");
      dangerGrid.className = "workflow-danger-grid";
      domain.dangerWindows.forEach((item) => {
        const card = document.createElement("article");
        const title = document.createElement("strong");
        const time = document.createElement("span");
        const reason = document.createElement("p");
        title.textContent = item.title;
        time.textContent = `${item.startAt ? formatThaiDateTime(item.startAt) : "ยังไม่ระบุเวลาเริ่ม"} — ${item.endAt ? formatThaiDateTime(item.endAt) : "ยังไม่ระบุเวลาสิ้นสุด"}`;
        reason.textContent = item.reason;
        card.append(title, time, reason);
        dangerGrid.appendChild(card);
      });
      section.appendChild(dangerGrid);
    }
    const newsTitle = document.createElement("h5");
    newsTitle.textContent = "ข่าวและเหตุการณ์จากแหล่งจริง";
    section.appendChild(newsTitle);
    if (!domain.news.length) section.appendChild(createWorkflowTruthEmpty("ยังไม่มีข่าวจริงจาก Backend จึงไม่แสดงข่าวจำลอง"));
    else {
      const newsGrid = document.createElement("div");
      newsGrid.className = "workflow-news-grid";
      domain.news.forEach((item) => {
        const card = document.createElement("article");
        const meta = document.createElement("span");
        const title = document.createElement("h5");
        const summary = document.createElement("p");
        meta.textContent = `${item.impact} • ${item.eventAt ? formatThaiDateTime(item.eventAt) : "ยังไม่ระบุเวลา"}`;
        title.textContent = item.title;
        summary.textContent = item.summary;
        card.append(meta, title, summary);
        const source = createWorkflowExternalSource(item.sourceUrl, item.sourceLabel);
        if (source) card.appendChild(source);
        newsGrid.appendChild(card);
      });
      section.appendChild(newsGrid);
    }
  } else if (tabId === "pair_bias") {
    renderFxBiasTable(section, domain.pairBias);
  } else if (tabId === "horizons") {
    renderFxBiasTable(section, domain.pairBias, { horizons: true });
  } else {
    const note = document.createElement("p");
    note.className = "workflow-schedule-note";
    const times = Array.isArray(domain.schedule?.times) ? domain.schedule.times.join(", ") : "ยังไม่ได้กำหนด";
    note.textContent = `เวลาที่บันทึกไว้: ${times || "ยังไม่ได้กำหนด"} • ระบบไม่สร้างข่าวหรือ Bias จำลองเมื่อแหล่งข้อมูลยังไม่พร้อม`;
    section.appendChild(note);
    if (domain.reports.length) renderWorkflowSourceCards(section, domain.reports.map((item) => ({
      reportId: item.id,
      sourcePropId: item.linkedPropId,
      title: item.title,
      summary: item.summary,
      status: item.status,
    })));
  }
  container.appendChild(section);
}

function renderTerminalOutputPanel(container, report = {}) {
  const section = document.createElement("section");
  const reports = workflowReportRows(report, ["ea_development_report", "ea_build_report", "ea_compile_report", "code_change_report"]);
  const artifacts = reports.flatMap((item) => item.safeAttachments || item.downloads || item.artifacts || item.attachments || []);
  section.className = "workflow-domain-panel workflow-terminal-outputs";
  const hasDownloads = appendDashboardArtifactLinks(section, artifacts);
  if (!hasDownloads) section.appendChild(createWorkflowTruthEmpty("ยังไม่มีไฟล์ที่ Backend อนุญาตให้ดาวน์โหลด"));
  if (reports.length) renderWorkflowSourceCards(section, reports.map((item) => ({
    reportId: item.id,
    sourcePropId: item.linkedPropId,
    title: item.title,
    summary: item.summary,
    status: item.status,
  })));
  container.appendChild(section);
}

function renderTerminalSourceCatalogPanel(container, dashboard) {
  const section = document.createElement("section");
  section.className = "workflow-domain-panel workflow-source-catalog";
  const heading = document.createElement("h5");
  heading.textContent = "Approved Workspace Source Catalog";
  section.appendChild(heading);
  if (!dashboard.workspaceSources.length) {
    section.appendChild(createWorkflowTruthEmpty(
      "ยังไม่มี Source ที่ Backend อนุญาต ให้นำ Source เข้า Workspace ผ่าน Backend ก่อน • Direct Import จากหน้าเว็บ: Coming Soon",
    ));
    container.appendChild(section);
    return;
  }
  const label = document.createElement("label");
  const select = document.createElement("select");
  const empty = document.createElement("option");
  label.className = "workflow-catalog-selector";
  label.textContent = "เลือก workspaceSourceId จาก Catalog";
  select.dataset.workflowCatalogSelector = "workspaceSourceId";
  empty.value = "";
  empty.textContent = "เลือก Source";
  select.appendChild(empty);
  dashboard.workspaceSources.forEach((source) => {
    const option = document.createElement("option");
    option.value = source.workspaceSourceId;
    option.textContent = `${source.title} • ${source.platform} • ${displayStatus(source.status)}`;
    select.appendChild(option);
  });
  select.addEventListener("change", () => {
    const target = container.querySelector('[data-workflow-field="workspaceSourceId"]');
    if (target instanceof HTMLSelectElement) {
      target.value = select.value;
      target.dispatchEvent(new Event("change", { bubbles: true }));
    }
  });
  label.appendChild(select);
  section.appendChild(label);
  const note = document.createElement("p");
  note.className = "workflow-schedule-note";
  note.textContent = "Catalog นี้มาจาก Backend เท่านั้น หน้าเว็บไม่รับการวาง Path และไม่มีช่องอัปโหลดไฟล์โดยตรง";
  section.appendChild(note);
  container.appendChild(section);
}

function renderVpsHqPanel(container, tabId, domain) {
  const section = document.createElement("section");
  section.className = "workflow-domain-panel workflow-vps-hq";
  if (tabId === "vps") {
    if (!domain.vps.length) section.appendChild(createWorkflowTruthEmpty("ยังไม่มีค่าตรวจ VPS จริงจาก Backend"));
    else {
      const grid = document.createElement("div");
      grid.className = "workflow-vps-grid";
      domain.vps.forEach((item) => {
        const card = document.createElement("article");
        const title = document.createElement("h5");
        const status = document.createElement("strong");
        const metrics = document.createElement("dl");
        title.textContent = item.name;
        status.textContent = item.status;
        [["Uptime", item.uptime], ["Latency", item.latency], ["CPU", item.cpu], ["RAM", item.ram]].forEach(([label, value]) => {
          const dt = document.createElement("dt");
          const dd = document.createElement("dd");
          dt.textContent = label;
          dd.textContent = value;
          metrics.append(dt, dd);
        });
        const checked = document.createElement("small");
        checked.textContent = item.checkedAt ? `ตรวจ ${formatThaiDateTime(item.checkedAt)}` : "Backend ยังไม่ส่งเวลาตรวจ";
        card.append(title, status, metrics, checked);
        grid.appendChild(card);
      });
      section.appendChild(grid);
    }
  } else if (tabId === "hq_bridge") {
    const facts = Object.entries(domain.bridge || {})
      .filter(([, value]) => ["string", "number", "boolean"].includes(typeof value))
      .slice(0, 20);
    if (!facts.length) section.appendChild(createWorkflowTruthEmpty("ยังไม่มีสถานะ HQ/Bridge ที่ Backend เปิดเผย"));
    else {
      const grid = document.createElement("dl");
      grid.className = "workflow-hq-facts";
      facts.forEach(([name, value]) => {
        const dt = document.createElement("dt");
        const dd = document.createElement("dd");
        dt.textContent = dashboardFieldLabel(name);
        dd.textContent = safeDashboardDisplayText(formatDashboardValue(value), "-");
        grid.append(dt, dd);
      });
      section.appendChild(grid);
    }
  } else if (tabId === "agent_settings") {
    const notice = document.createElement("article");
    const title = document.createElement("h5");
    const copy = document.createElement("p");
    notice.className = "workflow-adapter-notice";
    notice.dataset.tone = "ready";
    title.textContent = "ตั้งค่าเฉพาะ Preference ที่ปลอดภัย";
    copy.textContent = "หน้านี้ไม่รับ Token, API Key, Password, Cookie, Credential และไม่เปลี่ยนสิทธิ์ Tool หรือสิทธิ์ระบบของ Agent";
    notice.append(title, copy);
    section.appendChild(notice);
  } else {
    if (!domain.reports.length) section.appendChild(createWorkflowTruthEmpty("ยังไม่มีประวัติตรวจสถานะหรือเปลี่ยน Preference จาก Backend"));
    else renderWorkflowSourceCards(section, domain.reports.map((item) => ({
      reportId: item.id,
      sourcePropId: item.linkedPropId,
      title: item.title,
      summary: item.summary,
      status: item.status,
    })));
  }
  container.appendChild(section);
}

function renderWorkflowDomainPanel(container, subject, selectedTab, dashboard, report) {
  if (!container || !subject || !selectedTab) return false;
  if (subject.id === "left_audit_crystals") {
    renderIndicatorScoutPanel(container, selectedTab.id, dashboard.domainData.indicatorScout);
    return true;
  }
  if (subject.id === "left_signal_cube") {
    renderFxNewsBiasPanel(container, selectedTab.id, dashboard.domainData.fxNewsBias);
    return true;
  }
  if (subject.id === "terminal_workstation") {
    if (selectedTab.id === "source") {
      renderTerminalSourceCatalogPanel(container, dashboard);
      return true;
    }
    if (selectedTab.id === "outputs") {
      renderTerminalOutputPanel(container, report);
      return true;
    }
  }
  if (subject.id === "right_status_crystals") {
    renderVpsHqPanel(container, selectedTab.id, dashboard.domainData.vpsHqStatus);
    return true;
  }
  return false;
}

function renderWorkflowCatalog(container, dashboard) {
  const template = dashboard.sheetTemplate || normalizeWorkflowSheetTemplate();
  const deduplication = dashboard.deduplication || normalizeWorkflowDeduplication();
  const section = document.createElement("section");
  const statusGrid = document.createElement("div");
  const templateCard = document.createElement("article");
  const connectionCard = document.createElement("article");
  const templateHeading = document.createElement("div");
  const templateTitle = document.createElement("h4");
  const templateCount = document.createElement("strong");
  const templateReference = document.createElement("p");
  const columns = document.createElement("ol");
  const connectionTitle = document.createElement("h4");
  const connectionBadge = document.createElement("strong");
  const connectionCopy = document.createElement("p");
  const dedupTitle = document.createElement("h5");
  const dedupCopy = document.createElement("p");
  const dedupFields = document.createElement("div");
  const privacyCopy = document.createElement("p");
  const sheetsConnected = template.connectionStatus === "connected";

  section.className = "workflow-catalog";
  statusGrid.className = "workflow-catalog-grid";
  templateCard.className = "workflow-catalog-card workflow-catalog-template";
  connectionCard.className = "workflow-catalog-card workflow-catalog-connection";
  templateHeading.className = "workflow-catalog-card-heading";
  templateTitle.textContent = "แม่แบบคลังระบบเทรด";
  templateCount.textContent = `${template.columns.length} ช่อง`;
  templateReference.textContent = `แม่แบบอ้างอิง: ${template.templateReference}`;
  columns.className = "workflow-catalog-columns";
  template.columns.forEach((column, index) => {
    const item = document.createElement("li");
    const number = document.createElement("span");
    const code = document.createElement("code");
    number.textContent = String(index + 1);
    code.textContent = column;
    item.append(number, code);
    columns.appendChild(item);
  });
  templateHeading.append(templateTitle, templateCount);
  templateCard.append(templateHeading, templateReference, columns);

  connectionTitle.textContent = "การเชื่อม Google Sheets";
  connectionBadge.dataset.tone = sheetsConnected ? "ready" : "coming-soon";
  connectionBadge.textContent = sheetsConnected ? "Google Sheets เชื่อมแล้ว" : "Google Sheets: Coming Soon";
  connectionCopy.textContent = sheetsConnected
    ? template.connectionLabelTh
    : `${template.connectionLabelTh} • ระบบยังไม่อ่านหรือเขียนแถวใน Google Sheets`;
  dedupTitle.textContent = "การตรวจรายการซ้ำ";
  dedupCopy.textContent = deduplication.scopeLabelTh;
  dedupFields.className = "workflow-catalog-dedup-fields";
  template.deduplicationFields.forEach((field) => {
    const chip = document.createElement("code");
    chip.textContent = field;
    dedupFields.appendChild(chip);
  });
  privacyCopy.className = "workflow-catalog-privacy";
  privacyCopy.textContent = [
    deduplication.localReportCatalogAvailable
      ? "พร้อมตรวจรายการซ้ำกับ Report ในเครื่อง"
      : "ยังไม่ได้ยืนยัน Local Report Catalog",
    deduplication.googleSheetRowsAvailable
      ? "รวมข้อมูลจาก Google Sheets แล้ว"
      : "ยังไม่รวมข้อมูลจาก Google Sheets",
    "Frontend ไม่รับ Token, Credential หรือ Secret",
  ].join(" • ");
  connectionCard.append(
    connectionTitle,
    connectionBadge,
    connectionCopy,
    dedupTitle,
    dedupCopy,
    dedupFields,
    privacyCopy,
  );
  statusGrid.append(templateCard, connectionCard);
  section.appendChild(statusGrid);
  container.appendChild(section);
}

function getWorkflowDashboardEntries(subject, report = {}) {
  const missionMap = new Map();
  [
    ...getRelevantMissionsForSubject(subject, "prop"),
    ...(Array.isArray(report?.missions) ? report.missions : []),
  ].forEach((mission) => {
    if (!mission || getMissionPresentationStatus(mission) === "archived") return;
    missionMap.set(mission.id || `${mission.title}-${mission.createdAt || ""}`, mission);
  });
  const reportMap = new Map();
  (Array.isArray(report?.reports) ? report.reports : []).forEach((item) => {
    if (!item) return;
    reportMap.set(item.id || `${item.title}-${item.updatedAt || ""}`, item);
  });
  const entries = [
    ...[...missionMap.values()].map((item) => ({ kind: "mission", item })),
    ...[...reportMap.values()].map((item) => ({ kind: "report", item })),
  ];
  return {
    entries,
    grouped: {
      running: entries.filter(({ kind, item }) => getDashboardWorkState(item, kind) === "running"),
      completed: entries.filter(({ kind, item }) => getDashboardWorkState(item, kind) === "completed"),
      blocked: entries.filter(({ kind, item }) => getDashboardWorkState(item, kind) === "blocked"),
    },
  };
}

function renderWorkflowResults(subject, report = {}) {
  const { grouped } = getWorkflowDashboardEntries(subject, report);
  renderDashboardWorkColumn(els.workflowRunningList, grouped.running, "ยังไม่มีงานที่กำลังดำเนินการ");
  renderDashboardWorkColumn(els.workflowCompletedList, grouped.completed, "ยังไม่มีรายงานที่เสร็จแล้ว");
  renderDashboardWorkColumn(els.workflowBlockedList, grouped.blocked, "ยังไม่มีงานติดขัด");
  if (els.workflowRunningCount) els.workflowRunningCount.textContent = String(grouped.running.length);
  if (els.workflowCompletedCount) els.workflowCompletedCount.textContent = String(grouped.completed.length);
  if (els.workflowBlockedCount) els.workflowBlockedCount.textContent = String(grouped.blocked.length);
  if (els.workflowResultSummary) {
    els.workflowResultSummary.innerHTML = "";
    [
      ["running", "กำลังทำ", grouped.running.length],
      ["completed", "สำเร็จ", grouped.completed.length],
      ["blocked", "ติดขัด", grouped.blocked.length],
    ].forEach(([status, label, count]) => {
      const item = document.createElement("span");
      item.dataset.state = status;
      item.textContent = `${label} ${count}`;
      els.workflowResultSummary.appendChild(item);
    });
  }
}

function renderWorkflowActionStatus(propId) {
  if (!els.workflowActionStatus) return;
  const status = state.modal.workflowAction;
  const current = status.propId === propId && status.message;
  els.workflowActionStatus.dataset.tone = current ? status.tone : "neutral";
  els.workflowActionStatus.textContent = current
    ? status.message
    : "หน้าเว็บส่งเฉพาะคำขอ งานจริงและ Audit Log อยู่หลัง Local Runner";
}

function getWorkflowDashboardIdentity(propId) {
  return WORKFLOW_DASHBOARD_IDENTITIES[propId] || {
    id: "local-dashboard",
    mark: "HQ",
    labelTh: "LOCAL DASHBOARD",
    eyebrowTh: "Dashboard อิสระของอุปกรณ์",
    handoffAgentId: "manager",
  };
}

function renderWorkflowSettingsRail(subject, dashboard, identity = getWorkflowDashboardIdentity(subject?.id)) {
  if (!els.workflowSettingsRail || !els.workflowSettingsRailContent) return;
  const actions = (dashboard?.actions || []).filter((action) => WORKFLOW_DASHBOARD_SETTING_ACTION_IDS.has(action.id));
  els.workflowSettingsRail.hidden = !actions.length;
  els.workflowSettingsRail.dataset.dashboardIdentity = identity.id;
  els.workflowSettingsRailContent.innerHTML = "";
  actions.forEach((action) => {
    const card = createWorkflowActionCard(action, dashboard);
    card.classList.add("workflow-rail-action-card");
    els.workflowSettingsRailContent.appendChild(card);
  });
}

function getWorkflowHandoffReports(report = {}) {
  const seen = new Set();
  return (Array.isArray(report?.reports) ? report.reports : [])
    .map((item) => {
      const id = String(item?.id || "").trim();
      if (!/^[a-zA-Z0-9._:-]{1,160}$/.test(id) || seen.has(id)) return null;
      const type = String(item?.type || item?.reportType || "").trim();
      const status = String(item?.status || "").trim().toLowerCase();
      if (!/^[a-z0-9_]{1,120}$/.test(type) || !WORKFLOW_REPORT_TRANSFER_READY_STATUSES.has(status)) return null;
      seen.add(id);
      const platforms = new Set();
      const metrics = item?.metrics && typeof item.metrics === "object" ? item.metrics : {};
      const workflowContext = item?.workflowContext && typeof item.workflowContext === "object" ? item.workflowContext : {};
      const inputs = workflowContext?.inputs && typeof workflowContext.inputs === "object" ? workflowContext.inputs : {};
      const platformValues = [item?.platform, metrics?.platform, inputs?.platform]
        .concat(Array.isArray(item?.platforms) ? item.platforms : []);
      platformValues.forEach((value) => {
        const platform = String(value || "").trim().toLowerCase();
        if (["mt4", "mt5", "mql4", "mql5"].includes(platform)) platforms.add(platform);
      });
      (Array.isArray(item?.artifacts) ? item.artifacts : []).slice(0, 40).forEach((artifact) => {
        const value = typeof artifact === "string"
          ? artifact
          : String(artifact?.path || artifact?.file || artifact?.filePath || artifact?.href || "");
        const normalized = value.replaceAll("\\", "/").toLowerCase();
        if (normalized.endsWith(".mq4")) {
          platforms.add("mt4");
          platforms.add("mql4");
        } else if (normalized.endsWith(".mq5")) {
          platforms.add("mt5");
          platforms.add("mql5");
        }
      });
      return {
        id,
        title: safeDashboardDisplayText(item?.title, "Report จากอุปกรณ์นี้"),
        type,
        status,
        platforms: [...platforms],
      };
    })
    .filter(Boolean)
    .slice(0, 100);
}

function getWorkflowReportTransferRoutes(sourcePropId, report) {
  if (!report) return [];
  return WORKFLOW_REPORT_TRANSFER_ROUTES.filter((route) => {
    if (!route.sourcePropIds.includes(sourcePropId) || !route.reportTypes.includes(report.type)) return false;
    if (!Array.isArray(route.platforms) || !route.platforms.length) return true;
    return report.platforms.some((platform) => route.platforms.includes(platform));
  });
}

function getWorkflowTransferAction(route) {
  if (!route) return null;
  return (WORKFLOW_DASHBOARD_FALLBACKS[route.targetPropId]?.actions || [])
    .find((action) => action.id === route.actionId) || null;
}

function workflowHandoffFormSignature(propId, reportId, targetPropId, actionId) {
  return JSON.stringify({ propId, reportId, targetPropId, actionId });
}

function fillWorkflowHandoffSelect(select, rows, selectedValue, emptyLabel, labelForRow) {
  if (!select) return;
  select.innerHTML = "";
  if (!rows.length) {
    const option = document.createElement("option");
    option.value = "";
    option.textContent = emptyLabel;
    select.appendChild(option);
    select.value = "";
    return;
  }
  rows.forEach((row) => {
    const option = document.createElement("option");
    option.value = row.value;
    option.textContent = labelForRow(row);
    select.appendChild(option);
  });
  select.value = rows.some((row) => row.value === selectedValue) ? selectedValue : rows[0].value;
}

function renderWorkflowAgentHandoff(subject, report = {}, identity = getWorkflowDashboardIdentity(subject?.id)) {
  if (
    !els.workflowHandoffReport
    || !els.workflowHandoffTarget
    || !els.workflowHandoffAction
    || !els.workflowHandoffButton
    || !els.workflowHandoffStatus
  ) return;
  const reports = getWorkflowHandoffReports(report);
  const handoff = state.modal.workflowHandoff;
  const current = handoff.propId === subject.id;
  const selectedReportId = current && reports.some((item) => item.id === handoff.reportId)
    ? handoff.reportId
    : (reports[0]?.id || "");
  const selectedReport = reports.find((item) => item.id === selectedReportId) || null;
  const compatibleRoutes = getWorkflowReportTransferRoutes(subject.id, selectedReport);
  const targetRows = [...new Map(compatibleRoutes.map((route) => [route.targetPropId, {
    value: route.targetPropId,
    route,
  }])).values()];
  const selectedTargetPropId = current && targetRows.some((item) => item.value === handoff.targetPropId)
    ? handoff.targetPropId
    : (targetRows[0]?.value || "");
  const actionRoutes = compatibleRoutes.filter((route) => route.targetPropId === selectedTargetPropId);
  const actionRows = actionRoutes.map((route) => ({ value: route.actionId, route }));
  const selectedActionId = current && actionRows.some((item) => item.value === handoff.actionId)
    ? handoff.actionId
    : (actionRows[0]?.value || "");
  const selectedRoute = actionRoutes.find((route) => route.actionId === selectedActionId) || null;
  if (els.workflowAgentHandoffRail) {
    els.workflowAgentHandoffRail.hidden = !selectedRoute;
    els.workflowAgentHandoffRail.dataset.dashboardIdentity = identity.id;
  }
  const agentName = selectedRoute ? displayAgentName(selectedRoute.agentId, "Agent ผู้รับงาน") : "Agent ผู้รับงาน";
  const formSignature = selectedRoute
    ? workflowHandoffFormSignature(subject.id, selectedReportId, selectedTargetPropId, selectedActionId)
    : "";
  const submittedCurrentForm = current && formSignature && handoff.formSignature === formSignature;
  const inFlight = current && handoff.inFlight;
  const alreadyRecorded = submittedCurrentForm && handoff.tone === "success";

  fillWorkflowHandoffSelect(
    els.workflowHandoffReport,
    reports.map((item) => ({ value: item.id, report: item })),
    selectedReportId,
    "ยังไม่มี Report ที่พร้อมส่งต่อ",
    ({ report: item }) => `${item.title} • ${displayStatus(item.status)}`,
  );
  fillWorkflowHandoffSelect(
    els.workflowHandoffTarget,
    targetRows,
    selectedTargetPropId,
    "ไม่มีอุปกรณ์ปลายทางที่รับ Report นี้",
    ({ value }) => displayPropName(value),
  );
  fillWorkflowHandoffSelect(
    els.workflowHandoffAction,
    actionRows,
    selectedActionId,
    "ไม่มีงานปลายทางที่รับ Report นี้",
    ({ route }) => getWorkflowTransferAction(route)?.labelTh || route.actionId,
  );

  els.workflowHandoffReport.disabled = !reports.length || inFlight;
  els.workflowHandoffTarget.disabled = !targetRows.length || inFlight;
  els.workflowHandoffAction.disabled = !actionRows.length || inFlight;
  els.workflowHandoffButton.disabled = !selectedRoute || inFlight || alreadyRecorded;
  els.workflowHandoffButton.textContent = inFlight
    ? `กำลังให้ ${agentName} ส่งต่อ Report...`
    : (alreadyRecorded ? "ส่งต่อ Report นี้แล้ว" : `มอบหมาย ${agentName} ให้ส่งต่อ Report`);
  els.workflowHandoffStatus.dataset.tone = current ? handoff.tone : "neutral";
  els.workflowHandoffStatus.textContent = current && handoff.message
    ? handoff.message
    : (!reports.length
        ? "ยังไม่มี Report ที่ Backend ยืนยันว่าพร้อมใช้งาน จึงยังสร้าง Mission ส่งต่อไม่ได้"
        : (!selectedRoute
            ? "Report นี้ไม่มีเส้นทางปลายทางที่ Backend อนุญาตตามชนิด สถานะ หรือแพลตฟอร์ม ระบบจึงปิดปุ่มไว้เพื่อป้องกันการส่งผิด"
            : `เลือกปลายทางแล้วให้ ${agentName} ส่ง Report ผ่าน Mission • เป็นการบันทึกการส่งต่อเท่านั้น ยังไม่เริ่มงานปลายทางและไม่เปิดอุปกรณ์อื่นอัตโนมัติ`));

  if (
    !current
    || handoff.reportId !== selectedReportId
    || handoff.targetPropId !== selectedTargetPropId
    || handoff.actionId !== selectedActionId
  ) {
    state.modal.workflowHandoff = {
      ...handoff,
      propId: subject.id,
      reportId: selectedReportId,
      targetPropId: selectedTargetPropId,
      actionId: selectedActionId,
      message: current ? handoff.message : "",
      tone: current ? handoff.tone : "neutral",
    };
  }
}

function workflowHandoffErrorMessage(error) {
  if (error?.status === 404) return "ไม่พบอุปกรณ์ปลายทางใน Backend กรุณารีเฟรชหน้าและตรวจเวอร์ชัน Local Runner";
  if (error?.status === 409) return "Backend พบคำขอซ้ำที่รายละเอียดไม่ตรงกัน กรุณาเปลี่ยน Report หรืองานปลายทางแล้วลองใหม่";
  if (error?.status === 422) {
    return "Backend ไม่อนุญาตการส่งต่อนี้ กรุณาตรวจชนิดและสถานะ Report, Mission ต้นทาง และแพลตฟอร์มของไฟล์";
  }
  return error?.message || "ติดต่อ Local Runner ไม่สำเร็จ";
}

async function submitWorkflowAgentHandoff() {
  const subject = getModalSubject();
  if (!subject || !isWorkflowDashboardPropId(subject.id) || state.modal.workflowHandoff.inFlight) return;
  const report = state.propReports[subject.id] || {};
  const reports = getWorkflowHandoffReports(report);
  const reportId = String(els.workflowHandoffReport?.value || "").trim();
  const targetPropId = String(els.workflowHandoffTarget?.value || "").trim();
  const actionId = String(els.workflowHandoffAction?.value || "").trim();
  const selectedReport = reports.find((item) => item.id === reportId);
  const selectedRoute = getWorkflowReportTransferRoutes(subject.id, selectedReport)
    .find((route) => route.targetPropId === targetPropId && route.actionId === actionId);
  if (!selectedReport || !selectedRoute) {
    state.modal.workflowHandoff = {
      inFlight: false,
      propId: subject.id,
      reportId,
      targetPropId,
      actionId,
      idempotencyKey: "",
      formSignature: "",
      message: "ยังส่งต่อไม่ได้ เพราะ Report หรือเส้นทางปลายทางไม่ตรงกับรายการที่ Backend อนุญาต",
      tone: "error",
    };
    renderGameModal();
    return;
  }

  const agentName = displayAgentName(selectedRoute.agentId, "Agent ผู้รับงาน");
  const previousHandoff = state.modal.workflowHandoff;
  const formSignature = workflowHandoffFormSignature(subject.id, reportId, targetPropId, actionId);
  const idempotencyKey = previousHandoff.tone === "error"
    && previousHandoff.formSignature === formSignature
    && previousHandoff.idempotencyKey
    ? previousHandoff.idempotencyKey
    : createWorkflowIdempotencyKey();
  state.modal.workflowHandoff = {
    inFlight: true,
    propId: subject.id,
    reportId,
    targetPropId,
    actionId,
    idempotencyKey,
    formSignature,
    message: `กำลังให้ Backend ตรวจ Report และบันทึก Mission ส่งต่อแก่ ${agentName}`,
    tone: "working",
  };
  renderGameModal();
  try {
    const result = await postJson(`/api/props/${encodeURIComponent(targetPropId)}/workflow/transfers`, {
      actionId,
      sourceReportId: reportId,
      idempotencyKey,
    });
    const transfer = result?.agentTransfer;
    const mission = result?.mission;
    if (
      result?.ok !== true
      || result?.kind !== "agent_report_transfer_recorded"
      || !mission?.id
      || transfer?.sourceReportId !== reportId
      || transfer?.targetPropId !== targetPropId
    ) {
      throw new Error("Backend ยังไม่ได้ยืนยันการบันทึก Mission ส่งต่อ Report");
    }
    mergeBackendMission(mission);
    await Promise.all([loadPropReport(subject.id), loadPropReport(targetPropId)]);
    const transferAgentId = transfer.transferAgentId || mission.owner || selectedRoute.agentId;
    routeAgentToTargetId(transferAgentId, targetPropId, "ส่งต่อ Report ผ่าน Mission", {
      select: false,
    });
    recordOfficeEvent(
      "Agent ส่งต่อ Report แล้ว",
      `${selectedReport.title} → ${displayPropName(targetPropId)} • Mission ${mission.id}`,
      {
        agentId: transferAgentId,
        kind: "workflow.report_transferred",
        missionId: mission.id,
        targetId: targetPropId,
        persist: false,
        bridgeEvent: false,
      },
    );
    state.modal.workflowHandoff.message = `Backend บันทึก Mission ${mission.id} แล้ว • ${displayAgentName(transferAgentId, agentName)} ส่ง Report ไปยัง ${displayPropName(targetPropId)} สำเร็จ • ยังไม่ได้เริ่มงานปลายทาง`;
    state.modal.workflowHandoff.tone = "success";
  } catch (error) {
    state.modal.workflowHandoff.message = `ส่งต่อยังไม่สำเร็จ: ${workflowHandoffErrorMessage(error)}`;
    state.modal.workflowHandoff.tone = "error";
  } finally {
    state.modal.workflowHandoff.inFlight = false;
    if (state.modal.open && state.modal.id === subject.id) renderGameModal();
  }
}

function renderWorkflowDashboard(subject, propertyRole, report = {}) {
  if (!subject || !isWorkflowDashboardPropId(subject.id)) return;
  const dashboard = normalizeWorkflowDashboard(subject, propertyRole, report);
  const selectedTab = getWorkflowSelectedTab(subject.id, dashboard);
  const identity = getWorkflowDashboardIdentity(subject.id);
  const isPrimaryTab = selectedTab?.id === dashboard.tabs[0]?.id;
  const isHistoryTab = selectedTab?.id === dashboard.tabs.at(-1)?.id;
  if (selectedTab) state.modal.workflowTabs[subject.id] = selectedTab.id;
  if (els.modalWorkflowDashboardWorkspace) {
    els.modalWorkflowDashboardWorkspace.dataset.dashboardIdentity = identity.id;
  }
  if (els.modalPortraitPanel) els.modalPortraitPanel.dataset.dashboardIdentity = identity.id;
  renderWorkflowSettingsRail(subject, dashboard, identity);
  renderWorkflowAgentHandoff(subject, report, identity);
  renderWorkflowTabs(subject.id, dashboard, selectedTab);
  if (els.workflowResultsPanel) {
    els.workflowResultsPanel.hidden = !isHistoryTab;
    els.workflowResultsPanel.dataset.mode = "history";
  }
  if (els.workflowResultsEyebrow) els.workflowResultsEyebrow.textContent = "ข้อมูลย้อนหลัง";
  if (els.workflowResultsTitle) els.workflowResultsTitle.textContent = "ประวัติและรายงาน";
  if (els.workflowResultsCopy) {
    els.workflowResultsCopy.textContent = "กดรายการเพื่อดูรายละเอียด Mission, Report และหลักฐานย้อนหลัง";
  }
  if (els.workflowDashboardContent) {
    els.workflowDashboardContent.innerHTML = "";
    els.workflowDashboardContent.hidden = false;
    if (!isPrimaryTab && !isHistoryTab) {
      const intro = document.createElement("header");
      const title = document.createElement("h4");
      const description = document.createElement("p");
      intro.className = "workflow-tab-heading";
      title.textContent = selectedTab?.labelTh || dashboard.titleTh;
      description.textContent = selectedTab?.descriptionTh || dashboard.summaryTh;
      intro.append(title, description);
      els.workflowDashboardContent.appendChild(intro);
    }
    const actions = (selectedTab?.actionIds || []).map((actionId) => dashboard.actions.find((action) => action.id === actionId)).filter(Boolean);
    let renderedCatalog = false;
    if (subject.id === "codex_mcp_portal" && selectedTab?.id === "catalog") {
      renderWorkflowCatalog(els.workflowDashboardContent, dashboard);
      renderedCatalog = true;
    }
    const renderedDomain = renderWorkflowDomainPanel(
      els.workflowDashboardContent,
      subject,
      selectedTab,
      dashboard,
      report,
    );
    let renderedPrimaryOverview = false;
    if (isPrimaryTab && !renderedCatalog && !renderedDomain) {
      renderedPrimaryOverview = true;
      renderWorkflowPrimaryOverview(els.workflowDashboardContent, subject, dashboard, report, actions);
    }
    if (actions.length) {
      const actionGrid = document.createElement("div");
      actionGrid.className = "workflow-action-grid workflow-action-grid-secondary";
      actions.forEach((action) => actionGrid.appendChild(createWorkflowActionCard(action, dashboard)));
      els.workflowDashboardContent.appendChild(actionGrid);
    }
    if (!actions.length && !renderedCatalog && !renderedDomain && !renderedPrimaryOverview && !isHistoryTab) {
      const note = document.createElement("p");
      note.className = "workflow-empty-message";
      note.textContent = selectedTab?.emptyMessageTh || "ยังไม่มีข้อมูลในส่วนนี้ เมื่อ Local Runner ส่งผลกลับมาระบบจะแสดงที่นี่";
      els.workflowDashboardContent.appendChild(note);
    }
    if (isHistoryTab && ["left_server_racks", "right_server_racks", "right_tool_console", "terminal_workstation"].includes(subject.id)) {
      renderWorkflowSourceCards(els.workflowDashboardContent, dashboard.agentDeliveredSources);
    }
    if (isHistoryTab && !els.workflowDashboardContent.childElementCount) els.workflowDashboardContent.hidden = true;
  }
  renderWorkflowResults(subject, report);
  renderWorkflowActionStatus(subject.id);
}

function setWorkflowDashboardTab(propId, tabId, { focus = false } = {}) {
  if (!isWorkflowDashboardPropId(propId)) return;
  if (state.modal.workflowVoice.recognition) stopWorkflowVoiceDictation();
  const subject = getModalSubject();
  const propertyRole = getPropertyRole(subject);
  const report = state.propReports[propId] || {};
  const dashboard = normalizeWorkflowDashboard(subject, propertyRole, report);
  const selected = dashboard.tabs.find((tab) => tab.id === tabId) || dashboard.tabs[0];
  if (!selected) return;
  state.modal.workflowTabs[propId] = selected.id;
  renderWorkflowDashboard(subject, propertyRole, report);
  if (focus) els.workflowDashboardTabs?.querySelector(`[data-workflow-tab="${selected.id}"]`)?.focus();
  saveSessionSnapshot();
}

function workflowActionFormPayload(form, action) {
  const payload = {};
  action.formFields.forEach((field) => {
    const control = form.querySelector(`[data-workflow-field="${field.id}"]`);
    if (!control || control.disabled) return;
    if (field.type === "checkbox") {
      payload[field.id] = Boolean(control.checked);
      return;
    }
    const raw = String(control.value || "").trim();
    if (!raw && !field.required) return;
    if (field.type === "list") {
      payload[field.id] = raw.split(/[\n,]+/).map((item) => item.trim()).filter(Boolean).slice(0, 12);
    } else if (field.type === "number") {
      const numeric = Number(raw);
      if (Number.isFinite(numeric)) payload[field.id] = field.integer ? Math.trunc(numeric) : numeric;
    } else {
      payload[field.id] = raw.slice(0, field.type === "textarea" ? 4000 : 500);
    }
  });
  return payload;
}

function workflowActionFormSignature(propId, actionId, actionForm) {
  const input = JSON.stringify({ propId, actionId, form: actionForm });
  let hash = 2166136261;
  for (let index = 0; index < input.length; index += 1) {
    hash ^= input.charCodeAt(index);
    hash = Math.imul(hash, 16777619);
  }
  return `${input.length}:${(hash >>> 0).toString(16)}`;
}

function validateWorkflowSourceChoice(form, action) {
  const sourceFields = action.formFields.filter((field) => field.type === "source");
  const controls = sourceFields
    .map((field) => form.querySelector(`[data-workflow-field="${field.id}"]`))
    .filter((control) => control instanceof HTMLSelectElement && !control.disabled);
  controls.forEach((control) => control.setCustomValidity(""));
  const selected = controls.filter((control) => String(control.value || "").trim());
  if (selected.length > 1) {
    controls[0]?.setCustomValidity("เลือกได้เพียงอย่างเดียว: รายงานต้นทาง หรือ Source ใน Workspace");
    return false;
  }
  if (action.sourceRequired && selected.length !== 1) {
    controls[0]?.setCustomValidity("กรุณาเลือกแหล่งข้อมูลหนึ่งรายการ: รายงานต้นทาง หรือ Source ใน Workspace");
    return false;
  }
  return true;
}

function createWorkflowIdempotencyKey() {
  const uuid = globalThis.crypto?.randomUUID?.();
  if (uuid) return `wf-${uuid}`;
  let randomPart = "";
  if (typeof globalThis.crypto?.getRandomValues === "function") {
    const randomValues = new Uint32Array(4);
    globalThis.crypto.getRandomValues(randomValues);
    randomPart = [...randomValues].map((value) => value.toString(16).padStart(8, "0")).join("");
  }
  return `wf-${Date.now().toString(36)}-${randomPart || Math.random().toString(36).slice(2, 14)}`;
}

async function submitWorkflowDashboardAction(form) {
  const propId = state.modal.id;
  if (!isWorkflowDashboardPropId(propId) || state.modal.workflowAction.inFlight) return;
  const subject = getModalSubject();
  const propertyRole = getPropertyRole(subject);
  const report = state.propReports[propId] || {};
  const dashboard = normalizeWorkflowDashboard(subject, propertyRole, report);
  const actionId = String(form?.dataset.workflowActionForm || "");
  const action = dashboard.actions.find((item) => item.id === actionId);
  if (!action || !["ready", "settings_only"].includes(action.availability.status)) return;
  if (!validateWorkflowSourceChoice(form, action)) {
    form.reportValidity();
    return;
  }
  if (!form.reportValidity()) return;
  const actionForm = workflowActionFormPayload(form, action);
  const formSignature = workflowActionFormSignature(propId, actionId, actionForm);
  const previousAction = state.modal.workflowAction;
  const idempotencyKey = (
    previousAction.tone === "error"
    && previousAction.propId === propId
    && previousAction.actionId === actionId
    && previousAction.formSignature === formSignature
    && previousAction.idempotencyKey
  )
    ? previousAction.idempotencyKey
    : createWorkflowIdempotencyKey();
  state.modal.workflowAction = {
    inFlight: true,
    propId,
    actionId,
    idempotencyKey,
    formSignature,
    message: `กำลังส่งคำขอ “${action.labelTh}” ไปยัง Local Runner`,
    tone: "working",
  };
  renderWorkflowDashboard(subject, propertyRole, report);
  updateDecisionLog(`${displayPropName(propId)} กำลังส่งคำขอ ${action.labelTh}`);
  try {
    const response = await postJson(`/api/props/${encodeURIComponent(propId)}/workflow/actions`, {
      actionId,
      form: actionForm,
      idempotencyKey,
    });
    if (response?.mission) mergeBackendMission(response.mission);
    state.modal.workflowAction = {
      inFlight: false,
      propId,
      actionId,
      idempotencyKey: "",
      formSignature: "",
      message: safeDashboardDisplayText(response?.messageTh, "Local Runner รับคำขอแล้ว ติดตามสถานะได้จากรายการด้านล่าง"),
      tone: "success",
    };
    await loadPropReport(propId);
    if (state.modal.open && state.modal.id === propId) renderGameModal();
    const mission = response?.mission;
    if (mission?.owner && mission?.targetId) {
      routeAgentToTargetId(mission.owner, mission.targetId, `Task ${displayStatus(getMissionPresentationStatus(mission))}`, { select: false });
    }
    addBridgeEvent("สร้าง Mission แล้ว", `${displayPropName(propId)} • ${action.labelTh}`);
  } catch (error) {
    state.modal.workflowAction = {
      inFlight: false,
      propId,
      actionId,
      idempotencyKey,
      formSignature,
      message: safeDashboardDisplayText(error?.message, "Local Runner ยังไม่รับคำขอนี้ กรุณาตรวจการเชื่อมต่อแล้วลองใหม่"),
      tone: "error",
    };
    if (state.modal.open && state.modal.id === propId) renderWorkflowDashboard(subject, propertyRole, state.propReports[propId] || report);
    updateDecisionLog(`${displayPropName(propId)} ยังสร้าง Mission ไม่สำเร็จ`);
  }
}

function renderPropDashboard(subject, propertyRole) {
  const report = state.propReports[subject.id] || null;
  const isSignalConsensus = subject.id === AI_TRADE_COUNCIL_PROP_ID;
  const isWorkflowDashboard = isWorkflowDashboardPropId(subject.id);
  if (els.modalGenericDashboardWorkspace) els.modalGenericDashboardWorkspace.hidden = isSignalConsensus || isWorkflowDashboard;
  if (els.modalWorkflowDashboardWorkspace) els.modalWorkflowDashboardWorkspace.hidden = !isWorkflowDashboard;
  if (els.modalSignalConsensusWorkspace) els.modalSignalConsensusWorkspace.hidden = !isSignalConsensus;
  renderDashboardConnectionPanel(subject, propertyRole);
  if (isSignalConsensus) {
    renderSignalConsensusDashboard(subject, propertyRole, report || {});
    return;
  }
  if (isWorkflowDashboard) {
    renderWorkflowDashboard(subject, propertyRole, report || {});
    return;
  }
  const missions = getRelevantMissionsForSubject(subject, "prop")
    .filter((mission) => getMissionPresentationStatus(mission) !== "archived");
  const reports = [
    ...(Array.isArray(report?.reports) ? report.reports : []),
    ...memoryCardsToMissionItems((report?.memory || []).slice(0, 4), "mission_archivist").map((item) => ({
      ...item,
      summary: item.detail,
      status: "archived",
      ownerAgentId: item.owner,
      type: "memory_report",
    })),
  ];
  const entries = [
    ...missions.map((item) => ({ kind: "mission", item })),
    ...reports.map((item) => ({ kind: "report", item })),
  ];
  const grouped = {
    running: entries.filter(({ kind, item }) => getDashboardWorkState(item, kind) === "running"),
    completed: entries.filter(({ kind, item }) => getDashboardWorkState(item, kind) === "completed"),
    blocked: entries.filter(({ kind, item }) => getDashboardWorkState(item, kind) === "blocked"),
  };

  renderDashboardWorkColumn(
    els.modalDashboardRunning,
    grouped.running,
    "ยังไม่มีงานที่กำลังดำเนินการ",
  );
  renderDashboardWorkColumn(
    els.modalDashboardCompleted,
    grouped.completed,
    "ยังไม่มีรายงานสำเร็จส่งกลับมาที่อุปกรณ์นี้",
  );
  renderDashboardWorkColumn(
    els.modalDashboardBlocked,
    grouped.blocked,
    "ไม่มีงานติดขัด",
  );
  if (els.modalDashboardRunningCount) els.modalDashboardRunningCount.textContent = String(grouped.running.length);
  if (els.modalDashboardCompletedCount) els.modalDashboardCompletedCount.textContent = String(grouped.completed.length);
  if (els.modalDashboardBlockedCount) els.modalDashboardBlockedCount.textContent = String(grouped.blocked.length);
  if (els.modalDashboardWorkCount) els.modalDashboardWorkCount.textContent = `${entries.length} รายการ`;
  if (els.modalDashboardFreshness) {
    const updatedAt = report?.updatedAt ? new Date(report.updatedAt) : null;
    els.modalDashboardFreshness.textContent = updatedAt && !Number.isNaN(updatedAt.getTime())
      ? `อัปเดต ${updatedAt.toLocaleString("th-TH")}`
      : "ใช้ข้อมูลตั้งต้นในเครื่อง";
  }
}

function missionMatchesSearch(mission, query) {
  if (!query) return true;
  const haystack = [
    mission.id,
    mission.title,
    mission.detail,
    mission.result,
    mission.owner,
    mission.requester,
    mission.targetId,
    mission.toolId,
    mission.reportType,
    mission.parentMissionId,
    ...(mission.subtaskIds || []),
    ...(mission.reportIds || []),
  ].join(" ").toLowerCase();
  return haystack.includes(query);
}

function createKanbanCard(mission) {
  return createTaskCard(mission, { variant: "kanban-card", source: "kanban" });
}

function appendMissionDetailRow(container, label, value) {
  const row = document.createElement("div");
  const friendlyFact = container.classList?.contains("task-detail-facts");
  const term = document.createElement(friendlyFact ? "span" : "dt");
  const description = document.createElement(friendlyFact ? "strong" : "dd");
  if (friendlyFact) {
    row.className = "task-detail-fact";
    term.className = "task-detail-label";
  }
  term.textContent = label;
  description.textContent = formatDashboardValue(value);
  row.append(term, description);
  container.appendChild(row);
}

function getMissionApprovalState(mission) {
  return String(mission?.approval?.state || "not_required").trim().toLowerCase();
}

function hasHumanApprovalDecision(mission) {
  const decisions = Array.isArray(mission?.approval?.decisions) ? mission.approval.decisions : [];
  return decisions.some((decision) => String(decision?.actorId || "").toLowerCase() === "human");
}

function isMissionReadyForExplicitExecution(mission) {
  if (!mission?.id || normalizeMissionStatus(mission.status) !== "waiting_approval") return false;
  if (isBackendAutoEligibleMission(mission)) return false;
  return mission.readyToExecute === true;
}

function setMissionExecuteStatus(message, tone = "neutral") {
  if (!els.modalKanbanExecuteStatus) return;
  els.modalKanbanExecuteStatus.textContent = message;
  els.modalKanbanExecuteStatus.dataset.tone = tone;
}

function getActiveTaskDetailMission() {
  const missionId = state.taskDetailMissionId || state.modal.selectedMissionId;
  return state.missions.find((item) => item.id === missionId) || null;
}

function updateMissionExecutionConfirmation(mission = getActiveTaskDetailMission()) {
  if (!els.modalKanbanExecuteMissionId || !els.modalKanbanExecute) return;
  const canExecute = isMissionReadyForExplicitExecution(mission);
  const confirmation = els.modalKanbanExecuteMissionId.value.trim();
  const exactMatch = canExecute && confirmation === mission.id;
  const hasInput = confirmation.length > 0;
  els.modalKanbanExecuteMissionId.disabled = !canExecute || state.modal.executionInFlight;
  els.modalKanbanExecuteMissionId.setAttribute("aria-invalid", String(canExecute && hasInput && !exactMatch));
  els.modalKanbanExecute.disabled = !exactMatch || state.modal.executionInFlight;
  if (state.modal.executionInFlight) {
    setMissionExecuteStatus(`กำลังส่งคำขอรัน ${mission.id} หนึ่งครั้ง ระบบจะไม่ลองรันซ้ำอัตโนมัติ`, "neutral");
  } else if (exactMatch) {
    setMissionExecuteStatus("Mission ID ตรงกัน งานจะเริ่มเมื่อกดปุ่มยืนยันการรันด้านล่างเท่านั้น", "ready");
  } else if (hasInput) {
    setMissionExecuteStatus("Mission ID ไม่ตรง จึงยังไม่ได้ส่งคำขอ", "error");
  } else {
    setMissionExecuteStatus(`พิมพ์ ${mission?.id || "Mission ID ให้ตรง"} เพื่อปลดล็อกคำขอรันหนึ่งครั้ง`, "neutral");
  }
}

function syncMissionExecutionControls(mission) {
  const canExecute = isMissionReadyForExplicitExecution(mission);
  if (els.modalKanbanExecuteConfirmation) els.modalKanbanExecuteConfirmation.hidden = !canExecute;
  if (els.modalKanbanExecute) {
    els.modalKanbanExecute.hidden = !canExecute;
    els.modalKanbanExecute.dataset.missionId = canExecute ? mission.id : "";
  }
  if (!els.modalKanbanExecuteMissionId) return;
  if (!canExecute) {
    els.modalKanbanExecuteMissionId.value = "";
    els.modalKanbanExecuteMissionId.dataset.missionId = "";
    els.modalKanbanExecuteMissionId.disabled = true;
    els.modalKanbanExecuteMissionId.setAttribute("aria-invalid", "false");
    return;
  }
  if (els.modalKanbanExecuteMissionId.dataset.missionId !== mission.id) {
    els.modalKanbanExecuteMissionId.value = "";
    els.modalKanbanExecuteMissionId.dataset.missionId = mission.id;
  }
  updateMissionExecutionConfirmation(mission);
}

function looksLikeTechnicalText(value) {
  const text = String(value || "");
  return /(?:```|`[^`]+`|Traceback|Exception|\berror\b|\bsandbox\b|\bspawn\b|[A-Za-z]:\\|\/api\/|\b(?:const|function|class|import|SELECT|INSERT|UPDATE)\b|\{[\s\S]*\}|\[[\s\S]*\])/i.test(text);
}

function isPredominantlyEnglishText(value) {
  const text = String(value || "").trim();
  if (!text || /[ก-๙]/.test(text)) return false;
  const words = text.match(/[A-Za-z]{2,}/g) || [];
  return words.length >= 5;
}

function appendTaskDetailSection(container, titleText, value, className = "") {
  const text = String(value || "").trim();
  if (!text) return;
  const section = document.createElement("section");
  const title = document.createElement("h3");
  section.className = `task-detail-section ${className}`.trim();
  title.textContent = titleText;
  section.appendChild(title);
  if (looksLikeTechnicalText(text)) {
    const note = document.createElement("p");
    const disclosure = document.createElement("details");
    const summary = document.createElement("summary");
    const pre = document.createElement("pre");
    note.textContent = "มีผลลัพธ์แบบเทคนิค ให้กดเปิดเมื่อต้องการตรวจข้อความหรือโค้ด";
    summary.textContent = "ดูผลแบบเทคนิค";
    pre.textContent = text;
    disclosure.className = "task-technical-result";
    disclosure.append(summary, pre);
    section.append(note, disclosure);
  } else {
    const paragraph = document.createElement("p");
    paragraph.textContent = text;
    section.appendChild(paragraph);
  }
  container.appendChild(section);
}

function appendTaskEvidenceSection(container, evidence) {
  if (!Array.isArray(evidence) || !evidence.length) return;
  const section = document.createElement("section");
  const title = document.createElement("h3");
  const list = document.createElement("ul");
  section.className = "task-detail-section task-detail-evidence";
  title.textContent = "แหล่งข้อมูลที่ตรวจสอบ";
  list.className = "task-evidence-list";
  evidence.slice(0, 20).forEach((item) => {
    const rawUrl = String(item?.url || "").trim();
    let parsed;
    try {
      parsed = new URL(rawUrl);
    } catch {
      return;
    }
    if (!["http:", "https:"].includes(parsed.protocol) || parsed.username || parsed.password) return;
    const row = document.createElement("li");
    const link = document.createElement("a");
    const note = document.createElement("span");
    link.href = parsed.href;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    link.textContent = safeDashboardDisplayText(item?.label, parsed.hostname);
    note.textContent = safeDashboardDisplayText(item?.note, parsed.hostname);
    row.append(link, note);
    list.appendChild(row);
  });
  if (!list.children.length) return;
  section.append(title, list);
  container.appendChild(section);
}

function getMissionNextStep(mission) {
  const status = getMissionPresentationStatus(mission);
  const autoEligible = isBackendAutoEligibleMission(mission);
  const waitingChildren = Math.max(0, Number(mission?.delegation?.subtaskStatusCounts?.waiting_approval) || 0);
  if (status === "queued") {
    return autoEligible
      ? "Backend รับงานเข้าคิวอัตโนมัติแล้ว Agent จะเริ่มเมื่อ Runner ว่าง"
      : "รอ Agent ผู้รับผิดชอบเริ่มงาน";
  }
  if (status === "running") {
    return autoEligible
      ? "Agent กำลังทำงานผ่าน Local Runner และจะส่งรายงานกลับอุปกรณ์ที่กำหนด"
      : "รอ Agent ทำงานและส่งรายงานกลับมายังจุดแสดงผล";
  }
  if (status === "waiting_approval") {
    if (waitingChildren > 0) {
      return `Task ย่อย ${waitingChildren} งานกำลังรอการตรวจสอบ ยังไม่มี Runner ของ Task เหล่านี้เริ่มทำงาน`;
    }
    return isMissionReadyForExplicitExecution(mission)
      ? "อนุมัติครบแล้ว แต่ยังไม่รันอัตโนมัติ ต้องยืนยัน Mission ID ที่โต๊ะ Mission ก่อน"
      : "รอผู้ใช้และ Risk Guard ตรวจสอบก่อน งานจริงจะยังไม่เริ่ม";
  }
  if (status === "blocked") {
    if (mission?.workStatus === "waiting_input") {
      return "ส่งข้อมูลหรือไฟล์ที่ Agent ระบุไว้ แล้วสร้าง Task ใหม่เพื่อทำงานต่อ";
    }
    if (mission?.blockedCapability === "Native Codex Web Search verification") {
      return "ไม่ต้องอนุมัติงานนี้ซ้ำ ให้ตรวจการยืนยัน Web Search ของ Local Runner แล้วเริ่มวิเคราะห์ใหม่ด้วย Snapshot ปัจจุบัน ผลเก่าจะไม่ถูกนำมาใช้";
    }
    if (mission?.blockedCapability) {
      return `Task นี้ไม่ได้รอการอนุมัติ แต่ยังขาดความสามารถ ${safeDashboardDisplayText(mission.blockedCapability)} ให้เชื่อม Adapter ที่เกี่ยวข้องก่อนลองใหม่`;
    }
    return "เปิดรายละเอียดสาเหตุ แล้วให้ Manager Agent หรือ Risk Guard ช่วยปลดข้อขัดข้อง";
  }
  if (status === "completed") {
    return autoEligible
      ? "งานอัตโนมัติเสร็จแล้ว เปิดรายงานที่อุปกรณ์ปลายทางเพื่อตรวจผล"
      : "ตรวจรายงานที่ส่งกลับมา แล้วเก็บ Mission เข้าคลังเมื่อใช้งานเสร็จ";
  }
  if (status === "failed") return "ตรวจสาเหตุและรายงานก่อนสร้าง Task ใหม่ ระบบจะไม่ลองรันซ้ำเอง";
  if (status === "archived") return "Mission นี้ถูกเก็บในคลังแล้ว เปิดดูได้โดยไม่กระทบงานปัจจุบัน";
  return "รอข้อมูลขั้นตอนถัดไปจาก Manager Agent";
}

function renderMissionDetail(mission) {
  if (!els.modalKanbanDetailTitle || !els.modalKanbanDetailBody) return;
  els.modalKanbanDetailBody.innerHTML = "";
  if (!mission) {
    els.modalKanbanDetailTitle.textContent = "เลือก Mission";
    const empty = document.createElement("p");
    empty.textContent = "กดการ์ด Task เพื่อดูสถานะ ผู้รับผิดชอบ ผลล่าสุด และขั้นตอนถัดไป";
    els.modalKanbanDetailBody.appendChild(empty);
    if (els.modalKanbanOpenOwnerAgent) els.modalKanbanOpenOwnerAgent.disabled = true;
    if (els.modalKanbanOpenTargetProp) els.modalKanbanOpenTargetProp.disabled = true;
    if (els.modalKanbanApprove) els.modalKanbanApprove.hidden = true;
    if (els.modalKanbanReject) els.modalKanbanReject.hidden = true;
    syncMissionExecutionControls(null);
    return;
  }

  els.modalKanbanDetailTitle.textContent = mission.title || mission.id || "รายละเอียด Mission";
  const friendly = document.createElement("div");
  const facts = document.createElement("div");
  const nextStep = document.createElement("section");
  const nextTitle = document.createElement("h3");
  const nextText = document.createElement("p");
  friendly.className = "task-detail-friendly";
  facts.className = "task-detail-facts";
  const presentationStatus = getMissionPresentationStatus(mission);
  const autoEligible = isBackendAutoEligibleMission(mission);
  appendMissionDetailRow(facts, "สถานะ", displayStatus(presentationStatus));
  appendMissionDetailRow(facts, "ผู้รับผิดชอบ", displayAgentName(getAgentIdFromOwner(mission.owner) || mission.owner, "ยังไม่ได้มอบหมาย"));
  appendMissionDetailRow(facts, "จุดแสดงผล", displayPropName(mission.targetId || "mission_strategy_table"));
  appendMissionDetailRow(facts, "ความเสี่ยง", displayRisk(mission.risk));
  appendMissionDetailRow(facts, "รูปแบบการทำงาน", autoEligible ? "Backend อนุญาตให้อัตโนมัติ" : displayStatus(mission.executionMode || "manual_guarded"));
  appendMissionDetailRow(facts, "การอนุมัติ", autoEligible ? "งานนี้ไม่ต้องกดอนุมัติซ้ำ" : displayApproval(mission.approval?.state));
  appendMissionDetailRow(
    facts,
    "การค้นเว็บ",
    mission.webSearchEnabled === true
      ? (
        mission.webSearchEvidenceVerified === true
          ? "ค้นเว็บจริงแล้ว พร้อมลิงก์หลักฐาน"
          : mission.webSearchUsed === true
            ? "ค้นเว็บจริงแล้ว แต่ยังไม่มีลิงก์หลักฐาน"
            : presentationStatus === "running"
              ? "เปิดไว้ กำลังค้นหา"
              : "เปิดไว้ แต่ยังไม่พบหลักฐานการค้นเว็บ"
      )
      : "ไม่ได้ใช้ใน Task นี้",
  );
  appendMissionDetailRow(facts, "อัปเดตล่าสุด", formatThaiDateTime(mission.updatedAt || mission.createdAt));
  friendly.appendChild(facts);
  appendTaskDetailSection(friendly, "สิ่งที่ได้รับมอบหมาย", mission.detail || "ยังไม่มีคำอธิบายเพิ่มเติม", "task-detail-instruction");
  if (mission.result) appendTaskDetailSection(friendly, "ผลล่าสุด", mission.result, "task-detail-result");
  appendTaskEvidenceSection(friendly, mission.evidence);
  nextStep.className = "task-detail-section task-detail-next-step";
  nextTitle.textContent = "ขั้นตอนถัดไป";
  nextText.textContent = getMissionNextStep(mission);
  nextStep.append(nextTitle, nextText);
  friendly.appendChild(nextStep);

  const systemDisclosure = document.createElement("details");
  const systemSummary = document.createElement("summary");
  const systemGrid = document.createElement("dl");
  systemDisclosure.className = "task-system-disclosure";
  systemSummary.textContent = "ดูข้อมูลระบบ";
  systemGrid.className = "task-system-grid";
  appendMissionDetailRow(systemGrid, "Mission ID", mission.id || "local");
  appendMissionDetailRow(systemGrid, "ขั้นตอน", mission.phase || "-");
  appendMissionDetailRow(systemGrid, "ID ผู้รับผิดชอบ", mission.owner || "manager");
  appendMissionDetailRow(systemGrid, "ID ผู้ขอ", mission.requester || mission.requesterId || "human");
  appendMissionDetailRow(systemGrid, "ID จุดแสดงผล", mission.targetId || "mission_strategy_table");
  appendMissionDetailRow(systemGrid, "Tool ID", mission.toolId || "queue_only");
  appendMissionDetailRow(systemGrid, "โหมดจาก Backend", mission.executionMode || "manual_guarded");
  appendMissionDetailRow(systemGrid, "เริ่มอัตโนมัติได้", mission.autoEligible === true ? "true" : "false");
  appendMissionDetailRow(systemGrid, "ต้องให้ผู้ใช้อนุมัติ", mission.requiresHumanApproval === true ? "true" : "false");
  appendMissionDetailRow(systemGrid, "ระดับโมเดล", mission.modelTier || "local_default");
  appendMissionDetailRow(systemGrid, "งบประมาณ", mission.budget || "local_defaults");
  appendMissionDetailRow(systemGrid, "Mission หลัก", mission.parentMissionId || "-");
  appendMissionDetailRow(systemGrid, "ID ของ Task ย่อย", mission.subtaskIds || []);
  appendMissionDetailRow(systemGrid, "ประเภทรายงาน", mission.reportType || "-");
  appendMissionDetailRow(systemGrid, "ID รายงาน", mission.reportIds || []);
  appendMissionDetailRow(systemGrid, "สถานะการอนุมัติ", mission.approval?.state || "not_required");
  appendMissionDetailRow(systemGrid, "เวลาสร้าง", mission.createdAt || "-");
  appendMissionDetailRow(systemGrid, "เวลาอัปเดต", mission.updatedAt || "-");
  appendMissionDetailRow(systemGrid, "เวลาเสร็จสิ้น", mission.completedAt || "-");
  appendMissionDetailRow(systemGrid, "สถานะการแจกงาน", mission.delegation?.state || "-");
  systemDisclosure.append(systemSummary, systemGrid);
  els.modalKanbanDetailBody.append(friendly, systemDisclosure);

  if (autoEligible) {
    const notice = document.createElement("p");
    notice.className = "kanban-readonly-notice auto-eligible";
    notice.textContent = presentationStatus === "completed"
      ? `Backend ทำ Task นี้เสร็จแล้ว และส่งรายงานไปที่ ${displayPropName(mission.targetId || "mission_strategy_table")}`
      : "Backend ยืนยันว่า Task นี้เริ่มอัตโนมัติได้ จึงไม่มีปุ่มอนุมัติหรือปุ่มยืนยันการรันซ้ำบน Frontend";
    els.modalKanbanDetailBody.appendChild(notice);
  }

  if (normalizeMissionStatus(mission.status) === "waiting_approval" && !autoEligible) {
    const notice = document.createElement("p");
    notice.className = "kanban-readonly-notice";
    notice.textContent = isMissionReadyForExplicitExecution(mission)
      ? "อนุมัติครบแล้ว แต่งานจะไม่รันอัตโนมัติ ให้พิมพ์ Mission ID ให้ตรง แล้วกดปุ่มยืนยันด้านล่างเพื่อส่งคำขอไปยัง Backend เพียงครั้งเดียว"
      : "Mission นี้กำลังรออนุมัติ การกดอนุมัติจะยังไม่เริ่มงานจริง จนกว่า Risk Guard จะผ่านและผู้ใช้ยืนยันการรันอีกครั้ง";
    els.modalKanbanDetailBody.appendChild(notice);
  }

  const ownerAgentId = getAgentIdFromOwner(mission.owner);
  const approvalState = getMissionApprovalState(mission);
  const approvalClosed = ["approved", "consumed", "rejected", "expired", "invalidated"].includes(approvalState);
  const canRecordApproval = normalizeMissionStatus(mission.status) === "waiting_approval"
    && Boolean(mission.approval?.required)
    && !autoEligible
    && !approvalClosed
    && !hasHumanApprovalDecision(mission);
  if (els.modalKanbanApprove) {
    els.modalKanbanApprove.hidden = !canRecordApproval;
    els.modalKanbanApprove.disabled = state.modal.approvalInFlight;
  }
  if (els.modalKanbanReject) {
    els.modalKanbanReject.hidden = !canRecordApproval;
    els.modalKanbanReject.disabled = state.modal.approvalInFlight;
  }
  syncMissionExecutionControls(mission);
  if (els.modalKanbanOpenOwnerAgent) {
    els.modalKanbanOpenOwnerAgent.dataset.agentId = ownerAgentId || "";
    els.modalKanbanOpenOwnerAgent.disabled = !ownerAgentId;
  }
  const targetId = String(mission.targetId || "");
  const targetExists = targetId && targetId !== "mission_strategy_table" && getInteractiveObjects().some((item) => item.id === targetId);
  if (els.modalKanbanOpenTargetProp) {
    els.modalKanbanOpenTargetProp.dataset.targetId = targetExists ? targetId : "";
    els.modalKanbanOpenTargetProp.disabled = !targetExists;
  }
}

function openTaskDetail(missionId, trigger = null, options = {}) {
  const mission = state.missions.find((item) => item.id === missionId);
  if (!mission || !els.taskDetailDialog) return;
  state.taskDetailMissionId = mission.id;
  state.taskDetailSource = options.source || "list";
  taskDetailShouldRestoreFocus = true;
  taskDetailReturnFocus = trigger instanceof HTMLElement ? trigger : document.activeElement;
  taskDetailReturnMissionId = mission.id;
  taskDetailReturnContainerId = trigger?.closest?.("[id]")?.id || null;
  if (state.taskDetailSource === "kanban") {
    state.modal.selectedMissionId = mission.id;
    els.modalKanbanBoard?.querySelectorAll(".task-card.selected").forEach((card) => card.classList.remove("selected"));
    trigger?.classList.add("selected");
  }
  renderMissionDetail(mission);
  els.taskDetailDialog.querySelectorAll("details[open]").forEach((detail) => detail.removeAttribute("open"));
  if (!els.taskDetailDialog.open) els.taskDetailDialog.showModal();
  saveSessionSnapshot();
}

function closeTaskDetail({ restoreFocus = true } = {}) {
  taskDetailShouldRestoreFocus = restoreFocus;
  if (els.taskDetailDialog?.open) {
    els.taskDetailDialog.close();
    return;
  }
  state.taskDetailMissionId = null;
  state.taskDetailSource = null;
  restoreTaskDetailReturnFocus();
  taskDetailReturnFocus = null;
  taskDetailReturnMissionId = null;
  taskDetailReturnContainerId = null;
}

function restoreTaskDetailReturnFocus() {
  if (!taskDetailShouldRestoreFocus) return;
  let target = taskDetailReturnFocus?.isConnected ? taskDetailReturnFocus : null;
  if (!target && taskDetailReturnMissionId) {
    const scope = taskDetailReturnContainerId ? document.getElementById(taskDetailReturnContainerId) : document;
    target = [...(scope || document).querySelectorAll("[data-task-mission-id]")]
      .find((card) => card.dataset.taskMissionId === taskDetailReturnMissionId) || null;
  }
  target ||= state.modal.open
    ? (els.modalKanbanSearch || els.modalCloseButton)
    : (els.openMissionTableButton || els.stage);
  target?.focus?.();
}

function refreshOpenTaskDetail() {
  if (!els.taskDetailDialog?.open || !state.taskDetailMissionId) return;
  const mission = state.missions.find((item) => item.id === state.taskDetailMissionId);
  if (!mission) {
    closeTaskDetail();
    return;
  }
  renderMissionDetail(mission);
}

function renderMissionKanban({ preserveScroll = true } = {}) {
  if (!els.modalKanbanBoard) return;
  if (preserveScroll) {
    els.modalKanbanBoard.querySelectorAll(".kanban-column[data-status]").forEach((section) => {
      const status = section.dataset.status;
      const list = section.querySelector(".kanban-column-list");
      if (status && list) state.modal.kanbanScrollTop[status] = list.scrollTop;
    });
  } else {
    state.modal.kanbanScrollTop = {};
  }
  const archivedCount = state.missions.filter((mission) => getMissionPresentationStatus(mission) === "archived").length;
  const query = String(state.modal.searchText || "").trim().toLowerCase();
  const columns = state.modal.showArchived
    ? [...MISSION_KANBAN_COLUMNS, { id: "archived", label: "เก็บเข้าคลังแล้ว" }]
    : MISSION_KANBAN_COLUMNS;
  const visibleStatuses = new Set(columns.map((column) => column.id));
  const missions = state.missions.filter((mission) => (
    visibleStatuses.has(getMissionPresentationStatus(mission))
    && missionMatchesSearch(mission, query)
  ));

  if (els.modalKanbanArchiveToggle) {
    els.modalKanbanArchiveToggle.textContent = `${state.modal.showArchived ? "ซ่อน" : "แสดง"} คลังงาน (${archivedCount})`;
    els.modalKanbanArchiveToggle.setAttribute("aria-pressed", String(state.modal.showArchived));
    els.modalKanbanArchiveToggle.classList.toggle("active", state.modal.showArchived);
  }
  if (els.modalKanbanSearch && document.activeElement !== els.modalKanbanSearch) {
    els.modalKanbanSearch.value = state.modal.searchText || "";
  }

  els.modalKanbanBoard.innerHTML = "";
  columns.forEach((column) => {
    const columnMissions = missions.filter((mission) => getMissionPresentationStatus(mission) === column.id);
    const section = document.createElement("section");
    const heading = document.createElement("div");
    const label = document.createElement("strong");
    const count = document.createElement("span");
    const list = document.createElement("div");
    section.className = `kanban-column status-${column.id}`;
    section.dataset.status = column.id;
    heading.className = "kanban-column-heading";
    label.textContent = column.label;
    count.textContent = String(columnMissions.length);
    heading.append(label, count);
    list.className = "kanban-column-list";
    if (!columnMissions.length) {
      const empty = document.createElement("p");
      empty.className = "kanban-empty";
      empty.textContent = query ? "ไม่พบ Mission ที่ตรงกับคำค้น" : "ยังไม่มี Mission";
      list.appendChild(empty);
    } else {
      columnMissions.forEach((mission) => list.appendChild(createTaskCard(mission, { variant: "kanban-card", source: "kanban" })));
    }
    section.append(heading, list);
    els.modalKanbanBoard.appendChild(section);
    list.scrollTop = Math.max(0, Number(state.modal.kanbanScrollTop[column.id] || 0));
    list.addEventListener("scroll", () => {
      state.modal.kanbanScrollTop[column.id] = list.scrollTop;
    }, { passive: true });
  });

  const selectedVisible = missions.find((mission) => mission.id === state.modal.selectedMissionId);
  if (!selectedVisible && state.modal.selectedMissionId) {
    if (state.taskDetailSource === "kanban" && state.taskDetailMissionId === state.modal.selectedMissionId) {
      closeTaskDetail();
    }
    state.modal.selectedMissionId = null;
  }
  refreshOpenTaskDetail();
}

async function recordKanbanApprovalDecision(decision) {
  const mission = getActiveTaskDetailMission();
  if (!mission || normalizeMissionStatus(mission.status) !== "waiting_approval" || state.modal.approvalInFlight) return;
  state.modal.approvalInFlight = true;
  renderMissionDetail(mission);
  try {
    const isApproved = decision === "approved";
    const result = await postJson(`/api/missions/${encodeURIComponent(mission.id)}/approval`, {
      decision,
      actorId: "human",
      confirmMissionId: mission.id,
      note: isApproved
        ? "ผู้ใช้อนุมัติจาก Mission Table แล้ว แต่ยังไม่ได้สั่งให้ Tool ทำงาน"
        : "ผู้ใช้ไม่อนุมัติจาก Mission Table และ Mission ต้องหยุดอยู่ที่ประตูอนุมัติ",
    });
    if (result.mission) {
      mergeBackendMission({
        ...result.mission,
        readyToExecute: result.readyToExecute === true || result.mission.readyToExecute === true,
      });
    }
    await loadBridgeMissions({ replaceEvents: false });
    if (result.readyToExecute === true) {
      addBridgeEvent("อนุมัติครบแล้ว", `${mission.id} พร้อมสำหรับขั้นยืนยัน แต่ต้องพิมพ์ Mission ID ให้ตรงก่อนรัน`);
    }
    updateDecisionLog(isApproved
      ? (result.readyToExecute === true
        ? `${mission.id}: อนุมัติครบแล้ว ให้พิมพ์ Mission ID และกดปุ่มยืนยันเมื่อพร้อม`
        : `${mission.id}: บันทึกการอนุมัติจากผู้ใช้แล้ว แต่ยังต้องผ่าน Risk Guard และยืนยันการรันอีกครั้ง`)
      : `${mission.id}: Mission ไม่ได้รับอนุมัติและถูกหยุดไว้ที่ประตูอนุมัติ`);
  } catch (error) {
    handleBridgeRequestError(error, "mission_approval");
  } finally {
    state.modal.approvalInFlight = false;
    renderMissionKanban();
  }
}

async function executeApprovedKanbanMission() {
  // Guard contract: No automatic retry.
  const mission = getActiveTaskDetailMission();
  if (!mission || state.modal.executionInFlight) return;

  if (!isMissionReadyForExplicitExecution(mission)) {
    syncMissionExecutionControls(mission);
    updateDecisionLog(`${mission.id}: ยังรันไม่ได้ เพราะการอนุมัติในระบบยังไม่ครบ`);
    addBridgeEvent("ยังรันไม่ได้", `${mission.id}: Backend ยังยืนยันการอนุมัติไม่ครบ`);
    return;
  }

  const confirmation = String(els.modalKanbanExecuteMissionId?.value || "").trim();
  if (confirmation !== mission.id) {
    updateMissionExecutionConfirmation(mission);
    els.modalKanbanExecuteMissionId?.focus();
    updateDecisionLog(`${mission.id}: ยังรันไม่ได้ เพราะ Mission ID ที่พิมพ์ไม่ตรง`);
    addBridgeEvent("การยืนยันถูกหยุดไว้", `${mission.id}: ต้องพิมพ์ Mission ID ให้ตรง จึงยังไม่ได้ส่งคำขอ`);
    return;
  }

  state.modal.executionInFlight = true;
  updateMissionExecutionConfirmation(mission);
  state.bridge.status = "กำลังส่ง Mission ที่อนุมัติแล้ว";
  state.bridge.lastRun = `ส่งคำขอรัน ${mission.id} แบบยืนยันครั้งเดียว`;
  updateBridgeLabel();
  updateDecisionLog(`${mission.id}: ส่งคำขอรันผ่านระบบป้องกันหนึ่งครั้งแล้ว ระบบจะไม่ลองซ้ำอัตโนมัติ`);
  addBridgeEvent("ส่งคำขอรันแล้ว", `${mission.id}: ยืนยัน ID ตรงกันและส่งไปยัง Local Runner ที่มีระบบป้องกันแล้ว`);

  let feedbackMessage = "คำขอรันสิ้นสุดแล้ว ให้เปิด Mission เพื่อดูรายงาน";
  let feedbackTone = "neutral";
  try {
    const result = await postJson(`/api/missions/${encodeURIComponent(mission.id)}/execute`, {
      confirmMissionId: mission.id,
      requestedBy: "human",
      source: "frontend.mission_table.explicit_execute",
    });
    if (result.mission) mergeBackendMission(result.mission);
    applyBridgeResponse(result, { agentId: mission.owner, toolId: mission.toolId || "mission_execute" });
    feedbackMessage = result.ok
      ? `${mission.id}: งานผ่านระบบป้องกันเสร็จแล้ว ให้ตรวจรายงานที่ถูกส่งกลับมา`
      : `${mission.id}: Backend จบงานโดยยังไม่มีรายงานสำเร็จ และระบบไม่ได้ลองรันซ้ำอัตโนมัติ`;
    feedbackTone = result.ok ? "ready" : "error";
    addBridgeEvent("ผลการรัน", `${mission.id}: ${displayStatus(result.mission ? getMissionPresentationStatus(result.mission) : (result.ok ? "completed" : "failed"))}`);
    updateDecisionLog(feedbackMessage);
  } catch (error) {
    if (error.body?.mission) mergeBackendMission(error.body.mission);
    handleBridgeRequestError(error, "mission_execute");
    feedbackMessage = `${mission.id}: ${error.message} ระบบไม่ได้ลองรันซ้ำอัตโนมัติ`;
    feedbackTone = "error";
  } finally {
    state.modal.executionInFlight = false;
    if (els.modalKanbanExecuteMissionId) els.modalKanbanExecuteMissionId.value = "";
    await loadBridgeMissions({ replaceEvents: false });
    renderMissionKanban();
    if (isMissionReadyForExplicitExecution(state.missions.find((item) => item.id === mission.id))) {
      setMissionExecuteStatus(feedbackMessage, feedbackTone);
    }
    saveSessionSnapshot();
  }
}

function setModalTab(tabName) {
  const surface = getModalSurface();
  const allowedTabs = {
    agent: ["chat", "tasks"],
    dashboard: ["results"],
    kanban: ["kanban"],
  }[surface];
  state.modal.activeTab = allowedTabs.includes(tabName) ? tabName : allowedTabs[0];
  const tabs = els.modalTabs ? [...els.modalTabs.querySelectorAll(".modal-tab")] : [];
  tabs.forEach((tab) => {
    const surfaces = String(tab.dataset.surfaces || "").split(/\s+/).filter(Boolean);
    tab.hidden = !surfaces.includes(surface);
    tab.classList.toggle("active", tab.dataset.tab === state.modal.activeTab);
  });
  [...els.gameModal.querySelectorAll(".modal-tab-panel")].forEach((panel) => {
    const surfaces = String(panel.dataset.surfaces || "").split(/\s+/).filter(Boolean);
    panel.hidden = !surfaces.includes(surface);
    panel.classList.toggle("active", panel.dataset.panel === state.modal.activeTab);
  });
  saveSessionSnapshot();
}

function renderAgentComposer(subject) {
  if (!subject || !els.modalAgentComposer) return;
  const isCurrentChat = state.agentChat.agentId === subject.id;
  const chatBusy = state.agentChat.inFlight;
  if (els.modalComposerLabel) els.modalComposerLabel.textContent = `ข้อความถึง ${subject.name}`;
  if (els.modalSendButton) {
    els.modalSendButton.disabled = chatBusy;
    els.modalSendButton.textContent = chatBusy ? "กำลังคิด..." : "คุยกับ Codex";
  }
  if (els.modalAssignButton) els.modalAssignButton.textContent = "สร้าง Task ทางลัด";
  if (els.modalChatStatus) {
    els.modalChatStatus.textContent = isCurrentChat
      ? state.agentChat.message
      : chatBusy
        ? "Agent อีกตัวกำลังตอบผ่าน Codex กรุณารอให้คำตอบเดิมเสร็จก่อน"
        : "พร้อมคุยกับ Codex ผ่าน Local Runner";
    els.modalChatStatus.dataset.tone = isCurrentChat
      ? state.agentChat.tone
      : chatBusy ? "working" : "neutral";
  }
  if (els.modalChatUsageNote) {
    const autoMode = state.operatorMode.mode === "auto_guarded" && state.operatorMode.autoExecute === true;
    els.modalChatUsageNote.textContent = autoMode
      ? "คุยได้ทั้งถามและสั่งงาน หาก Backend ยืนยันว่าเป็นงานอัตโนมัติที่ทำได้ ระบบจะสร้าง Mission เริ่มงาน และส่งรายงานไปยังอุปกรณ์เอง งานเงินจริง การส่งออกภายนอก Deploy และลบไฟล์ยังต้องอนุมัติ"
      : "คุยได้ทั้งถามและสั่งงาน หากคำตอบสร้าง Task ระบบจะแสดงสถานะจริงจาก Backend งานที่ยังไม่ผ่านเกณฑ์จะรอตรวจสอบ สามารถใช้ปุ่ม “สร้าง Task ทางลัด” ได้เช่นกัน";
  }
}

function renderGameModal() {
  const subject = getModalSubject();
  if (!subject || !els.gameModal) return;
  const type = state.modal.type;
  const isAgent = type === "agent";
  const surface = getModalSurface(type, subject.id);
  const isKanban = surface === "kanban";
  const isWorkflowDashboard = surface === "dashboard" && isWorkflowDashboardPropId(subject.id);
  const propertyRole = isAgent ? null : getPropertyRole(subject);
  const dashboardProfile = isAgent ? null : state.propReports[subject.id]?.dashboardProfile;
  els.gameModal.classList.toggle("agent-modal", isAgent);
  els.gameModal.classList.toggle("prop-modal", !isAgent);
  els.gameModal.classList.toggle("dashboard-modal", surface === "dashboard");
  els.gameModal.classList.toggle("signal-consensus-modal", surface === "dashboard" && subject.id === AI_TRADE_COUNCIL_PROP_ID);
  els.gameModal.classList.toggle("workflow-dashboard-modal", isWorkflowDashboard);
  els.gameModal.classList.toggle("kanban-modal", isKanban);
  const title = isAgent
    ? subject.name
    : safeDashboardDisplayText(dashboardProfile?.moduleNameTh || propertyRole?.displayTitle || displayPropName(subject.id, subject.label));
  const role = isAgent ? subject.role : (propertyRole?.displayTitle || displayPropName(subject.id, subject.layer));
  const summary = isAgent ? (subject.summary || "") : (propertyRole?.purpose || subject.summary || "");
  const speech = isAgent
    ? getAgentSpeech(subject.id, "idle", subject.status)
    : isKanban
      ? "ศูนย์รวม Mission ของทุก Agent แยกตามสถานะ งานจริงจะยังไม่เริ่มจนกว่าจะผ่านระบบป้องกันของ Backend"
      : (propertyRole?.openingMessage || `Dashboard ของ ${title} แสดงข้อมูลในเครื่องแบบดูอย่างเดียว`);

  els.modalKind.textContent = isAgent ? "พื้นที่ทำงานของ Agent" : isKanban ? "ศูนย์ควบคุม Mission" : "Dashboard ของอุปกรณ์";
  els.modalTitle.textContent = title;
  els.modalSubtitle.textContent = isAgent ? `${role} | ${summary}` : summary;
  els.modalSpeaker.textContent = isAgent ? title : isKanban ? "คิว Mission ทั้งหมด" : `Dashboard: ${title}`;
  els.modalDialogue.textContent = isAgent ? (subject.status || speech) : speech;
  els.modalPortrait.src = getSubjectImage(subject, type);
  els.modalPortrait.alt = title;
  if (isAgent && els.modalCommandInput && document.activeElement !== els.modalCommandInput) {
    els.modalCommandInput.value = state.modal.lastPrompt || "";
    els.modalCommandInput.placeholder = isManagerWorkspace(subject)
      ? `ถาม ${subject.name} เพื่อช่วยคิด วางแผน หรือสรุปเป็นภาษาไทย...`
      : `ถาม ${subject.name} เกี่ยวกับหน้าที่ ${role} เป็นภาษาไทย...`;
  }
  if (els.modalAgentComposer) els.modalAgentComposer.hidden = !isAgent;
  if (els.modalDashboardConnectionRail) els.modalDashboardConnectionRail.hidden = surface !== "dashboard";
  if (els.workflowSettingsRail) els.workflowSettingsRail.hidden = !isWorkflowDashboard;
  if (els.workflowAgentHandoffRail) els.workflowAgentHandoffRail.hidden = true;
  if (els.modalPortraitPanel && !isWorkflowDashboard) delete els.modalPortraitPanel.dataset.dashboardIdentity;
  if (els.modalStatusGrid) els.modalStatusGrid.hidden = surface === "dashboard";

  if (isAgent) {
    renderStatusGrid([
      ["หน้าที่", role],
      ["สถานะ", subject.status],
      ["จุดทำงาน", displayPropName(subject.currentTarget || subject.defaultTarget)],
      ["Bridge", `${displayBridgeValue(state.bridge.mode)} / ${displayBridgeValue(state.bridge.status)}`],
      ["Memory", state.memoryStatus],
    ]);
    renderChatLog(subject, type);
    renderTaskList(els.modalTaskBoard, getRelevantMissionsForSubject(subject, type), "ยังไม่มี Task ที่มอบหมายให้ Agent นี้");
    renderAgentComposer(subject);
    const canManage = isManagerWorkspace(subject);
    if (els.modalMeetingButton) els.modalMeetingButton.hidden = !canManage;
    if (els.modalDelegateButton) els.modalDelegateButton.hidden = !canManage;
    setModalTab(state.modal.activeTab);
    return;
  }

  if (isKanban) {
    const counts = Object.fromEntries(MISSION_KANBAN_COLUMNS.map((column) => [
      column.id,
      state.missions.filter((mission) => getMissionPresentationStatus(mission) === column.id).length,
    ]));
    renderStatusGrid([
      ["Task ทั้งหมด", String(state.missions.length)],
      ["รอเริ่มงาน", String(counts.queued || 0)],
      ["กำลังทำงาน", String(counts.running || 0)],
      ["รออนุมัติ", String(counts.waiting_approval || 0)],
      ["ติดขัด", String((counts.blocked || 0) + (counts.failed || 0))],
      ["Bridge", `${displayBridgeValue(state.bridge.mode)} / ${displayBridgeValue(state.bridge.status)}`],
    ]);
    renderMissionKanban();
  } else {
    renderPropDashboard(subject, propertyRole);
  }
  setModalTab(state.modal.activeTab);
}

function openGameModal(type, id, tab = "chat") {
  if (els.taskDetailDialog?.open) closeTaskDetail({ restoreFocus: false });
  if (els.dashboardResultDialog?.open) closeDashboardResultDetail({ restoreFocus: false });
  state.modal.open = true;
  state.modal.type = type;
  state.modal.id = id;
  const surface = getModalSurface(type, id);
  if (surface === "dashboard" && isWorkflowDashboardPropId(id)) {
    delete state.modal.workflowTabs[id];
  }
  state.modal.activeTab = surface === "agent" ? tab : surface === "dashboard" ? "results" : "kanban";
  document.body.classList.add("modal-open");
  const subject = getModalSubject();
  if (subject && type === "agent") {
    state.modal.lastPrompt = "";
  } else {
    state.modal.lastPrompt = "";
  }
  els.gameModal?.classList.add("open");
  els.gameModalBackdrop?.classList.add("open");
  els.gameModal?.setAttribute("aria-hidden", "false");
  els.gameModalBackdrop?.setAttribute("aria-hidden", "false");
  renderGameModal();
  saveSessionSnapshot();
}

function closeGameModal() {
  if (els.taskDetailDialog?.open) closeTaskDetail({ restoreFocus: false });
  if (els.dashboardResultDialog?.open) closeDashboardResultDetail({ restoreFocus: false });
  if (state.modal.workflowVoice.recognition) stopWorkflowVoiceDictation();
  state.modal.open = false;
  document.body.classList.remove("modal-open");
  els.gameModal?.classList.remove("open");
  els.gameModal?.classList.remove("agent-modal", "prop-modal", "dashboard-modal", "signal-consensus-modal", "workflow-dashboard-modal", "kanban-modal");
  els.gameModalBackdrop?.classList.remove("open");
  els.gameModal?.setAttribute("aria-hidden", "true");
  els.gameModalBackdrop?.setAttribute("aria-hidden", "true");
  saveSessionSnapshot();
}

function openAgentDialog(agentId, tab = "chat") {
  showAgentPanel(agentId);
  const agent = getOfficeAgent(agentId);
  if (!agent) return;
  setAgentSpeech(agent.id, agent.status || getAgentSpeech(agent.id), "talking");
  const hasExistingChat = state.chatLog.some((line) => line.scopeType === "agent" && line.scopeId === agent.id);
  if (!hasExistingChat) {
    pushChatLine({
      scopeType: "agent",
      scopeId: agent.id,
      speaker: agent.name,
      text: getAgentSpeech(agent.id, "idle"),
      side: "agent",
    });
  }
  openGameModal("agent", agent.id, tab);
}

async function openPropDialog(propId, tab = null) {
  selectObject(propId, { loadBackendReport: false });
  openGameModal("prop", propId, tab || (propId === "mission_strategy_table" ? "kanban" : "dashboard"));
  const report = await loadPropReport(propId);
  if (report) renderGameModal();
}

function setConnectionActionState(propId, { inFlight = false, message = "", tone = "neutral" } = {}) {
  state.connectionAction = {
    inFlight: Boolean(inFlight),
    propId,
    message: safeDashboardDisplayText(message, ""),
    tone: ["neutral", "working", "success", "error"].includes(tone) ? tone : "neutral",
  };
  if (state.modal.open && state.modal.type === "prop" && state.modal.id === propId) {
    renderDashboardConnectionPanel(getModalSubject(), getPropertyRole(getModalSubject()));
  }
}

async function updatePropReportFromDashboardAction(propId, response) {
  if (response?.connectionChecklist && typeof response.connectionChecklist === "object" && !Array.isArray(response.connectionChecklist)) {
    state.propReports[propId] = {
      ...(state.propReports[propId] || {}),
      connectionChecklist: response.connectionChecklist,
    };
  }

  if (response?.propReport && typeof response.propReport === "object" && !Array.isArray(response.propReport)) {
    state.propReports[propId] = {
      ...(state.propReports[propId] || {}),
      ...response.propReport,
      ...(response.connectionChecklist ? { connectionChecklist: response.connectionChecklist } : {}),
    };
    return state.propReports[propId];
  }

  const reloadedReport = await loadPropReport(propId);
  return reloadedReport || state.propReports[propId] || null;
}

async function refreshDashboardConnections(propId) {
  if (!propId || state.connectionAction.inFlight) return null;
  setConnectionActionState(propId, {
    inFlight: true,
    message: "กำลังขอให้ Local Runner ตรวจการเชื่อมต่อแบบอ่านอย่างเดียว",
    tone: "working",
  });
  updateDecisionLog(`กำลังตรวจการเชื่อมต่อของ ${displayPropName(propId)}`);
  try {
    const response = await postJson(`/api/props/${encodeURIComponent(propId)}/connections/refresh`, { propId });
    await updatePropReportFromDashboardAction(propId, response);
    const message = safeDashboardDisplayText(response?.messageTh || response?.message, "ตรวจการเชื่อมต่อเสร็จแล้ว");
    setConnectionActionState(propId, { message, tone: "success" });
    updateDecisionLog(`ตรวจการเชื่อมต่อของ ${displayPropName(propId)} เสร็จแล้ว`);
    addBridgeEvent("ตรวจการเชื่อมต่อแล้ว", `${displayPropName(propId)} อัปเดตสถานะจาก Local Runner แล้ว`);
    return response;
  } catch {
    setConnectionActionState(propId, {
      message: "ตรวจการเชื่อมต่อไม่สำเร็จ กรุณาตรวจว่า Local Runner กำลังทำงานอยู่",
      tone: "error",
    });
    updateDecisionLog(`ยังตรวจการเชื่อมต่อของ ${displayPropName(propId)} ไม่สำเร็จ`);
    return null;
  } finally {
    state.connectionAction.inFlight = false;
    if (state.modal.open && state.modal.type === "prop" && state.modal.id === propId) renderGameModal();
  }
}

async function discoverMetatraderConnections(propId) {
  if (!propId || state.connectionAction.inFlight) return null;
  const report = state.propReports[propId];
  const canDiscover = Array.isArray(report?.connectionChecklist?.items)
    && report.connectionChecklist.items.some((item) => item?.action === "discover_metatrader");
  if (!canDiscover) return null;

  setConnectionActionState(propId, {
    inFlight: true,
    message: "กำลังส่งคำขอให้ Local Runner ค้นหา MT4 / MT5 แบบอ่านอย่างเดียว",
    tone: "working",
  });
  updateDecisionLog(`กำลังค้นหา MT4 / MT5 สำหรับ ${displayPropName(propId)}`);
  try {
    const response = await postJson("/api/integrations/metatrader/discover", { propId });
    await updatePropReportFromDashboardAction(propId, response);
    const message = safeDashboardDisplayText(response?.messageTh || response?.message, "ค้นหา MT4 / MT5 เสร็จแล้ว และอัปเดตเฉพาะสถานะที่ปลอดภัย");
    setConnectionActionState(propId, { message, tone: "success" });
    updateDecisionLog(`ค้นหา MT4 / MT5 สำหรับ ${displayPropName(propId)} เสร็จแล้ว`);
    addBridgeEvent("ค้นหา MT4 / MT5 แล้ว", `${displayPropName(propId)} ได้รับสถานะที่ปกปิดข้อมูลเครื่องแล้ว`);
    return response;
  } catch {
    setConnectionActionState(propId, {
      message: "ค้นหา MT4 / MT5 ไม่สำเร็จ ระบบไม่ได้แก้ไขไฟล์และไม่ได้เปิด Terminal",
      tone: "error",
    });
    updateDecisionLog(`ยังค้นหา MT4 / MT5 สำหรับ ${displayPropName(propId)} ไม่สำเร็จ`);
    return null;
  } finally {
    state.connectionAction.inFlight = false;
    if (state.modal.open && state.modal.type === "prop" && state.modal.id === propId) renderGameModal();
  }
}

async function confirmMetatraderSelection(propId) {
  if (!propId || state.connectionAction.inFlight) return null;
  const checklist = state.propReports[propId]?.connectionChecklist;
  const canDiscover = Array.isArray(checklist?.items)
    && checklist.items.some((item) => item?.action === "discover_metatrader");
  const selection = getMetatraderSelectionModel(checklist);
  const candidateId = String(state.metatraderCandidateChoice[propId] || "");
  const candidate = selection.candidates.find((item) => item.candidateId === candidateId && item.detected);
  if (!canDiscover || !selection.canSelect || !candidate) return null;

  setConnectionActionState(propId, {
    inFlight: true,
    message: `กำลังยืนยัน ${candidate.labelTh} เป็น Terminal เป้าหมายกับ Local Runner`,
    tone: "working",
  });
  updateDecisionLog(`กำลังยืนยัน Terminal เป้าหมายสำหรับ ${displayPropName(propId)}`);
  try {
    await postJson("/api/integrations/metatrader/select", { propId, candidateId });
    const refreshedReport = await loadPropReport(propId);
    if (!refreshedReport) throw new Error("report_reload_failed");
    const refreshedSelection = getMetatraderSelectionModel(refreshedReport.connectionChecklist);
    if (refreshedSelection.selectedCandidate?.candidateId !== candidateId) throw new Error("selection_not_confirmed");
    state.metatraderCandidateChoice[propId] = refreshedSelection.selectedCandidate.candidateId;
    setConnectionActionState(propId, {
      message: `เลือก ${candidate.labelTh} แล้ว • Adapter สั่งงานจริงยังไม่พร้อม`,
      tone: "success",
    });
    updateDecisionLog(`เลือก Terminal เป้าหมายของ ${displayPropName(propId)} แล้ว โดยยังไม่เชื่อม Adapter สั่งงานจริง`);
    addBridgeEvent("เลือก Terminal เป้าหมายแล้ว", `${displayPropName(propId)} บันทึกเฉพาะ Opaque Candidate ID ผ่าน Local Runner`);
    return refreshedReport;
  } catch {
    setConnectionActionState(propId, {
      message: "ยังยืนยัน Terminal ที่เลือกไม่สำเร็จ ระบบไม่ได้เปิด Terminal และไม่ได้เชื่อมบัญชี",
      tone: "error",
    });
    updateDecisionLog(`ยังยืนยัน Terminal เป้าหมายของ ${displayPropName(propId)} ไม่สำเร็จ`);
    return null;
  } finally {
    state.connectionAction.inFlight = false;
    if (state.modal.open && state.modal.type === "prop" && state.modal.id === propId) renderGameModal();
  }
}

function isMetatraderDiscoveryIntent(prompt) {
  const text = String(prompt || "").trim().toLowerCase();
  const mentionsTerminal = /(^|[^a-z0-9])(mt4|mt5|metatrader|terminal)([^a-z0-9]|$)/.test(text)
    || ["เทอร์มินัล", "โปรแกรมเทรด"].some((keyword) => text.includes(keyword));
  const asksToInspect = [
    "check", "search", "find", "scan", "detect", "discover", "list", "status",
    "ตรวจ", "ตรวจสอบ", "เช็ค", "เชค", "ค้น", "ค้นหา", "หา", "ดูสถานะ", "มีกี่", "มีไหม",
  ].some((keyword) => text.includes(keyword));
  return mentionsTerminal && asksToInspect;
}

function reportSupportsMetatraderDiscovery(report) {
  return Array.isArray(report?.connectionChecklist?.items)
    && report.connectionChecklist.items.some((item) => item?.action === "discover_metatrader");
}

async function resolveMetatraderDiscoveryProp(subject) {
  const preferredIds = [subject?.defaultTarget, subject?.homeTarget, "terminal_workstation"]
    .filter((value, index, values) => value && values.indexOf(value) === index);
  for (const propId of preferredIds) {
    const report = state.propReports[propId] || await loadPropReport(propId);
    if (reportSupportsMetatraderDiscovery(report)) return propId;
  }
  return null;
}

async function runMetatraderDiscoveryIntent(subject) {
  const propId = await resolveMetatraderDiscoveryProp(subject);
  if (!propId) {
    return {
      ok: false,
      kind: "metatrader_discovery_unavailable",
      propId: null,
      candidateCount: 0,
      reply: "ยังไม่พบ Dashboard ที่รองรับการค้นหา MT4 / MT5 จึงยังไม่มี Tool ใดทำงาน",
    };
  }
  const response = await discoverMetatraderConnections(propId);
  const selection = getMetatraderSelectionModel(state.propReports[propId]?.connectionChecklist);
  return {
    ok: Boolean(response),
    kind: "metatrader_discovery",
    propId,
    candidateCount: selection.candidateCount,
    reply: response
      ? `Local Runner ตรวจแบบอ่านอย่างเดียวแล้ว พบ ${selection.candidateCount} Terminal กรุณาเลือก Terminal เป้าหมายใน ${displayPropName(propId)} • Adapter สั่งงานจริงยังไม่พร้อม และระบบไม่ได้เปิด MT4 / MT5`
      : "ค้นหา MT4 / MT5 ไม่สำเร็จ ระบบไม่ได้เปิด Terminal ไม่ได้เชื่อมบัญชี และไม่ได้เรียก Codex",
  };
}

function getPromptFromModal() {
  const prompt = String(els.modalCommandInput?.value || state.modal.lastPrompt || "").trim();
  state.modal.lastPrompt = prompt;
  return prompt;
}

function isExplicitDelegationIntent(prompt) {
  const text = String(prompt || "").toLowerCase();
  return ["delegate", "create task", "create mission", "queue this", "assign this", "มอบหมาย", "แตกงาน", "สร้างงาน", "สร้าง task", "สร้าง mission"]
    .some((keyword) => text.includes(keyword));
}

function createAgentChatOpaqueId(prefix) {
  const randomValue = window.crypto?.randomUUID?.()
    || `${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}-${Math.random().toString(36).slice(2)}`;
  return `${prefix}-${String(randomValue).replace(/[^a-zA-Z0-9._:-]/g, "-")}`.slice(0, 160);
}

function getAgentChatSessionId(agentId) {
  const current = String(state.agentChat.sessionIds[agentId] || "");
  if (/^[a-zA-Z0-9][a-zA-Z0-9._:-]{0,159}$/.test(current)) return current;
  const sessionId = createAgentChatOpaqueId(`visual-chat-${agentId}`);
  state.agentChat.sessionIds[agentId] = sessionId;
  saveSessionSnapshot();
  return sessionId;
}

function setAgentChatStatus(agentId, message, tone = "neutral") {
  state.agentChat.agentId = agentId || null;
  state.agentChat.message = safeDashboardDisplayText(message, "กำลังตรวจสอบสถานะแชท");
  state.agentChat.tone = ["neutral", "working", "ready", "error"].includes(tone) ? tone : "neutral";
  if (state.modal.open && state.modal.type === "agent" && state.modal.id === agentId && els.modalChatStatus) {
    els.modalChatStatus.textContent = state.agentChat.message;
    els.modalChatStatus.dataset.tone = state.agentChat.tone;
  }
}

function validateAgentChatResponse(response, subject) {
  const sessionId = String(response?.sessionId || "");
  const turnId = String(response?.turnId || "");
  const taskCreated = response?.taskCreated === true;
  const taskMissionIds = Array.isArray(response?.taskMissionIds)
    ? response.taskMissionIds.map((item) => String(item || "")).filter(Boolean)
    : null;
  const taskStatus = String(response?.taskStatus || "").trim().toLowerCase().replace(/[ -]+/g, "_");
  const autoExecute = response?.autoExecute === true;
  const validMissionIds = taskMissionIds !== null
    && taskMissionIds.length <= 20
    && taskMissionIds.every((item) => /^[a-zA-Z0-9][a-zA-Z0-9._:-]{0,159}$/.test(item));
  const validTaskContract = typeof response?.taskCreated === "boolean"
    && typeof response?.autoExecute === "boolean"
    && validMissionIds
    && (taskCreated ? taskMissionIds.length > 0 : taskMissionIds.length === 0)
    && (!taskCreated || ["queued", "running", "waiting_approval", "blocked", "completed", "failed", "archived"].includes(taskStatus))
    && (!autoExecute || taskCreated);
  const idempotentReplay = response?.usage?.idempotentReplay === true;
  const quotaConsumptionStatus = String(response?.usage?.quotaConsumptionStatus || "");
  const quotaFlagIsValid = idempotentReplay
    ? response?.consumesCodexQuota === false && quotaConsumptionStatus === "none"
    : response?.consumesCodexQuota === true && quotaConsumptionStatus === "confirmed";
  const exactSuccess = response?.ok === true
    && response?.kind === "agent_chat"
    && response?.status === "completed"
    && response?.agentId === subject.id
    && typeof response?.agentName === "string"
    && typeof response?.reply === "string"
    && response.reply.trim().length > 0
    && typeof response?.modelTier === "string"
    && quotaFlagIsValid
    && typeof response?.toolsExecuted === "boolean"
    && validTaskContract
    && response?.usage
    && typeof response.usage === "object"
    && !Array.isArray(response.usage)
    && /^[a-zA-Z0-9][a-zA-Z0-9._:-]{0,159}$/.test(sessionId)
    && /^[a-zA-Z0-9][a-zA-Z0-9._:-]{0,159}$/.test(turnId);
  if (!exactSuccess) {
    const error = new Error("invalid_agent_chat_response");
    error.kind = "invalid_agent_chat_response";
    throw error;
  }
  return {
    reply: safeAgentChatReplyText(response.reply),
    sessionId,
    idempotentReplay,
    quotaConsumptionStatus,
    taskCreated,
    taskMissionIds,
    taskStatus: taskCreated ? taskStatus : null,
    autoExecute,
    toolsExecuted: response.toolsExecuted,
  };
}

async function syncAgentChatCreatedTasks(subject, validated) {
  if (!validated.taskCreated) return [];
  await loadBridgeMissions({ replaceEvents: false, persist: false });
  const missions = validated.taskMissionIds
    .map((missionId) => state.missions.find((mission) => mission.id === missionId))
    .filter(Boolean);
  const targetIds = [...new Set(missions.map((mission) => mission.targetId).filter(Boolean))];

  missions.forEach((mission) => {
    const ownerAgentId = getAgentIdFromOwner(mission.owner);
    if (ownerAgentId && mission.targetId && getTargetPoint(mission.targetId)) {
      routeAgentToTargetId(ownerAgentId, mission.targetId, `Task ${displayStatus(getMissionPresentationStatus(mission))}`, {
        select: false,
        persist: false,
      });
    }
  });
  await Promise.all(targetIds.map((targetId) => loadPropReport(targetId)));

  const primaryMission = missions[0];
  const destination = primaryMission?.targetId
    ? displayPropName(primaryMission.targetId)
    : "อุปกรณ์ที่ Backend กำหนด";
  const status = primaryMission ? getMissionPresentationStatus(primaryMission) : validated.taskStatus;
  const statusMessage = validated.autoExecute
    ? `สร้าง ${validated.taskMissionIds.length} Task แล้ว • Backend รับไปทำอัตโนมัติ • รายงานที่ ${destination}`
    : `สร้าง ${validated.taskMissionIds.length} Task แล้ว • สถานะ ${displayStatus(status || "queued")} • รายงานที่ ${destination}`;
  setAgentChatStatus(subject.id, statusMessage, "ready");
  addBridgeEvent(
    validated.autoExecute ? "Agent เริ่มงานจากบทสนทนาแล้ว" : "Agent สร้าง Task จากบทสนทนาแล้ว",
    `${validated.taskMissionIds.length} Task • ${displayStatus(status || "queued")} → ${destination}`,
  );
  updateDecisionLog(`${subject.name} สร้าง Mission จากบทสนทนาแล้ว ไม่ต้องกดสร้าง Task ซ้ำ`);
  return missions;
}

function agentChatErrorMessage(error) {
  const kind = String(error?.body?.kind || error?.kind || "").trim().toLowerCase();
  if (error?.status === 429 || ["rate_limited", "codex_limit_reached"].includes(kind)) {
    return "โควตา Codex ยังไม่พร้อมสำหรับข้อความนี้ กรุณารอตามเวลาที่ระบบกำหนดแล้วลองใหม่";
  }
  if (error?.status === 409 || ["idempotency_conflict", "runner_busy"].includes(kind)) {
    return "Codex กำลังตอบคำขออื่นอยู่ กรุณารอสักครู่แล้วส่งข้อความนี้ใหม่";
  }
  if (error?.status === 413 || kind === "message_too_large") {
    return "ข้อความยาวเกินขอบเขตที่ปลอดภัย กรุณาย่อข้อความแล้วลองใหม่";
  }
  if (kind === "secret_blocked") {
    return "Risk Guard หยุดข้อความนี้ เพราะอาจมีรหัสผ่าน Token หรือข้อมูลลับ กรุณาลบข้อมูลลับก่อนส่งใหม่";
  }
  if (error?.status === 422 || kind === "invalid_request") {
    return "ข้อความนี้ยังไม่ผ่านเงื่อนไขของระบบ กรุณาเขียนคำถามใหม่โดยไม่ใส่ข้อมูลลับหรือคำสั่งรันงานจริง";
  }
  if (error?.status === 503 || ["runner_not_ready", "auth_required", "config_error"].includes(kind)) {
    return "ระบบแชท Codex ใน Local Runner ยังไม่พร้อม กรุณาตรวจสถานะ Codex Login และ Config ก่อนลองใหม่";
  }
  if (error?.status === 504 || kind === "timeout") {
    return "Codex ใช้เวลาตอบเกินกำหนด ระบบหยุดคำขอนี้แล้วและจะไม่ส่งซ้ำอัตโนมัติ";
  }
  if (error?.status === 404) {
    return "ระบบแชท Agent ยังไม่พร้อมใช้งานใน Local Runner เวอร์ชันนี้";
  }
  if (kind === "invalid_agent_chat_response") {
    return "Backend ส่งผลแชทกลับมาไม่ครบตามสัญญาความปลอดภัย จึงไม่แสดงคำตอบนี้";
  }
  if (error?.status >= 500) {
    return "Agent ยังตอบไม่ได้เพราะ Local Runner มีปัญหาชั่วคราว กรุณาเปิด Mission Table ตรวจว่ามี Task ถูกสร้างไว้หรือไม่ก่อนส่งข้อความซ้ำ";
  }
  return "ติดต่อระบบแชท Agent ไม่สำเร็จ กรุณาตรวจว่า Local Runner กำลังทำงาน แล้วลองใหม่";
}

async function handleModalSend() {
  const subject = getModalSubject();
  if (!subject || state.modal.type !== "agent" || state.agentChat.inFlight) return;
  const prompt = getPromptFromModal();
  if (!prompt) {
    setAgentChatStatus(subject.id, "กรุณาพิมพ์ข้อความที่ต้องการคุยกับ Agent ก่อนส่ง", "error");
    els.modalCommandInput?.focus();
    return;
  }
  if (blockSecretIntent(prompt, state.modal.type, subject.id)) {
    setAgentChatStatus(subject.id, "Risk Guard หยุดข้อความที่อาจมีข้อมูลลับก่อนส่งออกจากหน้าเว็บ", "error");
    renderGameModal();
    return;
  }
  pushChatLine({
    scopeType: state.modal.type,
    scopeId: subject.id,
    speaker: "คุณ",
    text: prompt,
    side: "user",
  });

  state.agentChat.inFlight = true;
  state.agentChat.agentId = subject.id;
  renderAgentStatusPanel();
  if (els.modalSendButton) {
    els.modalSendButton.disabled = true;
    els.modalSendButton.textContent = "กำลังคิด...";
  }
  setAgentChatStatus(subject.id, "Agent กำลังตอบและให้ Backend ตรวจว่าคำสั่งนี้ควรสร้าง Task หรือไม่", "working");
  setAgentSpeech(subject.id, "กำลังคิดคำตอบให้คุณครับ", "working");
  let reply = "";
  let dashboardToOpen = null;
  try {
    if (isMetatraderDiscoveryIntent(prompt)) {
      setAgentChatStatus(subject.id, "กำลังส่งคำสั่งตรวจ MT4 / MT5 แบบอ่านอย่างเดียวไปยัง Local Runner โดยไม่ใช้โควตา Codex", "working");
      const result = await runMetatraderDiscoveryIntent(subject);
      reply = result.reply;
      dashboardToOpen = result.ok ? result.propId : null;
      setAgentChatStatus(
        subject.id,
        result.ok
          ? "ตรวจแบบอ่านอย่างเดียวเสร็จแล้ว • ไม่ใช้โควตา Codex • ไม่เปิด Terminal"
          : "ยังตรวจ MT4 / MT5 ไม่สำเร็จ • ไม่ได้เรียก Codex และไม่ได้เปิด Terminal",
        result.ok ? "ready" : "error",
      );
    } else {
      const response = await postJson(AGENT_CHAT_ENDPOINT, {
        agentId: subject.id,
        message: prompt,
        sessionId: getAgentChatSessionId(subject.id),
        idempotencyKey: createAgentChatOpaqueId("visual-agent-chat"),
      });
      const validated = validateAgentChatResponse(response, subject);
      state.agentChat.sessionIds[subject.id] = validated.sessionId;
      reply = validated.reply;
      if (validated.taskCreated) {
        await syncAgentChatCreatedTasks(subject, validated);
      } else {
        setAgentChatStatus(
          subject.id,
          validated.idempotentReplay
            ? "Agent คืนคำตอบเดิมจากคำขอที่บันทึกไว้ • ไม่ใช้โควตา Codex ซ้ำ"
            : "Agent ตอบแล้ว • ยังไม่มี Task ใหม่จากข้อความนี้",
          "ready",
        );
      }
      void refreshCodexRateLimits({ manual: false });
      saveSessionSnapshot();
    }
  } catch (error) {
    reply = agentChatErrorMessage(error);
    setAgentChatStatus(subject.id, reply, "error");
  } finally {
    state.agentChat.inFlight = false;
    renderAgentStatusPanel();
    state.modal.lastPrompt = "";
    if (els.modalCommandInput) els.modalCommandInput.value = "";
    setAgentSpeech(subject.id, reply, "talking");
    pushChatLine({ scopeType: "agent", scopeId: subject.id, speaker: subject.name, text: reply, side: "agent" });
    if (els.modalSendButton) {
      els.modalSendButton.disabled = false;
      els.modalSendButton.textContent = "คุยกับ Codex";
    }
    if (dashboardToOpen) await openPropDialog(dashboardToOpen);
    else renderGameModal();
  }
}

async function handleModalAssignTask() {
  const subject = getModalSubject();
  if (!subject || state.modal.type !== "agent") return;
  const prompt = getPromptFromModal();
  if (!prompt) {
    setAgentChatStatus(subject.id, "กรุณาพิมพ์รายละเอียดงานก่อนสร้าง Task", "error");
    els.modalCommandInput?.focus();
    return;
  }
  if (blockSecretIntent(prompt, state.modal.type, subject.id)) {
    renderGameModal();
    return;
  }
  const task = { title: prompt.slice(0, 72), detail: prompt };
  if (els.modalAssignButton) els.modalAssignButton.disabled = true;
  const mission = await assignTask(subject.id, task);
  if (els.modalAssignButton) els.modalAssignButton.disabled = false;
  if (!mission?.backendAccepted) {
    pushChatLine({
      scopeType: state.modal.type,
      scopeId: subject.id,
      speaker: "คิวงานในเครื่อง",
      text: mission?.detail || "Backend ยังไม่รับคำขอสร้าง Task และยังไม่มี Tool ใดทำงาน",
      side: "agent",
    });
    renderGameModal();
    return;
  }
  const assignee = getOfficeAgent(mission.owner) || getOfficeAgent(state.selectedAgentId);
  const presentationStatus = getMissionPresentationStatus(mission);
  const autoEligible = isBackendAutoEligibleMission(mission);
  pushChatLine({
    scopeType: state.modal.type,
    scopeId: subject.id,
    speaker: assignee?.name || "Manager Agent",
    text: autoEligible
      ? `Backend สร้าง Task ${mission.id} ให้ ${assignee?.name || mission.owner} แล้ว • ${displayStatus(presentationStatus)} • ผลงานจะส่งไปที่ ${displayPropName(mission.targetId)}`
      : `Backend สร้าง Task ${mission.id} ให้ ${assignee?.name || mission.owner} แล้ว • ${displayStatus(presentationStatus)} • รอขั้นตอนตามระบบป้องกัน`,
    side: "agent",
  });
  state.modal.lastPrompt = "";
  if (els.modalCommandInput) els.modalCommandInput.value = "";
  setAgentChatStatus(
    subject.id,
    autoEligible
      ? `Task ${mission.id} ${displayStatus(presentationStatus)} อัตโนมัติแล้ว • ไม่ต้องกดอนุมัติซ้ำ`
      : `สร้าง Task ${mission.id} แล้ว • ${displayStatus(presentationStatus)} • Backend จะตรวจสิทธิ์ก่อนเริ่ม`,
    "ready",
  );
  state.modal.activeTab = "tasks";
  renderGameModal();
}

async function loadNavigationMask(navigation = {}) {
  const blockerMode = navigation.blockerMode || "mask-and-blockers";
  state.navigation.clickBlockers = navigation.blockers || [];
  state.navigation.blockers = blockerMode === "mask-only" ? [] : (navigation.blockers || []);
  state.navigation.grid = navigation.grid || state.navigation.grid;
  state.navigation.alphaThreshold = navigation.maskAlphaThreshold ?? state.navigation.alphaThreshold;
  state.navigation.maskMode = navigation.maskMode || state.navigation.maskMode;
  state.navigation.agentFootprint = {
    ...state.navigation.agentFootprint,
    ...(navigation.agentFootprint || {}),
  };
  state.navigation.agentBlockerFootprint = {
    ...state.navigation.agentBlockerFootprint,
    ...(navigation.agentBlockerFootprint || {}),
  };
  state.navigation.walkSpeed = {
    ...DEFAULT_WALK_SPEED,
    ...(navigation.walkSpeed || {}),
  };

  if (!navigation.walkableMask) {
    state.navigation.mask = null;
    return;
  }

  const image = new Image();
  image.decoding = "async";
  image.draggable = false;

  await new Promise((resolve, reject) => {
    const timeoutId = window.setTimeout(() => {
      image.onload = null;
      image.onerror = null;
      reject(new Error(`โหลดพื้นที่เดิน ${navigation.walkableMask} ไม่สำเร็จภายในเวลาที่กำหนด`));
    }, 4000);
    image.onload = () => {
      window.clearTimeout(timeoutId);
      resolve();
    };
    image.onerror = () => {
      window.clearTimeout(timeoutId);
      reject(new Error(`ไม่สามารถโหลดพื้นที่เดิน ${navigation.walkableMask} ได้`));
    };
    image.src = resolveProjectAssetPath(navigation.walkableMask);
  });

  const canvas = document.createElement("canvas");
  canvas.width = image.naturalWidth;
  canvas.height = image.naturalHeight;
  const context = canvas.getContext("2d", { willReadFrequently: true });
  context.drawImage(image, 0, 0);

  state.navigation.mask = {
    image,
    canvas,
    context,
    width: canvas.width,
    height: canvas.height,
  };
}

function getInteractiveObjects() {
  return state.data.props || state.data.hotspots || [];
}

function renderLayers() {
  els.layerList.innerHTML = "";

  state.data.layers.forEach((layer) => {
    const layerObjects = getInteractiveObjects().filter((item) => item.layer === layer.id);
    const label = document.createElement("label");
    label.className = "layer-toggle";
    const input = document.createElement("input");
    const textWrap = document.createElement("span");
    const layerName = document.createElement("span");
    const layerDescription = document.createElement("span");
    const layerCount = document.createElement("span");
    input.type = "checkbox";
    input.checked = state.visibleLayers.has(layer.id);
    layerName.className = "layer-name";
    layerDescription.className = "layer-desc";
    layerCount.className = "layer-count";
    const layerDisplay = LAYER_DISPLAY[layer.id];
    layerName.textContent = layerDisplay?.[0] || layer.name;
    layerDescription.textContent = layerDisplay?.[1] || layer.description;
    layerCount.textContent = String(layerObjects.length);
    textWrap.append(layerName, layerDescription);
    label.append(input, textWrap, layerCount);

    input.addEventListener("change", (event) => {
      if (event.target.checked) {
        state.visibleLayers.add(layer.id);
      } else {
        state.visibleLayers.delete(layer.id);
      }
      updatePropVisibility();
    });

    els.layerList.appendChild(label);
  });
}

function renderProps() {
  els.propLayer.innerHTML = "";
  state.propHitTargets.clear();
  state.hoveredPropId = null;

  getInteractiveObjects().forEach((spot) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `prop-button prop-${spot.status || "idle"}`;
    button.dataset.id = spot.id;
    button.dataset.layer = spot.layer;
    const propLabel = displayPropName(spot.id, spot.label);
    button.dataset.label = propLabel;
    button.dataset.status = spot.status || "idle";
    button.setAttribute("aria-label", `เปิด ${propLabel}`);

    applyPropPlacement(button, spot);
    applyGlowColor(button, spot);

    if (spot.asset) {
      const image = document.createElement("img");
      image.src = resolveProjectAssetPath(spot.asset);
      image.alt = "";
      image.draggable = false;
      button.appendChild(image);
      registerPropHitTarget(button, spot, image);
    }

    els.propLayer.appendChild(button);
  });

  updatePropVisibility();
}

function registerPropHitTarget(button, spot, image) {
  const target = {
    button,
    spot,
    image,
    ready: false,
    context: null,
    width: 0,
    height: 0,
    alphaThreshold: spot.hitAlphaThreshold ?? PROP_HIT_ALPHA_THRESHOLD,
    hitArea: spot.hitArea || null,
  };
  state.propHitTargets.set(spot.id, target);

  const buildMask = () => {
    if (!image.naturalWidth || !image.naturalHeight) return;
    const canvas = document.createElement("canvas");
    canvas.width = image.naturalWidth;
    canvas.height = image.naturalHeight;
    const context = canvas.getContext("2d", { willReadFrequently: true });
    context.drawImage(image, 0, 0);
    target.context = context;
    target.width = canvas.width;
    target.height = canvas.height;
    target.ready = true;
  };

  if (image.complete && image.naturalWidth) {
    buildMask();
  } else {
    image.addEventListener("load", buildMask, { once: true });
    image.addEventListener("error", () => {
      target.ready = false;
    }, { once: true });
  }
}

function setHoveredProp(propId) {
  if (state.hoveredPropId === propId) return;
  state.hoveredPropId = propId;
  els.stage.classList.toggle("prop-hit", Boolean(propId));

  [...els.propLayer.children].forEach((node) => {
    node.classList.toggle("pixel-hover", node.dataset.id === propId);
  });
}

function getPropHitAtEvent(event, options = {}) {
  const pixelHit = getPropPixelHitAtEvent(event);
  if (pixelHit) return pixelHit;
  if (options.allowNavigationFallback === false) return null;

  return getPropAtNavigationPoint(getStagePoint(event));
}

function getPropPixelHitAtEvent(event) {
  const stageRect = els.stage.getBoundingClientRect();
  const targets = [...state.propHitTargets.values()]
    .filter((target) => canHitProp(target))
    .sort((a, b) => getPropZ(b.spot) - getPropZ(a.spot));

  return targets.find((target) => isPointerOnPropPixel(event, target, stageRect))?.spot || null;
}

function canHitProp(target) {
  if (!target?.ready || !target.context) return false;
  if (!state.visibleLayers.has(target.spot.layer)) return false;
  if (target.button.disabled || target.button.classList.contains("dimmed")) return false;
  return true;
}

function getPropAtNavigationPoint(point) {
  const blocker = findPropClickBlocker(point);
  if (!blocker?.id) return null;

  const propId = blocker.id.replace(/_collision$/, "");
  const spot = getInteractiveObjects().find((item) => item.id === propId);
  if (!spot || !state.visibleLayers.has(spot.layer)) return null;
  if (spot.strictPixelHit) return null;

  return spot;
}

function findPropClickBlocker(point) {
  return state.navigation.clickBlockers.find((blocker) => isPointInsideBlocker(point, blocker)) || null;
}

function getPropZ(spot) {
  const placement = spot.position || spot.rect || {};
  return Number(placement.z || 0);
}

function getPropScreenRect(spot, stageRect) {
  const placement = spot.position || spot.rect || { x: 0, y: 0, w: 10, h: 10 };
  const left = stageRect.left + (placement.x / 100) * stageRect.width;
  const top = stageRect.top + (placement.y / 100) * stageRect.height;
  const width = (placement.w / 100) * stageRect.width;
  let height = placement.h ? (placement.h / 100) * stageRect.height : width;

  if (!placement.h && spot.size?.[0] && spot.size?.[1]) {
    height = width * (spot.size[1] / spot.size[0]);
  }

  return { left, top, width, height };
}

function isPointerOnPropPixel(event, target, stageRect) {
  const rect = getPropScreenRect(target.spot, stageRect);
  const imageRect = getRenderedPropImageRect(rect, target);
  const localX = (event.clientX - imageRect.left) / imageRect.width;
  const localY = (event.clientY - imageRect.top) / imageRect.height;

  if (localX < 0 || localX > 1 || localY < 0 || localY > 1) return false;
  if (!isPointerInsidePropHitArea(localX, localY, target.hitArea)) return false;

  const pixelX = Math.round(localX * (target.width - 1));
  const pixelY = Math.round(localY * (target.height - 1));
  const alpha = target.context.getImageData(pixelX, pixelY, 1, 1).data[3];
  return alpha >= target.alphaThreshold;
}

function isPointerInsidePropHitArea(localX, localY, hitArea) {
  if (!hitArea) return true;
  if (hitArea.type === "rect") {
    return (
      localX >= (hitArea.x ?? 0)
      && localY >= (hitArea.y ?? 0)
      && localX <= (hitArea.x ?? 0) + (hitArea.w ?? 1)
      && localY <= (hitArea.y ?? 0) + (hitArea.h ?? 1)
    );
  }
  if (hitArea.type === "polygon" && Array.isArray(hitArea.points)) {
    return pointInPolygon({ x: localX, y: localY }, hitArea.points);
  }
  return true;
}

function getRenderedPropImageRect(rect, target) {
  if (!target.width || !target.height || !rect.width || !rect.height) return rect;

  const boxRatio = rect.width / rect.height;
  const imageRatio = target.width / target.height;
  if (imageRatio > boxRatio) {
    const height = rect.width / imageRatio;
    return {
      left: rect.left,
      top: rect.top + (rect.height - height) / 2,
      width: rect.width,
      height,
    };
  }

  const width = rect.height * imageRatio;
  return {
    left: rect.left + (rect.width - width) / 2,
    top: rect.top,
    width,
    height: rect.height,
  };
}

function appendAgentVisual(node, { bubbleText, name, image, bubbleId = "", imageId = "" }) {
  const bubble = document.createElement("span");
  const nameplate = document.createElement("span");
  const spriteWindow = document.createElement("span");
  const frame = document.createElement("img");
  const fallback = document.createElement("span");
  bubble.className = "agent-bubble";
  nameplate.className = "agent-nameplate";
  spriteWindow.className = "agent-sprite-window";
  spriteWindow.setAttribute("aria-hidden", "true");
  frame.className = "agent-frame";
  fallback.className = "agent-frame-fallback";
  fallback.hidden = true;
  fallback.textContent = String(name || "AI")
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0])
    .join("")
    .toUpperCase() || "AI";
  frame.alt = "";
  frame.draggable = false;
  if (bubbleId) bubble.id = bubbleId;
  if (imageId) frame.id = imageId;
    bubble.textContent = bubbleText || "พร้อมรับงาน";
  nameplate.textContent = name || "Agent";
  frame.addEventListener("error", () => {
    frame.hidden = true;
    fallback.hidden = false;
    spriteWindow.classList.add("asset-unavailable");
    reportBootResourceFailure(image || "ภาพ Agent", new Error(`ไม่พบภาพของ ${name || "Agent"}`));
  }, { once: true });
  frame.src = withAgentAssetVersion(image);
  spriteWindow.append(frame, fallback);
  node.append(bubble, nameplate, spriteWindow);
}

function renderAgent() {
  els.agentLayer.innerHTML = "";

  const target = document.createElement("div");
  target.className = "walk-target";
  target.id = "walkTarget";
  els.agentLayer.appendChild(target);

  const agent = document.createElement("button");
  agent.type = "button";
  agent.id = "hqManagerAgent";
  agent.dataset.agentId = state.agent.id;
  agent.className = "agent-unit office-agent manager-agent static-roster idle";
  agent.setAttribute("aria-label", `${state.agent.name} ${state.agent.role}`);
  appendAgentVisual(agent, {
    bubbleText: state.agent.status,
    name: state.agent.name,
    image: state.agent.frameImage,
    bubbleId: "agentBubble",
    imageId: "agentFrameImage",
  });
  agent.addEventListener("click", (event) => {
    event.stopPropagation();
    openAgentDialog(state.agent.id);
  });
  els.agentLayer.appendChild(agent);
  applyAgentPosition(false);
  startSpriteLoop("idle", "down");

  state.officeAgents
    .filter((officeAgent) => officeAgent.id !== state.agent.id)
    .forEach((officeAgent) => {
      const node = document.createElement("button");
      node.type = "button";
      node.id = getAgentNodeId(officeAgent.id);
      node.dataset.agentId = officeAgent.id;
      node.className = "agent-unit office-agent support-agent static-roster idle";
      node.setAttribute("aria-label", `${officeAgent.name} ${officeAgent.role}`);
      appendAgentVisual(node, {
        bubbleText: officeAgent.status,
        name: officeAgent.name,
        image: officeAgent.image,
        imageId: `agentFrameImage-${officeAgent.id}`,
      });
      node.addEventListener("click", (event) => {
        event.stopPropagation();
        openAgentDialog(officeAgent.id);
      });
      els.agentLayer.appendChild(node);
      updateAgentNodeState(officeAgent);
      startAgentSpriteLoop(officeAgent, "idle", officeAgent.direction || "down");
    });

  setSelectedAgent(state.selectedAgentId);
}

function applyAgentPosition(animated = true) {
  const node = document.getElementById("hqManagerAgent");
  if (!node) return;

  node.style.setProperty("--agent-x", state.agent.x.toFixed(3));
  node.style.setProperty("--agent-y", state.agent.y.toFixed(3));
  node.style.setProperty("--agent-w", state.agent.w.toFixed(3));
  node.style.setProperty("--agent-z", getDepthZ(state.agent.y));
  node.style.setProperty("--agent-speed", animated ? `${state.agent.speedMs}ms` : "1ms");
  syncSpriteVariables(node);

  const bubble = document.getElementById("agentBubble");
  if (bubble) bubble.textContent = state.agent.status;
  syncManagerOfficeAgent();
}

function syncSpriteVariables(node = document.getElementById("hqManagerAgent")) {
  if (!node) return;
  const agentId = node.dataset.agentId || state.agent.id;
  const agent = getOfficeAgent(agentId) || state.agent;
  const sprite = ensureAgentSprite(agent);
  node.dataset.spriteMode = sprite.mode || "status";
  node.dataset.spriteFrame = String(sprite.frame || 0);
}

function startSpriteLoop(mode, direction = state.agent.direction) {
  return startAgentSpriteLoop(state.agent, mode, direction);
}

function startAgentSpriteLoop(agent, mode, direction = agent?.direction || "down", options = {}) {
  if (!agent) return null;
  const sprite = ensureAgentSprite(agent);
  const statusKey = options.statusKey || getStatusKeyForAgent(agent);
  const frames = getAgentFramesFor(agent, mode, direction, statusKey);
  const fps = getAgentAnimationFps(sprite.animationMap, mode, direction, statusKey);
  const frameCount = frames.length;

  stopAgentSpriteLoop(agent.id);
  sprite.mode = mode === "walk" ? "walk" : "status";
  sprite.currentFrames = frames;
  sprite.frame = 0;
  updateAgentFrameImageForAgent(agent, frames[0]);
  syncSpriteVariables(document.getElementById(getAgentNodeId(agent.id)));

  if (frameCount <= 1) return null;

  const timer = window.setInterval(() => {
    sprite.frame = (sprite.frame + 1) % frameCount;
    updateAgentFrameImageForAgent(agent, frames[sprite.frame]);
    syncSpriteVariables(document.getElementById(getAgentNodeId(agent.id)));
  }, Math.round(1000 / fps));

  if (agent.id === state.agent.id) {
    state.agentSpriteTimer = timer;
  } else {
    state.supportSpriteTimers.set(agent.id, timer);
  }
  return timer;
}

function stopAgentSpriteLoop(agentId) {
  if (agentId === state.agent.id) {
    window.clearInterval(state.agentSpriteTimer);
    state.agentSpriteTimer = null;
    return;
  }

  window.clearInterval(state.supportSpriteTimers.get(agentId));
  state.supportSpriteTimers.delete(agentId);
}

function ensureAgentSprite(agent) {
  if (agent.id === state.agent.id) return state.agent.sprite;
  if (!agent.sprite) agent.sprite = createAgentSpriteState();
  if (!agent.sprite.animationMap) agent.sprite.animationMap = state.agent.sprite.animationMap;
  return agent.sprite;
}

function getStatusKeyForAgent(agent) {
  const stateName = String(agent?.visualState || "").toLowerCase();
  if (stateName.includes("meeting")) return "meeting";
  if (stateName.includes("working")) return "working";
  if (stateName.includes("reporting")) return "reporting";
  if (stateName.includes("blocked")) return "blocked";
  return "idle";
}

function getAgentFrames(mode, direction = "down") {
  return getAgentFramesFor(state.agent, mode, direction);
}

function getAgentFramesFor(agent, mode, direction = "down", statusKey = "idle") {
  const sprite = ensureAgentSprite(agent);
  const fallback = agent.id === state.agent.id
    ? state.agent.frameImage
    : (agent.image || state.agent.frameImage || MANAGER_STATIC_FRAME);
  const frames = getAnimationFrames(sprite.animationMap, mode, direction, statusKey);
  if (frames.length) {
    return frames.map(resolveAgentPackagePath);
  }
  return [fallback || MANAGER_STATIC_FRAME];
}

function getAnimationFrames(map, mode, direction = "down", statusKey = "idle") {
  if (!map) return [];

  if (mode === "walk") {
    return compactFrameList(
      map.walk?.[direction],
      map.paths?.walk?.[direction],
      map.animations?.walk?.[direction]?.frames,
      map.walk?.down,
      map.paths?.walk?.down,
      map.animations?.walk?.down?.frames,
    );
  }

  return compactFrameList(
    map.status?.[statusKey],
    map.paths?.status?.[statusKey],
    map.animations?.status?.[statusKey]?.frames,
    map.status?.idle,
    map.paths?.status?.idle,
    map.animations?.status?.idle?.frames,
  );
}

function compactFrameList(...candidates) {
  for (const candidate of candidates) {
    if (Array.isArray(candidate) && candidate.length) return candidate;
    if (typeof candidate === "string" && candidate) return [candidate];
  }
  return [];
}

function getResolvedAnimationFrame(map, mode, direction = "down", statusKey = "idle") {
  const [first] = getAnimationFrames(map, mode, direction, statusKey);
  return first ? resolveAgentPackagePath(first) : null;
}

function getAgentAnimationFps(map, mode, direction = "down", statusKey = "idle") {
  if (mode === "walk") {
    return map?.animations?.walk?.[direction]?.fps
      || map?.animations?.walk?.down?.fps
      || 8;
  }
  return map?.animations?.status?.[statusKey]?.fps
    || map?.animations?.status?.idle?.fps
    || 3;
}

function updateAgentFrameImage(path) {
  return updateAgentFrameImageForAgent(state.agent, path);
}

function updateAgentFrameImageForAgent(agent, path) {
  if (!path) return;
  if (agent.id === state.agent.id) {
    state.agent.frameImage = path;
  }
  agent.image = path;
  const image = document.getElementById(agent.id === state.agent.id ? "agentFrameImage" : `agentFrameImage-${agent.id}`);
  const displayPath = withAgentAssetVersion(path);
  if (image && image.getAttribute("src") !== displayPath) {
    image.src = displayPath;
  }
}

function showWalkTarget(x, y, blocked = false) {
  const target = document.getElementById("walkTarget");
  if (!target) return;
  target.style.setProperty("--target-x", x.toFixed(3));
  target.style.setProperty("--target-y", y.toFixed(3));
  target.classList.toggle("blocked", blocked);
  target.classList.remove("visible");
  target.offsetHeight;
  target.classList.add("visible");
}

function moveAgentToPoint(point, status = "กำลังเคลื่อนที่") {
  const target = {
    x: clamp(point.x, 3, 97),
    y: clamp(point.y, 24, 90),
    label: point.label || "จุดที่เลือก",
  };
  const start = { x: state.agent.x, y: state.agent.y, label: state.agent.name };
  const navigation = validateNavigationPoint(target);
  if (!navigation.ok) {
    showWalkTarget(target.x, target.y, true);
    drawPathPreview([start, target], true);
    const obstacleId = String(navigation.id || "").replace(/_collision$/, "");
    updateDecisionLog(`เดินไม่ได้: ${target.label} อยู่นอกพื้นที่เดินหรือชนกับ ${displayPropName(obstacleId, navigation.label || "สิ่งกีดขวาง")}`);
    return null;
  }

  const path = planAgentPath(start, target);
  if (!path || path.length === 0) {
    showWalkTarget(target.x, target.y, true);
    drawPathPreview([start, target], true);
    updateDecisionLog(`เดินไม่ได้: ไม่พบเส้นทางไปยัง ${target.label}`);
    return null;
  }

  drawPathPreview([start, ...path], false);
  return moveAgentAlongPath(path, status);
}

function moveAgentAlongPath(path, status = "Moving") {
  const steps = path.filter((point) => getVisualDistance({ x: state.agent.x, y: state.agent.y }, point) > 0.18);
  if (!steps.length) return null;

  const finalPoint = steps[steps.length - 1];
  showWalkTarget(finalPoint.x, finalPoint.y, false);
  showAgentPanel(state.agent.id, false);

  cancelAgentMotion();
  const points = [
    { x: state.agent.x, y: state.agent.y, label: state.agent.name },
    ...steps.map((point) => ({
      x: clamp(point.x, 7, 93),
      y: clamp(point.y, 30, 88),
      label: finalPoint.label,
    })),
  ];
  const timeline = buildAgentMoveTimeline(points);
  if (!timeline.length) return null;

  const blockedStep = timeline.find((segment) => !hasNavigationLine(segment.start, segment.end));
  if (blockedStep) {
    showWalkTarget(blockedStep.end.x, blockedStep.end.y, true);
      updateDecisionLog("เดินไม่ได้: เส้นทางช่วงถัดไปตัดผ่านอุปกรณ์");
    clearPathPreview();
    finishAgentWalk(state.agent.direction, status, blockedStep.end.label, false);
    return null;
  }

  animateAgentTimeline(timeline, finalPoint, status);
  return {
    agentId: state.agent.id,
    target: finalPoint.label || "จุดหมายที่กำหนด",
    pathLength: steps.length,
    durationMs: Math.round(timeline[timeline.length - 1].endMs),
  };
}

function cancelAgentMotion() {
  window.clearTimeout(state.agentMoveTimer);
  if (state.agentMoveFrame) {
    window.cancelAnimationFrame(state.agentMoveFrame);
    state.agentMoveFrame = null;
  }
}

function buildAgentMoveTimeline(points) {
  const walkSpeed = state.navigation.walkSpeed || DEFAULT_WALK_SPEED;
  const timeline = [];
  let elapsedMs = 0;

  for (let index = 1; index < points.length; index += 1) {
    const start = points[index - 1];
    const end = points[index];
    const distance = getVisualDistance(start, end);
    if (distance <= 0.01) continue;

    const durationMs = Math.round(clamp(
      distance * walkSpeed.msPerDistanceUnit,
      walkSpeed.minSegmentMs,
      walkSpeed.maxSegmentMs,
    ));
    timeline.push({
      start,
      end,
      distance,
      startMs: elapsedMs,
      endMs: elapsedMs + durationMs,
      durationMs,
    });
    elapsedMs += durationMs;
  }

  return timeline;
}

function animateAgentTimeline(timeline, finalPoint, status) {
  const node = document.getElementById("hqManagerAgent");
  if (!node) return;

  let activeSegmentIndex = 0;
  let activeDirection = state.agent.direction;
  const totalMs = timeline[timeline.length - 1].endMs;
  const startedAt = performance.now();

  node.classList.remove("idle");
  node.classList.add("walking", "active");
  state.agent.status = `${status}: ${finalPoint.label || "จุดหมายที่กำหนด"}`;

  const tick = (now) => {
    const elapsedMs = Math.min(now - startedAt, totalMs);
    while (
      activeSegmentIndex < timeline.length - 1
      && elapsedMs > timeline[activeSegmentIndex].endMs
    ) {
      activeSegmentIndex += 1;
    }

    const segment = timeline[activeSegmentIndex];
    const ratio = segment.durationMs > 0
      ? clamp((elapsedMs - segment.startMs) / segment.durationMs, 0, 1)
      : 1;
    const x = segment.start.x + (segment.end.x - segment.start.x) * ratio;
    const y = segment.start.y + (segment.end.y - segment.start.y) * ratio;
    const direction = getDirection(segment.end.x - segment.start.x, segment.end.y - segment.start.y);

    if (direction !== activeDirection) {
      activeDirection = direction;
      state.agent.direction = direction;
      startSpriteLoop("walk", direction);
    } else if (!node.classList.contains("walking")) {
      startSpriteLoop("walk", direction);
    }

    state.agent.x = x;
    state.agent.y = y;
    state.agent.speedMs = 1;
    state.agent.status = `${status}: ${finalPoint.label || "จุดที่เลือก"}`;
    applyAgentPosition(false);

    if (elapsedMs >= totalMs) {
      finishAgentWalk(direction, status, finalPoint.label, true);
      return;
    }

    state.agentMoveFrame = window.requestAnimationFrame(tick);
  };

  startSpriteLoop("walk", activeDirection);
  state.agentMoveFrame = window.requestAnimationFrame(tick);
}

function finishAgentWalk(direction, status, label, arrived) {
  const node = document.getElementById("hqManagerAgent");
  state.agentMoveFrame = null;
  if (node) {
    node.classList.remove("walking");
    node.classList.add("idle");
  }
  state.agent.status = arrived
    ? `ถึง ${label || "จุดที่เลือก"} แล้ว`
    : `${status}: ${label || "จุดที่เลือก"}`;
  state.agent.speedMs = 1;
  applyAgentPosition(false);
  startSpriteLoop("idle", direction);
  showAgentPanel(state.agent.id, false);
  window.clearTimeout(state.pathClearTimer);
  if (arrived) state.pathClearTimer = window.setTimeout(clearPathPreview, 900);
}

function moveAgentSegment(point, status = "กำลังเคลื่อนที่", onArrive = null) {
  const node = document.getElementById("hqManagerAgent");
  if (!node) return null;
  if (!onArrive) cancelAgentMotion();

  const nextX = clamp(point.x, 7, 93);
  const nextY = clamp(point.y, 30, 88);
  const dx = nextX - state.agent.x;
  const dy = nextY - state.agent.y;
  const direction = getDirection(dx, dy);
  const distance = getVisualDistance({ x: state.agent.x, y: state.agent.y }, { x: nextX, y: nextY });
  const walkSpeed = state.navigation.walkSpeed || DEFAULT_WALK_SPEED;
  const speedMs = Math.round(clamp(
    distance * walkSpeed.msPerDistanceUnit,
    walkSpeed.minSegmentMs,
    walkSpeed.maxSegmentMs,
  ));
  const wasWalking = node.classList.contains("walking");
  const directionChanged = state.agent.direction !== direction;

  state.agent.direction = direction;
  state.agent.speedMs = speedMs;
  state.agent.x = nextX;
  state.agent.y = nextY;
  state.agent.status = `${status}: ${point.label || "จุดที่เลือก"}`;

  node.classList.remove("idle");
  node.classList.add("walking", "active");
  if (!wasWalking || directionChanged) startSpriteLoop("walk", direction);
  applyAgentPosition(true);

  window.clearTimeout(state.agentMoveTimer);
  state.agentMoveTimer = window.setTimeout(() => {
    if (onArrive) {
      onArrive();
      return;
    }

    node.classList.remove("walking");
    node.classList.add("idle");
    state.agent.status = `ถึง ${point.label || "จุดที่เลือก"} แล้ว`;
    applyAgentPosition(false);
    startSpriteLoop("idle", direction);
    showAgentPanel(state.agent.id, false);
    window.clearTimeout(state.pathClearTimer);
    state.pathClearTimer = window.setTimeout(clearPathPreview, 900);
  }, speedMs + AGENT_WALK_SETTLE_MS);

  return {
    agentId: state.agent.id,
    target: point.label || "จุดที่เลือก",
    direction,
    speedMs,
  };
}

function getVisualDistance(start, target) {
  return Math.hypot((target.x - start.x) * 1.777, target.y - start.y);
}

function drawPathPreview(points, blocked = false) {
  clearPathPreview();
}

function clearPathPreview() {
  if (!els.pathLayer) return;
  els.pathLayer.classList.remove("visible", "blocked");
  window.clearTimeout(state.pathClearTimer);
}

function createSvgElement(tagName, attributes = {}) {
  const node = document.createElementNS("http://www.w3.org/2000/svg", tagName);
  Object.entries(attributes).forEach(([name, value]) => node.setAttribute(name, value));
  return node;
}

function getDirection(dx, dy) {
  if (Math.abs(dx) > Math.abs(dy) * 1.15) return dx >= 0 ? "right" : "left";
  return dy >= 0 ? "down" : "up";
}

function getNearestWalkablePoint(point) {
  if (validateNavigationPoint(point).ok) return point;
  const grid = state.navigation.grid || { columns: 72, rows: 40 };
  const columns = grid.columns || 72;
  const rows = grid.rows || 40;
  const cell = findNearestWalkableCell(pointToCell(point, columns, rows), columns, rows);
  if (!cell) return null;
  return {
    ...cellToPoint(cell, columns, rows),
    label: point.label,
  };
}

function moveSupportAgentToPoint(agent, point, status = "Moving", options = {}) {
  agent.persistMotion = options.persist !== false;
  const safePoint = getNearestWalkablePoint({
    x: clamp(point.x, 7, 93),
    y: clamp(point.y, 30, 88),
    label: point.label || "จุดหมายที่กำหนด",
  });

  if (!safePoint) {
    updateDecisionLog(`เดินไม่ได้: ${agent.name} ไม่พบเส้นทางไปยัง ${point.label || "จุดหมาย"}`, { persist: agent.persistMotion });
    recordOfficeEvent("เส้นทางถูกกีดขวาง", `${agent.name} ไปไม่ถึง ${point.label || "จุดหมาย"}`, {
      agentId: agent.id,
      kind: "route_blocked",
      persist: agent.persistMotion,
      bridgeEvent: agent.persistMotion,
    });
    return null;
  }

  const start = { x: agent.x, y: agent.y, label: agent.name };
  const path = planAgentPath(start, safePoint);
  if (!path || path.length === 0) {
    updateDecisionLog(`เดินไม่ได้: ${agent.name} ไม่พบเส้นทางไปยัง ${safePoint.label || "จุดหมาย"}`, { persist: agent.persistMotion });
    recordOfficeEvent("เส้นทางถูกกีดขวาง", `${agent.name} ไปไม่ถึง ${safePoint.label || "จุดหมาย"}`, {
      agentId: agent.id,
      kind: "route_blocked",
      persist: agent.persistMotion,
      bridgeEvent: agent.persistMotion,
    });
    return null;
  }

  const steps = path.filter((step) => getVisualDistance({ x: agent.x, y: agent.y }, step) > 0.18);
  if (!steps.length) return null;
  const finalPoint = steps[steps.length - 1];
  finalPoint.label = safePoint.label || point.label || "target";
  const timeline = buildAgentMoveTimeline([
    start,
    ...steps.map((step) => ({
      x: clamp(step.x, 7, 93),
      y: clamp(step.y, 30, 88),
      label: finalPoint.label,
    })),
  ]);
  if (!timeline.length) return null;

  const blockedStep = timeline.find((segment) => !hasNavigationLine(segment.start, segment.end));
  if (blockedStep) {
      updateDecisionLog(`เดินไม่ได้: เส้นทางของ ${agent.name} ตัดผ่านอุปกรณ์`, { persist: agent.persistMotion });
    finishSupportAgentWalk(agent, agent.direction, status, blockedStep.end.label, false);
    return null;
  }

  showWalkTarget(finalPoint.x, finalPoint.y, false);
  animateSupportAgentTimeline(agent, timeline, finalPoint, status);
  const durationMs = Math.round(timeline[timeline.length - 1].endMs);
  if (agent.persistMotion) saveSessionSnapshot();

  return {
    agentId: agent.id,
    target: finalPoint.label || "target",
    direction: getDirection(
      timeline[0].end.x - timeline[0].start.x,
      timeline[0].end.y - timeline[0].start.y,
    ),
    speedMs: durationMs,
  };
}

function cancelSupportAgentMotion(agentId) {
  window.clearTimeout(state.supportMoveTimers.get(agentId));
  state.supportMoveTimers.delete(agentId);
  const frameId = state.supportMoveFrames.get(agentId);
  if (frameId) window.cancelAnimationFrame(frameId);
  state.supportMoveFrames.delete(agentId);
}

function animateSupportAgentTimeline(agent, timeline, finalPoint, status) {
  const node = document.getElementById(getAgentNodeId(agent.id));
  if (!node) return;

  cancelSupportAgentMotion(agent.id);
  let activeSegmentIndex = 0;
  let activeDirection = agent.direction || "down";
  const totalMs = timeline[timeline.length - 1].endMs;
  const startedAt = performance.now();

  agent.visualState = "walking";
  agent.status = `${status}: ${finalPoint.label || "target"}`;
  agent.speedMs = 1;
  node.classList.remove("idle", "talking", "meeting", "working", "reporting");
  node.classList.add("walking", "active");
  updateAgentNodeState(agent);
  startAgentSpriteLoop(agent, "walk", activeDirection);

  const tick = (now) => {
    const elapsedMs = Math.min(now - startedAt, totalMs);
    while (
      activeSegmentIndex < timeline.length - 1
      && elapsedMs > timeline[activeSegmentIndex].endMs
    ) {
      activeSegmentIndex += 1;
    }

    const segment = timeline[activeSegmentIndex];
    const ratio = segment.durationMs > 0
      ? clamp((elapsedMs - segment.startMs) / segment.durationMs, 0, 1)
      : 1;
    const x = segment.start.x + (segment.end.x - segment.start.x) * ratio;
    const y = segment.start.y + (segment.end.y - segment.start.y) * ratio;
    const direction = getDirection(segment.end.x - segment.start.x, segment.end.y - segment.start.y);

    if (direction !== activeDirection) {
      activeDirection = direction;
      agent.direction = direction;
      startAgentSpriteLoop(agent, "walk", direction);
    }

    agent.x = x;
    agent.y = y;
    agent.speedMs = 1;
    agent.status = `${status}: ${finalPoint.label || "target"}`;
    updateAgentNodeState(agent);

    if (elapsedMs >= totalMs) {
      finishSupportAgentWalk(agent, direction, status, finalPoint.label, true);
      return;
    }

    state.supportMoveFrames.set(agent.id, window.requestAnimationFrame(tick));
  };

  state.supportMoveFrames.set(agent.id, window.requestAnimationFrame(tick));
  const timer = window.setTimeout(() => {
    finishSupportAgentWalk(agent, activeDirection, status, finalPoint.label, true);
  }, totalMs + AGENT_WALK_SETTLE_MS + 120);
  state.supportMoveTimers.set(agent.id, timer);
}

function finishSupportAgentWalk(agent, direction, status, label, arrived) {
  const node = document.getElementById(getAgentNodeId(agent.id));
  const frameId = state.supportMoveFrames.get(agent.id);
  if (frameId) window.cancelAnimationFrame(frameId);
  state.supportMoveFrames.delete(agent.id);
  window.clearTimeout(state.supportMoveTimers.get(agent.id));
  state.supportMoveTimers.delete(agent.id);

  agent.direction = direction || agent.direction || "down";
  agent.status = arrived ? `ถึง ${label || "จุดหมาย"} แล้ว` : `${status}: ${label || "จุดหมาย"}`;
  agent.speedMs = 1;
  const isMeetingRoute = /meeting|ประชุม/i.test(status);
  agent.visualState = isMeetingRoute && arrived ? "meeting" : "idle";

  if (node) {
    node.classList.remove("walking");
    node.classList.add(agent.visualState === "meeting" ? "meeting" : "idle");
  }
  updateAgentNodeState(agent);
  startAgentSpriteLoop(agent, "idle", agent.direction, { statusKey: getStatusKeyForAgent(agent) });
  if (state.panelObject === agent.id) showAgentPanel(agent.id, false);
  if (agent.persistMotion !== false) saveSessionSnapshot();
  delete agent.persistMotion;
}

function moveSelectedAgentToPoint(point, status = "กำลังเดิน") {
  const agent = getSelectedAgent();
  if (!agent || agent.id === state.agent.id) return moveAgentToPoint(point, status);
  return moveSupportAgentToPoint(agent, point, status);
}

function routeAgentToTargetId(agentId, targetId, status = "กำลังเดินตามเส้นทาง", options = {}) {
  const officeAgent = getOfficeAgent(agentId);
  if (!officeAgent) {
    updateDecisionLog(`กำหนดเส้นทางไม่ได้: ไม่พบ Agent ${agentId}`);
    return null;
  }

  const point = getAgentTargetPoint(targetId, agentId);
  if (!point) {
    updateDecisionLog(`กำหนดเส้นทางไม่ได้: ไม่พบจุดหมาย ${targetId}`);
    return null;
  }

  if (options.select !== false && options.persist !== false) setSelectedAgent(agentId);
  const routeLine = `${officeAgent.name} กำลังเดินไปที่ ${point.label}`;
  updateDecisionLog(routeLine, { persist: options.persist !== false });
  setAgentSpeech(agentId, routeLine, /meeting|ประชุม/i.test(status) ? "meeting" : "walking");
  recordOfficeEvent("เส้นทางของ Agent", `${officeAgent.name} → ${point.label}`, {
    agentId,
    kind: "route",
    persist: options.persist !== false,
    bridgeEvent: options.persist !== false,
  });

  if (agentId === state.agent.id) {
    officeAgent.currentTarget = targetId;
    return moveAgentToPoint(point, status);
  }
  const result = moveSupportAgentToPoint(officeAgent, point, status, options);
  if (result) officeAgent.currentTarget = targetId;
  return result;
}

function getAgentMeetingSeatTargetId(agentId) {
  return meetingSeats[agentId] ? agentId : "mission_strategy_table";
}

function getAgentTargetPoint(targetId, agentId) {
  if (targetId === "mission_strategy_table" && meetingSeats[agentId]) {
    return meetingSeats[agentId];
  }
  return sharedWorkstationSeats[targetId]?.[agentId] || getTargetPoint(targetId);
}

function getTargetPoint(targetId) {
  if (agentWaypoints[targetId]) return agentWaypoints[targetId];

  if (targetId?.endsWith("_agent_position")) {
    const agentId = targetId.replace(/_agent_position$/, "");
    const targetAgent = getOfficeAgent(agentId);
    if (targetAgent) {
      return {
        x: clamp(targetAgent.x + 2.4, 7, 93),
        y: clamp(targetAgent.y + 0.8, 30, 88),
        label: `ตำแหน่งของ ${targetAgent.name}`,
      };
    }
  }

  if (meetingSeats[targetId]) return meetingSeats[targetId];

  const targetAgent = getOfficeAgent(targetId);
  if (targetAgent) {
    return {
      x: clamp(targetAgent.x + 2.4, 7, 93),
      y: clamp(targetAgent.y + 0.8, 30, 88),
      label: `ตำแหน่งของ ${targetAgent.name}`,
    };
  }

  const spot = getInteractiveObjects().find((item) => item.id === targetId);
  if (!spot) return null;

  const placement = spot.position || spot.rect;
  if (!placement) return null;
  const visualHeight = getPropVisualHeight(spot, placement);

  return {
    x: clamp(placement.x + placement.w / 2, 7, 93),
    y: clamp(placement.y + visualHeight + 2, 30, 88),
    label: spot.label,
  };
}

function validateNavigationPoint(point) {
  if (state.navigation.maskMode === "strict" && !isPointInsideWalkableMask(point)) {
    return { ok: false, reason: "mask", label: "พื้นที่ที่ Agent เดินไม่ได้" };
  }

  const blocker = findNavigationBlocker(point);
  if (blocker) {
    return { ok: false, reason: "blocker", label: blocker.label || blocker.id };
  }

  return { ok: true };
}

function isPointInsideWalkableMask(point) {
  return !findWalkableMaskFailure(point);
}

function findWalkableMaskFailure(point) {
  const mask = state.navigation.mask;
  if (!mask) return null;

  for (const sample of getAgentFootprintSamples()) {
    const samplePoint = {
      x: point.x + sample.x,
      y: point.y + sample.y,
    };
    const alpha = getWalkableMaskAlpha(samplePoint);
    if (alpha < state.navigation.alphaThreshold) {
      return {
        ok: false,
        label: "พื้นที่ที่ Agent เดินไม่ได้",
        alpha,
        sample: samplePoint,
      };
    }
  }

  return null;
}

function getAgentFootprintSamples() {
  const footprint = state.navigation.agentFootprint || {};
  const x = footprint.xRadius || 0;
  const y = footprint.yRadius || 0;

  return [
    { x: 0, y: 0 },
    { x: -x, y: 0 },
    { x, y: 0 },
    { x: 0, y: -y },
    { x: 0, y },
    { x: -x * 0.72, y: -y * 0.72 },
    { x: x * 0.72, y: -y * 0.72 },
    { x: -x * 0.72, y: y * 0.72 },
    { x: x * 0.72, y: y * 0.72 },
  ];
}

function getWalkableMaskAlpha(point) {
  const mask = state.navigation.mask;
  if (!mask) return 255;

  const x = Math.round(clamp(point.x, 0, 100) / 100 * (mask.width - 1));
  const y = Math.round(clamp(point.y, 0, 100) / 100 * (mask.height - 1));
  return mask.context.getImageData(x, y, 1, 1).data[3];
}

function findNavigationBlocker(point, options = {}) {
  const samples = options.useAgentClearance === false ? [{ x: 0, y: 0 }] : getAgentBlockerSamples();

  for (const sample of samples) {
    const samplePoint = {
      x: point.x + sample.x,
      y: point.y + sample.y,
    };
    const blocker = state.navigation.blockers.find((item) => isPointInsideBlocker(samplePoint, item));
    if (blocker) return blocker;
  }

  return null;
}

function getAgentBlockerSamples() {
  const footprint = state.navigation.agentBlockerFootprint || {};
  const x = footprint.xRadius || 0;
  const backY = footprint.yBackRadius || 0;
  const frontY = footprint.yFrontRadius || 0;

  return [
    { x: 0, y: 0 },
    { x: -x * 0.68, y: 0 },
    { x: x * 0.68, y: 0 },
    { x: 0, y: frontY },
    { x: -x * 0.55, y: frontY },
    { x: x * 0.55, y: frontY },
    { x: 0, y: -backY * 0.35 },
    { x: -x, y: -backY * 0.35 },
    { x, y: -backY * 0.35 },
    { x: 0, y: -backY * 0.7 },
    { x: -x * 0.82, y: -backY * 0.7 },
    { x: x * 0.82, y: -backY * 0.7 },
    { x: 0, y: -backY },
    { x: -x * 0.48, y: -backY },
    { x: x * 0.48, y: -backY },
  ];
}

function isPointInsideBlocker(point, blocker) {
  if (!blocker) return false;
  const padding = blocker.padding || 0;

  if (blocker.type === "rect") {
    return (
      point.x >= blocker.x - padding &&
      point.x <= blocker.x + blocker.w + padding &&
      point.y >= blocker.y - padding &&
      point.y <= blocker.y + blocker.h + padding
    );
  }

  if (blocker.type === "ellipse") {
    const rx = blocker.w / 2 + padding;
    const ry = blocker.h / 2 + padding;
    const cx = blocker.x + blocker.w / 2;
    const cy = blocker.y + blocker.h / 2;
    return ((point.x - cx) ** 2) / (rx ** 2) + ((point.y - cy) ** 2) / (ry ** 2) <= 1;
  }

  if (blocker.type === "polygon" && Array.isArray(blocker.points)) {
    return pointInPolygon(point, blocker.points) || isPointNearPolygon(point, blocker.points, padding);
  }

  return false;
}

function pointInPolygon(point, polygon) {
  let inside = false;
  for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
    const xi = polygon[i].x;
    const yi = polygon[i].y;
    const xj = polygon[j].x;
    const yj = polygon[j].y;
    const intersects =
      yi > point.y !== yj > point.y &&
      point.x < ((xj - xi) * (point.y - yi)) / (yj - yi || 0.00001) + xi;
    if (intersects) inside = !inside;
  }
  return inside;
}

function isPointNearPolygon(point, polygon, padding) {
  if (!padding) return false;
  for (let index = 0; index < polygon.length; index += 1) {
    const start = polygon[index];
    const end = polygon[(index + 1) % polygon.length];
    if (distanceToSegment(point, start, end) <= padding) return true;
  }
  return false;
}

function distanceToSegment(point, start, end) {
  const dx = end.x - start.x;
  const dy = end.y - start.y;
  if (dx === 0 && dy === 0) return Math.hypot(point.x - start.x, point.y - start.y);

  const t = clamp(((point.x - start.x) * dx + (point.y - start.y) * dy) / (dx * dx + dy * dy), 0, 1);
  const projected = {
    x: start.x + t * dx,
    y: start.y + t * dy,
  };
  return Math.hypot(point.x - projected.x, point.y - projected.y);
}

function planAgentPath(start, target) {
  if (!state.navigation.mask && !state.navigation.blockers.length) {
    const directPath = densifyNavigationPath([start, target], target.label);
    return directPath.length ? directPath : null;
  }
  if (hasNavigationLine(start, target)) {
    const directPath = densifyNavigationPath([start, target], target.label);
    return directPath.length ? directPath : null;
  }

  const gridPath = findGridPath(start, target);
  if (!gridPath) return null;

  const stepped = densifyNavigationPath(gridPath, target.label);
  if (!stepped.length) return null;
  const final = stepped[stepped.length - 1];
  final.label = target.label;
  return stepped;
}

function hasNavigationLine(start, target) {
  const dx = target.x - start.x;
  const dy = target.y - start.y;
  const steps = Math.max(2, Math.ceil(getVisualDistance(start, target) / NAVIGATION_LINE_SAMPLE_STEP));

  for (let index = 1; index <= steps; index += 1) {
    const point = {
      x: start.x + (dx * index) / steps,
      y: start.y + (dy * index) / steps,
    };
    if (!validateNavigationPoint(point).ok) return false;
  }

  return true;
}

function densifyNavigationPath(points, finalLabel = "จุดที่เลือก") {
  const densified = [];

  for (let index = 1; index < points.length; index += 1) {
    const start = points[index - 1];
    const end = points[index];
    const distance = getVisualDistance(start, end);
    const steps = Math.max(1, Math.ceil(distance / NAVIGATION_MAX_STEP_DISTANCE));

    for (let step = 1; step <= steps; step += 1) {
      const ratio = step / steps;
      const point = {
        x: start.x + (end.x - start.x) * ratio,
        y: start.y + (end.y - start.y) * ratio,
        label: finalLabel,
      };
      if (!validateNavigationPoint(point).ok) return [];
      densified.push(point);
    }
  }

  return densified;
}

function findGridPath(start, target) {
  const grid = state.navigation.grid || { columns: 72, rows: 40 };
  const columns = grid.columns || 72;
  const rows = grid.rows || 40;
  const startCell = findNearestWalkableCell(pointToCell(start, columns, rows), columns, rows);
  const targetCell = findNearestWalkableCell(pointToCell(target, columns, rows), columns, rows);

  if (!startCell || !targetCell) return null;

  const startKey = cellKey(startCell);
  const targetKey = cellKey(targetCell);
  const open = new Map([[startKey, { ...startCell, g: 0, f: cellDistance(startCell, targetCell), parent: null }]]);
  const closed = new Set();
  const best = new Map([[startKey, 0]]);

  while (open.size) {
    let currentKey = null;
    let current = null;
    for (const [key, node] of open) {
      if (!current || node.f < current.f) {
        current = node;
        currentKey = key;
      }
    }

    if (currentKey === targetKey) return reconstructCellPath(current, columns, rows);

    open.delete(currentKey);
    closed.add(currentKey);

    for (const neighbor of getNeighborCells(current, columns, rows)) {
      const key = cellKey(neighbor);
      if (closed.has(key) || !isCellWalkable(neighbor, columns, rows)) continue;

      if (neighbor.c !== current.c && neighbor.r !== current.r) {
        const sideA = { c: neighbor.c, r: current.r };
        const sideB = { c: current.c, r: neighbor.r };
        if (!isCellWalkable(sideA, columns, rows) || !isCellWalkable(sideB, columns, rows)) continue;
      }

      const tentativeG = current.g + cellDistance(current, neighbor);
      if (tentativeG >= (best.get(key) ?? Infinity)) continue;

      best.set(key, tentativeG);
      open.set(key, {
        ...neighbor,
        g: tentativeG,
        f: tentativeG + cellDistance(neighbor, targetCell),
        parent: current,
      });
    }
  }

  return null;
}

function pointToCell(point, columns, rows) {
  return {
    c: Math.round(clamp(point.x, 0, 100) / 100 * (columns - 1)),
    r: Math.round(clamp(point.y, 0, 100) / 100 * (rows - 1)),
  };
}

function cellToPoint(cell, columns, rows) {
  return {
    x: (cell.c / (columns - 1)) * 100,
    y: (cell.r / (rows - 1)) * 100,
  };
}

function cellKey(cell) {
  return `${cell.c},${cell.r}`;
}

function cellDistance(a, b) {
  const dx = (a.c - b.c) * 1.78;
  const dy = a.r - b.r;
  return Math.hypot(dx, dy);
}

function isCellWalkable(cell, columns, rows) {
  if (cell.c < 0 || cell.r < 0 || cell.c >= columns || cell.r >= rows) return false;
  return validateNavigationPoint(cellToPoint(cell, columns, rows)).ok;
}

function findNearestWalkableCell(cell, columns, rows) {
  if (isCellWalkable(cell, columns, rows)) return cell;

  for (let radius = 1; radius <= 8; radius += 1) {
    for (let dc = -radius; dc <= radius; dc += 1) {
      for (let dr = -radius; dr <= radius; dr += 1) {
        if (Math.abs(dc) !== radius && Math.abs(dr) !== radius) continue;
        const candidate = { c: cell.c + dc, r: cell.r + dr };
        if (isCellWalkable(candidate, columns, rows)) return candidate;
      }
    }
  }

  return null;
}

function getNeighborCells(cell, columns, rows) {
  const neighbors = [];
  for (let dc = -1; dc <= 1; dc += 1) {
    for (let dr = -1; dr <= 1; dr += 1) {
      if (dc === 0 && dr === 0) continue;
      const next = { c: cell.c + dc, r: cell.r + dr };
      if (next.c >= 0 && next.r >= 0 && next.c < columns && next.r < rows) neighbors.push(next);
    }
  }
  return neighbors;
}

function reconstructCellPath(node, columns, rows) {
  const cells = [];
  let current = node;
  while (current) {
    cells.push(cellToPoint(current, columns, rows));
    current = current.parent;
  }
  return cells.reverse();
}

function smoothNavigationPath(points) {
  if (points.length <= 2) return points.slice(1);

  const smoothed = [];
  let anchorIndex = 0;
  while (anchorIndex < points.length - 1) {
    let nextIndex = points.length - 1;
    while (nextIndex > anchorIndex + 1 && !hasNavigationLine(points[anchorIndex], points[nextIndex])) {
      nextIndex -= 1;
    }
    smoothed.push(points[nextIndex]);
    anchorIndex = nextIndex;
  }
  return smoothed;
}

function getRelevantMemoryCards(text = "", limit = 4) {
  const query = String(text || "").toLowerCase();
  const tokens = query.replace(/[_/-]/g, " ").split(/\s+/).filter(Boolean);
  const scored = state.memoryCards
    .map((card) => {
      const haystack = [
        card.id,
        card.kind,
        card.title,
        card.summary,
        card.sourcePath,
        ...(card.agents || []),
        ...(card.tags || []),
      ].join(" ").toLowerCase();
      const score = tokens.reduce((sum, token) => sum + (haystack.includes(token) ? 1 : 0), 0);
      return { card, score };
    })
    .filter((row) => row.score > 0);
  const matched = scored.sort((a, b) => b.score - a.score).map((row) => row.card);
  return (matched.length ? matched : state.memoryCards).slice(0, limit);
}

function memoryCardsToMissionItems(cards = [], owner = "mission_archivist") {
  return cards.map((card) => ({
    title: `Memory: ${card.title || card.id}`,
    detail: card.summary || "จัดทำดัชนี Memory ไว้สำหรับค้นกลับมาใช้งานแล้ว",
    owner: (card.agents || []).join(", ") || owner,
    status: card.kind || "memory",
  }));
}

function showAgentPanel(agentId = state.selectedAgentId, setActiveObject = true) {
  const agent = getOfficeAgent(agentId) || getOfficeAgent(state.agent.id);
  if (!agent) return;
  setSelectedAgent(agent.id);

  [...els.agentLayer.querySelectorAll(".agent-unit")].forEach((node) => {
    node.classList.toggle("active", node.dataset.agentId === agent.id);
  });
  [...els.propLayer.children].forEach((propNode) => propNode.classList.remove("active"));

  state.panelObject = agent.id;
  if (setActiveObject) state.activeObject = agent.id;

  els.selectedLayer.textContent = "Agent ที่เลือก";
  els.reportTitle.textContent = `${agent.name} - ${agent.role}`;
  els.reportSummary.textContent = isManagerWorkspace(agent)
    ? "พื้นที่สำหรับคุย สร้าง Task เรียกประชุม และให้ Manager/CEO แจกงาน"
    : "พื้นที่สำหรับคุยและมอบหมาย Task ให้ Agent คนนี้โดยตรง";

  const metrics = {
    สถานะ: agent.status,
    หน้าที่: agent.role,
    จุดทำงาน: displayPropName(agent.currentTarget || agent.defaultTarget),
    Bridge: `${displayBridgeValue(state.bridge.mode)} - ${displayBridgeValue(state.bridge.status)}`,
    Memory: state.memoryStatus,
  };

  const agentMissions = state.missions
    .filter((mission) => mission.owner === agent.id || mission.owner === agent.role || mission.owner === agent.name)
    .slice(0, 4);
  const transcriptItems = state.meetingTranscript
    .filter((line) => (
      line.simulation !== true
      && (line.from === agent.id || line.to === agent.id || line.participants?.includes(agent.id))
    ))
    .slice(0, 3)
    .map((line) => ({
      title: "บทสนทนาของ Agent",
      detail: `${line.label || line.from || "การประชุม"}: ${line.message || line.summary || ""}`,
      owner: agent.name,
      status: "transcript",
    }));
  const memoryCards = agent.id === "mission_archivist"
    ? state.memoryCards.slice(0, 5)
    : getRelevantMemoryCards(`${agent.id} ${agent.name} ${agent.role} ${(agent.tools || []).join(" ")}`, 3);
  const memoryItems = memoryCardsToMissionItems(memoryCards, agent.name);

  renderMetrics(metrics);
  renderMissionItems([
    ...agentMissions,
    ...transcriptItems,
    ...memoryItems,
    {
      title: "เดินไป Workstation",
      detail: `${agent.name} เดินไปที่ ${getTargetPoint(agent.defaultTarget)?.label || agent.defaultTarget} ได้`,
      owner: agent.role,
      status: "available",
    },
    {
      title: isManagerWorkspace(agent) ? "คุย / มอบหมาย Task / ประชุม" : "คุย / Task ของฉัน",
      detail: isManagerWorkspace(agent)
        ? "Manager/CEO เปิดหน้าคุย สร้าง Task เรียกประชุม หรือแจกงานให้ทีมได้"
        : "Agent คนนี้เปิดหน้าคุยและรับ Task ได้ แต่ไม่มีสิทธิ์อนุมัติงานทั้งระบบหรือสั่ง Backend แบบทั่วไป",
      owner: agent.role,
      status: "ready",
    },
    {
      title: "ระบบป้องกัน Codex/MCP",
      detail: "หน้าเว็บส่งเฉพาะคำขอ งานจริงอยู่หลัง Backend/Local Runner พร้อมการอนุมัติและ Audit Log",
      owner: "Risk Guard",
      status: "guarded",
    },
  ]);
  renderAgentStatusPanel();
  saveSessionSnapshot();
}

function applyPropPlacement(button, spot) {
  const placement = spot.position || spot.rect || { x: 0, y: 0, w: 10, h: 10 };
  button.style.left = `${placement.x}%`;
  button.style.top = `${placement.y}%`;
  button.style.width = `${placement.w}%`;
  const visualHeight = getPropVisualHeight(spot, placement);

  if (spot.size) {
    button.style.aspectRatio = `${spot.size[0]} / ${spot.size[1]}`;
  } else if (placement.h) {
    button.style.height = `${placement.h}%`;
  }

  button.style.zIndex = getDepthZ(placement.y + visualHeight);
}

function getPropVisualHeight(spot, placement = spot.position || spot.rect || {}) {
  if (placement.h) return placement.h;
  if (spot.size?.[0] && spot.size?.[1] && placement.w) {
    return placement.w * (spot.size[1] / spot.size[0]);
  }
  return 6;
}

function getDepthZ(y) {
  return Math.round(clamp(y, 0, 100) * 10);
}

function applyGlowColor(button, spot) {
  const colorByStatus = {
    active: "39, 212, 255",
    online: "39, 212, 255",
    ready: "37, 215, 122",
    stable: "37, 215, 122",
    monitoring: "39, 212, 255",
    queued: "255, 178, 63",
    logging: "39, 212, 255",
    watching: "255, 178, 63",
    idle: "215, 168, 75",
    blank: "215, 168, 75",
  };
  button.style.setProperty("--glow-color", spot.glow || colorByStatus[spot.status] || "39, 212, 255");
}

function updatePropVisibility() {
  const overlayEnabled = state.visibleLayers.has("ui_overlay");

  [...els.propLayer.children].forEach((node) => {
    const visible = state.visibleLayers.has(node.dataset.layer);
    node.classList.toggle("dimmed", !visible);
    node.classList.toggle("overlay-muted", !overlayEnabled);
    node.disabled = !visible;
  });

  if (state.hoveredPropId) {
    const hoveredNode = els.propLayer.querySelector(`[data-id="${state.hoveredPropId}"]`);
    if (!hoveredNode || hoveredNode.disabled) setHoveredProp(null);
  }
}

function openPropReport(propId) {
  updateDecisionLog(`เปิดรายงานของ ${displayPropName(propId)}`);
  openPropDialog(propId);
  return getInteractiveObjects().find((item) => item.id === propId) || null;
}

function propReportToMissionItems(report, owner = "mission_archivist") {
  if (!report) return [];
  const missionItems = (report.missions || []).slice(0, 3).map((mission) => ({
    title: `Mission: ${mission.title || mission.id}`,
    detail: mission.result || mission.detail || displayStatus(getMissionPresentationStatus(mission)) || "Mission นี้ถูกส่งมาที่อุปกรณ์นี้",
    owner: mission.owner || owner,
    status: mission.status || "mission",
  }));
  const eventItems = (report.events || []).slice(0, 2).map((event) => ({
    title: `เหตุการณ์: ${event.title || event.kind}`,
    detail: event.detail || event.time || "เหตุการณ์ของ Agent นี้เกี่ยวข้องกับอุปกรณ์นี้",
    owner: event.agentId || owner,
    status: event.kind || "event",
  }));
  const reportItems = (report.reports || []).slice(0, 4).map((item) => ({
    title: `รายงาน: ${item.title || item.id}`,
    detail: item.summary || displayStatus(item.status) || "รายงานนี้ถูกส่งมาที่อุปกรณ์นี้",
    owner: item.ownerAgentId || owner,
    status: item.status || "ready",
  }));
  const memoryItems = memoryCardsToMissionItems((report.memory || []).slice(0, 3), owner);
  return [...missionItems, ...reportItems, ...eventItems, ...memoryItems];
}

async function loadPropReport(propId) {
  try {
    const report = await fetchJson(`/api/props/${encodeURIComponent(propId)}/report`);
    state.propReports[propId] = report;
    renderOperationalSidebars();
    if (state.panelObject === propId) selectObject(propId, { loadBackendReport: false });
    return report;
  } catch {
    return null;
  }
}

function selectObject(id, options = {}) {
  const { loadBackendReport = true } = options;
  if (isOfficeAgentId(id)) {
    showAgentPanel(id);
    return;
  }

  const spot = getInteractiveObjects().find((item) => item.id === id);
  if (!spot) return;
  state.activeObject = id;
  state.panelObject = id;
  [...els.agentLayer.querySelectorAll(".agent-unit")].forEach((node) => node.classList.remove("active"));

  [...els.propLayer.children].forEach((node) => {
    node.classList.toggle("active", node.dataset.id === id);
  });

  const layer = state.data.layers.find((item) => item.id === spot.layer);
  const propertyRole = state.propReports[id]?.propertyRole || null;
  els.selectedLayer.textContent = layer ? (LAYER_DISPLAY[layer.id]?.[0] || layer.name) : spot.layer;
  els.reportTitle.textContent = propertyRole?.displayTitle || displayPropName(spot.id, spot.label);
  els.reportSummary.textContent = id === "mission_strategy_table"
    ? "Mission Table รวม Task ของทุก Agent แยกตามสถานะ ค้นงานในคลัง และกดดูรายละเอียดของแต่ละ Mission ได้"
    : (propertyRole?.purpose || "อุปกรณ์นี้ใช้เป็น Dashboard สำหรับดูผลลัพธ์ หากต้องการสร้างงานให้คุยกับ Agent");

  const propMetrics = {
    หน้าที่: propertyRole?.displayTitle || displayPropName(spot.id, spot.layer),
    ผู้รับผิดชอบ: (propertyRole?.ownerAgents || []).map((agentId) => displayAgentName(agentId)).join(", ") || "-",
    ประเภทรายงาน: propertyRole?.reportType || "prop_report",
    สถานะ: displayStatus(spot.status || "ready"),
    Memory: state.memoryStatus,
  };
  const localMemoryItems = memoryCardsToMissionItems(
    getRelevantMemoryCards(`${spot.id} ${spot.label} ${spot.summary} ${spot.layer}`, 3),
    "mission_archivist",
  );
  const backendReportItems = propReportToMissionItems(state.propReports[id]);

  renderMetrics(propMetrics);
  renderMissionItems([
    ...propertyRoleToMissionItems(propertyRole),
    ...(spot.missions || []).map(() => ({
      title: "เปิด Dashboard ของอุปกรณ์",
      detail: `กด ${displayPropName(spot.id, spot.label)} เพื่อดู Task สถานะ และรายงานที่เกี่ยวข้อง`,
      owner: displayAgentName(getPropOwnerAgentId(spot) || "manager"),
      status: "ready",
    })),
    ...backendReportItems,
    ...localMemoryItems,
    {
      title: id === "mission_strategy_table" ? "Kanban รวม Task ทั้งหมด" : "Dashboard สำหรับดูผลลัพธ์",
      detail: id === "mission_strategy_table"
        ? "กดโต๊ะเพื่อดูงานที่รอเริ่ม กำลังทำ รออนุมัติ ติดขัด เสร็จแล้ว ไม่สำเร็จ และเก็บเข้าคลัง"
        : "กดอุปกรณ์เพื่อดู KPI สถานะ Task ปัจจุบัน และรายงาน หากต้องการสร้างงานให้เปิด Agent",
      owner: id === "mission_strategy_table" ? "manager" : listText(propertyRole?.ownerAgents, "manager"),
      status: id === "mission_strategy_table" ? "kanban" : "read_only",
    },
  ]);
  if (loadBackendReport) loadPropReport(id);
  saveSessionSnapshot();
}

function renderMetrics(metrics) {
  els.metricGrid.innerHTML = "";
  Object.entries(metrics).forEach(([name, value]) => {
    const wrapper = document.createElement("div");
    const term = document.createElement("dt");
    const description = document.createElement("dd");
    wrapper.className = "metric";
    term.textContent = name;
    description.textContent = String(value ?? "");
    wrapper.append(term, description);
    els.metricGrid.appendChild(wrapper);
  });
}

function renderMissionItems(items) {
  els.missionList.innerHTML = "";
  const seen = new Set();
  items.forEach((mission) => {
    const key = `${mission.title || ""}::${mission.detail || ""}`;
    if (seen.has(key)) return;
    seen.add(key);
    if (mission.id && state.missions.some((item) => item.id === mission.id)) {
      els.missionList.appendChild(createTaskCard(mission));
      return;
    }
    const item = document.createElement("div");
    item.className = "mission-item";
    const title = document.createElement("strong");
    const detail = document.createElement("span");
    title.textContent = mission.status ? `[${displayStatus(getMissionPresentationStatus(mission))}] ${mission.title}` : mission.title;
    detail.textContent = mission.detail;
    item.append(title, detail);
    els.missionList.appendChild(item);
  });
}

async function assignTask(agentId, task) {
  const title = typeof task === "string" ? task : task.title || "ตรวจชุดข้อมูล Mission";
  const detail = typeof task === "string" ? "สร้างจากหน้าสั่งงาน" : task.detail || "สร้างจากหน้าสั่งงาน";
  const taskText = `${title} ${detail}`;
  if (blockSecretIntent(taskText, "agent", agentId || "risk_guard")) return null;
  const selectedAgent = getOfficeAgent(agentId);
  const assignee = selectedAgent || getOfficeAgent(state.agent.id);
  const hasSpecialistRoute = Boolean(
    selectedAgent
    && !["manager", "ceo"].includes(selectedAgent.id),
  );
  const inferredTargetId = pickTargetForTask(taskText);
  const targetId = inferredTargetId !== "mission_strategy_table" || assignee.id === "manager" || assignee.id === "ceo"
    ? inferredTargetId
    : (assignee.defaultTarget || "mission_strategy_table");
  const target = getTargetPoint(targetId);
  const mission = {
    id: `visual-${Date.now()}`,
    title,
    detail,
    owner: assignee.id,
    status: "queued",
    targetId,
  };

  state.missions.unshift(mission);
  renderOperationalSidebars();
  updateDecisionLog(`กำลังส่งคำขอสร้าง Task แบบมีระบบป้องกันให้ ${assignee.name} → ${target?.label || targetId}`);
  let backendMission = null;
  try {
    const result = await postJson("/api/manager/delegate", {
      agentId: selectedAgent?.id === "ceo" ? "ceo" : "manager",
      goal: detail,
      idempotencyKey: mission.id,
      ...(hasSpecialistRoute
        ? {
            requestedOwnerAgentId: assignee.id,
            requestedTargetId: targetId,
          }
        : {}),
    });
    const subtasks = Array.isArray(result?.subtasks) ? result.subtasks : [];
    const matchedMission = hasSpecialistRoute
      ? (
          subtasks.find((item) => item.owner === assignee.id && item.targetId === targetId)
          || subtasks.find((item) => item.owner === assignee.id)
          || subtasks[0]
        )
      : (subtasks[0] || result.parent);
    if (!matchedMission) throw new Error("Manager Agent ยังไม่ได้ส่ง Mission ของ Agent ผู้เชี่ยวชาญกลับมา");
    state.missions = state.missions.filter((item) => item.id !== mission.id);
    mergeBackendMission(result.parent);
    subtasks.forEach((item) => mergeBackendMission(item));
    backendMission = { ...matchedMission, backendAccepted: true };
  } catch (error) {
    mission.status = "failed";
    mission.detail = `คิวงานในเครื่องยังไม่รับ Task นี้: ${error.message}`;
    mission.backendAccepted = false;
    renderOperationalSidebars();
    updateDecisionLog(`${mission.id}: Backend ยังไม่รับคำขอสร้าง Task และยังไม่มี Tool ใดทำงาน`);
    if (state.modal.open) renderGameModal();
    return mission;
  }
  const backendAssignee = getOfficeAgent(backendMission.owner) || assignee;
  const backendTargetId = backendMission.targetId || targetId;
  const backendTarget = getTargetPoint(backendTargetId) || target;
  const presentationStatus = getMissionPresentationStatus(backendMission);
  updateDecisionLog(`Backend สร้าง Task ${backendMission.id}: ${title} • ${displayStatus(presentationStatus)} • ${backendAssignee.name} → ${backendTarget?.label || backendTargetId}`);
  setAgentSpeech(backendAssignee.id, `${getAgentSpeech(backendAssignee.id, "task")} เป้าหมายคือ ${backendTarget?.label || backendTargetId}`, "working");
  setAgentSpeech(state.agent.id, `ผมมอบหมายงานให้ ${backendAssignee.name} แล้วครับ`, "talking");
  recordOfficeEvent("มอบหมาย Task แล้ว", `${backendAssignee.name}: ${title} → ${backendTarget?.label || backendTargetId}`, {
    agentId: backendAssignee.id,
    kind: "task",
    missionId: backendMission.id,
    targetId: backendTargetId,
  });
  if (backendAssignee.id !== state.agent.id) {
    agentTalk({
      fromAgentId: state.agent.id,
      toAgentId: backendAssignee.id,
      message: `รับงาน "${title}" แล้วไปที่ ${backendTarget?.label || backendTargetId}`,
      silentRoute: true,
    });
  }
  showAgentPanel(backendAssignee.id, false);
  routeAgentToTargetId(backendAssignee.id, backendTargetId, `Task ${displayStatus(presentationStatus)}`);
  if (state.modal.open) renderGameModal();
  return backendMission;
}

function escapeRegExp(value) {
  return String(value).replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function hasTaskKeyword(text, keywords) {
  return keywords.some((keyword) => {
    const token = String(keyword || "").trim().toLowerCase();
    if (!token) return false;
    if (/^[a-z0-9_]+$/.test(token)) {
      return new RegExp(`(^|[^a-z0-9_])${escapeRegExp(token)}($|[^a-z0-9_])`).test(text);
    }
    return text.includes(token);
  });
}

const taskKeywords = {
  indicatorScout: ["indicator scout", "discover indicator", "new indicator", "indicator discovery", "อินดิเคเตอร์ใหม่", "อินดี้ใหม่", "หาอินดิเคเตอร์", "ค้นหาอินดิเคเตอร์", "สแกนอินดิเคเตอร์"],
  fxNewsBias: ["daily market news", "forex news", "fx bias", "pair bias", "currency bias", "ข่าวรายวัน", "ข่าว forex", "ข่าวฟอเร็กซ์", "แนวโน้มคู่เงิน", "ไบแอสคู่เงิน", "bullish", "bearish", "sideway"],
  eaDevelopment: ["ea development", "develop ea", "develop source", "modify ea", "ea source", "source ea", "แก้ source ea", "พัฒนา ea", "แก้ไข ea", "แก้ ea", "ปรับ source ea", "โจทย์พัฒนา ea"],
  vpsAgentSettings: ["hq bridge", "hq status", "agent settings", "agent preference", "vps status", "ตั้งค่า agent", "ตั้งค่าเอเจนต์", "สถานะ hq", "สถานะ bridge", "สถานะ vps"],
  archive: ["archive", "history", "memory", "old mission", "transcript", "report archive", "คลัง", "ความจำ", "งานเก่า", "ประวัติ"],
  globalDiscovery: ["global trading system", "system scout", "trading system radar", "ระบบเทรดทั่วโลก", "ค้นหาระบบเทรด", "หาระบบเทรด", "ระบบเทรดใหม่", "ea ใหม่", "อัปเดต ea"],
  deepResearch: ["deep research", "verify strategy", "research archive", "วิจัยเชิงลึก", "ตรวจสอบระบบ", "ขยายงานวิจัย", "ตรวจแหล่งอ้างอิง"],
  eaDiscovery: ["ea discovery", "discovery ea", "สร้าง ea จากเป้าหมาย", "ค้นหา ea จากเป้าหมาย", "หา ea ตามกำไร", "หา ea ตาม drawdown"],
  backtest: ["backtest", "back test", "drawdown", "profit factor", "equity", "แบคเทส", "แบคเทรด"],
  autoTradeCouncil: ["auto trade", "auto trading", "autotrade", "ai trader", "ai trade council", "consensus", "vote", "technical analysis", "price action", "news analysis", "signal", "ออโต้เทรด", "เทรดอัตโนมัติ", "สภา ai", "โหวต", "วิเคราะห์ร่วม", "ตัดสินใจ", "ซิกแนล"],
  autoTradingStatus: ["auto trade status", "live trading status", "order", "position", "ea status", "terminal status", "สถานะเทรด", "สถานะ ea", "สถานะ terminal", "ออเดอร์", "โพซิชั่น"],
  eaBuild: ["ea", "mt4", "mt5", "compile", "indicator", "คอมไพล์", "อินดี้", "อินดิเคเตอร์"],
  vps: ["vps", "latency", "uptime", "cpu", "ram", "server"],
  telegram: ["telegram", "alert", "summary", "แจ้งเตือน", "เทเลแกรม"],
  risk: ["risk", "approval", "secret", "compliance", "อนุมัติ", "ความเสี่ยง", "โทเคน"],
  codex: ["mcp", "codex", "runner", "bridge", "cli", "local runner", "โคเดก", "หลังบ้าน"],
  optimization: ["optimize", "optimization", "parameter", "overfit", "ออปติไมซ์", "พารามิเตอร์"],
};

function pickTargetForTask(text) {
  const lower = text.toLowerCase();
  if (hasTaskKeyword(lower, taskKeywords.indicatorScout)) return "left_audit_crystals";
  if (hasTaskKeyword(lower, taskKeywords.fxNewsBias)) return "left_signal_cube";
  if (hasTaskKeyword(lower, taskKeywords.eaDevelopment)) return "terminal_workstation";
  if (hasTaskKeyword(lower, taskKeywords.vpsAgentSettings)) return "right_status_crystals";
  if (hasTaskKeyword(lower, taskKeywords.deepResearch)) return "left_server_racks";
  if (hasTaskKeyword(lower, taskKeywords.archive)) return "left_server_racks";
  if (hasTaskKeyword(lower, taskKeywords.eaDiscovery)) return "right_tool_console";
  if (hasTaskKeyword(lower, taskKeywords.backtest)) return "right_tool_console";
  if (hasTaskKeyword(lower, taskKeywords.optimization)) return "right_tool_console";
  if (hasTaskKeyword(lower, taskKeywords.autoTradingStatus)) return AI_TRADE_COUNCIL_PROP_ID;
  if (hasTaskKeyword(lower, taskKeywords.autoTradeCouncil)) return AI_TRADE_COUNCIL_PROP_ID;
  if (hasTaskKeyword(lower, taskKeywords.globalDiscovery)) return "codex_mcp_portal";
  if (hasTaskKeyword(lower, taskKeywords.risk)) return "mission_strategy_table";
  if (hasTaskKeyword(lower, taskKeywords.eaBuild)) return "right_server_racks";
  if (hasTaskKeyword(lower, taskKeywords.codex)) return "codex_mcp_portal";
  if (hasTaskKeyword(lower, taskKeywords.telegram)) return "mission_strategy_table";
  if (hasTaskKeyword(lower, taskKeywords.vps)) return "right_status_crystals";
  return "mission_strategy_table";
}

function pickAgentForTask(text) {
  const lower = text.toLowerCase();
  if (hasTaskKeyword(lower, taskKeywords.indicatorScout)) return "codex_mcp_operator";
  if (hasTaskKeyword(lower, taskKeywords.fxNewsBias)) return "codex_mcp_operator";
  if (hasTaskKeyword(lower, taskKeywords.eaDevelopment)) return "ea_developer";
  if (hasTaskKeyword(lower, taskKeywords.vpsAgentSettings)) return "vps_watch";
  if (hasTaskKeyword(lower, taskKeywords.deepResearch)) return "mission_archivist";
  if (hasTaskKeyword(lower, taskKeywords.archive)) return "mission_archivist";
  if (hasTaskKeyword(lower, taskKeywords.eaDiscovery)) return "ea_developer";
  if (hasTaskKeyword(lower, taskKeywords.backtest)) return "backtest_analyst";
  if (hasTaskKeyword(lower, taskKeywords.optimization)) return "optimization_agent";
  if (hasTaskKeyword(lower, taskKeywords.autoTradingStatus)) return "vps_watch";
  if (hasTaskKeyword(lower, taskKeywords.autoTradeCouncil)) return "manager";
  if (hasTaskKeyword(lower, taskKeywords.globalDiscovery)) return "codex_mcp_operator";
  if (hasTaskKeyword(lower, taskKeywords.codex)) return "codex_mcp_operator";
  if (hasTaskKeyword(lower, taskKeywords.telegram)) return "telegram_ops";
  if (hasTaskKeyword(lower, taskKeywords.risk)) return "risk_guard";
  if (hasTaskKeyword(lower, taskKeywords.eaBuild)) return "ea_developer";
  if (hasTaskKeyword(lower, taskKeywords.vps)) return "vps_watch";
  return "manager";
}

function callMeeting({ hostAgentId = state.agent.id, participantAgentIds = [], agenda = "วางแผนงานร่วมกับ Agent ผู้เชี่ยวชาญ" } = {}) {
  if (containsPotentialSecret(agenda)) {
    blockSecretIntent(agenda, "agent", hostAgentId || "risk_guard");
    return { ok: false, error: "Risk Guard หยุดข้อความที่อาจมีข้อมูลลับก่อนแสดงภาพประกอบ" };
  }
  const host = getOfficeAgent(hostAgentId) || getOfficeAgent(state.agent.id);
  const requestedParticipantIds = participantAgentIds.length
    ? participantAgentIds
    : ["ea_developer", "backtest_analyst", "optimization_agent", "vps_watch", "telegram_ops", "risk_guard"];
  const participantIds = [...new Set(requestedParticipantIds)]
    .filter((participantId) => participantId !== host.id && getOfficeAgent(participantId));
  const meetingId = `visual-huddle-${Date.now()}`;
  updateDecisionLog(`ภาพประกอบการรวมตัวของ Agent: ${agenda}.`, { persist: false });
  setAgentSpeech(host.id, "กำลังแสดงภาพการรวมทีมที่โต๊ะ Mission", "meeting");
  participantIds.forEach((participantId) => {
    setAgentSpeech(participantId, "กำลังแสดงภาพการรวมทีมที่โต๊ะ Mission", "meeting");
  });
  recordOfficeEvent("ภาพประกอบการรวมตัวของ Agent", `${host.name}: ${agenda}`, {
    agentId: host.id,
    kind: "visual_huddle",
    persist: false,
    bridgeEvent: false,
  });
  routeAgentToTargetId(host.id, getAgentMeetingSeatTargetId(host.id), "กำลังแสดงภาพการรวมทีม", {
    persist: false,
    select: false,
  });
  participantIds.forEach((participantId) => {
    const seat = getAgentMeetingSeatTargetId(participantId);
    routeAgentToTargetId(participantId, seat, "กำลังแสดงภาพการรวมทีม", {
      persist: false,
      select: false,
    });
  });
  return {
    id: meetingId,
    participants: [host.id, ...participantIds],
    simulation: true,
    durableTranscriptCreated: false,
  };
}

function agentTalk({ fromAgentId = state.agent.id, toAgentId = "risk_guard", message = "ช่วยตรวจ Mission นี้ให้หน่อยครับ", silentRoute = false } = {}) {
  const fromAgent = getOfficeAgent(fromAgentId) || getOfficeAgent(state.agent.id);
  const toAgent = getOfficeAgent(toAgentId);
  if (!fromAgent || !toAgent) return { ok: false, error: "ไม่พบ Agent ที่ระบุ" };
  if (containsPotentialSecret(message)) {
    blockSecretIntent(message, "agent", fromAgent.id);
    return { ok: false, error: "Risk Guard หยุดข้อความที่อาจมีข้อมูลลับก่อนแสดงภาพประกอบ" };
  }
  if (String(message).includes("à¸")) {
    message = "ตรวจสถานะงานแล้วส่งรายงานกลับ Mission Table";
  }
  const line = `ภาพประกอบ: ${fromAgent.name} ส่งต่องานให้ ${toAgent.name}: ${message}`;
  setAgentSpeech(fromAgent.id, `กำลังแสดงการส่งต่องานให้ ${toAgent.name}: ${message}`, "talking");
  setAgentSpeech(toAgent.id, `กำลังรับภาพประกอบการส่งต่องานจาก ${fromAgent.name}: ${message}`, "talking");
  updateDecisionLog(line, { persist: false });
  recordOfficeEvent("ภาพประกอบการส่งต่องานของ Agent", line, {
    agentId: fromAgent.id,
    kind: "visual_handoff",
    bridgeEvent: false,
    persist: false,
  });
  if (!silentRoute) {
    routeAgentToTargetId(fromAgent.id, `${toAgent.id}_agent_position`, "กำลังแสดงการส่งต่องาน", {
      persist: false,
      select: false,
    });
  }
  if (state.panelObject === fromAgent.id || state.panelObject === toAgent.id) showAgentPanel(state.panelObject, false);
  return {
    ok: true,
    line,
    bridgeMode: state.bridge.mode,
    simulation: true,
    durableTranscriptCreated: false,
  };
}

function mergeBackendMission(mission, resultOverride = "") {
  if (!mission?.id) return;
  const existing = state.missions.find((row) => row.id === mission.id) || {};
  const item = {
    ...existing,
    ...mission,
    detail: mission.detail || existing.detail || "Mission ถูกเพิ่มเข้าคิวแล้ว",
    result: resultOverride || mission.result || existing.result || "",
  };
  const index = state.missions.findIndex((row) => row.id === mission.id);
  if (index >= 0) state.missions[index] = item;
  else state.missions.unshift(item);
  renderOperationalSidebars();
}

function applyBridgeResponse(result, { agentId, toolId } = {}) {
  if (result.bridge) applyBridgeStatus(result.bridge);
  if (result.mission) {
    mergeBackendMission(result.mission, result.finalMessage || result.mission.result || "");
    addBridgeEvent(result.mission.title, `${displayStatus(getMissionPresentationStatus(result.mission))} → ${displayPropName(result.mission.targetId || "mission_strategy_table")}`);
  } else {
    addBridgeEvent("สถานะ Bridge", result.message || "ตรวจสถานะแล้ว");
  }
  if (result.finalMessage) addBridgeEvent("รายงานจาก AI", result.finalMessage.slice(0, 260));
  updateDecisionLog(result.finalMessage ? `ได้รับรายงานของ ${result.mission?.id || "Mission"} แล้ว` : (result.message || `Bridge ทำงาน ${toolId} เสร็จแล้ว`));
  updateBridgeLabel();
  if (result.targetId && result.kind !== "approval_required") {
    routeAgentToTargetId(agentId || result.mission?.owner || "manager", result.targetId, "ไปยังจุดรับรายงาน");
  }
  return result;
}

function handleBridgeRequestError(error, toolId) {
  if (error.status) {
    state.bridge.apiOnline = true;
    state.bridge.status = error.status === 503 ? "Runner ถูกหยุดไว้" : "คำขอถูกหยุดโดยระบบป้องกัน";
    state.bridge.lastRun = `${toolId} ถูกหยุดโดยระบบป้องกันของ Backend`;
    updateDecisionLog(`ระบบป้องกันของ Backend: ${error.message}`);
    addBridgeEvent("ระบบป้องกันของ Backend", error.message);
  } else {
    state.bridge.mode = "โหมด Demo";
    state.bridge.status = "Backend ออฟไลน์";
    state.bridge.apiOnline = false;
    state.bridge.lastRun = `${toolId} ทำงานไม่สำเร็จ`;
    updateDecisionLog(`Bridge ออฟไลน์: ${error.message}`);
    addBridgeEvent("Bridge ออฟไลน์", "ติดต่อ Backend/Local Runner ไม่ได้");
  }
  updateBridgeLabel();
  return { ok: false, kind: error.body?.kind || "request_failed", error: error.message, message: error.message };
}

async function runBridgeTask({ agentId = state.agent.id, toolId = "manager_mission", prompt = "เตรียมสรุป Mission แบบมีระบบป้องกัน" } = {}) {
  if (blockSecretIntent(prompt, state.modal.type || "agent", state.modal.id || agentId)) {
    return { ok: false, kind: "secret_blocked", message: "Risk Guard หยุดข้อความที่อาจมีข้อมูลลับก่อนส่งไป Backend" };
  }
  state.bridge.lastRun = `${agentId} ขอใช้ ${toolId}`;
  state.bridge.status = "กำลังทำงาน";
  updateBridgeLabel();
  updateDecisionLog(`ส่งคำขอไปยัง Bridge แล้ว: ${toolId}`);
  if (getOfficeAgent(agentId)) showAgentPanel(agentId, false);

  try {
    const result = await postJson("/api/bridge/run", { agentId, toolId, prompt });
    return applyBridgeResponse(result, { agentId, toolId });
  } catch (error) {
    return handleBridgeRequestError(error, toolId);
  }
}

function applyBridgeStatus(bridge) {
  state.bridge.mode = bridge.mode || state.bridge.mode || "Mock";
  state.bridge.status = bridge.status || "guarded";
  state.bridge.apiOnline = true;
  state.bridge.codex = bridge.codex || state.bridge.codex;
  state.bridge.mcp = bridge.mcp || state.bridge.mcp;
  state.bridge.lastRun = bridge.time ? `ตรวจล่าสุด ${new Date(bridge.time).toLocaleTimeString("th-TH")}` : state.bridge.lastRun;
}

function updateBridgeLabel() {
  if (els.bridgeModeLabel) {
    els.bridgeModeLabel.textContent = `Bridge: ${displayBridgeValue(state.bridge.mode)}`;
  }
  if (els.bridgeStatusPill) {
    els.bridgeStatusPill.textContent = state.bridge.apiOnline ? `Bridge ${displayBridgeValue(state.bridge.mode)}` : "Bridge ออฟไลน์";
    els.bridgeStatusPill.classList.toggle("online", Boolean(state.bridge.apiOnline));
  }
  if (els.bridgeStatusText) {
    els.bridgeStatusText.textContent = state.bridge.apiOnline ? displayBridgeValue(state.bridge.status) : "ออฟไลน์";
  }
  if (els.codexStatusText) {
    els.codexStatusText.textContent = displayBridgeValue(state.bridge.codex?.status);
  }
  if (els.mcpStatusText) {
    els.mcpStatusText.textContent = displayBridgeValue(state.bridge.mcp?.status);
  }
}

function updateDecisionLog(message, options = {}) {
  if (els.decisionLog) {
    els.decisionLog.textContent = message;
  }
  if (options.persist !== false) saveSessionSnapshot();
}

function addBridgeEvent(title, detail) {
  if (!els.bridgeEventList) return;
  const existing = state.bridgeEvents.length
    ? state.bridgeEvents
    : [...els.bridgeEventList.querySelectorAll(".bridge-event")].map((node) => ({
        title: node.querySelector("strong")?.textContent || "เหตุการณ์ของ Bridge",
        detail: node.querySelector("span")?.textContent || "",
      }));
  renderBridgeEvents([{ title, detail }, ...existing].slice(0, 8));
}

function renderBridgeEvents(events = [], options = {}) {
  if (!els.bridgeEventList) return;
  state.bridgeEvents = events.slice(0, 8);
  els.bridgeEventList.innerHTML = "";
  state.bridgeEvents.slice(0, 4).forEach((event) => {
    const node = document.createElement("div");
    const title = document.createElement("strong");
    const detail = document.createElement("span");
    node.className = "bridge-event";
    title.textContent = event.title || "เหตุการณ์ของ Bridge";
    detail.textContent = event.detail || "";
    node.append(title, detail);
    els.bridgeEventList.appendChild(node);
  });
  if (options.persist !== false) saveSessionSnapshot();
}

async function refreshBridgeStatus(options = {}) {
  const { recordEvent = true, preserveDecisionLog = false } = options;
  try {
    const status = await fetchJson("/api/bridge/status");
    applyBridgeStatus(status);
    updateBridgeLabel();
    if (recordEvent) {
      addBridgeEvent("สถานะ Bridge", `Codex ${displayBridgeValue(status.codex?.status)} / MCP ${displayBridgeValue(status.mcp?.status)}`);
    }
    if (!preserveDecisionLog) {
      updateDecisionLog(`ตรวจ Bridge แล้ว: ${displayBridgeValue(state.bridge.mode)} และ Codex ${displayBridgeValue(state.bridge.codex?.status)}`);
    } else {
      saveSessionSnapshot();
    }
    return status;
  } catch (error) {
    state.bridge.mode = "โหมด Demo";
    state.bridge.status = "Backend ออฟไลน์";
    state.bridge.apiOnline = false;
    updateBridgeLabel();
    if (recordEvent) addBridgeEvent("Bridge ออฟไลน์", "ให้เปิด Local Bridge Server ก่อนใช้งาน Backend");
    saveSessionSnapshot();
    return null;
  }
}

function missionReadModelSignature(missions = []) {
  const rows = Array.isArray(missions) ? missions : [];
  const payload = rows.map((mission) => ({
    id: mission?.id || "",
    title: mission?.title || "",
    owner: mission?.owner || "",
    requester: mission?.requester || "",
    targetId: mission?.targetId || "",
    toolId: mission?.toolId || "",
    reportType: mission?.reportType || "",
    risk: mission?.risk || "",
    executionMode: mission?.executionMode || "",
    requiresHumanApproval: mission?.requiresHumanApproval === true,
    status: getMissionPresentationStatus(mission),
    createdAt: mission?.createdAt || "",
    updatedAt: mission?.updatedAt || "",
    completedAt: mission?.completedAt || "",
    nextAttemptAt: mission?.nextAttemptAt || "",
    runnerStatus: mission?.runnerStatus || "",
    reasonCode: mission?.reasonCode || mission?.errorCode || "",
    blockedCapability: mission?.blockedCapability || "",
    workStatus: mission?.workStatus || "",
    phase: mission?.phase || "",
    blocker: mission?.blocker || null,
    detail: mission?.detail || "",
    result: mission?.result || "",
    modelTier: mission?.modelTier || "",
    budget: mission?.budget || null,
    webSearchEnabled: mission?.webSearchEnabled === true,
    webSearchEvidence: mission?.webSearchEvidence || null,
    evidence: mission?.evidence || null,
    approval: mission?.approval || null,
    parentMissionId: mission?.parentMissionId || "",
    subtaskIds: Array.isArray(mission?.subtaskIds) ? mission.subtaskIds : [],
    reportIds: Array.isArray(mission?.reportIds) ? mission.reportIds : [],
    delegation: mission?.delegation || null,
    execution: mission?.execution || null,
  }));
  const serialized = JSON.stringify(payload);
  let hash = 2166136261;
  for (let index = 0; index < serialized.length; index += 1) {
    hash ^= serialized.charCodeAt(index);
    hash = Math.imul(hash, 16777619);
  }
  return `${serialized.length}:${(hash >>> 0).toString(16)}`;
}

async function loadBridgeMissions(options = {}) {
  const { replaceEvents = false, persist = true, refreshUi = true } = options;
  try {
    const data = await fetchJson("/api/missions");
    const activeMissions = Array.isArray(data.missions) ? data.missions : (Array.isArray(data.items) ? data.items : []);
    const archivedMissions = Array.isArray(data.archivedMissions)
      ? data.archivedMissions
      : (Array.isArray(data.archived) ? data.archived : []);
    const backendRows = [...new Map([...activeMissions, ...archivedMissions].map((mission, index) => [mission.id || `row-${index}`, mission])).values()];
    const backendMissions = backendRows.map((mission) => ({
      ...mission,
      detail: mission.detail || "Mission ถูกเพิ่มเข้าคิวแล้ว",
      result: mission.result || "",
      owner: mission.owner || "manager",
      status: mission.status || "queued",
    }));
    const hasBackendMissionList = Array.isArray(data.missions) || Array.isArray(data.items);
    const nextSignature = hasBackendMissionList ? missionReadModelSignature(backendMissions) : "";
    const missionChanged = hasBackendMissionList && nextSignature !== state.missionSync.signature;
    if (missionChanged) {
      state.missions = backendMissions;
      state.missionSync.signature = nextSignature;
      reconcileAgentMissionState();
      const userIsEditing = document.activeElement?.matches?.("textarea, input, select, [contenteditable='true']");
      const taskDetailInUse = Boolean(
        els.taskDetailDialog?.open
        && document.activeElement
        && els.taskDetailDialog.contains(document.activeElement),
      );
      if (refreshUi && !userIsEditing && !taskDetailInUse) {
        refreshOpenTaskDetail();
        if (isOfficeAgentId(state.activeObject)) showAgentPanel(state.activeObject, false);
        if (state.modal.open) renderGameModal();
      }
    }

    const events = activeMissions
      .filter((mission) => getMissionPresentationStatus(mission) !== "archived")
      .slice(0, 4)
      .map((mission) => ({
      title: mission.title,
      detail: `${displayStatus(getMissionPresentationStatus(mission))} → ${displayPropName(mission.targetId || "mission_strategy_table")}`,
      }));
    if (missionChanged && events.length && (replaceEvents || !state.bridgeEvents.length)) {
      renderBridgeEvents(events, { persist });
    }
    state.missionSync.lastUpdatedAt = data.updatedAt || new Date().toISOString();
    if (persist && missionChanged) saveSessionSnapshot();
    data.missionReadModelChanged = missionChanged;
    return data;
  } catch {
    // The frontend can run as a static demo before the local bridge is started.
    return null;
  }
}

function getActiveMissionForAgent(agentId) {
  const priority = {
    running: 0,
    blocked: 1,
    failed: 1,
    waiting_approval: 2,
    queued: 3,
  };
  return state.missions
    .filter((mission) => (
      getAgentIdFromOwner(mission.owner) === agentId
      && Object.prototype.hasOwnProperty.call(priority, getMissionPresentationStatus(mission))
    ))
    .sort((left, right) => {
      const statusDifference = priority[getMissionPresentationStatus(left)]
        - priority[getMissionPresentationStatus(right)];
      return statusDifference || (getMissionActivityTime(right) - getMissionActivityTime(left));
    })[0] || null;
}

function getAgentSidebarState(agent) {
  const mission = getActiveMissionForAgent(agent.id);
  const agentRuntimeStatus = String(agent?.runtimeStatus || "").trim().toLowerCase().replace(/[ -]+/g, "_");
  const codexRuntimeStatus = String(state.bridge.codex?.status || "").trim().toLowerCase().replace(/[ -]+/g, "_");
  const confirmedRuntimeUnavailable = (
    agent?.runtimeReachable === false
    || ["offline", "unavailable"].includes(agentRuntimeStatus)
    || state.bridge.status === "Backend ออฟไลน์"
    || (
      state.bridge.apiOnline === true
      && ["auth_required", "config_error", "guard_config_error", "missing", "unavailable", "blocked", "degraded"].includes(codexRuntimeStatus)
    )
  );

  if (confirmedRuntimeUnavailable) {
    return {
      key: "unavailable",
      label: "ติดต่อไม่ได้",
      mission,
      activityText: "ยังติดต่อระบบ Agent ไม่ได้",
    };
  }
  if (state.agentChat.inFlight && state.agentChat.agentId === agent.id) {
    return {
      key: "busy",
      label: "กำลังตอบคุณ",
      mission,
      activityText: "Agent กำลังคิดและตอบข้อความของคุณ",
    };
  }
  if (mission) {
    const missionStatus = getMissionPresentationStatus(mission);
    const statusLabels = {
      running: "กำลังทำงาน",
      queued: "รอเริ่มงาน",
      waiting_approval: "รอระบบตรวจ",
      blocked: "รอแก้ปัญหา",
      failed: "รอแก้ปัญหา",
    };
    const taskStateLabels = {
      running: "Task กำลังทำ",
      queued: "Task รอเริ่ม",
      waiting_approval: "Task รอระบบตรวจ",
      blocked: "Task ติดขัด",
      failed: "Task ไม่สำเร็จ",
    };
    return {
      key: "busy",
      label: statusLabels[missionStatus] || "มี Task ค้างอยู่",
      mission,
      taskStateLabel: taskStateLabels[missionStatus] || "Task",
      activityText: ["blocked", "failed"].includes(missionStatus)
        ? signalMissionReason(mission, "เปิดรายละเอียด Task เพื่อดูสาเหตุและวิธีแก้")
        : undefined,
    };
  }
  return { key: "available", label: "ว่าง", mission: null };
}

function createAgentStatusCard(agent) {
  const workload = getAgentSidebarState(agent);
  const mission = workload.mission;
  const targetId = mission?.targetId || agent.defaultTarget || agent.currentTarget || "mission_strategy_table";
  const targetLabel = state.propReports[targetId]?.propertyRole?.displayTitle
    || displayPropName(targetId, targetId || "ยังไม่กำหนดอุปกรณ์");
  const targetExists = getInteractiveObjects().some((item) => item.id === targetId);
  const card = document.createElement("article");
  const agentButton = document.createElement("button");
  const identity = document.createElement("span");
  const dot = document.createElement("i");
  const name = document.createElement("strong");
  const status = document.createElement("b");
  const task = document.createElement("span");
  const target = document.createElement("span");
  const actions = document.createElement("span");
  const taskButton = document.createElement("button");
  const targetButton = document.createElement("button");

  card.className = `agent-status-card ${workload.key}`;
  card.dataset.agentId = agent.id;
  card.classList.toggle("selected", state.selectedAgentId === agent.id);
  card.setAttribute("aria-label", `สถานะ ${agent.name}: ${workload.label}`);

  agentButton.type = "button";
  agentButton.className = "agent-status-card-heading";
  agentButton.setAttribute(
    "aria-label",
    `เปิดหน้าคุยและรายละเอียดของ ${agent.name}`,
  );
  identity.className = "agent-status-identity";
  dot.className = `agent-state-dot ${workload.key}`;
  dot.setAttribute("aria-hidden", "true");
  name.textContent = agent.name;
  identity.append(dot, name);
  status.className = "agent-status-label";
  status.textContent = workload.label;
  agentButton.append(identity, status);
  agentButton.addEventListener("click", () => openAgentDialog(agent.id));

  task.className = "agent-status-task";
  task.textContent = workload.activityText
    || (mission ? `${workload.taskStateLabel}: ${mission?.title || mission?.id}` : "พร้อมรับ Task ใหม่");
  target.className = "agent-status-target";
  target.textContent = `รายงานที่: ${targetLabel}`;
  actions.className = "agent-status-actions";
  taskButton.type = "button";
  taskButton.textContent = mission?.id ? "ดูรายละเอียด Task" : "ดูหน้า Task";
  taskButton.setAttribute("aria-label", mission?.id
    ? `เปิดรายละเอียด Task ${mission.title || mission.id} ของ ${agent.name}`
    : `เปิดหน้า Task ของ ${agent.name}`);
  taskButton.addEventListener("click", () => {
    if (mission?.id && state.missions.some((item) => item.id === mission.id)) {
      openTaskDetail(mission.id, taskButton, { source: "agent-status" });
      return;
    }
    openAgentDialog(agent.id, "tasks");
  });
  targetButton.type = "button";
  targetButton.textContent = targetExists ? "เปิดอุปกรณ์รายงาน" : "ยังไม่ผูกอุปกรณ์";
  targetButton.setAttribute("aria-label", `เปิด ${targetLabel} ของ ${agent.name}`);
  targetButton.disabled = !targetExists;
  if (targetExists) targetButton.addEventListener("click", () => openPropReport(targetId));
  actions.append(taskButton, targetButton);
  card.append(agentButton, task, target, actions);
  return card;
}

function renderAgentStatusPanel() {
  if (!els.agentStatusList) return;
  els.agentStatusList.innerHTML = "";
  getAgentStatusPriorityOrder(state.officeAgents).forEach((agent) => {
    els.agentStatusList.appendChild(createAgentStatusCard(agent));
  });
}

function getMissionActivityTime(mission) {
  const value = mission.completedAt || mission.updatedAt || mission.createdAt || "";
  const parsed = value ? new Date(value).getTime() : Number.NaN;
  return Number.isFinite(parsed) ? parsed : 0;
}

function isMissionCompletedToday(mission, now = new Date()) {
  if (getMissionPresentationStatus(mission) !== "completed") return false;
  const value = mission.completedAt || mission.updatedAt;
  if (!value) return false;
  const completedAt = new Date(value);
  if (Number.isNaN(completedAt.getTime())) return false;
  return (
    completedAt.getFullYear() === now.getFullYear()
    && completedAt.getMonth() === now.getMonth()
    && completedAt.getDate() === now.getDate()
  );
}

function createTodayWorkCard(mission) {
  const status = getMissionPresentationStatus(mission);
  const targetId = mission.targetId || "mission_strategy_table";
  const targetLabel = state.propReports[targetId]?.propertyRole?.displayTitle
    || displayPropName(mission.targetId || "mission_strategy_table", targetId);
  const card = document.createElement("button");
  const topline = document.createElement("span");
  const badge = document.createElement("span");
  const owner = document.createElement("span");
  const title = document.createElement("strong");
  const target = document.createElement("span");

  card.type = "button";
  card.className = `today-work-card ${status}`;
  card.dataset.taskMissionId = mission.id || "";
  card.setAttribute("aria-haspopup", "dialog");
  card.setAttribute("aria-label", `เปิดรายละเอียด Task ${mission.title || mission.id || "ที่เลือก"}`);
  badge.className = "task-status-badge";
  badge.textContent = displayStatus(status);
  owner.className = "today-work-owner";
  owner.textContent = displayAgentName(getAgentIdFromOwner(mission.owner) || mission.owner, "ยังไม่ได้มอบหมาย");
  topline.className = "today-work-card-topline";
  topline.append(badge, owner);
  title.textContent = mission.title || mission.id || "Task ที่ยังไม่มีชื่อ";
  target.className = "today-work-target";
  target.textContent = `รายงานที่: ${targetLabel}`;
  card.append(topline, title, target);
  card.addEventListener("click", () => openTaskDetail(mission.id, card, { source: "today-work" }));
  return card;
}

function renderTodayWorkList(container, missions, emptyText, options = {}) {
  if (!container) return;
  container.innerHTML = "";
  if (!missions.length) {
    const empty = document.createElement("div");
    empty.className = "today-work-empty";
    empty.textContent = emptyText;
    container.appendChild(empty);
    return;
  }
  const requestedLimit = Number(options.limit);
  const limit = Number.isFinite(requestedLimit) && requestedLimit > 0
    ? Math.floor(requestedLimit)
    : missions.length;
  missions.slice(0, limit).forEach((mission) => container.appendChild(createTodayWorkCard(mission)));
  const remaining = Math.max(0, missions.length - limit);
  if (remaining > 0) {
    const moreButton = document.createElement("button");
    const nextBatch = Math.min(12, remaining);
    moreButton.type = "button";
    moreButton.className = "today-work-more";
    moreButton.textContent = `ดูเพิ่มอีก ${nextBatch} งาน • เหลือ ${remaining} งาน`;
    moreButton.setAttribute("aria-label", `แสดงงานเพิ่มอีก ${nextBatch} งาน จากทั้งหมด ${missions.length} งาน`);
    moreButton.addEventListener("click", () => {
      if (typeof options.onMore === "function") options.onMore(nextBatch);
    });
    container.appendChild(moreButton);
  }
}

function renderTodayWorkPanel() {
  const now = new Date();
  const dateKey = `${now.getFullYear()}-${now.getMonth()}-${now.getDate()}`;
  if (state.todayWorkView.dateKey !== dateKey) {
    state.todayWorkView.dateKey = dateKey;
    state.todayWorkView.runningLimit = 12;
    state.todayWorkView.completedLimit = 12;
  }
  const running = state.missions
    .filter((mission) => getMissionPresentationStatus(mission) === "running")
    .sort((left, right) => getMissionActivityTime(right) - getMissionActivityTime(left));
  const completed = state.missions
    .filter((mission) => isMissionCompletedToday(mission, now))
    .sort((left, right) => getMissionActivityTime(right) - getMissionActivityTime(left));

  if (els.todayWorkDate) {
    els.todayWorkDate.textContent = new Intl.DateTimeFormat("th-TH", {
      dateStyle: "long",
    }).format(now);
  }
  if (els.todayRunningCount) els.todayRunningCount.textContent = String(running.length);
  if (els.todayCompletedCount) els.todayCompletedCount.textContent = String(completed.length);
  renderTodayWorkList(els.todayRunningList, running, "ตอนนี้ยังไม่มี Task ที่กำลังทำ", {
    limit: state.todayWorkView.runningLimit,
    onMore: (count) => {
      state.todayWorkView.runningLimit += count;
      renderTodayWorkPanel();
    },
  });
  renderTodayWorkList(els.todayCompletedList, completed, "วันนี้ยังไม่มี Task ที่เสร็จสิ้น", {
    limit: state.todayWorkView.completedLimit,
    onMore: (count) => {
      state.todayWorkView.completedLimit += count;
      renderTodayWorkPanel();
    },
  });
}

function renderOperationalSidebars() {
  renderAgentStatusPanel();
  renderTodayWorkPanel();
}

function reconcileAgentMissionState() {
  state.officeAgents.forEach((agent) => {
    const mission = getActiveMissionForAgent(agent.id);
    if (!mission) {
      if (agent.activeMissionId) {
        agent.activeMissionId = null;
        agent.activeMissionStatus = null;
        agent.activeMissionTarget = null;
        agent.activeMissionKey = null;
        if (agent.visualState !== "walking") {
          agent.visualState = "idle";
          agent.status = "Mission ปิดแล้ว พร้อมรับ Task ถัดไปแบบมีระบบป้องกัน";
          updateAgentNodeState(agent);
        }
      }
      return;
    }

    const status = getMissionPresentationStatus(mission);
    const targetId = mission.targetId || agent.defaultTarget || "mission_strategy_table";
    const assignmentKey = `${mission.id}:${status}:${targetId}`;
    const changed = agent.activeMissionKey !== assignmentKey;
    agent.activeMissionId = mission.id;
    agent.activeMissionStatus = status;
    agent.activeMissionTarget = targetId;
    agent.activeMissionKey = assignmentKey;
    if (changed && agent.visualState !== "walking") {
      const statusLabel = displayStatus(status);
      agent.visualState = ["blocked", "failed", "waiting_approval", "queued"].includes(status)
        ? "reporting"
        : "working";
      agent.status = `${statusLabel}: ${mission.title || mission.id}`;
      updateAgentNodeState(agent);
    }

    if (!changed || agent.id === state.agent.id || agent.visualState === "walking") return;
    const target = getAgentTargetPoint(targetId, agent.id);
    if (!target || getVisualDistance(agent, target) <= 1.8) {
      agent.currentTarget = targetId;
      return;
    }
    agent.currentTarget = targetId;
    moveSupportAgentToPoint(agent, target, `Mission: ${displayStatus(status)}`, { persist: false });
  });
  renderOperationalSidebars();
}

async function pollMissionReadModel() {
  if (state.missionSync.inFlight || document.visibilityState !== "visible") return null;
  state.missionSync.inFlight = true;
  try {
    const data = await loadBridgeMissions({ replaceEvents: false, persist: false, refreshUi: true });
    if (state.modal.open && state.modal.type === "prop" && state.modal.id !== "mission_strategy_table") {
      await loadPropReport(state.modal.id);
      const userIsEditing = document.activeElement?.matches?.("textarea, input, select, [contenteditable='true']");
      if (!userIsEditing) renderGameModal();
    }
    return data;
  } finally {
    state.missionSync.inFlight = false;
  }
}

function startMissionPolling() {
  if (!state.missionSync.timer) {
    state.missionSync.timer = window.setInterval(() => {
      void pollMissionReadModel();
    }, MISSION_POLL_MS);
  }
  window.setTimeout(() => void pollMissionReadModel(), 3000);
  if (!state.missionSync.visibilityHandlerBound) {
    document.addEventListener("visibilitychange", () => {
      if (document.visibilityState === "visible") void pollMissionReadModel();
    });
    state.missionSync.visibilityHandlerBound = true;
  }
}

async function loadMemoryStatus(options = {}) {
  const { recordEvent = true } = options;
  try {
    const [memoryData, meetingData] = await Promise.all([
      fetchJson(MEMORY_ENDPOINT),
      fetchJson(MEETINGS_ENDPOINT),
    ]);
    const memoryCards = Array.isArray(memoryData.items) ? memoryData.items : [];
    const meetingRecords = Array.isArray(meetingData.meetings) ? meetingData.meetings : [];
    state.memoryCards = memoryCards.slice(0, 10);
    state.meetingRecords = meetingRecords.slice(0, 8);
    state.memoryStatus = `${memoryCards.length} Memory Card / ${meetingRecords.length} การประชุม`;
    if (recordEvent) {
      addBridgeEvent("คลัง Memory พร้อมใช้งาน", state.memoryStatus);
    }
    if (state.panelObject && isOfficeAgentId(state.panelObject)) showAgentPanel(state.panelObject, false);
    saveSessionSnapshot();
    return { ok: true, memoryCards, meetingRecords };
  } catch {
    state.memoryStatus = "Backend ของ Memory ออฟไลน์";
    if (recordEvent) addBridgeEvent("คลัง Memory ออฟไลน์", "ให้เปิด Local Bridge ก่อนอ่านไฟล์ Mission ที่บันทึกไว้");
    saveSessionSnapshot();
    return { ok: false };
  }
}

function startOfficeAutonomy() {
  window.clearInterval(state.officeAutonomyTimer);
  state.officeAutonomyTimer = window.setInterval(runOfficeAutonomyTick, OFFICE_AUTONOMY_MS);
  window.setTimeout(runOfficeAutonomyTick, 1800);
}

function runOfficeAutonomyTick() {
  if (!state.officeAgents.length || document.hidden) return;
  if (collaborationOwnsOfficeVisuals()) return;
  const activeElement = document.activeElement;
  if (state.modal.open || activeElement?.matches?.("textarea, input, select, [contenteditable='true']")) return;
  const now = Date.now();
  const workers = state.officeAgents.filter((agent) => (
    agent.id !== state.agent.id
    && agent.id !== "ceo"
    && agent.visualState !== "walking"
    && !agent.activeMissionId
  ));
  if (!workers.length) return;

  const index = Math.floor(now / OFFICE_AUTONOMY_MS) % workers.length;
  const agent = workers[index];
  const defaultTarget = agent.defaultTarget || "mission_strategy_table";
  const homeTarget = agent.homeTarget || defaultTarget;
  const currentPoint = getTargetPoint(agent.currentTarget || "");
  const defaultPoint = getTargetPoint(defaultTarget);
  const isAtDefault = currentPoint && defaultPoint && getVisualDistance(currentPoint, defaultPoint) < 1.8;
  const nextTarget = isAtDefault ? "mission_strategy_table" : defaultTarget;
  const targetLabel = getTargetPoint(nextTarget)?.label || nextTarget;

  agentTalk({
    fromAgentId: state.agent.id,
    toAgentId: agent.id,
    message: `ตรวจ ${targetLabel} แล้วส่งสถานะกลับ Mission Table`,
    silentRoute: true,
  });
  recordOfficeEvent("Agent ตรวจพื้นที่อัตโนมัติ", `${agent.name} ตรวจ ${targetLabel}`, {
    agentId: agent.id,
    kind: "autonomy",
    bridgeEvent: false,
    persist: false,
  });
  routeAgentToTargetId(agent.id, nextTarget || homeTarget, "กำลังตรวจพื้นที่", { persist: false });
}

async function submitManagerCommand(goalOverride = "", requesterAgentId = "manager") {
  const requester = ["manager", "ceo"].includes(requesterAgentId) ? requesterAgentId : "manager";
  const goal = String(goalOverride || els.managerCommandInput?.value || "ตรวจสถานะ Codex/MCP Bridge และเตรียม Mission ถัดไปแบบปลอดภัย").trim();
  if (blockSecretIntent(goal, "agent", requester)) return { ok: false, kind: "secret_blocked" };
  if (state.managerCommandInFlight) return { ok: false, kind: "in_flight" };

  if (isMetatraderDiscoveryIntent(goal)) {
    state.managerCommandInFlight = true;
    if (els.runCommandButton) {
      els.runCommandButton.disabled = true;
      els.runCommandButton.textContent = "กำลังค้นหา Terminal...";
    }
    state.bridge.status = "กำลังตรวจ MT4 / MT5 แบบอ่านอย่างเดียว";
    updateBridgeLabel();
    setAgentSpeech(requester, "กำลังขอให้ Local Runner ตรวจ MT4 / MT5 แบบอ่านอย่างเดียว โดยไม่เรียก Codex และไม่เปิด Terminal", "working");
    try {
      const subject = getOfficeAgent(requester) || getOfficeAgent("manager");
      const result = await runMetatraderDiscoveryIntent(subject);
      setAgentSpeech(requester, result.reply, "talking");
      updateDecisionLog(result.reply);
      if (result.ok && result.propId) {
        state.bridge.status = "guarded";
        state.bridge.apiOnline = true;
        updateBridgeLabel();
        routeAgentToTargetId(requester, result.propId, "กำลังดูรายการ Terminal");
        await openPropDialog(result.propId);
      }
      return result;
    } catch {
      const result = {
        ok: false,
        kind: "metatrader_discovery_failed",
        reply: "ค้นหา MT4 / MT5 ไม่สำเร็จ ระบบไม่ได้เปิด Terminal ไม่ได้เชื่อมบัญชี และไม่ได้เรียก Codex",
      };
      setAgentSpeech(requester, result.reply, "talking");
      updateDecisionLog(result.reply);
      return result;
    } finally {
      state.managerCommandInFlight = false;
      if (els.runCommandButton) {
        els.runCommandButton.disabled = false;
        els.runCommandButton.textContent = "ให้ Manager แจกงาน";
      }
    }
  }

  state.managerCommandInFlight = true;
  if (els.runCommandButton) {
    els.runCommandButton.disabled = true;
    els.runCommandButton.textContent = "กำลังแจกงาน...";
  }
  state.bridge.status = "กำลังวางแผน";
  updateBridgeLabel();
  setAgentSpeech(requester, "กำลังแบ่งเป้าหมายเป็น Task และให้ Backend ตรวจว่างานใดเริ่มอัตโนมัติได้ครับ", "working");
  routeAgentToTargetId("manager", "mission_strategy_table", "กำลังวางแผน");

  try {
    const result = await postJson("/api/manager/delegate", {
      agentId: requester,
      goal,
      idempotencyKey: `visual-manager-${Date.now()}-${Math.round(Math.random() * 100000)}`,
    });
    mergeBackendMission(result.parent);
    (result.subtasks || []).forEach((mission) => mergeBackendMission(mission));
    const autoTaskCount = (result.subtasks || []).filter((mission) => isBackendAutoEligibleMission(mission)).length;
    const participants = [...new Set((result.subtasks || []).map((mission) => mission.owner).filter((id) => id && id !== "manager"))];
    if (participants.length) {
      callMeeting({
        hostAgentId: "manager",
        participantAgentIds: participants,
        agenda: `Manager Agent แจก Task ย่อย ${result.subtasks.length} งาน สำหรับ Mission ${result.parent?.id || "ใหม่"} • Backend อนุญาตอัตโนมัติ ${autoTaskCount} งาน`,
      });
    }
    (result.subtasks || []).forEach((mission) => {
      if (getOfficeAgent(mission.owner) && getTargetPoint(mission.targetId)) {
        const missionStatus = getMissionPresentationStatus(mission);
        setAgentSpeech(mission.owner, `รับ Task ย่อย ${mission.id} แล้วครับ • ${displayStatus(missionStatus)} • ไปที่ ${getTargetPoint(mission.targetId)?.label || mission.targetId}`, "working");
        routeAgentToTargetId(mission.owner, mission.targetId, `Task ${displayStatus(missionStatus)}`, { select: false });
      }
    });
    addBridgeEvent("แผนของ Manager Agent", `${result.subtasks?.length || 0} Task ย่อย • อัตโนมัติ ${autoTaskCount} งาน → โต๊ะวางแผน Mission`);
    state.bridge.status = "guarded";
    state.bridge.apiOnline = true;
    updateBridgeLabel();
    updateDecisionLog(result.report?.summary || result.parent?.result || "Manager Agent สร้างแผนแจกงานแล้ว");
    await loadBridgeMissions({ replaceEvents: false });
    await loadPropReport("mission_strategy_table");
    selectObject("mission_strategy_table");
    return result;
  } catch (error) {
    return handleBridgeRequestError(error, "manager_delegate");
  } finally {
    state.managerCommandInFlight = false;
    if (els.runCommandButton) {
      els.runCommandButton.disabled = false;
      els.runCommandButton.textContent = "ให้ Manager แจกงาน";
    }
  }
}

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

function getStagePoint(event) {
  const rect = els.stage.getBoundingClientRect();
  return {
    x: ((event.clientX - rect.left) / rect.width) * 100,
    y: ((event.clientY - rect.top) / rect.height) * 100,
    label: "จุดที่เลือกบนพื้น",
  };
}

els.openAgentButton?.addEventListener("click", () => {
  openAgentDialog("manager");
});

els.openCeoButton?.addEventListener("click", () => {
  openAgentDialog("ceo");
});

els.openMissionTableButton?.addEventListener("click", () => {
  openPropDialog("mission_strategy_table");
});

els.runCommandButton?.addEventListener("click", () => {
  submitManagerCommand();
});

els.openBridgeButton?.addEventListener("click", () => {
  runBridgeTask({
    agentId: "codex_mcp_operator",
    toolId: "codex_status",
    prompt: "ตรวจความพร้อมของ Codex CLI และ MCP",
  });
});

els.codexRateRefreshButton?.addEventListener("click", () => {
  void refreshCodexRateLimits({ manual: true });
});

els.agentCollabButton?.addEventListener("click", () => {
  setAgentCollaborationPanelOpen(Boolean(els.agentCollabPanel?.hidden));
});

[
  els.agentCollabTopic,
  els.agentCollabStartTime,
  els.agentCollabEndTime,
  els.agentCollabInterval,
  els.agentCollabMaxTurns,
  els.agentCollabMaxDailyRuns,
  els.agentCollabMinRemaining,
].forEach((element) => {
  element?.addEventListener("input", () => {
    state.agentCollaboration.editing = true;
  });
});

els.agentCollabSave?.addEventListener("click", () => {
  void saveAgentCollaborationSchedule(collaborationFormPayload());
});

els.agentCollabToggle?.addEventListener("click", () => {
  void saveAgentCollaborationSchedule({ enabled: !state.agentCollaboration.enabled });
});

els.agentCollabRunNow?.addEventListener("click", () => {
  void runAgentCollaborationNow();
});

els.operatorModeButton?.addEventListener("click", () => {
  setOperatorModePanelOpen(Boolean(els.operatorModePanel?.hidden));
});

els.operatorModeToggle?.addEventListener("click", () => {
  const nextMode = state.operatorMode.mode === "auto_guarded" ? "manual_guarded" : "auto_guarded";
  void setOperatorMode(nextMode);
});

document.addEventListener("click", (event) => {
  if (els.operatorModePanel?.hidden || els.operatorModeControl?.contains(event.target)) return;
  setOperatorModePanelOpen(false);
});

document.addEventListener("click", (event) => {
  if (els.agentCollabPanel?.hidden || els.agentCollabControl?.contains(event.target)) return;
  setAgentCollaborationPanelOpen(false);
});

els.modalCloseButton?.addEventListener("click", closeGameModal);
els.gameModalBackdrop?.addEventListener("click", closeGameModal);

els.modalTabs?.addEventListener("click", (event) => {
  const tab = event.target.closest(".modal-tab");
  if (!tab) return;
  setModalTab(tab.dataset.tab || "chat");
});

els.signalConsensusTabs?.addEventListener("click", (event) => {
  const tab = event.target.closest("[data-signal-tab]");
  if (!tab) return;
  setSignalConsensusTab(tab.dataset.signalTab, { focus: true });
});

els.signalConsensusTabs?.addEventListener("keydown", (event) => {
  const current = event.target.closest("[data-signal-tab]");
  if (!current) return;
  const currentIndex = SIGNAL_CONSENSUS_TABS.indexOf(current.dataset.signalTab);
  let nextIndex = currentIndex;
  if (event.key === "ArrowRight") nextIndex = (currentIndex + 1) % SIGNAL_CONSENSUS_TABS.length;
  else if (event.key === "ArrowLeft") nextIndex = (currentIndex - 1 + SIGNAL_CONSENSUS_TABS.length) % SIGNAL_CONSENSUS_TABS.length;
  else if (event.key === "Home") nextIndex = 0;
  else if (event.key === "End") nextIndex = SIGNAL_CONSENSUS_TABS.length - 1;
  else return;
  event.preventDefault();
  setSignalConsensusTab(SIGNAL_CONSENSUS_TABS[nextIndex], { focus: true });
});

els.workflowDashboardTabs?.addEventListener("click", (event) => {
  const tab = event.target.closest("[data-workflow-tab]");
  if (!tab || !els.workflowDashboardTabs.contains(tab)) return;
  setWorkflowDashboardTab(state.modal.id, tab.dataset.workflowTab, { focus: true });
});

els.workflowDashboardTabs?.addEventListener("keydown", (event) => {
  const current = event.target.closest("[data-workflow-tab]");
  if (!current || !els.workflowDashboardTabs.contains(current)) return;
  const tabs = [...els.workflowDashboardTabs.querySelectorAll("[data-workflow-tab]")];
  const currentIndex = tabs.indexOf(current);
  if (currentIndex < 0) return;
  let nextIndex = currentIndex;
  if (event.key === "ArrowRight") nextIndex = (currentIndex + 1) % tabs.length;
  else if (event.key === "ArrowLeft") nextIndex = (currentIndex - 1 + tabs.length) % tabs.length;
  else if (event.key === "Home") nextIndex = 0;
  else if (event.key === "End") nextIndex = tabs.length - 1;
  else return;
  event.preventDefault();
  setWorkflowDashboardTab(state.modal.id, tabs[nextIndex].dataset.workflowTab, { focus: true });
});

els.workflowDashboardContent?.addEventListener("submit", (event) => {
  const form = event.target.closest("[data-workflow-action-form]");
  if (!form || !els.workflowDashboardContent.contains(form)) return;
  event.preventDefault();
  void submitWorkflowDashboardAction(form);
});

els.workflowDashboardContent?.addEventListener("click", (event) => {
  const button = event.target.closest("[data-workflow-dictation]");
  if (!button || !els.workflowDashboardContent.contains(button)) return;
  event.preventDefault();
  toggleWorkflowVoiceDictation(button);
});

els.workflowSettingsRailContent?.addEventListener("submit", (event) => {
  const form = event.target.closest("[data-workflow-action-form]");
  if (!form || !els.workflowSettingsRailContent.contains(form)) return;
  event.preventDefault();
  void submitWorkflowDashboardAction(form);
});

els.workflowSettingsRailContent?.addEventListener("click", (event) => {
  const button = event.target.closest("[data-workflow-dictation]");
  if (!button || !els.workflowSettingsRailContent.contains(button)) return;
  event.preventDefault();
  toggleWorkflowVoiceDictation(button);
});

els.workflowHandoffReport?.addEventListener("change", () => {
  state.modal.workflowHandoff = {
    ...state.modal.workflowHandoff,
    propId: state.modal.id,
    reportId: String(els.workflowHandoffReport.value || ""),
    targetPropId: "",
    actionId: "",
    idempotencyKey: "",
    formSignature: "",
    message: "",
    tone: "neutral",
  };
  renderGameModal();
});

els.workflowHandoffTarget?.addEventListener("change", () => {
  state.modal.workflowHandoff = {
    ...state.modal.workflowHandoff,
    propId: state.modal.id,
    targetPropId: String(els.workflowHandoffTarget.value || ""),
    actionId: "",
    idempotencyKey: "",
    formSignature: "",
    message: "",
    tone: "neutral",
  };
  renderGameModal();
});

els.workflowHandoffAction?.addEventListener("change", () => {
  state.modal.workflowHandoff = {
    ...state.modal.workflowHandoff,
    propId: state.modal.id,
    actionId: String(els.workflowHandoffAction.value || ""),
    idempotencyKey: "",
    formSignature: "",
    message: "",
    tone: "neutral",
  };
  renderGameModal();
});

els.workflowHandoffButton?.addEventListener("click", () => {
  void submitWorkflowAgentHandoff();
});

els.signalConsensusLiveTabs?.addEventListener("click", (event) => {
  const tab = event.target.closest("[data-signal-live-tab]");
  if (!tab || !els.signalConsensusLiveTabs.contains(tab)) return;
  setSignalLiveAnalysisTab(tab.dataset.signalLiveTab, { focus: true });
});

els.signalConsensusLiveTabs?.addEventListener("keydown", (event) => {
  const current = event.target.closest("[data-signal-live-tab]");
  if (!current || !els.signalConsensusLiveTabs.contains(current)) return;
  const currentIndex = SIGNAL_LIVE_ANALYSIS_TABS.indexOf(current.dataset.signalLiveTab);
  if (currentIndex < 0) return;
  let nextIndex = currentIndex;
  if (event.key === "ArrowRight") nextIndex = (currentIndex + 1) % SIGNAL_LIVE_ANALYSIS_TABS.length;
  else if (event.key === "ArrowLeft") nextIndex = (currentIndex - 1 + SIGNAL_LIVE_ANALYSIS_TABS.length) % SIGNAL_LIVE_ANALYSIS_TABS.length;
  else if (event.key === "Home") nextIndex = 0;
  else if (event.key === "End") nextIndex = SIGNAL_LIVE_ANALYSIS_TABS.length - 1;
  else return;
  event.preventDefault();
  setSignalLiveAnalysisTab(SIGNAL_LIVE_ANALYSIS_TABS[nextIndex], { focus: true });
});

els.modalCommandInput?.addEventListener("input", () => {
  state.modal.lastPrompt = els.modalCommandInput.value;
});

els.modalSendButton?.addEventListener("click", handleModalSend);
els.modalAssignButton?.addEventListener("click", handleModalAssignTask);
els.modalMeetingButton?.addEventListener("click", async () => {
  const subject = getModalSubject();
  if (state.modal.type !== "agent" || !isManagerWorkspace(subject)) return;
  const agenda = getPromptFromModal();
  if (!agenda) {
    setAgentChatStatus(subject.id, "กรุณาพิมพ์หัวข้อประชุมก่อนเรียก Agent เข้าประชุม", "error");
    els.modalCommandInput?.focus();
    return;
  }
  els.modalMeetingButton.disabled = true;
  setAgentChatStatus(subject.id, "กำลังบันทึกหัวข้อและให้ Backend ตรวจ Full Access กับ Rate Limit", "working");
  try {
    const saved = await saveAgentCollaborationSchedule({ topic: agenda });
    if (!saved) {
      setAgentChatStatus(
        subject.id,
        state.agentCollaboration.messageTh || "บันทึกหัวข้อประชุมไม่สำเร็จ",
        "error",
      );
      return;
    }
    const queued = await runAgentCollaborationNow();
    if (!queued) {
      setAgentChatStatus(
        subject.id,
        state.agentCollaboration.messageTh || "Backend ยังเริ่มการประชุมไม่ได้",
        "error",
      );
      return;
    }
    setAgentChatStatus(subject.id, "Backend รับคำขอแล้ว Agent จะคุยผ่าน Codex และส่งสรุปกลับโต๊ะ Mission", "ready");
    state.modal.activeTab = "tasks";
    await loadBridgeMissions({ replaceEvents: false, persist: false });
    renderGameModal();
  } finally {
    if (els.modalMeetingButton) els.modalMeetingButton.disabled = false;
  }
});

els.modalDelegateButton?.addEventListener("click", async () => {
  const subject = getModalSubject();
  if (state.modal.type !== "agent" || !isManagerWorkspace(subject) || state.managerCommandInFlight) return;
  const goal = getPromptFromModal();
  if (!goal) {
    setAgentChatStatus(subject.id, "กรุณาพิมพ์เป้าหมายก่อนให้ Manager กระจายงานเข้าคิว", "error");
    els.modalCommandInput?.focus();
    return;
  }
  await submitManagerCommand(goal, subject.id);
  state.modal.activeTab = "tasks";
  renderGameModal();
});

els.modalDashboardRefreshConnections?.addEventListener("click", () => {
  if (state.modal.type !== "prop" || getModalSurface() !== "dashboard") return;
  void refreshDashboardConnections(state.modal.id);
});

els.modalDashboardDiscoverMetatrader?.addEventListener("click", () => {
  if (state.modal.type !== "prop" || getModalSurface() !== "dashboard") return;
  void discoverMetatraderConnections(state.modal.id);
});

els.modalDashboardConfirmMetatrader?.addEventListener("click", () => {
  if (state.modal.type !== "prop" || getModalSurface() !== "dashboard") return;
  void confirmMetatraderSelection(state.modal.id);
});

els.modalKanbanSearch?.addEventListener("input", () => {
  state.modal.searchText = els.modalKanbanSearch.value;
  renderMissionKanban({ preserveScroll: false });
});

els.modalKanbanArchiveToggle?.addEventListener("click", () => {
  state.modal.showArchived = !state.modal.showArchived;
  state.modal.selectedMissionId = null;
  renderMissionKanban({ preserveScroll: false });
  saveSessionSnapshot();
});

els.modalKanbanRefresh?.addEventListener("click", async () => {
  els.modalKanbanRefresh.disabled = true;
  try {
    await loadBridgeMissions({ replaceEvents: false });
    renderMissionKanban();
  } finally {
    els.modalKanbanRefresh.disabled = false;
  }
});

els.modalKanbanCloseDetail?.addEventListener("click", () => {
  closeTaskDetail();
});

els.taskDetailDialog?.addEventListener("cancel", (event) => {
  event.preventDefault();
  closeTaskDetail();
});

els.taskDetailDialog?.addEventListener("click", (event) => {
  if (event.target === els.taskDetailDialog) closeTaskDetail();
});

els.taskDetailDialog?.addEventListener("close", () => {
  state.taskDetailMissionId = null;
  state.taskDetailSource = null;
  syncMissionExecutionControls(null, false);
  restoreTaskDetailReturnFocus();
  taskDetailReturnFocus = null;
  taskDetailReturnMissionId = null;
  taskDetailReturnContainerId = null;
  taskDetailShouldRestoreFocus = true;
  saveSessionSnapshot();
});

els.dashboardResultDetailClose?.addEventListener("click", () => {
  closeDashboardResultDetail();
});

els.dashboardResultDialog?.addEventListener("cancel", (event) => {
  event.preventDefault();
  closeDashboardResultDetail();
});

els.dashboardResultDialog?.addEventListener("click", (event) => {
  if (event.target === els.dashboardResultDialog) closeDashboardResultDetail();
});

els.dashboardResultDialog?.addEventListener("close", () => {
  if (dashboardResultShouldRestoreFocus) dashboardResultReturnFocus?.focus?.();
  dashboardResultReturnFocus = null;
  dashboardResultShouldRestoreFocus = true;
});

els.modalKanbanApprove?.addEventListener("click", () => {
  recordKanbanApprovalDecision("approved");
});

els.modalKanbanReject?.addEventListener("click", () => {
  recordKanbanApprovalDecision("rejected");
});

els.modalKanbanExecuteMissionId?.addEventListener("input", () => {
  updateMissionExecutionConfirmation();
});

els.modalKanbanExecute?.addEventListener("click", () => {
  executeApprovedKanbanMission();
});

els.modalKanbanOpenOwnerAgent?.addEventListener("click", () => {
  const agentId = els.modalKanbanOpenOwnerAgent.dataset.agentId;
  if (agentId && getOfficeAgent(agentId)) {
    closeTaskDetail({ restoreFocus: false });
    openAgentDialog(agentId, "tasks");
  }
});

els.modalKanbanOpenTargetProp?.addEventListener("click", () => {
  const targetId = els.modalKanbanOpenTargetProp.dataset.targetId;
  if (targetId) {
    closeTaskDetail({ restoreFocus: false });
    openPropDialog(targetId);
  }
});

document.addEventListener("keydown", (event) => {
  if (event.key !== "Escape") return;
  if (!els.agentCollabPanel?.hidden) {
    setAgentCollaborationPanelOpen(false);
    els.agentCollabButton?.focus();
    return;
  }
  if (!els.operatorModePanel?.hidden) {
    setOperatorModePanelOpen(false);
    els.operatorModeButton?.focus();
    return;
  }
  if (els.dashboardResultDialog?.open) {
    event.preventDefault();
    event.stopPropagation();
    closeDashboardResultDetail();
    return;
  }
  if (els.taskDetailDialog?.open) {
    event.preventDefault();
    event.stopPropagation();
    closeTaskDetail();
    return;
  }
  if (state.modal.open) closeGameModal();
});

els.stage.addEventListener("click", (event) => {
  if (event.target.closest(".agent-unit")) return;

  const prop = getPropHitAtEvent(event);
  if (prop) {
    openPropReport(prop.id);
    return;
  }

  moveSelectedAgentToPoint(getStagePoint(event), "กำลังเดิน");
});

els.stage.addEventListener("pointermove", (event) => {
  if (event.target.closest(".agent-unit")) {
    setHoveredProp(null);
    return;
  }

  setHoveredProp(getPropHitAtEvent(event, { allowNavigationFallback: false })?.id || null);
});

els.stage.addEventListener("pointerleave", () => {
  setHoveredProp(null);
});

els.stage.addEventListener("dragstart", (event) => {
  event.preventDefault();
});

let signalChartResizeFrame = null;
window.addEventListener("resize", () => {
  if (
    !state.modal.open
    || state.modal.id !== AI_TRADE_COUNCIL_PROP_ID
    || state.modal.signalTab !== "live_analysis"
    || state.modal.signalLiveTab !== "price_action"
  ) return;
  window.cancelAnimationFrame(signalChartResizeFrame);
  signalChartResizeFrame = window.requestAnimationFrame(() => {
    const canvas = els.signalConsensusPriceActionContent?.querySelector("[data-signal-deep-price-chart]");
    drawSignalChartGrid(canvas);
  });
});

window.selectAgent = (agentId = state.agent.id) => {
  showAgentPanel(agentId);
  return getOfficeAgent(agentId) || state.agent;
};
window.moveAgentTo = routeAgentToTargetId;
window.assignTask = assignTask;
window.callMeeting = callMeeting;
window.agentTalk = agentTalk;
window.openPropReport = openPropReport;
window.runBridgeTask = runBridgeTask;
window.loadMemoryStatus = loadMemoryStatus;

init().catch((error) => {
  reportBootResourceFailure("การเริ่มหน้าเว็บ", error);
  els.reportTitle.textContent = "Visual Office กำลังใช้โหมดสำรอง";
  els.reportSummary.textContent = error.message;
  try {
    state.data ||= createFallbackRoomData();
    initializeOfficeAgents(state.restoredSession);
    renderAgentSelector();
    renderAgent();
    const renderedAgentCount = els.agentLayer.querySelectorAll(".agent-unit").length;
    window.MetafxHqBoot?.markReady({ agentCount: renderedAgentCount });
    window.setTimeout(startCodexRateLimitPolling, 0);
    window.setTimeout(startOperatorModePolling, 0);
    window.setTimeout(startAgentCollaborationPolling, 0);
    window.setTimeout(startMissionPolling, 0);
  } catch (fallbackError) {
    reportBootResourceFailure("ระบบแสดง Agent สำรอง", fallbackError, { blocking: true });
  }
});
