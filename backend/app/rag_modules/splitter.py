from __future__ import annotations

from typing import Any


def split_documents(documents: list[dict[str, Any]], chunk_size: int = 180) -> list[dict[str, Any]]:
    chunks: list[dict[str, Any]] = []
    for doc in documents:
        content = doc.get("content") or doc.get("summary") or ""
        for index, start in enumerate(range(0, max(len(content), 1), chunk_size)):
            chunk_text = content[start : start + chunk_size] or content
            chunks.append({**doc, "id": f"{doc['id']}-chunk-{index}", "content": chunk_text, "chunk_index": index})
    return chunks
