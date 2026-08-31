from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import numpy as np

from ..config import ROOT_DIR
from .embedding_service import embedding_service


class AnatomyTextbookService:
    """Searches the locally extracted systematic anatomy textbook by page text."""

    def __init__(self) -> None:
        self.file = ROOT_DIR / "data" / "anatomy_textbook.json"
        self.emb_file = ROOT_DIR / "data" / "anatomy_textbook_embeddings.npy"
        self.meta_file = ROOT_DIR / "data" / "anatomy_textbook_embeddings.json"
        self.source = "《系统解剖学》（第10版）"
        self.pages: list[dict[str, Any]] = []
        self._embeddings: np.ndarray | None = None
        self._meta: list[dict[str, Any]] = []
        self._load()

    def _load(self) -> None:
        if not self.file.exists():
            return
        payload = json.loads(self.file.read_text(encoding="utf-8"))
        self.source = payload.get("source", self.source)
        self.pages = payload.get("pages", [])
        self._load_embeddings()

    def _load_embeddings(self) -> None:
        if not self.emb_file.exists() or not self.meta_file.exists():
            return
        try:
            self._embeddings = np.load(self.emb_file)
            self._meta = json.loads(self.meta_file.read_text(encoding="utf-8"))
        except Exception:
            self._embeddings = None
            self._meta = []

    def search(self, query: str) -> dict[str, Any] | None:
        keyword = re.sub(r"\s+", "", query.strip())
        if not keyword:
            return None

        # Prefer an exact textbook hit so citations remain deterministic.
        variants = self._variants(keyword)
        for variant in variants:
            match = self._find_passage(variant)
            if match:
                return match

        # Fall back to semantic search for natural-language questions.
        semantic = self._search_semantic(keyword)
        if semantic:
            return semantic
        return None

    def _search_semantic(self, query: str) -> dict[str, Any] | None:
        if self._embeddings is None or len(self._meta) == 0 or len(self.pages) == 0:
            return None
        try:
            query_emb = embedding_service.encode([query], batch_size=1)[0]
            scores = self._embeddings @ query_emb
            top_idx = int(np.argmax(scores))
            top_score = float(scores[top_idx])
            if top_score < 0.25:
                return None
            meta = self._meta[top_idx]
            page_idx = meta.get("index", top_idx)
            if page_idx < 0 or page_idx >= len(self.pages):
                return None
            item = self.pages[page_idx]
            text = item.get("text", "")
            chapter = meta.get("chapter") or item.get("chapter") or self._nearest_chapter(item)
            return {
                "query": query,
                "title": chapter or query,
                "content": self._best_passage(text, query),
                "page": item.get("page"),
                "chapter": chapter,
                "source": self.source,
                "citation": f"{self.source} · {chapter or '未标注章节'} · 第 {item.get('page')} 页",
                "score": round(top_score, 4),
            }
        except Exception:
            return None

    def _variants(self, keyword: str) -> list[str]:
        variants = [keyword]
        if keyword.endswith(("病例", "结构", "系统", "总览", "图")):
            variants.append(keyword.rstrip("病例结构系统总览图"))
        return variants

    def _find_passage(self, keyword: str) -> dict[str, Any] | None:
        for item in self.pages:
            text = item.get("text", "")
            position = text.find(keyword)
            if position < 0:
                continue
            content = self._passage(text, position)
            chapter = item.get("chapter") or self._nearest_chapter(item)
            return {
                "query": keyword,
                "title": chapter or keyword,
                "content": content,
                "page": item.get("page"),
                "chapter": chapter,
                "source": self.source,
                "citation": f"{self.source} · {chapter or '未标注章节'} · 第 {item.get('page')} 页",
            }
        return None

    @staticmethod
    def _passage(text: str, position: int) -> str:
        start = max(0, position - 260)
        sentence = text.rfind("。", start, position)
        if sentence >= 0:
            start = sentence + 1
        end = min(len(text), position + 760)
        tail = text.find("。", position + 60)
        if 0 < tail < end:
            end = tail + 1
        return text[start:end].strip()

    def _best_passage(self, text: str, query: str) -> str:
        """Return the most relevant passage, preferring sentences that contain query tokens."""
        sentences = re.split(r"(?<=[。！？])", text)
        for sent in sentences:
            if query in sent:
                start = max(0, text.find(sent) - 120)
                end = min(len(text), text.find(sent) + len(sent) + 360)
                return text[start:end].strip()
        # Fallback: first reasonable chunk.
        return text[:760].strip()

    def _nearest_chapter(self, item: dict[str, Any]) -> str:
        for previous in reversed(self.pages[: self.pages.index(item)]):
            if previous.get("chapter"):
                return previous["chapter"]
        return ""


anatomy_textbook_service = AnatomyTextbookService()
