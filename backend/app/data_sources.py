from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"


def load_data_file(name: str) -> Any:
    return json.loads((DATA_DIR / name).read_text(encoding="utf-8"))


def load_data_sources() -> list[dict[str, Any]]:
    return load_data_file("data_sources.json")


def load_admin_users() -> list[dict[str, Any]]:
    return load_data_file("admin_users.json")


def load_textbook_pathways() -> list[dict[str, Any]]:
    return load_data_file("textbook_pathways.json")
