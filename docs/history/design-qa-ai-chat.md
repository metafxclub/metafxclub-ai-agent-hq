# Design QA — ห้องแชต AI รวม

## Source truth

- Reference: `artifacts/design-qa/reference-ai-chat-1904x893.png`
- Requested change: remove the two repeated room headings and prioritize a substantially taller live conversation area while preserving the existing Metafxclub visual system and meeting behavior.

## Implementation evidence

- Screenshot: `artifacts/design-qa/ai-chat-expanded-1904x893.png`
- Local preview: `http://127.0.0.1:4191/frontend/index.html`
- Viewport: 1904 × 893 CSS pixels
- Screenshot dimensions: 1904 × 893 pixels
- Density: 1×
- State: Mission center open, `ห้องแชต AI รวม` selected, Backend ready, latest real Session loaded with 5 messages.

## Comparison findings

- The visible outer dialogue banner was removed from the Mission center surface.
- The repeated `AI MEETING ROOM / ห้องแชต AI รวม` inner heading was removed.
- The room name now appears once, in the selected tab, with the Backend status badge retained.
- The transcript viewport increased from 220 px to 402 px at the matched viewport, an increase of 182 px (82.7%).
- Existing spacing, borders, colors, typography, left-side meeting controls, Session selector, chat composer, status chips, and approval disclosure remain aligned with the source product.
- No horizontal page overflow was observed at the 800 × 720 responsive check; the transcript uses the 320 px mobile/tablet floor.
- Mission and AI chat tabs still switch correctly, all 5 real Backend messages render, and browser console warnings/errors were empty.
- Full repository regression passed: 1,241/1,241 tests, 0 failures, 0 errors.

## Fix history

1. Removed the visible duplicate headings while retaining a visually hidden live status region for accessibility and Backend feedback.
2. Reclaimed the removed header rows for the workspace.
3. Increased the transcript to a responsive 340–440 px desktop target and kept lower decision/proposal content scrollable rather than shrinking the conversation.
4. Added responsive transcript floors for widths below 900 px and 640 px.

## Final result

passed

# Design QA — ห้องทดลอง EA อัตโนมัติ

## Source truth

- Reference: `artifacts/design-qa/reference-ea-optimization-lab-1904x893.png`
- Requested change: turn the existing empty EA Lab shell into an EA-only MT4/MT5 optimization workflow with source inspection, explicit Input ranges, case-by-case rounds, and truthful result analysis.
- Combined comparison: `artifacts/design-qa/ea-optimization-lab-comparison-1904x893.png`

## Implementation evidence

- Initial-state screenshot: `artifacts/design-qa/ea-optimization-lab-empty-1904x893.png`
- Populated workflow screenshot: `artifacts/design-qa/ea-optimization-lab-functional-1904x893.png`
- Local preview: `http://127.0.0.1:4191/frontend/index.html`
- Matched viewport: 1904 × 893 CSS pixels, density 1×.
- Responsive checks: 900 × 800 and 520 × 800 CSS pixels.
- State: EA Lab open; initial screenshot has no selected EA. Functional pass used `SampleOptimizationEA.mq4` plus `SampleOptimizationEA.set`, MT4, XAUUSD, H1, 2024-01-01 through 2025-12-31, and three optimization rounds.

## Comparison findings

- Existing modal dimensions, left equipment rail, four-tab navigation, square borders, cyan/amber status language, dark palette, and dense desktop hierarchy remain aligned with the source product.
- The previously empty main area now exposes four clear steps: select EA, inspect Inputs/ranges, build a multi-round plan, and read verified results.
- File import is explicit and truthful: `.mq4/.mq5` source can be inspected in the browser; `.ex4/.ex5` remains opaque and requires source or `.set`; local browser files are not presented as Backend-registered artifacts.
- The QA fixture produced six Inputs, five optimizable Inputs, 896 combinations, categorical bool/Mode values, and a fixed non-optimizable `sinput`.
- MT4/MT5, file extension, detected Terminal, and Backend Adapter readiness are checked separately. The real Run control remains disabled because no verified Strategy Tester adapter is connected.
- Draft Plan saved only in the browser Session and did not create a Mission or claim a Terminal run.
- The Report tab showed no fabricated Profit, Drawdown, Pass, Candidate, Current Bands, or Next Parameter Plan data.
- Switching tabs resets the inner workspace to its heading. At 900 px the rail stacks above the workspace; at 520 px the tabs remain horizontally scrollable without overlapping the content.
- Browser console warnings/errors: none.
- Full repository regression: 1,255/1,255 tests passed.

## Interaction checks

1. Opened the EA Lab from the room hotspot.
2. Uploaded one `.mq4` file and one `.set` file through the real file chooser.
3. Selected an MT4 Terminal candidate, entered XAUUSD, and moved through Inputs and round planning.
4. Verified numeric Start/Step/Stop, categorical Mode/bool handling, and the one-million-combination fail-closed guard.
5. Saved a three-round Draft Plan and confirmed the real Optimization action stays disabled.
6. Opened the Report tab and confirmed missing Backend evidence remains visibly missing.

## Final result

passed
