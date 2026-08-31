from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from datetime import datetime
from time import mktime
from typing import Any
from urllib.parse import urlencode, urlparse
from wsgiref.handlers import format_date_time

from ..config import settings


class SparkOsError(RuntimeError):
    """Raised when the SparkOS adapter cannot complete an audio session."""


class SparkOsService:
    def configured(self) -> bool:
        return all((settings.sparkos_app_id, settings.sparkos_api_key, settings.sparkos_api_secret, settings.sparkos_ws_url))

    def status(self) -> dict[str, Any]:
        return {
            "configured": self.configured(),
            "ws_url": settings.sparkos_ws_url,
            "scene": settings.sparkos_scene,
            "rag_configured": bool(settings.rag_url and settings.rag_api_password),
            "provider": "讯飞 SparkOS 超拟人对话",
        }

    def audio_chat(self, audio: bytes, uid: str = "medical-student", voice: str = "x5_lingxiaoyue_flow") -> dict[str, Any]:
        if not self.configured():
            raise SparkOsError("SparkOS 配置不完整，请检查 LLM_APPID、LLM_APIKEY、LLM_APISECRET 和 LLM_WS_URL。")
        if not audio:
            raise SparkOsError("音频内容不能为空。")
        try:
            from websocket import create_connection
        except ImportError as exc:
            raise SparkOsError("缺少 websocket-client，请先安装后端依赖。") from exc

        ws = create_connection(self._auth_url(), timeout=30)
        tts_audio: list[bytes] = []
        text_parts: list[str] = []
        try:
            chunks = [audio[index:index + 1280] for index in range(0, len(audio), 1280)]
            for index, chunk in enumerate(chunks):
                status = 0 if index == 0 else 2 if index == len(chunks) - 1 else 1
                if len(chunks) == 1:
                    status = 2
                ws.send(json.dumps(self._frame(chunk, status, uid, voice), ensure_ascii=False))
                time.sleep(0.04)

            deadline = time.time() + 30
            while time.time() < deadline:
                result = json.loads(ws.recv())
                header = result.get("header") or {}
                if int(header.get("code", 0)) != 0:
                    raise SparkOsError(str(header.get("message") or f"SparkOS 返回错误码 {header.get('code')}"))
                payload = result.get("payload") or {}
                for key in ("event", "iat", "nlp"):
                    item = payload.get(key)
                    if item and item.get("text"):
                        text_parts.append(self._decode_text(item["text"]))
                tts = payload.get("tts") or {}
                if tts.get("audio"):
                    tts_audio.append(base64.b64decode(tts["audio"]))
                if int(tts.get("status", -1)) == 2:
                    break
            return {"status": "ok", "text": "".join(text_parts), "audio_base64": base64.b64encode(b"".join(tts_audio)).decode(), "audio_format": "mp3"}
        finally:
            ws.close()

    def _auth_url(self) -> str:
        parsed = urlparse(settings.sparkos_ws_url)
        host = parsed.netloc
        path = parsed.path or "/"
        date = format_date_time(mktime(datetime.now().timetuple()))
        origin = f"host: {host}\ndate: {date}\nGET {path} HTTP/1.1"
        signature = base64.b64encode(hmac.new(settings.sparkos_api_secret.encode(), origin.encode(), hashlib.sha256).digest()).decode()
        authorization_origin = (
            f'api_key="{settings.sparkos_api_key}", algorithm="hmac-sha256", '
            f'headers="host date request-line", signature="{signature}"'
        )
        query = {"host": host, "date": date, "authorization": base64.b64encode(authorization_origin.encode()).decode()}
        return f"{settings.sparkos_ws_url}?{urlencode(query)}"

    def _frame(self, chunk: bytes, status: int, uid: str, voice: str) -> dict[str, Any]:
        return {
            "header": {"app_id": settings.sparkos_app_id, "uid": uid, "status": 1 if status else 0, "stmid": "1", "scene": settings.sparkos_scene, "interact_mode": "continuous_vad"},
            "parameter": {
                "iat": {"iat": {"encoding": "utf8", "compress": "raw", "format": "json"}},
                "nlp": {"nlp": {"encoding": "utf8", "compress": "raw", "format": "json"}, "new_session": "global"},
                "tts": {"vcn": voice, "speed": 50, "volume": 50, "pitch": 50, "tts": {"encoding": "lame", "sample_rate": 16000, "channels": 1, "bit_depth": 16, "frame_size": 0}},
            },
            "payload": {"audio": {"status": status, "audio": base64.b64encode(chunk).decode(), "encoding": "raw", "sample_rate": 16000, "channels": 1, "bit_depth": 16, "frame_size": 0}},
        }

    @staticmethod
    def _decode_text(value: str) -> str:
        try:
            return base64.b64decode(value).decode("utf-8")
        except (ValueError, UnicodeDecodeError):
            return value


sparkos_service = SparkOsService()
