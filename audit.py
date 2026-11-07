"""Show locally persisted authorization and post-change evidence for a workflow."""
import argparse
import json
import sqlite3


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('workflow')
    parser.add_argument('--db', default='state/controller.sqlite3')
    args = parser.parse_args()
    db = sqlite3.connect(args.db)
    db.row_factory = sqlite3.Row
    rows = db.execute('''
        SELECT a.created_ts, a.proposal_id, a.kind, a.status, a.approval_id,
               a.body, a.response, a.applied_ts, a.followup,
               c.ts AS event_ts, c.actor, c.version, c.changed_dims
        FROM actions a LEFT JOIN changes c ON c.proposal_id = a.proposal_id
        WHERE a.workflow = ? ORDER BY a.created_ts, a.proposal_id
    ''', (args.workflow,)).fetchall()
    for row in rows:
        item = dict(row)
        body = json.loads(item.pop('body'))
        item['rationale'] = body.get('rationale')
        item['change_summary'] = body.get('change_summary')
        item['diff'] = body.get('diff')
        item['evidence'] = body.get('evidence')
        if item['followup']:
            item['followup'] = json.loads(item['followup'])
        print(json.dumps(item, sort_keys=True))
    for row in db.execute('''SELECT ts, actor, version, changed_dims FROM changes
                            WHERE workflow=? AND actor='supervisor' ORDER BY ts''',
                          (args.workflow,)):
        print(json.dumps({'supervisor_change': dict(row)}, sort_keys=True))


if __name__ == '__main__':
    main()
