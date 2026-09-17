from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from time import perf_counter
from typing import Callable
from uuid import uuid4

from ..models import SkillPolicyUpdate, SkillQuery, SkillResult

CATALOG = {
    'anatomy_search': {'name': '解剖结构检索', 'description': '检索模型结构、中文术语与器官归属', 'source': 'BodyParts3D 4.0'},
    'textbook_search': {'name': '教材依据检索', 'description': '查询本地教材片段、章节和页码', 'source': '本地系统解剖学教材索引'},
    'graph_query': {'name': '解剖图谱查询', 'description': '查询系统、器官与精细结构的一层归属关系', 'source': '本地解剖知识图谱'},
}


class SkillRegistry:
    def __init__(self, database_path: Path, handlers: dict[str, Callable[[SkillQuery], SkillResult]]) -> None:
        self.database_path, self.handlers = database_path, handlers
        database_path.parent.mkdir(parents=True, exist_ok=True)
        with self._db() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS skill_policies (
                    id TEXT PRIMARY KEY, enabled INTEGER NOT NULL DEFAULT 0,
                    allowed_roles TEXT NOT NULL DEFAULT '[]', hourly_limit INTEGER NOT NULL DEFAULT 120,
                    updated_by TEXT NOT NULL DEFAULT '', updated_at TEXT NOT NULL DEFAULT ''
                );
                CREATE TABLE IF NOT EXISTS skill_calls (
                    id TEXT PRIMARY KEY, run_id TEXT NOT NULL, skill_id TEXT NOT NULL,
                    account TEXT NOT NULL, role TEXT NOT NULL, status TEXT NOT NULL,
                    duration_ms INTEGER NOT NULL DEFAULT 0, message TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_skill_budget ON skill_calls(skill_id, account, created_at);
            ''')
            for skill_id in CATALOG:
                db.execute('INSERT OR IGNORE INTO skill_policies(id) VALUES (?)', (skill_id,))

    @contextmanager
    def _db(self):
        db = sqlite3.connect(self.database_path, timeout=10)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    @staticmethod
    def _public(row: sqlite3.Row) -> dict:
        return {
            'id': row['id'], **CATALOG[row['id']], 'version': '1.0.0', 'read_only': True,
            'enabled': bool(row['enabled']), 'allowed_roles': json.loads(row['allowed_roles']),
            'hourly_limit': row['hourly_limit'], 'updated_by': row['updated_by'], 'updated_at': row['updated_at'],
        }

    def list_skills(self) -> list[dict]:
        with self._db() as db:
            return [self._public(row) for row in db.execute('SELECT * FROM skill_policies') if row['id'] in CATALOG]

    def update(self, skill_id: str, policy: SkillPolicyUpdate, account: str) -> dict:
        if skill_id not in CATALOG:
            raise KeyError(skill_id)
        if policy.enabled and not policy.allowed_roles:
            raise ValueError('启用 Skill 时至少选择一种允许角色')
        with self._db() as db:
            db.execute(
                'UPDATE skill_policies SET enabled=?, allowed_roles=?, hourly_limit=?, updated_by=?, updated_at=? WHERE id=?',
                (int(policy.enabled), json.dumps(sorted(set(policy.allowed_roles))), policy.hourly_limit, account, datetime.now(timezone.utc).isoformat(), skill_id),
            )
            return self._public(db.execute('SELECT * FROM skill_policies WHERE id=?', (skill_id,)).fetchone())

    def invoke(self, skill_id: str, args: SkillQuery, account: str, role: str, run_id: str) -> SkillResult:
        if skill_id not in CATALOG or skill_id not in self.handlers:
            raise KeyError(skill_id)
        role = 'admin' if role == 'super_admin' else role
        call_id = uuid4().hex
        now = datetime.now(timezone.utc)
        with self._db() as db:
            # Serialize policy checks and budget reservations across workers.
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT * FROM skill_policies WHERE id=?', (skill_id,)).fetchone()
            status, message = 'running', ''
            if not row or not row['enabled']:
                status, message = 'disabled', '管理员尚未启用此 Skill'
            elif role not in json.loads(row['allowed_roles']):
                status, message = 'forbidden', '当前身份没有此 Skill 的调用权限'
            else:
                count = db.execute(
                    "SELECT COUNT(*) FROM skill_calls WHERE skill_id=? AND account=? AND created_at>? AND status IN ('running','success','empty','error')",
                    (skill_id, account, (now - timedelta(hours=1)).isoformat()),
                ).fetchone()[0]
                if count >= row['hourly_limit']:
                    status, message = 'rate_limited', '本账号此 Skill 的每小时调用额度已用完'
            db.execute(
                'INSERT INTO skill_calls(id,run_id,skill_id,account,role,status,message,created_at) VALUES (?,?,?,?,?,?,?,?)',
                (call_id, run_id, skill_id, account, role, status, message, now.isoformat()),
            )
        if status != 'running':
            return SkillResult(skill_id=skill_id, status=status, message=message, call_id=call_id)
        started = perf_counter()
        try:
            result = SkillResult.model_validate(self.handlers[skill_id](args))
            if result.skill_id != skill_id or result.status not in {'success', 'empty'}:
                raise ValueError('Invalid skill result')
        except Exception:
            result = SkillResult(skill_id=skill_id, status='error', message='检索服务异常，请稍后重试或联系管理员')
        result.duration_ms = max(0, round((perf_counter() - started) * 1000))
        result.call_id = call_id
        with self._db() as db:
            db.execute('UPDATE skill_calls SET status=?,duration_ms=?,message=? WHERE id=?', (result.status, result.duration_ms, result.message, call_id))
        return result

    def recent_calls(self, limit: int = 50) -> list[dict]:
        with self._db() as db:
            return [dict(row) for row in db.execute('SELECT * FROM skill_calls ORDER BY created_at DESC LIMIT ?', (max(1, min(limit, 100)),))]
