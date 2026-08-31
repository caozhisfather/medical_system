from __future__ import annotations

import base64
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..services.sparkos_service import SparkOsError, sparkos_service

router = APIRouter(prefix="/api/sparkos", tags=["sparkos"])


class SparkOsAudioRequest(BaseModel):
    audio_base64: str = Field(..., min_length=1, max_length=15_000_000)
    uid: str = Field(default="medical-student", max_length=120)
    voice: str = Field(default="x5_lingxiaoyue_flow", max_length=120)


@router.get("/status")
def status() -> dict[str, Any]:
    return sparkos_service.status()


@router.post("/audio-chat")
def audio_chat(payload: SparkOsAudioRequest) -> dict[str, Any]:
    try:
        return sparkos_service.audio_chat(base64.b64decode(payload.audio_base64), payload.uid, payload.voice)
    except (ValueError, SparkOsError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        message = str(exc).splitlines()[0][:240]
        raise HTTPException(status_code=502, detail=f"讯飞 SparkOS 调用失败：{message}") from exc
