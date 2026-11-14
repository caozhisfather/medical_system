from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.isoformat()


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 310_000)
    return f"pbkdf2_sha256$310000${salt.hex()}${digest.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations, salt_hex, expected_hex = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        actual = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), int(iterations)
        )
        return hmac.compare_digest(actual, bytes.fromhex(expected_hex))
    except (ValueError, TypeError):
        return False


class AuthService:
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
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    account TEXT NOT NULL UNIQUE COLLATE NOCASE,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE COLLATE NOCASE,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL CHECK (role IN ('student', 'teacher', 'admin', 'super_admin')),
                    status TEXT NOT NULL,
                    email_verified INTEGER NOT NULL DEFAULT 0,
                    department TEXT NOT NULL DEFAULT '',
                    permissions TEXT NOT NULL DEFAULT '[]',
                    last_login TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS auth_tokens (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    token_hash TEXT NOT NULL UNIQUE,
                    purpose TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    used_at TEXT
                );
                CREATE TABLE IF NOT EXISTS email_verification_codes (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    code_hash TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    used_at TEXT,
                    attempts INTEGER NOT NULL DEFAULT 0,
                    delivery_failed INTEGER NOT NULL DEFAULT 0
                );
                CREATE INDEX IF NOT EXISTS idx_email_codes_user ON email_verification_codes(user_id, created_at);
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    token_hash TEXT NOT NULL UNIQUE,
                    expires_at TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    revoked_at TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_auth_tokens_user ON auth_tokens(user_id, purpose, created_at);
                CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token_hash);
                """
            )
            columns = {row["name"] for row in db.execute("PRAGMA table_info(users)")}
            if "nickname" not in columns:
                db.execute("ALTER TABLE users ADD COLUMN nickname TEXT NOT NULL DEFAULT ''")
            if "permissions" not in columns:
                db.execute("ALTER TABLE users ADD COLUMN permissions TEXT NOT NULL DEFAULT '[]'")
            if "last_login" not in columns:
                db.execute("ALTER TABLE users ADD COLUMN last_login TEXT NOT NULL DEFAULT ''")

    def seed_demo_users(self, users: list[dict[str, Any]]) -> None:
        passwords = {"admin": "admin123", "student01": "student123", "teacher01": "teacher123"}
        with self._connection() as db:
            for item in users:
                permissions = json.dumps(item.get("permissions", []), ensure_ascii=False)
                existing = db.execute(
                    "SELECT id FROM users WHERE id = ? OR account = ? COLLATE NOCASE",
                    (item["id"], item["account"]),
                ).fetchone()
                if existing:
                    db.execute(
                        """UPDATE users SET name = ?, department = ?, permissions = ?, last_login = ?
                        WHERE id = ?""",
                        (
                            item["name"], item.get("department", ""), permissions,
                            item.get("last_login", ""), existing["id"],
                        ),
                    )
                    continue
                password = passwords.get(item["account"], secrets.token_urlsafe(32))
                db.execute(
                    """INSERT OR IGNORE INTO users
                    (id, account, name, email, password_hash, role, status, email_verified, department, permissions, last_login, created_at)
                    VALUES (?, ?, ?, NULL, ?, ?, ?, 1, ?, ?, ?, ?)""",
                    (
                        item["id"], item["account"], item["name"], hash_password(password),
                        item["role"], item["status"], item.get("department", ""), permissions,
                        item.get("last_login", ""), _iso(_now()),
                    ),
                )

    @staticmethod
    def public_user(row: sqlite3.Row) -> dict[str, Any]:
        try:
            permissions = json.loads(row["permissions"] or "[]")
        except (json.JSONDecodeError, TypeError):
            permissions = []
        return {
            "id": row["id"], "name": row["name"], "nickname": row["nickname"] or row["name"], "account": row["account"],
            "email": row["email"] or "", "role": row["role"], "status": row["status"],
            "department": row["department"], "permissions": permissions,
        }

    def register(self, account: str, name: str, email: str, password: str, role: str, nickname: str | None = None) -> tuple[dict[str, Any], str]:
        nickname = self.validate_nickname(nickname if nickname is not None else name)
        if not name.strip():
            raise ValueError("请填写真实姓名")
        account, name, email = account.strip(), name.strip(), email.strip().lower()
        if role not in {"student", "teacher"}:
            raise ValueError("仅支持注册学生或教师账号")
        with self._connection() as db:
            if db.execute("SELECT 1 FROM users WHERE account = ? COLLATE NOCASE", (account,)).fetchone():
                raise ValueError("用户名已被使用")
            if db.execute("SELECT 1 FROM users WHERE email = ? COLLATE NOCASE", (email,)).fetchone():
                raise ValueError("该邮箱已注册")
            user_id = f"u_{uuid4().hex}"
            db.execute(
                """INSERT INTO users
                (id, account, name, email, password_hash, role, status, email_verified, created_at)
                VALUES (?, ?, ?, ?, ?, ?, 'email_pending', 0, ?)""",
                (user_id, account, name, email, hash_password(password), role, _iso(_now())),
            )
            db.execute("UPDATE users SET nickname=? WHERE id=?", (nickname,user_id))
            token = self._create_verification_code(db, user_id)
            row = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return self.public_user(row), token

    @staticmethod
    def validate_nickname(value: str) -> str:
        import unicodedata
        value = value.strip()
        if not 1 <= len(value) <= 40 or any(unicodedata.category(c) in {"Cc", "Cs"} for c in value):
            raise ValueError("昵称需为1至40个字符，不能包含换行或控制字符")
        return value

    def update_nickname(self, user_id: str, nickname: str) -> dict[str, Any]:
        nickname = self.validate_nickname(nickname)
        with self._connection() as db:
            row=db.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
            if not row:
                raise ValueError("账号不存在")
            db.execute("UPDATE users SET nickname=? WHERE id=?", (nickname,user_id))
            return self.public_user(db.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone())

    def _create_verification_code(self, db: sqlite3.Connection, user_id: str) -> str:
        now = _now()
        recent = db.execute("SELECT * FROM email_verification_codes WHERE user_id = ? AND created_at > ? ORDER BY created_at DESC", (user_id, _iso(now - timedelta(hours=1)))).fetchall()
        if len(recent) >= 5:
            raise ValueError("发送过于频繁，请一小时后重试")
        if any(not row["delivery_failed"] and datetime.fromisoformat(row["created_at"]) > now - timedelta(seconds=60) for row in recent):
            raise ValueError("请等待60秒后再发送验证码")
        previous = db.execute("SELECT code_hash FROM email_verification_codes WHERE user_id=? ORDER BY created_at DESC LIMIT 1", (user_id,)).fetchone()
        code = f"{secrets.randbelow(1000000):06d}"
        while previous and verify_password(code, previous["code_hash"]):
            code = f"{secrets.randbelow(1000000):06d}"
        db.execute("UPDATE email_verification_codes SET used_at=? WHERE user_id=? AND used_at IS NULL", (_iso(now), user_id))
        db.execute("INSERT INTO email_verification_codes(id,user_id,code_hash,expires_at,created_at) VALUES(?,?,?,?,?)", (uuid4().hex,user_id,hash_password(code),_iso(now+timedelta(minutes=10)),_iso(now)))
        return code

    def verification_delivery_failed(self, email: str, code: str) -> None:
        with self._connection() as db:
            db.execute("BEGIN IMMEDIATE")
            row=db.execute("SELECT c.* FROM email_verification_codes c JOIN users u ON u.id=c.user_id WHERE u.email=? COLLATE NOCASE ORDER BY c.created_at DESC LIMIT 1", (email.strip(),)).fetchone()
            if row and verify_password(code,row["code_hash"]):
                db.execute("UPDATE email_verification_codes SET delivery_failed=1,used_at=? WHERE id=?", (_iso(_now()),row["id"]))

    def verify_email_code(self, email: str, code: str) -> dict[str, Any]:
        error = None
        user = None
        with self._connection() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT c.*,u.role,u.status,u.email_verified FROM email_verification_codes c JOIN users u ON u.id=c.user_id WHERE u.email=? COLLATE NOCASE ORDER BY c.created_at DESC LIMIT 1", (email.strip(),)).fetchone()
            if not row or row["used_at"] or row["delivery_failed"] or row["email_verified"] or datetime.fromisoformat(row["expires_at"]) <= _now():
                error = "验证码无效或已过期，请重新获取"
            elif row["attempts"] >= 5:
                error = "验证码错误次数已达上限，请重新获取"
            elif not verify_password(code, row["code_hash"]):
                db.execute("UPDATE email_verification_codes SET attempts=attempts+1 WHERE id=?", (row["id"],))
                error = "验证码错误次数已达上限，请重新获取" if row["attempts"] >= 4 else "验证码不正确，请检查后重试"
            elif row["status"] != "email_pending":
                error = "账号当前不可用，请联系管理员"
            else:
                status="active" if row["role"] == "student" else "pending_review"
                db.execute("UPDATE users SET email_verified=1,status=? WHERE id=?", (status,row["user_id"]))
                db.execute("UPDATE email_verification_codes SET used_at=? WHERE user_id=? AND used_at IS NULL", (_iso(_now()),row["user_id"]))
                db.execute("UPDATE auth_tokens SET used_at=? WHERE user_id=? AND purpose='verify_email' AND used_at IS NULL", (_iso(_now()),row["user_id"]))
                user=db.execute("SELECT * FROM users WHERE id=?",(row["user_id"],)).fetchone()
        # Raise after committing so incorrect-attempt counters cannot roll back.
        if error:
            raise ValueError(error)
        return self.public_user(user)

    def _create_token(self, db: sqlite3.Connection, user_id: str, purpose: str, minutes: int) -> str:
        cutoff = _iso(_now() - timedelta(hours=1))
        recent = db.execute(
            "SELECT COUNT(*) FROM auth_tokens WHERE user_id = ? AND purpose = ? AND created_at > ?",
            (user_id, purpose, cutoff),
        ).fetchone()[0]
        if recent >= 5:
            raise ValueError("请求过于频繁，请一小时后重试")
        token = secrets.token_urlsafe(32)
        db.execute(
            "INSERT INTO auth_tokens VALUES (?, ?, ?, ?, ?, ?, NULL)",
            (uuid4().hex, user_id, _token_hash(token), purpose, _iso(_now() + timedelta(minutes=minutes)), _iso(_now())),
        )
        return token

    def verify_email(self, token: str) -> dict[str, Any]:
        with self._connection() as db:
            row = db.execute(
                """SELECT t.*, u.role FROM auth_tokens t JOIN users u ON u.id = t.user_id
                WHERE t.token_hash = ? AND t.purpose = 'verify_email'""", (_token_hash(token),)
            ).fetchone()
            if not row or row["used_at"] or datetime.fromisoformat(row["expires_at"]) < _now():
                raise ValueError("验证链接无效或已过期")
            status = "active" if row["role"] == "student" else "pending_review"
            db.execute("UPDATE auth_tokens SET used_at = ? WHERE id = ?", (_iso(_now()), row["id"]))
            db.execute("UPDATE users SET email_verified = 1, status = ? WHERE id = ?", (status, row["user_id"]))
            db.execute("UPDATE auth_tokens SET used_at = ? WHERE user_id = ? AND purpose = 'verify_email' AND used_at IS NULL", (_iso(_now()), row["user_id"]))
            user = db.execute("SELECT * FROM users WHERE id = ?", (row["user_id"],)).fetchone()
        return self.public_user(user)

    def create_verification(self, email: str) -> tuple[str, str] | None:
        with self._connection() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT * FROM users WHERE email = ? COLLATE NOCASE AND email_verified = 0",
                (email.strip(),),
            ).fetchone()
            if not row:
                return None
            return row["email"], self._create_verification_code(db, row["id"])

    def login(self, account: str, password: str, requested_role: str) -> tuple[str, dict[str, Any]]:
        with self._connection() as db:
            row = db.execute(
                "SELECT * FROM users WHERE account = ? COLLATE NOCASE OR email = ? COLLATE NOCASE",
                (account.strip(), account.strip()),
            ).fetchone()
            if not row and account.strip().lower() in {"student", "teacher"}:
                row = db.execute("SELECT * FROM users WHERE account = ?", (account.strip().lower() + "01",)).fetchone()
            if not row or not verify_password(password, row["password_hash"]):
                raise ValueError("账号或密码错误")
            effective_role = "admin" if row["role"] == "super_admin" else row["role"]
            if effective_role != requested_role:
                raise ValueError("该账号不属于当前选择的身份")
            if not row["email_verified"]:
                raise ValueError("请先完成邮箱验证")
            if row["status"] == "pending_review":
                raise ValueError("教师账号正在等待管理员审核")
            if row["status"] != "active":
                raise ValueError("账号当前不可用")
            token = secrets.token_urlsafe(40)
            db.execute(
                "INSERT INTO sessions VALUES (?, ?, ?, ?, ?, NULL)",
                (uuid4().hex, row["id"], _token_hash(token), _iso(_now() + timedelta(days=7)), _iso(_now())),
            )
        return token, self.public_user(row)

    def authenticated_user(self, token: str) -> dict[str, Any] | None:
        with self._connection() as db:
            row = db.execute(
                """SELECT u.* FROM sessions s JOIN users u ON u.id = s.user_id
                WHERE s.token_hash = ? AND s.revoked_at IS NULL AND s.expires_at > ?""",
                (_token_hash(token), _iso(_now())),
            ).fetchone()
        return self.public_user(row) if row else None

    def logout(self, token: str) -> None:
        with self._connection() as db:
            db.execute("UPDATE sessions SET revoked_at = ? WHERE token_hash = ?", (_iso(_now()), _token_hash(token)))

    def create_password_reset(self, email: str) -> tuple[str, str] | None:
        with self._connection() as db:
            row = db.execute("SELECT * FROM users WHERE email = ? COLLATE NOCASE AND email_verified = 1", (email.strip(),)).fetchone()
            if not row:
                return None
            token = self._create_token(db, row["id"], "reset_password", 15)
            return row["email"], token

    def reset_password(self, token: str, password: str) -> None:
        with self._connection() as db:
            row = db.execute(
                "SELECT * FROM auth_tokens WHERE token_hash = ? AND purpose = 'reset_password'",
                (_token_hash(token),),
            ).fetchone()
            if not row or row["used_at"] or datetime.fromisoformat(row["expires_at"]) < _now():
                raise ValueError("重置链接无效或已过期")
            db.execute("UPDATE users SET password_hash = ? WHERE id = ?", (hash_password(password), row["user_id"]))
            db.execute("UPDATE auth_tokens SET used_at = ? WHERE id = ?", (_iso(_now()), row["id"]))
            db.execute("UPDATE sessions SET revoked_at = ? WHERE user_id = ? AND revoked_at IS NULL", (_iso(_now()), row["user_id"]))
            db.execute("UPDATE auth_tokens SET used_at = ? WHERE user_id = ? AND purpose = 'reset_password' AND used_at IS NULL", (_iso(_now()), row["user_id"]))

    def list_users(self) -> list[dict[str, Any]]:
        with self._connection() as db:
            rows = db.execute("SELECT * FROM users ORDER BY created_at DESC").fetchall()
        return [self.public_user(row) for row in rows]

    def review_teacher(self, user_id: str, approved: bool) -> dict[str, Any]:
        with self._connection() as db:
            row = db.execute("SELECT * FROM users WHERE id = ? AND role = 'teacher'", (user_id,)).fetchone()
            if not row:
                raise ValueError("教师账号不存在")
            if not row["email_verified"]:
                raise ValueError("该账号尚未完成邮箱验证")
            status = "active" if approved else "rejected"
            db.execute("UPDATE users SET status = ? WHERE id = ?", (status, user_id))
            if not approved:
                db.execute("UPDATE sessions SET revoked_at = ? WHERE user_id = ? AND revoked_at IS NULL", (_iso(_now()), user_id))
            updated = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return self.public_user(updated)
