from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from backend.app.models import Citation
from backend.app.services.case_citation_service import CaseCitationService


def normalize_title(value: str) -> str:
    return value.strip().replace("《", "").replace("》", "").replace(" ", "")


def main() -> None:
    cases = json.loads((ROOT_DIR / "data" / "cases.json").read_text(encoding="utf-8"))
    guidelines = json.loads(
        (ROOT_DIR / "data" / "guidelines.json").read_text(encoding="utf-8")
    )
    service = CaseCitationService(guidelines)
    unrelated_chest_result = [
        Citation(
            id="chest-fallback",
            title="《急性胸痛基层诊疗指南》",
            source="教学示例知识库",
            snippet="错误的跨病例回退引用。",
        )
    ]

    summaries: list[dict[str, object]] = []
    for case in cases:
        citations = service.for_case(case, unrelated_chest_result, limit=4)
        allowed = {
            normalize_title(title) for title in case.get("recommended_guidelines", [])
        }
        returned = {normalize_title(citation.title) for citation in citations}

        if allowed:
            assert returned <= allowed, (
                f"{case['case_id']} 返回了不属于当前病例的引用：{returned - allowed}"
            )
        else:
            assert citations[0].id.endswith("-evidence-placeholder")

        if case["case_id"] != "emergency_chest_pain":
            assert not (
                normalize_title("急性胸痛基层诊疗指南") in returned
                and normalize_title("急性胸痛基层诊疗指南") not in allowed
            ), f"{case['case_id']} 错误复用了胸痛指南"

        if case["case_id"] in {
            "emergency_chest_pain",
            "palpitations",
            "jaundice_case",
        }:
            summaries.append(
                {
                    "case_id": case["case_id"],
                    "citations": [citation.title for citation in citations],
                    "sources": [citation.source for citation in citations],
                }
            )

    print(
        json.dumps(
            {
                "verified_case_count": len(cases),
                "cross_case_samples": summaries,
                "status": "case_id citation isolation passed",
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

