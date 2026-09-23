from __future__ import annotations

import json
import hashlib
import re
from typing import Any
from uuid import uuid4
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from ..config import ROOT_DIR, settings
from .anatomy_textbook_service import anatomy_textbook_service
from .anatomy_term_service import anatomy_term_service
from .exam_settings_service import exam_settings_service

QUESTION_CACHE_FILE = ROOT_DIR / "data" / "exam_questions.json"
MAX_CACHED_QUIZZES = 250

_QUESTION_SPECS: dict[str, str] = {
    "single_choice": (
        "生成 {count} 道单项选择题。每题返回 options（选项数量依次从 {option_counts} 中循环使用，"
        "只写选项正文，不要写 A/B/C/D 前缀）"
        "与 answer_index（正确选项从 0 开始的序号）。干扰项必须来自同一系统或邻近结构。"
    ),
    "true_false": (
        "生成 {count} 道判断题。每题返回 stem（一句关于该结构的陈述，真伪明确、无歧义）"
        "与 answer（布尔值，true 表示该陈述正确）。"
    ),
    "short_answer": (
        "生成 {count} 道简答题，覆盖三个方面：这个结构是什么、有什么功能、会发生什么病变。"
        "每题返回 stem（题干）与 points（参考答案要点数组，3 至 5 条）。"
    ),
}

_OUTPUT_CONTRACT = (
    "只输出一个 JSON 对象，不要 Markdown 代码块或任何解释文字。结构如下：\n"
    '{"questions":[{"type":"single_choice","stem":"...","options":["...","..."],"answer_index":0,'
    '"explanation":"...","points":["..."]}]}\n'
    "选择题用 options 与 answer_index；判断题用 answer（布尔）并省略 options；简答题用 points。"
    "每题都要有 explanation，说明判断依据。"
)


def _extract_json(text: str) -> dict[str, Any] | None:
    cleaned = re.sub(r"^```(?:json)?", "", text.strip()).strip()
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


def _chat(messages: list[dict[str, str]], max_tokens: int = 8000) -> str | None:
    if settings.demo_mode or not (settings.openai_api_key and settings.openai_base_url and settings.openai_model):
        return None
    body = json.dumps(
        {
            "model": settings.openai_model,
            "messages": messages,
            "temperature": 0.4,
            # The configured model is a reasoning model, so the budget has to
            # cover hidden reasoning tokens before any content is emitted.
            "max_tokens": max_tokens,
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
        with urlopen(request, timeout=180) as response:
            raw = response.read()
        if not raw:
            return None
        payload = json.loads(raw.decode("utf-8"))
        choice = payload.get("choices", [{}])[0]
        if choice.get("finish_reason") == "length":
            return None
        return str(choice.get("message", {}).get("content", "")).strip() or None
    except Exception:
        # Model calls can fail in many ways (timeouts, truncated responses,
        # rate limits). Any failure degrades to "no questions" rather than
        # surfacing a 500 to the student.
        return None


class ExamQuizService:
    """Generates and grades the anatomy quiz.

    Question style is driven entirely by the teacher's stored settings: which
    types are enabled, how many options a choice question offers, the difficulty
    baseline, and the system prompt itself.
    """

    def _load_cache(self) -> dict[str, Any]:
        if not QUESTION_CACHE_FILE.exists():
            return {}
        try:
            payload = json.loads(QUESTION_CACHE_FILE.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        return payload if isinstance(payload, dict) else {}

    def _save_cache(self, cache: dict[str, Any]) -> None:
        QUESTION_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        temporary = QUESTION_CACHE_FILE.with_suffix(".tmp")
        temporary.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")
        temporary.replace(QUESTION_CACHE_FILE)

    def configured(self) -> bool:
        return not settings.demo_mode and bool(settings.openai_api_key and settings.openai_base_url and settings.openai_model)

    def _enabled_types(self, config: dict[str, Any]) -> list[tuple[str, int]]:
        types = config.get("question_types", {})
        enabled: list[tuple[str, int]] = []
        for key in ("single_choice", "true_false", "short_answer"):
            entry = types.get(key) or {}
            if entry.get("enabled"):
                enabled.append((key, int(entry.get("weight") or 0)))
        return enabled

    def _citation_for(self, chinese_name: str | None, english_name: str) -> tuple[str | None, str | None]:
        hit = anatomy_textbook_service.search(chinese_name or english_name)
        if not hit and chinese_name and chinese_name != english_name:
            hit = anatomy_textbook_service.search(english_name)
        if not hit:
            return None, None
        return hit.get("citation"), hit.get("content")

    def generate(
        self,
        english_name: str,
        chinese_name: str | None,
        system_label: str | None = None,
        force: bool = False,
    ) -> dict[str, Any]:
        english_name = english_name.strip()
        if not english_name:
            raise ValueError("english_name is required")

        config = exam_settings_service.get()
        enabled = self._enabled_types(config)
        if not enabled:
            return {
                "structure_en": english_name,
                "structure_cn": chinese_name,
                "enabled": False,
                "questions": [],
                "message": "教师尚未启用任何题型。",
            }

        mode = config.get("generation_mode", "prebuild")
        cache = self._load_cache()
        cache_key = english_name.lower()
        cached = next(
            (
                item
                for item in reversed(list(cache.values()))
                if isinstance(item, dict)
                and str(item.get("structure_en") or "").lower() == cache_key
                and item.get("signature") == self._signature(config)
            ),
            None,
        )
        if (
            mode == "prebuild"
            and not force
            and isinstance(cached, dict)
            and cached.get("signature") == self._signature(config)
        ):
            return {**self._public_payload(cached), "cached": True}

        citation, evidence = self._citation_for(chinese_name, english_name)
        label = f"{chinese_name}（{english_name}）" if chinese_name else english_name

        difficulty_map = {
            "basic": "基础识记：只考结构与名称。",
            "exam": "考试标准：考位置、毗邻与功能。",
            "clinical": "临床应用：结合损伤与病变。",
        }
        difficulty = difficulty_map.get(config.get("difficulty", "exam"), difficulty_map["exam"])

        specs: list[str] = []
        question_counts = self._question_counts(enabled)
        option_counts = config["question_types"]["single_choice"].get("option_counts") or [4]
        for key, weight in enabled:
            spec = _QUESTION_SPECS[key].format(
                count=question_counts[key],
                option_counts=" / ".join(str(item) for item in option_counts),
            )
            specs.append(f"[{key}，占分 {weight}%] {spec}")

        system_prompt = f"{config.get('system_prompt', '')}\n\n命题要求：{difficulty}"
        user_prompt = (
            f"解剖结构：{label}\n所属系统：{system_label or '未标注'}\n"
            + (f"教材依据：{citation}\n教材原文片段：{evidence[:500]}\n" if citation else "教材依据：暂未匹配到，请只使用公认的解剖学常识。\n")
            + "\n" + "\n".join(specs) + "\n\n" + _OUTPUT_CONTRACT
        )

        content = _chat([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ])
        parsed = _extract_json(content) if content else None
        raw_questions = parsed.get("questions") if isinstance(parsed, dict) else None
        questions = self._normalize(
            raw_questions if isinstance(raw_questions, list) else [],
            english_name,
            chinese_name,
            label,
            citation,
        )
        source = "ai"
        message = None
        if not questions:
            source = "local_fallback"
            message = "智能出题服务暂时不可用，已切换到本地辨认题库。"
            questions = self._normalize(
                self._fallback_questions(
                    english_name,
                    chinese_name,
                    system_label,
                    enabled,
                    question_counts,
                    option_counts,
                ),
                english_name,
                chinese_name,
                label,
                citation,
            )
        for question in questions:
            question["system"] = system_label or ""

        payload = {
            "quiz_id": uuid4().hex,
            "structure_en": english_name,
            "structure_cn": chinese_name,
            "structure_label": label,
            "system": system_label,
            "citation": citation,
            "enabled": True,
            "mode": mode,
            "source": source,
            "message": message,
            "signature": self._signature(config),
            "questions": questions,
        }
        cache[f"{cache_key}:{payload['quiz_id']}"] = payload
        while len(cache) > MAX_CACHED_QUIZZES:
            cache.pop(next(iter(cache)))
        self._save_cache(cache)
        return self._public_payload(payload)

    @staticmethod
    def _fallback_questions(
        english_name: str,
        chinese_name: str | None,
        system_label: str | None,
        enabled: list[tuple[str, int]],
        question_counts: dict[str, int],
        option_counts: list[int],
    ) -> list[dict[str, Any]]:
        """Build deterministic identification questions from the local glossary."""
        terms = anatomy_term_service.all()
        english_pool = sorted({name for name in terms if name.lower() != english_name.lower()})
        chinese_pool = sorted({name for name in terms.values() if name and name != chinese_name})
        seed = int(hashlib.sha256(english_name.lower().encode("utf-8")).hexdigest()[:12], 16)

        def options_for(answer: str, pool: list[str], count: int, offset: int) -> tuple[list[str], int]:
            size = max(2, min(5, count))
            candidates: list[str] = []
            if pool:
                start = (seed + offset) % len(pool)
                for step in range(len(pool)):
                    candidate = pool[(start + step) % len(pool)]
                    if candidate != answer and candidate not in candidates:
                        candidates.append(candidate)
                    if len(candidates) == size - 1:
                        break
            generic_index = 1
            while len(candidates) < size - 1:
                candidate = f"其他解剖结构 {generic_index}"
                if candidate != answer:
                    candidates.append(candidate)
                generic_index += 1
            answer_index = (seed + offset) % size
            candidates.insert(answer_index, answer)
            return candidates, answer_index

        questions: list[dict[str, Any]] = []
        enabled_keys = {key for key, _ in enabled}
        choice_total = question_counts.get("single_choice", 0)
        for index in range(choice_total):
            option_count = option_counts[index % len(option_counts)] if option_counts else 4
            if chinese_name and index % 2 == 0:
                options, answer_index = options_for(chinese_name, chinese_pool, option_count, index)
                stem = f"{english_name} 对应的规范中文解剖名称是？"
            else:
                options, answer_index = options_for(english_name, english_pool, option_count, index)
                stem = f"{chinese_name or '当前选中结构'} 对应的英文解剖名称是？"
            questions.append(
                {
                    "type": "single_choice",
                    "stem": stem,
                    "options": options,
                    "answer_index": answer_index,
                    "explanation": f"当前三维模型选中的结构为 {chinese_name or english_name}（{english_name}）。",
                }
            )

        for index in range(question_counts.get("true_false", 0)):
            if system_label and index % 2:
                stem = f"当前结构 {chinese_name or english_name} 的训练分类为{system_label}。"
                explanation = f"该结构在当前训练模型中归入{system_label}。"
            else:
                stem = f"{chinese_name or english_name} 的英文解剖名称是 {english_name}。"
                explanation = f"本地解剖术语表记录为 {chinese_name or english_name}（{english_name}）。"
            questions.append(
                {
                    "type": "true_false",
                    "stem": stem,
                    "answer": True,
                    "explanation": explanation,
                }
            )

        short_prompts: list[tuple[str, list[str], list[list[str]]]] = []
        if chinese_name:
            short_prompts.append(
                (
                    f"写出英文解剖名词 {english_name} 对应的规范中文名称。",
                    [f"中文名称：{chinese_name}"],
                    [[chinese_name]],
                )
            )
        short_prompts.append(
            (
                f"写出当前结构 {chinese_name or english_name} 的英文解剖名称。",
                [f"英文名称：{english_name}"],
                [[english_name]],
            )
        )
        if system_label:
            short_prompts.append(
                (
                    f"当前结构 {chinese_name or english_name} 在本训练模型中归入哪个系统？",
                    [f"所属系统：{system_label}"],
                    [[system_label, system_label.removesuffix("系统")]],
                )
            )
        for index in range(question_counts.get("short_answer", 0)):
            stem, points, keywords = short_prompts[index % len(short_prompts)]
            questions.append(
                {
                    "type": "short_answer",
                    "stem": stem,
                    "points": points,
                    "grading_keywords": keywords,
                    "explanation": "依据当前三维结构名称与本地解剖术语表评分。",
                }
            )

        return [question for question in questions if question["type"] in enabled_keys]

    @staticmethod
    def _question_counts(enabled: list[tuple[str, int]], total: int = 5) -> dict[str, int]:
        """Allocate a compact quiz according to the teacher's type weights."""
        total = max(total, len(enabled))
        counts = {key: 1 for key, _ in enabled}
        remaining = total - len(enabled)
        if not remaining:
            return counts

        weights = [max(0, weight) for _, weight in enabled]
        if not any(weights):
            weights = [1] * len(enabled)
        weight_total = sum(weights)
        quotas = [remaining * weight / weight_total for weight in weights]
        for (key, _), quota in zip(enabled, quotas):
            counts[key] += int(quota)
        assigned = sum(counts.values())
        order = sorted(
            range(len(enabled)),
            key=lambda index: (quotas[index] - int(quotas[index]), weights[index]),
            reverse=True,
        )
        for index in order[: total - assigned]:
            counts[enabled[index][0]] += 1
        return counts

    @staticmethod
    def _signature(config: dict[str, Any]) -> str:
        """Cache key for 'the teacher changed how questions are written'."""
        relevant = {
            "difficulty": config.get("difficulty"),
            "generation_mode": config.get("generation_mode"),
            "question_types": config.get("question_types", {}),
            "system_prompt": config.get("system_prompt", ""),
        }
        encoded = json.dumps(relevant, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()[:20]

    @staticmethod
    def _public_payload(payload: dict[str, Any]) -> dict[str, Any]:
        public = {key: value for key, value in payload.items() if key != "signature"}
        public["questions"] = [
            {
                key: value
                for key, value in question.items()
                if key not in {"answer_index", "answer", "points", "grading_keywords", "explanation"}
            }
            for question in payload.get("questions", [])
            if isinstance(question, dict)
        ]
        return public

    def _normalize(
        self,
        raw_questions: list[Any],
        english_name: str,
        chinese_name: str | None,
        label: str,
        citation: str | None,
    ) -> list[dict[str, Any]]:
        questions: list[dict[str, Any]] = []
        for index, raw in enumerate(raw_questions):
            if not isinstance(raw, dict):
                continue
            kind = str(raw.get("type") or "").strip()
            stem = str(raw.get("stem") or "").strip()
            if kind not in _QUESTION_SPECS or not stem:
                continue
            item: dict[str, Any] = {
                "type": kind,
                "stem": stem,
                "structure_en": english_name,
                "structure_cn": chinese_name,
                "structure_label": label,
                "explanation": str(raw.get("explanation") or "").strip(),
                "citation": citation,
            }
            if kind == "single_choice":
                options = [str(option).strip() for option in (raw.get("options") or []) if str(option).strip()]
                try:
                    answer_index = int(raw.get("answer_index"))
                except (TypeError, ValueError):
                    continue
                if len(options) < 2 or not 0 <= answer_index < len(options):
                    continue
                item["options"] = options
                item["answer_index"] = answer_index
            elif kind == "true_false":
                answer = raw.get("answer")
                if not isinstance(answer, bool):
                    continue
                item["answer"] = answer
            else:
                points = [str(point).strip() for point in (raw.get("points") or []) if str(point).strip()]
                if not points:
                    continue
                item["points"] = points
                grading_keywords = raw.get("grading_keywords")
                if isinstance(grading_keywords, list):
                    item["grading_keywords"] = [
                        [str(keyword).strip() for keyword in group if str(keyword).strip()]
                        for group in grading_keywords
                        if isinstance(group, list)
                    ]
            fingerprint = json.dumps(
                {"structure": english_name, "index": index, "question": item},
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
            item["id"] = hashlib.sha256(fingerprint).hexdigest()[:24]
            questions.append(item)
        return questions

    def grade_by_id(self, question_id: str, answer: Any) -> dict[str, Any]:
        located = self.find_question(question_id)
        question = located["question"]
        result = self.grade(question, answer)
        if question.get("type") == "single_choice":
            result["correct_answer"] = question.get("answer_index")
        elif question.get("type") == "true_false":
            result["correct_answer"] = question.get("answer")
        return result

    def find_question(self, question_id: str) -> dict[str, Any]:
        question_id = question_id.strip()
        if not question_id:
            raise KeyError(question_id)
        for payload in self._load_cache().values():
            if not isinstance(payload, dict):
                continue
            for question in payload.get("questions", []):
                if isinstance(question, dict) and question.get("id") == question_id:
                    return {
                        "quiz_id": str(payload.get("quiz_id") or ""),
                        "question": question,
                    }
        raise KeyError(question_id)

    def grade(self, question: dict[str, Any], answer: Any) -> dict[str, Any]:
        kind = question.get("type")
        if kind == "single_choice":
            try:
                picked = int(answer)
            except (TypeError, ValueError):
                return {"correct": False, "score": 0, "feedback": "未作答。"}
            correct = picked == question.get("answer_index")
            return {
                "correct": correct,
                "score": 100 if correct else 0,
                "feedback": question.get("explanation") or ("回答正确。" if correct else "回答错误。"),
                "expected": question.get("options", [None])[question.get("answer_index", 0)],
            }
        if kind == "true_false":
            if not isinstance(answer, bool):
                return {"correct": False, "score": 0, "feedback": "未作答。"}
            correct = answer == question.get("answer")
            return {
                "correct": correct,
                "score": 100 if correct else 0,
                "feedback": question.get("explanation") or ("判断正确。" if correct else "判断错误。"),
                "expected": "正确" if question.get("answer") else "错误",
            }
        if kind == "short_answer":
            text = str(answer or "").strip()
            if not text:
                return {"correct": False, "score": 0, "feedback": "未作答。"}
            return self._grade_short(question, text)
        return {"correct": False, "score": 0, "feedback": "未知题型。"}

    def _grade_short(self, question: dict[str, Any], answer: str) -> dict[str, Any]:
        points = question.get("points") or []
        keyword_groups = question.get("grading_keywords")
        if isinstance(keyword_groups, list) and keyword_groups:
            normalized_answer = re.sub(r"\s+", "", answer).lower()
            matched = [
                any(re.sub(r"\s+", "", str(keyword)).lower() in normalized_answer for keyword in group)
                for group in keyword_groups
                if isinstance(group, list) and group
            ]
            hit_points = [point for point, hit in zip(points, matched) if hit]
            missed_points = [point for point, hit in zip(points, matched) if not hit]
            score = round(100 * len(hit_points) / len(matched)) if matched else 0
            return {
                "correct": score >= 60,
                "score": score,
                "feedback": "已按本地术语关键词完成评分。",
                "hit_points": hit_points,
                "missed_points": missed_points,
            }
        fallback = {
            "correct": False,
            "score": 0,
            "feedback": "答案已记录，但自动评分服务暂时不可用。",
            "hit_points": [],
            "missed_points": points,
        }
        if not self.configured():
            return fallback
        content = _chat(
            [
                {
                    "role": "system",
                    "content": (
                        "你是解剖学阅卷老师。对照参考答案要点给学生作答打分，只输出 JSON："
                        '{"score":0-100,"hit_points":["..."],"missed_points":["..."],"feedback":"一句话总评"}'
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"题目：{question.get('stem')}\n"
                        f"参考答案要点：{json.dumps(points, ensure_ascii=False)}\n"
                        f"学生作答：{answer}"
                    ),
                },
            ],
            max_tokens=6000,
        )
        parsed = _extract_json(content) if content else None
        if not isinstance(parsed, dict):
            return fallback
        try:
            score = max(0, min(100, int(parsed.get("score"))))
        except (TypeError, ValueError):
            return fallback
        return {
            "correct": score >= 60,
            "score": score,
            "feedback": str(parsed.get("feedback") or "").strip() or "已评分。",
            "hit_points": [str(item) for item in (parsed.get("hit_points") or [])],
            "missed_points": [str(item) for item in (parsed.get("missed_points") or [])],
        }

    def status(self) -> dict[str, Any]:
        cache = self._load_cache()
        structures = {
            str(payload.get("structure_en") or "").lower()
            for payload in cache.values()
            if isinstance(payload, dict) and payload.get("structure_en")
        }
        return {
            "cached_quizzes": len(cache),
            "cached_structures": len(structures),
            "configured": self.configured(),
        }


exam_quiz_service = ExamQuizService()
