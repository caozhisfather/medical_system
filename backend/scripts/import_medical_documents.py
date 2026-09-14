"""Register external medical PDFs as whole-document knowledge assets.

The original files stay in their supplied directories. This script writes only
metadata and processing state into data/document_library.json, so it is safe to
rerun after adding more textbooks or guidelines.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

try:
    from pypdf import PdfReader
except ImportError:  # pragma: no cover
    PdfReader = None

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "document_library.json"
SOURCES = [
    (Path(r"E:\18_本科计算机专业课程笔记\07_竞赛\全球人工智能算法精英赛\教科书籍\书籍"), "textbook", "教材"),
    (Path(r"E:\18_本科计算机专业课程笔记\07_竞赛\全球人工智能算法精英赛\奈特解剖图谱\奈特解剖图谱"), "textbook", "解剖图谱"),
    (Path(r"E:\18_本科计算机专业课程笔记\07_竞赛\全球人工智能算法精英赛\全科室临床指南中（英文版）\全科室临床指南（中英文版）"), "evidence", "临床指南"),
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    existing = json.loads(DATA.read_text(encoding="utf-8")) if DATA.exists() else {"version": 1, "documents": []}
    documents = {item.get("file_hash"): item for item in existing.get("documents", []) if item.get("file_hash")}
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    added = 0
    skipped = 0
    for directory, document_type, category in SOURCES:
        if not directory.exists():
            continue
        for path in sorted(directory.rglob("*.pdf")):
            file_hash = sha256(path)
            if file_hash in documents:
                skipped += 1
                continue
            pages = None
            if PdfReader is not None:
                try:
                    pages = len(PdfReader(str(path), strict=False).pages)
                except Exception:
                    pages = None
            title = path.stem
            entry = {
                "id": f"doc_{file_hash[:12]}",
                "document_id": f"doc_{file_hash[:12]}",
                "document_type": document_type,
                "knowledge_type": "textbook" if document_type == "textbook" else "textbook",
                "document_scope": "whole_document",
                "title": title,
                "category": category,
                "source": str(path),
                "source_path": str(path),
                "file_hash": file_hash,
                "page_count": pages,
                "content": "",
                "status": "待OCR",
                "processing_status": "OCR 待处理",
                "ocr_status": "pending",
                "embedding_status": "待生成",
                "graph_status": "待更新",
                "anonymized": True,
                "imported": True,
                "pii_removed": [],
                "risk_flags": [],
                "created_at": now,
                "updated_at": now,
            }
            documents[file_hash] = entry
            added += 1
    result = {"version": 1, "updated_at": now, "documents": list(documents.values())}
    DATA.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"added": added, "skipped": skipped, "total": len(documents)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
