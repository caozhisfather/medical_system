from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Protocol

from .models import Citation

ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"


def tokenize(text: str) -> set[str]:
    tokens = set(re.findall(r"[A-Za-z0-9_]+", text.lower()))
    for keyword in ["胸痛", "心电图", "肌钙蛋白", "急性冠脉综合征", "主动脉夹层", "肺栓塞", "问诊", "指南", "诊断学"]:
        if keyword.lower() in text.lower():
            tokens.add(keyword.lower())
    return tokens


class VectorStoreAdapter(Protocol):
    def add_documents(self, documents: list[dict[str, Any]]) -> None: ...
    def search(self, query: str, limit: int = 3) -> list[dict[str, Any]]: ...


class MockChromaAdapter:
    def __init__(self) -> None:
        self.documents: list[dict[str, Any]] = []

    def add_documents(self, documents: list[dict[str, Any]]) -> None:
        self.documents = documents

    def search(self, query: str, limit: int = 3) -> list[dict[str, Any]]:
        query_tokens = tokenize(query)
        ranked: list[tuple[int, dict[str, Any]]] = []
        for doc in self.documents:
            haystack = " ".join([doc.get("title", ""), doc.get("content", ""), " ".join(doc.get("tags", []))])
            ranked.append((len(query_tokens & tokenize(haystack)), doc))
        ranked.sort(key=lambda item: item[0], reverse=True)
        selected = [doc for score, doc in ranked if score > 0][:limit]
        return selected or self.documents[:limit]


class MockMilvusAdapter(MockChromaAdapter):
    pass


class RagPipeline:
    def __init__(self, provider: str = "chroma") -> None:
        self.provider = provider
        self.documents = self.load_documents()
        self.adapter: VectorStoreAdapter = MockMilvusAdapter() if provider == "milvus" else MockChromaAdapter()
        self.adapter.add_documents(self.chunk_documents(self.documents))

    def load_documents(self) -> list[dict[str, Any]]:
        return json.loads((DATA_DIR / "guidelines.json").read_text(encoding="utf-8"))

    def chunk_documents(self, documents: list[dict[str, Any]]) -> list[dict[str, Any]]:
        chunks: list[dict[str, Any]] = []
        for doc in documents:
            content = doc["content"]
            for index, start in enumerate(range(0, len(content), 120)):
                chunks.append({**doc, "id": f"{doc['id']}-chunk-{index}", "content": content[start : start + 180]})
        return chunks

    def embed(self, text: str) -> list[float]:
        base = sum(ord(char) for char in text[:64]) or 1
        return [round(((base + index * 17) % 101) / 100, 3) for index in range(8)]

    def write_vector_store(self) -> dict[str, Any]:
        return {"provider": self.provider, "documents": len(self.documents), "chunks": len(self.adapter.search("胸痛", 20))}

    def retrieve(self, query: str, limit: int = 3) -> list[Citation]:
        docs = self.adapter.search(query, limit)
        return [Citation(id=doc["id"], title=doc["title"], source=doc["source"], snippet=doc["content"][:180]) for doc in docs]

    def answer(self, question: str, scenario: str) -> tuple[str, list[Citation], list[str]]:
        citations = self.retrieve(f"{scenario} {question}")
        titles = "、".join(c.title for c in citations)
        answer = (
            f"围绕“{scenario}”，系统已检索指南与教材依据：{titles}。"
            "建议将学生表现拆为病史采集、检查选择、鉴别诊断、临床决策、指南依据和沟通表达六个维度评分。"
            "本回答仅用于医学教育训练，不用于真实临床诊断。"
        )
        safety_notes = [
            "AI标准化病人只能依据虚拟病例脚本回答，不能主动泄露诊断。",
            "所有反馈均用于教学训练，不构成诊疗建议。",
            "真实病例接入前必须脱敏、授权并经过教师复核。",
        ]
        return answer, citations, safety_notes
