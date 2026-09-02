from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ..config import settings
from ..services.digital_human_service import DigitalHumanService

router = APIRouter(prefix="/api/digital-human", tags=["digital-human"])
service = DigitalHumanService()


class DigitalHumanSpeakRequest(BaseModel):
    session_id: str = Field(default="demo-session-001", max_length=120)
    text: str = Field(..., min_length=1, max_length=1200)
    emotion: str = Field(default="teaching", max_length=60)
    action: str = Field(default="explain", max_length=60)
    avatar_id: str = Field(default="standardized_patient_001", max_length=120)
    voice: str = Field(default="zh_female_warm", max_length=120)
    mode: Literal["mock", "liveact"] = "mock"
    audio_url: str | None = Field(default=None, max_length=1000)
    context: dict[str, str] = Field(default_factory=dict)


class DigitalHumanStatusRequest(BaseModel):
    session_id: str = Field(..., min_length=1, max_length=120)
    state: Literal["idle", "listening", "speaking", "warning", "scoring"]
    detail: str = Field(default="", max_length=600)


class DigitalHumanSessionRequest(BaseModel):
    role: str = Field(default="student", max_length=40)
    avatar_id: str = Field(default="standardized_patient_001", max_length=120)


@router.post("/speak")
def speak(payload: DigitalHumanSpeakRequest) -> dict[str, Any]:
    try:
        return service.speak(payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/status")
def status(payload: DigitalHumanStatusRequest) -> dict[str, Any]:
    return {"status": "ok", **service.update_status(payload.session_id, payload.state, payload.detail)}


@router.post("/session")
def session(payload: DigitalHumanSessionRequest) -> dict[str, Any]:
    return {"status": "ok", **service.create_session(payload.role, payload.avatar_id)}


@router.get("/modes")
def modes() -> dict[str, Any]:
    return service.modes()


@router.get("/acceleration")
def acceleration() -> dict[str, Any]:
    return service.acceleration_status()


@router.get("/mock-video")
def mock_video(
    state: str = Query(default="idle"),
    avatar_id: str = Query(default=settings.liveact_avatar_id),
) -> dict[str, Any]:
    return service.mock_video(state, avatar_id)
