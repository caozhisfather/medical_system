from __future__ import annotations

import json
from typing import Any
from uuid import uuid4

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
    TrainingReport, TrainingScoreRequest, CaseRandomRequest, TrainingStartRequest, TrainingOrderTestRequest, TrainingDiagnosisRequest, CaseValidateRequest,
    TeacherCaseDraftRequest, TeacherCaseEditRequest, TeacherCaseDecisionRequest, TeacherRecommendationDecisionRequest,
)
from .services.case_generation_service import CaseGenerationService
from .services.case_citation_service import CaseCitationService
from .services.case_repository import CaseRepository
from .services.case_source_adapter import CaseSourceAdapter
from .services.case_validation_service import CaseValidationService
from .services.patient_agent_service import PatientAgent
from .services.scoring_service import ScoringAgent
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
case_repository = CaseRepository()
case_citation_service = CaseCitationService(
    json.loads((DATA_DIR / "guidelines.json").read_text(encoding="utf-8"))
)
patient_agent = PatientAgent()
scoring_agent = ScoringAgent()
case_generator = CaseGenerationService()
case_validator = CaseValidationService()
case_source_adapter = CaseSourceAdapter()
training_sessions: dict[str, dict[str, Any]] = {}
TEACHER_CASE_STATE_FILE = DATA_DIR / "teacher_case_workbench.json"
_teacher_case_state = json.loads(TEACHER_CASE_STATE_FILE.read_text(encoding="utf-8")) if TEACHER_CASE_STATE_FILE.exists() else {"drafts": [], "recommendation_decisions": {}}
teacher_case_drafts: dict[str, dict[str, Any]] = {item["draft_id"]: item for item in _teacher_case_state.get("drafts", [])}
teacher_recommendation_decisions: dict[str, dict[str, str]] = _teacher_case_state.get("recommendation_decisions", {})


def read_json(name: str) -> Any:
    return json.loads((DATA_DIR / name).read_text(encoding="utf-8"))


def persist_teacher_case_state() -> None:
    payload = {"drafts": list(teacher_case_drafts.values()), "recommendation_decisions": teacher_recommendation_decisions}
    temporary = TEACHER_CASE_STATE_FILE.with_suffix(".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(TEACHER_CASE_STATE_FILE)


def get_case_data(case_id: str, variant_id: str | None = None) -> dict[str, Any]:
    draft = teacher_case_drafts.get(case_id)
    if draft and draft["case"].get("review_status") == "已批准":
        return json.loads(json.dumps(draft["case"], ensure_ascii=False))
    try:
        return case_repository.get(case_id, variant_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"病例不存在：{case_id}") from exc


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
    elif "随机" in msg and any(key in msg for key in ["病例", "训练", "呼吸", "气促"]):
        symptom = "呼吸困难" if any(key in msg for key in ["呼吸", "气促"]) else ""
        try:
            selected = case_repository.random(symptom=symptom)
        except LookupError:
            selected = case_repository.random()
        intent, action, target_module = "navigation", "open_case", "training"
        target_case_id = selected["case_id"]
        reply = f"已随机抽取{selected['title_zh']}（变体{selected.get('active_variant', 'A')}）。"
        cards = [{"kind": "病例", "title": selected["title_zh"], "summary": selected["chief_complaint"], "target": selected["case_id"]}]
        learning_path = selected.get("recommended_followups", learning_path)
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
    return {"name": "临思智训", "subtitle": "AI标准化病人临床思维训练平台", "contest_track": "AI+医学教育交叉", "positioning": "整合AI标准化病人、教材学习路径、ModelScope 数据源规划、Hybrid RAG、双语知识图谱和超级管理员闭环。", "metrics": [{"label": "虚拟病例", "value": "41个", "trend": "差异化脚本"}, {"label": "知识条目", "value": "85条", "trend": "双语mock"}, {"label": "图谱规模", "value": "177/162", "trend": "节点/关系"}, {"label": "数据源", "value": "7类", "trend": "含ModelScope"}], "scenarios": ["学生端", "教师端", "超级管理员"]}


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


@app.get("/api/cases")
def cases() -> list[dict[str, Any]]:
    approved = [item["case"] for item in teacher_case_drafts.values() if item["case"].get("review_status") == "已批准"]
    return [*case_repository.all(), *approved]


@app.get("/api/cases/search")
def cases_search(q: str = "", department: str = "", symptom: str = "", difficulty: str = "", training_goal: str = "") -> dict[str, Any]:
    result = case_repository.search(q, department, symptom, difficulty, training_goal)
    return {"count": len(result), "items": result, "filters": {"q": q, "department": department, "symptom": symptom, "difficulty": difficulty, "training_goal": training_goal}}


@app.post("/api/cases/random")
def cases_random(payload: CaseRandomRequest) -> dict[str, Any]:
    try:
        return case_repository.random(payload.department, payload.symptom, payload.difficulty, payload.training_goal)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/cases/{case_id}/variants")
def case_variants(case_id: str) -> dict[str, Any]:
    case = get_case_data(case_id)
    return {"case_id": case_id, "core_diagnosis_locked": True, "variants": case["case_variants"]}


@app.get("/api/cases/{case_id}")
def case_detail(case_id: str, variant_id: str = "A") -> dict[str, Any]:
    return get_case_data(case_id, variant_id)


@app.post("/api/training/start")
def training_start(payload: TrainingStartRequest) -> dict[str, Any]:
    case = get_case_data(payload.case_id, payload.variant_id)
    session_id = f"TS-{uuid4().hex[:12]}"
    training_sessions[session_id] = {
        "session_id": session_id,
        "case_id": case["case_id"],
        "variant_id": case.get("active_variant", payload.variant_id),
        "difficulty": payload.difficulty or case["difficulty"],
        "mode": payload.mode,
        "history": [],
        "ordered_tests": [],
        "diagnosis_submission": {},
    }
    return {
        "session_id": session_id,
        "case": case,
        "opening_statement": case["opening_statement"],
        "available_tests": [{"test_name": item["test_name"], "locked": True} for item in case["available_tests"]],
        "safety_notes": safety_notes(),
    }


def _session_or_request(payload: PatientChatRequest) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    session = training_sessions.get(payload.session_id or "")
    if session:
        return session, get_case_data(session["case_id"], session["variant_id"])
    return None, get_case_data(payload.case_id, payload.variant_id)


@app.post("/api/patient/chat")
@app.post("/api/training/chat")
def patient_chat(payload: PatientChatRequest) -> dict[str, Any]:
    session, case = _session_or_request(payload)
    history = session["history"] if session else [item.model_dump() for item in payload.history]
    answer = patient_agent.answer(case, payload.message)
    if session is not None:
        session["history"].extend([
            {"role": "student", "content": payload.message},
            {"role": "patient", "content": answer["reply"]},
        ])
        if answer.get("ordered_test") and answer["ordered_test"] not in session["ordered_tests"]:
            session["ordered_tests"].append(answer["ordered_test"])
    transcript = " ".join(item.get("content", "") for item in history) + " " + payload.message
    score_result = scoring_agent.score(case, transcript, (session or {}).get("ordered_tests", []))
    retrieved = rag_pipeline.retrieve(f"{case['title_zh']} {payload.message}", limit=3)
    citations = case_citation_service.for_case(case, retrieved, limit=3)
    return {
        "session_id": session["session_id"] if session else None,
        "case_id": case["case_id"],
        "variant_id": case.get("active_variant", "A"),
        "patient_reply": {"role": "patient", "content": answer["reply"], "citations": []},
        "matched_field": answer["matched_field"],
        "revealed_diagnosis": answer["revealed_diagnosis"],
        "ordered_test": answer.get("ordered_test"),
        "tutor_hint": f"请继续围绕{case['title_zh']}的独立评分点推进：{'、'.join(case['key_scoring_points'][:3])}。",
        "scores": score_result["scores"],
        "missing_points": score_result["missing_points"][:5],
        "workflow_trace": build_trace(payload.message, case["title_zh"], "patient"),
        "citations": citations,
        "safety_notes": safety_notes(),
    }


@app.post("/api/training/order-test")
def training_order_test(payload: TrainingOrderTestRequest) -> dict[str, Any]:
    session = training_sessions.get(payload.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="训练会话不存在或已失效")
    case = get_case_data(session["case_id"], session["variant_id"])
    result = patient_agent.order_test(case, payload.test_name)
    if result["available"] and result["test_name"] not in session["ordered_tests"]:
        session["ordered_tests"].append(result["test_name"])
    return {"session_id": payload.session_id, "case_id": case["case_id"], **result, "ordered_tests": session["ordered_tests"]}


@app.post("/api/training/submit-diagnosis")
def training_submit_diagnosis(payload: TrainingDiagnosisRequest) -> dict[str, Any]:
    session = training_sessions.get(payload.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="训练会话不存在或已失效")
    session["diagnosis_submission"] = payload.model_dump(exclude={"session_id"})
    case = get_case_data(session["case_id"], session["variant_id"])
    result = scoring_agent.score(
        case,
        " ".join(item["content"] for item in session["history"]),
        session["ordered_tests"],
        payload.preliminary_diagnosis,
        payload.differentials,
        payload.treatment_principles,
        payload.medication_plan,
        payload.citations,
    )
    return {"status": "submitted", **result}


@app.post("/api/training/score")
def training_score(payload: TrainingScoreRequest) -> dict[str, Any]:
    session = training_sessions.get(payload.session_id or "")
    if session:
        case = get_case_data(session["case_id"], session["variant_id"])
        transcript = " ".join(item["content"] for item in session["history"])
        ordered_tests = list(dict.fromkeys([*session["ordered_tests"], *payload.exams]))
    else:
        case = get_case_data(payload.case_id, payload.variant_id)
        transcript = " ".join(item.content for item in payload.history)
        ordered_tests = payload.exams
    return scoring_agent.score(case, transcript, ordered_tests, payload.preliminary_diagnosis, payload.differentials, payload.treatment_principles, payload.medication_plan, payload.citations)


@app.get("/api/training/recommendations")
def training_recommendations(case_id: str = "", focus: str = "") -> dict[str, Any]:
    cases = case_repository.all()
    active = get_case_data(case_id) if case_id else cases[0]
    related = [item for item in cases if item["case_id"] != active["case_id"] and (item["department"] == active["department"] or set(item["symptom_tags"]) & set(active["symptom_tags"]))]
    retraining = [item for item in cases if any(term in " ".join(item["training_goals"]) for term in (active["recommended_followups"] + [focus]) if term)]
    return {
        "today": cases[:3],
        "retraining": (retraining or related)[:3],
        "similar": related[:4],
        "based_on_case_id": active["case_id"],
    }

@app.get("/api/reports/{student_id}")
def student_reports(student_id: str) -> list[dict[str, Any]]:
    return [{"student_id": student_id, "created_at": "2026-07-27", "report": training_report("emergency_chest_pain").model_dump()}]


@app.get("/api/training/report", response_model=TrainingReport)
def training_report(case_id: str = "emergency_chest_pain") -> TrainingReport:
    case = get_case_data(case_id)
    retrieved = rag_pipeline.retrieve(
        f"{case['title_zh']} {' '.join(case.get('recommended_retraining', []))}",
        limit=4,
    )
    citations = case_citation_service.for_case(case, retrieved, limit=4)
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


def _teacher_case_recommendations() -> dict[str, Any]:
    dashboard = read_json("teacher_dashboard.json")
    risk_rankings = dashboard.get("risk_rankings", [])
    top_risk_count = risk_rankings[0].get("count", 0) if risk_rankings else 0
    recommendations = [
        {
            "id": "rec_fatal_chest_pain",
            "rank": 1,
            "score": min(98, 60 + top_risk_count),
            "title": "增加致命性胸痛鉴别进阶病例",
            "reason": f"{top_risk_count} 名学生出现“未排除主动脉夹层”，是当前最高频高风险遗漏。",
            "target_students": "高危鉴别薄弱学生",
            "expected_impact": "降低致命性胸痛遗漏率",
            "evidence": dashboard.get("common_missing_points", [])[:3],
            "suggested_case": {"title": "突发胸背痛的高风险鉴别", "department": "急诊医学", "chief_complaint": "突发胸背部剧烈疼痛1小时", "learning_goal": "主动脉夹层与急性冠脉综合征的优先鉴别", "difficulty": "高阶", "suspected_diagnosis": "主动脉夹层待排"},
        },
        {
            "id": "rec_exam_priority",
            "rank": 2,
            "score": 89,
            "title": "补充检查优先级决策病例",
            "reason": "班级共性问题包含心电图、肌钙蛋白等关键检查申请不及时。",
            "target_students": "检查选择薄弱学生",
            "expected_impact": "提升检查选择与时序决策评分",
            "evidence": dashboard.get("teaching_suggestions", [])[:2],
            "suggested_case": {"title": "胸痛检查时序训练", "department": "心血管内科", "chief_complaint": "活动后胸痛伴大汗30分钟", "learning_goal": "根据风险和时效选择心电图、肌钙蛋白及影像检查", "difficulty": "进阶", "suspected_diagnosis": "急性冠脉综合征待排"},
        },
        {
            "id": "rec_evidence_reasoning",
            "rank": 3,
            "score": 84,
            "title": "增加指南证据引用专项病例",
            "reason": f"当前指南引用准确率为 {dashboard.get('citation_accuracy', '待统计')}，仍可通过专项病例强化证据与决策关联。",
            "target_students": "证据引用薄弱学生",
            "expected_impact": "提高指南依据的准确性与可追溯性",
            "evidence": [item.get("label", str(item)) for item in dashboard.get("improvements", [])[:2]],
            "suggested_case": {"title": "循证处置方案训练", "department": "全科医学科", "chief_complaint": "慢性病复诊并咨询用药调整", "learning_goal": "引用指南证据解释检查和处理方案", "difficulty": "进阶", "suspected_diagnosis": "慢性病随访评估"},
        },
    ]
    for item in recommendations:
        item["decision"] = teacher_recommendation_decisions.get(item["id"], {"action": "pending", "note": ""})
    return {
        "analysis": {
            "training_sessions": dashboard.get("training_sessions", 0) + len(training_sessions),
            "class_average": dashboard.get("class_average", 0),
            "common_missing_points": dashboard.get("common_missing_points", []),
            "students_analyzed": len(dashboard.get("students", [])),
        },
        "algorithm": "按高风险遗漏频次、薄弱能力覆盖度和预期教学收益进行加权排序；AI 只提供建议，教师保留最终决策权。",
        "recommendations": recommendations,
    }


@app.get("/api/teacher/case-drafts")
def teacher_case_draft_list() -> list[dict[str, Any]]:
    return list(reversed(list(teacher_case_drafts.values())))


@app.post("/api/teacher/case-drafts/generate")
def teacher_case_draft_generate(payload: TeacherCaseDraftRequest) -> dict[str, Any]:
    analytics = _teacher_case_recommendations()["analysis"]
    analytics.update(read_json("teacher_dashboard.json"))
    draft = case_generator.generate_teacher_draft(payload.model_dump(), analytics)
    teacher_case_drafts[draft["draft_id"]] = draft
    persist_teacher_case_state()
    return draft


@app.patch("/api/teacher/case-drafts/{draft_id}")
def teacher_case_draft_edit(draft_id: str, payload: TeacherCaseEditRequest) -> dict[str, Any]:
    draft = teacher_case_drafts.get(draft_id)
    if draft is None:
        raise HTTPException(status_code=404, detail="病例草稿不存在")
    updates = payload.model_dump(exclude_none=True)
    case = draft["case"]
    field_map = {"title": "title", "department": "department", "chief_complaint": "chief_complaint", "difficulty": "difficulty", "suspected_diagnosis": "hidden_final_diagnosis", "teacher_note": "teacher_note"}
    for source, target in field_map.items():
        if source in updates:
            case[target] = updates[source]
    if "title" in updates:
        case["title_zh"] = updates["title"]
    if "present_illness" in updates:
        case["present_illness"] = updates["present_illness"]
        case["history"]["present_illness"] = [updates["present_illness"]]
    if "learning_goal" in updates:
        case["training_goals"][0] = updates["learning_goal"]
        case["learning_goals"][0] = updates["learning_goal"]
        case["specialty"] = updates["learning_goal"][:30]
    case["review_status"] = "待教师审核"
    draft["validation"] = case_validator.validate(case)
    draft["workflow"][-1].update({"status": "waiting", "detail": "病例已编辑，等待教师最终决策。"})
    persist_teacher_case_state()
    return draft


@app.post("/api/teacher/case-drafts/{draft_id}/decision")
def teacher_case_draft_decision(draft_id: str, payload: TeacherCaseDecisionRequest) -> dict[str, Any]:
    draft = teacher_case_drafts.get(draft_id)
    if draft is None:
        raise HTTPException(status_code=404, detail="病例草稿不存在")
    statuses = {"approve": "已批准", "reject": "已拒绝", "request_revision": "退回修改"}
    if payload.action not in statuses:
        raise HTTPException(status_code=400, detail="不支持的教师决策")
    if payload.action == "approve" and not draft["validation"]["valid"]:
        raise HTTPException(status_code=400, detail="病例校验未通过，不能批准发布")
    draft["case"]["review_status"] = statuses[payload.action]
    draft["case"]["teacher_note"] = payload.note
    draft["decision"] = {"action": payload.action, "note": payload.note, "decided_by": "当前教师"}
    draft["workflow"][-1].update({"status": "done", "detail": f"教师决策：{statuses[payload.action]}。{payload.note}"})
    persist_teacher_case_state()
    return draft


@app.get("/api/teacher/case-recommendations")
def teacher_case_recommendations() -> dict[str, Any]:
    return _teacher_case_recommendations()


@app.post("/api/teacher/case-recommendations/{recommendation_id}/decision")
def teacher_case_recommendation_decision(recommendation_id: str, payload: TeacherRecommendationDecisionRequest) -> dict[str, Any]:
    if payload.action not in {"accept", "dismiss"}:
        raise HTTPException(status_code=400, detail="不支持的推荐决策")
    teacher_recommendation_decisions[recommendation_id] = {"action": payload.action, "note": payload.note}
    persist_teacher_case_state()
    return {"recommendation_id": recommendation_id, "decision": teacher_recommendation_decisions[recommendation_id]}


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


@app.get("/api/data-sources")
def public_data_sources() -> list[dict[str, Any]]:
    return load_data_sources()


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


@app.post("/api/admin/cases/generate-mock")
def admin_cases_generate_mock(source: dict[str, Any] | None = None) -> dict[str, Any]:
    return case_generator.generate_mock(source)


@app.post("/api/admin/cases/validate")
def admin_cases_validate(payload: CaseValidateRequest) -> dict[str, Any]:
    if payload.case_data is not None:
        return case_validator.validate(payload.case_data)
    if payload.case_id:
        return case_validator.validate(get_case_data(payload.case_id))
    results = [case_validator.validate(case) for case in case_repository.all()]
    return {"valid": all(item["valid"] for item in results), "count": len(results), "results": results}


@app.get("/api/admin/cases/source-plan")
def admin_cases_source_plan() -> dict[str, Any]:
    return {
        "sources": case_source_adapter.plan(),
        "policy": "仅将公开来源用于字段设计和自行摘要；接入前必须完成许可、伦理、隐私与脱敏审查。",
    }

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








