from __future__ import annotations

import json
import time
import uuid
from dataclasses import asdict, dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from ..config import settings
from .sparkos_service import sparkos_service

VALID_STATES = {"idle", "listening", "speaking", "warning", "scoring"}
VALID_MODES = {"mock", "liveact"}


@dataclass
class DigitalHumanResult:
    status: str
    session_id: str
    request_id: str
    requested_mode: str
    mode: str
    state: str
    video_url: str | None
    stream_url: str | None
    poster_url: str
    subtitle: str
    emotion: str
    action: str
    duration: float
    provider: str
    fallback_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class DigitalHumanService:
    """Lightweight adapter between the teaching API and 真实数字人."""

    def __init__(self) -> None:
        self.sessions: dict[str, dict[str, Any]] = {}

    def create_session(self, role: str, avatar_id: str | None = None) -> dict[str, Any]:
        session_id = f"dh-{uuid.uuid4().hex[:12]}"
        session = {
            "session_id": session_id,
            "role": role,
            "avatar_id": avatar_id or settings.liveact_avatar_id,
            "state": "idle",
            "mode": settings.digital_human_mode if settings.digital_human_mode in VALID_MODES else "mock",
            "created_at": int(time.time()),
        }
        self.sessions[session_id] = session
        return session

    def update_status(self, session_id: str, state: str, detail: str = "") -> dict[str, Any]:
        normalized = state if state in VALID_STATES else "idle"
        session = self.sessions.setdefault(
            session_id,
            {
                "session_id": session_id,
                "role": "student",
                "avatar_id": settings.liveact_avatar_id,
                "mode": "mock",
                "created_at": int(time.time()),
            },
        )
        session.update({"state": normalized, "detail": detail, "updated_at": int(time.time())})
        return session

    def modes(self) -> dict[str, Any]:
        available = self.liveact_available()
        return {
            "active_mode": settings.digital_human_mode if settings.digital_human_mode in VALID_MODES else "mock",
            "modes": [
                {"id": "mock", "label": "本地演示", "available": True, "description": "本地动态占位，不需要 GPU 或模型权重。"},
                {
                    "id": "liveact",
                    "label": "真实数字人",
                    "available": available,
                    "description": "连接独立 GPU 数字人推理服务，生成语音同步视频；服务不可用时自动回退。",
                },
                {
                    "id": "sparkos",
                    "label": "讯飞语音",
                    "available": sparkos_service.configured(),
                    "description": "通过讯飞 SparkOS 进行语音问答并返回语音结果。",
                },
            ],
            "liveact_service_url": settings.liveact_service_url,
            "liveact_available": available,
            "sparkos_available": sparkos_service.configured(),
            "fallback_enabled": True,
        }

    def mock_video(self, state: str = "idle", avatar_id: str | None = None) -> dict[str, Any]:
        normalized = state if state in VALID_STATES else "idle"
        return {
            "status": "ok",
            "mode": "mock",
            "state": normalized,
            "avatar_id": avatar_id or settings.liveact_avatar_id,
            "video_url": None,
            "poster_url": "/assets/digital-human/medical-tutor.png",
            "animation": f"css-{normalized}",
            "provider": "数字人本地演示适配器",
        }

    def speak(self, payload: dict[str, Any]) -> dict[str, Any]:
        requested_mode = str(payload.get("mode") or settings.digital_human_mode).lower()
        requested_mode = requested_mode if requested_mode in VALID_MODES else "mock"
        session_id = str(payload.get("session_id") or self.create_session("student")["session_id"])
        text = str(payload.get("text") or "").strip()
        if not text:
            raise ValueError("Digital human subtitle text is required.")

        if requested_mode == "liveact":
            try:
                result = self._normalize_liveact_result(
                    self._call_liveact(payload | {"session_id": session_id}),
                    payload,
                    session_id,
                )
                self.update_status(session_id, result["state"], text)
                return result
            except (HTTPError, URLError, TimeoutError, ValueError, OSError, json.JSONDecodeError) as exc:
                result = self._mock_result(payload, session_id, requested_mode, f"{type(exc).__name__}: {exc}")
                self.update_status(session_id, result.state, text)
                return result.to_dict()

        result = self._mock_result(payload, session_id, requested_mode)
        self.update_status(session_id, result.state, text)
        return result.to_dict()

    def liveact_available(self) -> bool:
        try:
            request = Request(f"{settings.liveact_service_url.rstrip('/')}/health", headers={"Accept": "application/json"})
            with urlopen(request, timeout=min(settings.liveact_request_timeout, 1.5)) as response:
                health = json.loads(response.read().decode("utf-8"))
                return 200 <= response.status < 300 and bool(health.get("ready_for_liveact"))
        except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError):
            return False

    def acceleration_status(self) -> dict[str, Any]:
        try:
            request = Request(
                f"{settings.liveact_service_url.rstrip('/')}/kernel-health",
                headers={"Accept": "application/json"},
            )
            with urlopen(request, timeout=min(settings.liveact_request_timeout, 1.5)) as response:
                result = json.loads(response.read().decode("utf-8"))
                return {
                    "status": "ok" if 200 <= response.status < 300 else "unavailable",
                    "service_available": 200 <= response.status < 300,
                    **result,
                }
        except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
            return {
                "status": "unavailable",
                "service_available": False,
                "selected_backend": "torch",
                "notes": [f"独立数字人服务暂不可用：{type(exc).__name__}。"],
            }

    def _call_liveact(self, payload: dict[str, Any]) -> dict[str, Any]:
        request = Request(
            f"{settings.liveact_service_url.rstrip('/')}/speak",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=settings.liveact_request_timeout) as response:
            return json.loads(response.read().decode("utf-8"))

    def _normalize_liveact_result(
        self,
        result: dict[str, Any],
        payload: dict[str, Any],
        session_id: str,
    ) -> dict[str, Any]:
        text = str(payload.get("text") or "")
        action = str(payload.get("action") or "explain")
        emotion = str(payload.get("emotion") or "teaching")
        state = str(result.get("state") or self._state_for(action, emotion))
        reported_mode = str(result.get("mode") or "mock")
        actual_mode = reported_mode if reported_mode in VALID_MODES else "mock"
        fallback_reason = result.get("fallback_reason")
        status = str(result.get("status") or "ok")
        if actual_mode != "liveact":
            status = "fallback"
            fallback_reason = fallback_reason or "真实数字人 独立服务当前运行在 本地演示 模式。"
        return DigitalHumanResult(
            status=status,
            session_id=session_id,
            request_id=str(result.get("request_id") or f"liveact-{uuid.uuid4().hex[:10]}"),
            requested_mode="liveact",
            mode=actual_mode,
            state=state if state in VALID_STATES else "speaking",
            video_url=result.get("video_url"),
            stream_url=result.get("stream_url"),
            poster_url=str(result.get("poster_url") or "/assets/digital-human/medical-tutor.png"),
            subtitle=str(result.get("subtitle") or text),
            emotion=emotion,
            action=action,
            duration=float(result.get("duration") or self._duration(text)),
            provider=str(result.get("provider") or "真实数字人服务"),
            fallback_reason=str(fallback_reason) if fallback_reason else None,
        ).to_dict()

    def _mock_result(
        self,
        payload: dict[str, Any],
        session_id: str,
        requested_mode: str,
        fallback_reason: str | None = None,
    ) -> DigitalHumanResult:
        text = str(payload.get("text") or "")
        action = str(payload.get("action") or "explain")
        emotion = str(payload.get("emotion") or "teaching")
        return DigitalHumanResult(
            status="fallback" if fallback_reason else "ok",
            session_id=session_id,
            request_id=f"mock-{uuid.uuid4().hex[:10]}",
            requested_mode=requested_mode,
            mode="mock",
            state=self._state_for(action, emotion),
            video_url=None,
            stream_url=None,
            poster_url="/assets/digital-human/medical-tutor.png",
            subtitle=text,
            emotion=emotion,
            action=action,
            duration=self._duration(text),
            provider="数字人本地演示适配器",
            fallback_reason=fallback_reason,
        )

    @staticmethod
    def _state_for(action: str, emotion: str) -> str:
        combined = f"{action} {emotion}".lower()
        if any(token in combined for token in ("warning", "warn", "risk", "alert")):
            return "warning"
        if any(token in combined for token in ("score", "scoring", "evaluate")):
            return "scoring"
        if any(token in combined for token in ("listen", "listening")):
            return "listening"
        return "speaking"

    @staticmethod
    def _duration(text: str) -> float:
        return round(max(2.5, min(22.0, len(text) / 5.2)), 1)

