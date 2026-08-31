from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from ..config import ROOT_DIR, settings

_history_taking_prompt_cache: str | None = None


def _load_history_taking_prompt() -> str:
    global _history_taking_prompt_cache
    if _history_taking_prompt_cache is None:
        prompt_path = ROOT_DIR / "data" / "history_taking_standard_prompt.txt"
        try:
            _history_taking_prompt_cache = prompt_path.read_text(encoding="utf-8").strip()
        except OSError:
            _history_taking_prompt_cache = ""
    return _history_taking_prompt_cache


class LlmPatientService:
    """OpenAI-compatible patient dialogue adapter with safe local fallback."""

    def configured(self) -> bool:
        return bool(settings.openai_api_key and settings.openai_base_url and settings.openai_model)

    def answer(self, case: dict[str, Any], message: str, history: list[dict[str, Any]]) -> dict[str, Any] | None:
        if not self.configured():
            return None
        system = self._system_prompt(case)
        messages = [{"role": "system", "content": system}]
        for item in history[-12:]:
            role = "assistant" if item.get("role") == "patient" else "user"
            content = str(item.get("content") or "").strip()
            if content:
                messages.append({"role": role, "content": content})
        messages.append({"role": "user", "content": message})
        body = json.dumps({"model": settings.openai_model, "messages": messages, "temperature": 0.35, "max_tokens": 220}, ensure_ascii=False).encode("utf-8")
        request = Request(
            f"{settings.openai_base_url.rstrip('/')}/v1/chat/completions",
            data=body,
            headers={"Authorization": f"Bearer {settings.openai_api_key}", "Content-Type": "application/json", "Accept": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=22) as response:
                payload = json.loads(response.read().decode("utf-8"))
            content = str(payload.get("choices", [{}])[0].get("message", {}).get("content", "")).strip()
            if not content or len(content) > 1200:
                return None
            return {"reply": content, "matched_field": "llm_patient", "revealed_diagnosis": False, "provider": settings.openai_model}
        except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError, IndexError, AttributeError):
            return None

    def _system_prompt(self, case: dict[str, Any]) -> str:
        profile = case.get("patient_profile", {})
        history = case.get("history", {})
        tests = [item.get("test_name") for item in case.get("available_tests", [])]
        standard = _load_history_taking_prompt()
        return f"""\u4f60\u662f\u533b\u5b66\u6559\u5b66\u5e73\u53f0\u4e2d\u7684AI\u6807\u51c6\u5316\u75c5\u4eba\uff0c\u53ea\u80fd\u626e\u6f14\u60a3\u8005\uff0c\u4e0d\u80fd\u626e\u6f14\u533b\u751f\u3002
\u75c5\u4f8b\uff1a{case.get('title_zh', '')}\uff1b\u4e3b\u8bc9\uff1a{case.get('chief_complaint', '')}
\u60a3\u8005\u7279\u5f81\uff1a{profile}
\u5df2\u77e5\u75c5\u53f2\uff08\u53ea\u6709\u88ab\u5b66\u751f\u95ee\u5230\u65f6\u624d\u9010\u6b65\u900f\u9732\uff09\uff1a{history}
\u53ef\u7533\u8bf7\u68c0\u67e5\uff1a{tests}
\u4e25\u683c\u89c4\u5219\uff1a
1. \u53ea\u6839\u636e\u4e0a\u8ff0\u75c5\u4f8b\u4e8b\u5b9e\u56de\u7b54\uff0c\u4e0d\u7f16\u9020\u65b0\u7684\u75c7\u72b6\u3001\u68c0\u67e5\u7ed3\u679c\u6216\u7528\u836f\u4fe1\u606f\u3002
2. \u4e0d\u4e3b\u52a8\u8bf4\u51fa\u6700\u7ec8\u8bca\u65ad\u3001\u9274\u522b\u8bca\u65ad\u3001\u75be\u75c5\u540d\u79f0\u6216\u6559\u5b66\u8bc4\u5206\uff1b\u88ab\u95ee\u8bca\u65ad\u65f6\u56de\u7b54\u201c\u6211\u4e0d\u6e05\u695a\u6700\u7ec8\u8bca\u65ad\uff0c\u8bf7\u7ee7\u7eed\u8be2\u95ee\u6211\u7684\u75c7\u72b6\u548c\u60c5\u51b5\u201d\u3002
3. \u6bcf\u6b21\u53ea\u56de\u7b54\u5f53\u524d\u95ee\u9898\uff0c\u4f7f\u7528\u81ea\u7136\u3001\u7b80\u77ed\u7684\u60a3\u8005\u53e3\u543b\uff0c\u4e2d\u6587\u4e0d\u8d85\u8fc7 120 \u5b57\u3002
4. \u672a\u88ab\u8be2\u95ee\u7684\u75c5\u53f2\u4e0d\u8981\u4e00\u6b21\u6027\u5168\u90e8\u900f\u9732\uff1b\u4e0d\u8981\u7ed9\u533b\u7597\u5efa\u8bae\u3002
---
{standard}
"""


llm_patient_service = LlmPatientService()
