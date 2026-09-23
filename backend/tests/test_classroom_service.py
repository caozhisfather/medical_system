from pathlib import Path

import pytest

from backend.app.services.classroom_service import ClassroomService


def test_teacher_creates_class_student_joins_and_guidance_is_shared(tmp_path: Path) -> None:
    service = ClassroomService(tmp_path / "classrooms.sqlite3")
    classroom = service.create_class(
        teacher_id="teacher-1",
        teacher_account="teacher01",
        teacher_name="王老师",
        name="临床医学 2026-1 班",
        description="解剖学基础课程",
    )
    joined = service.join_by_code(
        student_id="student-1",
        student_account="student01",
        student_name="陈同学",
        code=classroom["code"].lower(),
    )

    detail = service.class_detail("teacher-1", classroom["id"])
    guidance = service.add_guidance(
        class_id=classroom["id"],
        student_id="student-1",
        author_id="teacher-1",
        author_name="王老师",
        source="teacher",
        content="先复习肝胆胰解剖定位，再完成一组混合题。",
        recommended_score=85,
    )

    assert joined["id"] == classroom["id"]
    assert detail["student_count"] == 1
    assert detail["students"][0]["student_name"] == "陈同学"
    assert guidance["recommended_score"] == 85
    assert service.list_guidance(student_id="student-1", class_id=classroom["id"])[0]["content"].startswith("先复习")
    assert service.is_member(classroom["id"], "student-1") is True


def test_classroom_requires_owner_and_valid_code(tmp_path: Path) -> None:
    service = ClassroomService(tmp_path / "classrooms.sqlite3")
    classroom = service.create_class(
        teacher_id="teacher-1",
        teacher_account="teacher01",
        teacher_name="王老师",
        name="解剖学一班",
    )

    with pytest.raises(PermissionError):
        service.class_detail("teacher-2", classroom["id"])
    with pytest.raises(KeyError):
        service.join_by_code(
            student_id="student-1",
            student_account="student01",
            student_name="陈同学",
            code="NOTFOUND",
        )
