"""Kill a running controller and restart it against the same simulator and SQLite DB.

Run only with a fresh simulator; this script creates one ignored run directory.
"""
import argparse
import json
import sqlite3
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

import httpx


def wait_until(predicate, seconds=180):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        try:
            result = predicate()
            if result:
                return result
        except (httpx.TransportError, httpx.HTTPStatusError):
            pass
        time.sleep(0.05)
    raise TimeoutError('condition not reached')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', default='http://127.0.0.1:8700')
    parser.add_argument('--scenario', default='scenarios/public_01_dev.yaml')
    parser.add_argument('--run-dir', default='runs/recovery_demo')
    parser.add_argument('--db', default='state/recovery_demo.sqlite3')
    args = parser.parse_args()
    run_dir, db_path = Path(args.run_dir), Path(args.db)
    if run_dir.exists() or db_path.exists():
        raise SystemExit('Use fresh --run-dir and --db paths; this script never deletes existing evidence.')
    run_dir.parent.mkdir(parents=True, exist_ok=True)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    client = httpx.Client(base_url=args.url, timeout=10)
    parsed = urlparse(args.url)
    if parsed.hostname not in ('127.0.0.1', 'localhost') or not parsed.port:
        raise SystemExit('--url must name a loopback host and explicit port')
    server = subprocess.Popen([sys.executable, '-m', 'sim', 'serve', '--scenario',
                               args.scenario, '--run-dir', str(run_dir), '--port', str(parsed.port)],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    controller = None
    try:
        wait_until(lambda: client.get('/health').status_code == 200)
        command = [sys.executable, 'controller.py', args.url, '--db', str(db_path)]
        controller = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
                                      text=True)
        def progressed():
            state = client.get('/sim/state').json()
            if controller.poll() is not None:
                raise RuntimeError('controller exited before kill: ' + controller.stderr.read()[-1500:])
            pending = [a['proposal_id'] for a in client.get('/approvals',
                       params={'status': 'pending'}).json()]
            return (state, pending) if pending else None
        before, pending_before = wait_until(progressed)
        controller.kill()
        controller.wait(timeout=30)
        with sqlite3.connect(db_path) as db:
            checkpoint_before = db.execute("SELECT v FROM checkpoint WHERE k='chunk'").fetchone()[0]
        controller = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
                                      text=True)
        try:
            stdout, stderr = controller.communicate(timeout=600)
        except subprocess.TimeoutExpired:
            controller.kill()
            raise
        after = client.get('/sim/state').json()
        with sqlite3.connect(db_path) as db:
            checkpoint_after = db.execute("SELECT v FROM checkpoint WHERE k='chunk'").fetchone()[0]
            actions = db.execute('SELECT proposal_id,status FROM actions').fetchall()
            duplicated = db.execute('''SELECT proposal_id,COUNT(*) FROM actions
                                      GROUP BY proposal_id HAVING COUNT(*)>1''').fetchall()
        approvals = client.get('/approvals').json()
        proposal_ids = [a['proposal_id'] for a in approvals]
        result = {'killed_at_minute': before['sim_minute'], 'pending_at_kill': pending_before,
                  'checkpoint_before': checkpoint_before,
                  'checkpoint_after': checkpoint_after, 'finished': after['finished'],
                  'controller_exit': controller.returncode, 'actions': len(actions),
                  'duplicate_local_ids': duplicated,
                  'duplicate_remote_ids': len(proposal_ids)-len(set(proposal_ids)),
                  'stderr_tail': stderr[-500:]}
        print(json.dumps(result, indent=2))
        if not after['finished'] or controller.returncode or duplicated or result['duplicate_remote_ids']:
            raise SystemExit(1)
    finally:
        if controller and controller.poll() is None:
            controller.kill()
            controller.wait(timeout=30)
        server.terminate()
        server.wait(timeout=30)


if __name__ == '__main__':
    main()
