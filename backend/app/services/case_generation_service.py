from __future__ import annotations

from typing import Any

from .case_source_adapter import CaseSourceAdapter
from .case_validation_service import CaseValidationService


class CaseGenerationService:
    """Mock generation pipeline. A reviewed LLM adapter can replace enrich()."""

    def __init__(self) -> None:
        self.source_adapter = CaseSourceAdapter()
        self.validator = CaseValidationService()

    def generate_mock(self, source: dict[str, Any] | None = None) -> dict[str, Any]:
        candidate = self.source_adapter.adapt(source or {})
        case = {
            "case_id": "generated_mock_case",
            "title_zh": candidate["title"],
            "title_en": "Generated mock teaching case",
            "department": "待教师审核",
            "specialty": "病例生成器",
            "difficulty": "入门",
            "scenario": "由候选摘要转换的虚拟教学病例草稿",
            "chief_complaint": "示例主诉",
            "patient_profile": {
                "age": 40,
                "gender": "未设定",
                "occupation": "虚拟角色",
                "personality": "配合",
                "communication_style": "简洁回答",
            },
            "opening_statement": "医生，我有一些不舒服。",
            "history": {
                "present_illness": [candidate["summary"] or "待教师补充现病史"],
                "past_history": ["待补充"],
                "medication_history": ["待补充"],
                "allergy_history": ["待补充"],
                "personal_history": ["待补充"],
                "family_history": ["待补充"],
            },
            "physical_exam": ["待补充"],
            "available_tests": [],
            "hidden_final_diagnosis": "待教师确认的教学诊断",
            "differential_diagnoses": ["鉴别诊断A", "鉴别诊断B", "鉴别诊断C"],
            "key_scoring_points": ["主诉", "现病史", "既往史", "检查选择", "风险识别"],
            "high_risk_misses": ["未完成教师审核"],
            "common_student_errors": [],
            "recommended_guidelines": [],
            "related_knowledge_ids": [],
            "related_graph_node_ids": [],
            "recommended_followups": [],
            "patient_answer_rules": {
                "can_only_answer_known_facts": True,
                "do_not_reveal_final_diagnosis": True,
                "unknown_answer": "这个我不太清楚，医生您能再具体问一下吗？",
            },
            "source": {
                "type": "synthetic",
                "name": candidate["source_id"],
                "contains_real_patient_data": False,
            },
            "review_status": "待教师审核",
        }
        return {"case": case, "validation": self.validator.validate(case)}

