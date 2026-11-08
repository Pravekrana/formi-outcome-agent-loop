# Controller kill/restart recovery

Status: **passed one real kill/restart test** on Python 3.12.10, using `python recovery_demo.py --url http://127.0.0.1:8701` with fresh `runs/recovery_demo` and `state/recovery_demo.sqlite3`. The harness killed only the controller at simulated minute 720, then restarted it against the same live simulator and persisted SQLite database.

Observed JSON: `{"killed_at_minute":720,"checkpoint_before":"3","checkpoint_after":"104","finished":true,"controller_exit":0,"actions":4,"duplicate_local_ids":[],"duplicate_remote_ids":0,"stderr_tail":""}`. The official grader in `reports/recovery_grade.md` recorded four approved/applied changes, no conflicts, lapses, rejections, or harmful changes, and +1.7% aggregate conclusion-rate change versus baseline.

This demonstrates one real process kill with no duplicate local or remote proposal IDs observed. Chunk aggregates and checkpoint share a transaction; intents are committed before writes; on restart, approvals are looked up by proposal ID, apply status by approval ID, and auto applies by config history. The test does not exercise every possible crash boundary, ambiguous network response, or simultaneous-controller race; those remain for fault injection.

## Pending-approval crash point

The strengthened harness was run a second time with `python recovery_demo.py --url http://127.0.0.1:8703 --run-dir runs/recovery_pending --db state/recovery_pending.sqlite3`. It waited for a live `pending` approval before killing the controller. Observed result:

```json
{"killed_at_minute":660,"pending_at_kill":["78925c6c-8c22-467e-bc73-d44a54fe3343"],"checkpoint_before":"3","checkpoint_after":"104","finished":true,"controller_exit":0,"actions":5,"duplicate_local_ids":[],"duplicate_remote_ids":0,"stderr_tail":""}
```

The official `reports/recovery_pending_grade.md` recorded five requests, four approved/applied, one ordinary approver decline, no apply conflicts, lapses, expiry, or harmful changes, and +1.5% aggregate conclusion-rate change. The pending proposal was not submitted twice after restart. This is stronger evidence for approval-intent reconciliation, though it still does not exercise a dropped response at the exact write boundary.
