from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.wsgi import WSGIMiddleware

from .config import ROOT_DIR, settings
from .flask_app import create_flask_app
from .models import (
    CaseSummary,
    ChatMessage,
    MissingPoint,
    PatientChatRequest,
    PatientChatResponse,
    RagAnswer,
    RagQuery,
    ScoreItem,
    TrainingReport,
)
from .rag import RagPipeline
from .workflow import build_trace, load_workflow

DATA_DIR = ROOT_DIR / "data"

app = FastAPI(title="AI标准化病人临床思维训练平台", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin, "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/flask", WSGIMiddleware(create_flask_app()))
rag_pipeline = RagPipeline()


def read_json(name: str) -> Any:
    return json.loads((DATA_DIR / name).read_text(encoding="utf-8"))


def get_case(case_id: str) -> dict[str, Any]:
    cases = read_json("cases.json")
    return next((case for case in cases if case["id"] == case_id), cases[0])


def patient_reply(case: dict[str, Any], message: str) -> str:
    script = case.get("script") or {}
    for item in script.get("answers", []):
        if any(keyword in message for keyword in item["keywords"]):
            return item["reply"]
    return script.get("opening", "我只能根据这个虚拟教学病例回答你的问诊问题。")


def score_message(message: str, history: list[ChatMessage]) -> list[ScoreItem]:
    combined = " ".join([m.content for m in history] + [message])
    checks = {
        "病史采集": ["性质", "部位", "多久", "伴随", "既往", "诱因"],
        "检查选择": ["心电图", "肌钙蛋白", "血压", "血氧", "胸片"],
        "鉴别诊断": ["主动脉夹层", "肺栓塞", "气胸", "冠脉", "ACS"],
        "临床决策": ["急诊", "监护", "复查", "风险", "会诊"],
        "指南依据": ["指南", "依据", "教材", "证据"],
        "沟通表达": ["请", "担心", "解释", "告知", "复核"],
    }
    scores: list[ScoreItem] = []
    for name, keywords in checks.items():
        hit = sum(1 for keyword in keywords if keyword in combined)
        value = min(100, 42 + hit * 14)
        feedback = "已覆盖关键点" if value >= 70 else "建议继续补充该维度信息"
        scores.append(ScoreItem(name=name, score=value, feedback=feedback))
    return scores


def missing_points(message: str, history: list[ChatMessage], citations: list) -> list[MissingPoint]:
    combined = " ".join([m.content for m in history] + [message])
    rules = [
        ("pain_quality", "warning", "尚未询问胸痛性质", "追问压榨样、撕裂样、针刺样等疼痛特征。", ["性质", "怎么疼", "压榨", "撕裂"]),
        ("dissection", "danger", "尚未排除主动脉夹层", "询问撕裂样胸背痛、血压差、神经系统症状。", ["主动脉夹层", "撕裂", "背痛"]),
        ("ecg_troponin", "warning", "建议申请心电图和肌钙蛋白", "疑似ACS时应尽早完成心电图和心肌损伤标志物评估。", ["心电图", "肌钙蛋白"]),
        ("pe", "notice", "尚未系统鉴别肺栓塞", "询问呼吸困难、咯血、下肢肿痛、卧床或长途旅行史。", ["肺栓塞", "咯血", "下肢"]),
    ]
    result: list[MissingPoint] = []
    citation = citations[0] if citations else None
    for item_id, level, text, suggestion, keywords in rules:
        if not any(keyword in combined for keyword in keywords):
            result.append(MissingPoint(id=item_id, level=level, text=text, suggestion=suggestion, citation=citation))
    return result


@app.get("/api/health")
def health() -> dict:
    return {
        "status": "ok",
        "app": "AI标准化病人临床思维训练平台",
        "environment": settings.environment,
        "rag_provider": settings.rag_provider,
        "vector_stores": {"chroma_db_path": settings.chroma_db_path, "milvus_uri": settings.milvus_uri},
        "tts_provider": settings.tts_provider,
    }


@app.get("/api/site/overview")
def site_overview() -> dict:
    return {
        "name": "临思智训",
        "subtitle": "面向医学教育的AI标准化病人临床思维训练平台",
        "contest_track": "AI+医学学科交叉",
        "positioning": "通过AI标准化病人、RAG指南依据、过程性评分和教师反馈闭环训练医学生临床思维。",
        "metrics": [
            {"label": "虚拟病例", "value": "5个", "trend": "可扩展病例库"},
            {"label": "评分维度", "value": "6项", "trend": "过程性评价"},
            {"label": "Agent节点", "value": "6个", "trend": "工作流编排"},
            {"label": "知识来源", "value": "3类", "trend": "指南教材共识"},
        ],
        "scenarios": ["学生端", "教师端"],
    }


@app.get("/api/cases", response_model=list[CaseSummary])
def cases() -> list[CaseSummary]:
    return [CaseSummary(**{key: case[key] for key in CaseSummary.model_fields}) for case in read_json("cases.json")]


@app.post("/api/patient/chat", response_model=PatientChatResponse)
def patient_chat(payload: PatientChatRequest) -> PatientChatResponse:
    case = get_case(payload.case_id)
    citations = rag_pipeline.retrieve(payload.message, limit=3)
    reply = patient_reply(case, payload.message)
    scores = score_message(payload.message, payload.history)
    missed = missing_points(payload.message, payload.history, citations)
    safety_notes = [
        "本病例为虚拟教学病例，不含真实患者信息。",
        "AI病人不会主动泄露诊断，学生需通过问诊和检查选择推进推理。",
        "平台反馈用于教学训练，不用于真实临床诊断或治疗。",
    ]
    return PatientChatResponse(
        patient_reply=ChatMessage(role="patient", content=reply, citations=[]),
        tutor_hint="请继续围绕胸痛性质、放射痛、高危鉴别诊断和必要检查推进问诊。",
        scores=scores,
        missing_points=missed,
        workflow_trace=build_trace(payload.message, case["title"]),
        citations=citations,
        safety_notes=safety_notes,
    )


@app.get("/api/guidelines")
def guidelines() -> list[dict[str, Any]]:
    return read_json("guidelines.json")


@app.get("/api/teacher/dashboard")
def teacher_dashboard() -> dict[str, Any]:
    return read_json("teacher_dashboard.json")


@app.get("/api/training/report", response_model=TrainingReport)
def training_report(case_id: str = "emergency_chest_pain") -> TrainingReport:
    citations = rag_pipeline.retrieve("胸痛 急性冠脉综合征 心电图 肌钙蛋白", limit=3)
    return TrainingReport(
        case_id=case_id,
        diagnosis_path=["主诉胸痛", "识别ACS危险因素", "补充高危鉴别", "申请心电图和肌钙蛋白", "根据证据更新诊断路径"],
        strengths=["能关注胸痛持续时间和活动诱因", "能提出急性冠脉综合征作为重点鉴别"],
        improvements=["需更早询问胸痛性质和放射痛", "需主动排除主动脉夹层和肺栓塞", "需说明指南依据和非诊疗边界"],
        recommended_cases=["呼吸困难", "急性腹痛", "发热待查"],
        citations=citations,
    )


@app.get("/api/knowledge-graph")
def knowledge_graph() -> dict[str, Any]:
    return read_json("medical_kg.json")


@app.get("/api/workflow")
def workflow() -> dict:
    return load_workflow()


@app.post("/api/rag/query", response_model=RagAnswer)
def rag_query(payload: RagQuery) -> RagAnswer:
    answer, citations, safety_notes = rag_pipeline.answer(payload.question, payload.scenario)
    return RagAnswer(answer=answer, citations=citations, workflow_trace=build_trace(payload.question, payload.scenario), safety_notes=safety_notes)


@app.post("/api/rag/index")
def rag_index() -> dict[str, Any]:
    return rag_pipeline.write_vector_store()


if __name__ == "__main__":
    uvicorn.run("backend.app.main:app", host=settings.backend_host, port=settings.backend_port, reload=True)
