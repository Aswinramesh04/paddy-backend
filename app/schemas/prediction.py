"""Pydantic schemas for prediction / scan endpoints."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class ClassProbability(BaseModel):
    class_name: str
    probability: float


class RecommendationOut(BaseModel):
    id: int
    medicine_name: str
    dosage: Optional[str]
    how_to_use: Optional[str]
    benefits: Optional[str]
    precautions: Optional[str]
    medicine_type: str
    price_range: Optional[str]

    model_config = {"from_attributes": True, "protected_namespaces": ()}


class PreventionTipOut(BaseModel):
    tip: str

    model_config = {"from_attributes": True, "protected_namespaces": ()}


class DiseaseOut(BaseModel):
    id: int
    class_index: int
    name: str
    name_ta: Optional[str]
    name_si: Optional[str]
    description: Optional[str]
    symptoms: Optional[str]
    severity: str
    image_url: Optional[str]
    recommendations: List[RecommendationOut] = []
    prevention_tips: List[str] = []

    model_config = {"from_attributes": True, "protected_namespaces": ()}


class PredictionResponse(BaseModel):
    id: int
    predicted_class: str
    confidence: float
    confidence_percent: float
    severity: str
    image_url: str
    processing_time_ms: Optional[float]
    model_version: str
    created_at: datetime
    disease: Optional[DiseaseOut]
    top_probabilities: List[ClassProbability] = []

    model_config = {"from_attributes": True, "protected_namespaces": ()}


class PredictionHistoryItem(BaseModel):
    id: int
    predicted_class: str
    confidence: float
    confidence_percent: float
    severity: str
    image_url: str
    created_at: datetime

    model_config = {"from_attributes": True, "protected_namespaces": ()}


class PredictionListResponse(BaseModel):
    predictions: List[PredictionHistoryItem]
    total: int
    page: int
    page_size: int
    total_pages: int