"""
Disease catalogue endpoints.

GET /diseases           → List all diseases
GET /diseases/{id}      → Get disease detail with recommendations
GET /diseases/chat      → AI chat stub (extensible)
"""
from __future__ import annotations

# When running this module directly (e.g. `python diseases.py`) the
# project root may not be on sys.path which causes "No module named 'app'".
# Ensure the repository root is first on sys.path so absolute imports work.
import os
import sys
if "app" not in sys.modules:
    _project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../"))
    if _project_root not in sys.path:
        sys.path.insert(0, _project_root)

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload

from app.api.v1.dependencies import get_current_user
from app.db.database import get_db
from app.models.disease import Disease, PreventionTip, Recommendation
from app.models.user import User
from app.schemas.common import SuccessResponse
from app.schemas.disease import DiseaseDetailResponse, DiseaseListResponse, RecommendationResponse
from app.core.exceptions import DiseaseNotFoundException

router = APIRouter(prefix="/diseases", tags=["Diseases"])


def _build_disease_response(disease: Disease, db: Session) -> DiseaseDetailResponse:
    tips = (
        db.query(PreventionTip)
        .filter(PreventionTip.disease_id == disease.id)
        .order_by(PreventionTip.order_index)
        .all()
    )
    return DiseaseDetailResponse(
        id=disease.id,
        class_index=disease.class_index,
        english=disease.name,
        tamil=disease.name_ta,
        # Sinhala column may not exist in DB yet; use getattr to avoid attribute errors
        sinhala=getattr(disease, "name_si", None),
        description=disease.description,
        symptoms=disease.symptoms,
        severity=disease.severity,
        image_url=disease.image_url,
        recommendations=[
            RecommendationResponse.model_validate(r)
            for r in sorted(disease.recommendations, key=lambda x: x.order_index)
        ],
        prevention_tips=[t.tip for t in tips],
    )


@router.get(
    "",
    response_model=SuccessResponse[DiseaseListResponse],
    summary="List all diseases",
    description="Returns the complete paddy disease catalogue with recommendations and prevention tips.",
)
def list_diseases(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    diseases = (
        db.query(Disease)
        .options(joinedload(Disease.recommendations))
        .order_by(Disease.class_index)
        .all()
    )
    items = [_build_disease_response(d, db) for d in diseases]
    return SuccessResponse(
        message="Diseases retrieved.",
        data=DiseaseListResponse(diseases=items, total=len(items)),
    )


@router.get(
    "/{disease_id}",
    response_model=SuccessResponse[DiseaseDetailResponse],
    summary="Get disease detail",
)
def get_disease(
    disease_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    disease = (
        db.query(Disease)
        .options(joinedload(Disease.recommendations))
        .filter(Disease.id == disease_id)
        .first()
    )
    if not disease:
        raise DiseaseNotFoundException()

    return SuccessResponse(
        message="Disease retrieved.",
        data=_build_disease_response(disease, db),
    )


@router.get(
    "/by-class/{class_index}",
    response_model=SuccessResponse[DiseaseDetailResponse],
    summary="Get disease by model class index",
)
def get_disease_by_class(
    class_index: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    disease = (
        db.query(Disease)
        .options(joinedload(Disease.recommendations))
        .filter(Disease.class_index == class_index)
        .first()
    )
    if not disease:
        raise DiseaseNotFoundException()

    return SuccessResponse(
        message="Disease retrieved.",
        data=_build_disease_response(disease, db),
    )