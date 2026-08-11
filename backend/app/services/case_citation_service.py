from __future__ import annotations

from typing import Any

from ..models import Citation


def _normalize_title(value: str) -> str:
    return value.strip().replace("《", "").replace("》", "").replace(" ", "")


def _display_title(value: str) -> str:
    title = value.strip()
    return title if title.startswith("《") else f"《{title}》"


class CaseCitationService:
    """Restricts training citations to the active case's evidence allowlist."""

    def __init__(self, guideline_documents: list[dict[str, Any]]) -> None:
        self.guideline_documents = guideline_documents
        self.documents_by_title = {
            _normalize_title(document.get("title", "")): document
            for document in guideline_documents
            if document.get("title")
        }

    def for_case(
        self,
        case: dict[str, Any],
        retrieved: list[Citation] | None = None,
        limit: int = 3,
    ) -> list[Citation]:
        allowed_titles = case.get("recommended_guidelines", [])
        retrieved_by_title = {
            _normalize_title(citation.title): citation
            for citation in (retrieved or [])
        }
        citations: list[Citation] = []

        for index, allowed_title in enumerate(allowed_titles[:limit]):
            normalized = _normalize_title(allowed_title)
            document = self.documents_by_title.get(normalized)
            retrieved_citation = retrieved_by_title.get(normalized)

            if document:
                citations.append(
                    Citation(
                        id=document.get("id", f"{case['case_id']}-guide-{index + 1}"),
                        title=document["title"],
                        source=document.get("source", "教学指南知识库"),
                        snippet=document.get("content", "")[:180],
                    )
                )
            elif retrieved_citation:
                citations.append(retrieved_citation)
            else:
                citations.append(
                    Citation(
                        id=f"{case['case_id']}-guide-{index + 1}",
                        title=_display_title(allowed_title),
                        source="病例教学证据索引（Mock，待教师审核）",
                        snippet=(
                            f"该条目来自“{case['title_zh']}”病例的指南引用配置。"
                            "当前原型未收录指南原文，仅用于教学引用占位；"
                            "正式使用前需接入合法来源并由教师审核。"
                        ),
                    )
                )

        if citations:
            return citations

        return [
            Citation(
                id=f"{case['case_id']}-evidence-placeholder",
                title=f"《{case['title_zh']}教学证据待补充》",
                source="病例教学证据索引（Mock，待教师审核）",
                snippet="当前病例尚未配置指南条目，不能使用其他病例的证据替代。",
            )
        ]
