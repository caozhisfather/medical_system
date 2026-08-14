from __future__ import annotations

from datetime import date, timedelta
from typing import Any
from uuid import uuid4


class DailyReviewService:
    """Build deterministic mock daily reviews from virtual teaching data."""

    def __init__(self) -> None:
        self._today = date.today()

    def today(self, student_id: str) -> dict[str, Any]:
        return self._review(student_id, self._today, "已生成")

    def history(self, student_id: str) -> list[dict[str, Any]]:
        return [
            self._review(student_id, self._today - timedelta(days=offset), "已生成" if offset != 2 else "需要教师关注")
            for offset in range(0, 7)
        ]

    def generate(self, student_id: str, force: bool = False) -> dict[str, Any]:
        review = self.today(student_id)
        review["generation_mode"] = "force_mock" if force else "mock"
        review["status_message"] = "已根据训练记录、错题、图谱路径和解剖练习生成今日复盘。"
        return review

    def recommendations(self, student_id: str) -> dict[str, Any]:
        review = self.today(student_id)
        return {
            "student_id": student_id,
            "date": review["date"],
            "recommended_cases": review["recommended_cases"],
            "recommended_knowledge": review["recommended_knowledge"],
            "recommended_anatomy": review["recommended_anatomy"],
            "recommended_graph_path": review["recommended_graph_path"],
            "tomorrow_plan": review["tomorrow_plan"],
        }

    def class_review(self, class_id: str = "clinical-2023-2") -> dict[str, Any]:
        return {
            "class_id": class_id,
            "date": self._today.isoformat(),
            "summary": "今日 38 名学生完成训练，腹痛查体流程遗漏率 42%，建议明天课堂重点讲解急腹症体格检查。",
            "trained_students": 38,
            "review_completion_rate": 86,
            "average_score": 81.8,
            "high_risk_rankings": [
                {"label": "未及时排除主动脉夹层", "count": 9, "level": "danger"},
                {"label": "腹膜刺激征记录不完整", "count": 16, "level": "warning"},
                {"label": "肺栓塞风险分层不足", "count": 7, "level": "danger"},
            ],
            "common_weak_points": ["急腹症查体流程", "致命性胸痛鉴别", "检查优先级与证据引用"],
            "attention_students": [
                {"student_id": "student_017", "name": "林同学", "reason": "连续两天出现高风险鉴别遗漏", "average_score": 68},
                {"student_id": "student_024", "name": "周同学", "reason": "腹痛病例查体流程持续不完整", "average_score": 71},
                {"student_id": "student_031", "name": "许同学", "reason": "指南依据引用准确率低于 60%", "average_score": 73},
            ],
            "teaching_suggestions": [
                "用 15 分钟复盘急腹症体格检查顺序，并让学生现场标注反跳痛、肌紧张和肠鸣音。",
                "安排 2 个胸痛变体进行对照训练，要求学生先排除主动脉夹层、肺栓塞和 ACS。",
                "复核 5 名连续高风险遗漏学生的问诊记录，给出个体化复训病例。",
            ],
        }

    def admin_config(self) -> dict[str, Any]:
        return {
            "generate_time": "21:30",
            "score_weights": {
                "inquiry_completeness": 0.18,
                "differential_diagnosis": 0.22,
                "exam_selection": 0.16,
                "guideline_evidence": 0.14,
                "anatomy_accuracy": 0.12,
                "clinical_safety": 0.18,
            },
            "recommended_case_count": 3,
            "recommended_knowledge_count": 5,
            "digital_human_review_enabled": True,
            "teacher_alert_enabled": True,
            "service_status": "mock_ready",
            "last_generated_at": f"{self._today.isoformat()} 21:30",
            "policy_note": "仅基于虚拟教学病例和脱敏/合成训练记录生成，不用于真实临床诊断。",
        }

    def _review(self, student_id: str, review_date: date, status: str) -> dict[str, Any]:
        offset = (self._today - review_date).days
        completed_cases = max(1, 4 - min(offset, 2))
        high_risk_misses = ["主动脉夹层相关追问略晚", "腹痛病例反跳痛与肠鸣音评估遗漏"] if offset < 2 else ["肺栓塞风险分层不足"]
        weak_points = ["主动脉夹层鉴别不足", "腹痛查体流程不完整", "肝胆胰解剖定位错误"] if offset < 2 else ["指南依据引用不充分", "检查优先级表达不清"]
        summary = (
            f"你今天完成了 {completed_cases} 个病例，胸痛病例表现较好，但腹痛病例中漏掉了反跳痛和肠鸣音评估。"
            "建议明天重点复习急腹症鉴别诊断和腹部查体流程。"
        )
        return {
            "review_id": f"DR-{review_date.strftime('%y%m%d')}-{uuid4().hex[:6]}",
            "student_id": student_id,
            "date": review_date.isoformat(),
            "status": status,
            "summary": summary,
            "completed_cases": completed_cases,
            "anatomy_practices": 3 - min(offset, 1),
            "knowledge_searches": 11 - offset,
            "average_score": 84 - offset * 2,
            "high_risk_misses": high_risk_misses,
            "performance": {
                "inquiry_completeness": 82 - offset,
                "differential_diagnosis": 76 - offset * 2,
                "exam_selection": 81 - offset,
                "guideline_evidence": 78 - offset,
                "anatomy_accuracy": 72 - offset * 2,
                "clinical_safety": 74 - offset,
            },
            "weak_points": weak_points,
            "strengths": ["胸痛危险因素识别较完整", "能主动使用心电图和肌钙蛋白证据", "问诊节奏比上次更稳定"],
            "recommended_cases": ["急性腹痛", "急诊胸痛", "呼吸困难"],
            "recommended_knowledge": ["急腹症鉴别诊断", "腹部查体流程", "主动脉夹层红旗征", "肺栓塞风险分层", "指南证据引用格式"],
            "recommended_anatomy": ["肝胆胰解剖定位训练"],
            "recommended_graph_path": ["腹痛症状", "腹膜刺激征", "急性阑尾炎", "肝胆胰解剖", "影像检查选择"],
            "tomorrow_plan": [
                "完成急性腹痛复训，重点补齐腹部查体顺序。",
                "沿知识图谱复习腹痛到急腹症鉴别路径。",
                "完成 1 次肝胆胰解剖定位训练，并记录错误区域。",
            ],
            "teacher_attention_required": status == "需要教师关注" or len(high_risk_misses) >= 2,
        }
