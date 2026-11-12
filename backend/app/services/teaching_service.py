"""Transactional class management. All counts come from persisted records.

Auth users live in a separate database: their IDs are external references;
class, roster and teaching records have database-enforced foreign keys.
"""
from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone, date
from pathlib import Path
from uuid import uuid4

from .classroom_service import ClassroomService, _now

TZ = timezone(timedelta(hours=8))


def uid():
    return uuid4().hex


def day(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(TZ).date().isoformat()


class TeachingService:
    def __init__(self, classrooms: ClassroomService, learning_path: Path):
        self.classes = classrooms
        self.path = classrooms.database_path
        self.learning_path = learning_path
        self.files = self.path.parent / "class_resources"
        self.migrate()

    @contextmanager
    def db(self):
        with self.classes._connection() as db:
            yield db

    def migrate(self):
        with self.db() as db:
            # An online SQLite backup includes committed WAL pages, unlike copying the file.
            columns = {r[1] for r in db.execute("PRAGMA table_info(classrooms)")}
            if "major" not in columns:
                backup = self.path.with_suffix(".pre-teaching-v1.sqlite3")
                if not backup.exists():
                    with sqlite3.connect(backup) as target:
                        db.backup(target)
            db.execute('BEGIN IMMEDIATE')
            columns = {r[1] for r in db.execute("PRAGMA table_info(classrooms)")}
            for name, definition in {
                "major": "TEXT NOT NULL DEFAULT ''", "grade": "TEXT NOT NULL DEFAULT ''",
                "semester": "TEXT NOT NULL DEFAULT ''", "updated_at": "TEXT NOT NULL DEFAULT ''",
            }.items():
                if name not in columns:
                    db.execute(f"ALTER TABLE classrooms ADD COLUMN {name} {definition}")
            columns = {r[1] for r in db.execute("PRAGMA table_info(classroom_memberships)")}
            if "active" not in columns:
                db.execute("ALTER TABLE classroom_memberships ADD COLUMN active INTEGER NOT NULL DEFAULT 1")
                db.execute("ALTER TABLE classroom_memberships ADD COLUMN removed_at TEXT")
            db.executescript("""
            CREATE TABLE IF NOT EXISTS teaching_schema_versions(version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS attendance_sessions(
              id TEXT PRIMARY KEY, class_id TEXT NOT NULL REFERENCES classrooms(id),
              title TEXT NOT NULL, attendance_date TEXT NOT NULL, teacher_id TEXT NOT NULL,
              teacher_name TEXT NOT NULL, completed INTEGER NOT NULL DEFAULT 0,
              created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS attendance_records(
              session_id TEXT NOT NULL REFERENCES attendance_sessions(id), class_id TEXT NOT NULL,
              student_id TEXT NOT NULL, status TEXT CHECK(status IN ('present','late','leave','absent')),
              PRIMARY KEY(session_id,student_id),
              FOREIGN KEY(class_id,student_id) REFERENCES classroom_memberships(class_id,student_id));
            CREATE TABLE IF NOT EXISTS assignments(
              id TEXT PRIMARY KEY, class_id TEXT NOT NULL REFERENCES classrooms(id), title TEXT NOT NULL,
              content TEXT NOT NULL, kind TEXT NOT NULL CHECK(kind IN ('assignment','task')),
              status TEXT NOT NULL CHECK(status IN ('draft','published')),
              due_at TEXT NOT NULL, teacher_id TEXT NOT NULL, teacher_name TEXT NOT NULL,
              created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS assignment_recipients(
              assignment_id TEXT NOT NULL REFERENCES assignments(id), class_id TEXT NOT NULL,
              student_id TEXT NOT NULL, PRIMARY KEY(assignment_id,student_id),
              FOREIGN KEY(class_id,student_id) REFERENCES classroom_memberships(class_id,student_id));
            CREATE TABLE IF NOT EXISTS assignment_submissions(
              id TEXT PRIMARY KEY, assignment_id TEXT NOT NULL, student_id TEXT NOT NULL,
              content TEXT NOT NULL, submitted_at TEXT NOT NULL, score REAL CHECK(score BETWEEN 0 AND 100),
              feedback TEXT NOT NULL DEFAULT '', grader_id TEXT, graded_at TEXT,
              UNIQUE(assignment_id,student_id),
              FOREIGN KEY(assignment_id,student_id) REFERENCES assignment_recipients(assignment_id,student_id));
            CREATE TABLE IF NOT EXISTS class_announcements(
              id TEXT PRIMARY KEY, class_id TEXT NOT NULL REFERENCES classrooms(id), title TEXT NOT NULL,
              content TEXT NOT NULL, status TEXT NOT NULL CHECK(status IN ('draft','published','withdrawn')),
              pinned INTEGER NOT NULL DEFAULT 0, teacher_id TEXT NOT NULL, teacher_name TEXT NOT NULL,
              published_at TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS study_groups(
              id TEXT PRIMARY KEY, class_id TEXT NOT NULL REFERENCES classrooms(id), name TEXT NOT NULL,
              leader_id TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
              FOREIGN KEY(class_id,leader_id) REFERENCES classroom_memberships(class_id,student_id));
            CREATE TABLE IF NOT EXISTS study_group_members(
              group_id TEXT NOT NULL REFERENCES study_groups(id) ON DELETE CASCADE,
              class_id TEXT NOT NULL, student_id TEXT NOT NULL, PRIMARY KEY(group_id,student_id),
              UNIQUE(class_id,student_id),
              FOREIGN KEY(class_id,student_id) REFERENCES classroom_memberships(class_id,student_id));
            CREATE TABLE IF NOT EXISTS class_resources(
              id TEXT PRIMARY KEY, class_id TEXT NOT NULL REFERENCES classrooms(id), name TEXT NOT NULL,
              category TEXT NOT NULL, visible INTEGER NOT NULL, storage_name TEXT NOT NULL UNIQUE,
              size INTEGER NOT NULL, teacher_id TEXT NOT NULL, teacher_name TEXT NOT NULL,
              deleted INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS class_activity_logs(
              id TEXT PRIMARY KEY, class_id TEXT NOT NULL REFERENCES classrooms(id), action TEXT NOT NULL,
              description TEXT NOT NULL, actor_id TEXT NOT NULL, actor_name TEXT NOT NULL, created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS teacher_todos(
              id TEXT PRIMARY KEY, class_id TEXT NOT NULL REFERENCES classrooms(id), teacher_id TEXT NOT NULL,
              title TEXT NOT NULL, due_at TEXT, priority INTEGER NOT NULL DEFAULT 1,
              done INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS class_import_previews(
              id TEXT PRIMARY KEY, class_id TEXT NOT NULL REFERENCES classrooms(id), teacher_id TEXT NOT NULL,
              payload TEXT NOT NULL, created_at TEXT NOT NULL, used INTEGER NOT NULL DEFAULT 0);
            CREATE TABLE IF NOT EXISTS class_join_requests(
              id TEXT PRIMARY KEY, class_id TEXT NOT NULL REFERENCES classrooms(id), student_id TEXT NOT NULL,
              student_account TEXT NOT NULL, student_name TEXT NOT NULL,
              status TEXT NOT NULL CHECK(status IN ('pending','approved','rejected')),
              reviewed_by TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
              UNIQUE(class_id,student_id));
            CREATE INDEX IF NOT EXISTS idx_attendance_class_date ON attendance_sessions(class_id,attendance_date);
            CREATE INDEX IF NOT EXISTS idx_assignments_class_status ON assignments(class_id,status,due_at);
            CREATE INDEX IF NOT EXISTS idx_submission_student ON assignment_submissions(student_id,submitted_at);
            CREATE INDEX IF NOT EXISTS idx_announcement_class ON class_announcements(class_id,status,pinned,published_at);
            CREATE INDEX IF NOT EXISTS idx_resources_class ON class_resources(class_id,deleted,visible);
            CREATE INDEX IF NOT EXISTS idx_activity_class ON class_activity_logs(class_id,created_at DESC);
            CREATE INDEX IF NOT EXISTS idx_todos_owner ON teacher_todos(teacher_id,class_id,done,due_at);
            CREATE INDEX IF NOT EXISTS idx_members_active ON classroom_memberships(class_id,active);
            CREATE INDEX IF NOT EXISTS idx_join_requests_status ON class_join_requests(class_id,status);
            """)
            db.execute("INSERT OR IGNORE INTO teaching_schema_versions VALUES(1,?)", (_now(),))

    def access(self, db, user, cid, *, write=False, student=False):
        row = db.execute("SELECT * FROM classrooms WHERE id=?", (cid,)).fetchone()
        if not row:
            raise KeyError("班级不存在")
        if user.role == "student":
            if not student or not db.execute("SELECT 1 FROM classroom_memberships WHERE class_id=? AND student_id=? AND active=1", (cid, user.id)).fetchone():
                raise PermissionError("无权访问该班级")
        elif user.role not in {"admin", "super_admin"} and row["teacher_id"] != user.id:
            raise PermissionError("只能管理获得授权的班级")
        if write and row["archived"]:
            raise ValueError("已归档班级只读，历史记录仍然保留")
        return dict(row)

    def log(self, db, user, cid, action, description):
        db.execute("INSERT INTO class_activity_logs VALUES(?,?,?,?,?,?,?)",
                   (uid(), cid, action, description, user.id, user.name, _now()))

    def roster(self, db, cid):
        return [dict(r) for r in db.execute("SELECT * FROM classroom_memberships WHERE class_id=? AND active=1 ORDER BY student_name", (cid,))]

    def list_classes(self, user, q="", major="", grade="", semester="", status="", page=1, size=50):
        with self.db() as db:
            where, args = ["1=1"], []
            if user.role == "student":
                where.append("EXISTS(SELECT 1 FROM classroom_memberships m WHERE m.class_id=c.id AND m.student_id=? AND m.active=1)")
                args.append(user.id)
            elif user.role == "teacher":
                where.append("teacher_id=?")
                args.append(user.id)
            for col, val in [("name", q), ("major", major), ("grade", grade), ("semester", semester)]:
                if val:
                    where.append(f"{col} LIKE ?")
                    args.append(f"%{val}%")
            if status in {"active", "archived"}:
                where.append("archived=?")
                args.append(int(status == "archived"))
            clause = " AND ".join(where)
            total = db.execute(f"SELECT COUNT(*) FROM classrooms c WHERE {clause}", args).fetchone()[0]
            rows = db.execute(f"SELECT c.*,(SELECT COUNT(*) FROM classroom_memberships m WHERE m.class_id=c.id AND m.active=1) student_count FROM classrooms c WHERE {clause} ORDER BY created_at DESC LIMIT ? OFFSET ?", [*args, size, (page-1)*size])
            return {"items": [dict(r) for r in rows], "total": total, "page": page, "size": size}

    def save_class(self, user, data, teacher, cid=None):
        with self.db() as db:
            if cid is None:
                cid = 'class-'+uid()[:12]
                db.execute('INSERT INTO classrooms(id,name,code,description,teacher_id,teacher_account,teacher_name,created_at) VALUES(?,?,?,?,?,?,?,?)', (cid,data['name'],self.classes._new_code(db),data['description'],teacher['id'],teacher['account'],teacher['name'],_now()))
            self.access(db, user, cid, write=True)
            db.execute("UPDATE classrooms SET name=?,description=?,major=?,grade=?,semester=?,teacher_id=?,teacher_account=?,teacher_name=?,updated_at=? WHERE id=?", (data["name"].strip(), data["description"].strip(), data["major"].strip(), data["grade"].strip(), data["semester"].strip(), teacher["id"], teacher["account"], teacher["name"], _now(), cid))
            self.log(db, user, cid, "class", "保存班级信息：" + data["name"])
            return dict(db.execute("SELECT * FROM classrooms WHERE id=?", (cid,)).fetchone())

    def archive(self, user, cid):
        with self.db() as db:
            self.access(db, user, cid, write=True)
            db.execute("UPDATE classrooms SET archived=1,updated_at=? WHERE id=?", (_now(), cid))
            self.log(db, user, cid, "archive", "归档班级，保留全部教学记录")

    def add_members(self, db, user, cid, students):
        for s in students:
            db.execute("INSERT INTO classroom_memberships(class_id,student_id,student_account,student_name,joined_at,active) VALUES(?,?,?,?,?,1) ON CONFLICT(class_id,student_id) DO UPDATE SET active=1,removed_at=NULL,student_name=excluded.student_name,student_account=excluded.student_account", (cid, s["id"], s["account"], s["name"], _now()))
        self.log(db, user, cid, "students", f"导入学生名单（{len(students)} 人）")

    def remove_member(self, user, cid, sid):
        with self.db() as db:
            self.access(db, user, cid, write=True)
            row = db.execute("SELECT * FROM classroom_memberships WHERE class_id=? AND student_id=? AND active=1", (cid, sid)).fetchone()
            if not row:
                raise KeyError("学生不在班级")
            db.execute("UPDATE classroom_memberships SET active=0,removed_at=? WHERE class_id=? AND student_id=?", (_now(), cid, sid))
            db.execute("DELETE FROM study_group_members WHERE class_id=? AND student_id=?", (cid, sid))
            db.execute("UPDATE study_groups SET leader_id=NULL WHERE class_id=? AND leader_id=?", (cid, sid))
            self.log(db, user, cid, "students", "移出学生：" + row["student_name"] + "（历史成绩保留）")

    def attendance(self, user, cid, data, session_id=None):
        with self.db() as db:
            self.access(db, user, cid, write=True)
            now = _now()
            if session_id:
                existing = db.execute("SELECT * FROM attendance_sessions WHERE id=? AND class_id=?", (session_id, cid)).fetchone()
                if not existing:
                    raise KeyError("考勤活动不存在")
                if existing['attendance_date'] != data['attendance_date']:
                    raise ValueError('考勤日期不可修改，请创建新的考勤活动')
                db.execute('UPDATE attendance_sessions SET title=? WHERE id=?',(data['title'],session_id))
            else:
                if data["attendance_date"] > datetime.now(TZ).date().isoformat():
                    raise ValueError("不能登记未来日期的考勤")
                session_id = uid()
                db.execute("INSERT INTO attendance_sessions VALUES(?,?,?,?,?,?,0,?,?)", (session_id, cid, data["title"], data["attendance_date"], user.id, user.name, now, now))
                db.executemany("INSERT INTO attendance_records VALUES(?,?,?,NULL)", [(session_id, cid, s["student_id"]) for s in self.roster(db, cid)])
            for record in data["records"]:
                changed = db.execute("UPDATE attendance_records SET status=? WHERE session_id=? AND student_id=?", (record["status"], session_id, record["student_id"]))
                if not changed.rowcount:
                    raise ValueError("考勤学生不属于该活动的名单")
            if data["completed"]:
                count, missing = db.execute("SELECT COUNT(*),SUM(status IS NULL) FROM attendance_records WHERE session_id=?", (session_id,)).fetchone()
                if not count or missing:
                    raise ValueError("完成考勤前请登记名单中所有学生的状态")
            db.execute("UPDATE attendance_sessions SET completed=?,updated_at=? WHERE id=?", (int(data["completed"]), now, session_id))
            self.log(db, user, cid, "attendance", "完成考勤" if data["completed"] else "保存考勤草稿")
            return {"id": session_id}

    def assignment(self, user, cid, data, aid=None):
        with self.db() as db:
            self.access(db, user, cid, write=True)
            now = _now()
            old = db.execute("SELECT * FROM assignments WHERE id=? AND class_id=?", (aid, cid)).fetchone() if aid else None
            if aid and not old:
                raise KeyError("作业不存在")
            if old and old["status"] == "published":
                raise ValueError("已发布作业不能改写题目和接收名单")
            if data["status"] == "published" and data["due_at"] <= now:
                raise ValueError("发布时截止时间必须晚于当前时间")
            aid = aid or uid()
            if old:
                db.execute("UPDATE assignments SET title=?,content=?,kind=?,status=?,due_at=?,updated_at=? WHERE id=?", (data["title"], data["content"], data["kind"], data["status"], data["due_at"], now, aid))
            else:
                db.execute("INSERT INTO assignments VALUES(?,?,?,?,?,?,?,?,?,?,?)", (aid, cid, data["title"], data["content"], data["kind"], data["status"], data["due_at"], user.id, user.name, now, now))
            if data["status"] == "published":
                members = self.roster(db, cid)
                if not members:
                    raise ValueError("班级没有在籍学生，无法发布")
                db.executemany("INSERT OR IGNORE INTO assignment_recipients VALUES(?,?,?)", [(aid, cid, s["student_id"]) for s in members])
            self.log(db, user, cid, "assignment", f"{'发布' if data['status']=='published' else '保存草稿'}：{data['title']}")
            return {"id": aid}

    def submit(self, user, cid, aid, content):
        with self.db() as db:
            self.access(db, user, cid, write=True, student=True)
            row = db.execute("SELECT a.* FROM assignments a JOIN assignment_recipients r ON a.id=r.assignment_id WHERE a.id=? AND a.class_id=? AND r.student_id=? AND a.status='published'", (aid, cid, user.id)).fetchone()
            if not row:
                raise PermissionError("你不是该作业的接收学生")
            if row["due_at"] < _now():
                raise ValueError("作业已截止，不能继续提交")
            db.execute("INSERT INTO assignment_submissions(id,assignment_id,student_id,content,submitted_at) VALUES(?,?,?,?,?) ON CONFLICT(assignment_id,student_id) DO UPDATE SET content=excluded.content,submitted_at=excluded.submitted_at,score=NULL,feedback='',grader_id=NULL,graded_at=NULL", (uid(), aid, user.id, content, _now()))

    def grade(self, user, cid, aid, sid, score, feedback):
        with self.db() as db:
            self.access(db, user, cid, write=True)
            if not db.execute("SELECT 1 FROM assignments WHERE id=? AND class_id=?", (aid, cid)).fetchone():
                raise KeyError("作业不存在")
            if not db.execute("UPDATE assignment_submissions SET score=?,feedback=?,grader_id=?,graded_at=? WHERE assignment_id=? AND student_id=?", (score, feedback, user.id, _now(), aid, sid)).rowcount:
                raise KeyError("学生尚未提交")
            self.log(db, user, cid, "grade", "教师批改作业")

    def announcement(self, user, cid, data, item_id=None):
        with self.db() as db:
            self.access(db, user, cid, write=True)
            old = db.execute("SELECT * FROM class_announcements WHERE id=? AND class_id=?", (item_id, cid)).fetchone() if item_id else None
            if item_id and not old:
                raise KeyError("公告不存在")
            now = _now()
            published = old["published_at"] if old else None
            if data["status"] == "published" and (not old or old["status"] != "published"):
                published = now
            item_id = item_id or uid()
            db.execute("INSERT INTO class_announcements VALUES(?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET title=excluded.title,content=excluded.content,status=excluded.status,pinned=excluded.pinned,published_at=excluded.published_at,updated_at=excluded.updated_at", (item_id, cid, data["title"], data["content"], data["status"], int(data["pinned"]), user.id, user.name, published, old["created_at"] if old else now, now))
            self.log(db, user, cid, "announcement", f"{data['status']} 公告：{data['title']}")
            return {"id": item_id}

    def save_groups(self, user, cid, groups, replace=False):
        with self.db() as db:
            self.access(db, user, cid, write=True)
            valid = {s["student_id"] for s in self.roster(db, cid)}
            seen = set()
            for g in groups:
                if not g["name"].strip():
                    raise ValueError("小组名称不能为空")
                ids = g["members"]
                if not set(ids) <= valid or len(set(ids)) != len(ids) or seen.intersection(ids):
                    raise ValueError("组员必须来自当前班级且不能重复分组")
                if g["leader_id"] and g["leader_id"] not in ids:
                    raise ValueError("组长必须是本组成员")
                seen.update(ids)
            if db.execute("SELECT 1 FROM study_groups WHERE class_id=?", (cid,)).fetchone() and not replace:
                raise ValueError("已有分组，请确认替换后保存")
            db.execute("DELETE FROM study_groups WHERE class_id=?", (cid,))
            for g in groups:
                gid = uid()
                db.execute("INSERT INTO study_groups VALUES(?,?,?,?,?,?)", (gid, cid, g["name"].strip(), g["leader_id"] or None, _now(), _now()))
                db.executemany("INSERT INTO study_group_members VALUES(?,?,?)", [(gid, cid, sid) for sid in g["members"]])
            self.log(db, user, cid, "groups", f"确认保存学习小组（{len(groups)} 组）")

    def todo(self, user, cid, data, item_id=None):
        with self.db() as db:
            self.access(db, user, cid, write=True)
            if item_id and not db.execute("SELECT 1 FROM teacher_todos WHERE id=? AND class_id=? AND teacher_id=?", (item_id, cid, user.id)).fetchone():
                raise KeyError("待办不存在")
            item_id = item_id or uid()
            db.execute("INSERT INTO teacher_todos VALUES(?,?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET title=excluded.title,due_at=excluded.due_at,priority=excluded.priority,done=excluded.done,updated_at=excluded.updated_at", (item_id, cid, user.id, data["title"], data["due_at"], data["priority"], int(data["done"]), _now(), _now()))
            return {"id": item_id}

    def metrics(self, user):
        with self.db() as db:
            owner = "1=1" if user.role in {"admin", "super_admin"} else "teacher_id=?"
            args = [] if owner == "1=1" else [user.id]
            ids = [r[0] for r in db.execute(f"SELECT id FROM classrooms WHERE archived=0 AND {owner}", args)]
            if not ids:
                return {"classes": 0, "students": 0, "attendance_rate": None, "assignment_rate": None, "progress": None}
            marks = ','.join('?' for _ in ids)
            students = db.execute(f"SELECT COUNT(DISTINCT student_id) FROM classroom_memberships WHERE active=1 AND class_id IN ({marks})", ids).fetchone()[0]
            month = datetime.now(TZ).strftime('%Y-%m')
            records = list(db.execute(f"SELECT r.status FROM attendance_records r JOIN attendance_sessions s ON s.id=r.session_id WHERE s.completed=1 AND s.attendance_date LIKE ? AND s.class_id IN ({marks})", [month+'%', *ids]))
            expected = sum(r[0] != 'leave' for r in records)
            attendance = round(sum(r[0] in {'present','late'} for r in records)/expected*100, 1) if expected else None
            def completion(kind, due_only):
                condition = ' AND a.due_at<=?' if due_only else ''
                params = [*ids, kind, *([_now()] if due_only else [])]
                row = db.execute(f"SELECT COUNT(*),SUM(s.id IS NOT NULL) FROM assignment_recipients r JOIN assignments a ON a.id=r.assignment_id LEFT JOIN assignment_submissions s ON s.assignment_id=r.assignment_id AND s.student_id=r.student_id WHERE a.class_id IN ({marks}) AND a.kind=? AND a.status='published'{condition}", params).fetchone()
                return round((row[1] or 0)/row[0]*100, 1) if row[0] else None
            return {"classes": len(ids), "students": students, "attendance_rate": attendance, "assignment_rate": completion('assignment', True), "progress": completion('task', False)}

    def analytics(self, db, cid, start, end):
        members = self.roster(db, cid)
        accounts = {s['student_account']: s for s in members}
        member_ids = {s['student_id'] for s in members}
        active = {}
        scores = []
        def event(sid, stamp):
            d = day(stamp)
            if sid in member_ids and start <= d <= end:
                active.setdefault(d, set()).add(sid)
        # Read-only connection; legacy learning data remains in its original database.
        if self.learning_path.exists() and accounts:
            with sqlite3.connect(f"file:{self.learning_path.as_posix()}?mode=ro", uri=True) as learning:
                for table in ('anatomy_attempts', 'quiz_attempts'):
                    if not learning.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone():
                        continue
                    keys = list(accounts)
                    cutoff = datetime.combine(date.fromisoformat(start), datetime.min.time(), TZ).astimezone(timezone.utc).isoformat(timespec='seconds')
                    for account, stamp, score in learning.execute(f"SELECT account,created_at,score FROM {table} WHERE account IN ({','.join('?' for _ in keys)}) AND created_at>=?", [*keys, cutoff]):
                        if stamp >= accounts[account]['joined_at']:
                            event(accounts[account]['student_id'], stamp)
                            if start <= day(stamp) <= end:
                                scores.append(score)
        for r in db.execute("SELECT s.student_id,s.submitted_at,s.score FROM assignment_submissions s JOIN assignments a ON a.id=s.assignment_id WHERE a.class_id=?", (cid,)):
            event(r[0], r[1])
            if r[2] is not None and start <= day(r[1]) <= end:
                scores.append(r[2])
        total = len(members)
        dates = [date.fromisoformat(start)+timedelta(days=i) for i in range((date.fromisoformat(end)-date.fromisoformat(start)).days+1)]
        trend = [{"date": d.isoformat(), "active": len(active.get(d.isoformat(), set())), "rate": round(len(active.get(d.isoformat(), set()))/total*100, 1) if total else None} for d in dates]
        attendance = [dict(r) for r in db.execute("SELECT s.attendance_date date,COUNT(*) expected,SUM(r.status IN ('present','late')) present,SUM(r.status='leave') leaves FROM attendance_sessions s JOIN attendance_records r ON r.session_id=s.id WHERE s.class_id=? AND s.completed=1 AND s.attendance_date BETWEEN ? AND ? GROUP BY s.attendance_date ORDER BY s.attendance_date", (cid, start, end))]
        for r in attendance:
            denominator = r['expected']-r['leaves']
            r['rate'] = round(r['present']/denominator*100,1) if denominator else None
        assignments = [dict(r) for r in db.execute("SELECT a.id,a.title,a.kind,a.due_at,COUNT(r.student_id) expected,COUNT(s.id) submitted FROM assignments a LEFT JOIN assignment_recipients r ON r.assignment_id=a.id LEFT JOIN assignment_submissions s ON s.assignment_id=r.assignment_id AND s.student_id=r.student_id WHERE a.class_id=? AND a.status='published' GROUP BY a.id", (cid,))]
        return {"trend": trend, "has_activity": any(p['active'] for p in trend), "attendance": attendance, "assignments": assignments,
                "score_distribution": [{"label": label, "count": sum(lo <= v <= hi for v in scores)} for label, lo, hi in [('0–59',0,59.999),('60–79',60,79.999),('80–89',80,89.999),('90–100',90,100)]],
                "students": [{**s, "completed_tasks": db.execute("SELECT COUNT(*) FROM assignment_submissions x JOIN assignments a ON a.id=x.assignment_id WHERE a.class_id=? AND a.kind='task' AND x.student_id=?", (cid,s['student_id'])).fetchone()[0], "assigned_tasks": db.execute("SELECT COUNT(*) FROM assignment_recipients r JOIN assignments a ON a.id=r.assignment_id WHERE a.class_id=? AND a.kind='task' AND r.student_id=?", (cid,s['student_id'])).fetchone()[0]} for s in members]}

    def workspace(self, user, cid, start, end, attendance_date):
        with self.db() as db:
            classroom = self.access(db, user, cid, student=True)
            student = user.role == 'student'
            assignments = [dict(r) for r in db.execute("SELECT * FROM assignments WHERE class_id=? ORDER BY created_at DESC", (cid,))]
            for a in assignments:
                a['submissions'] = [dict(r) for r in db.execute("SELECT r.student_id,m.student_account,m.student_name,s.content,s.submitted_at,s.score,s.feedback FROM assignment_recipients r JOIN classroom_memberships m ON m.class_id=r.class_id AND m.student_id=r.student_id LEFT JOIN assignment_submissions s ON s.assignment_id=r.assignment_id AND s.student_id=r.student_id WHERE r.assignment_id=?" + (" AND r.student_id=?" if student else ''), [a['id'], *([user.id] if student else [])])]
            if student:
                assignments = [a for a in assignments if a['status']=='published' and a['submissions']]
            sessions = [dict(r) for r in db.execute("SELECT * FROM attendance_sessions WHERE class_id=?" + (" AND completed=1" if student else '') + " ORDER BY attendance_date DESC,created_at DESC", (cid,))]
            for s in sessions:
                s['records'] = [dict(r) for r in db.execute("SELECT r.*,m.student_name,m.student_account FROM attendance_records r JOIN classroom_memberships m ON m.class_id=r.class_id AND m.student_id=r.student_id WHERE r.session_id=?" + (" AND r.student_id=?" if student else ''), [s['id'], *([user.id] if student else [])])]
            announcements = [dict(r) for r in db.execute("SELECT * FROM class_announcements WHERE class_id=?" + (" AND status='published'" if student else '') + " ORDER BY pinned DESC,created_at DESC", (cid,))]
            resources = [dict(r) for r in db.execute("SELECT id,name,category,visible,size,teacher_name,created_at FROM class_resources WHERE class_id=? AND deleted=0" + (" AND visible=1" if student else '') + " ORDER BY created_at DESC", (cid,))]
            base = {"classroom": classroom, "assignments": assignments, "attendance": sessions, "announcements": announcements, "resources": resources}
            if student:
                base['groups'] = [dict(r) for r in db.execute("SELECT g.name,m.student_id,c.student_name,g.leader_id FROM study_groups g JOIN study_group_members own ON own.group_id=g.id AND own.student_id=? JOIN study_group_members m ON m.group_id=g.id JOIN classroom_memberships c ON c.class_id=m.class_id AND c.student_id=m.student_id WHERE g.class_id=?", (user.id,cid))]
                return base
            overview_session = next((s for s in sessions if s['attendance_date']==attendance_date and s['completed']), None)
            overview = None
            if overview_session:
                overview = {k: sum(r['status']==k for r in overview_session['records']) for k in ('present','late','leave','absent')}
                overview['total'] = len(overview_session['records'])
                overview['session_title'] = overview_session['title']
            groups = [dict(r) for r in db.execute("SELECT * FROM study_groups WHERE class_id=?", (cid,))]
            for g in groups:
                g['members'] = [r[0] for r in db.execute("SELECT student_id FROM study_group_members WHERE group_id=?", (g['id'],))]
            todos = [dict(r) for r in db.execute("SELECT * FROM teacher_todos WHERE class_id=? AND teacher_id=? ORDER BY done,priority DESC,due_at", (cid,user.id))]
            for t in todos:
                t['tab'] = 'todos'
                t['custom'] = True
            applications = [dict(r) for r in db.execute("SELECT * FROM class_join_requests WHERE class_id=? AND status='pending' ORDER BY created_at",(cid,))]
            for request in applications:
                todos.append({'id':'join-'+request['id'],'title':'待处理入班申请：'+request['student_name'],'tab':'students','priority':2,'done':False})
            for a in assignments:
                ungraded = sum(bool(s['submitted_at']) and s['score'] is None for s in a['submissions'])
                if ungraded and a['kind']=='assignment':
                    todos.append({"id": 'grade-'+a['id'], "title": f"待批改：{a['title']}（{ungraded} 份）", "tab": 'assignments', "due_at": a['due_at'], "priority": 2, "done": False})
                if a['status']=='draft':
                    todos.append({"id": 'draft-'+a['id'], "title": ('待审核与发布题目：' if a['kind']=='assignment' else '待发布学习任务：')+a['title'], "tab": 'assignments', "priority": 1, "done": False})
            for r in resources:
                if not r['visible']:
                    todos.append({"id": 'resource-'+r['id'], "title": '待发布资料：'+r['name'], "tab": 'resources', "priority": 1, "done": False})
            todos.sort(key=lambda t: (bool(t['done']), -t['priority'], t.get('due_at') or '9999'))
            base.update({"students": self.roster(db,cid), "applications":applications,"overview": overview, "groups": groups, "todos": todos,
                         "analytics": self.analytics(db,cid,start,end),
                         "logs": [dict(r) for r in db.execute("SELECT * FROM class_activity_logs WHERE class_id=? ORDER BY created_at DESC,rowid DESC LIMIT 8", (cid,))]})
            return base
