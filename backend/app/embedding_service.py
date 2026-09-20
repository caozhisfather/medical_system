from __future__ import annotations

import json
from urllib.request import Request, urlopen

from .config import settings


class EmbeddingService:
    @property
    def model(self) -> str:
        return settings.embedding_model

    def configured(self) -> bool:
        return bool(settings.embedding_api_key and settings.embedding_base_url and settings.embedding_model)

    def encode(self, texts: list[str], batch_size: int = 8):
        """Use the configured OpenAI-compatible embedding endpoint."""
        if not self.configured():
            raise RuntimeError("embedding provider is not configured")
        body = json.dumps({"model": self.model, "input": texts}, ensure_ascii=False).encode("utf-8")
        request = Request(
            f"{settings.embedding_base_url.rstrip('/')}/v1/embeddings",
            data=body,
            headers={"Authorization": f"Bearer {settings.embedding_api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=settings.embedding_timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
        items = sorted(payload.get("data", []), key=lambda item: item.get("index", 0))
        if len(items) != len(texts):
            raise RuntimeError("embedding provider returned an incomplete result")
        import numpy as np
        return np.asarray([item["embedding"] for item in items], dtype=np.float32)
    def embed_text_mock(self, text: str) -> list[float]:
        base = sum(ord(char) for char in text[:96]) or 1
        return [round(((base + index * 23) % 101) / 100, 3) for index in range(12)]

    def batch_embed_mock(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_text_mock(text) for text in texts]

    def reserve_real_provider_adapter(self) -> dict[str, str]:
        return {"status": "pending", "adapter": "replace with real embedding provider configured in env/.env"}


embedding_service = EmbeddingService()
