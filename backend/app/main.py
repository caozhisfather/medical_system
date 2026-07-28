from __future__ import annotations

import json
from typing import Any

import uvicorn
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.wsgi import WSGIMiddleware

from .api.digital_human import router as digital_human_router
from .config import ROOT_DIR, settings
from .data_sources import load_admin_users, load_data_sources, load_textbook_pathways
from .flask_app import create_flask_app
from .hybrid_retrieval_service import HybridRetrievalService
from .knowledge_graph_service import KnowledgeGraphService
from .obsidian_export_service import ObsidianGraphExportService
from .models import (
    AgentChatRequest, AgentChatResponse, AnatomySubmitRequest, AnatomySubmitResponse, AuthLoginRequest, AuthLoginResponse, AuthUser, CaseSummary, ChatMessage,
    MissingPoint, PatientChatRequest, PatientChatResponse, RagAnswer, RagQuery, ScoreItem, TTSRequest, TTSResponse,
    TrainingReport, TrainingScoreRequest,
)
from .rag import RagPipeline
from .workflow import build_trace, load_workflow

DATA_DIR = ROOT_DIR / "data"
app = FastAPI(title="AI标准化病人临床思维训练平台", version="0.4.0")
app.add_middleware(CORSMiddleware, allow_origins=[settings.frontend_origin, "http://localhost:5173", "http://127.0.0.1:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.mount("/flask", WSGIMiddleware(create_flask_app()))
app.include_router(digital_human_router)
rag_pipeline = RagPipeline(settings.rag_provider)
hybrid_service = HybridRetrievalService()
graph_service = KnowledgeGraphService()
obsidian_service = ObsidianGraphExportService()


def read_json(name: str) -> Any:
    return json.loads((DATA_DIR / name).read_text(encoding="utf-8"))


def get_case_data(case_id: str) -> dict[str, Any]:
    cases = read_json("cases.json")
    return next((case for case in cases if case["id"] == case_id), cases[0])


def safety_notes() -> list[str]:
    return ["本平台仅用于虚拟医学教学训练。", "所有病例均为虚拟病例，不含真实患者信息。", "系统反馈不构成真实临床诊断或治疗建议。"]


def patient_reply(case: dict[str, Any], message: str) -> str:
    script = case.get("script") or {}
    for item in script.get("answers", []):
        if any(keyword in message for keyword in item.get("keywords", [])):
            return item["reply"]
    field_routes = [
        (["现病史", "多久", "开始", "诱因", "症状", "疼", "性质", "放射", "喘", "平卧", "夜间", "咳嗽", "咯血", "发热", "热型", "皮疹", "恶心", "呕吐", "停经", "妊娠", "黄", "尿", "便", "头痛"], "present_illness"),
        (["既往", "病史", "用药", "高血压", "糖尿病", "贫血", "肝炎"], "past_history"),
        (["个人史", "吸烟", "饮酒", "生活", "饮食", "运动", "职业"], "personal_history"),
        (["家族", "遗传"], "family_history"),
        (["查体", "体温", "血压", "心率", "腹部", "肺部", "神经", "巩膜"], "physical_exam"),
    ]
    for keywords, field in field_routes:
        if any(keyword in message for keyword in keywords) and case.get(field):
            return case[field]
    for exam, result in (case.get("exam_results") or {}).items():
        if exam in message:
            return f"检查结果显示：{result}"
    if any(word in message for word in ["诊断", "最终", "是什么病"]):
        return "我不知道最终诊断，只能告诉您这个虚拟病例里的症状和已知信息。"
    return "这个我不太清楚，医生您能再具体问一下吗？"


def score_message(message: str, history: list[ChatMessage] | None = None, case: dict[str, Any] | None = None) -> list[ScoreItem]:
    combined = " ".join([m.content for m in (history or [])] + [message])
    points = (case or {}).get("key_scoring_points") or []
    dimensions = {
        "问诊完整性": ["现病史", "多久", "诱因", "伴随", "既往", "家族", "性质", "部位"],
        "检查选择合理性": (case or {}).get("available_exams", []) or ["心电图", "血常规", "影像"],
        "鉴别诊断覆盖率": (case or {}).get("differential_diagnoses", []) or ["鉴别"],
        "临床决策安全性": ["急诊", "风险", "复查", "监护", "会诊", "禁忌"],
        "指南引用准确率": (case or {}).get("recommended_guidelines", []) or ["指南", "依据"],
        "沟通表达评分": ["请", "担心", "解释", "告知", "教学", "复核"],
    }
    scores: list[ScoreItem] = []
    for name, keywords in dimensions.items():
        hit = sum(1 for keyword in keywords if keyword and keyword in combined)
        point_hit = sum(1 for point in points if point and any(part in combined for part in point.split("和")))
        value = min(100, 42 + hit * 10 + point_hit * 4)
        scores.append(ScoreItem(name=name, score=value, feedback="已覆盖关键点" if value >= 70 else "建议继续补充该病例相关信息"))
    return scores


def missing_points(message: str, history: list[ChatMessage], citations: list, case: dict[str, Any]) -> list[MissingPoint]:
    combined = " ".join([m.content for m in history] + [message])
    citation = citations[0] if citations else None
    result: list[MissingPoint] = []
    for item in case.get("high_risk_omissions", []):
        keywords = item.get("keywords") or [item.get("text", "")]
        if not any(keyword and keyword in combined for keyword in keywords):
            result.append(MissingPoint(id=item["id"], level=item.get("level", "warning"), text=item["text"], suggestion=item.get("suggestion", "请补充该关键点。"), citation=citation))
    return result[:5]


def search_items(query: str, lang: str = "zh") -> list[dict[str, Any]]:
    bundle = hybrid_service.query(query, lang=lang)
    results: list[dict[str, Any]] = []
    for case in bundle["related_cases"][:3]:
        results.append({"kind": "病例", "title": case["title"], "summary": case["chief_complaint"], "target": case["id"]})
    for item in bundle["matched_knowledge"][:6]:
        title = item.get("title_en") if lang == "en" else item.get("title_zh")
        summary = item.get("summary_en") if lang == "en" else item.get("summary_zh")
        results.append({"kind": item.get("subject", item.get("type", "知识")), "title": title or item.get("title", item["id"]), "summary": summary or item.get("summary", ""), "target": item.get("graph_node_ids", [item["id"]])[0] if item.get("graph_node_ids") else item.get("graph_node_id", item["id"])})
    for exercise in bundle["related_anatomy_exercises"][:4]:
        results.append({"kind": "解剖练习", "title": exercise["title"], "summary": exercise["prompt"], "target": exercise["id"]})
    return results[:10]


def match_case(message: str) -> dict[str, Any] | None:
    alias = {"腹痛": "acute_abdominal_pain", "发热": "fever_unknown", "呼吸困难": "dyspnea", "糖尿病": "diabetes_education", "头痛": "headache_case", "贫血": "anemia_case", "黄疸": "jaundice_case", "胸痛": "emergency_chest_pain"}
    for case in read_json("cases.json"):
        keys = [case["title"], case["chief_complaint"], *case.get("differential_diagnoses", []), *case.get("recommended_retraining", [])]
        if any(key and key in message for key in keys):
            return case
    for key, case_id in alias.items():
        if key in message:
            return get_case_data(case_id)
    return None


def match_anatomy(message: str) -> dict[str, Any] | None:
    alias = {"胃": "stomach_position", "心脏": "heart_position", "肺": "left_lung", "肝": "liver_position", "脑": "brain_position", "肾": "kidney_position", "主动脉": "aorta_course"}
    for item in read_json("anatomy.json"):
        if item["target"] in message or item["title"] in message:
            return item
    for key, exercise_id in alias.items():
        if key in message:
            return next((item for item in read_json("anatomy.json") if item["id"] == exercise_id), None)
    return None


def resolve_agent(message: str, role: str, active_module: str) -> AgentChatResponse:
    msg = message.strip()
    role_key = "admin" if role in {"admin", "super_admin"} else role
    lang = "en" if any(ord(char) < 128 for char in msg) and any(token in msg.lower() for token in ["acs", "chest", "heart", "modelscope", "obsidian"]) else "zh"
    bundle = hybrid_service.query(msg, lang=lang)
    cards = search_items(msg, lang=lang)
    intent, action, target_module = "retrieval", "show_results", "knowledge"
    target_case_id = None
    target_exercise_id = None
    learning_path = bundle["recommended_learning_path"]
    reply = f"已检索到 {len(cards)} 条站内资源，并生成学习路径。"
    case = match_case(msg)
    exercise = match_anatomy(msg)
    if role_key == "admin" and any(key in msg.lower() for key in ["modelscope", "数据源", "同步", "rag配置", "后台"]):
        intent, action, target_module = "admin_control", "open_admin_data_sources", "admin"
        sources = load_data_sources()
        reply = "已打开超级管理员工作台，并定位到 ModelScope 数据源与 RAG 配置。"
        cards = [{"kind": source["platform"], "title": source["name"], "summary": f"{source['type']} · {source['index_status']}", "target": source["id"]} for source in sources[:5]]
        learning_path = ["数据源审查", "字段映射", "Embedding mock", "Milvus/ChromaDB 配置", "引用追踪"]
    elif role_key == "admin" and any(key in msg.lower() for key in ["obsidian", "导出", "vault"]):
        intent, action, target_module = "admin_control", "obsidian_export", "admin"
        preview = obsidian_service.export_preview(limit=5)
        reply = preview["message"]
        cards = [{"kind": "Obsidian", "title": note["filename"], "summary": note["content"].split("\n")[6] if note.get("content") else "Markdown note", "target": note["filename"]} for note in preview["notes"]]
        learning_path = ["双语节点", "Markdown 双链", "证据来源", "学习路径"]
    elif role_key == "teacher" and any(key in msg for key in ["薄弱", "班级", "看板", "干预"]):
        intent, action, target_module = "teaching_analytics", "navigate", "teacher"
        reply = "已打开教师看板，重点查看常见遗漏、干预名单和引用准确率。"
        dashboard = read_json("teacher_dashboard.json")
        cards = [{"kind": "薄弱点", "title": item, "summary": "建议加入下一节课讲评", "target": item} for item in dashboard.get("common_missing_points", [])]
        learning_path = dashboard.get("teaching_suggestions", learning_path)
    elif case and any(key in msg for key in ["打开", "练", "病例", "做错"]):
        intent, action, target_module = "navigation", "open_case", "training"
        target_case_id = case["id"]
        reply = f"已为你打开{case['title']}病例。"
        cards = [{"kind": "病例", "title": case["title"], "summary": case["chief_complaint"], "target": case["id"]}]
        learning_path = case.get("recommended_retraining", learning_path)
    elif exercise and any(key in msg for key in ["解剖", "位置", "定位", "练"]):
        intent, action, target_module = "navigation", "open_anatomy", "anatomy"
        target_exercise_id = exercise["id"]
        reply = f"已跳转到{exercise['title']}。"
        cards = [{"kind": "解剖练习", "title": exercise["title"], "summary": exercise["prompt"], "target": exercise["id"]}]
        learning_path = [exercise["target"], *exercise.get("graph_node_ids", [])]
    elif any(key in msg for key in ["教师", "看板", "班级"]):
        intent, action, target_module = "navigation", "navigate", "teacher"
        reply = "已为你打开教师看板。"
    elif any(key in msg for key in ["报告", "训练报告"]):
        intent, action, target_module = "navigation", "navigate", "report"
        reply = "已跳转到训练报告。"
    elif any(key in msg.lower() for key in ["关系", "路径", "哪些内容", "学什么", "鉴别", "acs", "graph"]):
        intent, action, target_module = "graph_retrieval", "show_results", "graph"
        reply = "已基于知识库、mock embedding 和双语知识图谱生成关联学习路径。"
    return AgentChatResponse(intent=intent, action=action, target_module=target_module, target_case_id=target_case_id, target_exercise_id=target_exercise_id, reply=reply, result_cards=cards, learning_path=learning_path, workflow_trace=build_trace(msg, active_module, "navigation" if action in {"navigate", "open_case", "open_anatomy"} else "graph"), safety_notes=safety_notes())


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "app": settings.app_name, "environment": settings.environment, "rag_provider": settings.rag_provider, "vector_stores": {"chroma_db_path": settings.chroma_db_path, "milvus_uri": settings.milvus_uri}, "tts_provider": settings.tts_provider}


@app.get("/api/site/overview")
def site_overview() -> dict:
    return {"name": "临思智训", "subtitle": "AI标准化病人临床思维训练平台", "contest_track": "AI+医学教育交叉", "positioning": "整合AI标准化病人、教材学习路径、ModelScope 数据源规划、Hybrid RAG、双语知识图谱和超级管理员闭环。", "metrics": [{"label": "虚拟病例", "value": "8个", "trend": "差异化脚本"}, {"label": "知识条目", "value": "85条", "trend": "双语mock"}, {"label": "图谱规模", "value": "177/162", "trend": "节点/关系"}, {"label": "数据源", "value": "7类", "trend": "含ModelScope"}], "scenarios": ["学生端", "教师端", "超级管理员"]}


@app.post("/api/auth/login", response_model=AuthLoginResponse)
def auth_login(payload: AuthLoginRequest) -> AuthLoginResponse:
    passwords = {"admin": "admin123", "student": "student123", "student01": "student123", "teacher": "teacher123", "teacher01": "teacher123"}
    if passwords.get(payload.account) != payload.password:
        raise HTTPException(status_code=401, detail="账号或密码错误")
    users = load_admin_users()
    user = next((item for item in users if item["account"] == payload.account), None)
    if user is None and payload.account == "teacher":
        user = next(item for item in users if item["role"] == "teacher")
    if user is None and payload.account == "student":
        user = next(item for item in users if item["role"] == "student")
    if user is None:
        raise HTTPException(status_code=401, detail="账号未配置")
    token = f"mock-{user['role']}-{user['account']}-token"
    return AuthLoginResponse(token=token, user=AuthUser(**user))


@app.get("/api/auth/me", response_model=AuthUser)
def auth_me(authorization: str | None = Header(default=None)) -> AuthUser:
    users = load_admin_users()
    if authorization:
        token = authorization.replace("Bearer", "").strip()
        for user in users:
            if user["account"] in token:
                return AuthUser(**user)
    return AuthUser(**users[0])


@app.post("/api/auth/logout")
def auth_logout() -> dict[str, str]:
    return {"status": "ok", "message": "已退出演示登录"}


@app.get("/api/cases", response_model=list[CaseSummary])
def cases() -> list[CaseSummary]:
    return [CaseSummary(**{**case, "opening": case.get("script", {}).get("opening", "")}) for case in read_json("cases.json")]


@app.get("/api/cases/{case_id}")
def case_detail(case_id: str) -> dict[str, Any]:
    return get_case_data(case_id)


@app.post("/api/patient/chat", response_model=PatientChatResponse)
@app.post("/api/training/chat", response_model=PatientChatResponse)
def patient_chat(payload: PatientChatRequest) -> PatientChatResponse:
    case = get_case_data(payload.case_id)
    citations = rag_pipeline.retrieve(f"{case['title']} {payload.message}", limit=3)
    reply = patient_reply(case, payload.message)
    scores = score_message(payload.message, payload.history, case)
    missed = missing_points(payload.message, payload.history, citations, case)
    hint = f"请继续围绕{case['title']}的关键得分点推进：{'、'.join(case.get('key_scoring_points', [])[:3])}。"
    return PatientChatResponse(patient_reply=ChatMessage(role="patient", content=reply, citations=[]), tutor_hint=hint, scores=scores, missing_points=missed, workflow_trace=build_trace(payload.message, case["title"], "patient"), citations=citations, safety_notes=safety_notes())


@app.post("/api/training/score")
def training_score(payload: TrainingScoreRequest) -> dict[str, Any]:
    case = get_case_data(payload.case_id)
    combined = " ".join([payload.preliminary_diagnosis, " ".join(payload.differentials), payload.treatment_principles, " ".join(payload.exams), " ".join(payload.citations)])
    citations = rag_pipeline.retrieve(combined, 2)
    return {"case_id": payload.case_id, "scores": score_message(combined, payload.history, case), "summary": "已完成过程性评分，建议教师复核高风险扣分项。", "missing_points": missing_points(combined, payload.history, citations, case)}


@app.get("/api/reports/{student_id}")
def student_reports(student_id: str) -> list[dict[str, Any]]:
    return [{"student_id": student_id, "created_at": "2026-07-27", "report": training_report("emergency_chest_pain").model_dump()}]


@app.get("/api/training/report", response_model=TrainingReport)
def training_report(case_id: str = "emergency_chest_pain") -> TrainingReport:
    case = get_case_data(case_id)
    citations = rag_pipeline.retrieve(f"{case['title']} {' '.join(case.get('recommended_retraining', []))}", limit=4)
    return TrainingReport(case_id=case_id, diagnosis_path=[case["chief_complaint"], "补全现病史和高危线索", "提出核心鉴别诊断", "选择必要检查", "依据指南更新诊断路径"], strengths=["能围绕主诉开展问诊", "能提出至少一个重点鉴别"], improvements=[item["text"] for item in case.get("high_risk_omissions", [])[:3]], recommended_cases=case.get("recommended_retraining", [])[:4], citations=citations)


@app.get("/api/guidelines")
def guidelines() -> list[dict[str, Any]]:
    return read_json("guidelines.json")


@app.get("/api/knowledge")
def knowledge() -> list[dict[str, Any]]:
    return read_json("knowledge.json")


@app.get("/api/knowledge/search")
def knowledge_search(q: str = "", lang: str = "zh") -> dict[str, Any]:
    query = q or "胸痛"
    bundle = hybrid_service.query(query, lang=lang)
    return {"query": q, "count": len(bundle["matched_knowledge"]), "items": search_items(query, lang=lang), **bundle}


@app.get("/api/teacher/dashboard")
def teacher_dashboard() -> dict[str, Any]:
    return read_json("teacher_dashboard.json")


@app.get("/api/knowledge-graph")
@app.get("/api/graph")
def knowledge_graph(lang: str = "zh") -> dict[str, Any]:
    graph = read_json("medical_kg_bilingual.json")
    nodes = []
    for node in graph["nodes"]:
        node_group = node.get("group") or node.get("type")
        label = node.get("label_en") if lang == "en" else node.get("label_zh")
        nodes.append({**node, "label": label or node.get("label", node["id"]), "group": node_group})
    edges = [{**edge, "relation": edge.get("relation_en") if lang == "en" else edge.get("relation_zh", edge.get("relation", "关联"))} for edge in graph["edges"]]
    return {"nodes": nodes, "edges": edges}


@app.get("/api/graph/search")
def graph_search(q: str = "", query: str = "", node_type: str = "", lang: str = "zh") -> dict[str, Any]:
    search_text = query or q
    nodes = graph_service.search_nodes(search_text, node_type=node_type, lang=lang)
    neighborhood = graph_service.get_neighbors(nodes[0]["id"], depth=2, lang=lang) if nodes else {"nodes": [], "edges": []}
    return {"query": search_text, "nodes": nodes[:16], "edges": neighborhood["edges"][:32], "neighbors": neighborhood["nodes"][:24], "learning_path": graph_service.build_learning_path(search_text, lang=lang)}


@app.get("/api/workflow")
def workflow() -> dict:
    return load_workflow()


@app.post("/api/rag/query", response_model=RagAnswer)
def rag_query(payload: RagQuery) -> RagAnswer:
    answer, citations, notes = rag_pipeline.answer(payload.question, payload.scenario)
    bundle = hybrid_service.query(payload.question)
    return RagAnswer(answer=answer, citations=citations, workflow_trace=build_trace(payload.question, payload.scenario, "graph"), safety_notes=notes, matched_knowledge=bundle["matched_knowledge"], graph_nodes=bundle["graph_nodes"], graph_edges=bundle["graph_edges"], bilingual_terms=bundle["bilingual_terms"], related_cases=bundle["related_cases"], related_anatomy_exercises=bundle["related_anatomy_exercises"], recommended_learning_path=bundle["recommended_learning_path"])


@app.post("/api/rag/hybrid-query")
def rag_hybrid_query(payload: RagQuery, lang: str = "zh") -> dict[str, Any]:
    bundle = hybrid_service.query(payload.question, lang=lang)
    return {"query": payload.question, "scenario": payload.scenario, **bundle, "safety_notes": safety_notes()}


@app.post("/api/rag/index")
def rag_index() -> dict[str, Any]:
    return rag_pipeline.write_vector_store()


@app.get("/api/textbook-pathways")
def textbook_pathways() -> list[dict[str, Any]]:
    return load_textbook_pathways()


@app.get("/api/admin/users")
def admin_users() -> list[dict[str, Any]]:
    return load_admin_users()


@app.get("/api/admin/data-sources")
def admin_data_sources() -> list[dict[str, Any]]:
    return load_data_sources()


@app.post("/api/admin/data-sources/sync")
def admin_data_sources_sync() -> dict[str, Any]:
    return {"status": "mock_queued", "message": "已模拟提交数据源同步任务，真实环境需先完成授权、许可和脱敏审查。", "sources": load_data_sources()}


@app.get("/api/admin/knowledge-status")
def admin_knowledge_status() -> dict[str, Any]:
    knowledge_items = read_json("knowledge.json")
    return {"items": len(knowledge_items), "bilingual_items": sum(1 for item in knowledge_items if item.get("title_en")), "vector_ready": sum(1 for item in knowledge_items if item.get("vector_status") == "mock_ready"), "sources": sorted({item.get("data_source", "mock") for item in knowledge_items})}


@app.get("/api/admin/graph-status")
def admin_graph_status() -> dict[str, Any]:
    graph = read_json("medical_kg_bilingual.json")
    node_types: dict[str, int] = {}
    for node in graph["nodes"]:
        node_types[node.get("type", node.get("group", "Unknown"))] = node_types.get(node.get("type", node.get("group", "Unknown")), 0) + 1
    return {"nodes": len(graph["nodes"]), "edges": len(graph["edges"]), "node_types": node_types, "obsidian_ready": True, "neo4j_status": "env_placeholder"}


@app.post("/api/admin/obsidian/export")
def admin_obsidian_export() -> dict[str, Any]:
    return obsidian_service.export_preview()


@app.post("/api/agent/chat", response_model=AgentChatResponse)
def agent_chat(payload: AgentChatRequest) -> AgentChatResponse:
    return resolve_agent(payload.message, payload.role, payload.active_module)


@app.get("/api/anatomy")
def anatomy() -> list[dict[str, Any]]:
    return read_json("anatomy.json")


@app.post("/api/anatomy/submit", response_model=AnatomySubmitResponse)
def anatomy_submit(payload: AnatomySubmitRequest) -> AnatomySubmitResponse:
    exercise = next((item for item in read_json("anatomy.json") if item["id"] == payload.exercise_id), read_json("anatomy.json")[0])
    correct = payload.selected_zone == exercise["answer_zone"]
    score = 94 if correct else 56
    feedback = "定位正确，能把解剖结构和临床场景联系起来。" if correct else f"你选择的位置不在{exercise['target']}标准区域。{exercise['explanation']}"
    if not correct and exercise["target"] == "胃":
        feedback = "你的位置偏右，胃主要位于左上腹，毗邻肝左叶、脾脏和胰腺。"
    return AnatomySubmitResponse(correct=correct, score_items=[ScoreItem(name="定位准确性", score=score, feedback=feedback), ScoreItem(name="解剖名称掌握", score=86 if correct else 62, feedback="请继续巩固结构名称和分区。"), ScoreItem(name="临床关联理解", score=88 if correct else 60, feedback=exercise["clinical_link"]), ScoreItem(name="错误原因分析", score=90 if correct else 68, feedback="已给出复习建议。")], feedback=feedback, explanation=exercise["explanation"], clinical_link=exercise["clinical_link"])


@app.post("/api/tts/speak", response_model=TTSResponse)
def tts_speak(payload: TTSRequest) -> TTSResponse:
    return TTSResponse(status="mock_ready", voice=payload.voice, duration_seconds=max(2, min(18, len(payload.text) // 18)), audio_url=None, message="已模拟生成数字人导师语音，真实TTS可通过.env配置接入。")


if __name__ == "__main__":
    uvicorn.run("backend.app.main:app", host=settings.backend_host, port=settings.backend_port, reload=True)


