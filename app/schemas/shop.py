"""Pydantic schemas for nearby agro shops."""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel


class ShopResponse(BaseModel):
    id: int
    name: str
    address: Optional[str]
    phone: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    rating: float
    review_count: int
    opening_time: Optional[str]
    closing_time: Optional[str]
    is_open: bool
    available_medicines: Optional[List[str]]
    image_url: Optional[str]
    distance_km: Optional[float] = None   # Populated when lat/lng provided

    model_config = {"from_attributes": True}


class NearbyShopsRequest(BaseModel):
    latitude: float
    longitude: float
    radius_km: float = 10.0
    medicine: Optional[str] = None       # Filter by medicine availability

    model_config = {
        "json_schema_extra": {
            "examples": [{"latitude": 11.1085, "longitude": 77.3411, "radius_km": 10}]
        }
    }