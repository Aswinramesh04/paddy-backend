"""
PaddyCare AI — FastAPI Application Entry Point
"""
from __future__ import annotations

import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import PaddyCareException
from app.core.logging import get_logger, setup_logging
from app.db.database import check_db_connection
from app.db.init_db import init_db
from app.schemas.common import ErrorResponse, HealthResponse
from app.services.model_service import model_service

setup_logging()
log = get_logger(__name__)


# ── Lifespan ──────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    log.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION} [{settings.ENVIRONMENT}]")

    # Initialize database
    init_db()

    # Load AI model
    model_service.load()

    # Ensure upload directory exists
    Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)

    log.info("Application startup complete.")
    yield

    log.info("Application shutdown.")


# ── App instance ──────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "PaddyCare AI — REST API for paddy disease detection, "
        "treatment recommendations, and nearby agro shop discovery.\n\n"
        "**Authentication:** All endpoints (except /auth/*) require a Bearer JWT token.\n\n"
        "**Quick Start:**\n"
        "1. `POST /api/v1/auth/send-otp` with your phone number\n"
        "2. `POST /api/v1/auth/verify-otp` to get your token\n"
        "3. Include `Authorization: Bearer <token>` in all subsequent requests\n\n"
        "**Dev OTP bypass:** Set `OTP_BYPASS=true` and use code `123456`."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)


# ── Middleware ────────────────────────────────────────────────
app.add_middleware(GZipMiddleware, minimum_size=1000)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request timing middleware ─────────────────────────────────
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed = (time.perf_counter() - start) * 1000
    response.headers["X-Process-Time-Ms"] = f"{elapsed:.2f}"
    return response


# ── Static files (uploaded images) ───────────────────────────
upload_path = Path(settings.UPLOAD_DIR)
upload_path.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(upload_path)), name="static")


# ── Exception handlers ────────────────────────────────────────
@app.exception_handler(PaddyCareException)
async def paddycare_exception_handler(request: Request, exc: PaddyCareException):
    log.warning(f"Domain exception: {exc.error_code} — {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error_code=exc.error_code,
            message=exc.message,
            detail=exc.detail,
        ).model_dump(),
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    log.exception(f"Unhandled exception on {request.method} {request.url}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error_code="INTERNAL_ERROR",
            message="An unexpected error occurred. Please try again.",
        ).model_dump(),
    )


# ── Routers ───────────────────────────────────────────────────
app.include_router(api_router)


# ── Health check ──────────────────────────────────────────────
@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Service health check",
    description="Returns current health status of the API, database connection, and AI model.",
)
def health_check():
    return HealthResponse(
        status="ok",
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        db_connected=check_db_connection(),
        model_loaded=model_service.is_loaded,
    )


@app.get("/", include_in_schema=False)
def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health",
    }