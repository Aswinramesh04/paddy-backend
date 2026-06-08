"""
Disease prediction (scan) endpoints.

POST /predictions/scan          → Upload image and get disease prediction
GET  /predictions/{id}          → Get single prediction detail
DELETE /predictions/{id}        → Delete a prediction
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, Request, UploadFile, status
from sqlalchemy.orm import Session

from app.api.v1.dependencies import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.common import SuccessResponse
from app.schemas.prediction import PredictionResponse
from app.services.prediction_service import PredictionService
from app.utils.file_utils import validate_and_save_image

router = APIRouter(prefix="/predictions", tags=["Predictions"])


@router.post(
    "/scan",
    response_model=SuccessResponse[dict],
    status_code=status.HTTP_201_CREATED,
    summary="Scan paddy leaf image",
    description=(
        "Upload a clear image of a paddy leaf. "
        "The AI model analyzes the image and returns the predicted disease, "
        "confidence score, severity, and treatment recommendations."
    ),
)
async def scan_image(
    request: Request,
    file: UploadFile = File(..., description="JPEG/PNG/WebP image of paddy leaf (max 10 MB)"),
    latitude: float | None = None,
    longitude: float | None = None,
    radius_km: float = 10.0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    relative_path, full_path = await validate_and_save_image(file, sub_dir="predictions")
    result = PredictionService.run_prediction(
        db=db,
        user_id=current_user.id,
        image_path=full_path,
        image_filename=file.filename or "upload.jpg",
        request=request,
    )

    disease = result.disease
    recommendation = None
    if disease and getattr(disease, "recommendations", None):
        first = disease.recommendations[0]
        recommendation = {
            "medicine": first.medicine_name if hasattr(first, "medicine_name") else getattr(first, "medicine", None),
            "dosage": first.dosage if hasattr(first, "dosage") else None,
            "how_to_use": getattr(first, "how_to_use", None),
        }

    ui_payload = {
        "predicted_class": result.predicted_class,
        "confidence_percent": result.confidence_percent,
        "confidence": result.confidence,
        "severity": result.severity,
        "recommendation": recommendation,
        "prevention": disease.prevention_tips if disease and getattr(disease, "prevention_tips", None) else [],
        "top_probabilities": [p.model_dump() if hasattr(p, "model_dump") else p for p in result.top_probabilities],

        "_raw": result.model_dump() if hasattr(result, "model_dump") else result,
    }

    if latitude is not None and longitude is not None and recommendation and recommendation.get("medicine"):
        from app.services.shop_service import ShopService

        try:
            shops = ShopService.get_nearby(db, latitude, longitude, radius_km, medicine=recommendation.get("medicine"))
            ui_payload["nearby_shops"] = [s.model_dump() for s in shops]
        except Exception:
            ui_payload["nearby_shops"] = []

    return SuccessResponse(
        message="Prediction completed.",
        data=ui_payload,
    )


@router.get(
    "/{prediction_id}",
    response_model=SuccessResponse[PredictionResponse],
    summary="Get prediction detail",
)
def get_prediction(
    prediction_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = PredictionService.get_prediction_detail(
        db, prediction_id, current_user.id, request
    )
    return SuccessResponse(message="Prediction retrieved.", data=result)


@router.delete(
    "/{prediction_id}",
    response_model=SuccessResponse,
    summary="Delete prediction and associated image",
)
def delete_prediction(
    prediction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    PredictionService.delete_prediction(db, prediction_id, current_user.id)
    return SuccessResponse(message="Prediction deleted.")