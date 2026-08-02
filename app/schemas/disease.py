"""Pydantic schemas for disease catalogue endpoints."""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel


class RecommendationResponse(BaseModel):
    id: int
    medicine_name: str
    dosage: Optional[str]
    how_to_use: Optional[str]
    benefits: Optional[str]
    precautions: Optional[str]
    medicine_type: str
    price_range: Optional[str]

    model_config = {"from_attributes": True}


class DiseaseDetailResponse(BaseModel):
    id: int
    class_index: int
    name: str
    name_ta: Optional[str]
    name_si: Optional[str]
    description: Optional[str]
    symptoms: Optional[str]
    severity: str
    image_url: Optional[str]
    recommendations: List[RecommendationResponse]
    prevention_tips: List[str]

    model_config = {"from_attributes": True}


class DiseaseListResponse(BaseModel):
    diseases: List[DiseaseDetailResponse]
    total: int