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
        medication_plan: str = "",
        citations: list[str] | None = None,
    ) -> dict[str, Any]:
        ordered_tests = ordered_tests or []
        differentials = differentials or []
        citations = citations or []
        combined = " ".join(
            [transcript, *ordered_tests, preliminary_diagnosis, *differentials, treatment_principles, medication_plan, *citations]
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

        medication_has_dose = bool(re.search(r"\d+(?:\.\d+)?\s*(?:mg|g|ml|片|支|单位)", medication_plan, re.IGNORECASE))
        medication_has_route_or_frequency = bool(
            re.search(r"口服|静脉|肌注|皮下|每日|每\d+小时|次/日|qd|bid|tid|q\d+h", medication_plan, re.IGNORECASE)
        )
        medication_has_safety = any(
            term in medication_plan for term in ("过敏", "禁忌", "监测", "肝功能", "肾功能", "出血", "相互作用", "妊娠")
        )
        if not medication_plan:
            missing.append({
                "id": f"{case['case_id']}_medication_plan",
                "level": "warning",
                "text": "未提交教学用药方案",
                "suggestion": "补充药物、剂量、途径、频次及安全监测要点。",
            })
        elif not medication_has_safety:
            missing.append({
                "id": f"{case['case_id']}_medication_safety",
                "level": "warning",
                "text": "教学用药方案缺少禁忌证或安全监测",
                "suggestion": "结合过敏史、脏器功能、相互作用或出血风险补充用药安全依据。",
            })

        medication_score = 38 if not medication_plan else 58
        medication_score += 12 if medication_has_dose else 0
        medication_score += 10 if medication_has_route_or_frequency else 0
        medication_score += 14 if medication_has_safety else 0
        medication_feedback = (
            "未提交教学用药方案"
            if not medication_plan
            else f"处方要素：剂量{'已' if medication_has_dose else '未'}说明，途径/频次{'已' if medication_has_route_or_frequency else '未'}说明，安全依据{'已' if medication_has_safety else '未'}说明"
        )

        dimensions = [
            self._dimension("病史采集", 40 + len(point_hits) * 7, f"覆盖 {len(point_hits)}/{len(case['key_scoring_points'])} 个病例关键点"),
            self._dimension("检查选择", 42 + len(test_hits) * 13, f"命中：{'、'.join(test_hits) or '尚未申请病例关键检查'}"),
            self._dimension("鉴别诊断", 40 + len(diff_hits) * 14, f"覆盖：{'、'.join(diff_hits) or '尚未覆盖核心鉴别'}"),
            self._dimension("临床决策", 52 + (18 if diagnosis_hit else 0) + (10 if treatment_principles else 0), "初步诊断与处置原则已纳入评估"),
            self._dimension("教学用药与安全", medication_score, medication_feedback),
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
