from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class Citation(BaseModel):
    id: str
    title: str
    source: str
    snippet: str


class WorkflowStep(BaseModel):
    id: str
    name: str
    agent: str
    status: str
    detail: str


class CaseSummary(BaseModel):
    id: str
    title: str
    department: str
    chief_complaint: str
    difficulty: str
    learning_goals: list[str] = Field(default_factory=list)
    patient_profile: dict[str, Any] = Field(default_factory=dict)
    patient_profile_text: str = ''
    speaking_style: str = ''
    opening: str = ''
    opening_statement: str = ''
    specialty: str = ''
    scenario: str = ''
    symptom_tags: list[str] = Field(default_factory=list)
    training_goals: list[str] = Field(default_factory=list)
    recommended_minutes: int = 20
    history: dict[str, list[str]] = Field(default_factory=dict)
    physical_exam: list[str] = Field(default_factory=list)
    available_tests: list[dict[str, Any]] = Field(default_factory=list)
    available_exams: list[str] = Field(default_factory=list)
    hidden_final_diagnosis: str = ''
    differential_diagnoses: list[str] = Field(default_factory=list)
    key_scoring_points: list[str] = Field(default_factory=list)
    high_risk_omissions: list[dict[str, Any]] = Field(default_factory=list)
    recommended_guidelines: list[str] = Field(default_factory=list)
    graph_node_ids: list[str] = Field(default_factory=list)
    recommended_retraining: list[str] = Field(default_factory=list)
    case_variants: list[dict[str, Any]] = Field(default_factory=list)
    script: dict[str, Any] = Field(default_factory=dict)


class ChatMessage(BaseModel):
    role: str
    content: str
    citations: list[Citation] = Field(default_factory=list)


class PatientChatRequest(BaseModel):
    case_id: str = Field(default="emergency_chest_pain")
    session_id: str | None = None
    variant_id: str = "A"
    message: str = Field(..., min_length=1, max_length=1200)
    history: list[ChatMessage] = Field(default_factory=list)


class ScoreItem(BaseModel):
    name: str
    score: int
    max_score: int = 100
    feedback: str


class MissingPoint(BaseModel):
    id: str
    level: str
    text: str
    suggestion: str
    citation: Citation | None = None


class PatientChatResponse(BaseModel):
    patient_reply: ChatMessage
    tutor_hint: str
    scores: list[ScoreItem]
    missing_points: list[MissingPoint]
    workflow_trace: list[WorkflowStep]
    citations: list[Citation]
    safety_notes: list[str]


class TrainingReport(BaseModel):
    case_id: str
    diagnosis_path: list[str]
    strengths: list[str]
    improvements: list[str]
    recommended_cases: list[str]
    citations: list[Citation]


class RagQuery(BaseModel):
    question: str = Field(..., min_length=2, max_length=1000)
    scenario: str = Field(default="AI标准化病人训练", max_length=80)


class RagAnswer(BaseModel):
    answer: str
    citations: list[Citation]
    workflow_trace: list[WorkflowStep]
    safety_notes: list[str]
    matched_knowledge: list[dict[str, Any]] = Field(default_factory=list)
    graph_nodes: list[dict[str, Any]] = Field(default_factory=list)
    graph_edges: list[dict[str, Any]] = Field(default_factory=list)
    bilingual_terms: list[dict[str, Any]] = Field(default_factory=list)
    related_cases: list[dict[str, Any]] = Field(default_factory=list)
    related_anatomy_exercises: list[dict[str, Any]] = Field(default_factory=list)
    recommended_learning_path: list[str] = Field(default_factory=list)


class AuthLoginRequest(BaseModel):
    account: str = Field(..., min_length=1, max_length=80)
    password: str = Field(..., min_length=1, max_length=120)
    role: str = Field(default="student", max_length=30)


class AuthUser(BaseModel):
    id: str
    name: str
    account: str
    role: str
    status: str
    department: str = ""
    permissions: list[str] = Field(default_factory=list)
    email: str = ""


class AuthLoginResponse(BaseModel):
    token: str
    user: AuthUser


class AuthRegisterRequest(BaseModel):
    account: str = Field(..., min_length=3, max_length=40, pattern=r"^[A-Za-z0-9_]+$")
    name: str = Field(..., min_length=2, max_length=40)
    email: str = Field(..., min_length=5, max_length=120)
    password: str = Field(..., min_length=8, max_length=120)
    role: str = Field(default="student", max_length=20)


class AuthEmailTokenRequest(BaseModel):
    token: str = Field(..., min_length=20, max_length=200)


class AuthForgotPasswordRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=120)


class AuthResetPasswordRequest(BaseModel):
    token: str = Field(..., min_length=20, max_length=200)
    password: str = Field(..., min_length=8, max_length=120)


class AuthTeacherReviewRequest(BaseModel):
    approved: bool


class TrainingScoreRequest(BaseModel):
    case_id: str = "emergency_chest_pain"
    session_id: str | None = None
    variant_id: str = "A"
    history: list[ChatMessage] = Field(default_factory=list)
    exams: list[str] = Field(default_factory=list)
    preliminary_diagnosis: str = ""
    differentials: list[str] = Field(default_factory=list)
    treatment_principles: str = ""
    medication_plan: str = ""
    citations: list[str] = Field(default_factory=list)

class CaseRandomRequest(BaseModel):
    department: str = ""
    symptom: str = ""
    difficulty: str = ""
    training_goal: str = ""


class TrainingStartRequest(BaseModel):
    case_id: str
    variant_id: str = "A"
    difficulty: str = ""
    mode: str = "完整训练"


class TrainingOrderTestRequest(BaseModel):
    session_id: str
    test_name: str


class TrainingDiagnosisRequest(BaseModel):
    session_id: str
    preliminary_diagnosis: str
    differentials: list[str] = Field(default_factory=list)
    treatment_principles: str = ""
    medication_plan: str = ""
    citations: list[str] = Field(default_factory=list)


class TeacherCaseDraftRequest(BaseModel):
    title: str = Field(..., min_length=2, max_length=100)
    department: str = Field(..., min_length=2, max_length=50)
    chief_complaint: str = Field(..., min_length=2, max_length=200)
    learning_goal: str = Field(..., min_length=2, max_length=300)
    difficulty: str = "进阶"
    suspected_diagnosis: str = "待教师确认"
    source_summary: str = Field(default="", max_length=1500)
    recommendation_id: str | None = None


class TeacherCaseEditRequest(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=100)
    department: str | None = Field(default=None, min_length=2, max_length=50)
    chief_complaint: str | None = Field(default=None, min_length=2, max_length=200)
    difficulty: str | None = None
    suspected_diagnosis: str | None = None
    present_illness: str | None = None
    learning_goal: str | None = None
    teacher_note: str | None = None


class TeacherCaseDecisionRequest(BaseModel):
    action: str
    note: str = Field(default="", max_length=500)


class TeacherRecommendationDecisionRequest(BaseModel):
    action: str
    note: str = Field(default="", max_length=500)


class CaseLibraryEntryCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=120)
    category: str = Field(default="未分类", max_length=80)
    diagnosis: str = Field(default="", max_length=160)
    chief_complaint: str = Field(default="", max_length=300)
    present_illness: str = Field(default="", max_length=2400)
    content: str = Field(default="", max_length=30000)
    source: str = Field(default="教师手工录入", max_length=300)
    status: str = Field(default="已脱敏入库", max_length=40)


class CaseLibraryEntryUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=120)
    category: str | None = Field(default=None, max_length=80)
    diagnosis: str | None = Field(default=None, max_length=160)
    chief_complaint: str | None = Field(default=None, max_length=300)
    present_illness: str | None = Field(default=None, max_length=2400)
    content: str | None = Field(default=None, max_length=30000)
    source: str | None = Field(default=None, max_length=300)
    status: str | None = Field(default=None, max_length=40)


class CaseLibraryDeidentifyRequest(BaseModel):
    text: str = Field(..., max_length=30000)


class CaseLibraryImportRequest(BaseModel):
    source_dir: str | None = None


class CaseLibraryCompileRequest(BaseModel):
    entry_ids: list[str] = Field(..., min_length=1, max_length=8)
    title: str | None = Field(default=None, min_length=2, max_length=100)
    department: str | None = Field(default=None, min_length=2, max_length=50)
    learning_goal: str | None = Field(default=None, min_length=2, max_length=300)
    suspected_diagnosis: str | None = Field(default=None, max_length=200)
    difficulty: str = Field(default="进阶", max_length=20)
    publish_immediately: bool = False


class TeachingKnowledgeCreateRequest(BaseModel):
    knowledge_type: str = Field(default="case", max_length=30)
    title: str = Field(..., min_length=1, max_length=160)
    category: str = Field(default="未分类", max_length=100)
    content: str = Field(default="", max_length=30000)
    source: str = Field(default="教师手工录入", max_length=300)
    diagnosis: str = Field(default="", max_length=160)
    chief_complaint: str = Field(default="", max_length=300)
    present_illness: str = Field(default="", max_length=2400)
    status: str = Field(default="待审核", max_length=40)
    processing_status: str = Field(default="待审核", max_length=40)


class TeachingKnowledgeUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=160)
    category: str | None = Field(default=None, max_length=100)
    content: str | None = Field(default=None, max_length=30000)
    source: str | None = Field(default=None, max_length=300)
    diagnosis: str | None = Field(default=None, max_length=160)
    chief_complaint: str | None = Field(default=None, max_length=300)
    present_illness: str | None = Field(default=None, max_length=2400)
    status: str | None = Field(default=None, max_length=40)
    processing_status: str | None = Field(default=None, max_length=40)


class CaseValidateRequest(BaseModel):
    case_data: dict[str, Any] | None = None
    case_id: str | None = None


class SkillQuery(BaseModel):
    query: str = Field(..., min_length=1, max_length=200, pattern=r'\S')
    part_id: str | None = Field(default=None, max_length=80)


class SkillPolicyUpdate(BaseModel):
    enabled: bool
    allowed_roles: list[Literal['student', 'teacher', 'admin']] = Field(..., max_length=3)
    hourly_limit: int = Field(default=120, ge=1, le=1000)


class SkillCitation(BaseModel):
    source: str
    reference: str
    page: int | None = None


class SkillResult(BaseModel):
    skill_id: str
    status: Literal['success', 'empty', 'disabled', 'forbidden', 'rate_limited', 'error']
    message: str
    data: dict[str, Any] = Field(default_factory=dict)
    citations: list[SkillCitation] = Field(default_factory=list)
    duration_ms: int = 0
    call_id: str = ''


class AgentAction(BaseModel):
    type: Literal['highlight_structure', 'open_graph', 'open_textbook']
    target: str
    label: str


class AgentChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1200)
    role: str = "student"
    active_module: str = "training"
    context: SkillQuery | None = None


class AgentChatResponse(BaseModel):
    intent: str
    action: str
    target_module: str | None = None
    target_case_id: str | None = None
    target_exercise_id: str | None = None
    reply: str
    result_cards: list[dict[str, Any]] = Field(default_factory=list)
    learning_path: list[str] = Field(default_factory=list)
    workflow_trace: list[WorkflowStep] = Field(default_factory=list)
    safety_notes: list[str] = Field(default_factory=list)
    execution_mode: str = 'legacy_rules'
    skill_results: list[SkillResult] = Field(default_factory=list)
    citations: list[SkillCitation] = Field(default_factory=list)
    actions: list[AgentAction] = Field(default_factory=list)


class AnatomySubmitRequest(BaseModel):
    exercise_id: str
    selected_zone: str
    node_id: str = ""
    structure_id: str = ""
    click_x: float | None = Field(default=None, ge=0, le=100)
    click_y: float | None = Field(default=None, ge=0, le=100)


class AnatomySubmitResponse(BaseModel):
    correct: bool
    score_items: list[ScoreItem]
    feedback: str
    explanation: str
    clinical_link: str
    record_id: str | None = None
    score: int = 0


class AnatomyNoteRequest(BaseModel):
    note_id: str | None = None
    document_id: str
    page: int = Field(..., ge=1)
    line_start: int | None = Field(default=None, ge=1)
    line_end: int | None = Field(default=None, ge=1)
    content: str = Field(default="", max_length=5000)


class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=800)
    voice: str = "clinical_tutor"


class TTSResponse(BaseModel):
    status: str
    voice: str
    duration_seconds: int
    audio_url: str | None = None
    message: str


