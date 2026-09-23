from pathlib import Path

from backend.app.services.anatomy_learning_service import AnatomyLearningService


def test_anatomy_learning_records_and_mistakes(tmp_path: Path) -> None:
    service = AnatomyLearningService(tmp_path / "anatomy_learning.sqlite3")
    exercise = {
        "id": "heart_position",
        "title": "心脏定位",
        "system": "循环系统",
        "organ": "心脏",
        "target": "心脏",
        "explanation": "心脏位于纵隔内。",
        "clinical_link": "与胸痛评估相关。",
    }

    correct = service.record(
        account="student01",
        user_id="u_student_01",
        exercise=exercise,
        selected_zone="left_chest",
        correct=True,
        score=90,
        feedback="定位正确",
        explanation=exercise["explanation"],
        clinical_link=exercise["clinical_link"],
        image_node_id="heart_chambers",
        target_structure_id="left_ventricle",
        click_x=60,
        click_y=70,
    )
    service.record(
        account="student01",
        user_id="u_student_01",
        exercise=exercise,
        selected_zone="outside",
        correct=False,
        score=60,
        feedback="定位错误",
        explanation=exercise["explanation"],
        clinical_link=exercise["clinical_link"],
        image_node_id="heart_chambers",
        target_structure_id="left_ventricle",
        click_x=10,
        click_y=10,
    )
    service.record(
        account="student01",
        user_id="u_student_01",
        exercise=exercise,
        selected_zone="outside",
        correct=False,
        score=64,
        feedback="定位错误",
        explanation=exercise["explanation"],
        clinical_link=exercise["clinical_link"],
    )

    records = service.records("student01")
    mistakes = service.mistakes("student01")

    assert correct["id"].startswith("anatomy-")
    assert records["summary"] == {
        "total": 3,
        "correct": 1,
        "accuracy": 33,
        "average_score": 71,
    }
    assert len(records["items"]) == 3
    assert any(item["target_structure_id"] == "" for item in records["items"])
    assert mistakes["items"][0]["exercise_id"] == "heart_position"
    assert mistakes["items"][0]["attempt_count"] == 2
    assert mistakes["items"][0]["best_score"] == 64


def test_quiz_attempts_are_upserted_and_wrong_questions_are_listed(tmp_path: Path) -> None:
    service = AnatomyLearningService(tmp_path / "anatomy_learning.sqlite3")
    question = {
        "id": "question-1",
        "type": "single_choice",
        "stem": "左心室流出道连接哪一结构？",
        "options": ["主动脉", "肺动脉", "上腔静脉", "肺静脉"],
        "answer_index": 0,
        "structure_en": "heart",
        "structure_cn": "心脏",
        "structure_label": "心脏",
        "system": "循环系统",
        "citation": "《系统解剖学》",
    }

    service.record_quiz(
        account="student01",
        user_id="u_student_01",
        question=question,
        answer=1,
        result={
            "correct": False,
            "score": 0,
            "feedback": "回答错误。",
            "expected": "主动脉",
        },
        quiz_id="quiz-1",
    )
    service.record_quiz(
        account="student01",
        user_id="u_student_01",
        question=question,
        answer=0,
        result={
            "correct": True,
            "score": 100,
            "feedback": "回答正确。",
            "expected": "主动脉",
        },
        quiz_id="quiz-1",
    )

    records = service.quiz_records("student01")
    mistakes = service.quiz_mistakes("student01")

    assert records["summary"] == {
        "total": 1,
        "correct": 1,
        "accuracy": 100,
        "average_score": 100,
    }
    assert records["items"][0]["answer"] == "主动脉"
    assert mistakes["items"] == []
