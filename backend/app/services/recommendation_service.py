from __future__ import annotations

from typing import Any

ABILITY_DIMENSIONS = ("inquiry", "differential", "exam", "guideline", "anatomy", "safety")
DIMENSION_LABELS = {
    "inquiry": "问诊完整性", "differential": "鉴别诊断", "exam": "检查选择", "guideline": "指南证据", "anatomy": "解剖定位", "safety": "临床安全",
}
TERMS = {
    "inquiry": ("问诊", "现病史", "主诉", "病史", "症状"),
    "differential": ("鉴别", "危险鉴别", "诊断", "风险识别"),
    "exam": ("检查", "心电图", "肌钙蛋白", "影像", "筛查"),
    "guideline": ("指南", "证据", "依据"),
    "anatomy": ("解剖", "定位", "结构", "器官"),
    "safety": ("安全", "红旗", "高危", "处置", "监测"),
}


def ability_vector(focus: str = "") -> dict[str, int]:
    vector = {key: 72 for key in ABILITY_DIMENSIONS}
    text = focus or ""
    for dimension, terms in TERMS.items():
        if any(term in text for term in terms):
            vector[dimension] = 56
    return vector


def case_vector(case: dict[str, Any]) -> dict[str, int]:
    text = " ".join(str(case.get(key, "")) for key in ("title_zh", "scenario", "specialty", "department")) + " " + " ".join(case.get("training_goals", [])) + " " + " ".join(case.get("high_risk_misses", []))
    return {dimension: 100 if any(term in text for term in terms) else 35 for dimension, terms in TERMS.items()}


def rank_cases(cases: list[dict[str, Any]], focus: str = "", active_case_id: str = "") -> dict[str, Any]:
    student = ability_vector(focus)
    ranked = []
    for case in cases:
        if case.get("case_id") == active_case_id:
            continue
        needs = case_vector(case)
        gap_score = sum(needs[key] * (100 - student[key]) / 100 for key in ABILITY_DIMENSIONS) / len(ABILITY_DIMENSIONS)
        risk_bonus = min(12, len(case.get("high_risk_misses", [])) * 3)
        score = round(gap_score + risk_bonus, 1)
        ranked.append({**case, "recommendation_score": score, "ability_match": {DIMENSION_LABELS[key]: needs[key] for key in ABILITY_DIMENSIONS}, "reason": f"优先补强：{', '.join(DIMENSION_LABELS[key] for key in ABILITY_DIMENSIONS if needs[key] >= 100 and student[key] < 70) or '综合临床思维'}"})
    ranked.sort(key=lambda item: item["recommendation_score"], reverse=True)
    return {"student_vector": {DIMENSION_LABELS[key]: value for key, value in student.items()}, "algorithm": "能力缺口匹配 + 病例风险加权", "cases": ranked}
