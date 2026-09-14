from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from threading import Lock
from typing import Any
from uuid import uuid4

import uvicorn
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.wsgi import WSGIMiddleware

from .api.daily_review import router as daily_review_router
from .api.digital_human import router as digital_human_router
from .api.sparkos import router as sparkos_router
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
    CaseLibraryEntryCreateRequest, CaseLibraryEntryUpdateRequest, CaseLibraryDeidentifyRequest, CaseLibraryImportRequest,
    CaseLibraryCompileRequest, TeachingKnowledgeCreateRequest, TeachingKnowledgeUpdateRequest,
)
from .services.case_generation_service import CaseGenerationService
from .services.case_citation_service import CaseCitationService
from .services.case_knowledge_service import CaseKnowledgeService
from .services.case_repository import CaseRepository
from .services.case_source_adapter import CaseSourceAdapter
from .services.case_validation_service import CaseValidationService
from .services.daily_review_service import DailyReviewService
from .services.patient_agent_service import PatientAgent
from .services.recommendation_service import rank_cases
from .services.llm_patient_service import llm_patient_service
from .services.scoring_service import ScoringAgent
from .services.anatomy_textbook_service import anatomy_textbook_service
from .services.anatomy_term_service import anatomy_term_service
from .services.history_taking_service import history_taking_service
from .rag import RagPipeline
from .workflow import build_trace, load_workflow

DATA_DIR = ROOT_DIR / "data"
app = FastAPI(title="AI标准化病人临床思维训练平台", version="0.4.0")
app.add_middleware(CORSMiddleware, allow_origins=[settings.frontend_origin, "http://localhost:5173", "http://127.0.0.1:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.mount("/flask", WSGIMiddleware(create_flask_app()))
app.include_router(daily_review_router)
app.include_router(digital_human_router)
app.include_router(sparkos_router)
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
case_knowledge_service = CaseKnowledgeService()
document_processing: dict[str, Any] = {"running": False, "pid": None}
embedding_processing: dict[str, Any] = {"running": False, "pid": None}
TRAINING_SESSION_FILE = DATA_DIR / "training_sessions.json"
try:
    training_sessions: dict[str, dict[str, Any]] = json.loads(TRAINING_SESSION_FILE.read_text(encoding="utf-8")) if TRAINING_SESSION_FILE.exists() else {}
except (OSError, json.JSONDecodeError):
    training_sessions = {}
TEACHER_CASE_STATE_FILE = DATA_DIR / "teacher_case_workbench.json"
AUDIT_LOG_FILE = DATA_DIR / "audit_logs.jsonl"
AUDIT_LOG_LOCK = Lock()
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


def persist_training_sessions() -> None:
    temporary = TRAINING_SESSION_FILE.with_suffix(".tmp")
    temporary.write_text(json.dumps(training_sessions, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(TRAINING_SESSION_FILE)


def require_role(authorization: str | None, allowed_roles: set[str]) -> AuthUser:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="请先登录")
    token = authorization[7:].strip()
    users = load_admin_users()
    for item in users:
        expected = f"mock-{item['role']}-{item['account']}-token"
        if token == expected:
            user = AuthUser(**item)
            if user.status != "active":
                raise HTTPException(status_code=403, detail="账号当前不可用")
            if user.role not in allowed_roles:
                raise HTTPException(status_code=403, detail="没有权限访问该接口")
            return user
    raise HTTPException(status_code=401, detail="登录状态无效或已过期")


def write_audit_log(user: AuthUser, action: str, target: str, detail: str = "") -> None:
    entry = {
        "id": f"audit-{uuid4().hex[:12]}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "account": user.account,
        "name": user.name,
        "role": user.role,
        "action": action,
        "target": target,
        "detail": detail[:500],
    }
    try:
        with AUDIT_LOG_LOCK, AUDIT_LOG_FILE.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError:
        # 审计存储故障不应中断教师正在进行的教学操作。
        return


def read_audit_logs(limit: int = 100) -> list[dict[str, Any]]:
    if not AUDIT_LOG_FILE.exists():
        return []
    try:
        lines = AUDIT_LOG_FILE.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    records: list[dict[str, Any]] = []
    for line in reversed(lines[-limit:]):
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return records


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
    if role_key == "student" and any(key in msg for key in ["复盘", "今天哪里", "哪里做得不好", "明日计划", "今日总结"]):
        review = DailyReviewService().today("student_001")
        intent, action, target_module = "daily_review", "open_daily_review", "daily_review"
        reply = f"{review['summary']} 我已为你生成明日复训计划。"
        cards = [
            {"kind": "AI复盘总结", "title": "今日复盘", "summary": review["summary"], "target": review["review_id"]},
            {"kind": "薄弱点", "title": review["weak_points"][0], "summary": "点击后可进入病例、知识图谱或解剖训练。", "target": "acute_abdominal_pain"},
            {"kind": "明日计划", "title": "复训病例与图谱路径", "summary": "、".join(review["tomorrow_plan"][:2]), "target": "daily_review"},
        ]
        learning_path = review["recommended_graph_path"]
    elif active_module == "anatomy_lab":
        structure_match = re.search(r"结构：([^\n；]+)", msg)
        structure_name = structure_match.group(1).strip() if structure_match else "当前解剖结构"
        chinese_name = anatomy_term_service.lookup(structure_name)
        textbook_hit = anatomy_textbook_service.search(chinese_name or structure_name)
        if not textbook_hit and chinese_name and chinese_name != structure_name:
            textbook_hit = anatomy_textbook_service.search(structure_name)
        label = f"{chinese_name}（{structure_name}）" if chinese_name else structure_name
        if "空间关系" in msg:
            focus = "重点观察它与相邻器官、血管、神经及体表定位之间的前后、上下和内外关系。"
        elif "临床联系" in msg:
            focus = "可进一步关联该结构受损、压迫或阻塞时的典型表现，并回到教材核对适用范围。"
        elif "考试重点" in msg:
            focus = "建议按位置、形态、连接关系、功能和常见临床意义五个要点复习。"
        else:
            focus = "先掌握它的标准位置、主要组成和功能，再用定位测验确认空间认知。"
        intent, action, target_module = "anatomy_teaching", "explain_structure", "anatomy"
        citation = textbook_hit.get("citation") if textbook_hit else None
        reply = f"{label}教学提示：{focus}"
        if citation:
            reply += f" 已匹配教材依据：{citation}。"
        else:
            reply += " 暂未匹配到本地教材段落，建议打开教材详解或由教师补充依据。"
        reply += " 当前回答仅用于医学教育，具体结论请以已审核教材和教师讲解为准。"
        cards = [
            {"kind": "解剖结构", "title": label, "summary": "已读取三维模型结构上下文", "target": structure_name},
            {"kind": "教材依据", "title": textbook_hit.get("title", "检索权威教材") if textbook_hit else "检索权威教材", "summary": textbook_hit.get("content", "建议打开教材详解查看章节与页码") if textbook_hit else "建议打开教材详解查看章节与页码", "target": textbook_hit.get("citation", structure_name) if textbook_hit else structure_name},
        ]
        learning_path = [label, "教材依据", "空间定位测验", "知识图谱临床联系"]
    elif role_key == "teacher" and any(key in msg for key in ["班级复盘", "复盘", "教学建议", "今日班级"]):
        class_review = DailyReviewService().class_review()
        intent, action, target_module = "class_daily_review", "open_class_review", "class_review"
        reply = class_review["summary"]
        cards = [{"kind": "班级薄弱点", "title": item, "summary": "建议加入明日课堂讲评", "target": item} for item in class_review["common_weak_points"]]
        learning_path = class_review["teaching_suggestions"]
    elif role_key == "admin" and any(key in msg for key in ["复盘策略", "复盘配置", "生成时间", "教师预警"]):
        config = DailyReviewService().admin_config()
        intent, action, target_module = "admin_daily_review_config", "open_review_policy", "admin_review"
        reply = f"已打开复盘策略配置，当前生成时间为 {config['generate_time']}，复盘服务状态为 {config['service_status']}。"
        cards = [{"kind": "复盘策略", "title": "每日复盘配置", "summary": config["policy_note"], "target": "daily_review_policy"}]
        learning_path = ["评分权重", "推荐数量", "数字人复盘", "教师预警", "Mock 数据生成"]
    elif role_key == "admin" and any(key in msg.lower() for key in ["modelscope", "数据源", "同步", "rag配置", "后台"]):
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
    return {"status": "ok", "app": settings.app_name, "environment": settings.environment, "rag_provider": settings.rag_provider, "vector_stores": {"chroma_db_path": settings.chroma_db_path, "milvus_uri": settings.milvus_uri}, "tts_provider": settings.tts_provider, "active_training_sessions": len(training_sessions), "persistence": {"training_sessions": TRAINING_SESSION_FILE.exists(), "teacher_workbench": TEACHER_CASE_STATE_FILE.exists(), "audit_log": AUDIT_LOG_FILE.exists()}, "ai": {"llm_configured": bool(settings.openai_api_key), "llm_model": settings.openai_model, "sparkos_configured": bool(settings.sparkos_app_id and settings.sparkos_api_key and settings.sparkos_api_secret)}}


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
    return require_role(authorization, {"student", "teacher", "admin", "super_admin"})


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
        "patient_state": {"stage": "chief_complaint", "completed": [], "progress": 0},
        "ordered_tests": [],
        "diagnosis_submission": {},
    }
    persist_training_sessions()
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


def _advance_patient_state(session: dict[str, Any] | None, answer: dict[str, Any]) -> dict[str, Any]:
    state = (session or {}).setdefault("patient_state", {"stage": "chief_complaint", "completed": [], "progress": 0})
    field = str(answer.get("matched_field") or "")
    mapping = {
        "history.chief_complaint": ("chief_complaint", "主诉"),
        "history.present_illness": ("present_illness", "现病史"),
        "history.past_history": ("past_history", "既往史"),
        "history.medication_history": ("medication_history", "用药史"),
        "history.allergy_history": ("allergy_history", "过敏史"),
        "history.personal_history": ("personal_history", "个人史"),
        "history.family_history": ("family_history", "家族史"),
        "physical_exam": ("physical_exam", "查体"),
        "available_tests": ("tests", "检查"),
    }
    if field in mapping:
        key, label = mapping[field]
        completed = list(state.get("completed", []))
        if key not in completed: completed.append(key)
        state["completed"] = completed
        state["progress"] = min(100, round(len(completed) / 8 * 100))
        stages = ["chief_complaint", "present_illness", "past_history", "medication_history", "allergy_history", "physical_exam", "tests"]
        state["stage"] = next((item for item in stages if item not in completed), "clinical_decision")
        state["last_collected"] = label
    return state


@app.post("/api/patient/chat")
@app.post("/api/training/chat")
def patient_chat(payload: PatientChatRequest) -> dict[str, Any]:
    session, case = _session_or_request(payload)
    history = session["history"] if session else [item.model_dump() for item in payload.history]
    # 诊断泄露和检查申请先走确定性安全规则，其余问诊优先使用 LLM，失败时回退本地脚本。
    deterministic = patient_agent.answer(case, payload.message)
    answer = deterministic
    if not deterministic.get("ordered_test") and not deterministic.get("matched_field", "").endswith("diagnosis_guard"):
        answer = llm_patient_service.answer(case, payload.message, history) or deterministic
    if session is not None:
        session["history"].extend([
            {"role": "student", "content": payload.message},
            {"role": "patient", "content": answer["reply"]},
        ])
        if answer.get("ordered_test") and answer["ordered_test"] not in session["ordered_tests"]:
            session["ordered_tests"].append(answer["ordered_test"])
        persist_training_sessions()
    patient_state = _advance_patient_state(session, answer)
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
        "ai_provider": answer.get("provider", "本地规则患者"),
        "patient_state": patient_state,
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
        persist_training_sessions()
    return {"session_id": payload.session_id, "case_id": case["case_id"], **result, "ordered_tests": session["ordered_tests"]}


@app.post("/api/training/submit-diagnosis")
def training_submit_diagnosis(payload: TrainingDiagnosisRequest) -> dict[str, Any]:
    session = training_sessions.get(payload.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="训练会话不存在或已失效")
    session["diagnosis_submission"] = payload.model_dump(exclude={"session_id"})
    persist_training_sessions()
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
    ranked = rank_cases(cases, focus, active.get("case_id", ""))
    related = [item for item in cases if item["case_id"] != active["case_id"] and (item["department"] == active["department"] or set(item["symptom_tags"]) & set(active["symptom_tags"]))]
    retraining = [item for item in cases if any(term in " ".join(item["training_goals"]) for term in (active["recommended_followups"] + [focus]) if term)]
    return {
        "today": cases[:3],
        "retraining": (retraining or related)[:3],
        "similar": related[:4],
        "student_vector": ranked["student_vector"],
        "algorithm": ranked["algorithm"],
        "ranked": ranked["cases"][:6],
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
def teacher_dashboard(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    require_role(authorization, {"teacher", "admin", "super_admin"})
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
def teacher_case_draft_list(authorization: str | None = Header(default=None)) -> list[dict[str, Any]]:
    require_role(authorization, {"teacher", "admin", "super_admin"})
    return list(reversed(list(teacher_case_drafts.values())))


@app.post("/api/teacher/case-drafts/generate")
def teacher_case_draft_generate(payload: TeacherCaseDraftRequest, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    user = require_role(authorization, {"teacher", "admin", "super_admin"})
    analytics = _teacher_case_recommendations()["analysis"]
    analytics.update(read_json("teacher_dashboard.json"))
    draft = case_generator.generate_teacher_draft(payload.model_dump(), analytics)
    teacher_case_drafts[draft["draft_id"]] = draft
    persist_teacher_case_state()
    write_audit_log(user, "teacher.case.generate", draft["draft_id"], draft["case"].get("title", ""))
    return draft


@app.patch("/api/teacher/case-drafts/{draft_id}")
def teacher_case_draft_edit(draft_id: str, payload: TeacherCaseEditRequest, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    user = require_role(authorization, {"teacher", "admin", "super_admin"})
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
    write_audit_log(user, "teacher.case.edit", draft_id, ",".join(sorted(updates.keys())))
    return draft


@app.post("/api/teacher/case-drafts/{draft_id}/decision")
def teacher_case_draft_decision(draft_id: str, payload: TeacherCaseDecisionRequest, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    user = require_role(authorization, {"teacher", "admin", "super_admin"})
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
    draft["decision"] = {"action": payload.action, "note": payload.note, "decided_by": user.name}
    draft["workflow"][-1].update({"status": "done", "detail": f"教师决策：{statuses[payload.action]}。{payload.note}"})
    persist_teacher_case_state()
    write_audit_log(user, f"teacher.case.{payload.action}", draft_id, payload.note)
    return draft


@app.get("/api/teacher/case-recommendations")
def teacher_case_recommendations(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    require_role(authorization, {"teacher", "admin", "super_admin"})
    return _teacher_case_recommendations()


@app.post("/api/teacher/case-recommendations/{recommendation_id}/decision")
def teacher_case_recommendation_decision(recommendation_id: str, payload: TeacherRecommendationDecisionRequest, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    user = require_role(authorization, {"teacher", "admin", "super_admin"})
    if payload.action not in {"accept", "dismiss"}:
        raise HTTPException(status_code=400, detail="不支持的推荐决策")
    teacher_recommendation_decisions[recommendation_id] = {"action": payload.action, "note": payload.note}
    persist_teacher_case_state()
    write_audit_log(user, f"teacher.recommendation.{payload.action}", recommendation_id, payload.note)
    return {"recommendation_id": recommendation_id, "decision": teacher_recommendation_decisions[recommendation_id]}


@app.get("/api/teacher/case-library")
def case_knowledge_list(q: str = "", category: str = "", authorization: str | None = Header(default=None)) -> dict[str, Any]:
    require_role(authorization, {"teacher", "admin", "super_admin"})
    entries = case_knowledge_service.list(q or None, category or None)
    return {"total": len(entries), "items": entries, "categories": case_knowledge_service.categories()}


@app.get("/api/teacher/teaching-knowledge")
@app.get("/api/admin/teaching-knowledge")
def teaching_knowledge_list(q: str = "", category: str = "", knowledge_type: str = "", document_type: str = "", authorization: str | None = Header(default=None)) -> dict[str, Any]:
    require_role(authorization, {"teacher", "admin", "super_admin"})
    items = case_knowledge_service.list_teaching(q or None, category or None, knowledge_type or None, document_type or None)
    type_counts = {"all": len(case_knowledge_service.list_teaching()), "case": len(case_knowledge_service.list_teaching(document_type="case")), "textbook": len(case_knowledge_service.list_teaching(document_type="textbook")), "evidence": len(case_knowledge_service.list_teaching(document_type="evidence"))}
    return {"total": len(items), "items": items, "categories": case_knowledge_service.teaching_categories(), "type_counts": type_counts}


@app.post("/api/teacher/teaching-knowledge")
@app.post("/api/admin/teaching-knowledge")
def teaching_knowledge_create(payload: TeachingKnowledgeCreateRequest, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    user = require_role(authorization, {"teacher", "admin", "super_admin"})
    entry = case_knowledge_service.teaching_create(payload.model_dump())
    write_audit_log(user, "teacher.teaching-knowledge.create", entry["id"], entry.get("title", ""))
    return entry


@app.post("/api/admin/teaching-knowledge/upload")
async def teaching_knowledge_upload(request: Request, filename: str = "资料文件", document_type: str = "textbook", authorization: str | None = Header(default=None)) -> dict[str, Any]:
    """Save a source file and create an OCR-pending knowledge entry."""
    user = require_role(authorization, {"admin", "super_admin"})
    raw = await request.body()
    if not raw:
        raise HTTPException(status_code=400, detail="上传文件不能为空")
    safe_name = re.sub(r"[^\w.\-\u4e00-\u9fff]+", "_", filename or "资料文件")[:120]
    upload_dir = ROOT_DIR / "storage" / "knowledge_uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    stored = upload_dir / f"{uuid4().hex[:12]}_{safe_name}"
    stored.write_bytes(raw)
    if document_type not in {"textbook", "evidence", "case"}:
        raise HTTPException(status_code=422, detail="资料类型必须是 textbook、evidence 或 case")
    type_label = {"textbook": "教材", "evidence": "医学依据", "case": "病例"}[document_type]
    relative_path = str(stored.relative_to(ROOT_DIR))
    entry = case_knowledge_service.teaching_create({
        "knowledge_type": "case" if document_type == "case" else "textbook",
        "title": safe_name.rsplit(".", 1)[0],
        "category": f"待分类{type_label}",
        "source": f"上传文件：{safe_name}",
        "status": "待OCR",
        "processing_status": "OCR 待处理",
        "document_type": document_type,
        "document_scope": "whole_document",
        "source_path": relative_path,
    })
    write_audit_log(user, "admin.teaching-knowledge.upload", entry["id"], safe_name)
    return {"status": "accepted", "item": entry, "filename": safe_name, "bytes": len(raw)}


@app.post("/api/admin/teaching-knowledge/process")
def start_document_processing(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    user = require_role(authorization, {"admin", "super_admin"})
    process = document_processing.get("pid")
    if document_processing.get("running") and process:
        return {"status": "running", "pid": process}
    script = ROOT_DIR / "backend" / "scripts" / "extract_document_text.py"
    process = subprocess.Popen([sys.executable, str(script)], cwd=ROOT_DIR)
    document_processing.update({"running": True, "pid": process.pid, "started_at": datetime.now(timezone.utc).isoformat(timespec="seconds")})
    write_audit_log(user, "admin.teaching-knowledge.ocr.start", "document_library", "启动批量 OCR")
    return {"status": "started", "pid": process.pid}


@app.get("/api/admin/teaching-knowledge/process")
def document_processing_status(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    require_role(authorization, {"admin", "super_admin"})
    library = ROOT_DIR / "data" / "document_library.json"
    documents = json.loads(library.read_text(encoding="utf-8")).get("documents", []) if library.exists() else []
    counts: dict[str, int] = {}
    for item in documents:
        key = item.get("processing_status", "未知")
        counts[key] = counts.get(key, 0) + 1
    pid = document_processing.get("pid")
    running = bool(document_processing.get("running") and pid and subprocess.run(["powershell", "-NoProfile", "-Command", f"Get-Process -Id {pid} -ErrorAction SilentlyContinue"], capture_output=True).returncode == 0)
    document_processing["running"] = running
    return {"running": running, "pid": pid, "counts": counts, "total": len(documents)}


@app.post("/api/admin/teaching-knowledge/embeddings/process")
def start_embedding_processing(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    user = require_role(authorization, {"admin", "super_admin"})
    pid = embedding_processing.get("pid")
    if embedding_processing.get("running") and pid:
        return {"status": "running", "pid": pid}
    script = ROOT_DIR / "backend" / "scripts" / "build_document_embeddings.py"
    process = subprocess.Popen([sys.executable, str(script)], cwd=ROOT_DIR)
    embedding_processing.update({"running": True, "pid": process.pid, "started_at": datetime.now(timezone.utc).isoformat(timespec="seconds")})
    write_audit_log(user, "admin.teaching-knowledge.embedding.start", "document_library", "启动 Qwen 全量向量索引")
    return {"status": "started", "pid": process.pid}


@app.get("/api/admin/teaching-knowledge/embeddings/process")
def embedding_processing_status(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    require_role(authorization, {"admin", "super_admin"})
    pid = embedding_processing.get("pid")
    running = bool(embedding_processing.get("running") and pid and subprocess.run(["powershell", "-NoProfile", "-Command", f"Get-Process -Id {pid} -ErrorAction SilentlyContinue"], capture_output=True).returncode == 0)
    embedding_processing["running"] = running
    library = ROOT_DIR / "data" / "document_library.json"
    documents = json.loads(library.read_text(encoding="utf-8")).get("documents", []) if library.exists() else []
    counts: dict[str, int] = {}
    for item in documents:
        key = item.get("embedding_status", "待生成")
        counts[key] = counts.get(key, 0) + 1
    return {"running": running, "pid": pid, "counts": counts, "total": len(documents)}


@app.put("/api/teacher/teaching-knowledge/{entry_id}")
@app.put("/api/admin/teaching-knowledge/{entry_id}")
def teaching_knowledge_update(entry_id: str, payload: TeachingKnowledgeUpdateRequest, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    user = require_role(authorization, {"teacher", "admin", "super_admin"})
    try:
        entry = case_knowledge_service.teaching_update(entry_id, payload.model_dump(exclude_none=True))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="教学知识库条目不存在") from exc
    write_audit_log(user, "teacher.teaching-knowledge.update", entry_id, entry.get("title", ""))
    return entry


@app.delete("/api/teacher/teaching-knowledge/{entry_id}")
@app.delete("/api/admin/teaching-knowledge/{entry_id}")
def teaching_knowledge_delete(entry_id: str, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    user = require_role(authorization, {"teacher", "admin", "super_admin"})
    try:
        case_knowledge_service.teaching_delete(entry_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="教学知识库条目不存在") from exc
    write_audit_log(user, "teacher.teaching-knowledge.delete", entry_id, "")
    return {"status": "deleted", "id": entry_id}


@app.post("/api/teacher/case-library/deidentify")
def case_knowledge_deidentify(payload: CaseLibraryDeidentifyRequest, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    require_role(authorization, {"teacher", "admin", "super_admin"})
    return case_knowledge_service.deidentify_preview(payload.text)


@app.post("/api/teacher/case-library/import")
def case_knowledge_import(payload: CaseLibraryImportRequest, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    user = require_role(authorization, {"teacher", "admin", "super_admin"})
    source_dir = payload.source_dir or r"C:\Users\lenovo\Downloads\内科病例\内科病例"
    report = case_knowledge_service.import_from_dir(source_dir)
    write_audit_log(user, "teacher.case-library.import", source_dir, f"导入 {report['imported']} 条去标识化病例")
    return report


@app.post("/api/teacher/case-library/compile")
def case_knowledge_compile(payload: CaseLibraryCompileRequest, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    user = require_role(authorization, {"teacher", "admin", "super_admin"})
    entries: list[dict[str, Any]] = []
    for entry_id in payload.entry_ids:
        try:
            entries.append(case_knowledge_service.get(entry_id))
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=f"病例知识库条目不存在：{entry_id}") from exc

    chief_complaint = next((item.get("chief_complaint", "") for item in entries if item.get("chief_complaint")), "教师整合病例待补充主诉")
    present_illness = "；".join(item.get("present_illness", "") for item in entries if item.get("present_illness"))[:2400]
    diagnoses = [item.get("diagnosis", "") for item in entries if item.get("diagnosis")]
    categories = [item.get("category", "") for item in entries if item.get("category")]
    source_labels = [f"{item.get('title', '未命名')}（{item.get('source', '病例知识库')}）" for item in entries[:3]]
    title = payload.title or f"{categories[0] if categories else '内科'}病例整合训练"
    department = payload.department or (categories[0] if categories else "内科")
    learning_goal = payload.learning_goal or f"结合病例知识库素材，训练{categories[0] if categories else '内科'}问诊、鉴别与处置能力"
    suspected_diagnosis = payload.suspected_diagnosis or (diagnoses[0] if diagnoses else "待教师确认")
    source_summary = f"由 {len(entries)} 条脱敏病例整合：{'；'.join(source_labels)}。核心现病史线索：{present_illness[:500] or '待教师补充'}"

    analytics = _teacher_case_recommendations()["analysis"]
    analytics.update(read_json("teacher_dashboard.json"))
    draft = case_generator.generate_teacher_draft(
        {
            "title": title,
            "department": department,
            "chief_complaint": chief_complaint,
            "learning_goal": learning_goal,
            "difficulty": payload.difficulty,
            "suspected_diagnosis": suspected_diagnosis,
            "source_summary": source_summary,
        },
        analytics,
    )
    draft["workflow"].insert(
        0,
        {
            "id": "knowledge_base",
            "name": "病例知识库整合",
            "agent": "CaseKnowledgeAgent",
            "status": "done",
            "detail": f"合并 {len(entries)} 条脱敏病例，提取主诉、现病史与诊断线索。",
        },
    )
    draft["case"]["source"] = {"type": "synthetic", "name": "病例知识库整合", "contains_real_patient_data": False}
    draft["case"]["knowledge_entry_ids"] = payload.entry_ids
    draft["case"]["source_summary"] = source_summary
    draft["case"]["present_illness"] = present_illness or source_summary
    draft["case"]["history"]["present_illness"] = [present_illness or source_summary]
    matched_template = history_taking_service.search(suspected_diagnosis) or (history_taking_service.search(diagnoses[0]) if diagnoses else None)
    if matched_template:
        draft["workflow"].insert(
            1,
            {
                "id": "history_standard",
                "name": "问诊标准匹配",
                "agent": "HistoryTakingAgent",
                "status": "done",
                "detail": f"匹配问诊模板「{matched_template.get('title', '未命名')}」，用于生成问诊要点与评分依据。",
            },
        )
        draft["case"]["history_taking_reference"] = matched_template
        raw_points = matched_template.get("sections", {}).get("问诊要点", "")
        interview_points = [point.strip("；;。，, ") for point in re.split(r"[；;。]", raw_points) if len(point.strip("；;。，, ")) > 4][:5]
        if interview_points:
            draft["case"]["key_scoring_points"] = list(dict.fromkeys([*interview_points, *draft["case"]["key_scoring_points"]]))[:8]
        draft["validation"] = case_validator.validate(draft["case"])

    if payload.publish_immediately:
        if not draft["validation"]["valid"]:
            raise HTTPException(status_code=400, detail="整合病例校验未通过，请先编辑补充后再发布")
        draft["case"]["review_status"] = "已批准"
        draft["decision"] = {"action": "approve", "note": "教师选择直接发布", "decided_by": user.name}
        draft["workflow"][-1].update({"status": "done", "detail": "教师决策：已批准并直接发布。"})

    teacher_case_drafts[draft["draft_id"]] = draft
    persist_teacher_case_state()
    write_audit_log(user, "teacher.case-library.compile", draft["draft_id"], f"整合 {len(entries)} 条病例，直接发布={payload.publish_immediately}")
    return draft


@app.post("/api/teacher/case-library")
def case_knowledge_create(payload: CaseLibraryEntryCreateRequest, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    user = require_role(authorization, {"teacher", "admin", "super_admin"})
    entry = case_knowledge_service.create(payload.model_dump())
    write_audit_log(user, "teacher.case-library.create", entry["id"], entry["title"])
    return entry


@app.get("/api/teacher/case-library/{entry_id}")
def case_knowledge_get(entry_id: str, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    require_role(authorization, {"teacher", "admin", "super_admin"})
    try:
        return case_knowledge_service.get(entry_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="病例知识库条目不存在") from exc


@app.put("/api/teacher/case-library/{entry_id}")
def case_knowledge_update(entry_id: str, payload: CaseLibraryEntryUpdateRequest, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    user = require_role(authorization, {"teacher", "admin", "super_admin"})
    try:
        entry = case_knowledge_service.update(entry_id, payload.model_dump(exclude_none=True))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="病例知识库条目不存在") from exc
    write_audit_log(user, "teacher.case-library.update", entry_id, entry.get("title", ""))
    return entry


@app.delete("/api/teacher/case-library/{entry_id}")
def case_knowledge_delete(entry_id: str, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    user = require_role(authorization, {"teacher", "admin", "super_admin"})
    try:
        case_knowledge_service.delete(entry_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="病例知识库条目不存在") from exc
    write_audit_log(user, "teacher.case-library.delete", entry_id, "")
    return {"status": "deleted", "id": entry_id}


@app.get("/api/teacher/history-taking")
def history_taking_template(q: str = "", authorization: str | None = Header(default=None)) -> dict[str, Any]:
    require_role(authorization, {"teacher", "admin", "super_admin"})
    matched = history_taking_service.search(q)
    if matched is None:
        return {"found": False, "query": q, "hint": "问诊模板库中暂未匹配到该诊断"}
    return {"found": True, "query": q, **matched}


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
def rag_index(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    user = require_role(authorization, {"admin", "super_admin"})
    result = rag_pipeline.write_vector_store()
    write_audit_log(user, "admin.rag.reindex", "vector_store")
    return result


@app.get("/api/textbook-pathways")
def textbook_pathways() -> list[dict[str, Any]]:
    return load_textbook_pathways()


@app.get("/api/data-sources")
def public_data_sources() -> list[dict[str, Any]]:
    return load_data_sources()


@app.get("/api/admin/users")
def admin_users(authorization: str | None = Header(default=None)) -> list[dict[str, Any]]:
    require_role(authorization, {"admin", "super_admin"})
    return load_admin_users()


@app.get("/api/admin/data-sources")
def admin_data_sources(authorization: str | None = Header(default=None)) -> list[dict[str, Any]]:
    require_role(authorization, {"admin", "super_admin"})
    return load_data_sources()


@app.post("/api/admin/data-sources/sync")
def admin_data_sources_sync(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    user = require_role(authorization, {"admin", "super_admin"})
    write_audit_log(user, "admin.data_sources.sync", "all", "提交演示同步任务")
    return {"status": "mock_queued", "message": "已模拟提交数据源同步任务，真实环境需先完成授权、许可和脱敏审查。", "sources": load_data_sources()}


@app.get("/api/admin/knowledge-status")
def admin_knowledge_status(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    require_role(authorization, {"admin", "super_admin"})
    knowledge_items = read_json("knowledge.json")
    return {"items": len(knowledge_items), "bilingual_items": sum(1 for item in knowledge_items if item.get("title_en")), "vector_ready": sum(1 for item in knowledge_items if item.get("vector_status") == "mock_ready"), "sources": sorted({item.get("data_source", "mock") for item in knowledge_items})}


@app.get("/api/admin/graph-status")
def admin_graph_status(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    require_role(authorization, {"admin", "super_admin"})
    graph = read_json("medical_kg_bilingual.json")
    node_types: dict[str, int] = {}
    for node in graph["nodes"]:
        node_types[node.get("type", node.get("group", "Unknown"))] = node_types.get(node.get("type", node.get("group", "Unknown")), 0) + 1
    return {"nodes": len(graph["nodes"]), "edges": len(graph["edges"]), "node_types": node_types, "obsidian_ready": True, "neo4j_status": "env_placeholder"}


@app.post("/api/admin/obsidian/export")
def admin_obsidian_export(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    user = require_role(authorization, {"admin", "super_admin"})
    result = obsidian_service.export_preview()
    write_audit_log(user, "admin.obsidian.export", "knowledge_graph", "生成导出预览")
    return result


@app.post("/api/admin/cases/generate-mock")
def admin_cases_generate_mock(source: dict[str, Any] | None = None, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    user = require_role(authorization, {"admin", "super_admin"})
    result = case_generator.generate_mock(source)
    write_audit_log(user, "admin.case.generate_mock", str(result.get("case_id", "generated")))
    return result


@app.post("/api/admin/cases/validate")
def admin_cases_validate(payload: CaseValidateRequest, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    user = require_role(authorization, {"admin", "super_admin"})
    if payload.case_data is not None:
        result = case_validator.validate(payload.case_data)
        write_audit_log(user, "admin.case.validate", "payload", f"valid={result.get('valid')}")
        return result
    if payload.case_id:
        result = case_validator.validate(get_case_data(payload.case_id))
        write_audit_log(user, "admin.case.validate", payload.case_id, f"valid={result.get('valid')}")
        return result
    results = [case_validator.validate(case) for case in case_repository.all()]
    write_audit_log(user, "admin.case.validate_all", "case_library", f"count={len(results)}")
    return {"valid": all(item["valid"] for item in results), "count": len(results), "results": results}


@app.get("/api/admin/cases/source-plan")
def admin_cases_source_plan(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    require_role(authorization, {"admin", "super_admin"})
    return {
        "sources": case_source_adapter.plan(),
        "policy": "仅将公开来源用于字段设计和自行摘要；接入前必须完成许可、伦理、隐私与脱敏审查。",
    }


@app.get("/api/admin/audit-logs")
def admin_audit_logs(limit: int = 100, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    require_role(authorization, {"admin", "super_admin"})
    safe_limit = max(1, min(limit, 500))
    items = read_audit_logs(safe_limit)
    return {"count": len(items), "items": items}

@app.post("/api/agent/chat", response_model=AgentChatResponse)
def agent_chat(payload: AgentChatRequest) -> AgentChatResponse:
    return resolve_agent(payload.message, payload.role, payload.active_module)


@app.get("/api/anatomy")
def anatomy() -> list[dict[str, Any]]:
    return read_json("anatomy.json")


@app.get("/api/anatomy/textbook")
def anatomy_textbook(q: str = "") -> dict[str, Any]:
    result = anatomy_textbook_service.search(q)
    if result is None:
        return {"found": False, "query": q, "hint": "教材索引中暂未找到该结构的详细讲解"}
    return {"found": True, "query": q, **result}


@app.get("/api/anatomy/glossary")
def anatomy_glossary() -> dict[str, Any]:
    """Chinese names for the English structure names in the 3D atlas."""
    terms = anatomy_term_service.all()
    return {"count": len(terms), "source": "BodyParts3D 4.0", "terms": terms}


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
    return TTSResponse(status="mock_ready", voice=payload.voice, duration_seconds=max(2, min(18, len(payload.text) // 18)), audio_url=None, message="已模拟生成数字人语音，真实TTS可通过.env配置接入。")


if __name__ == "__main__":
    uvicorn.run("backend.app.main:app", host=settings.backend_host, port=settings.backend_port, reload=True)








