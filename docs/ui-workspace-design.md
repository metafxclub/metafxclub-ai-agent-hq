# Metafxclub HQ workspace presentation

The October 2026 workspace refresh shares one visual template across Agent chat,
Mission Control, and all equipment dashboards. Existing characters, equipment
artwork, controls, tabs, backend payloads, permission checks and workflow states
remain in place.

## Style ownership

Load these local stylesheets in this order from `frontend/index.html`:

1. `frontend/src/styles/main.css` — existing scene, layout and visibility rules.
2. `frontend/src/styles/workspace.css` — shared tokens, modal chrome, identity
   sidebar, typography, controls, focus states and responsive shell.
3. `frontend/src/styles/agent-workspace.css` — Agent runtime, chat, attachments,
   approvals, meeting sessions and transcripts.
4. `frontend/src/styles/dashboard-workspace.css` — equipment tabs, metrics,
   research, factory, optimization, development, news, connections and Council.
5. `frontend/src/styles/home.css` — game-first home, compact header, connection
   controls, full-size room and optional status drawer.
6. `frontend/src/styles/home-panels.css` — Agent roster, quota and today's work.

The `--ui-*` variables define the navy surfaces, mint primary accent, blue
secondary accent, amber warning and rose error colors. Colors supplement the
existing status text. Numeric and loading states still come from the backend;
the design does not supply demonstration performance figures.

## Shared window

Every modal has a common header with its current subject title and a close
button. `renderGameModal()` copies its existing title into this header with
`textContent`; it does not change routing or permissions. The existing dialog
label, focus trap, Escape handling, backdrop, hidden tabs and inert closed state
are retained.

Equipment and Agent identity panels retain their original image and description.
EA Factory and Mission Control retain their existing full-width layouts. Smaller
screens stack the identity and work area, keeping settings available by scrolling.

## Preserved interaction contract

The home screen gives all space below its compact header to the interactive room.
The workspace shortcut dock and separate scene heading are removed. Users open
equipment and Agent workspaces directly from the room. The room remains at
1672:941 with no internal padding or cropping: hit testing and movement use its
bounding rectangle. It scales to the available width and height without a fixed
1672px ceiling and retains stacking isolation.

The existing quota, Agent roster and today's work controls live intact inside
the native `homeStatusMenu` disclosure. It is closed initially and overlays the
room when requested, reserving no side columns. It is not a modal dialog, so
existing workspaces and native detail dialogs can appear above it. Escape closes
the active workspace first; a subsequent Escape closes the drawer and returns
focus to its summary. Handled modal Escape events stop propagation. Header
connection popovers remain nested under their original controls for outside-click
handling. Narrow screens wrap header controls while preserving the full room.

- Keep every original input/control ID and event binding.
- Keep `[hidden]`, `disabled`, `aria-disabled`, active-tab and backend state rules.
- Do not show a control as ready unless the existing read model allows it.
- Keep `Chat`, `Workspace`, `Computer Use` and `Full Agent` capability IDs intact.
- Keep approvals, quota, platform locks, trade guards and workflow prerequisites.
- Do not replace missing data with mock profits, prices, account state or reports.
- Add a new stylesheet to runtime health, installer/release inventories and asset
  tests before depending on it in the browser.

## Verification

Run the repository regression suite with interactive Windows tests left opt-in.
Then inspect actual rendered workspaces at desktop and narrow widths. Check
navigation, scrolling, close/Escape behavior, hidden panels, disabled controls,
empty/loading/blocked states and browser errors. Browser review must not start
missions, grant access, submit Google forms, change schedules or place trades.

The frontend cache key identifies this presentation build separately from the
application's release version. Updating the local runtime is not publishing a
GitHub Release.
