# Audit example from the completed public_02b run

Database: ignored `state/mine02b.sqlite3`. This is an actual read-only query result from the local audit tables. The database predates the later `followup` column population logic, so the outcome counts come directly from `stats` joined to `changes`.

```sql
SELECT c.ts, c.workflow, c.version, c.actor, c.proposal_id,
       COALESCE(a.approval_id,''), SUM(s.dials), SUM(s.connected), SUM(s.engaged)
FROM changes c
LEFT JOIN actions a ON a.proposal_id=c.proposal_id
LEFT JOIN stats s ON s.workflow=c.workflow AND s.version=c.version
                 AND s.dimension='prompt_version'
WHERE c.workflow='ks_cancel' AND c.version IN (3,4)
GROUP BY c.event_id ORDER BY c.version;
```

```text
2027-01-04T12:00:00+05:30  ks_cancel  3  controller_approved  e59b3651-fb5a-42c0-b4d2-ac69418f07d1  apr_00004  10800  2505  1260
2027-01-06T15:00:00+05:30  ks_cancel  4  controller_auto      c03a4d90-aa8a-4cde-a481-e2a206c0a636             400    70    35
```

Version 3 had a named approval. Version 4 used policy-permitted auto apply during a caller-ID incident; its 400 dials yielded 70 pickups and 35 engagements before the next version. These counts describe what happened, without claiming that the version alone caused the difference. `python audit.py ks_cancel --db state/mine02b.sqlite3` prints each action's rationale and diff alongside the actor and approval ID.

The same command's actual prompt-repair record is:

```json
{"actor":"controller_approved","applied_ts":"2027-01-07T18:00:00+05:30","approval_id":"apr_00005","change_summary":"Validated response to hallucination incident","diff":{"prompt_version":{"new":"P3","old":"P2"}},"evidence":{"validation_run_id":"val_00002"},"proposal_id":"5f11eabb-125a-4b4d-a809-db1f8d8d077a","rationale":"Observed detector flags 15/325 connected calls; validation 0.992.","status":"applied","version":8}
```

It shows why the prompt changed, the validation evidence, the approval authorizing it, and the applied version. The official public_02 grade subsequently measured 70 hallucinated `ks_cancel` calls over the complete run versus 330 baseline; that is whole-run outcome evidence, not a version-isolated causal estimate.
