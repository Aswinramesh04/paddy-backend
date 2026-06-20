"""
Prediction service — orchestrates image preprocessing, model inference,
database storage, and result assembly.
"""
from __future__ import annotations

import json
import math
from typing import Dict, List, Optional, Tuple

from fastapi import Request
from sqlalchemy.orm import Session, joinedload

from app.core.config import settings
from app.core.exceptions import InvalidPaddyImageException
from app.core.logging import get_logger
from app.models.disease import Disease, PreventionTip, Recommendation
from app.models.prediction import Prediction
from app.services.clip_service import clip_service
from app.schemas.prediction import (
    ClassProbability,
    DiseaseOut,
    PredictionHistoryItem,
    PredictionListResponse,
    PredictionResponse,
    PreventionTipOut,
    RecommendationOut,
)
from app.services.image_service import get_severity_from_confidence, preprocess_image_from_path
from app.services.model_service import DISEASE_CLASSES, model_service
from app.utils.file_utils import get_image_url

log = get_logger(__name__)


class PredictionService:

    @staticmethod
    def run_prediction(
        db: Session,
        user_id: int,
        image_path: str,
        image_filename: str,
        request: Optional[Request] = None,
    ) -> PredictionResponse:
        """
        Full prediction pipeline:
          1. Preprocess image
          2. Run model inference
          3. Persist prediction to DB
          4. Assemble and return response
        """
        # 1. Preprocess
        tensor = preprocess_image_from_path(image_path)

        
        if not clip_service.is_paddy_leaf(image_path):
            raise InvalidPaddyImageException(
                "Please upload a clear paddy leaf image."
            )
        # 2. Inference
        predicted_class, confidence, top_probs, elapsed_ms = model_service.predict(tensor)
        all_probs_json = json.dumps({p["class_name"]: p["probability"] for p in top_probs})
        severity = get_severity_from_confidence(confidence, predicted_class)

        # 3. Look up disease in DB by class name
        disease_record = (
            db.query(Disease)
            .options(
                joinedload(Disease.recommendations),
            )
            .filter(Disease.name == predicted_class)
            .first()
        )

        # 4. Persist prediction
        relative_path = image_path.replace(str(settings.UPLOAD_DIR) + "/", "")
        prediction = Prediction(
            user_id=user_id,
            disease_id=disease_record.id if disease_record else None,
            image_path=relative_path,
            image_filename=image_filename,
            predicted_class=predicted_class,
            confidence=confidence,
            severity=severity,
            all_probabilities=all_probs_json,
            processing_time_ms=elapsed_ms,
            model_version=model_service._model_version,
            status="completed",
        )
        db.add(prediction)
        db.commit()
        db.refresh(prediction)

        base_url = str(request.base_url).rstrip("/") if request else ""
        image_url = get_image_url(relative_path, base_url)

        # 5. Assemble response
        disease_out = None
        if disease_record:
            prevention_tips = (
                db.query(PreventionTip)
                .filter(PreventionTip.disease_id == disease_record.id)
                .order_by(PreventionTip.order_index)
                .all()
            )
            disease_out = DiseaseOut(
                id=disease_record.id,
                class_index=disease_record.class_index,
                name=disease_record.name,
                name_ta=disease_record.name_ta,
                name_hi=disease_record.name_hi,
                name_te=disease_record.name_te,
                description=disease_record.description,
                symptoms=disease_record.symptoms,
                severity=disease_record.severity,
                image_url=disease_record.image_url,
                recommendations=[
                    RecommendationOut.model_validate(r)
                    for r in sorted(disease_record.recommendations, key=lambda x: x.order_index)
                ],
                prevention_tips=[pt.tip for pt in prevention_tips],
            )

        return PredictionResponse(
            id=prediction.id,
            predicted_class=predicted_class,
            confidence=round(confidence, 4),
            confidence_percent=round(confidence * 100, 2),
            severity=severity,
            image_url=image_url,
            processing_time_ms=round(elapsed_ms, 2),
            model_version=prediction.model_version,
            created_at=prediction.created_at,
            disease=disease_out,
            top_probabilities=[ClassProbability(**p) for p in top_probs],
        )

    @staticmethod
    def get_history(
        db: Session,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
        request: Optional[Request] = None,
    ) -> PredictionListResponse:
        """Return paginated prediction history for a user."""
        offset = (page - 1) * page_size
        total = db.query(Prediction).filter(Prediction.user_id == user_id).count()

        records = (
            db.query(Prediction)
            .filter(Prediction.user_id == user_id)
            .order_by(Prediction.created_at.desc())
            .offset(offset)
            .limit(page_size)
            .all()
        )

        base_url = str(request.base_url).rstrip("/") if request else ""

        items = [
            PredictionHistoryItem(
                id=r.id,
                predicted_class=r.predicted_class,
                confidence=round(r.confidence, 4),
                confidence_percent=round(r.confidence * 100, 2),
                severity=r.severity,
                image_url=get_image_url(r.image_path, base_url),
                created_at=r.created_at,
            )
            for r in records
        ]

        total_pages = math.ceil(total / page_size) if page_size else 1

        return PredictionListResponse(
            predictions=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    @staticmethod
    def get_prediction_detail(
        db: Session, prediction_id: int, user_id: int, request: Optional[Request] = None
    ) -> PredictionResponse:
        from app.core.exceptions import PredictionNotFoundException

        prediction = (
            db.query(Prediction)
            .filter(Prediction.id == prediction_id, Prediction.user_id == user_id)
            .first()
        )
        if not prediction:
            raise PredictionNotFoundException()

        base_url = str(request.base_url).rstrip("/") if request else ""
        image_url = get_image_url(prediction.image_path, base_url)

        disease_out = None
        if prediction.disease_id:
            disease_record = (
                db.query(Disease)
                .options(joinedload(Disease.recommendations))
                .filter(Disease.id == prediction.disease_id)
                .first()
            )
            if disease_record:
                prevention_tips = (
                    db.query(PreventionTip)
                    .filter(PreventionTip.disease_id == disease_record.id)
                    .order_by(PreventionTip.order_index)
                    .all()
                )
                disease_out = DiseaseOut(
                    id=disease_record.id,
                    class_index=disease_record.class_index,
                    name=disease_record.name,
                    name_ta=disease_record.name_ta,
                    name_hi=disease_record.name_hi,
                    name_te=disease_record.name_te,
                    description=disease_record.description,
                    symptoms=disease_record.symptoms,
                    severity=disease_record.severity,
                    image_url=disease_record.image_url,
                    recommendations=[
                        RecommendationOut.model_validate(r)
                        for r in sorted(disease_record.recommendations, key=lambda x: x.order_index)
                    ],
                    prevention_tips=[pt.tip for pt in prevention_tips],
                )

        # Rebuild top probabilities from stored JSON
        top_probs = []
        if prediction.all_probabilities:
            stored = json.loads(prediction.all_probabilities)
            top_probs = [
                ClassProbability(class_name=k, probability=v)
                for k, v in sorted(stored.items(), key=lambda x: x[1], reverse=True)[:5]
            ]

        return PredictionResponse(
            id=prediction.id,
            predicted_class=prediction.predicted_class,
            confidence=round(prediction.confidence, 4),
            confidence_percent=round(prediction.confidence * 100, 2),
            severity=prediction.severity,
            image_url=image_url,
            processing_time_ms=prediction.processing_time_ms,
            model_version=prediction.model_version,
            created_at=prediction.created_at,
            disease=disease_out,
            top_probabilities=top_probs,
        )

    @staticmethod
    def delete_prediction(db: Session, prediction_id: int, user_id: int) -> None:
        from app.core.exceptions import PredictionNotFoundException
        from app.utils.file_utils import delete_file

        prediction = (
            db.query(Prediction)
            .filter(Prediction.id == prediction_id, Prediction.user_id == user_id)
            .first()
        )
        if not prediction:
            raise PredictionNotFoundException()
        delete_file(prediction.image_path)
        db.delete(prediction)
        db.commit()