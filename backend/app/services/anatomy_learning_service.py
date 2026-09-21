from __future__ import annotations

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
