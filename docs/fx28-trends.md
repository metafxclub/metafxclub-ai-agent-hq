# FX28 trends: prices first, daily Codex context

The `left_signal_cube` dashboard shows 28 canonical Forex pairs in full-width rows. Each row separates short (M15/H1), medium (H1/H4/D1), and long (D1/W1) closed-bar trends. It is analysis-only: no order submission, account access, chart switching or EA input changes.

## Data and calculation

The Backend refreshes prices every 15 minutes, including when the browser is closed. The selected MT5 terminal must already be running and connected. The bounded child collector binds to that terminal's process, executable and data path; it does not log in or issue trading commands. Broker suffixes are resolved from base/profit currencies and ambiguous symbols remain unavailable. Missing history is shown explicitly and retried on the next refresh.

Each timeframe uses up to 200 closed bars (at least 60 required). Bullish means close > EMA20 > EMA50, positive five-bar EMA20 slope and EMA separation both greater than 0.10 ATR14. Bearish uses the symmetric negative conditions. A horizon is bullish/bearish only when all its timeframes agree; otherwise it is labelled sideways/mixed. This is an auditable technical classification, not a probability or a promise of returns.

Tick volume is the broker's quote activity. The H1 ratio compares the last closed bar with the preceding 20 bars; it is not global exchange volume or net buy/sell flow. UTC normalization uses an offset verified by advancing live quotes from multiple pairs. Recent verified offsets can be reused over market closures; historical DST boundaries may differ by one hour.

## Daily AI and news

One daily workflow is admitted after 08:00 Asia/Bangkok, with same-day catch-up after startup. It uses the current machine's existing Codex session and normal quota/reserve/operator gates. Previously admitted work, including the trading Council, has priority. Opening the dashboard only reads cached results and cannot start duplicate work.

Codex explains an immutable, hash-bound snapshot. It cannot change computed directions or prices. Optional official news context must cite assigned sources and pass native same-run URL evidence checks. The legacy direct news schedule remains separate. News outages or quota waits do not hide fresh price trends. The daily AI snapshot/date are distinct from the more frequently refreshed prices.

Backend state exposes waiting/deferred/error and next refresh times. Stale prices lose current directional status instead of silently remaining current. The daily mission has a durable idempotency key; tasks still pending after midnight cannot consume quota for the old day. Technical failures may receive one bounded same-mission retry through the normal gates; schema or evidence failures remain explicit. No credentials or user runtime state belong in release artifacts.

## Distribution and checks

The Windows installer requirements include pinned, hashed MetaTrader5 and NumPy wheels for supported Python versions. Both FX28 modules are mandatory in installer/release inventories. Students need a version containing these changes, their own connected MT5 terminal and their own Codex login; updating the instructor's machine does not update other installations.

Regression coverage includes the pure calculations, selected-terminal collector, strict Runner output/provenance, daily workflow/GET/idempotency/quota behavior, dashboard rendering and existing Council/Gateway behavior. Live validation must additionally confirm real closed bars, one actual daily result, visible UI, and unchanged trading configuration/command ledger.

Official API references: [closed-bar rates](https://www.mql5.com/en/docs/python_metatrader5/mt5copyratesfrompos_py), [terminal connection](https://www.mql5.com/en/docs/python_metatrader5/mt5initialize_py).
