from __future__ import annotations

from typing import Any

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
    patient_profile: str = ''
    speaking_style: str = ''
    opening: str = ''
    available_exams: list[str] = Field(default_factory=list)
    hidden_final_diagnosis: str = ''
    differential_diagnoses: list[str] = Field(default_factory=list)
    key_scoring_points: list[str] = Field(default_factory=list)
    high_risk_omissions: list[dict[str, Any]] = Field(default_factory=list)
    recommended_guidelines: list[str] = Field(default_factory=list)
    graph_node_ids: list[str] = Field(default_factory=list)
    recommended_retraining: list[str] = Field(default_factory=list)
    script: dict[str, Any] = Field(default_factory=dict)


class ChatMessage(BaseModel):
    role: str
    content: str
    citations: list[Citation] = Field(default_factory=list)


class PatientChatRequest(BaseModel):
    case_id: str = Field(default="emergency_chest_pain")
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


class AuthLoginResponse(BaseModel):
    token: str
    user: AuthUser


class TrainingScoreRequest(BaseModel):
    case_id: str = "emergency_chest_pain"
    history: list[ChatMessage] = Field(default_factory=list)
    exams: list[str] = Field(default_factory=list)
    preliminary_diagnosis: str = ""
    differentials: list[str] = Field(default_factory=list)
    treatment_principles: str = ""
    citations: list[str] = Field(default_factory=list)


class AgentChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1200)
    role: str = "student"
    active_module: str = "training"


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


class AnatomySubmitRequest(BaseModel):
    exercise_id: str
    selected_zone: str


class AnatomySubmitResponse(BaseModel):
    correct: bool
    score_items: list[ScoreItem]
    feedback: str
    explanation: str
    clinical_link: str


class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=800)
    voice: str = "clinical_tutor"


class TTSResponse(BaseModel):
    status: str
    voice: str
    duration_seconds: int
    audio_url: str | None = None
    message: str

