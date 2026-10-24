# Sentiment Universe — local data and HQ embedding

The read-only market service listens on `http://127.0.0.1:4197`. It does not call the HQ council, trading gateway, EA or order interfaces. The HQ integration remains a release candidate until its release/package gates pass; an older published HQ tag does not automatically contain it.

## Two frontends, one local service

| Surface | Compiled files | Market data |
| --- | --- | --- |
| Standalone on 4197 | `dist/client` | Same-origin `/api/market` |
| HQ equipment `left_signal_cube` | `dist/hq-embed`, mounted in a ShadowRoot | Same-origin `/frontend/public/sentiment-universe/market.json` |

HQ serves the module, images and fonts itself. It does not use a cross-port iframe. Its existing CSP/frame restrictions remain in force. The separate service atomically publishes a sanitized public mirror with `mirror.publishedAt` every 30 seconds. Missing heartbeat, age over 120 seconds, or a timestamp over 30 seconds in the future marks the connection stale. This heartbeat does **not** change provider `lastSuccessAt` or market `asOf` times.

Setup opens `http://127.0.0.1:4197/connect` as a top-level local page for Myfxbook and running-MT5 selection. The HQ frontend receives no password, session token, credential path or private configuration. Its cancellable polling stops when the equipment closes; scheduled collection continues independently of the browser.

Canonical frontend source is `frontend/sentiment-universe-src` in HQ. See `docs/sentiment-universe-frontend-build.md` there for reproducible builds and the exact merge of both public outputs. Compiled HQ files are under `frontend/public/sentiment-universe`, not just the original `dist/client` output.

## First-time customer setup and operation

Use a tested HQ release that includes the service. HQ supplies its pinned Python dependencies; customers should not manually install another Python environment. Open `/connect`, enter the customer's own Myfxbook credentials and choose the customer's own already-running MT5. Check each source after saving; healthy service does not prove provider coverage.

From the installed HQ directory:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup-sentiment-universe.ps1 -OpenSetup
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\sentiment-universe.ps1 -Action Status
```

HQ uses a per-user `Metafxclub Sentiment Universe` task and its own supervisor. It starts after Windows sign-in, checks periodically, and does not create another worker when already running. It neither restarts HQ nor launches or changes MT5. Another application's port is not reclaimed. The computer must remain on/online, with selected MT5 running and connected for fresh history.

The original `python scripts/start-live.py` is a development/legacy launcher. Do not run it alongside HQ's instance or install both startup mechanisms. Customer migration instructions are in HQ's `docs/sentiment-universe-setup-th.md`.

Private state is `%LOCALAPPDATA%/Metafxclub/SentimentUniverse`. Credentials/session use Windows DPAPI for the current user, outside repository/static files. Copying a DPAPI file to another user/machine does not provision that account. Never package instructor credentials, snapshots, caches or logs. Frontend updates preserve private state.

## Sources and schedules

- **Myfxbook:** official HTTPS login/community-outlook endpoints provide Long/Short percentages and average entry prices when available. Outlook attempts are at least 20 minutes apart, with a persistent rolling budget of 100 calls per 24 hours including login/failed calls. Browser refreshes read local cache. Authentication replacement is serialized with collection; sessions can renew using stored local credentials.
- **MT5 correlation:** a guarded, bounded reader uses the selected running executable and exact data directory. It does not log in, change accounts/charts, attach EAs or trade. Correlation refreshes hourly with bounded failure retries. Pearson uses natural-log close-to-close returns, aligning both ends of consecutive H1 intervals before taking the latest 200 common observations, with at least 100 required. Gaps are not forward-filled. Missing/flat/stale data has no coefficient/link; zero remains valid.
- **Forex Factory:** official weekly JSON/ICS/XML exports supply a daily calendar snapshot. It preserves all exported events/impact levels, simultaneous releases and adjacent cached weeks, and flags incomplete Thai-day coverage. Times use explicit offsets and source America/New_York where specified, then display in Asia/Bangkok. Fetch occurs once per successful Thai day with bounded retries for unavailable/new-week feeds or HTTP 429. The export does not supply actual release results.

Thai explanations/scenarios use explicit educational rules/dictionaries. No Codex or council quota is used for these collections/calculations. They do not promise market direction. Failures retain last successful evidence with its timestamp/status rather than inventing replacements.

Provider rounding can make Myfxbook shares total 99/101. Raw displayed percentages remain unchanged; only the color scale normalizes their visual proportion. Sentiment is community positioning, not a short/medium/long price-trend analysis.

## MT5 selection and clock verification

Current setup records an independent `selectionId`, exact `terminalPath`/`dataPath`, and installer-owned interpreter. New installations do **not** require an HQ price snapshot or old `inputCachePath` to establish selection. Choose through `/connect`; avoid editing private configuration manually.

The reader verifies broker-clock offset from multiple actually advancing quote clocks bound to the selected terminal. It requires at least three agreeing instruments and two advancing quotes, with offsets in 15-minute steps within ±14 hours. A first installation during market closure may wait for quotes; it does not invent an offset. Prior verified clocks are held only within bounded brief-pause/weekend rules. Observed offset changes exclude ambiguous history intervals; older unobserved history remains explicitly marked as a historical-clock approximation.

The MT5 Python library has no connect-only initialization option. Exact process/path checks reduce, but cannot eliminate, the narrow native initialization race if the selected terminal dies at that moment.

The former adapter required HQ `inputCachePath`/`candidateId` and clock metadata. These are legacy migration inputs, not requirements for new customers. Migration detaches old configuration only when terminal identity, discovery and cache binding agree; it does not copy another user's market/account state.

Coverage depends on broker instruments and history. The instructor's 24 October 2026 verification had 28 FX plus XAUUSD/XAGUSD: 30 instruments and 435 valid relationships. WTI/BRENT were unavailable, leaving their 61 possible relationships missing. Other machines may differ. No oil contract substitution or symbol mapping is automatic.

## Recovery and provider rights

The UI distinguishes readiness, partial coverage, stale data, authentication problems, rate limits and an offline service. Missing data never becomes 50/50 sentiment, zero correlation or invented news. Reopening the page does not reset budgets. Keep private rate-limit/failure state intact during maintenance.

This local integration is not a blanket redistribution license. Myfxbook's sentiment plans specify personal use and direct commercial users to contact the provider. Forex Factory restricts republication/redistribution of its calendar database. Confirm rights before sharing feeds or publishing a hosted product; public export URLs alone do not grant redistribution rights.

- Myfxbook API: https://www.myfxbook.com/api
- Myfxbook plans: https://www.myfxbook.com/outlook-indicator
- Forex Factory exports: https://www.forexfactory.com/calendar
- Forex Factory notices: https://www.forexfactory.com/notices
- MT5 closed bars: https://www.mql5.com/en/docs/python_metatrader5/mt5copyratesfrompos_py
