from __future__ import annotations

from typing import Any
from pathlib import Path

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from ..config import settings
from ..services.auth_service import AuthService
from ..services.daily_review_service import DailyReviewService


router = APIRouter(prefix="/api/daily-review", tags=["daily-review"])
service = DailyReviewService()
auth_service = AuthService(Path(settings.auth_database_path))


class DailyReviewGenerateRequest(BaseModel):
    student_id: str = "student_001"
    force: bool = False


def require_review_role(authorization: str | None, allowed_roles: set[str]) -> dict[str, Any]:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="请先登录")
    user = auth_service.authenticated_user(authorization[7:].strip())
    if not user:
        raise HTTPException(status_code=401, detail="登录状态无效或已过期")
    if user.get("status") != "active":
        raise HTTPException(status_code=403, detail="账号当前不可用")
    if user["role"] not in allowed_roles:
        raise HTTPException(status_code=403, detail="没有权限访问该接口")
    return user


@router.get("/today/{student_id}")
def get_today_review(student_id: str) -> dict[str, Any]:
    return service.today(student_id)


@router.get("/history/{student_id}")
def get_review_history(student_id: str) -> list[dict[str, Any]]:
    return service.history(student_id)


@router.post("/generate")
def generate_review(payload: DailyReviewGenerateRequest) -> dict[str, Any]:
    return service.generate(payload.student_id, payload.force)


@router.get("/recommendations/{student_id}")
def get_review_recommendations(student_id: str) -> dict[str, Any]:
    return service.recommendations(student_id)


@router.get("/class/{class_id}")
def get_class_review(class_id: str = "clinical-2023-2", authorization: str | None = Header(default=None)) -> dict[str, Any]:
    require_review_role(authorization, {"teacher", "admin", "super_admin"})
    return service.class_review(class_id)


@router.get("/admin/config")
def get_admin_review_config(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    require_review_role(authorization, {"admin", "super_admin"})
    return service.admin_config()
