from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = ROOT_DIR / "data"


def load_documents() -> list[dict[str, Any]]:
    documents: list[dict[str, Any]] = []
    for name in ["guidelines.json", "knowledge.json"]:
        path = DATA_DIR / name
        if path.exists():
            documents.extend(json.loads(path.read_text(encoding="utf-8")))
    return documents
