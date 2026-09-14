"""Qwen vision client used for document/image OCR and anatomy image explanation."""
from __future__ import annotations

import base64
import json
import mimetypes
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from ..config import settings


class QwenVisionService:
    def configured(self) -> bool:
        return bool(settings.vision_api_key and settings.vision_base_url and settings.vision_model)

    def recognize_image(self, image_path: str | Path, prompt: str = "请准确识别图片中的全部文字，保留标题、段落和表格结构。") -> str:
        if not self.configured():
            raise RuntimeError("Qwen 视觉模型未配置，请设置 QWEN_VISION_API_KEY")
        path = Path(image_path)
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        mime = mimetypes.guess_type(path.name)[0] or "image/png"
        payload = {
            "model": settings.vision_model,
            "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}, {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{encoded}"}}]}],
            "temperature": 0,
        }
        request = Request(f"{settings.vision_base_url.rstrip('/')}/chat/completions", data=json.dumps(payload, ensure_ascii=False).encode("utf-8"), headers={"Authorization": f"Bearer {settings.vision_api_key}", "Content-Type": "application/json"}, method="POST")
        try:
            with urlopen(request, timeout=settings.vision_timeout) as response:
                result = json.loads(response.read().decode("utf-8"))
            content = result["choices"][0]["message"]["content"]
            if isinstance(content, list):
                return "\n".join(str(part.get("text", "")) for part in content if isinstance(part, dict))
            return str(content)
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:300]
            raise RuntimeError(f"Qwen 视觉模型 HTTP {exc.code}: {detail}") from exc
        except (URLError, OSError, KeyError, IndexError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"Qwen 视觉模型请求失败: {exc}") from exc


qwen_vision_service = QwenVisionService()
