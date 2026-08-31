from __future__ import annotations

from typing import Any

from ..models import Citation


def to_citations(documents: list[dict[str, Any]]) -> list[Citation]:
    citations: list[Citation] = []
    for doc in documents:
        snippet = doc.get("content") or doc.get("summary") or ""
        citations.append(Citation(id=doc["id"], title=doc["title"], source=doc.get("source", "教学示例知识库"), snippet=snippet[:180]))
    return citations
