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
