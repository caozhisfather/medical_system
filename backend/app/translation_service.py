from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"


class TranslationService:
    def __init__(self) -> None:
        graph = json.loads((DATA_DIR / "medical_kg_bilingual.json").read_text(encoding="utf-8"))
        self.nodes = graph["nodes"]

    def search_terms(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        q = query.lower().strip()
        if not q:
            return []
        matches: list[dict[str, Any]] = []
        for node in self.nodes:
            text = " ".join([
                node.get("id", ""),
                node.get("label", ""),
                node.get("label_zh", ""),
                node.get("label_en", ""),
                " ".join(node.get("aliases_zh", [])),
                " ".join(node.get("aliases_en", [])),
                node.get("description_zh", ""),
                node.get("description_en", ""),
                node.get("embedding_text_zh", ""),
                node.get("embedding_text_en", ""),
            ]).lower()
            if q in text or any(token and token.lower() in text for token in query.split()):
                matches.append({
                    "id": node["id"],
                    "type": node.get("type", node.get("group", "")),
                    "label_zh": node.get("label_zh", node.get("label", "")),
                    "label_en": node.get("label_en", node.get("label", "")),
                    "aliases_zh": node.get("aliases_zh", []),
                    "aliases_en": node.get("aliases_en", []),
                })
        return matches[:limit]

    @staticmethod
    def localized_label(item: dict[str, Any], lang: str = "zh") -> str:
        if lang == "en":
            return item.get("label_en") or item.get("title_en") or item.get("label") or item.get("title") or item.get("id", "")
        return item.get("label_zh") or item.get("title_zh") or item.get("label") or item.get("title") or item.get("id", "")
