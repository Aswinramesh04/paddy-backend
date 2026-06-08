"""Aggregate all API v1 endpoint routers."""
from fastapi import APIRouter

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.diseases import router as diseases_router
from app.api.v1.endpoints.history import router as history_router
from app.api.v1.endpoints.predictions import router as predictions_router
from app.api.v1.endpoints.shops import router as shops_router
from app.api.v1.endpoints.users import router as users_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(predictions_router)
api_router.include_router(history_router)
api_router.include_router(diseases_router)
api_router.include_router(shops_router)