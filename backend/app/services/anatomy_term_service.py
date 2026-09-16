from __future__ import annotations

import json
import re
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from ..config import ROOT_DIR, settings

GLOSSARY_FILE = ROOT_DIR / "data" / "anatomy_term_glossary.json"

SYSTEM_PROMPT = (
    "你是医学解剖学术语专家。把给定的英文解剖学名词翻译成规范的中文解剖学名词，"
    "参照《系统解剖学》和《人体解剖学名词》的用词习惯，例如 Right femur 译为 右股骨，"
    "Left ventricle 译为 左心室。只输出一个 JSON 对象，键是英文原名，值是中文名，"
    "不要输出解释、Markdown 代码块或任何其他内容。"
)


def _extract_json(text: str) -> dict[str, Any] | None:
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
    cleaned = re.sub(r"```$", "", cleaned).strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        payload = json.loads(cleaned[start : end + 1])
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


class AnatomyTermService:
    """Maps BodyParts3D English structure names to Chinese anatomical terms.

    The atlas ships English names, while the indexed textbooks are Chinese, so a
    bilingual bridge is required before a structure can be traced back to a
    specific book, chapter, and page. Translations are produced once and cached
    on disk so repeated lookups stay offline and deterministic.
    """

    def __init__(self) -> None:
        self._map: dict[str, str] = {}
        self._lower: dict[str, str] = {}
        self._load()

    def _load(self) -> None:
        if not GLOSSARY_FILE.exists():
            return
        try:
            payload = json.loads(GLOSSARY_FILE.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        terms = payload.get("terms") if isinstance(payload, dict) else None
        if isinstance(terms, dict):
            self._map = {str(key): str(value) for key, value in terms.items() if value}
            for key, value in self._map.items():
                self._lower.setdefault(key.lower(), value)

    def save(self) -> None:
        GLOSSARY_FILE.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "source": "BodyParts3D 4.0 English names translated to Chinese anatomical terms",
            "model": settings.openai_model,
            "count": len(self._map),
            "terms": dict(sorted(self._map.items())),
        }
        GLOSSARY_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")

    def lookup(self, english_name: str) -> str | None:
        key = english_name.strip()
        # The model occasionally echoes a name back with different casing, so
        # lookups must not be case-sensitive.
        return self._map.get(key) or self._lower.get(key.lower())

    def all(self) -> dict[str, str]:
        return dict(self._map)

    def add(self, mapping: dict[str, str]) -> int:
        added = 0
        for english, chinese in mapping.items():
            key = english.strip()
            value = str(chinese).strip()
            if not key or not value or key in self._map or key.lower() in self._lower:
                continue
            self._map[key] = value
            self._lower[key.lower()] = value
            added += 1
        return added

    def missing(self, names: list[str]) -> list[str]:
        seen: list[str] = []
        seen_lower: set[str] = set()
        for name in names:
            key = name.strip()
            lower = key.lower()
            if key and key not in self._map and lower not in self._lower and lower not in seen_lower:
                seen.append(key)
                seen_lower.add(lower)
        return seen

    def configured(self) -> bool:
        return bool(settings.openai_api_key and settings.openai_base_url and settings.openai_model)

    def translate(self, names: list[str]) -> dict[str, str]:
        if not names or not self.configured():
            return {}
        body = json.dumps(
            {
                "model": settings.openai_model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": json.dumps(names, ensure_ascii=False)},
                ],
                "temperature": 0.1,
                # The configured model is a reasoning model: it spends tokens on
                # hidden reasoning before emitting content, so the budget has to
                # cover both or the answer comes back empty.
                "max_tokens": 8000,
            },
            ensure_ascii=False,
        ).encode("utf-8")
        request = Request(
            f"{settings.openai_base_url.rstrip('/')}/v1/chat/completions",
            data=body,
            headers={
                "Authorization": f"Bearer {settings.openai_api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=90) as response:
                payload = json.loads(response.read().decode("utf-8"))
            choice = payload.get("choices", [{}])[0]
            if choice.get("finish_reason") == "length":
                return {}
            content = str(choice.get("message", {}).get("content", ""))
        except Exception:
            # Network hiccups and truncated responses are expected when
            # translating hundreds of names in a row; skip the batch and let
            # the caller retry the remainder.
            return {}
        parsed = _extract_json(content)
        if not parsed:
            return {}
        return {str(key): str(value) for key, value in parsed.items() if isinstance(value, str) and value.strip()}


anatomy_term_service = AnatomyTermService()
