from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app, exam_quiz_service
from backend.app.services import exam_quiz_service as quiz_module
from backend.app.services.exam_quiz_service import ExamQuizService


def settings(mode: str = "prebuild") -> dict:
    return {
        "question_types": {
            "single_choice": {"enabled": True, "option_counts": [4], "weight": 40},
            "true_false": {"enabled": True, "weight": 20},
            "short_answer": {"enabled": True, "weight": 40},
        },
        "difficulty": "exam",
        "generation_mode": mode,
        "system_prompt": "test prompt",
    }


def model_response() -> str:
    return json.dumps(
        {
            "questions": [
                {
                    "type": "single_choice",
                    "stem": "Which answer is correct?",
                    "options": ["A", "B", "C", "D"],
                    "answer_index": 1,
                    "explanation": "B is correct.",
                },
                {
                    "type": "true_false",
                    "stem": "This statement is true.",
                    "answer": True,
                    "explanation": "It is true.",
                },
                {
                    "type": "short_answer",
                    "stem": "Describe the structure.",
                    "points": ["point one", "point two"],
                    "explanation": "Reference explanation.",
                },
            ]
        }
    )


@pytest.fixture
def service(tmp_path, monkeypatch) -> ExamQuizService:
    monkeypatch.setattr(quiz_module, "QUESTION_CACHE_FILE", tmp_path / "exam_questions.json")
    monkeypatch.setattr(quiz_module.anatomy_textbook_service, "search", lambda _query: None)
    return ExamQuizService()


def test_signature_is_stable_and_sensitive_to_settings() -> None:
    first = settings()
    second = json.loads(json.dumps(first))
    assert ExamQuizService._signature(first) == ExamQuizService._signature(second)
    second["system_prompt"] = "changed"
    assert ExamQuizService._signature(first) != ExamQuizService._signature(second)


def test_question_counts_follow_teacher_weights() -> None:
    enabled = [("single_choice", 40), ("true_false", 20), ("short_answer", 40)]
    assert ExamQuizService._question_counts(enabled) == {
        "single_choice": 2,
        "true_false": 1,
        "short_answer": 2,
    }


def test_prebuild_cache_hides_answers_and_grades_by_id(service, monkeypatch) -> None:
    calls = 0

    def fake_chat(_messages, max_tokens=8000):
        nonlocal calls
        calls += 1
        return model_response()

    monkeypatch.setattr(quiz_module.exam_settings_service, "get", lambda: settings())
    monkeypatch.setattr(quiz_module, "_chat", fake_chat)

    first = service.generate("Heart", "心", "心血管系统")
    second = service.generate("Heart", "心", "心血管系统")

    assert calls == 1
    assert second["cached"] is True
    assert {"answer_index", "answer", "points", "explanation"}.isdisjoint(first["questions"][0])

    result = service.grade_by_id(first["questions"][0]["id"], 1)
    assert result["correct"] is True
    assert result["correct_answer"] == 1


def test_realtime_mode_bypasses_cached_quiz(service, monkeypatch) -> None:
    calls = 0

    def fake_chat(_messages, max_tokens=8000):
        nonlocal calls
        calls += 1
        return model_response()

    monkeypatch.setattr(quiz_module.exam_settings_service, "get", lambda: settings("realtime"))
    monkeypatch.setattr(quiz_module, "_chat", fake_chat)

    first = service.generate("Heart", "心", "心血管系统")
    second = service.generate("Heart", "心", "心血管系统")
    assert calls == 2
    assert first["quiz_id"] != second["quiz_id"]
    assert service.status()["cached_quizzes"] == 2


def test_model_failure_uses_gradable_local_fallback(service, monkeypatch) -> None:
    monkeypatch.setattr(quiz_module.exam_settings_service, "get", lambda: settings())
    monkeypatch.setattr(quiz_module, "_chat", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        quiz_module.anatomy_term_service,
        "all",
        lambda: {
            "Heart": "心",
            "Liver": "肝",
            "Spleen": "脾",
            "Kidney": "肾",
            "Stomach": "胃",
        },
    )

    quiz = service.generate("Heart", "心", "循环系统")

    assert quiz["source"] == "local_fallback"
    assert len(quiz["questions"]) == 5
    assert {question["type"] for question in quiz["questions"]} == {
        "single_choice",
        "true_false",
        "short_answer",
    }
    private_fields = {"answer_index", "answer", "points", "grading_keywords", "explanation"}
    assert all(private_fields.isdisjoint(question) for question in quiz["questions"])

    choice = next(question for question in quiz["questions"] if question["type"] == "single_choice")
    cached_choice = next(
        question
        for payload in service._load_cache().values()
        for question in payload["questions"]
        if question["id"] == choice["id"]
    )
    choice_result = service.grade_by_id(choice["id"], cached_choice["answer_index"])
    assert choice_result["correct"] is True

    short_answer = next(question for question in quiz["questions"] if question["type"] == "short_answer")
    short_result = service.grade_by_id(short_answer["id"], "心")
    assert short_result["correct"] is True
    assert short_result["score"] == 100


def test_quiz_api_requires_auth_and_uses_question_id(monkeypatch) -> None:
    client = TestClient(app)
    assert client.post("/api/exam/quiz/generate", json={"structure_en": "Heart"}).status_code == 401

    login = client.post(
        "/api/auth/login",
        json={"account": "student", "password": "student123"},
    )
    headers = {"Authorization": f"Bearer {login.json()['token']}"}
    monkeypatch.setattr(
        exam_quiz_service,
        "generate",
        lambda *_args, **_kwargs: {
            "enabled": True,
            "structure_en": "Heart",
            "questions": [{"id": "question-1", "type": "true_false", "stem": "Test"}],
        },
    )
    monkeypatch.setattr(
        exam_quiz_service,
        "grade_by_id",
        lambda question_id, answer: {
            "correct": question_id == "question-1" and answer is True,
            "score": 100,
            "feedback": "ok",
            "correct_answer": True,
        },
    )

    generated = client.post(
        "/api/exam/quiz/generate",
        headers=headers,
        json={"structure_en": "Heart"},
    )
    graded = client.post(
        "/api/exam/quiz/grade",
        headers=headers,
        json={"question_id": "question-1", "answer": True},
    )
    assert generated.status_code == 200
    assert graded.status_code == 200
    assert graded.json()["correct"] is True
