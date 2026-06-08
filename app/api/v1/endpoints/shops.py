"""
Nearby agro shops endpoints.

POST /shops/nearby     → Find shops near GPS coordinates
GET  /shops            → List all shops (paginated)
GET  /shops/{id}       → Get shop detail
"""
from __future__ import annotations

import os
import sys
if "app" not in sys.modules:
    _project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../"))
    if _project_root not in sys.path:
        sys.path.insert(0, _project_root)

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.v1.dependencies import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.common import SuccessResponse
from app.schemas.shop import NearbyShopsRequest, ShopResponse
from app.services.shop_service import ShopService

router = APIRouter(prefix="/shops", tags=["Shops"])


@router.post(
    "/nearby",
    response_model=SuccessResponse[list[ShopResponse]],
    summary="Find nearby agro shops",
    description=(
        "Accepts user GPS coordinates and returns a list of nearby agro shops "
        "sorted by distance. Optionally filter by medicine name."
    ),
)
def get_nearby_shops(
    payload: NearbyShopsRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    shops = ShopService.get_nearby(
        db, payload.latitude, payload.longitude, payload.radius_km, payload.medicine
    )
    return SuccessResponse(
        message=f"{len(shops)} shops found.",
        data=shops,
    )


@router.get(
    "",
    response_model=SuccessResponse[list[ShopResponse]],
    summary="List all shops",
)
def list_shops(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    shops = ShopService.list_all(db, page, page_size)
    return SuccessResponse(message="Shops retrieved.", data=shops)


@router.get(
    "/{shop_id}",
    response_model=SuccessResponse[ShopResponse],
    summary="Get shop detail",
)
def get_shop(
    shop_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    shop = ShopService.get_by_id(db, shop_id)
    return SuccessResponse(message="Shop retrieved.", data=shop)