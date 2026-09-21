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
