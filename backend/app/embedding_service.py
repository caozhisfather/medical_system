from __future__ import annotations


class EmbeddingService:
    def embed_text_mock(self, text: str) -> list[float]:
        base = sum(ord(char) for char in text[:96]) or 1
        return [round(((base + index * 23) % 101) / 100, 3) for index in range(12)]

    def batch_embed_mock(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_text_mock(text) for text in texts]

    def reserve_real_provider_adapter(self) -> dict[str, str]:
        return {"status": "pending", "adapter": "replace with real embedding provider configured in env/.env"}
