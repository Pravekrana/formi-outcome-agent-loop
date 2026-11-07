# Controller kill/restart recovery

Status: **not executed**. The terminal cannot access Python, so there is no real kill/restart measurement to claim. The existing corrected public_02 run finished in a previous desktop session, but that was not a deliberate process kill and restart test.

Once Python is available, start a fresh simulator and controller with a unique database, wait until at least one approval is pending, kill only the controller process, and restart `./run.sh` with the same `FORMI_DB`. Verify `/sim/state` reaches `finished`, that each chunk number is checkpointed once, that each proposal ID appears once in `/approvals`, and that each approved proposal changes config at most once. Save the before/after process IDs, simulator minute, checkpoint, approval IDs, and official grade here. Do not restart the simulator between controller processes.

The intended recovery logic is: chunk aggregates and checkpoint share a transaction; intents are committed before writes; on restart, approvals are looked up by proposal ID, apply status is looked up by approval ID, auto applies are compared to config history, and an ambiguous advance response is resolved by reading `/sim/state` and the chunk backlog. This is a design description, not test evidence.
