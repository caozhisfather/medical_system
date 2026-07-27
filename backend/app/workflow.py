from __future__ import annotations

import json
from pathlib import Path

from .models import WorkflowStep

ROOT_DIR = Path(__file__).resolve().parents[2]

WORKFLOW_STAGES = [
    {"id": "input", "name": "学生输入", "agent": "TutorAgent", "goal": "接收学生问诊、诊断或检查选择。"},
    {"id": "context", "name": "病例上下文读取", "agent": "PatientAgent", "goal": "读取虚拟病例脚本和已问诊历史。"},
    {"id": "safety", "name": "安全检查", "agent": "SafetyAgent", "goal": "确认输出不用于真实诊断并避免泄露病例诊断。"},
    {"id": "patient", "name": "病人回复生成", "agent": "PatientAgent", "goal": "仅根据病例脚本模拟标准化病人回答。"},
    {"id": "retrieval", "name": "RAG检索指南依据", "agent": "RetrievalAgent", "goal": "检索指南、教材和专家共识片段并返回citation。"},
    {"id": "scoring", "name": "临床思维评分", "agent": "ScoringAgent", "goal": "对病史、检查、鉴别诊断、决策、依据和沟通评分。"},
    {"id": "missing", "name": "关键遗漏检测", "agent": "TutorAgent", "goal": "提示尚未询问或尚未排除的高危问题。"},
    {"id": "save", "name": "训练记录保存", "agent": "TutorAgent", "goal": "保存本轮过程性训练记录。"},
    {"id": "report", "name": "报告生成", "agent": "ReportAgent", "goal": "生成诊断路径、优点、改进点和复训建议。"},
]


def load_workflow() -> dict:
    return {"name": "AI标准化病人临床思维训练 Workflow", "stages": WORKFLOW_STAGES}


def build_trace(question: str, scenario: str) -> list[WorkflowStep]:
    trace: list[WorkflowStep] = []
    for stage in WORKFLOW_STAGES:
        trace.append(
            WorkflowStep(
                id=stage["id"],
                name=stage["name"],
                agent=stage["agent"],
                status="done",
                detail=f"已针对“{scenario}”处理：{stage['goal']}",
            )
        )
    return trace
