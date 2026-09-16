from __future__ import annotations

import json
from typing import Any

from ..config import ROOT_DIR

SETTINGS_FILE = ROOT_DIR / "data" / "exam_settings.json"

DEFAULT_SYSTEM_PROMPT = (
    "你是医学解剖学命题专家。根据给定的三维解剖结构，生成符合《系统解剖学》教学要求的题目。\n"
    "要求：\n"
    "1. 只考察该结构的形态、位置、毗邻、功能与常见临床联系，不涉及超纲内容。\n"
    "2. 干扰项必须来自同一系统或邻近结构，具有迷惑性但不能有歧义。\n"
    "3. 题干简洁，不使用否定式提问，不出现“以上都对”这类选项。\n"
    "4. 解析要给出判断依据，并尽量指向教材章节。"
)

DEFAULT_SETTINGS: dict[str, Any] = {
    "question_types": {
        "single_choice": {"enabled": True, "option_counts": [4], "weight": 40},
        "true_false": {"enabled": True, "weight": 20},
        "short_answer": {"enabled": True, "weight": 40},
    },
    "difficulty": "exam",
    # prebuild: the model writes questions ahead of time so students answer
    # without waiting. realtime: one call per structure, slower but always fresh.
    "generation_mode": "prebuild",
    "system_prompt": DEFAULT_SYSTEM_PROMPT,
    "updated_at": None,
    "updated_by": None,
}

ALLOWED_OPTION_COUNTS = {2, 3, 4, 5}
ALLOWED_DIFFICULTY = {"basic", "exam", "clinical"}
ALLOWED_GENERATION_MODES = {"prebuild", "realtime"}


class ExamSettingsService:
    """Stores the teacher-facing question configuration.

    The quiz engine reads this before asking the model for questions, so the
    teacher steers the exam through configuration instead of code changes.
    """

    def _read(self) -> dict[str, Any]:
        if not SETTINGS_FILE.exists():
            return json.loads(json.dumps(DEFAULT_SETTINGS))
        try:
            payload = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return json.loads(json.dumps(DEFAULT_SETTINGS))
        merged = json.loads(json.dumps(DEFAULT_SETTINGS))
        if isinstance(payload, dict):
            merged.update(payload)
        return merged

    def get(self) -> dict[str, Any]:
        return self._read()

    def update(self, payload: dict[str, Any], account: str | None = None) -> dict[str, Any]:
        current = self._read()

        incoming = payload.get("question_types")
        if isinstance(incoming, dict):
            for key, value in incoming.items():
                if key not in current["question_types"] or not isinstance(value, dict):
                    continue
                target = current["question_types"][key]
                if "enabled" in value:
                    target["enabled"] = bool(value["enabled"])
                if "weight" in value:
                    try:
                        target["weight"] = max(0, min(100, int(value["weight"])))
                    except (TypeError, ValueError):
                        pass
                if key == "single_choice" and "option_counts" in value:
                    counts = [
                        int(item)
                        for item in value["option_counts"]
                        if str(item).isdigit() and int(item) in ALLOWED_OPTION_COUNTS
                    ] if isinstance(value["option_counts"], list) else []
                    target["option_counts"] = sorted(set(counts)) or [4]

        difficulty = str(payload.get("difficulty") or "").strip()
        if difficulty in ALLOWED_DIFFICULTY:
            current["difficulty"] = difficulty

        mode = str(payload.get("generation_mode") or "").strip()
        if mode in ALLOWED_GENERATION_MODES:
            current["generation_mode"] = mode

        prompt = payload.get("system_prompt")
        if isinstance(prompt, str):
            cleaned = prompt.strip()
            # An empty prompt would leave the model unconstrained; keep the default.
            current["system_prompt"] = cleaned[:4000] if cleaned else DEFAULT_SYSTEM_PROMPT

        current["updated_at"] = _now()
        current["updated_by"] = account

        SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        temporary = SETTINGS_FILE.with_suffix(".tmp")
        temporary.write_text(json.dumps(current, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(SETTINGS_FILE)
        return current


def _now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()


exam_settings_service = ExamSettingsService()
