from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import numpy as np

from ..config import ROOT_DIR, settings
from ..embedding_service import embedding_service


class DocumentEvidenceService:
    """Retrieves page-level evidence from all administrator-uploaded documents."""

    def __init__(self) -> None:
        self.library_file = ROOT_DIR / "data" / "document_library.json"
        self.index_file = ROOT_DIR / "data" / "document_embeddings.json"
        self.vectors_file = ROOT_DIR / "data" / "document_embeddings.npz"

    def _library(self) -> list[dict[str, Any]]:
        if not self.library_file.exists():
            return []
        try:
            payload = json.loads(self.library_file.read_text(encoding="utf-8"))
            return [item for item in payload.get("documents", []) if not item.get("deleted")]
        except (OSError, json.JSONDecodeError):
            return []

    def _records(self) -> list[dict[str, Any]]:
        if self.index_file.exists():
            try:
                payload = json.loads(self.index_file.read_text(encoding="utf-8"))
                indexed = list(payload.get("items", []))
                if indexed:
                    return indexed
            except (OSError, json.JSONDecodeError):
                pass
        # An embedding quota failure must not make uploaded teaching material disappear.
        # The page OCR remains searchable until an administrator rebuilds vectors.
        records: list[dict[str, Any]] = []
        for document in self._library():
            raw_path = Path(str(document.get("ocr_text_path", "")))
            path = raw_path if raw_path.is_absolute() else ROOT_DIR / raw_path
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            for page in payload.get("pages", []):
                text = str(page.get("text") or "").strip()
                if text:
                    records.append({
                        "document_id": document.get("document_id") or document.get("id"),
                        "document_title": document.get("title", "未命名资料"),
                        "document_type": document.get("document_type", ""),
                        "category": document.get("category", ""),
                        "page": page.get("page"),
                        "text": text,
                        "text_hash": f"ocr-{document.get('id')}-{page.get('page')}",
                    })
        return records

    @staticmethod
    def _normalise(text: str) -> str:
        return re.sub(r"[\s\W_]+", "", text.casefold(), flags=re.UNICODE)

    @staticmethod
    def _terms(text: str) -> list[str]:
        compact = DocumentEvidenceService._normalise(text)
        if not compact:
            return []
        terms = [compact]
        if re.fullmatch(r"[\u4e00-\u9fff]+", compact):
            terms.extend(compact)
        terms.extend(re.findall(r"[a-z0-9]+", compact))
        return list(dict.fromkeys(term for term in terms if term))

    def _lexical_score(
        self,
        query: str,
        text: str,
        title: str = "",
        document_type: str = "",
        category: str = "",
    ) -> float:
        query_terms = self._terms(query)
        query_phrase = self._normalise(query)
        haystack = self._normalise(text)
        if not query_terms or not haystack:
            return 0.0

        matched = sum(1 for term in query_terms if term in haystack)
        coverage = matched / len(query_terms)
        phrase_hits = haystack.count(query_phrase) if query_phrase else 0
        frequency = min(1.0, math.log1p(phrase_hits) / math.log(6))
        density = min(1.0, phrase_hits / max(len(haystack) / 900, 1))
        title_haystack = self._normalise(title)
        title_bonus = 1.0 if query_phrase and query_phrase in title_haystack else 0.0

        # TOC/front-matter pages often contain the term once plus long dot leaders.
        dot_leaders = len(re.findall(r"\.{4,}|…{3,}", text))
        toc_penalty = min(0.46, dot_leaders * 0.022)
        if "目录" in title:
            toc_penalty += 0.08
        source_bonus = 0.0
        if document_type == "textbook":
            source_bonus += 0.07
        if category in {"解剖图谱", "解剖学"} or "解剖" in title or "图谱" in title:
            source_bonus += 0.11
        if document_type == "evidence" or category in {"临床指南", "医学依据"}:
            source_bonus -= 0.08

        score = (
            coverage * 0.48
            + min(frequency, 1.0) * 0.24
            + density * 0.16
            + title_bonus * 0.12
            + source_bonus
            - toc_penalty
        )
        return round(max(0.0, min(0.98, score)), 4)

    def _query_vector_scores(self, query: str, records: list[dict[str, Any]]) -> dict[str, float]:
        if not self.vectors_file.exists() or not records or not embedding_service.configured():
            return {}
        try:
            matrix = np.load(self.vectors_file)["vectors"]
            if matrix.ndim != 2 or len(matrix) == 0 or len(matrix) != len(records):
                return {}
            vector = np.asarray(embedding_service.encode([query], batch_size=1)[0], dtype=np.float32)
            if matrix.shape[1] != len(vector):
                return {}
            denominator = np.linalg.norm(matrix, axis=1) * np.linalg.norm(vector)
            scores = np.divide(matrix @ vector, denominator, out=np.zeros(len(records)), where=denominator != 0)
            return {str(record.get("text_hash")): round(float(score), 4) for record, score in zip(records, scores)}
        except Exception:
            return {}

    @staticmethod
    def _lines(text: str, query: str) -> tuple[list[dict[str, Any]], int, int]:
        rows = text.splitlines() or [text]
        terms = [term for term in DocumentEvidenceService._terms(query) if len(term) > 1]
        matches = [index for index, row in enumerate(rows) if any(term in row.casefold() for term in terms)]
        if not matches and rows:
            matches = [0]
        start = max(0, (matches[0] if matches else 0) - 2)
        end = min(len(rows), (matches[-1] if matches else 0) + 3)
        selected = [{"line": index + 1, "text": rows[index], "matched": index in matches} for index in range(start, end)]
        return selected, (matches[0] + 1 if matches else 1), (matches[-1] + 1 if matches else 1)

    def search(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        query = query.strip()
        if not query:
            return []
        library = {str(item.get("document_id") or item.get("id")): item for item in self._library()}
        records = self._records()
        vector_scores = self._query_vector_scores(query, records)
        candidates: list[dict[str, Any]] = []
        for record in records:
            document = library.get(str(record.get("document_id")), {})
            lexical = self._lexical_score(
                query,
                str(record.get("text", "")),
                str(record.get("document_title") or document.get("title", "")),
                str(record.get("document_type") or document.get("document_type", "")),
                str(record.get("category") or document.get("category", "")),
            )
            vector = vector_scores.get(str(record.get("text_hash")), 0.0)
            score = max(lexical, vector) if vector_scores else lexical
            if score <= 0:
                continue
            lines, line_start, line_end = self._lines(str(record.get("text", "")), query)
            candidates.append({
                "document_id": record.get("document_id"),
                "document_title": record.get("document_title") or document.get("title", "未命名资料"),
                "document_type": record.get("document_type") or document.get("document_type", ""),
                "category": record.get("category") or document.get("category", ""),
                "page": record.get("page"),
                "line_start": line_start,
                "line_end": line_end,
                "lines": lines,
                "content": str(record.get("text", "")),
                "score": round(score, 4),
                "source_path": document.get("source_path", ""),
            })
        candidates.sort(key=lambda item: item["score"], reverse=True)
        return candidates[: max(1, min(limit, 8))]

    def page_path(self, document_id: str, page: int) -> Path:
        item = next((item for item in self._library() if str(item.get("document_id") or item.get("id")) == document_id), None)
        if not item:
            raise FileNotFoundError(document_id)
        source = Path(str(item.get("source_path", "")))
        if not source.is_absolute():
            source = ROOT_DIR / source
        if page < 1 or page > int(item.get("page_count") or 0):
            raise ValueError("页码超出资料范围")
        return source

    def answer(self, query: str, evidence: list[dict[str, Any]]) -> dict[str, Any] | None:
        if not evidence or not (not settings.demo_mode and settings.openai_api_key and settings.openai_base_url and settings.openai_model):
            return None
        sources = "\n\n".join(
            f"[资料{index + 1}] {item['document_title']} 第{item['page']}页，第{item['line_start']}-{item['line_end']}行\n{item['content']}"
            for index, item in enumerate(evidence[:4])
        )
        prompt = (
            "你是医学教育平台的垂类解剖学讲解模型。只能依据给定教材证据回答。"
            "先写‘教材依据’，再写‘模型补充说明（非教材原文）’；教材没有或一笔带过时才允许补充，"
            "补充必须明确标注。每个关键结论后标注[资料编号-页码-行号]。不得编造页码，不提供诊断或治疗建议。\n\n"
            "请严格按照 Markdown 输出，使用清晰标题、短段落和列表。"
            "当需要比较两个及以上结构、层次、位置差异或临床联系时，优先使用 Markdown 表格；"
            "表头应简洁明确，每个单元格只放一个结论，避免为了凑表格而虚构内容。"
            "模型补充内容必须与教材依据分开，不能把推测写成教材原文。\n\n"
            f"问题：{query}\n教材证据：\n{sources}"
        )
        body = json.dumps({"model": settings.openai_answer_model, "messages": [{"role": "user", "content": prompt}], "temperature": 0.15, "max_tokens": settings.openai_max_tokens}, ensure_ascii=False).encode("utf-8")
        request = Request(f"{settings.openai_base_url.rstrip('/')}/v1/chat/completions", data=body, headers={"Authorization": f"Bearer {settings.openai_api_key}", "Content-Type": "application/json"}, method="POST")
        try:
            with urlopen(request, timeout=30) as response:
                payload = json.loads(response.read().decode("utf-8"))
            content = str(payload.get("choices", [{}])[0].get("message", {}).get("content", "")).strip()
            return {"answer": content, "model": settings.openai_answer_model} if content else None
        except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError, IndexError, AttributeError):
            return None


document_evidence_service = DocumentEvidenceService()
