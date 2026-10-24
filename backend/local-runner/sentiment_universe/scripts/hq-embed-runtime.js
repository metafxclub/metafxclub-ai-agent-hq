// BEGIN SENTIMENT_UNIVERSE_HQ_V1
const SENTIMENT_UNIVERSE_ENABLED = true;
const SENTIMENT_UNIVERSE_BASE = "/frontend/public/sentiment-universe/";
let sentimentUniverseMount = null;
let sentimentUniverseGeneration = 0;
let sentimentUniverseModule = null;

function disposeSentimentUniverse() {
  sentimentUniverseGeneration += 1;
  sentimentUniverseMount?.handle?.unmount();
  sentimentUniverseMount?.host?.remove();
  sentimentUniverseMount = null;
  els.gameModal?.classList.remove("sentiment-universe-modal");
}

function renderSentimentUniverse() {
  const content = els.workflowDashboardContent;
  if (!content) return;
  els.gameModal?.classList.add("sentiment-universe-modal");
  if (els.workspaceTitle) els.workspaceTitle.textContent = "Sentiment Universe · 32 สินทรัพย์";
  if (els.modalTitle) els.modalTitle.textContent = "Sentiment Universe · 32 สินทรัพย์";
  if (els.modalWorkflowDashboardWorkspace) els.modalWorkflowDashboardWorkspace.hidden = false;
  if (els.workflowResultsPanel) els.workflowResultsPanel.hidden = true;
  content.hidden = false;
  content.setAttribute("aria-label", "Sentiment Universe · ข้อมูลตลาดแบบดูอย่างเดียว");
  if (!document.getElementById("sentiment-universe-layout")) {
    const stylesheet = document.createElement("link");
    stylesheet.id = "sentiment-universe-layout";
    stylesheet.rel = "stylesheet";
    stylesheet.href = "/frontend/src/styles/sentiment-universe.css?v=20261024-hq-v1";
    document.head.appendChild(stylesheet);
  }
  if (sentimentUniverseMount?.host?.parentNode === content) return;
  disposeSentimentUniverse();
  els.gameModal?.classList.add("sentiment-universe-modal");
  const generation = ++sentimentUniverseGeneration;
  const host = document.createElement("div");
  host.className = "hq-sentiment-universe-host";
  const loading = document.createElement("p");
  loading.className = "hq-sentiment-loading";
  loading.setAttribute("role", "status");
  loading.textContent = "กำลังเปิด Sentiment Universe…";
  host.appendChild(loading);
  content.replaceChildren(host);
  sentimentUniverseMount = {host,handle:null};
  const moduleUrl = `${SENTIMENT_UNIVERSE_BASE}sentiment-universe.js?v=20261024-hq-v1`;
  if (!sentimentUniverseModule) {
    sentimentUniverseModule = import(moduleUrl).catch((error) => {
      sentimentUniverseModule = null;
      throw error;
    });
  }
  sentimentUniverseModule.then((module) => {
    if (generation !== sentimentUniverseGeneration || !host.isConnected || !state.modal.open
      || state.modal.type !== "prop" || state.modal.id !== FX_NEWS_BIAS_PROP_ID) return;
    host.replaceChildren();
    sentimentUniverseMount.handle = module.mountSentimentUniverse(host, {
      assetBase: SENTIMENT_UNIVERSE_BASE,
      marketUrl: `${SENTIMENT_UNIVERSE_BASE}market.json`,
      setupUrl: "http://127.0.0.1:4197/connect",
    });
  }).catch(() => {
    if (generation !== sentimentUniverseGeneration || !host.isConnected) return;
    const message = document.createElement("p");
    message.setAttribute("role", "alert");
    message.textContent = "ยังเปิด Sentiment Universe ไม่สำเร็จ ตรวจบริการข้อมูลในเครื่องแล้วลองอีกครั้ง";
    const setup = document.createElement("a");
    setup.href = "http://127.0.0.1:4197/connect";
    setup.target = "_blank"; setup.rel = "noopener noreferrer";
    setup.textContent = "ตั้งค่า Myfxbook / MT5";
    const retry = document.createElement("button");
    retry.type = "button"; retry.textContent = "ลองเปิดอีกครั้ง";
    retry.addEventListener("click", () => {disposeSentimentUniverse();renderSentimentUniverse();});
    host.replaceChildren(message,setup,retry);
  });
}
// END SENTIMENT_UNIVERSE_HQ_V1
