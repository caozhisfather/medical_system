from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from ..config import ROOT_DIR
from .case_deidentifier import deidentify_text
from .case_library_importer import import_case_library


class CaseKnowledgeService:
    """De-identified case knowledge base with file-backed CRUD persistence."""

    def __init__(self) -> None:
        self.file = ROOT_DIR / "data" / "case_knowledge_base.json"
        self.textbook_file = ROOT_DIR / "data" / "anatomy_textbook.json"
        self.textbook_overrides_file = ROOT_DIR / "data" / "anatomy_textbook_overrides.json"
        self._lock = threading.Lock()
        self._entries: dict[str, dict[str, Any]] = {}
        self._textbook_overrides: dict[str, dict[str, Any]] = {}
        self._load()

    def _load(self) -> None:
        if not self.file.exists():
            self._entries = {}
            return
        payload = json.loads(self.file.read_text(encoding="utf-8"))
        items = payload.get("entries", []) if isinstance(payload, dict) else payload
        self._entries = {item["id"]: item for item in items if isinstance(item, dict) and item.get("id")}
        if self.textbook_overrides_file.exists():
            payload = json.loads(self.textbook_overrides_file.read_text(encoding="utf-8"))
            self._textbook_overrides = payload.get("overrides", {}) if isinstance(payload, dict) else {}

    def _textbook_entries(self) -> list[dict[str, Any]]:
        if not self.textbook_file.exists():
            return []
        payload = json.loads(self.textbook_file.read_text(encoding="utf-8"))
        source = payload.get("source", "《系统解剖学》（第10版）")
        result = []
        for page in payload.get("pages", []):
            page_no = page.get("page")
            entry_id = f"tb_page_{page_no}"
            override = self._textbook_overrides.get(entry_id, {})
            if override.get("deleted"):
                continue
            result.append({
                "id": entry_id,
                "knowledge_type": "textbook",
                "title": override.get("title") or f"{page.get('chapter') or '教材内容'} · 第 {page_no} 页",
                "category": override.get("category") or "教材章节",
                "diagnosis": "",
                "chief_complaint": "",
                "present_illness": "",
                "content": override.get("content") or page.get("text", ""),
                "source": override.get("source") or f"{source} · 第 {page_no} 页",
                "status": override.get("status") or "已索引",
                "processing_status": override.get("processing_status") or "已发布",
                "anonymized": True,
                "imported": True,
                "pii_removed": [],
                "risk_flags": [],
                "embedding_status": "待重建" if override else "已生成",
                "created_at": override.get("created_at") or "",
                "updated_at": override.get("updated_at") or "",
                "page": page_no,
                "chapter": page.get("chapter", ""),
            })
        for entry_id, override in self._textbook_overrides.items():
            if not entry_id.startswith("tb_custom_") or override.get("deleted"):
                continue
            result.append({**override, "id": entry_id, "knowledge_type": "textbook", "embedding_status": "待生成"})
        return result

    def _persist(self) -> None:
        entries = sorted(self._entries.values(), key=lambda item: item.get("updated_at", ""), reverse=True)
        self.file.write_text(
            json.dumps({"version": 1, "entries": entries}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat(timespec="seconds")

    def list(self, q: str | None = None, category: str | None = None) -> list[dict[str, Any]]:
        with self._lock:
            entries = list(self._entries.values())
        if category:
            entries = [item for item in entries if item.get("category") == category]
        if q:
            query = q.strip().lower()
            entries = [
                item
                for item in entries
                if query
                in " ".join(
                    str(item.get(key, ""))
                    for key in ("title", "category", "diagnosis", "chief_complaint", "present_illness")
                ).lower()
            ]
        return sorted(entries, key=lambda item: item.get("updated_at", ""), reverse=True)

    def list_teaching(self, q: str | None = None, category: str | None = None, knowledge_type: str | None = None) -> list[dict[str, Any]]:
        entries = [{**item, "knowledge_type": item.get("knowledge_type", "case")} for item in self._entries.values()] + self._textbook_entries()
        if knowledge_type in {"case", "textbook"}:
            entries = [item for item in entries if item.get("knowledge_type", "case") == knowledge_type]
        if category:
            entries = [item for item in entries if item.get("category") == category]
        if q:
            query = q.strip().lower()
            entries = [item for item in entries if query in " ".join(str(item.get(key, "")) for key in ("title", "category", "content", "diagnosis")).lower()]
        return sorted(entries, key=lambda item: item.get("updated_at", ""), reverse=True)

    def teaching_categories(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for item in list(self._entries.values()) + self._textbook_entries():
            category = item.get("category") or "未分类"
            counts[category] = counts.get(category, 0) + 1
        return dict(sorted(counts.items(), key=lambda pair: pair[1], reverse=True))

    def teaching_get(self, entry_id: str) -> dict[str, Any]:
        if entry_id.startswith("tb_"):
            for item in self._textbook_entries():
                if item["id"] == entry_id:
                    return item
            raise KeyError(entry_id)
        return self.get(entry_id)

    def teaching_create(self, payload: dict[str, Any]) -> dict[str, Any]:
        if payload.get("knowledge_type", "case") != "textbook":
            return self.create(payload)
        now = self._now()
        entry_id = f"tb_custom_{uuid4().hex[:10]}"
        entry = {"id": entry_id, "knowledge_type": "textbook", "title": payload.get("title", "未命名教材条目").strip(), "category": payload.get("category", "教材补充").strip(), "content": payload.get("content", "").strip(), "source": payload.get("source", "教师手工录入").strip(), "status": payload.get("status", "待审核"), "processing_status": payload.get("processing_status", "待审核"), "document_id": payload.get("document_id", entry_id), "document_type": payload.get("document_type", "textbook"), "document_scope": payload.get("document_scope", "whole_document"), "created_at": now, "updated_at": now, "anonymized": True, "imported": False, "pii_removed": [], "risk_flags": [], "embedding_status": "待生成"}
        with self._lock:
            self._textbook_overrides[entry_id] = entry
            self._persist_textbook_overrides()
        return entry

    def teaching_update(self, entry_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        if not entry_id.startswith("tb_"):
            return self.update(entry_id, payload)
        current = self.teaching_get(entry_id)
        now = self._now()
        updated = {**current, **{key: value for key, value in payload.items() if value is not None}, "updated_at": now, "embedding_status": "待重建"}
        self._textbook_overrides[entry_id] = updated
        self._persist_textbook_overrides()
        return updated

    def teaching_delete(self, entry_id: str) -> None:
        if not entry_id.startswith("tb_"):
            return self.delete(entry_id)
        self.teaching_get(entry_id)
        self._textbook_overrides[entry_id] = {"deleted": True, "updated_at": self._now()}
        self._persist_textbook_overrides()

    def _persist_textbook_overrides(self) -> None:
        self.textbook_overrides_file.write_text(json.dumps({"version": 1, "overrides": self._textbook_overrides}, ensure_ascii=False, indent=2), encoding="utf-8")

    def categories(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        with self._lock:
            for item in self._entries.values():
                category = item.get("category") or "未分类"
                counts[category] = counts.get(category, 0) + 1
        return dict(sorted(counts.items(), key=lambda pair: pair[1], reverse=True))

    def get(self, entry_id: str) -> dict[str, Any]:
        with self._lock:
            entry = self._entries.get(entry_id)
        if entry is None:
            raise KeyError(entry_id)
        return dict(entry)

    @staticmethod
    def _mask_field(value: str) -> str:
        return deidentify_text(value).text

    def create(self, payload: dict[str, Any]) -> dict[str, Any]:
        now = self._now()
        entry = {
            "id": f"ckb_{uuid4().hex[:10]}",
            "title": (payload.get("title") or "").strip() or "未命名病例",
            "category": (payload.get("category") or "未分类").strip(),
            "diagnosis": self._mask_field((payload.get("diagnosis") or "").strip()),
            "chief_complaint": self._mask_field((payload.get("chief_complaint") or "").strip()),
            "present_illness": self._mask_field((payload.get("present_illness") or "").strip()),
            "content": self._mask_field((payload.get("content") or "").strip()),
            "source": (payload.get("source") or "教师手工录入").strip(),
            "status": (payload.get("status") or "已脱敏入库").strip(),
            "processing_status": (payload.get("processing_status") or "待审核").strip(),
            "anonymized": True,
            "imported": False,
            "pii_removed": [],
            "risk_flags": [],
            "created_at": now,
            "updated_at": now,
        }
        with self._lock:
            self._entries[entry["id"]] = entry
            self._persist()
        return dict(entry)

    def update(self, entry_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            entry = self._entries.get(entry_id)
            if entry is None:
                raise KeyError(entry_id)
            allowed = ("title", "category", "diagnosis", "chief_complaint", "present_illness", "content", "source", "status", "processing_status")
            for key in allowed:
                if key in payload and payload[key] is not None:
                    value = str(payload[key]).strip()
                    entry[key] = self._mask_field(value) if key in {"diagnosis", "chief_complaint", "present_illness", "content"} else value
            entry["anonymized"] = True
            entry["updated_at"] = self._now()
            self._persist()
            return dict(entry)

    def delete(self, entry_id: str) -> None:
        with self._lock:
            if entry_id not in self._entries:
                raise KeyError(entry_id)
            del self._entries[entry_id]
            self._persist()

    def deidentify_preview(self, text: str) -> dict[str, Any]:
        result = deidentify_text(text)
        return {
            "original_length": len(text),
            "masked_length": len(result.text),
            "masked_text": result.text,
            "pii_types": result.pii_types,
            "counts": result.counts,
            "risk_flags": result.risk_flags,
        }

    def import_from_dir(self, source_dir: str) -> dict[str, Any]:
        entries, report = import_case_library(source_dir)
        with self._lock:
            self._entries = {item_id: item for item_id, item in self._entries.items() if not item.get("imported")}
            for entry in entries:
                self._entries[entry["id"]] = entry
            self._persist()
        report["total"] = len(self._entries)
        return report
