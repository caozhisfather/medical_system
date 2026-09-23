from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class AnatomyLearningService:
    """Persist spatial anatomy attempts and mistake summaries per account."""

    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path, timeout=10)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS anatomy_attempts (
                    id TEXT PRIMARY KEY,
                    account TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    exercise_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    system TEXT NOT NULL,
                    organ TEXT NOT NULL DEFAULT '',
                    target TEXT NOT NULL,
                    selected_zone TEXT NOT NULL,
                    correct INTEGER NOT NULL,
                    score INTEGER NOT NULL,
                    feedback TEXT NOT NULL,
                    explanation TEXT NOT NULL,
                    clinical_link TEXT NOT NULL,
                    image_node_id TEXT NOT NULL DEFAULT '',
                    target_structure_id TEXT NOT NULL DEFAULT '',
                    click_x REAL,
                    click_y REAL,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_anatomy_attempts_account_created
                    ON anatomy_attempts(account, created_at DESC);
                CREATE INDEX IF NOT EXISTS idx_anatomy_attempts_account_exercise
                    ON anatomy_attempts(account, exercise_id, created_at DESC);
                CREATE TABLE IF NOT EXISTS quiz_attempts (
                    id TEXT PRIMARY KEY,
                    account TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    question_id TEXT NOT NULL,
                    quiz_id TEXT NOT NULL DEFAULT '',
                    structure_en TEXT NOT NULL DEFAULT '',
                    structure_cn TEXT NOT NULL DEFAULT '',
                    structure_label TEXT NOT NULL DEFAULT '',
                    system TEXT NOT NULL DEFAULT '',
                    question_type TEXT NOT NULL DEFAULT '',
                    question_stem TEXT NOT NULL DEFAULT '',
                    question_options TEXT NOT NULL DEFAULT '[]',
                    answer TEXT NOT NULL DEFAULT '',
                    correct_answer TEXT NOT NULL DEFAULT '',
                    correct INTEGER NOT NULL,
                    score INTEGER NOT NULL,
                    feedback TEXT NOT NULL DEFAULT '',
                    hit_points TEXT NOT NULL DEFAULT '[]',
                    missed_points TEXT NOT NULL DEFAULT '[]',
                    citation TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(account, question_id)
                );
                CREATE INDEX IF NOT EXISTS idx_quiz_attempts_account_updated
                    ON quiz_attempts(account, updated_at DESC);
                CREATE INDEX IF NOT EXISTS idx_quiz_attempts_account_correct
                    ON quiz_attempts(account, correct, updated_at DESC);
                """
            )

    def record(
        self,
        *,
        account: str,
        user_id: str,
        exercise: dict[str, Any],
        selected_zone: str,
        correct: bool,
        score: int,
        feedback: str,
        explanation: str,
        clinical_link: str,
        image_node_id: str = "",
        target_structure_id: str = "",
        click_x: float | None = None,
        click_y: float | None = None,
    ) -> dict[str, Any]:
        attempt_id = f"anatomy-{uuid4().hex[:12]}"
        created_at = _now()
        payload = {
            "id": attempt_id,
            "account": account,
            "user_id": user_id,
            "exercise_id": str(exercise.get("id", "")),
            "title": str(exercise.get("title", "")),
            "system": str(exercise.get("system", "")),
            "organ": str(exercise.get("organ", "")),
            "target": str(exercise.get("target", "")),
            "selected_zone": selected_zone,
            "correct": 1 if correct else 0,
            "score": int(score),
            "feedback": feedback,
            "explanation": explanation,
            "clinical_link": clinical_link,
            "image_node_id": image_node_id,
            "target_structure_id": target_structure_id,
            "click_x": click_x,
            "click_y": click_y,
            "created_at": created_at,
        }
        with self._connect() as db:
            db.execute(
                """
                INSERT INTO anatomy_attempts (
                    id, account, user_id, exercise_id, title, system, organ, target,
                    selected_zone, correct, score, feedback, explanation, clinical_link,
                    image_node_id, target_structure_id, click_x, click_y, created_at
                ) VALUES (
                    :id, :account, :user_id, :exercise_id, :title, :system, :organ, :target,
                    :selected_zone, :correct, :score, :feedback, :explanation, :clinical_link,
                    :image_node_id, :target_structure_id, :click_x, :click_y, :created_at
                )
                """,
                payload,
            )
        payload["correct"] = correct
        return payload

    @staticmethod
    def _public_attempt(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "id": row["id"],
            "exercise_id": row["exercise_id"],
            "title": row["title"],
            "system": row["system"],
            "organ": row["organ"],
            "target": row["target"],
            "selected_zone": row["selected_zone"],
            "correct": bool(row["correct"]),
            "score": row["score"],
            "feedback": row["feedback"],
            "explanation": row["explanation"],
            "clinical_link": row["clinical_link"],
            "image_node_id": row["image_node_id"],
            "target_structure_id": row["target_structure_id"],
            "click_x": row["click_x"],
            "click_y": row["click_y"],
            "created_at": row["created_at"],
        }

    def records(self, account: str, limit: int = 80) -> dict[str, Any]:
        safe_limit = max(1, min(limit, 200))
        with self._connect() as db:
            rows = db.execute(
                """
                SELECT * FROM anatomy_attempts
                WHERE account = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (account, safe_limit),
            ).fetchall()
            summary = db.execute(
                """
                SELECT
                    COUNT(*) AS total,
                    COALESCE(SUM(correct), 0) AS correct_count,
                    COALESCE(ROUND(AVG(score)), 0) AS average_score
                FROM anatomy_attempts
                WHERE account = ?
                """,
                (account,),
            ).fetchone()
        total = int(summary["total"] or 0)
        correct_count = int(summary["correct_count"] or 0)
        return {
            "items": [self._public_attempt(row) for row in rows],
            "summary": {
                "total": total,
                "correct": correct_count,
                "accuracy": round(correct_count / total * 100) if total else 0,
                "average_score": int(summary["average_score"] or 0),
            },
        }

    @staticmethod
    def _answer_text(question: dict[str, Any], answer: Any) -> str:
        if question.get("type") == "single_choice":
            options = question.get("options") or []
            try:
                index = int(answer)
                return str(options[index])
            except (TypeError, ValueError, IndexError):
                return str(answer or "")
        if question.get("type") == "true_false":
            return "正确" if answer is True else "错误" if answer is False else ""
        return str(answer or "").strip()

    @staticmethod
    def _correct_answer_text(question: dict[str, Any], result: dict[str, Any]) -> str:
        expected = str(result.get("expected") or "").strip()
        if expected:
            return expected
        if question.get("type") == "single_choice":
            options = question.get("options") or []
            try:
                return str(options[int(question.get("answer_index"))])
            except (TypeError, ValueError, IndexError):
                return ""
        if question.get("type") == "true_false":
            return "正确" if question.get("answer") else "错误"
        return "、".join(str(point) for point in (question.get("points") or []))

    def record_quiz(
        self,
        *,
        account: str,
        user_id: str,
        question: dict[str, Any],
        answer: Any,
        result: dict[str, Any],
        quiz_id: str = "",
    ) -> dict[str, Any]:
        now = _now()
        payload = {
            "id": f"quiz-{uuid4().hex[:12]}",
            "account": account,
            "user_id": user_id,
            "question_id": str(question.get("id") or ""),
            "quiz_id": quiz_id,
            "structure_en": str(question.get("structure_en") or ""),
            "structure_cn": str(question.get("structure_cn") or ""),
            "structure_label": str(question.get("structure_label") or ""),
            "system": str(question.get("system") or ""),
            "question_type": str(question.get("type") or ""),
            "question_stem": str(question.get("stem") or ""),
            "question_options": json.dumps(question.get("options") or [], ensure_ascii=False),
            "answer": self._answer_text(question, answer),
            "correct_answer": self._correct_answer_text(question, result),
            "correct": 1 if result.get("correct") else 0,
            "score": int(result.get("score") or 0),
            "feedback": str(result.get("feedback") or ""),
            "hit_points": json.dumps(result.get("hit_points") or [], ensure_ascii=False),
            "missed_points": json.dumps(result.get("missed_points") or [], ensure_ascii=False),
            "citation": str(question.get("citation") or ""),
            "created_at": now,
            "updated_at": now,
        }
        with self._connect() as db:
            db.execute(
                """
                INSERT INTO quiz_attempts (
                    id, account, user_id, question_id, quiz_id, structure_en,
                    structure_cn, structure_label, system, question_type,
                    question_stem, question_options, answer, correct_answer,
                    correct, score, feedback, hit_points, missed_points,
                    citation, created_at, updated_at
                ) VALUES (
                    :id, :account, :user_id, :question_id, :quiz_id, :structure_en,
                    :structure_cn, :structure_label, :system, :question_type,
                    :question_stem, :question_options, :answer, :correct_answer,
                    :correct, :score, :feedback, :hit_points, :missed_points,
                    :citation, :created_at, :updated_at
                )
                ON CONFLICT(account, question_id) DO UPDATE SET
                    user_id = excluded.user_id,
                    quiz_id = excluded.quiz_id,
                    structure_en = excluded.structure_en,
                    structure_cn = excluded.structure_cn,
                    structure_label = excluded.structure_label,
                    system = excluded.system,
                    question_type = excluded.question_type,
                    question_stem = excluded.question_stem,
                    question_options = excluded.question_options,
                    answer = excluded.answer,
                    correct_answer = excluded.correct_answer,
                    correct = excluded.correct,
                    score = excluded.score,
                    feedback = excluded.feedback,
                    hit_points = excluded.hit_points,
                    missed_points = excluded.missed_points,
                    citation = excluded.citation,
                    updated_at = excluded.updated_at
                """,
                payload,
            )
        return {**payload, "correct": bool(payload["correct"])}

    @staticmethod
    def _public_quiz_attempt(row: sqlite3.Row) -> dict[str, Any]:
        def json_list(value: str) -> list[Any]:
            try:
                payload = json.loads(value or "[]")
                return payload if isinstance(payload, list) else []
            except json.JSONDecodeError:
                return []

        return {
            "id": row["id"],
            "question_id": row["question_id"],
            "quiz_id": row["quiz_id"],
            "structure_en": row["structure_en"],
            "structure_cn": row["structure_cn"],
            "structure_label": row["structure_label"],
            "system": row["system"],
            "question_type": row["question_type"],
            "question_stem": row["question_stem"],
            "question_options": json_list(row["question_options"]),
            "answer": row["answer"],
            "correct_answer": row["correct_answer"],
            "correct": bool(row["correct"]),
            "score": row["score"],
            "feedback": row["feedback"],
            "hit_points": json_list(row["hit_points"]),
            "missed_points": json_list(row["missed_points"]),
            "citation": row["citation"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    def quiz_records(self, account: str, limit: int = 80) -> dict[str, Any]:
        safe_limit = max(1, min(limit, 200))
        with self._connect() as db:
            rows = db.execute(
                """
                SELECT * FROM quiz_attempts
                WHERE account = ?
                ORDER BY updated_at DESC
                LIMIT ?
                """,
                (account, safe_limit),
            ).fetchall()
            summary = db.execute(
                """
                SELECT
                    COUNT(*) AS total,
                    COALESCE(SUM(correct), 0) AS correct_count,
                    COALESCE(ROUND(AVG(score)), 0) AS average_score
                FROM quiz_attempts
                WHERE account = ?
                """,
                (account,),
            ).fetchone()
        total = int(summary["total"] or 0)
        correct_count = int(summary["correct_count"] or 0)
        return {
            "items": [self._public_quiz_attempt(row) for row in rows],
            "summary": {
                "total": total,
                "correct": correct_count,
                "accuracy": round(correct_count / total * 100) if total else 0,
                "average_score": int(summary["average_score"] or 0),
            },
        }

    def quiz_mistakes(self, account: str, limit: int = 80) -> dict[str, Any]:
        safe_limit = max(1, min(limit, 200))
        with self._connect() as db:
            rows = db.execute(
                """
                SELECT * FROM quiz_attempts
                WHERE account = ? AND correct = 0
                ORDER BY updated_at DESC
                LIMIT ?
                """,
                (account, safe_limit),
            ).fetchall()
        return {"items": [self._public_quiz_attempt(row) for row in rows]}

    def mistakes(self, account: str, limit: int = 80) -> dict[str, Any]:
        safe_limit = max(1, min(limit, 200))
        with self._connect() as db:
            rows = db.execute(
                """
                SELECT
                    exercise_id,
                    title,
                    system,
                    organ,
                    target,
                    COUNT(*) AS attempt_count,
                    MAX(score) AS best_score,
                    MIN(score) AS worst_score,
                    MAX(created_at) AS latest_at,
                    (
                        SELECT explanation FROM anatomy_attempts AS inner_attempt
                        WHERE inner_attempt.account = outer_attempt.account
                          AND inner_attempt.exercise_id = outer_attempt.exercise_id
                          AND inner_attempt.correct = 0
                        ORDER BY inner_attempt.created_at DESC
                        LIMIT 1
                    ) AS explanation,
                    (
                        SELECT clinical_link FROM anatomy_attempts AS inner_attempt
                        WHERE inner_attempt.account = outer_attempt.account
                          AND inner_attempt.exercise_id = outer_attempt.exercise_id
                          AND inner_attempt.correct = 0
                        ORDER BY inner_attempt.created_at DESC
                        LIMIT 1
                    ) AS clinical_link
                FROM anatomy_attempts AS outer_attempt
                WHERE account = ? AND correct = 0
                GROUP BY exercise_id, title, system, organ, target
                ORDER BY latest_at DESC
                LIMIT ?
                """,
                (account, safe_limit),
            ).fetchall()
        return {
            "items": [
                {
                    "exercise_id": row["exercise_id"],
                    "title": row["title"],
                    "system": row["system"],
                    "organ": row["organ"],
                    "target": row["target"],
                    "attempt_count": int(row["attempt_count"]),
                    "best_score": int(row["best_score"] or 0),
                    "worst_score": int(row["worst_score"] or 0),
                    "latest_at": row["latest_at"],
                    "explanation": row["explanation"],
                    "clinical_link": row["clinical_link"],
                }
                for row in rows
            ]
        }
