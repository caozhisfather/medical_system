import pytest
from fastapi.testclient import TestClient

from backend.app import main
from backend.app.api import daily_review
from backend.app.services.auth_service import AuthService


@pytest.fixture
def auth_client(tmp_path, monkeypatch):
    service = AuthService(tmp_path / "auth.sqlite3")
    service.seed_demo_users(main.load_admin_users())
    monkeypatch.setattr(main, "auth_service", service)
    monkeypatch.setattr(daily_review, "auth_service", service)
    monkeypatch.setattr(main, "write_audit_log", lambda *args, **kwargs: None)
    sent = {}
    monkeypatch.setattr(main.mail_service, "send_verification", lambda email, token: sent.update(verification=token))
    monkeypatch.setattr(main.mail_service, "send_password_reset", lambda email, token: sent.update(reset=token))
    return TestClient(main.app), service, sent


def test_registration_verify_login_reset_and_logout(auth_client):
    client, service, sent = auth_client
    payload = {"account": "new_student", "name": "Test Student", "email": "student@example.com", "password": "Medical123", "role": "student"}
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 201
    assert "token" not in response.json()
    credentials = {"account": payload["account"], "password": payload["password"], "role": "student"}
    assert client.post("/api/auth/login", json=credentials).status_code == 401
    assert client.post("/api/auth/verify-email", json={"token": sent["verification"]}).status_code == 200
    assert client.post("/api/auth/verify-email", json={"token": sent["verification"]}).status_code == 400
    login = client.post("/api/auth/login", json=credentials)
    assert login.status_code == 200
    headers = {"Authorization": f"Bearer {login.json()['token']}"}
    assert client.get("/api/auth/me", headers=headers).status_code == 200
    assert client.get("/api/admin/users", headers=headers).status_code == 403
    assert client.post("/api/auth/forgot-password", json={"email": payload["email"]}).status_code == 200
    assert client.post("/api/auth/reset-password", json={"token": sent["reset"], "password": "NewMedical456"}).status_code == 200
    assert client.get("/api/auth/me", headers=headers).status_code == 401
    login = client.post("/api/auth/login", json={**credentials, "password": "NewMedical456"})
    headers = {"Authorization": f"Bearer {login.json()['token']}"}
    assert client.post("/api/auth/logout", headers=headers).status_code == 200
    assert client.get("/api/auth/me", headers=headers).status_code == 401


def test_teacher_review_and_existing_features(auth_client):
    client, service, sent = auth_client
    user, token = service.register("new_teacher", "Test Teacher", "teacher@example.com", "Medical123", "teacher")
    service.verify_email(token)
    credentials = {"account": "new_teacher", "password": "Medical123", "role": "teacher"}
    assert client.post("/api/auth/login", json=credentials).status_code == 401
    login = client.post("/api/auth/login", json={"account": "admin", "password": "admin123", "role": "admin"})
    assert login.status_code == 200
    headers = {"Authorization": f"Bearer {login.json()['token']}"}
    assert client.put(f"/api/admin/users/{user['id']}/teacher-review", headers=headers, json={"approved": True}).status_code == 200
    login = client.post("/api/auth/login", json=credentials)
    headers = {"Authorization": f"Bearer {login.json()['token']}"}
    assert client.get("/api/exam/settings", headers=headers).status_code == 200
    assert client.get("/api/daily-review/admin/config", headers=headers).status_code == 403
    assert client.get("/api/daily-review/class/clinical-2023-2", headers=headers).status_code == 200
    graph = client.get("/api/graph?scope=anatomy").json()
    assert sum(node["group"] == "AnatomyOrgan" for node in graph["nodes"]) == 48


def test_registration_validation_and_failed_mail_recovery(auth_client, monkeypatch):
    client, service, sent = auth_client
    payload = {"account": "mail_recovery", "name": "Test Student", "email": "mail@example.com", "password": "Medical123", "role": "student"}
    assert client.post("/api/auth/register", json={**payload, "role": "admin"}).status_code == 409
    assert client.post("/api/auth/register", json={**payload, "password": "abcdefgh"}).status_code == 422
    def failed_mail(*args):
        raise RuntimeError("private SMTP information")
    monkeypatch.setattr(main.mail_service, "send_verification", failed_mail)
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 503
    assert "private SMTP information" not in response.text
    monkeypatch.setattr(main.mail_service, "send_verification", lambda email, token: sent.update(verification=token))
    assert client.post("/api/auth/resend-verification", json={"email": payload["email"]}).status_code == 200
    assert client.post("/api/auth/verify-email", json={"token": sent["verification"]}).status_code == 200
