from __future__ import annotations

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
    learning_goals: list[str]


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
