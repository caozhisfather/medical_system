from __future__ import annotations

import re
from typing import Any


def _tokens(value: str) -> list[str]:
    cleaned = re.sub(r"[未与和及、，。；：()（）]", " ", value)
    return [token for token in cleaned.split() if len(token) >= 2]


class ScoringAgent:
    def score(
        self,
        case: dict[str, Any],
        transcript: str,
        ordered_tests: list[str] | None = None,
        preliminary_diagnosis: str = "",
        differentials: list[str] | None = None,
        treatment_principles: str = "",
        citations: list[str] | None = None,
    ) -> dict[str, Any]:
        ordered_tests = ordered_tests or []
        differentials = differentials or []
        citations = citations or []
        combined = " ".join(
            [transcript, *ordered_tests, preliminary_diagnosis, *differentials, treatment_principles, *citations]
        )

        point_hits = [
            point for point in case["key_scoring_points"] if any(token in combined for token in _tokens(point))
        ]
        test_hits = [
            test["test_name"]
            for test in case["available_tests"]
            if test["test_name"] in combined or test["test_name"] in ordered_tests
        ]
        diff_hits = [item for item in case["differential_diagnoses"] if item in combined or item in differentials]
        diagnosis_hit = bool(
            preliminary_diagnosis
            and (
                preliminary_diagnosis in case["hidden_final_diagnosis"]
                or case["hidden_final_diagnosis"] in preliminary_diagnosis
            )
        )
        missing = []
        for index, risk in enumerate(case["high_risk_misses"]):
            if not any(token in combined for token in _tokens(risk)):
                missing.append(
                    {
                        "id": f"{case['case_id']}_risk_{index + 1}",
                        "level": "danger" if index == 0 else "warning",
                        "text": risk,
                        "suggestion": f"围绕“{risk.replace('未', '', 1)}”补充证据或决策。",
                    }
                )

        dimensions = [
            self._dimension("病史采集", 40 + len(point_hits) * 7, f"覆盖 {len(point_hits)}/{len(case['key_scoring_points'])} 个病例关键点"),
            self._dimension("检查选择", 42 + len(test_hits) * 13, f"命中：{'、'.join(test_hits) or '尚未申请病例关键检查'}"),
            self._dimension("鉴别诊断", 40 + len(diff_hits) * 14, f"覆盖：{'、'.join(diff_hits) or '尚未覆盖核心鉴别'}"),
            self._dimension("临床决策", 52 + (18 if diagnosis_hit else 0) + (10 if treatment_principles else 0), "初步诊断与处置原则已纳入评估"),
            self._dimension("指南依据", 48 + min(36, len(citations) * 18), f"提交 {len(citations)} 条证据引用"),
            self._dimension("沟通表达", 62 + min(28, transcript.count("？") * 3 + transcript.count("请") * 5), "依据开放式提问和沟通措辞评分"),
        ]
        total = round(sum(item["score"] for item in dimensions) / len(dimensions))
        return {
            "case_id": case["case_id"],
            "variant_id": case.get("active_variant", "A"),
            "total_score": total,
            "scores": dimensions,
            "covered_scoring_points": point_hits,
            "ordered_test_hits": test_hits,
            "differential_hits": diff_hits,
            "diagnosis_match": diagnosis_hit,
            "missing_points": missing,
            "feedback": (
                f"本次按“{case['title_zh']}”独立评分规则完成评估。"
                f"已覆盖 {len(point_hits)} 个关键点，仍有 {len(missing)} 个风险遗漏。"
            ),
        }

    @staticmethod
    def _dimension(name: str, value: int, feedback: str) -> dict[str, Any]:
        return {"name": name, "score": min(96, value), "max_score": 100, "feedback": feedback}

