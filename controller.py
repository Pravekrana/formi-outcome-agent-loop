"""HTTP-only outcome controller. State is a compact, transactional SQLite audit store."""
import argparse
import copy
import json
import math
import os
import sqlite3
import time
import uuid
from collections import defaultdict
from datetime import datetime, timedelta

import httpx


def wilson(s, n, z=2.4):
    if not n:
        return (0.0, 1.0)
    p = s / n
    d = 1 + z*z/n
    c = (p + z*z/(2*n))/d
    h = z*math.sqrt(p*(1-p)/n + z*z/(4*n*n))/d
    return c-h, c+h


class AmbiguousWrite(Exception):
    """The server may have committed a write before the connection failed."""


class Store:
    def __init__(self, path):
        os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
        self.db = sqlite3.connect(path)
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.execute('PRAGMA synchronous=FULL')
        self.db.executescript('''
        CREATE TABLE IF NOT EXISTS checkpoint(k TEXT PRIMARY KEY, v TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS stats(
          workflow TEXT, day TEXT, version INTEGER, cohort TEXT, dimension TEXT, option TEXT,
          dials INTEGER, connected INTEGER, engaged INTEGER, hallucinations INTEGER,
          PRIMARY KEY(workflow,day,version,cohort,dimension,option));
        CREATE INDEX IF NOT EXISTS stats_lookup ON stats(workflow,day,dimension,option);
        CREATE TABLE IF NOT EXISTS actions(
          proposal_id TEXT PRIMARY KEY, workflow TEXT, created_ts TEXT, base_version INTEGER,
          kind TEXT, status TEXT, approval_id TEXT, body TEXT, response TEXT,
          applied_ts TEXT, baseline TEXT, followup TEXT);
        CREATE INDEX IF NOT EXISTS actions_workflow ON actions(workflow,status);
        CREATE TABLE IF NOT EXISTS changes(
          event_id INTEGER PRIMARY KEY, workflow TEXT, ts TEXT, version INTEGER, actor TEXT,
          proposal_id TEXT, approval_id TEXT, changed_dims TEXT);
        CREATE TABLE IF NOT EXISTS observations(
          id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, workflow TEXT, type TEXT, detail TEXT);
        CREATE TABLE IF NOT EXISTS ingest_metrics(
          chunk INTEGER PRIMARY KEY, calls INTEGER, elapsed_s REAL);
        ''')
        self.db.commit()

    def get(self, k, default=None):
        row = self.db.execute('SELECT v FROM checkpoint WHERE k=?', (k,)).fetchone()
        return row[0] if row else default

    def put(self, k, v):
        self.db.execute('INSERT OR REPLACE INTO checkpoint VALUES (?,?)', (k,str(v)))
        self.db.commit()

    def observe(self, ts, wf, typ, detail):
        self.db.execute('INSERT INTO observations(ts,workflow,type,detail) VALUES (?,?,?,?)',
                        (ts,wf,typ,json.dumps(detail,sort_keys=True)))
        self.db.commit()

    def ingest(self, client, chunk):
        # A chunk is the recovery unit. Aggregate in memory with bounded cardinality.
        if chunk <= int(self.get('chunk','-1')):
            return 0
        started = time.perf_counter()
        agg = defaultdict(lambda: [0,0,0,0])
        changes = []
        calls = 0
        with client.stream('GET', f'/events/chunks/{chunk}') as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if not line:
                    continue
                e = json.loads(line)
                if e['type'] == 'call':
                    calls += 1
                    day = e['ts'][:10]
                    wf = e['workflow_id']
                    cohort = e.get('cohort_id','default')
                    ver = e.get('config_version',0)
                    variants = e.get('variant',{})
                    for dim in ('caller_id','welcome_message','voice','prompt_version'):
                        opt = variants.get(dim)
                        if opt is None:
                            continue
                        a = agg[(wf,day,ver,cohort,dim,opt)]
                        a[0] += 1
                        a[1] += bool(e['connected'])
                        a[2] += bool(e['engaged'])
                        a[3] += bool((e.get('qa') or {}).get('hallucination_flag'))
                elif e['type'] == 'config_changed':
                    changes.append((e['event_id'],e['workflow_id'],e['ts'],e['version'],
                                    e['actor'],e.get('proposal_id'),e.get('approval_id'),
                                    json.dumps(e.get('changed_dims',[]))))
        with self.db:
            self.db.executemany('''INSERT INTO stats VALUES (?,?,?,?,?,?,?,?,?,?)
              ON CONFLICT(workflow,day,version,cohort,dimension,option) DO UPDATE SET
              dials=dials+excluded.dials, connected=connected+excluded.connected,
              engaged=engaged+excluded.engaged, hallucinations=hallucinations+excluded.hallucinations''',
              [(*k,*v) for k,v in agg.items()])
            self.db.executemany('INSERT OR IGNORE INTO changes VALUES (?,?,?,?,?,?,?,?)',changes)
            self.db.execute('INSERT OR REPLACE INTO ingest_metrics VALUES (?,?,?)',
                            (chunk,calls,time.perf_counter()-started))
            self.db.execute('INSERT OR REPLACE INTO checkpoint VALUES (?,?)',('chunk',str(chunk)))
        return calls

    def version_rows(self,wf,dim,version):
        return self.db.execute('''SELECT option,SUM(dials),SUM(connected),SUM(engaged),SUM(hallucinations)
          FROM stats WHERE workflow=? AND dimension=? AND version=? GROUP BY option''',
          (wf,dim,version)).fetchall()

    def rows(self,wf,dim,days=2):
        return self.db.execute('''SELECT option,SUM(dials),SUM(connected),SUM(engaged),SUM(hallucinations)
          FROM stats WHERE workflow=? AND dimension=? AND day >=
          (SELECT COALESCE(MAX(day),'') FROM stats WHERE workflow=?)
          GROUP BY option''',(wf,dim,wf)).fetchall() if days == 0 else self.db.execute('''
          SELECT option,SUM(dials),SUM(connected),SUM(engaged),SUM(hallucinations)
          FROM stats WHERE workflow=? AND dimension=? AND day >=
          date((SELECT MAX(day) FROM stats WHERE workflow=?), ?)
          GROUP BY option''',(wf,dim,wf,f'-{days-1} day')).fetchall()

    def allrows(self,wf,dim):
        return self.db.execute('''SELECT option,SUM(dials),SUM(connected),SUM(engaged),SUM(hallucinations)
          FROM stats WHERE workflow=? AND dimension=? GROUP BY option''',(wf,dim)).fetchall()


class Controller:
    def __init__(self,url,path):
        self.c = httpx.Client(base_url=url, timeout=120)
        self.s = Store(path)
        self.workflows = {w['workflow_id']:w for w in self.c.get('/workflows').json()}

    def request(self,method,path,body=None):
        for i in range(4):
            try:
                r=self.c.request(method,path,json=body)
                if r.status_code >= 500:
                    if method != 'GET':
                        raise AmbiguousWrite(f'{method} {path}: HTTP {r.status_code}')
                    time.sleep(min(2**i,8)); continue
                return r
            except (httpx.TimeoutException,httpx.TransportError):
                if method != 'GET':
                    raise AmbiguousWrite(f'{method} {path}: response lost')
                time.sleep(min(2**i,8))
        raise RuntimeError(f'HTTP unavailable: {method} {path}')

    def backlog(self):
        after=int(self.s.get('chunk','-1'))
        # List only metadata. The first boot includes history; subsequent boots fetch only new chunks.
        for kind in ('history','events'):
            listing=self.request('GET',f'/events/chunks?kind={kind}&after={after}').json()
            for ch in listing:
                n=ch['chunk']
                if n>after:
                    self.s.ingest(self.c,n)
                    after=n

    def reconcile(self,ts):
        for pid,wf,kind,status,aid,body in self.s.db.execute('''SELECT proposal_id,workflow,kind,status,approval_id,body
            FROM actions WHERE status IN ('intent','pending','approved','applying')''').fetchall():
            body=json.loads(body)
            if status=='intent':
                if kind=='auto':
                    current=self.request('GET',f'/workflows/{wf}/config').json()
                    if current['version']>body['base_version']:
                        history=self.request('GET',f'/workflows/{wf}/config/history').json()
                        ours=any(h.get('proposal_id')==pid and h.get('actor')=='controller_auto'
                                 for h in history)
                        self.s.db.execute('UPDATE actions SET status=?,applied_ts=? WHERE proposal_id=?',
                                          ('applied' if ours else 'stale',ts if ours else None,pid))
                        self.s.db.commit()
                        continue
                    try:
                        r=self.request('PUT',f'/workflows/{wf}/config',body)
                    except AmbiguousWrite:
                        continue
                    new='applied' if r.is_success else ('stale' if r.status_code==409 else 'failed')
                    self._record(pid,new,r,ts if new=='applied' else None)
                    continue
                approvals=self.request('GET',f'/approvals?workflow_id={wf}').json()
                match=next((a for a in approvals if a.get('proposal_id')==pid),None)
                if match:
                    aid=match['approval_id']
                    self.s.db.execute('UPDATE actions SET status=?,approval_id=?,response=? WHERE proposal_id=?',
                                      ('pending',aid,json.dumps(match),pid)); self.s.db.commit()
                    status='pending'
                else:
                    try:
                        r=self.request('POST','/approvals',body)
                    except AmbiguousWrite:
                        continue
                if not match and r.is_success:
                    aid=r.json()['approval_id']
                    self.s.db.execute('UPDATE actions SET status=?,approval_id=?,response=? WHERE proposal_id=?',
                                      ('pending',aid,r.text,pid)); self.s.db.commit()
                elif not match and r.status_code==409:
                    approvals=self.request('GET',f'/approvals?workflow_id={wf}').json()
                    match=next((a for a in approvals if a.get('proposal_id')==pid),None)
                    if match:
                        aid=match['approval_id']
                        self.s.db.execute('UPDATE actions SET status=?,approval_id=?,response=? WHERE proposal_id=?',
                                          ('pending',aid,json.dumps(match),pid)); self.s.db.commit()
                    else:
                        self._record(pid,'stale',r)
                        continue
                elif not match:
                    self._record(pid,'failed',r); continue
            if aid:
                ap=self.request('GET',f'/approvals/{aid}').json()
                status=ap['status']
                if status in ('rejected','expired','lapsed'):
                    self.s.db.execute('UPDATE actions SET status=?,response=? WHERE proposal_id=?',
                                      (status,json.dumps(ap),pid)); self.s.db.commit(); continue
                if status=='applied':
                    self.s.db.execute('UPDATE actions SET status=?,applied_ts=? WHERE proposal_id=?',
                                      ('applied',ts,pid)); self.s.db.commit(); continue
                if status=='approved':
                    cur=self.request('GET',f'/workflows/{wf}/config').json()
                    if cur['version']!=body['base_version']:
                        self.s.db.execute('UPDATE actions SET status=? WHERE proposal_id=?',('stale',pid)); self.s.db.commit(); continue
                    self.s.db.execute('UPDATE actions SET status=? WHERE proposal_id=?',('applying',pid)); self.s.db.commit()
                    try:
                        r=self.request('POST',f'/workflows/{wf}/apply',{'approval_id':aid})
                    except AmbiguousWrite:
                        continue
                    if r.is_success:
                        self._record(pid,'applied',r,ts)
                    elif r.status_code in (409,410):
                        self._record(pid,'stale',r)
                    else:
                        self._record(pid,'failed',r)

    def _record(self,pid,status,r,ts=None):
        self.s.db.execute('UPDATE actions SET status=?,response=?,applied_ts=? WHERE proposal_id=?',
                          (status,r.text,ts,pid)); self.s.db.commit()

    def monitor(self):
        """Persist observed outcomes for each applied change; never infer from hidden truth."""
        actions=self.s.db.execute("SELECT proposal_id,workflow,base_version FROM actions WHERE status='applied'").fetchall()
        for pid,wf,base in actions:
            changed=self.s.db.execute('SELECT version FROM changes WHERE proposal_id=?',(pid,)).fetchone()
            if not changed:
                continue
            def totals(version):
                return self.s.db.execute('''SELECT COALESCE(SUM(dials),0),COALESCE(SUM(connected),0),
                  COALESCE(SUM(engaged),0),COALESCE(SUM(hallucinations),0) FROM stats
                  WHERE workflow=? AND version=? AND dimension='prompt_version' ''',
                  (wf,version)).fetchone()
            before,after=totals(base),totals(changed[0])
            if after[0]:
                self.s.db.execute('UPDATE actions SET followup=? WHERE proposal_id=?',
                                  (json.dumps({'base_version':base,'new_version':changed[0],
                                               'before':before,'after':after}),pid))
        self.s.db.commit()

    def approval_window(self,wf,ts):
        policy=self.workflows[wf]['governance']
        hour=int(ts[11:13])
        start,end=policy['approver_hours']
        if not max(11,start)<=hour<end-1:
            return False
        cutoff=(datetime.fromisoformat(ts)-timedelta(hours=24)).isoformat()
        count=self.s.db.execute('''SELECT COUNT(*) FROM actions WHERE workflow=? AND kind='approval'
          AND created_ts>=?''',(wf,cutoff)).fetchone()[0]
        return count<min(2,policy['max_requests_per_24h'])

    def propose(self,wf,ts,cfg,summary,diff,rationale,impact=0.2,evidence=None,original_cfg=None):
        cur=self.request('GET',f'/workflows/{wf}/config').json()
        if original_cfg is not None and cur['config']!=original_cfg:
            return
        if cfg==cur['config']:
            return
        existing=self.s.db.execute("SELECT 1 FROM actions WHERE workflow=? AND status IN ('intent','pending','approved','applying')",(wf,)).fetchone()
        if existing:
            return
        policy=self.workflows[wf]['governance']
        pid=str(uuid.uuid4())
        base={'proposal_id':pid,'workflow_id':wf,'base_version':cur['version'],'proposed_config':cfg,
              'rationale':rationale}
        dim=next(iter(diff))
        auto=policy.get('auto_apply',{})
        # Only the simulator policy determines whether auto apply is attempted.
        eligible=auto.get('enabled') and dim in auto.get('allowed_dims',[]) and dim in ('caller_id','schedule')
        kind='auto' if eligible else 'approval'
        if not eligible:
            if not self.approval_window(wf,ts):
                return
            base.update(change_summary=summary,diff=diff,
                        affected_leads=self.workflows[wf]['daily_batch']['size'],
                        dry_run={'method':'observed aggregate comparison','note':'No causal replay; conservative estimate'},
                        impact_score=min(max(impact,0),1))
            if evidence:
                base['evidence']=evidence
        self.s.db.execute('''INSERT INTO actions(proposal_id,workflow,created_ts,base_version,kind,status,body,baseline)
          VALUES (?,?,?,?,?,?,?,?)''',(pid,wf,ts,cur['version'],kind,'intent',json.dumps(base),
                                       json.dumps(self.s.allrows(wf,dim))))
        self.s.db.commit()
        self.reconcile(ts)

    def decide(self,ts):
        for wf,w in self.workflows.items():
            cur=self.request('GET',f'/workflows/{wf}/config').json()
            cfg=cur['config']
            if self.s.db.execute("SELECT 1 FROM actions WHERE workflow=? AND status IN ('intent','pending','approved','applying')",(wf,)).fetchone():
                continue
            alloc=cfg['allocations']['default']
            objective=w['objective']['primary']
            guard=w['objective']['guardrail']
            # Caller ID pickup: compare each arm to the best with conservative Wilson bounds.
            rows=self.s.rows(wf,'caller_id',2)
            eligible=[r for r in rows if r[1]>=150]
            if len(eligible)>=2:
                best=max(eligible,key=lambda r:r[2]/r[1])
                worst=min(eligible,key=lambda r:r[2]/r[1])
                engagement_limit=guard.get('engagement_rate_max_drop',0.02)
                guardrail_ok=(best[2]>=100 and worst[2]>=100 and
                    wilson(best[3],best[2])[1] >= wilson(worst[3],worst[2])[0]-engagement_limit)
                if (guardrail_ok and best[0]!=worst[0] and
                    wilson(best[2],best[1],3.0)[0] > wilson(worst[2],worst[1],3.0)[1]+0.005):
                    old=alloc['caller_id']; new=dict(old)
                    auto_policy=w['governance']['auto_apply']
                    policy_shift=(auto_policy['max_shift'] if auto_policy['enabled'] and
                                  'caller_id' in auto_policy['allowed_dims'] else 0.2)
                    shift=min(0.2,policy_shift,new.get(worst[0],0))
                    if shift>=0.02:
                        new[worst[0]]-=shift; new[best[0]]=new.get(best[0],0)+shift
                        proposed=copy.deepcopy(cfg); proposed['allocations']['default']['caller_id']=new
                        self.propose(wf,ts,proposed,'Rotate traffic from degraded caller ID',
                                     {'caller_id':{'old':old,'new':new}},
                                     f'Pickup Wilson intervals separated; {worst[0]} {worst[2]}/{worst[1]}, {best[0]} {best[2]}/{best[1]}.',
                                     impact=min(1.0,shift*(best[2]/best[1]-worst[2]/worst[1])),
                                     original_cfg=cfg)
                        continue
            # Prompt incident: detector is imperfect; require a population and a 2-day baseline.
            prompt=cfg['prompt_version']; recent={r[0]:r for r in self.s.rows(wf,'prompt_version',1)}.get(prompt)
            overall={r[0]:r for r in self.s.allrows(wf,'prompt_version')}.get(prompt)
            if recent and overall and recent[2]>=80:
                old_conn=max(0,overall[2]-recent[2]); old_bad=max(0,overall[4]-recent[4])
                old_rate=old_bad/old_conn if old_conn>=80 else 0.01
                lower=wilson(recent[4],recent[2],2.4)[0]
                if lower>max(0.025,old_rate+0.012):
                    self.s.observe(ts,wf,'hallucination_incident',{'recent':recent,'prior_rate':old_rate})
                    incident_key=f'incident:{wf}:{prompt}'
                    if self.s.get(incident_key)==ts[:10] or not self.approval_window(wf,ts):
                        continue
                    credits=self.request('GET','/sim/state').json().get('credits_remaining',0)
                    if credits<8: continue
                    self.s.put(incident_key,ts[:10])
                    try:
                        suggestion=self.request('POST','/llm/suggest-fixes',
                                                {'workflow_id':wf,'problem':'High hallucination rate on current prompt'})
                    except AmbiguousWrite:
                        continue
                    if not suggestion.is_success: continue
                    data=suggestion.json()
                    candidates=data if isinstance(data,list) else data.get('suggestions',[])
                    historical={r[0]:r for r in self.s.allrows(wf,'prompt_version')}
                    def prior_evidence(candidate):
                        option=candidate if isinstance(candidate,str) else candidate.get('prompt_version')
                        row=historical.get(option)
                        return (row[2],row[3]/row[2]) if row and row[2] else (0,0)
                    candidates=sorted(candidates,key=prior_evidence,reverse=True)
                    for candidate in candidates[:3]:
                        option=candidate if isinstance(candidate,str) else candidate.get('prompt_version')
                        if not option or option==prompt or option not in w['options']['prompt_version']: continue
                        try:
                            validation=self.request('POST','/validation/runs',
                                                    {'workflow_id':wf,'prompt_version':option,'n':500})
                        except AmbiguousWrite:
                            break
                        if not validation.is_success: continue
                        result=validation.json()
                        if result.get('pass_rate',0)<w['governance'].get('min_validation_pass_rate',1): continue
                        proposed=copy.deepcopy(cfg); proposed['prompt_version']=option
                        self.propose(wf,ts,proposed,'Validated response to hallucination incident',
                                     {'prompt_version':{'old':prompt,'new':option}},
                                     f'Observed detector flags {recent[4]}/{recent[2]} connected calls; validation {result["pass_rate"]:.3f}.',
                                     evidence={'validation_run_id':result['validation_run_id']},original_cfg=cfg)
                        break
            # Safe experimentation only after enough observed traffic. Keep a control arm.
            if objective=='engagement_rate' and ts[11:13]=='11':
                for dim in ('welcome_message','voice'):
                    options=w['options'][dim]
                    observed={r[0]:r for r in self.s.version_rows(wf,dim,cur['version'])}
                    current=alloc[dim]
                    if len(current)==1 and sum(r[2] for r in self.s.allrows(wf,dim))>=300:
                        alt=next((o for o in options if o not in current),None)
                        if alt:
                            proposed=copy.deepcopy(cfg)
                            main=next(iter(current))
                            proposed['allocations']['default'][dim]={main:0.8,alt:0.2}
                            self.propose(wf,ts,proposed,f'Explore {dim} with control retained',
                                         {dim:{'old':current,'new':proposed['allocations']['default'][dim]}},
                                         'Randomized 80/20 experiment after 300 connected calls.',original_cfg=cfg)
                            break
                    elif len(current)>1:
                        arms=[observed.get(o) for o in current]
                        if all(a and a[2]>=200 for a in arms):
                            best=max(arms,key=lambda a:a[3]/a[2]); worst=min(arms,key=lambda a:a[3]/a[2])
                            pickup_limit=guard.get('pickup_rate_max_drop',0.02)
                            pickup_ok=(wilson(best[2],best[1],3.3)[1] >=
                                       wilson(worst[2],worst[1],3.3)[0]-pickup_limit)
                            if (pickup_ok and wilson(best[3],best[2],3.3)[0]>
                                wilson(worst[3],worst[2],3.3)[1]+0.01):
                                proposed=copy.deepcopy(cfg)
                                proposed['allocations']['default'][dim]={best[0]:0.9,worst[0]:0.1}
                                self.propose(wf,ts,proposed,f'Promote measured {dim} winner',
                                             {dim:{'old':current,'new':proposed['allocations']['default'][dim]}},
                                             f'Engagement conservative intervals separated: {best[3]}/{best[2]} vs {worst[3]}/{worst[2]}.',
                                             original_cfg=cfg)
                                break

    def run(self):
        while True:
            state=self.request('GET','/sim/state').json()
            self.backlog()
            self.reconcile(state['ts'])
            if state['finished']:
                break
            if state['ts'][11:16]=='20:00':
                self.monitor()
            if state['sim_minute']%60==0:
                self.decide(state['ts'])
            try:
                advanced=self.request('POST','/sim/advance',{'minutes':60})
                if advanced.status_code==409:
                    if self.request('GET','/sim/state').json()['finished']:
                        break
                    continue
                advanced.raise_for_status()
            except AmbiguousWrite:
                # Unknown write result: state and event backlog are authoritative on retry.
                continue
        self.backlog()
        self.reconcile(self.request('GET','/sim/state').json()['ts'])
        self.monitor()


def main():
    p=argparse.ArgumentParser()
    p.add_argument('url')
    p.add_argument('--db',default='state/controller.sqlite3')
    a=p.parse_args()
    Controller(a.url,a.db).run()

if __name__=='__main__':
    main()
