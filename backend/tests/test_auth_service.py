from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.app.services.auth_service import AuthService


class AuthServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.service = AuthService(Path(self.temporary.name) / "auth.sqlite3")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_student_registration_verification_login_and_logout(self) -> None:
        user, verification_token = self.service.register(
            "student_new", "测试学生", "student@example.com", "Medical123", "student"
        )
        self.assertEqual(user["status"], "email_pending")
        verified = self.service.verify_email(verification_token)
        self.assertEqual(verified["status"], "active")

        session_token, logged_in = self.service.login("student@example.com", "Medical123", "student")
        self.assertEqual(logged_in["account"], "student_new")
        self.assertIsNotNone(self.service.authenticated_user(session_token))

        self.service.logout(session_token)
        self.assertIsNone(self.service.authenticated_user(session_token))

    def test_password_reset_revokes_existing_sessions(self) -> None:
        _, verification_token = self.service.register(
            "student_reset", "重置学生", "reset@example.com", "Medical123", "student"
        )
        self.service.verify_email(verification_token)
        session_token, _ = self.service.login("student_reset", "Medical123", "student")
        _, reset_token = self.service.create_password_reset("reset@example.com") or (None, None)
        self.assertIsNotNone(reset_token)
        self.service.reset_password(reset_token, "NewMedical456")
        self.assertIsNone(self.service.authenticated_user(session_token))
        self.service.login("student_reset", "NewMedical456", "student")

    def test_teacher_requires_admin_review(self) -> None:
        user, verification_token = self.service.register(
            "teacher_new", "测试教师", "teacher@example.com", "Medical123", "teacher"
        )
        verified = self.service.verify_email(verification_token)
        self.assertEqual(verified["status"], "pending_review")
        with self.assertRaisesRegex(ValueError, "等待管理员审核"):
            self.service.login("teacher_new", "Medical123", "teacher")
        approved = self.service.review_teacher(user["id"], True)
        self.assertEqual(approved["status"], "active")
        self.service.login("teacher_new", "Medical123", "teacher")

    def test_tokens_are_single_use(self) -> None:
        _, token = self.service.register(
            "student_once", "一次验证", "once@example.com", "Medical123", "student"
        )
        self.service.verify_email(token)
        with self.assertRaisesRegex(ValueError, "无效或已过期"):
            self.service.verify_email(token)

    def test_old_verification_cannot_undo_teacher_review(self) -> None:
        user, old_token = self.service.register("teacher_tokens", "Test Teacher", "tokens@example.com", "Medical123", "teacher")
        _, new_token = self.service.create_verification("tokens@example.com")
        self.service.verify_email(new_token)
        self.service.review_teacher(user["id"], True)
        with self.assertRaises(ValueError):
            self.service.verify_email(old_token)
        self.service.login("teacher_tokens", "Medical123", "teacher")

    def test_reset_invalidates_other_reset_links(self) -> None:
        _, verification = self.service.register("reset_tokens", "Test Student", "resets@example.com", "Medical123", "student")
        self.service.verify_email(verification)
        _, old_token = self.service.create_password_reset("resets@example.com")
        _, new_token = self.service.create_password_reset("resets@example.com")
        self.service.reset_password(new_token, "NewMedical456")
        with self.assertRaises(ValueError):
            self.service.reset_password(old_token, "WrongMedical456")

    def test_demo_seed_preserves_latest_user_directory(self) -> None:
        users = [
            {
                "id": "u_admin", "account": "admin", "name": "Admin", "role": "super_admin",
                "status": "active", "department": "System", "last_login": "Demo",
                "permissions": ["users", "graph"],
            },
            {
                "id": "u_teacher_02", "account": "teacher02", "name": "Teacher 2", "role": "teacher",
                "status": "active", "department": "Anatomy", "last_login": "2026-09-17",
                "permissions": ["dashboard"],
            },
        ]
        self.service.seed_demo_users(users)
        seeded = {user["account"]: user for user in self.service.list_users()}
        self.assertEqual(set(seeded), {"admin", "teacher02"})
        self.assertEqual(seeded["admin"]["permissions"], ["users", "graph"])
        self.assertEqual(seeded["teacher02"]["department"], "Anatomy")
        self.service.login("admin", "admin123", "admin")
        with self.assertRaises(ValueError):
            self.service.login("teacher02", "teacher123", "teacher")


if __name__ == "__main__":
    unittest.main()
