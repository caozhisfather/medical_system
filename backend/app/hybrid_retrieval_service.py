from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .embedding_service import EmbeddingService
from .knowledge_graph_service import KnowledgeGraphService
from .translation_service import TranslationService

ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"


def _load(name: str) -> Any:
    return json.loads((DATA_DIR / name).read_text(encoding="utf-8"))


class HybridRetrievalService:
    def __init__(self) -> None:
        self.knowledge = _load("knowledge.json")
        self.cases = _load("cases.json")
        self.anatomy = _load("anatomy.json")
        self.graph = KnowledgeGraphService()
        self.embedding = EmbeddingService()
        self.translation = TranslationService()

    def _knowledge_text(self, item: dict[str, Any]) -> str:
        return " ".join([
            item.get("id", ""),
            item.get("title", ""),
            item.get("title_zh", ""),
            item.get("title_en", ""),
            item.get("summary", ""),
            item.get("summary_zh", ""),
            item.get("summary_en", ""),
            item.get("category", ""),
            item.get("type", ""),
            item.get("source_type", ""),
            item.get("source_name", ""),
            item.get("data_source", ""),
            item.get("embedding_text", ""),
            item.get("embedding_text_zh", ""),
            item.get("embedding_text_en", ""),
            " ".join(item.get("keywords", [])),
            " ".join(item.get("keywords_en", [])),
            " ".join(item.get("related_symptoms", [])),
            " ".join(item.get("related_diseases", [])),
            " ".join(item.get("related_exams", [])),
            " ".join(item.get("related_anatomy", [])),
            " ".join(item.get("related_cases", [])),
        ]).lower()

    def keyword_search(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        q = query.lower().strip()
        ranked = []
        terms = [query, q, *query.split()]
        for item in self.knowledge:
            text = self._knowledge_text(item)
            score = sum(2 for token in terms if token and token.lower() in text)
            score += sum(1 for token in item.get("keywords", []) + item.get("keywords_en", []) if token and token.lower() in q)
            if score:
                ranked.append((score, item))
        ranked.sort(key=lambda pair: pair[0], reverse=True)
        return [item for _, item in ranked[:limit]] or self.knowledge[:limit]

    def vector_search_mock(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        qv = self.embedding.embed_text_mock(query)
        scored = []
        for item in self.knowledge:
            iv = item.get("embedding_text_zh") or item.get("embedding_text") or item.get("summary", "")
            ev = self.embedding.embed_text_mock(iv)
            score = sum(a * b for a, b in zip(qv, ev))
            scored.append((score, item))
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [item for _, item in scored[:limit]]

    def graph_expand(self, query: str, lang: str = "zh") -> dict[str, Any]:
        nodes = self.graph.search_nodes(query, lang=lang)[:8]
        if not nodes:
            nodes = self.graph.search_nodes("胸痛", lang=lang)[:4]
        expanded_nodes = []
        expanded_edges = []
        for node in nodes[:5]:
            neighbors = self.graph.get_neighbors(node["id"], depth=1, lang=lang)
            expanded_nodes.extend(neighbors["nodes"])
            expanded_edges.extend(neighbors["edges"])
        seen = set()
        unique_nodes = []
        for node in expanded_nodes:
            if node["id"] not in seen:
                unique_nodes.append(node)
                seen.add(node["id"])
        return {"nodes": unique_nodes[:24], "edges": expanded_edges[:36]}

    def related_cases(self, query: str) -> list[dict[str, Any]]:
        q = query.lower()
        result = []
        for case in self.cases:
            text = " ".join([case["title"], case["chief_complaint"], " ".join(case.get("differential_diagnoses", [])), " ".join(case.get("graph_node_ids", []))]).lower()
            if q in text or any(part in text for part in ["胸痛", "腹痛", "发热", "呼吸困难", "黄疸", "头痛", "贫血", "糖尿病", "chest", "acs"] if part in q):
                result.append(case)
        return result[:5]

    def related_anatomy(self, query: str) -> list[dict[str, Any]]:
        q = query.lower()
        result = []
        for item in self.anatomy:
            text = " ".join([item["title"], item.get("system", ""), item["target"], item["clinical_link"], " ".join(item.get("graph_node_ids", []))]).lower()
            if q in text or any(part in text for part in ["心", "肺", "肝", "胃", "脑", "肾", "腹", "黄疸", "胸痛", "呼吸", "heart", "lung", "liver"] if part in q):
                result.append(item)
        return result[:6]

    def rerank(self, keyword_items: list[dict[str, Any]], vector_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        merged = []
        seen = set()
        for item in keyword_items + vector_items:
            if item["id"] not in seen:
                merged.append(item)
                seen.add(item["id"])
        return merged[:12]

    def query(self, question: str, lang: str = "zh") -> dict[str, Any]:
        keyword_items = self.keyword_search(question)
        vector_items = self.vector_search_mock(question)
        matched = self.rerank(keyword_items, vector_items)
        graph = self.graph_expand(question, lang=lang)
        return {
            "matched_knowledge": matched,
            "graph_nodes": graph["nodes"],
            "graph_edges": graph["edges"],
            "bilingual_terms": self.translation.search_terms(question),
            "related_cases": self.related_cases(question),
            "related_anatomy_exercises": self.related_anatomy(question),
            "recommended_learning_path": self.graph.build_learning_path(question, lang=lang),
        }
