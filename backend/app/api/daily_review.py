from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from ..services.daily_review_service import DailyReviewService


router = APIRouter(prefix="/api/daily-review", tags=["daily-review"])
service = DailyReviewService()


class DailyReviewGenerateRequest(BaseModel):
    student_id: str = "student_001"
    force: bool = False


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
def get_class_review(class_id: str = "clinical-2023-2") -> dict[str, Any]:
    return service.class_review(class_id)


@router.get("/admin/config")
def get_admin_review_config() -> dict[str, Any]:
    return service.admin_config()
