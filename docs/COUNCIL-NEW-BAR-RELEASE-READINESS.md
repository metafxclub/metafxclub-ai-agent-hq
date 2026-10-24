# Council new-bar scheduling and gateway projection

This release keeps automatic Council analysis restricted to the newly observed
closed bar. If quota, a worker, the selected stream or the immutable snapshot is
not ready within the admission window, that bar is recorded as skipped. A later
quota recovery, a restart or a timeframe change does not replay the missed bar.

## Changes

- The three Council workers reserve three distinct queued specialist missions
  before readiness checks. A reservation does not consume authorization, model
  budget or an execution lease. The durable claim remains the execution gate.
  Reservations are released by the owning worker in `finally`, including STOP,
  cancellation and exceptions. They are process-local and are not restart work.
- Automatic votes check current-bar identity, startup identity, the bounded
  admission window and the EA snapshot-age limit before claim and again before
  starting the model. Already started work may finish, but its result cannot
  bypass the normal round deadline or execution validation.
- Automatic transient failures are final for that bar. The bounded provider-429
  retry exists only for an eligible manually requested round with an explicitly
  issued second-run budget and the same immutable snapshot. It never grants an
  automatic backlog retry.
- History distinguishes an entirely unstarted skipped round from a partially
  analyzed round. Broker outcomes preserve the EA's confirmed evidence,
  64-bit ticket identifiers and unknown recovered slippage.
- MT5 v1.07 status includes initialization diagnostics and its price-risk cost
  basis. These are read-only status fields; they cannot be sent as trade-command
  overrides. Broker permission, risk, duplicate-command and evidence guards
  remain authoritative.
- Standalone Council status polling builds only the Council read model. It uses
  the same coherent gateway/selection/chart capture as the equipment report,
  retries a generation mismatch at most once and fails closed if the selection
  still differs. It does not reuse a cached snapshot or refresh old timestamps.
  Exact mission lookup copies only the selected record from the shared immutable
  store instead of deep-copying the full archive.

## Focused regression coverage

The tests include a deterministic reproduction using the actual worker loop:
three workers pause before claim. The old loop selects one specialist three
times; the reservation loop selects all three specialists. Further tests cover
wrong-owner release, capacity, STOP, exception, cancelled/stale selection,
authorization and lease checks, duplicate completion, no-backfill on restart or
quota recovery, timeframe changes, late results, snapshot-age expiry, and the
read-only status generation race.

Relevant test modules include `test_council_dispatch_reservations`,
`test_council_newbar_worker`, `test_council_newbar_admission`,
`test_council_new_bar_policy_contracts`, `test_council_status_projection`,
`test_council_request_snapshot_reuse`, `test_council_provider_rate_limit`,
`test_council_scheduler_recovery`, `test_council_execution_history_truth`, and
the Council/gateway integration modules in `tests/`.

## Verification boundary

Backend regression verification uses an isolated temporary runtime and an audit
hook which rejects network access, child processes, production runtime/terminal
reads and writes outside that temporary directory. Inert Node harness tests for
EA logic are verified separately. Native EA compile evidence is documented with
the MT4/MT5 artifacts; compilation and simulated logic tests do not prove a live
broker execution.

No existing terminal, chart, order, account, EA input or live Backend is changed
by these tests. The worker fix removes a reproduced source of starvation; it is
not a guarantee that a slow machine or external AI service always completes a
round within its window. The strict deadline still skips work when it cannot
start in time. An observed earlier delay before child creation was not fully
attributed, so this release does not claim that every source of latency is fixed.
