from __future__ import annotations

from typing import Any

from .vector_store import MockVectorAdapter


class HybridRetriever:
    def __init__(self, adapter: MockVectorAdapter) -> None:
        self.adapter = adapter

    def retrieve(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        return self.adapter.search(query, limit)
