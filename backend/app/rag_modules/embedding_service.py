from __future__ import annotations


class MockEmbeddingService:
    def embed(self, text: str) -> list[float]:
        base = sum(ord(char) for char in text[:80]) or 1
        return [round(((base + index * 19) % 101) / 100, 3) for index in range(8)]
