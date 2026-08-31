from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import numpy as np

from ..config import settings


class EmbeddingService:
    """Embedding API client with an OpenAI-compatible request contract."""

    def __init__(self) -> None:
        self.model = settings.embedding_model
        self.base_url = settings.embedding_base_url.rstrip("/")
        self.api_key = settings.embedding_api_key
        self.timeout = settings.embedding_timeout

    def configured(self) -> bool:
        return bool(self.api_key and self.base_url and self.model)

    def encode(self, texts: list[str], batch_size: int = 16) -> np.ndarray:
        if not texts:
            return np.empty((0, 0), dtype=np.float32)
        if not self.configured():
            raise RuntimeError("Embedding API 未配置，请设置 EMBEDDING_API_KEY")

        vectors: list[list[float]] = []
        for start in range(0, len(texts), max(1, batch_size)):
            batch = [text[:8000] for text in texts[start : start + batch_size]]
            payload = self._request(batch)
            vectors.extend(self._extract_vectors(payload))
        array = np.asarray(vectors, dtype=np.float32)
        norms = np.linalg.norm(array, axis=1, keepdims=True)
        return array / np.clip(norms, 1e-12, None)

    def _request(self, texts: list[str]) -> dict[str, Any]:
        body = json.dumps(
            {"model": self.model, "input": texts, "encoding_format": "float"},
            ensure_ascii=False,
        ).encode("utf-8")
        endpoint = self.base_url if self.base_url.endswith("/v1") else f"{self.base_url}/v1"
        request = Request(
            f"{endpoint}/embeddings",
            data=body,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:300]
            raise RuntimeError(f"Embedding API HTTP {exc.code}: {detail}") from exc
        except (URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"Embedding API 请求失败: {exc}") from exc

    @staticmethod
    def _extract_vectors(payload: dict[str, Any]) -> list[list[float]]:
        data = payload.get("data")
        if not isinstance(data, list):
            raise RuntimeError("Embedding API 返回缺少 data")
        ordered = sorted(data, key=lambda item: item.get("index", 0))
        vectors = [item.get("embedding") for item in ordered]
        if not vectors or any(not isinstance(vector, list) for vector in vectors):
            raise RuntimeError("Embedding API 返回的 embedding 格式无效")
        return vectors


embedding_service = EmbeddingService()
