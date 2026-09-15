from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"


def _load(name: str) -> Any:
    return json.loads((DATA_DIR / name).read_text(encoding="utf-8"))


class KnowledgeGraphService:
    def __init__(self) -> None:
        bilingual = DATA_DIR / "medical_kg_bilingual.json"
        self.graph = _load("medical_kg_bilingual.json") if bilingual.exists() else _load("medical_kg.json")
        self.nodes = self.graph["nodes"]
        self.edges = self.graph["edges"]

    def get_node(self, node_id: str) -> dict[str, Any] | None:
        return next((node for node in self.nodes if node["id"] == node_id), None)

    def _node_text(self, node: dict[str, Any]) -> str:
        return " ".join([
            node.get("id", ""),
            node.get("label", ""),
            node.get("label_zh", ""),
            node.get("label_en", ""),
            node.get("summary", ""),
            node.get("description_zh", ""),
            node.get("description_en", ""),
            node.get("embedding_text", ""),
            node.get("embedding_text_zh", ""),
            node.get("embedding_text_en", ""),
            " ".join(node.get("aliases_zh", [])),
            " ".join(node.get("aliases_en", [])),
            " ".join(node.get("source_ids", [])),
            " ".join(node.get("related_case_ids", [])),
            " ".join(node.get("related_knowledge_ids", [])),
        ]).lower()

    @staticmethod
    def label(node: dict[str, Any], lang: str = "zh") -> str:
        if lang == "en":
            return node.get("label_en") or node.get("label") or node.get("id", "")
        return node.get("label_zh") or node.get("label") or node.get("id", "")

    def search_nodes(self, query: str = "", node_type: str = "", lang: str = "zh") -> list[dict[str, Any]]:
        q = query.lower().strip()
        result = []
        for node in self.nodes:
            node_group = node.get("group") or node.get("type")
            type_ok = not node_type or node_type == "全部" or node_group == node_type or node.get("type") == node_type
            query_ok = not q or q in self._node_text(node) or any(token and token.lower() in self._node_text(node) for token in query.split())
            if type_ok and query_ok:
                result.append({**node, "label": self.label(node, lang), "group": node_group})
        return result[:30]

    def get_neighbors(self, node_id: str, depth: int = 1, lang: str = "zh") -> dict[str, Any]:
        frontier = {node_id}
        seen = {node_id}
        selected_edges = []
        for _ in range(max(depth, 1)):
            next_frontier = set()
            for edge in self.edges:
                if edge["source"] in frontier or edge["target"] in frontier:
                    selected_edges.append({
                        **edge,
                        "relation": edge.get("relation_en") if lang == "en" else edge.get("relation_zh", edge.get("relation", "关联")),
                    })
                    next_frontier.add(edge["source"])
                    next_frontier.add(edge["target"])
            frontier = next_frontier - seen
            seen |= next_frontier
        nodes = []
        for node in self.nodes:
            if node["id"] in seen:
                node_group = node.get("group") or node.get("type")
                nodes.append({**node, "label": self.label(node, lang), "group": node_group})
        return {"nodes": nodes, "edges": selected_edges}

    def build_learning_path(self, query: str, lang: str = "zh") -> list[str]:
        nodes = self.search_nodes(query, lang=lang)[:8]
        if not nodes:
            nodes = [
                {**node, "label": self.label(node, lang), "group": node.get("group") or node.get("type")}
                for node in self.nodes[:8]
            ]
        return [node["label"] for node in nodes[:8]]
