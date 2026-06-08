"""
Authentication endpoints.

POST /auth/send-otp      → Send OTP to phone number
POST /auth/verify-otp    → Verify OTP and receive JWT tokens
POST /auth/refresh       → Refresh access token
POST /auth/guest         → Issue limited guest token
"""
from __future__ import annotations

import os
import sys
if "app" not in sys.modules:
    _project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../"))
    if _project_root not in sys.path:
        sys.path.insert(0, _project_root)

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_user_id_from_token
from app.db.database import get_db
from app.schemas.auth import (
    RefreshTokenRequest,
    SendOTPRequest,
    SendOTPResponse,
    TokenResponse,
    VerifyOTPRequest,
)
from app.schemas.common import SuccessResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/send-otp",
    response_model=SuccessResponse[SendOTPResponse],
    status_code=status.HTTP_200_OK,
    summary="Send OTP to mobile number",
    description=(
        "Sends a one-time password to the given phone number via SMS. "
        "If the number is new, a user account is automatically created. "
        "OTP expires after the configured timeout (default 10 minutes)."
    ),
)
async def send_otp(
    payload: SendOTPRequest,
    db: Session = Depends(get_db),
):
    await AuthService.send_otp(db, payload.phone)
    return SuccessResponse(
        message="OTP sent successfully.",
        data=SendOTPResponse(
            message="OTP has been sent to your mobile number.",
            phone=payload.phone,
            expires_in_minutes=settings.OTP_EXPIRE_MINUTES,
        ),
    )


@router.post(
    "/verify-otp",
    response_model=SuccessResponse[TokenResponse],
    status_code=status.HTTP_200_OK,
    summary="Verify OTP and receive JWT tokens",
    description=(
        "Verifies the OTP submitted by the user. "
        "On success, returns access and refresh tokens. "
        "Pass `name` on first-time login to set the user's display name."
    ),
)
def verify_otp(
    payload: VerifyOTPRequest,
    db: Session = Depends(get_db),
):
    user, access_token, refresh_token, is_new = AuthService.verify_otp_and_login(
        db, payload.phone, payload.otp, payload.name
    )
    return SuccessResponse(
        message="Login successful.",
        data=TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            is_new_user=is_new,
        ),
    )


@router.post(
    "/refresh",
    response_model=SuccessResponse[TokenResponse],
    status_code=status.HTTP_200_OK,
    summary="Refresh access token",
    description="Provide a valid refresh token to receive a new access/refresh token pair.",
)
def refresh_token(
    payload: RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    user_id = get_user_id_from_token(payload.refresh_token, expected_type="refresh")
    access_token, refresh_token = AuthService.refresh_tokens(db, user_id)
    return SuccessResponse(
        message="Token refreshed.",
        data=TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        ),
    )