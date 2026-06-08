"""
Shop service — queries shops from DB and computes distances.
In production, integrate with Google Places API for real-time data.
"""
from __future__ import annotations

import json
import math
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.shop import Shop
from app.schemas.shop import ShopResponse


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return distance in km between two GPS coordinates."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _shop_to_response(shop: Shop, distance_km: Optional[float] = None) -> ShopResponse:
    medicines: Optional[List[str]] = None
    if shop.available_medicines:
        try:
            medicines = json.loads(shop.available_medicines)
        except Exception:
            medicines = [shop.available_medicines]

    return ShopResponse(
        id=shop.id,
        name=shop.name,
        address=shop.address,
        phone=shop.phone,
        latitude=shop.latitude,
        longitude=shop.longitude,
        rating=shop.rating,
        review_count=shop.review_count,
        opening_time=shop.opening_time,
        closing_time=shop.closing_time,
        is_open=shop.is_open,
        available_medicines=medicines,
        image_url=shop.image_url,
        distance_km=round(distance_km, 2) if distance_km is not None else None,
    )


class ShopService:

    @staticmethod
    def get_nearby(
        db: Session,
        latitude: float,
        longitude: float,
        radius_km: float = 10.0,
        medicine: Optional[str] = None,
    ) -> List[ShopResponse]:
        shops = db.query(Shop).filter(Shop.is_open == True).all()  # noqa: E712

        results = []
        for shop in shops:
            if shop.latitude is None or shop.longitude is None:
                continue
            dist = _haversine_km(latitude, longitude, shop.latitude, shop.longitude)
            if dist <= radius_km:
                # If medicine filter provided, parse shop.available_medicines (JSON list or string)
                if medicine:
                    meds = None
                    if shop.available_medicines:
                        try:
                            meds = json.loads(shop.available_medicines)
                        except Exception:
                            meds = [shop.available_medicines]
                    if not meds:
                        continue
                    # Normalize entries and do substring match per item
                    lowered = [str(m).lower() for m in meds]
                    if not any(medicine.lower() in m for m in lowered):
                        continue
                results.append((shop, dist))

        results.sort(key=lambda x: x[1])
        return [_shop_to_response(s, d) for s, d in results]

    @staticmethod
    def get_by_id(db: Session, shop_id: int) -> ShopResponse:
        from app.core.exceptions import NotFoundException
        shop = db.query(Shop).filter(Shop.id == shop_id).first()
        if not shop:
            raise NotFoundException(message="Shop not found.")
        return _shop_to_response(shop)

    @staticmethod
    def list_all(db: Session, page: int = 1, page_size: int = 20) -> List[ShopResponse]:
        offset = (page - 1) * page_size
        shops = db.query(Shop).offset(offset).limit(page_size).all()
        return [_shop_to_response(s) for s in shops]