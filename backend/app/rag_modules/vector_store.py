from __future__ import annotations

import re
from typing import Any


def tokenize(text: str) -> set[str]:
    text = text.lower()
    tokens = set(re.findall(r"[A-Za-z0-9_]+", text))
    for keyword in ["胸痛", "心电图", "肌钙蛋白", "急性冠脉综合征", "主动脉夹层", "肺栓塞", "解剖", "心脏", "胃", "腹痛", "指南", "诊断学"]:
        if keyword.lower() in text:
            tokens.add(keyword.lower())
    return tokens


class MockVectorAdapter:
    name = "mock"

    def __init__(self) -> None:
        self.documents: list[dict[str, Any]] = []

    def add_documents(self, documents: list[dict[str, Any]]) -> None:
        self.documents = documents

    def search(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        query_tokens = tokenize(query)
        ranked: list[tuple[int, dict[str, Any]]] = []
        for doc in self.documents:
            fields = [doc.get("title", ""), doc.get("content", ""), doc.get("summary", "")]
            fields.extend(doc.get("keywords", []))
            fields.extend(doc.get("tags", []))
            score = len(query_tokens & tokenize(" ".join(fields)))
            ranked.append((score, doc))
        ranked.sort(key=lambda item: item[0], reverse=True)
        selected = [doc for score, doc in ranked if score > 0][:limit]
        return selected or self.documents[:limit]


class ChromaAdapter(MockVectorAdapter):
    name = "chroma"


class MilvusAdapter(MockVectorAdapter):
    name = "milvus"
