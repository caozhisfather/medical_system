import pytest
from fastapi.testclient import TestClient

from backend.app import main
from backend.app.services.auth_service import AuthService
from backend.app.services.classroom_service import ClassroomService


@pytest.fixture
def classroom_client(tmp_path, monkeypatch):
    auth = AuthService(tmp_path / "auth.sqlite3")
    auth.seed_demo_users(main.load_admin_users())
    classrooms = ClassroomService(tmp_path / "classrooms.sqlite3")
    monkeypatch.setattr(main, "auth_service", auth)
    monkeypatch.setattr(main, "classroom_service", classrooms)
    monkeypatch.setattr(main, "write_audit_log", lambda *args, **kwargs: None)
    return TestClient(main.app)


def _headers(client: TestClient, account: str, password: str, role: str) -> dict[str, str]:
    response = client.post(
        "/api/auth/login",
        json={"account": account, "password": password, "role": role},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['token']}"}


def test_teacher_class_join_guidance_and_ai_flow(classroom_client) -> None:
    client = classroom_client
    teacher_headers = _headers(client, "teacher", "teacher123", "teacher")
    student_headers = _headers(client, "student", "student123", "student")

    created = client.post(
        "/api/classrooms",
        headers=teacher_headers,
        json={"name": "临床医学 2026-1 班", "description": "解剖学课程"},
    )
    assert created.status_code == 200
    classroom = created.json()

    joined = client.post(
        "/api/classrooms/join",
        headers=student_headers,
        json={"code": classroom["code"]},
    )
    assert joined.status_code == 200

    detail = client.get(
        f"/api/classrooms/{classroom['id']}",
        headers=teacher_headers,
    )
    assert detail.status_code == 200
    student = detail.json()["students"][0]
    assert student["student_account"] == "student01"

    guidance = client.post(
        f"/api/classrooms/{classroom['id']}/guidance",
        headers=teacher_headers,
        json={
            "student_id": student["student_id"],
            "content": "先复习心脏和肝胆胰定位。",
            "recommended_score": 85,
        },
    )
    assert guidance.status_code == 200

    mine = client.get(
        "/api/classrooms/guidance/mine",
        headers=student_headers,
    )
    assert mine.status_code == 200
    assert mine.json()["items"][0]["recommended_score"] == 85

    ai = client.post(
        f"/api/classrooms/{classroom['id']}/guidance/ai",
        headers=student_headers,
        json={},
    )
    assert ai.status_code == 200
    assert ai.json()["source"] == "ai"
    assert ai.json()["content"]
