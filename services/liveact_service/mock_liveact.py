from __future__ import annotations

import uuid

from .schemas import LiveActResponse, LiveActSpeakRequest


def state_from_request(payload: LiveActSpeakRequest) -> str:
    combined = f"{payload.action} {payload.emotion}".lower()
    if any(token in combined for token in ("warning", "warn", "risk", "alert")):
        return "warning"
    if any(token in combined for token in ("score", "scoring", "evaluate")):
        return "scoring"
    if "listen" in combined:
        return "listening"
    return "speaking"


def mock_response(payload: LiveActSpeakRequest, reason: str | None = None) -> LiveActResponse:
    return LiveActResponse(
        status="fallback" if reason else "ok",
        session_id=payload.session_id,
        request_id=f"mock-{uuid.uuid4().hex[:10]}",
        mode="mock",
        state=state_from_request(payload),
        video_url=None,
        stream_url=None,
        subtitle=payload.text,
        emotion=payload.emotion,
        action=payload.action,
        duration=round(max(2.5, min(22.0, len(payload.text) / 5.2)), 1),
        provider="独立数字人本地演示服务",
        fallback_reason=reason,
    )
