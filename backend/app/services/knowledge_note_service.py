from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any
from uuid import uuid4


class KnowledgeNoteService:
    """Store per-account textbook notes with atomic JSON updates."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._lock = RLock()

    def _read_unlocked(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return []
        return payload if isinstance(payload, list) else []

    def _write_unlocked(self, notes: list[dict[str, Any]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_name(f".{self.path.name}.{uuid4().hex}.tmp")
        try:
            temporary.write_text(
                json.dumps(notes, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            os.replace(temporary, self.path)
        finally:
            if temporary.exists():
                temporary.unlink()

    def list(
        self,
        account: str,
        document_id: str = "",
        page: int = 0,
    ) -> list[dict[str, Any]]:
        with self._lock:
            notes = self._read_unlocked()
        return [
            item
            for item in notes
            if item.get("account") == account
            and (not document_id or item.get("document_id") == document_id)
            and (not page or item.get("page") == page)
        ]

    def upsert(
        self,
        account: str,
        payload: dict[str, Any],
        note_id: str | None = None,
    ) -> dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        with self._lock:
            notes = self._read_unlocked()
            resolved_id = note_id or uuid4().hex
            note = {
                "id": resolved_id,
                "account": account,
                **payload,
                "updated_at": now,
            }
            notes = [
                item
                for item in notes
                if not (
                    item.get("id") == resolved_id
                    and item.get("account") == account
                )
            ]
            notes.append(note)
            self._write_unlocked(notes)
        return note

    def delete(self, account: str, note_id: str) -> None:
        with self._lock:
            notes = self._read_unlocked()
            remaining = [
                item
                for item in notes
                if not (
                    item.get("id") == note_id
                    and item.get("account") == account
                )
            ]
            self._write_unlocked(remaining)
