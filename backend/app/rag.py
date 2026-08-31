from __future__ import annotations

from typing import Any

from .models import Citation
from .rag_modules import ChromaAdapter, HybridRetriever, MilvusAdapter, MockEmbeddingService, MockVectorAdapter, load_documents, split_documents, to_citations


class RagPipeline:
    def __init__(self, provider: str = "mock") -> None:
        self.provider = provider
        self.embedding_service = MockEmbeddingService()
        self.documents = load_documents()
        self.chunks = split_documents(self.documents)
        if provider == "milvus":
            self.adapter: MockVectorAdapter = MilvusAdapter()
        elif provider == "chroma":
            self.adapter = ChromaAdapter()
        else:
            self.adapter = MockVectorAdapter()
        for chunk in self.chunks:
            chunk["embedding"] = self.embedding_service.embed(chunk.get("content", ""))
        self.adapter.add_documents(self.chunks)
        self.retriever = HybridRetriever(self.adapter)

    def load_documents(self) -> list[dict[str, Any]]:
        return self.documents

    def chunk_documents(self, documents: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return split_documents(documents)

    def embed(self, text: str) -> list[float]:
        return self.embedding_service.embed(text)

    def write_vector_store(self) -> dict[str, Any]:
        return {"provider": self.adapter.name, "documents": len(self.documents), "chunks": len(self.chunks), "status": "mock_index_ready"}

    def retrieve_documents(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        return self.retriever.retrieve(query, limit)

    def retrieve(self, query: str, limit: int = 3) -> list[Citation]:
        return to_citations(self.retrieve_documents(query, limit))

    def answer(self, question: str, scenario: str) -> tuple[str, list[Citation], list[str]]:
        citations = self.retrieve(f"{scenario} {question}", limit=4)
        titles = "、".join(c.title for c in citations)
        answer = (
            f"围绕“{scenario}”，参考依据包括：{titles}。"
            "建议把学习任务拆成病史采集、检查选择、鉴别诊断、临床决策、指南依据和沟通表达。"
            "本回答仅用于医学教育训练，不用于真实临床诊断。"
        )
        safety_notes = [
            "AI标准化病人只能依据虚拟病例脚本回答，不能主动泄露诊断。",
            "所有反馈均用于教学训练，不构成诊疗建议。",
            "真实病例接入前必须脱敏、授权并经过教师复核。",
        ]
        return answer, citations, safety_notes
