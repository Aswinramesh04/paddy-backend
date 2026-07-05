"""Pydantic schemas for authentication endpoints."""
from __future__ import annotations

import re
from typing import Optional

from pydantic import BaseModel, field_validator


class SendOTPRequest(BaseModel):
    phone: str

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        cleaned = re.sub(r"\s+", "", v)
        if not re.match(r"^\+?[1-9]\d{7,14}$", cleaned):
            raise ValueError("Invalid phone number format.")
        return cleaned

    model_config = {
        "json_schema_extra": {
            "examples": [{"phone": "+919876543210"}]
        }
    }


class VerifyOTPRequest(BaseModel):
    phone: str
    otp: str
    name: Optional[str] = None          # Collected on first-time signup

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        cleaned = re.sub(r"\s+", "", v)
        if not re.match(r"^\+?[1-9]\d{7,14}$", cleaned):
            raise ValueError("Invalid phone number format.")
        return cleaned

    @field_validator("otp")
    @classmethod
    def validate_otp(cls, v: str) -> str:
        if not v.isdigit():
            raise ValueError("OTP must be numeric.")
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [{"phone": "+919876543210", "otp": "123456", "name": "Ramesh Kumar"}]
        }
    }


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class RegisterRequest(BaseModel):
    email: str
    password: str
    name: Optional[str] = None

    model_config = {
        "json_schema_extra": {"examples": [{"email": "user@example.com", "password": "s3cret", "name": "Ramesh"}]}
    }


class LoginRequest(BaseModel):
    email: str
    password: str

    model_config = {"json_schema_extra": {"examples": [{"email": "user@example.com", "password": "s3cret"}]}}


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int                     # seconds
    is_new_user: bool = False

    model_config = {"from_attributes": True}


class SendOTPResponse(BaseModel):
    message: str
    phone: str
    expires_in_minutes: int


class PasswordResetRequest(BaseModel):
    email: str


class VerifyEmailRequest(BaseModel):
    token: str


class PasswordResetConfirmRequest(BaseModel):
    token: str
    new_password: str


class PasswordResetResponse(BaseModel):
    message: str