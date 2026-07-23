const PROJECT_ASSET_ROOT = "./frontend/public/assets";
const MANAGER_EXEC_ASSET_ROOT = `${PROJECT_ASSET_ROOT}/agents/agent-manager-exec-v001`;
const MALE_ROSTER_ASSET_ROOT = `${PROJECT_ASSET_ROOT}/agents/male-roster-set-a-core-command-operators-v001`;
const AGENT_ASSET_VERSION = "20260612-multi-agent-roster-v001";
const MANAGER_STATIC_FRAME = `${MALE_ROSTER_ASSET_ROOT}/characters/02-hq-manager-male-static-v001.png`;
const SESSION_STORAGE_KEY = "metafx-ai-agent-hq-session-v001";
const UI_SESSION_ENDPOINT = "/api/ui-session";
const AGENT_EVENTS_ENDPOINT = "/api/agent-events";
const AGENT_CHAT_ENDPOINT = "/api/agents/chat";
const MEMORY_ENDPOINT = "/api/memory";
const MEMORY_SEARCH_ENDPOINT = "/api/memory/search";
const MEETINGS_ENDPOINT = "/api/meetings";
const CODEX_RATE_LIMIT_ENDPOINT = "/api/codex/rate-limits";
const OPERATOR_MODE_ENDPOINT = "/api/operator-mode";
const CODEX_RATE_LIMIT_POLL_MS = 60000;
const CODEX_RATE_LIMIT_FETCH_TIMEOUT_MS = 25000;
const CODEX_RATE_LIMIT_STALE_MAX_MS = 15 * 60 * 1000;
const OPERATOR_MODE_POLL_MS = 30000;
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
  auto_guarded: "อัตโนมัติ — Full Access ใน Workspace",
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
    name: "Backtest Analyst",
    role: "นักวิเคราะห์ผล Backtest",
    summary: "อ่านรายงาน Backtest, Equity, Drawdown, Profit Factor และรูปแบบการเทรด",
    status: "กำลังตรวจรายงาน",
  },
  optimization_agent: {
    name: "Optimization Agent",
    role: "ผู้เชี่ยวชาญด้านการหา Parameter",
    summary: "แนะนำช่วง Parameter เปรียบเทียบผล และเตือนความเสี่ยงจาก Overfit",
    status: "กำลังตรวจช่วง Parameter",
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
    name: "Codex MCP Operator",
    role: "ผู้ดูแล Bridge และ Local Runner",
    summary: "ตรวจความพร้อมของ Codex, MCP และ Local Runner โดยไม่เปิดเผยข้อมูลลับ",
    status: "กำลังเฝ้าดู Bridge",
  },
  mission_archivist: {
    name: "Mission Archivist",
    role: "ผู้ดูแลคลัง Mission และ Memory",
    summary: "ค้น Mission เก่า บันทึกการประชุม และชุดรายงานเพื่อนำกลับมาใช้ในงานใหม่",
    status: "กำลังจัดทำดัชนี Memory",
  },
};

const PROP_DISPLAY = {
  codex_mcp_portal: "ประตูเชื่อม Codex/MCP",
  left_server_racks: "ตู้ข้อมูลและรายงานย้อนหลัง",
  right_server_racks: "ตู้ Optimization Lab MT4/MT5",
  left_analytics_console: "จอ EA Discovery Lab และ Backtest",
  right_tool_console: "จอ Telegram และ Tool Runner",
  mission_strategy_table: "โต๊ะวางแผน Mission",
  terminal_workstation: "โต๊ะพัฒนา EA สำหรับ MT4/MT5",
  left_audit_crystals: "คริสตัลตรวจความเสี่ยงและการอนุมัติ",
  left_signal_cube: "คิวบิกสถานะ Auto Trading",
  right_status_crystals: "คริสตัลสถานะ VPS และภาพรวม HQ",
  front_entry_gate: "จุดเข้า Agent",
};

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
  missionSync: {
    inFlight: false,
    timer: null,
    visibilityHandlerBound: false,
    lastUpdatedAt: null,
  },
  managerCommandInFlight: false,
  connectionAction: {
    inFlight: false,
    propId: null,
    message: "",
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
  resetButton: document.getElementById("resetButton"),
  fitModeButton: document.getElementById("fitModeButton"),
  agentRouteButton: document.getElementById("agentRouteButton"),
  agentMeetingButton: document.getElementById("agentMeetingButton"),
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
  modalDashboardKpis: document.getElementById("modalDashboardKpis"),
  modalDashboardWork: document.getElementById("modalDashboardWork"),
  modalDashboardWorkCount: document.getElementById("modalDashboardWorkCount"),
  modalDashboardReports: document.getElementById("modalDashboardReports"),
  modalDashboardStatus: document.getElementById("modalDashboardStatus"),
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
  modalDashboardOpenMissionTable: document.getElementById("modalDashboardOpenMissionTable"),
  modalDashboardOpenOwnerAgent: document.getElementById("modalDashboardOpenOwnerAgent"),
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
  codex_mcp_portal: { x: 42.0, y: 46.0, label: "ประตูเชื่อม Codex/MCP" },
  left_analytics_console: { x: 27.0, y: 58.0, label: "จอ EA Discovery Lab และ Backtest" },
  right_tool_console: { x: 73.0, y: 58.0, label: "จอ Telegram และ Tool Runner" },
  terminal_workstation: { x: 72.5, y: 70.0, label: "โต๊ะพัฒนา EA สำหรับ MT4/MT5" },
  left_server_racks: { x: 28.0, y: 46.0, label: "ตู้ข้อมูลและรายงานย้อนหลัง" },
  right_server_racks: { x: 70.0, y: 46.0, label: "ตู้ Optimization Lab MT4/MT5" },
  left_audit_crystals: { x: 22.0, y: 72.0, label: "คริสตัลตรวจความเสี่ยงและการอนุมัติ" },
  left_signal_cube: { x: 24.2, y: 66.0, label: "คิวบิกสถานะ Auto Trading" },
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
    defaultTarget: "terminal_workstation",
    homeTarget: "terminal_workstation",
    tools: ["terminal_workstation", "code_workspace", "compile_log"],
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
    tools: ["left_analytics_console", "left_report_board", "report_archive"],
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
    defaultTarget: "right_server_racks",
    homeTarget: "right_server_racks",
    tools: ["right_server_racks", "left_analytics_console", "mission_strategy_table"],
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
    tools: ["right_status_crystals", "left_signal_cube", "right_server_racks"],
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
    defaultTarget: "right_tool_console",
    homeTarget: "right_tool_console",
    tools: ["right_tool_console", "right_status_crystals", "left_audit_crystals"],
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
    defaultTarget: "left_audit_crystals",
    homeTarget: "left_audit_crystals",
    tools: ["left_audit_crystals", "right_status_crystals", "mission_strategy_table"],
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
    tools: ["codex_mcp_portal", "right_tool_console", "mission_strategy_table"],
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
    tools: ["left_report_board", "mission_strategy_table", "report_archive"],
    status: AGENT_DISPLAY.mission_archivist.status,
    x: 28.0,
    y: 72.0,
    w: 6.0,
  },
];

const meetingSeats = {
  manager: { x: 43.5, y: 67.2, label: "ที่นั่ง Manager Agent" },
  ceo: { x: 47.2, y: 69.0, label: "ที่นั่ง CEO" },
  ea_developer: { x: 55.5, y: 68.2, label: "ที่นั่ง EA Developer" },
  backtest_analyst: { x: 38.7, y: 66.8, label: "ที่นั่ง Backtest Analyst" },
  optimization_agent: { x: 51.8, y: 72.2, label: "ที่นั่ง Optimization Agent" },
  vps_watch: { x: 58.6, y: 72.6, label: "ที่นั่ง VPS Watch" },
  telegram_ops: { x: 45.1, y: 73.0, label: "ที่นั่ง Telegram Ops" },
  risk_guard: { x: 35.7, y: 70.8, label: "ที่นั่ง Risk Guard" },
  codex_mcp_operator: { x: 49.2, y: 65.8, label: "ที่นั่ง Codex MCP Operator" },
  mission_archivist: { x: 40.8, y: 72.9, label: "ที่นั่ง Mission Archivist" },
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

  const savedSession = await loadSessionSnapshot();
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
      mode === "auto_guarded" ? "อัตโนมัติ — Full Access ใน Workspace" : "ตรวจสอบก่อนเริ่มงาน",
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
    ? "อัตโนมัติ — Full Access ใน Workspace"
    : operatorMode.mode === "manual_guarded"
      ? "ตรวจสอบก่อนเริ่มงาน"
      : "กำลังตรวจสอบ Backend...";

  els.operatorModeControl.dataset.mode = visibleMode;
  if (els.operatorModeLabel) els.operatorModeLabel.textContent = label;
  if (els.operatorModePanelTitle) {
    els.operatorModePanelTitle.textContent = operatorMode.fallback
      ? "ตรวจสอบก่อนเริ่มงาน — ค่าปลอดภัย"
      : label;
  }
  if (els.operatorModeDescription) {
    els.operatorModeDescription.textContent = autoExecutionActive
      ? "งานที่ Backend อนุญาตสามารถแก้ไฟล์และรันงานในโฟลเดอร์โปรเจกต์ได้อัตโนมัติ แล้วส่งรายงานกลับอุปกรณ์โดยไม่ต้องกดอนุมัติซ้ำ"
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
        ? "เปลี่ยนเป็นตรวจสอบก่อนเริ่มงาน"
        : operatorMode.backendAvailable
          ? "เปิดอัตโนมัติใน Workspace"
          : "รอการเชื่อมต่อ Backend";
  }
}

function setOperatorModePanelOpen(open) {
  if (!els.operatorModePanel || !els.operatorModeButton) return;
  const nextOpen = Boolean(open);
  els.operatorModePanel.hidden = !nextOpen;
  els.operatorModeButton.setAttribute("aria-expanded", String(nextOpen));
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

async function loadSessionSnapshot() {
  const localSession = loadLocalSessionSnapshot();
  try {
    const payload = await fetchJson(UI_SESSION_ENDPOINT, { timeoutMs: 1500 });
    return payload.session || localSession;
  } catch (error) {
    reportBootResourceFailure(UI_SESSION_ENDPOINT, error);
    return localSession;
  }
}

function saveSessionSnapshot() {
  if (!state.data) return;
  try {
    const snapshot = {
      savedAt: new Date().toISOString(),
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
    state.agentChat.sessionIds = Object.fromEntries(
      Object.entries(snapshot.agentChatSessions)
        .filter(([agentId, sessionId]) => (
          getOfficeAgent(agentId)
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
    task: "รับงานแล้วครับ ผมจะไปที่โต๊ะพัฒนา EA เพื่อดู Logic และโค้ด",
    meeting: "ผมเข้าประชุมเพื่อรับสเปก EA ครับ",
    backend: "ถ้าต้องแก้ไฟล์จริง ให้ Manager Agent ส่งงานผ่าน Bridge และให้ Risk Guard ตรวจด้วยครับ",
  },
  backtest_analyst: {
    idle: "ผมพร้อมอ่านผล Backtest, equity, drawdown และ profit factor ครับ",
    task: "รับงานแล้วครับ ผมจะไปที่ Analytics Console เพื่อสรุปผลทดสอบ",
    meeting: "ผมจะเตรียมมุมมองตัวเลขและข้อควรระวังเข้าประชุมครับ",
    backend: "ถ้ามีไฟล์รายงาน ให้ส่งผ่าน Backend แล้วผมจะสรุปเป็น Memory และรายงานครับ",
  },
  optimization_agent: {
    idle: "ผมพร้อมหา parameter และเช็ค overfit ครับ",
    task: "รับงาน optimize แล้วครับ ผมจะดูช่วง parameter และความเสถียร",
    meeting: "ผมจะเข้าประชุมพร้อมข้อเสนอ parameter candidate ครับ",
    backend: "งาน Optimization ขนาดใหญ่ควรกำหนดเวลารอ และบันทึกผลลงคลังงานครับ",
  },
  vps_watch: {
    idle: "ผมกำลังเฝ้าดู VPS, latency, uptime, CPU/RAM และ terminal status ครับ",
    task: "รับงานตรวจระบบแล้วครับ ผมจะไปที่ Server Racks",
    meeting: "ผมจะรายงานสถานะ VPS และ Server ให้ทีมครับ",
    backend: "คำสั่ง Restart หรือเปลี่ยน Config ต้องรอการอนุมัติก่อนเสมอครับ",
  },
  telegram_ops: {
    idle: "ผมพร้อมเตรียมการแจ้งเตือนและข้อความสรุปสำหรับ Telegram ครับ",
    task: "รับงานแจ้งเตือนแล้วครับ ผมจะไปที่จอ Telegram และ Tool Runner",
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
    idle: "ผมพร้อมตรวจ Codex CLI, MCP config และ Local Runner ครับ",
    task: "รับงานตรวจ Bridge แล้วครับ ผมจะไปที่ประตูเชื่อม Codex/MCP",
    meeting: "ผมจะรายงานสถานะ Bridge และข้อจำกัดของ Runner ครับ",
    backend: "การรันจริงจะเกิดที่ Backend เท่านั้น และต้องกำหนดเวลารอพร้อมบันทึกตรวจสอบครับ",
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
      .filter((line) => line.from === subject.id || line.to === subject.id || line.participants?.includes(subject.id))
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

function openDashboardResultDetail(item, trigger = null) {
  if (!item || !els.dashboardResultDialog || !els.dashboardResultDetailBody) return;
  const title = safeDashboardDisplayText(item.title, "รายละเอียดผลลัพธ์งาน");
  const summary = safeDashboardDisplayText(item.detail, "ยังไม่มีรายละเอียดเพิ่มเติมจาก Local Runner");
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
    item.owner ? displayAgentName(getAgentIdFromOwner(item.owner) || item.owner, item.owner) : "ยังไม่ได้ระบุ",
  );
  appendDashboardResultFact(facts, "แหล่งข้อมูล", "รายงานที่ผ่าน Backend/Local Runner และปกปิดข้อมูลลับแล้ว");
  els.dashboardResultDetailBody.append(summaryText, facts);
  if (!els.dashboardResultDialog.open) els.dashboardResultDialog.showModal();
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
      .filter((line) => line.from === subject.id || line.to === subject.id || line.participants?.includes(subject.id))
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
    detailTh: safeDashboardDisplayText(rawSelection.detailTh || "เลือก Terminal เป้าหมายได้เมื่อ Local Runner ตรวจพบรายการแบบอ่านอย่างเดียว"),
  };
}

function renderMetatraderSelection(subject, checklist, canDiscoverMetatrader) {
  if (!els.modalDashboardMetatraderSelection || !els.modalDashboardMetatraderCandidates) return;
  els.modalDashboardMetatraderSelection.hidden = !canDiscoverMetatrader;
  if (!canDiscoverMetatrader) {
    els.modalDashboardMetatraderCandidates.innerHTML = "";
    if (els.modalDashboardConfirmMetatrader) els.modalDashboardConfirmMetatrader.disabled = true;
    return;
  }

  const selection = getMetatraderSelectionModel(checklist);
  const backendSelectedId = selection.selectedCandidate?.candidateId || "";
  let chosenId = String(state.metatraderCandidateChoice[subject.id] || "");
  if (!selection.candidates.some((candidate) => candidate.candidateId === chosenId)) {
    chosenId = backendSelectedId;
    if (chosenId) state.metatraderCandidateChoice[subject.id] = chosenId;
    else delete state.metatraderCandidateChoice[subject.id];
  }
  const chosenCandidate = selection.candidates.find((candidate) => candidate.candidateId === chosenId) || null;

  if (els.modalDashboardMetatraderSummary) {
    els.modalDashboardMetatraderSummary.textContent = selection.selectedCandidate
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
      const isBackendSelected = candidate.candidateId === backendSelectedId;

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
        renderMetatraderSelection(subject, checklist, canDiscoverMetatrader);
      });

      copy.className = "metatrader-candidate-copy";
      title.textContent = candidate.labelTh;
      detail.textContent = !candidate.detected
        ? "ไม่พบรายการนี้ในการตรวจล่าสุด และยังไม่ได้เชื่อม Adapter"
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
        isBackendSelected ? "configured" : candidate.detected ? "detected" : "not_found",
        isBackendSelected ? "เลือกแล้ว" : candidate.detected ? "พบแล้ว" : "ไม่พบล่าสุด",
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
      || chosenId === backendSelectedId;
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
  const aiSchedule = operationMode?.aiEveryTwoHours || {};
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
  const currentModeLabel = operationMode?.labelTh || (currentMode === "ai_every_2h" ? "AI ตรวจทุก 2 ชั่วโมง" : "สั่งทำงานเอง");
  if (els.modalDashboardOperationMode) {
    els.modalDashboardOperationMode.textContent = safeDashboardDisplayText(currentModeLabel, "สั่งทำงานเอง");
  }

  const scheduleInterval = formatConnectionInterval(aiSchedule?.intervalMinutes);
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
  renderMetatraderSelection(subject, checklist, canDiscoverMetatrader);
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

function structuredReportItems(item) {
  const owner = item?.ownerAgentId || item?.owner || "mission_archivist";
  return [
    {
      title: safeDashboardDisplayText(item?.title || item?.id || "รายงานแบบมีโครงสร้าง"),
      detail: safeDashboardDisplayText(item?.summary || displayStatus(item?.status) || "รายงานนี้ถูกส่งมาที่ Dashboard แล้ว"),
      status: item?.status || "ready",
      owner,
    },
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

function renderPropDashboard(subject, propertyRole) {
  const report = state.propReports[subject.id] || null;
  const missions = getRelevantMissionsForSubject(subject, "prop");
  const reportItems = [
    ...(report?.reports || []).flatMap(structuredReportItems),
    ...memoryCardsToMissionItems((report?.memory || []).slice(0, 5), "Mission Archivist"),
  ];
  const meetingItems = meetingDashboardItems(report?.meetings);
  const statusItems = [
    {
      title: "ข้อมูลที่ Dashboard นี้แสดง",
      detail: propertyRole?.purpose || "ยังไม่ได้กำหนดข้อมูลสำหรับ Dashboard นี้",
      status: "read_only",
    },
    {
      title: "แหล่งข้อมูลในเครื่อง",
      detail: propertyRole?.dataSources?.length
        ? `เชื่อมข้อมูลผ่าน Local Runner และคลังรายงาน ${propertyRole.dataSources.length} แหล่ง`
        : "กำลังรอข้อมูลจาก Local Runner หรือคลังรายงาน",
      status: state.bridge.apiOnline ? "connected" : "offline",
    },
    {
      title: "ขอบเขตความปลอดภัย",
      detail: "ห้ามแสดงรหัสผ่าน Token, Cookie หรือข้อมูลลับบนหน้าจอนี้",
      status: "guarded",
    },
    ...(report?.events || []).slice(0, 4).map((event) => ({
      title: event.title || event.kind || "เหตุการณ์ล่าสุด",
      detail: event.detail || event.time || "เหตุการณ์ในเครื่องที่เกี่ยวข้องกับอุปกรณ์นี้",
      status: event.kind || "event",
    })),
    ...capabilityDashboardItems(report?.capabilities),
    ...bridgeDashboardItems(report?.bridge),
    ...meetingItems,
  ];

  renderDashboardKpis(subject, report, missions);
  renderTaskList(els.modalDashboardWork, missions.slice(0, 12), "ยังไม่มี Task ที่ส่งมาที่ Dashboard นี้");
  renderCardList(els.modalDashboardReports, [...reportItems, ...meetingItems], "ยังไม่มีรายงานหรือหลักฐานที่ส่งมาที่ Dashboard นี้");
  renderCardList(els.modalDashboardStatus, statusItems, "ยังไม่มีสถานะจากระบบในเครื่อง");
  renderDashboardConnectionPanel(subject, propertyRole);
  if (els.modalDashboardWorkCount) els.modalDashboardWorkCount.textContent = `${missions.length} Mission`;
  if (els.modalDashboardFreshness) {
    const updatedAt = report?.updatedAt ? new Date(report.updatedAt) : null;
    els.modalDashboardFreshness.textContent = updatedAt && !Number.isNaN(updatedAt.getTime())
      ? `อัปเดต ${updatedAt.toLocaleString("th-TH")}`
      : "ใช้ข้อมูลตั้งต้นในเครื่อง";
  }
  const ownerAgentId = getPropOwnerAgentId(subject);
  if (els.modalDashboardOpenOwnerAgent) {
    els.modalDashboardOpenOwnerAgent.dataset.agentId = ownerAgentId || "";
    els.modalDashboardOpenOwnerAgent.disabled = !ownerAgentId;
    els.modalDashboardOpenOwnerAgent.textContent = ownerAgentId
      ? `เปิด ${getOfficeAgent(ownerAgentId)?.name || "Agent ผู้รับผิดชอบ"}`
      : "ยังไม่มี Agent ผู้รับผิดชอบ";
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

function updateMissionExecutionConfirmation(mission = state.missions.find((item) => item.id === state.modal.selectedMissionId)) {
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
  const actionsAllowed = arguments.length < 2 ? true : Boolean(arguments[1]);
  const canExecute = actionsAllowed && isMissionReadyForExplicitExecution(mission);
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
  if (status === "blocked") return "เปิดรายละเอียดสาเหตุ แล้วให้ Manager Agent หรือ Risk Guard ช่วยปลดข้อขัดข้อง";
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
  appendMissionDetailRow(facts, "อัปเดตล่าสุด", formatThaiDateTime(mission.updatedAt || mission.createdAt));
  friendly.appendChild(facts);
  appendTaskDetailSection(friendly, "สิ่งที่ได้รับมอบหมาย", mission.detail || "ยังไม่มีคำอธิบายเพิ่มเติม", "task-detail-instruction");
  if (mission.result) appendTaskDetailSection(friendly, "ผลล่าสุด", mission.result, "task-detail-result");
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
  const openedFromKanban = state.taskDetailSource === "kanban" && state.modal.selectedMissionId === mission.id;
  const canRecordApproval = openedFromKanban
    && normalizeMissionStatus(mission.status) === "waiting_approval"
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
  syncMissionExecutionControls(mission, openedFromKanban);
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
  const mission = state.missions.find((item) => item.id === state.modal.selectedMissionId);
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
  const mission = state.missions.find((item) => item.id === state.modal.selectedMissionId);
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
    dashboard: ["connections", "tasks", "results"],
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
  const propertyRole = isAgent ? null : getPropertyRole(subject);
  const dashboardProfile = isAgent ? null : state.propReports[subject.id]?.dashboardProfile;
  const dashboardAvailability = isAgent ? null : getDashboardDataAvailability(dashboardProfile, Boolean(state.propReports[subject.id]));
  els.gameModal.classList.toggle("agent-modal", isAgent);
  els.gameModal.classList.toggle("prop-modal", !isAgent);
  els.gameModal.classList.toggle("dashboard-modal", surface === "dashboard");
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
    renderStatusGrid([
      ["โมดูล", safeDashboardDisplayText(dashboardProfile?.moduleNameTh || propertyRole?.displayTitle || displayPropName(subject.id, subject.label))],
      ["ความพร้อมของข้อมูล", safeDashboardDisplayText(dashboardAvailability?.label || "กำลังตรวจสอบ")],
      ["หน้าที่", propertyRole?.displayTitle || displayPropName(subject.id, subject.layer)],
      ["ผู้รับผิดชอบ", (propertyRole?.ownerAgents || []).map((id) => displayAgentName(id)).join(", ") || "-"],
      ["ประเภทรายงาน", propertyRole?.reportType || "prop_report"],
      ["สถานะ", displayStatus(subject.status || "ready")],
      ["จำนวน Mission", String(getRelevantMissionsForSubject(subject, type).length)],
      ["Bridge", `${displayBridgeValue(state.bridge.mode)} / ${displayBridgeValue(state.bridge.status)}`],
      ["Memory", state.memoryStatus],
    ]);
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
  state.modal.activeTab = surface === "agent" ? tab : surface === "dashboard" ? "connections" : "kanban";
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
  state.modal.open = false;
  document.body.classList.remove("modal-open");
  els.gameModal?.classList.remove("open");
  els.gameModal?.classList.remove("agent-modal", "prop-modal", "dashboard-modal", "kanban-modal");
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

  const point = getTargetPoint(targetId);
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
    .filter((line) => line.from === agent.id || line.to === agent.id || line.participants?.includes(agent.id))
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
  archive: ["archive", "history", "memory", "old mission", "transcript", "report archive", "คลัง", "ความจำ", "งานเก่า", "ประวัติ"],
  backtest: ["backtest", "back test", "drawdown", "profit factor", "equity", "แบคเทส", "แบคเทรด"],
  autoTrading: ["auto trade", "auto trading", "autotrade", "ai trader", "live trading", "order", "position", "signal", "ea status", "ออโต้เทรด", "เทรดอัตโนมัติ", "ออเดอร์", "โพซิชั่น", "ซิกแนล"],
  eaBuild: ["ea", "mt4", "mt5", "compile", "indicator", "คอมไพล์", "อินดี้", "อินดิเคเตอร์"],
  vps: ["vps", "latency", "uptime", "cpu", "ram", "server"],
  telegram: ["telegram", "alert", "summary", "แจ้งเตือน", "เทเลแกรม"],
  risk: ["risk", "approval", "secret", "compliance", "อนุมัติ", "ความเสี่ยง", "โทเคน"],
  codex: ["mcp", "codex", "runner", "bridge", "cli", "local runner", "โคเดก", "หลังบ้าน"],
  optimization: ["optimize", "optimization", "parameter", "overfit", "ออปติไมซ์", "พารามิเตอร์"],
};

function pickTargetForTask(text) {
  const lower = text.toLowerCase();
  if (hasTaskKeyword(lower, taskKeywords.archive)) return "left_server_racks";
  if (hasTaskKeyword(lower, taskKeywords.backtest)) return "left_analytics_console";
  if (hasTaskKeyword(lower, taskKeywords.optimization)) return "right_server_racks";
  if (hasTaskKeyword(lower, taskKeywords.autoTrading)) return "left_signal_cube";
  if (hasTaskKeyword(lower, taskKeywords.codex)) return "codex_mcp_portal";
  if (hasTaskKeyword(lower, taskKeywords.telegram)) return "right_tool_console";
  if (hasTaskKeyword(lower, taskKeywords.risk)) return "left_audit_crystals";
  if (hasTaskKeyword(lower, taskKeywords.eaBuild)) return "terminal_workstation";
  if (hasTaskKeyword(lower, taskKeywords.vps)) return "right_status_crystals";
  return "mission_strategy_table";
}

function pickAgentForTask(text) {
  const lower = text.toLowerCase();
  if (hasTaskKeyword(lower, taskKeywords.archive)) return "mission_archivist";
  if (hasTaskKeyword(lower, taskKeywords.backtest)) return "backtest_analyst";
  if (hasTaskKeyword(lower, taskKeywords.optimization)) return "optimization_agent";
  if (hasTaskKeyword(lower, taskKeywords.autoTrading)) return "vps_watch";
  if (hasTaskKeyword(lower, taskKeywords.codex)) return "codex_mcp_operator";
  if (hasTaskKeyword(lower, taskKeywords.telegram)) return "telegram_ops";
  if (hasTaskKeyword(lower, taskKeywords.risk)) return "risk_guard";
  if (hasTaskKeyword(lower, taskKeywords.eaBuild)) return "ea_developer";
  if (hasTaskKeyword(lower, taskKeywords.vps)) return "vps_watch";
  return "manager";
}

function callMeeting({ hostAgentId = state.agent.id, participantAgentIds = [], agenda = "วางแผนงานร่วมกับ Agent ผู้เชี่ยวชาญ", persist = true, linkedMissionId = null } = {}) {
  if (containsPotentialSecret(agenda)) {
    if (persist) blockSecretIntent(agenda, "agent", hostAgentId || "risk_guard");
    return { ok: false, error: "Risk Guard หยุดข้อความที่อาจมีข้อมูลลับก่อนบันทึกการประชุม" };
  }
  const host = getOfficeAgent(hostAgentId) || getOfficeAgent(state.agent.id);
  const participantIds = participantAgentIds.length
    ? participantAgentIds
    : ["ea_developer", "backtest_analyst", "optimization_agent", "vps_watch", "telegram_ops", "risk_guard"];
  const participants = participantIds
    .map((id) => getOfficeAgent(id)?.name || id)
    .join(", ");
  const meetingId = `meeting-${Date.now()}`;
  state.meetingTranscript.unshift({
    id: meetingId,
    label: "เริ่มการประชุม",
    from: host.id,
    participants: [host.id, ...participantIds],
    message: `${agenda} ผู้เข้าร่วม: ${participants}`,
    time: new Date().toISOString(),
  });
  state.meetingTranscript = state.meetingTranscript.slice(0, 80);
  if (persist) {
    postJson(MEETINGS_ENDPOINT, {
      id: meetingId,
      title: "การประชุมวางแผนของ Manager Agent",
      agenda,
      participants: [host.id, ...participantIds],
      summary: `${agenda} ผู้เข้าร่วม: ${participants}`,
      messages: state.meetingTranscript.slice(0, 6),
      linkedMissionId,
      source: "frontend.callMeeting",
    }).then(() => loadMemoryStatus({ recordEvent: false })).catch(() => {});
  }
  updateDecisionLog(`เรียกประชุมแล้ว: ${agenda}.`, { persist });
  setAgentSpeech(host.id, getAgentSpeech(host.id, "meeting"), "meeting");
  participantIds.forEach((participantId) => {
    setAgentSpeech(participantId, getAgentSpeech(participantId, "meeting"), "meeting");
  });
  pushChatLine({
    scopeType: "prop",
    scopeId: "mission_strategy_table",
    speaker: host.name,
    text: `เรียกประชุม: ${agenda}. ผู้เข้าร่วม: ${participants}`,
    side: "agent",
    persist,
  });
  recordOfficeEvent("เรียกประชุม", `${host.name}: ${agenda}`, {
    agentId: host.id,
    kind: "meeting",
    persist,
    bridgeEvent: persist,
  });
  if (persist) selectObject("mission_strategy_table");
  routeAgentToTargetId(host.id, meetingSeats[host.id] ? host.id : "mission_strategy_table", "กำลังเข้าประชุม", { persist, select: false });
  participantIds.forEach((participantId) => {
    const seat = meetingSeats[participantId] ? participantId : "mission_strategy_table";
    routeAgentToTargetId(participantId, seat, "กำลังเข้าประชุม", { persist, select: false });
  });
  return { id: meetingId, participants: [host.id, ...participantIds] };
}

function agentTalk({ fromAgentId = state.agent.id, toAgentId = "risk_guard", message = "ช่วยตรวจ Mission นี้ให้หน่อยครับ", silentRoute = false, persist = true } = {}) {
  const fromAgent = getOfficeAgent(fromAgentId) || getOfficeAgent(state.agent.id);
  const toAgent = getOfficeAgent(toAgentId);
  if (!fromAgent || !toAgent) return { ok: false, error: "ไม่พบ Agent ที่ระบุ" };
  if (containsPotentialSecret(message)) {
    if (persist) blockSecretIntent(message, "agent", fromAgent.id);
    return { ok: false, error: "Risk Guard หยุดข้อความที่อาจมีข้อมูลลับก่อนบันทึก" };
  }
  if (String(message).includes("à¸")) {
    message = "ตรวจสถานะงานแล้วส่งรายงานกลับ Mission Table";
  }
  const line = `${fromAgent.name} -> ${toAgent.name}: ${message}`;
  state.meetingTranscript.unshift({
    id: `talk-${Date.now()}`,
    from: fromAgent.id,
    to: toAgent.id,
    label: `${fromAgent.name} to ${toAgent.name}`,
    message,
    time: new Date().toISOString(),
  });
  state.meetingTranscript = state.meetingTranscript.slice(0, 80);
  if (persist) {
    postJson(MEETINGS_ENDPOINT.replace(/\/$/, "") + "/turn", {
      title: `${fromAgent.name} to ${toAgent.name}`,
      participants: [fromAgent.id, toAgent.id],
      summary: line,
      messages: state.meetingTranscript.slice(0, 6),
      source: "frontend.agentTalk",
    }).then(() => loadMemoryStatus({ recordEvent: false })).catch(() => {});
  }
  setAgentSpeech(fromAgent.id, `กำลังคุยกับ ${toAgent.name}: ${message}`, "talking");
  setAgentSpeech(toAgent.id, `รับข้อความจาก ${fromAgent.name}: ${message}`, "talking");
  pushChatLine({ scopeType: "agent", scopeId: fromAgent.id, speaker: fromAgent.name, text: message, side: "agent", persist });
  pushChatLine({ scopeType: "agent", scopeId: toAgent.id, speaker: fromAgent.name, text: message, side: "agent", persist });
  updateDecisionLog(line, { persist });
  recordOfficeEvent("Agent สนทนากัน", line, {
    agentId: fromAgent.id,
    kind: "talk",
    bridgeEvent: persist && !silentRoute,
    persist,
  });
  if (!silentRoute) routeAgentToTargetId(fromAgent.id, `${toAgent.id}_agent_position`, "กำลังไปคุย", { persist, select: persist });
  if (state.panelObject === fromAgent.id || state.panelObject === toAgent.id) showAgentPanel(state.panelObject, false);
  return { ok: true, line, bridgeMode: state.bridge.mode };
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
    if (hasBackendMissionList) {
      state.missions = backendMissions;
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
    if (events.length && (replaceEvents || !state.bridgeEvents.length)) renderBridgeEvents(events, { persist });
    state.missionSync.lastUpdatedAt = data.updatedAt || new Date().toISOString();
    if (persist) saveSessionSnapshot();
    return data;
  } catch {
    // The frontend can run as a static demo before the local bridge is started.
    return null;
  }
}

function getActiveMissionForAgent(agentId) {
  return state.missions
    .filter((mission) => (
      getAgentIdFromOwner(mission.owner) === agentId
      && getMissionPresentationStatus(mission) === "running"
    ))
    .sort((left, right) => getMissionActivityTime(right) - getMissionActivityTime(left))[0] || null;
}

function getAgentSidebarState(agent) {
  const mission = state.missions
    .filter((item) => (
      getAgentIdFromOwner(item.owner) === agent.id
      && getMissionPresentationStatus(item) === "running"
    ))
    .sort((left, right) => getMissionActivityTime(right) - getMissionActivityTime(left))[0] || null;
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
    return {
      key: "busy",
      label: "กำลังทำงาน",
      mission,
      taskStateLabel: "Task กำลังทำ",
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
  state.officeAgents.forEach((agent) => {
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

function renderTodayWorkList(container, missions, emptyText) {
  if (!container) return;
  container.innerHTML = "";
  if (!missions.length) {
    const empty = document.createElement("div");
    empty.className = "today-work-empty";
    empty.textContent = emptyText;
    container.appendChild(empty);
    return;
  }
  missions.forEach((mission) => container.appendChild(createTodayWorkCard(mission)));
}

function renderTodayWorkPanel() {
  const running = state.missions
    .filter((mission) => getMissionPresentationStatus(mission) === "running")
    .sort((left, right) => getMissionActivityTime(right) - getMissionActivityTime(left));
  const completed = state.missions
    .filter((mission) => isMissionCompletedToday(mission))
    .sort((left, right) => getMissionActivityTime(right) - getMissionActivityTime(left));

  if (els.todayWorkDate) {
    els.todayWorkDate.textContent = new Intl.DateTimeFormat("th-TH", {
      dateStyle: "long",
    }).format(new Date());
  }
  if (els.todayRunningCount) els.todayRunningCount.textContent = String(running.length);
  if (els.todayCompletedCount) els.todayCompletedCount.textContent = String(completed.length);
  renderTodayWorkList(els.todayRunningList, running, "ตอนนี้ยังไม่มี Task ที่กำลังทำ");
  renderTodayWorkList(els.todayCompletedList, completed, "วันนี้ยังไม่มี Task ที่เสร็จสิ้น");
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
      agent.visualState = status === "blocked" ? "reporting" : "working";
      agent.status = `${statusLabel}: ${mission.title || mission.id}`;
      updateAgentNodeState(agent);
    }

    if (!changed || agent.id === state.agent.id || agent.visualState === "walking") return;
    const target = getTargetPoint(targetId);
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

  if (now - state.lastAutonomyMeetingAt > 65000) {
    state.lastAutonomyMeetingAt = now;
    callMeeting({
      hostAgentId: state.agent.id,
      participantAgentIds: ["ea_developer", "backtest_analyst", "optimization_agent", "vps_watch", "risk_guard"],
      agenda: "ประชุมสถานะอัตโนมัติ ให้ Agent ผู้เชี่ยวชาญรายงานสถานะจุดทำงานของตน",
      persist: false,
    });
    return;
  }

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
    persist: false,
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
        linkedMissionId: result.parent?.id || null,
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

els.resetButton.addEventListener("click", () => {
  clearSessionSnapshot();
  cancelAgentMotion();
  state.supportMoveTimers.forEach((timer) => window.clearTimeout(timer));
  state.supportMoveTimers.clear();
  state.supportMoveFrames.forEach((frameId) => window.cancelAnimationFrame(frameId));
  state.supportMoveFrames.clear();
  state.supportSpriteTimers.forEach((timer) => window.clearInterval(timer));
  state.supportSpriteTimers.clear();
  window.clearTimeout(state.pathClearTimer);
  state.visibleLayers = new Set(state.data.layers.map((layer) => layer.id));
  renderLayers();
  renderProps();
  state.agent.x = agentWaypoints.front_entry_gate.x;
  state.agent.y = agentWaypoints.front_entry_gate.y;
  state.agent.direction = "down";
  state.agent.status = "พร้อมรับคำสั่ง";
  state.agent.speedMs = 1;
  state.missions = state.missions.slice(0, 1);
  state.bridgeEvents = [];
  state.officeEventLog = [];
  state.meetingTranscript = [];
  state.selectedAgentId = state.agent.id;
  initializeOfficeAgents(null);
  renderAgentSelector();
  clearPathPreview();
  renderAgent();
  renderOperationalSidebars();
  selectObject(state.data.defaultSelection || "mission_strategy_table");
  updateDecisionLog("รีเซ็ตมุมมองแล้ว และ Manager Agent กลับไปยังจุดเข้า");
  saveSessionSnapshot();
});

els.fitModeButton.addEventListener("click", () => {
  state.fitMode = state.fitMode === "contain" ? "cover" : "contain";
  els.stage.classList.toggle("cover", state.fitMode === "cover");
  saveSessionSnapshot();
});

els.agentRouteButton.addEventListener("click", () => {
  let waypointId = agentRoute[state.agentRouteIndex % agentRoute.length];

  for (let attempts = 0; attempts < agentRoute.length; attempts += 1) {
    waypointId = agentRoute[state.agentRouteIndex % agentRoute.length];
    state.agentRouteIndex += 1;
    const point = getTargetPoint(waypointId);
    if (!point || getVisualDistance(state.agent, point) > 0.4) break;
  }

  routeAgentToTargetId(state.selectedAgentId || state.agent.id, waypointId, "กำลังเดินตามเส้นทาง");
});

els.agentMeetingButton.addEventListener("click", () => {
  callMeeting({
    hostAgentId: state.agent.id,
    participantAgentIds: ["ea_developer", "backtest_analyst", "optimization_agent", "vps_watch", "telegram_ops", "risk_guard"],
    agenda: "แบ่งคำสั่งของ CEO เป็น Mission สำหรับ Agent ผู้เชี่ยวชาญ",
  });
});

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

els.modalCloseButton?.addEventListener("click", closeGameModal);
els.gameModalBackdrop?.addEventListener("click", closeGameModal);

els.modalTabs?.addEventListener("click", (event) => {
  const tab = event.target.closest(".modal-tab");
  if (!tab) return;
  setModalTab(tab.dataset.tab || "chat");
});

els.modalCommandInput?.addEventListener("input", () => {
  state.modal.lastPrompt = els.modalCommandInput.value;
});

els.modalSendButton?.addEventListener("click", handleModalSend);
els.modalAssignButton?.addEventListener("click", handleModalAssignTask);
els.modalMeetingButton?.addEventListener("click", () => {
  const subject = getModalSubject();
  if (state.modal.type !== "agent" || !isManagerWorkspace(subject)) return;
  const agenda = getPromptFromModal();
  if (!agenda) {
    setAgentChatStatus(subject.id, "กรุณาพิมพ์หัวข้อประชุมก่อนเรียก Agent เข้าประชุม", "error");
    els.modalCommandInput?.focus();
    return;
  }
  const participants = ["ea_developer", "backtest_analyst", "optimization_agent", "vps_watch", "telegram_ops", "risk_guard"];
  callMeeting({
    hostAgentId: subject.id,
    participantAgentIds: participants.filter((id) => id !== subject.id),
    agenda,
  });
  state.modal.activeTab = "tasks";
  renderGameModal();
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

els.modalDashboardOpenMissionTable?.addEventListener("click", () => {
  openPropDialog("mission_strategy_table");
});

els.modalDashboardOpenOwnerAgent?.addEventListener("click", () => {
  const agentId = els.modalDashboardOpenOwnerAgent.dataset.agentId;
  if (agentId && getOfficeAgent(agentId)) openAgentDialog(agentId);
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
    window.setTimeout(startMissionPolling, 0);
  } catch (fallbackError) {
    reportBootResourceFailure("ระบบแสดง Agent สำรอง", fallbackError, { blocking: true });
  }
});
