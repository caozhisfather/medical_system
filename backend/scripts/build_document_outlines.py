"""Build a book-level table of contents from OCR output.

The knowledge library owns one record per book, guideline or case source.
This script only adds an outline to that record; individual PDF pages remain
internal evidence locations used by retrieval and citations.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LIBRARY = ROOT / "data" / "document_library.json"

HEADING_PATTERNS = (
    re.compile(r"^(第[一二三四五六七八九十百0-9]+[编篇章节部分卷].{1,70})$"),
    re.compile(r"^((?:Chapter|CHAPTER|Part|SECTION)\s+[0-9IVXLC]+.{0,70})$"),
    re.compile(r"^([0-9]{1,2}(?:\.[0-9]{1,2}){0,3}\s+.{2,70})$"),
)


def compact(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def find_heading(text: str) -> str | None:
    for raw in text.splitlines()[:18]:
        line = compact(raw)
        if not (3 <= len(line) <= 76):
            continue
        if any(pattern.match(line) for pattern in HEADING_PATTERNS):
            return line
    return None


def fallback_title(text: str, page: int) -> str:
    first = next((compact(line) for line in text.splitlines() if compact(line)), "")
    if first:
        return first[:48]
    return f"第 {page} 页内容"


def make_outline(pages: list[dict]) -> tuple[list[dict], str]:
    sections: list[dict] = []
    for record in pages:
        page = int(record.get("page") or len(sections) + 1)
        text = record.get("text") or ""
        heading = find_heading(text)
        if heading:
            if sections:
                sections[-1]["end_page"] = max(sections[-1]["start_page"], page - 1)
            sections.append({"title": heading, "start_page": page, "end_page": page, "level": 1})
    if not sections and pages:
        # A scanned or poorly structured book still has one readable whole-book card.
        first_page = int(pages[0].get("page") or 1)
        last_page = int(pages[-1].get("page") or len(pages))
        sections = [{"title": fallback_title(pages[0].get("text") or "", first_page), "start_page": first_page, "end_page": last_page, "level": 1}]
    elif sections:
        last_page = int(pages[-1].get("page") or len(pages))
        sections[-1]["end_page"] = max(sections[-1]["start_page"], last_page)
    first_text = " ".join(compact(item.get("text") or "") for item in pages[:3])
    summary = first_text[:260] or "已完成文本提取，可按目录层级检索本书内容。"
    return sections[:80], summary


def main() -> None:
    payload = json.loads(LIBRARY.read_text(encoding="utf-8"))
    built = missing = 0
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    for document in payload.get("documents", []):
        raw_path = document.get("ocr_text_path")
        path = ROOT / raw_path if raw_path and not Path(raw_path).is_absolute() else Path(raw_path or "")
        if not path.is_file():
            missing += 1
            continue
        pages = json.loads(path.read_text(encoding="utf-8")).get("pages", [])
        outline, summary = make_outline(pages)
        document["content_structure"] = "whole_document_outline"
        document["outline"] = outline
        document["outline_status"] = "completed"
        document["content_summary"] = summary
        document["updated_at"] = now
        built += 1
    payload["updated_at"] = now
    LIBRARY.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"outlined": built, "missing_ocr": missing}, ensure_ascii=False))


if __name__ == "__main__":
    main()
