from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class LiveActSpeakRequest(BaseModel):
    session_id: str = Field(default="demo-session-001", max_length=120)
    text: str = Field(..., min_length=1, max_length=1200)
    audio_url: str | None = Field(default=None, max_length=1000)
    emotion: str = Field(default="teaching", max_length=60)
    action: str = Field(default="explain", max_length=60)
    avatar_id: str = Field(default="medical_tutor_001", max_length=120)
    voice: str = Field(default="zh_female_warm", max_length=120)
    mode: Literal["mock", "liveact"] = "mock"


class LiveActStatusRequest(BaseModel):
    session_id: str = Field(..., min_length=1, max_length=120)
    state: Literal["idle", "listening", "speaking", "warning", "scoring"]
    detail: str = Field(default="", max_length=600)


class LiveActResponse(BaseModel):
    status: str
    session_id: str
    request_id: str
    mode: Literal["mock", "liveact"]
    state: str
    video_url: str | None = None
    stream_url: str | None = None
    poster_url: str = "/assets/digital-human/medical-tutor.png"
    subtitle: str
    emotion: str
    action: str
    duration: float
    provider: str
    fallback_reason: str | None = None
