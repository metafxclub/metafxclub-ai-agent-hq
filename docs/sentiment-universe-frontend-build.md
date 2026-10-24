# Sentiment Universe — frontend build and maintenance

This is a developer procedure for a prepared HQ checkout/release candidate. It does not install on a customer machine, start providers, migrate credentials or authorize deployment. Customer setup is in [sentiment-universe-setup-th.md](sentiment-universe-setup-th.md).

## Source and outputs

Canonical source lives at `frontend/sentiment-universe-src`. Keep its `src`, `public`, scripts, tests, `index.html`, `package.json`, `pnpm-lock.yaml`, Vite configurations, `worker` and `.openai` inputs together. The latter two support the existing standalone build script. Rebuilding must not require the instructor's original workspace.

The verified build environment used Node 24.19.0 and pnpm 11.25.0. Use the committed lockfile; review dependency changes deliberately. Starting from the HQ source root:

```powershell
Set-Location .\frontend\sentiment-universe-src
pnpm install --frozen-lockfile
pnpm build
pnpm build:hq
pnpm test
Set-Location ..\..
```

`pnpm build` produces `dist/client/index.html` and `dist/client/assets`; its Sites metadata is not used by HQ. `pnpm build:hq` produces `dist/hq-embed/sentiment-universe.js` and `dist/hq-embed/assets`. Run the full test suite after building: its packaging test checks those generated standalone files. Neither build connects to Myfxbook, Forex Factory, MT5 or HQ trading. Node/pnpm are developer build requirements; customers use the compiled package.

## Merge public outputs into the candidate

Run this from the **prepared HQ source root** after both builds. It copies public artifacts only and does not delete an existing directory:

```powershell
$hqSourceRoot = (Get-Location).Path
$universeSource = Join-Path $hqSourceRoot 'frontend\sentiment-universe-src'
$universePublic = Join-Path $hqSourceRoot 'frontend\public\sentiment-universe'
$universeAssets = Join-Path $universePublic 'assets'
New-Item -ItemType Directory -Path $universeAssets -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $universeSource 'dist\client\index.html') -Destination (Join-Path $universePublic 'index.html') -Force
Copy-Item -LiteralPath (Join-Path $universeSource 'dist\hq-embed\sentiment-universe.js') -Destination (Join-Path $universePublic 'sentiment-universe.js') -Force
foreach ($assetFolder in @('dist\client\assets', 'dist\hq-embed\assets')) {
    Get-ChildItem -LiteralPath (Join-Path $universeSource $assetFolder) -File | ForEach-Object {
        Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $universeAssets $_.Name) -Force
    }
}
```

The asset folders are merged: standalone HTML references its hashed bundle/CSS; the HQ module needs its fonts/images. Copying only one output breaks the other surface. Current Vite output is flat under `assets`; review this copy step if that structure changes. Old hashes are not deleted by these commands; release cleanup should occur only in a separately prepared, verified staging directory.

**Do not copy `market.json`, private state, credentials/DPAPI, provider cache, logs, user MT5/account information, `node_modules` or instructor snapshots into a release.** The service creates `market.json` on each customer's machine. Keep release source clean of that generated file; an installed public mirror is not a build input and must not be overwritten with a packaged snapshot.

## HQ mount contract

`frontend/src/app/main.js` mounts the module only for equipment ID `left_signal_cube`:

```javascript
const handle = mountSentimentUniverse(host, {
  assetBase: '/frontend/public/sentiment-universe/',
  marketUrl: '/frontend/public/sentiment-universe/market.json',
  setupUrl: 'http://127.0.0.1:4197/connect',
});
// Equipment close/switch:
handle.unmount();
```

HQ must retain one mount across normal renders so camera, selection and motion survive data updates. `unmount()` cancels fetches/timers/animation frames and disposes WebGL resources. The bounded migration script `frontend/sentiment-universe-src/scripts/patch-hq-sentiment.py --main <prepared-copy>/frontend/src/app/main.js` checks known anchors and is idempotent; use it on baseline copies and review the diff. It also installs scoped `frontend/src/styles/sentiment-universe.css`. It is not a replacement for reviewing a live update.

The mirror uses the existing live schema plus `mirror.publishedAt`, refreshed every 30 seconds without rewriting per-source success/data times. Missing heartbeat or age over 120 seconds marks it stale; more than 30 seconds into the future is also stale. Cached source evidence remains visible with explicit stale/offline status.

HQ's CSP allows same-origin scripts/fonts and denies iframe embedding. Keep fonts as files (`assetsInlineLimit: 0`); `data:` fonts are not allowed. Asset/market URLs stay same-origin. Setup opens as a top-level loopback page, and no credentials/session/private configuration enter HQ frontend state. Missing fonts retain readable sans-serif fallback; module/market failures show recovery/setup actions.

## Verification and deployment boundary

- `pnpm test` covers data validation, motion, cleanup, mirror freshness, late-load/unmount cancellation, repeated HQ renders and ShadowRoot Escape/Tab behavior.
- Run HQ `tests.test_sentiment_package` and relevant release preflight after refreshing assets; retain required inventory/installer checks. Package/lifecycle smoke uses temporary state, without contacting providers or changing user task registration.
- Render under HQ headers: check room label, galaxy, selected asset, news date changes, simultaneous releases, setup link, responsive layout, close/reopen and repeated HQ polls. Check missing assets/CSP errors and preservation of camera/selection.
- Some automation `fill` implementations change a native date input's DOM value inside ShadowRoot without dispatching React's change path. Validate real calendar/keyboard selection before treating that as a user-facing filtering defect.
- Updating frontend assets does not require restarting the trading backend or MT5. Python/backend changes and full HQ releases have a separate reviewed lifecycle. Do not run the full installer just to refresh this component while trading is active.

Historical ring/trend fixtures remain for design/geometry tests. Production entries are `src/main.jsx` (standalone) and `src/embed.jsx` (HQ), both using `AppSentiment` and the live store. Do not route them to the old mock modules.
