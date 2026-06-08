"""Pydantic schemas for user profile endpoints."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator


class UserBase(BaseModel):
    name: Optional[str] = None
    language: str = "en"
    dark_mode: bool = False
    notification_enabled: bool = True


class UserUpdateRequest(BaseModel):
    name: Optional[str] = None
    language: Optional[str] = None
    dark_mode: Optional[bool] = None
    notification_enabled: Optional[bool] = None

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        allowed = {"en", "ta", "hi", "te"}
        if v not in allowed:
            raise ValueError(f"Language must be one of: {', '.join(allowed)}")
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [{"name": "Ramesh Kumar", "language": "ta", "dark_mode": False}]
        }
    }


class UserResponse(BaseModel):
    id: int
    phone: str
    name: Optional[str]
    language: str
    is_verified: bool
    profile_image: Optional[str]
    dark_mode: bool
    notification_enabled: bool
    created_at: datetime

    model_config = {"from_attributes": True}