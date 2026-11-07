import json

import pytest

from controller import Controller, Store, wilson


class Chunk:
    def __init__(self, lines):
        self.lines = lines

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def raise_for_status(self):
        pass

    def iter_lines(self):
        yield from self.lines


class Client:
    def __init__(self, lines):
        self.lines = lines

    def stream(self, method, path):
        assert method == 'GET'
        assert path == '/events/chunks/0'
        return Chunk(self.lines)


def call():
    return json.dumps({
        'type': 'call', 'ts': '2027-01-04T11:00:00+05:30',
        'workflow_id': 'wf', 'config_version': 1, 'cohort_id': 'default',
        'variant': {'voice': 'V1', 'caller_id': 'D1',
                    'welcome_message': 'W1', 'prompt_version': 'P1'},
        'connected': True, 'engaged': False, 'qa': None,
    })


def test_chunk_checkpoint_prevents_double_count(tmp_path):
    store = Store(str(tmp_path / 'controller.db'))
    client = Client([call()])
    assert store.ingest(client, 0) == 1
    assert store.ingest(client, 0) == 0
    assert store.get('chunk') == '0'
    assert store.db.execute("SELECT SUM(dials) FROM stats WHERE dimension='voice'").fetchone()[0] == 1


def test_malformed_chunk_does_not_advance_checkpoint(tmp_path):
    store = Store(str(tmp_path / 'controller.db'))
    with pytest.raises(json.JSONDecodeError):
        store.ingest(Client([call(), '{broken']), 0)
    assert store.get('chunk') is None
    assert store.db.execute('SELECT COUNT(*) FROM stats').fetchone()[0] == 0


def test_approval_window_and_fatigue(tmp_path):
    controller = Controller.__new__(Controller)
    controller.s = Store(str(tmp_path / 'controller.db'))
    controller.workflows = {'wf': {'governance': {
        'approver_hours': [10, 19], 'max_requests_per_24h': 1}}}
    assert not controller.approval_window('wf', '2027-01-04T10:00:00+05:30')
    assert controller.approval_window('wf', '2027-01-04T11:00:00+05:30')
    controller.s.db.execute("INSERT INTO actions(proposal_id,workflow,created_ts,base_version,kind,status,body) VALUES ('p','wf','2027-01-04T11:00:00+05:30',1,'approval','pending','{}')")
    controller.s.db.commit()
    assert not controller.approval_window('wf', '2027-01-04T12:00:00+05:30')


def test_wilson_needs_population():
    assert wilson(1, 1)[0] < 0.2
    assert wilson(800, 1000)[0] > wilson(200, 1000)[1]
