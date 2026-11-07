# Controller operations

## Run and recover

Use Python 3.11+ on Linux, `python -m pip install -r requirements.txt`, then `FORMI_DB=state/<run>.sqlite3 ./run.sh http://127.0.0.1:8700`. The database and WAL files belong in ignored `state/`; simulator files belong in ignored `runs/`. One database represents one simulator world. Restart with the same `FORMI_DB` and URL after a controller crash. Do not restart the simulator: its world is held in memory. Keep the SQLite files together during backup and do not copy a live database without SQLite's backup API.

The controller lists chunk metadata and ingests only numbers greater than its durable checkpoint. A chunk's aggregates, change events, ingest timing, and checkpoint commit in one transaction. A crash before commit replays the chunk. The proposal intent is committed before any HTTP write. On restart, an approval intent is reconciled by proposal ID, an apply is checked by approval status, and an auto apply is checked against config history before retrying. An ambiguous `/sim/advance` response causes a state and backlog reread.

## Observe

`python audit.py <workflow> --db state/<run>.sqlite3` shows the locally recorded rationale, approval ID, actor, changed dimensions, and observed followup. Inspect `checkpoint` for ingestion position, `ingest_metrics` for chunk throughput, `actions` for pending and terminal proposals, `changes` for supervisor edits, and `observations` for incident detections. The local audit store is the source of the controller's reasoning; official grading reports assess outcomes separately.

Page an operator for a persistent HTTP outage, ingestion lag over one simulated day, a pending approval approaching its expiry, an approved action approaching `apply_by`, or a hallucination spike with no validated option. A neutral experiment result, a routine rejection, or a normal overnight approval delay can wait for the next shift. On a 4xx response, inspect the recorded `response` in `actions`; stale versions require a fresh proposal and validation failures prohibit prompt changes.

## Boundaries

The simulator's 15-minute tick only advances through HTTP. This controller advances by one hour and checks incidents hourly, so incidents can be detected no faster than one simulated hour plus the evidence threshold. It does not change cadence, dialling windows, or capacity. It does not read hidden truth. Approval requests are restricted to the approver window beginning no earlier than 11:00 and to at most two per workflow in 24 hours. Caller-ID auto apply is attempted only where the workflow's live policy allows it, with a 0.2 maximum allocation shift per change.

The simulator's `/validation/runs` measures prompt safety, not engagement. The controller favors a previously observed suggestion when available, validates it, and then routes the prompt change through human approval. Monitor engagement and detector flags after application. If the post-change population is harmful, an operator should use the audit trail and governance endpoint to propose a validated rollback; automatic rollback is deferred.
