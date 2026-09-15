from __future__ import annotations

from typing import Any
from uuid import uuid4

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

    def generate_teacher_draft(self, request: dict[str, Any], analytics: dict[str, Any]) -> dict[str, Any]:
        draft_id = f"teacher_case_{uuid4().hex[:8]}"
        learning_goal = request["learning_goal"].strip()
        source_summary = request.get("source_summary", "").strip()
        diagnosis = request.get("suspected_diagnosis", "").strip() or "待教师确认"
        common_gaps = analytics.get("common_missing_points", [])[:3]
        risk_items = analytics.get("risk_rankings", [])[:2]
        case = {
            "case_id": draft_id,
            "id": draft_id,
            "title_zh": request["title"],
            "title_en": "Teacher reviewed AI-assisted teaching case",
            "title": request["title"],
            "department": request["department"],
            "specialty": learning_goal[:30],
            "difficulty": request.get("difficulty", "进阶"),
            "scenario": f"教师围绕“{learning_goal}”创建的合成虚拟教学病例。",
            "chief_complaint": request["chief_complaint"],
            "symptom_tags": [request["chief_complaint"][:12]],
            "training_goals": [learning_goal, "结构化问诊", "检查选择", "安全决策"],
            "learning_goals": [learning_goal, "形成可解释的临床推理路径"],
            "recommended_minutes": 20,
            "completion_status": "未训练",
            "patient_profile": {
                "age": 48,
                "gender": "待教师设定",
                "occupation": "虚拟角色",
                "personality": "配合教学问诊，不主动补充未被问及的信息",
                "communication_style": "简洁回答，仅陈述病例脚本内事实",
            },
            "patient_profile_text": "48岁虚拟标准化病人，具体信息待教师复核",
            "speaking_style": "简洁回答，仅陈述病例脚本内事实",
            "opening_statement": f"医生，我主要是{request['chief_complaint']}。",
            "opening": f"医生，我主要是{request['chief_complaint']}。",
            "history": {
                "present_illness": [source_summary or f"围绕{request['chief_complaint']}的起病、性质、诱因和伴随表现待教师补充"],
                "past_history": ["相关既往史待教师补充"],
                "medication_history": ["既往用药待教师补充"],
                "allergy_history": ["过敏史待教师补充"],
                "personal_history": ["个人史待教师补充"],
                "family_history": ["家族史待教师补充"],
            },
            "present_illness": source_summary or f"围绕{request['chief_complaint']}的现病史待教师补充",
            "past_history": "相关既往史待教师补充",
            "physical_exam": ["生命体征待教师设定", "目标系统查体待教师设定"],
            "available_tests": [],
            "available_exams": [],
            "exam_results": {},
            "hidden_final_diagnosis": diagnosis,
            "differential_diagnoses": ["核心鉴别诊断A", "高风险鉴别诊断B", "常见鉴别诊断C"],
            "key_scoring_points": [learning_goal, "主诉特征", "现病史结构", "危险因素", "检查选择", "风险处置"],
            "high_risk_misses": [item.get("label", str(item)) for item in risk_items] or ["未完成高风险项教师审核"],
            "high_risk_omissions": [
                {"id": f"{draft_id}_risk_{index + 1}", "level": "warning", "text": gap, "suggestion": f"围绕“{gap}”设置评分点。", "keywords": [gap]}
                for index, gap in enumerate(common_gaps)
            ],
            "common_student_errors": common_gaps,
            "recommended_guidelines": ["相关专科指南待教师确认"],
            "recommended_retraining": [learning_goal],
            "patient_answer_rules": {
                "can_only_answer_known_facts": True,
                "do_not_reveal_final_diagnosis": True,
                "unknown_answer": "这个我不太清楚，医生您能再具体问一下吗？",
            },
            "case_variants": [],
            "script": {"opening": f"医生，我主要是{request['chief_complaint']}。", "answers": []},
            "source": {"type": "synthetic", "name": "teacher-ai-workflow", "contains_real_patient_data": False},
            "review_status": "待教师审核",
            "teacher_note": "",
            "recommendation_id": request.get("recommendation_id"),
        }
        workflow = [
            {"id": "analytics", "name": "学习结果分析", "agent": "LearningAnalyticsAgent", "status": "done", "detail": f"分析 {analytics.get('training_sessions', 0)} 次训练及共性薄弱项。"},
            {"id": "design", "name": "病例结构设计", "agent": "CaseDesignerAgent", "status": "done", "detail": f"围绕“{learning_goal}”生成病例结构。"},
            {"id": "patient", "name": "病人脚本生成", "agent": "PatientScriptAgent", "status": "done", "detail": "生成受病例事实约束的标准化病人脚本。"},
            {"id": "scoring", "name": "评分规则生成", "agent": "ScoringAgent", "status": "done", "detail": "将学生薄弱项转化为关键得分点和风险扣分项。"},
            {"id": "safety", "name": "安全与隐私检查", "agent": "SafetyAgent", "status": "done", "detail": "确认病例为合成教学内容且不含真实身份信息。"},
            {"id": "teacher", "name": "教师最终决策", "agent": "HumanReviewGate", "status": "waiting", "detail": "等待教师编辑、批准、退回或拒绝。"},
        ]
        return {"draft_id": draft_id, "case": case, "validation": self.validator.validate(case), "workflow": workflow}
