# Council scheduling: new closed bars only

The current policy is `new_closed_bar_only_no_backfill`. It replaces historical queue replay. The scheduler runs in the Backend independently of browser visibility. See [the Thai operator guide](council-new-bar-only-th.md).

## Admission and recovery

- A natural new closed-bar observation is admitted only when quota, runtime and snapshot-age checks pass. The identity remains terminal channel, broker symbol, timeframe and closed-bar time.
- The immutable capture may wait briefly for settling within its bounded admission window. Scheduler and Worker recheck validity before starting AI.
- A denied gate, failed admission, expired capture or missed trigger is recorded as skipped. It does not become deferred AI work and is not retried automatically later in the candle.
- Quota recovery during a candle waits for the next closed bar. Restart, re-enable and chart changes establish a baseline rather than replaying unstarted captures.
- Recovery may reattach an already-created parent for the same stream and bar. It does not create another round or order. Already-started work and genuine historical results remain evidence of what occurred.

## History and capacity

New admission allows only the current settling trigger; no historical backlog is accumulated for analysis. The existing pending-count fields remain compatible with older clients. Unstarted legacy captures are retired to skipped history, while completed and partially analyzed rounds retain their actual evidence.

If every automatic Specialist is skipped before process start, the parent and canonical history show skipped rather than an analyzed 0/3 result. Expired records retain the original timestamp and reason; they are never refreshed to regain eligibility.

Gap records use only actual closed-bar timestamps in the broker snapshot. Session breaks are not filled with invented bars. An unknown older interval is recorded separately when the bounded snapshot cannot establish it. Bangkok midnight resets daily counters without reviving skipped work.

`analysisStartPreflight` records age, the EA age limit, remaining seconds and reason. It does not authorize an order. Existing final price, age, stream, SL/TP, quota, position, command-identity and EA guards still apply.

## Validation

The per-bar automation, scheduler recovery, stream-switching, new-bar Worker and frontend history suites cover denied gates, mid-bar recovery, restart/re-enable, expiry, duplicate prevention and truthful skipped history. Tests run with live runtime, terminal and network access denied; fixture model execution does not send real orders.
