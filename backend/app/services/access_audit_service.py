from __future__ import annotations
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path


class AccessAuditService:
    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with self.db() as db:
            db.executescript('''
            CREATE TABLE IF NOT EXISTS access_events(
              id INTEGER PRIMARY KEY AUTOINCREMENT,timestamp TEXT NOT NULL,
              account TEXT NOT NULL,name TEXT NOT NULL,role TEXT NOT NULL,
              ip TEXT NOT NULL,path TEXT NOT NULL,method TEXT NOT NULL,status INTEGER NOT NULL,
              kind TEXT NOT NULL,visitor_id TEXT NOT NULL,user_agent TEXT NOT NULL);
            CREATE INDEX IF NOT EXISTS access_time ON access_events(timestamp DESC,id DESC);
            CREATE TABLE IF NOT EXISTS access_presence(
              visitor_id TEXT PRIMARY KEY,account TEXT NOT NULL,name TEXT NOT NULL,
              role TEXT NOT NULL,ip TEXT NOT NULL,path TEXT NOT NULL,last_seen TEXT NOT NULL);
            CREATE INDEX IF NOT EXISTS presence_time ON access_presence(last_seen);
            ''')

    @contextmanager
    def db(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def record(self, *, user=None, ip='', path='/', method='GET', status=200,
               kind='page_view', visitor_id='', user_agent=''):
        stamp = datetime.now(timezone.utc).isoformat(timespec='milliseconds')
        account, name, role = (user.account, user.name, user.role) if user else ('', '未登录访客', 'guest')
        # Do not retain query strings: URLs can contain reset tokens and other secrets.
        path = path.split('?')[0].split('#')[0][:300]
        with self.db() as db:
            if kind != 'heartbeat':
                db.execute('INSERT INTO access_events(timestamp,account,name,role,ip,path,method,status,kind,visitor_id,user_agent) VALUES(?,?,?,?,?,?,?,?,?,?,?)',
                           (stamp,account,name,role,ip[:64],path,method,status,kind,visitor_id[:80],user_agent[:300]))
            if visitor_id:
                db.execute('INSERT INTO access_presence VALUES(?,?,?,?,?,?,?) ON CONFLICT(visitor_id) DO UPDATE SET account=excluded.account,name=excluded.name,role=excluded.role,ip=excluded.ip,path=excluded.path,last_seen=excluded.last_seen',
                           (visitor_id[:80],account,name,role,ip[:64],path,stamp))

    def list(self, q='', kind='', page=1, size=30, role='', result='', since='', until=''):
        where, params = ['1=1'], []
        if q:
            where.append('(account LIKE ? OR name LIKE ? OR ip LIKE ? OR path LIKE ?)')
            params.extend(['%'+q+'%']*4)
        if kind:
            where.append('kind=?'); params.append(kind)
        if role:
            where.append('role=?'); params.append(role)
        if result:
            where.append('status>=400' if result=='failure' else 'status<400')
        if since:
            where.append('timestamp>=?'); params.append(since)
        if until:
            where.append('timestamp<=?'); params.append(until)
        clause = ' AND '.join(where)
        today = datetime.now(timezone(timedelta(hours=8))).replace(hour=0,minute=0,second=0,microsecond=0).astimezone(timezone.utc).isoformat(timespec='milliseconds')
        cutoff = (datetime.now(timezone.utc)-timedelta(seconds=90)).isoformat(timespec='milliseconds')
        with self.db() as db:
            total = db.execute(f'SELECT COUNT(*) FROM access_events WHERE {clause}',params).fetchone()[0]
            rows = [dict(r) for r in db.execute(f'SELECT * FROM access_events WHERE {clause} ORDER BY id DESC LIMIT ? OFFSET ?',[*params,size,(page-1)*size])]
            return {'items':rows,'total':total,'page':page,'size':size,
                    'today_views':db.execute("SELECT COUNT(*) FROM access_events WHERE kind='page_view' AND timestamp>=?",(today,)).fetchone()[0],
                    'online_sessions':db.execute('SELECT COUNT(*) FROM access_presence WHERE last_seen>=?',(cutoff,)).fetchone()[0],
                    'online_accounts':db.execute("SELECT COUNT(DISTINCT account) FROM access_presence WHERE last_seen>=? AND account!=''",(cutoff,)).fetchone()[0]}
