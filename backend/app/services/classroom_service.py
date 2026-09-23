from __future__ import annotations

import secrets
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _repair_text(value: str) -> str:
    """Repair legacy Chinese text that was decoded as GBK before storage."""
    if not value:
        return value
    try:
        repaired = value.encode("gbk").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return value
    return repaired if repaired.count("\ufffd") < value.count("\ufffd") else value


class ClassroomService:
    """Manage teacher-led classes, student membership, and learning guidance."""

    CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"

    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    @contextmanager
    def _connection(self):
        connection = self._connect()
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def _initialize(self) -> None:
        with self._connection() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS classrooms (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    code TEXT NOT NULL UNIQUE COLLATE NOCASE,
                    description TEXT NOT NULL DEFAULT '',
                    teacher_id TEXT NOT NULL,
                    teacher_account TEXT NOT NULL,
                    teacher_name TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    archived INTEGER NOT NULL DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS classroom_memberships (
                    class_id TEXT NOT NULL REFERENCES classrooms(id) ON DELETE CASCADE,
                    student_id TEXT NOT NULL,
                    student_account TEXT NOT NULL,
                    student_name TEXT NOT NULL,
                    joined_at TEXT NOT NULL,
                    PRIMARY KEY (class_id, student_id)
                );
                CREATE TABLE IF NOT EXISTS classroom_guidance (
                    id TEXT PRIMARY KEY,
                    class_id TEXT NOT NULL REFERENCES classrooms(id) ON DELETE CASCADE,
                    student_id TEXT NOT NULL,
                    author_id TEXT NOT NULL,
                    author_name TEXT NOT NULL,
                    source TEXT NOT NULL CHECK (source IN ('teacher', 'ai')),
                    content TEXT NOT NULL,
                    recommended_score INTEGER,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_classrooms_teacher
                    ON classrooms(teacher_id, created_at DESC);
                CREATE INDEX IF NOT EXISTS idx_class_members_student
                    ON classroom_memberships(student_id, joined_at DESC);
                CREATE INDEX IF NOT EXISTS idx_class_guidance_student
                    ON classroom_guidance(student_id, created_at DESC);
                """
            )

    def _new_code(self, db: sqlite3.Connection) -> str:
        for _ in range(20):
            code = "".join(secrets.choice(self.CODE_ALPHABET) for _ in range(6))
            if not db.execute(
                "SELECT 1 FROM classrooms WHERE code = ? COLLATE NOCASE",
                (code,),
            ).fetchone():
                return code
        raise RuntimeError("班级码生成失败，请稍后重试")

    @staticmethod
    def _public_class(row: sqlite3.Row, **extra: Any) -> dict[str, Any]:
        return {
            "id": row["id"],
            "name": row["name"],
            "code": row["code"],
            "description": row["description"],
            "teacher_name": row["teacher_name"],
            "created_at": row["created_at"],
            **extra,
        }

    def create_class(
        self,
        *,
        teacher_id: str,
        teacher_account: str,
        teacher_name: str,
        name: str,
        description: str = "",
    ) -> dict[str, Any]:
        name = name.strip()
        if len(name) < 2:
            raise ValueError("班级名称至少需要 2 个字符")
        with self._connection() as db:
            class_id = f"class-{uuid4().hex[:12]}"
            code = self._new_code(db)
            db.execute(
                """
                INSERT INTO classrooms (
                    id, name, code, description, teacher_id, teacher_account,
                    teacher_name, created_at, archived
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)
                """,
                (
                    class_id,
                    name[:60],
                    code,
                    description.strip()[:500],
                    teacher_id,
                    teacher_account,
                    teacher_name,
                    _now(),
                ),
            )
            row = db.execute("SELECT * FROM classrooms WHERE id = ?", (class_id,)).fetchone()
        return self._public_class(row, student_count=0)

    def list_for_teacher(self, teacher_id: str) -> list[dict[str, Any]]:
        with self._connection() as db:
            rows = db.execute(
                """
                SELECT c.*,
                       (SELECT COUNT(*) FROM classroom_memberships m WHERE m.class_id = c.id) AS student_count
                FROM classrooms c
                WHERE c.teacher_id = ? AND c.archived = 0
                ORDER BY c.created_at DESC
                """,
                (teacher_id,),
            ).fetchall()
        return [
            self._public_class(row, student_count=int(row["student_count"] or 0))
            for row in rows
        ]

    def list_for_student(self, student_id: str) -> list[dict[str, Any]]:
        with self._connection() as db:
            rows = db.execute(
                """
                SELECT c.*, m.joined_at,
                       (SELECT COUNT(*) FROM classroom_memberships members
                        WHERE members.class_id = c.id) AS student_count
                FROM classroom_memberships m
                JOIN classrooms c ON c.id = m.class_id
                WHERE m.student_id = ? AND c.archived = 0
                ORDER BY m.joined_at DESC
                """,
                (student_id,),
            ).fetchall()
        return [
            self._public_class(
                row,
                joined_at=row["joined_at"],
                student_count=int(row["student_count"] or 0),
            )
            for row in rows
        ]

    def join_by_code(
        self,
        *,
        student_id: str,
        student_account: str,
        student_name: str,
        code: str,
    ) -> dict[str, Any]:
        code = code.strip().upper()
        if len(code) < 4:
            raise ValueError("请输入有效的班级码")
        with self._connection() as db:
            row = db.execute(
                "SELECT * FROM classrooms WHERE code = ? COLLATE NOCASE AND archived = 0",
                (code,),
            ).fetchone()
            if not row:
                raise KeyError(code)
            db.execute(
                """
                INSERT INTO classroom_memberships (
                    class_id, student_id, student_account, student_name, joined_at
                ) VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(class_id, student_id) DO UPDATE SET
                    student_account = excluded.student_account,
                    student_name = excluded.student_name
                """,
                (row["id"], student_id, student_account, student_name, _now()),
            )
            student_count = db.execute(
                "SELECT COUNT(*) AS count FROM classroom_memberships WHERE class_id = ?",
                (row["id"],),
            ).fetchone()["count"]
        return self._public_class(row, student_count=int(student_count or 0))

    def _require_owner(self, db: sqlite3.Connection, class_id: str, teacher_id: str) -> sqlite3.Row:
        row = db.execute(
            "SELECT * FROM classrooms WHERE id = ? AND archived = 0",
            (class_id,),
        ).fetchone()
        if not row:
            raise KeyError(class_id)
        if row["teacher_id"] != teacher_id:
            raise PermissionError("只能管理自己创建的班级")
        return row

    def class_detail(self, teacher_id: str, class_id: str) -> dict[str, Any]:
        with self._connection() as db:
            class_row = self._require_owner(db, class_id, teacher_id)
            member_rows = db.execute(
                """
                SELECT * FROM classroom_memberships
                WHERE class_id = ?
                ORDER BY student_name COLLATE NOCASE
                """,
                (class_id,),
            ).fetchall()
        return self._public_class(
            class_row,
            student_count=len(member_rows),
            students=[
                {
                    "student_id": row["student_id"],
                    "student_account": row["student_account"],
                    "student_name": row["student_name"],
                    "joined_at": row["joined_at"],
                }
                for row in member_rows
            ],
        )

    def is_member(self, class_id: str, student_id: str) -> bool:
        with self._connection() as db:
            return bool(
                db.execute(
                    """
                    SELECT 1 FROM classroom_memberships
                    WHERE class_id = ? AND student_id = ?
                    """,
                    (class_id, student_id),
                ).fetchone()
            )

    def is_teacher(self, class_id: str, teacher_id: str) -> bool:
        with self._connection() as db:
            return bool(
                db.execute(
                    """
                    SELECT 1 FROM classrooms
                    WHERE id = ? AND teacher_id = ? AND archived = 0
                    """,
                    (class_id, teacher_id),
                ).fetchone()
            )

    def add_guidance(
        self,
        *,
        class_id: str,
        student_id: str,
        author_id: str,
        author_name: str,
        source: str,
        content: str,
        recommended_score: int | None = None,
    ) -> dict[str, Any]:
        content = _repair_text(content.strip())
        author_name = _repair_text(author_name.strip())
        if not content:
            raise ValueError("指导内容不能为空")
        if source not in {"teacher", "ai"}:
            raise ValueError("指导来源无效")
        if not self.is_member(class_id, student_id):
            raise KeyError(student_id)
        guidance_id = f"guidance-{uuid4().hex[:12]}"
        created_at = _now()
        with self._connection() as db:
            db.execute(
                """
                INSERT INTO classroom_guidance (
                    id, class_id, student_id, author_id, author_name,
                    source, content, recommended_score, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    guidance_id,
                    class_id,
                    student_id,
                    author_id,
                    author_name,
                    source,
                    content[:5000],
                    recommended_score,
                    created_at,
                ),
            )
        return {
            "id": guidance_id,
            "class_id": class_id,
            "student_id": student_id,
            "author_id": author_id,
            "author_name": _repair_text(author_name),
            "source": source,
            "content": content[:5000],
            "recommended_score": recommended_score,
            "created_at": created_at,
        }

    def latest_ai_guidance(
        self,
        *,
        class_id: str,
        student_id: str,
        within_minutes: int = 10,
    ) -> dict[str, Any] | None:
        cutoff = (datetime.now(timezone.utc) - timedelta(minutes=within_minutes)).isoformat(timespec="seconds")
        with self._connection() as db:
            row = db.execute(
                """
                SELECT g.*, c.name AS class_name
                FROM classroom_guidance g
                JOIN classrooms c ON c.id = g.class_id
                WHERE g.class_id = ? AND g.student_id = ? AND g.source = 'ai' AND g.created_at >= ?
                ORDER BY g.created_at DESC
                LIMIT 1
                """,
                (class_id, student_id, cutoff),
            ).fetchone()
        if not row:
            return None
        return self._guidance_dict(row)

    @staticmethod
    def _guidance_dict(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "id": row["id"],
            "class_id": row["class_id"],
            "class_name": row["class_name"] if "class_name" in row.keys() else "",
            "student_id": row["student_id"],
            "author_id": row["author_id"],
            "author_name": _repair_text(row["author_name"]),
            "source": row["source"],
            "content": _repair_text(row["content"]),
            "recommended_score": row["recommended_score"],
            "created_at": row["created_at"],
        }

    def list_guidance(
        self,
        *,
        student_id: str,
        class_id: str = "",
    ) -> list[dict[str, Any]]:
        query = """
            SELECT g.*, c.name AS class_name
            FROM classroom_guidance g
            JOIN classrooms c ON c.id = g.class_id
            WHERE g.student_id = ?
        """
        params: list[Any] = [student_id]
        if class_id:
            query += " AND g.class_id = ?"
            params.append(class_id)
        query += " ORDER BY g.created_at DESC"
        with self._connection() as db:
            rows = db.execute(query, params).fetchall()
        return [self._guidance_dict(row) for row in rows]

    def class_guidance(
        self,
        *,
        teacher_id: str,
        class_id: str,
        student_id: str = "",
    ) -> list[dict[str, Any]]:
        with self._connection() as db:
            self._require_owner(db, class_id, teacher_id)
        return self.list_guidance(student_id=student_id, class_id=class_id) if student_id else self._class_guidance(class_id)

    def _class_guidance(self, class_id: str) -> list[dict[str, Any]]:
        with self._connection() as db:
            rows = db.execute(
                """
                SELECT g.*, c.name AS class_name
                FROM classroom_guidance g
                JOIN classrooms c ON c.id = g.class_id
                WHERE g.class_id = ?
                ORDER BY g.created_at DESC
                """,
                (class_id,),
            ).fetchall()
        return [self._guidance_dict(row) for row in rows]
