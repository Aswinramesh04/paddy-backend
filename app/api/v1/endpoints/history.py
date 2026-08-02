"""
Scan history / reports endpoints.

GET /history       → Paginated list of past scans
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.api.v1.dependencies import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.common import SuccessResponse
from app.schemas.prediction import PredictionListResponse
from app.services.prediction_service import PredictionService

router = APIRouter(prefix="/history", tags=["History"])


@router.get(
    "",
    response_model=SuccessResponse[PredictionListResponse],
    summary="Get scan history",
    description=(
        "Returns a paginated list of all previous disease scans for the current user, "
        "ordered most-recent first. Supports pagination via `page` and `page_size`."
    ),
)
def get_history(
    request: Request,
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = PredictionService.get_history(db, current_user.id, page, page_size, request)
    return SuccessResponse(message="History retrieved.", data=result)