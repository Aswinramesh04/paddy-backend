"""Authentication endpoints.

POST /auth/register      → Register with email/password
POST /auth/login         → Login with email/password
POST /auth/refresh       → Refresh access token
POST /auth/guest         → Issue limited guest token
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session

from app.core.security import get_user_id_from_token
from app.core.config import settings
from app.db.database import get_db
from app.schemas.auth import (
    RefreshTokenRequest,
    TokenResponse,
)
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    PasswordResetRequest,
    PasswordResetConfirmRequest,
    VerifyEmailRequest,
)
from app.schemas.common import SuccessResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])




@router.post(
    "/register",
    response_model=SuccessResponse[dict],
    status_code=status.HTTP_201_CREATED,
    summary="Register with email and password",
)
def register(
    payload: RegisterRequest,
    db: Session = Depends(get_db),
):
    user, message = AuthService.register_user(db, payload.email, payload.password, payload.name)
    return SuccessResponse(message=message, data={"email": user.email, "is_verified": user.is_verified})


@router.post(
    "/login",
    response_model=SuccessResponse[TokenResponse],
    status_code=status.HTTP_200_OK,
    summary="Login with email and password",
)
def login(
    payload: LoginRequest,
    db: Session = Depends(get_db),
):
    user, access_token, refresh_token = AuthService.login_with_password(db, payload.email, payload.password)
    return SuccessResponse(
        message="Login successful.",
        data=TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        ),
    )


@router.post(
    "/verify-email",
    response_model=SuccessResponse[dict],
    status_code=status.HTTP_200_OK,
    summary="Confirm email verification token",
)
def verify_email(payload: VerifyEmailRequest, db: Session = Depends(get_db)):
    ok = AuthService.confirm_email_verification(db, payload.token)
    if not ok:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired verification token.")
    return SuccessResponse(message="Email verified successfully.", data={})


@router.post(
    "/password-reset/request",
    response_model=SuccessResponse[dict],
    status_code=status.HTTP_200_OK,
    summary="Request password reset",
)
def password_reset_request(
    payload: "PasswordResetRequest",  # type: ignore
    db: Session = Depends(get_db),
):
    # Always return success to avoid user enumeration
    token = AuthService.create_password_reset(db, payload.email)
    return SuccessResponse(message="If an account exists, a password reset email has been sent.", data={})


@router.post(
    "/password-reset/confirm",
    response_model=SuccessResponse[dict],
    status_code=status.HTTP_200_OK,
    summary="Confirm password reset",
)
def password_reset_confirm(
    payload: "PasswordResetConfirmRequest",  # type: ignore
    db: Session = Depends(get_db),
):
    ok = AuthService.confirm_password_reset(db, payload.token, payload.new_password)
    if not ok:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token.")
    return SuccessResponse(message="Password has been reset.", data={})


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