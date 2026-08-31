from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from ..config import ROOT_DIR


_DEPT_RE = re.compile(r"《([^》]+)》")
_SECTION_RE = re.compile(r"^(问诊要点|鉴别诊断问诊要点|鉴别诊断|查体|辅助检查|诊疗经过|诊疗计划|主诉|现病史|诊断|临床表现|治疗计划)")


class HistoryTakingService:
    """Disease-indexed interview templates extracted from the standardized history-taking notes."""

    def __init__(self) -> None:
        self.file = ROOT_DIR / "data" / "history_taking_standard.txt"
        self.source = "《内科规培技能问诊总结》"
        self.entries: list[dict[str, Any]] = []
        self._load()

    def _load(self) -> None:
        if not self.file.exists():
            return
        text = self.file.read_text(encoding="utf-8")
        self.entries = self._parse(text)

    def _parse(self, text: str) -> list[dict[str, Any]]:
        entries: list[dict[str, Any]] = []
        department = ""
        current: dict[str, Any] | None = None
        section = "正文"

        def flush() -> None:
            nonlocal current
            if current and (current["title"] or current["sections"]):
                entries.append(current)
            current = None

        for line in text.splitlines():
            stripped = line.strip()
            dept_match = _DEPT_RE.search(stripped)
            if dept_match and len(stripped) <= 12:
                flush()
                department = dept_match.group(1).strip()
                continue
            if not stripped:
                flush()
                continue
            section_match = _SECTION_RE.match(stripped)
            if section_match:
                if current is None:
                    current = {"department": department, "title": "", "sections": {}}
                section = section_match.group(1)
                remainder = stripped[len(section_match.group(0)):].lstrip("：: ").strip()
                if remainder:
                    current["sections"][section] = remainder
                continue
            if current is None or not current["title"]:
                if current is None:
                    current = {"department": department, "title": "", "sections": {}}
                if len(stripped) <= 28 and not current["title"]:
                    current["title"] = stripped
                    continue
            existing = current["sections"].get(section, "")
            current["sections"][section] = f"{existing} {stripped}".strip() if existing else stripped
        flush()
        return entries

    def search(self, query: str) -> dict[str, Any] | None:
        keyword = re.sub(r"\s+", "", (query or "").strip())
        if not keyword:
            return None
        title_match = next((item for item in self.entries if item["title"] and keyword in re.sub(r"\s+", "", item["title"])), None)
        if title_match:
            return self._format(title_match)
        for item in self.entries:
            haystack = re.sub(r"\s+", "", " ".join(f"{key} {value}" for key, value in item["sections"].items()))
            if keyword and keyword[:4] in haystack:
                return self._format(item)
        return None

    def _format(self, item: dict[str, Any]) -> dict[str, Any]:
        return {
            "department": item.get("department", ""),
            "title": item.get("title", ""),
            "sections": item.get("sections", {}),
            "source": f"{self.source} · {item.get('department', '未标注科室')} · {item.get('title', '未命名模板')}",
        }


history_taking_service = HistoryTakingService()
