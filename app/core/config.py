"""
Application configuration loaded from environment variables / .env file.
All settings are validated by Pydantic at startup.
"""
from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ───────────────────────────────────────────
    APP_NAME: str = "PaddyCare AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # ── Server ────────────────────────────────────────────────
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # ── Database ──────────────────────────────────────────────
    DATABASE_URL: str = "sqlite:///./paddycare.db"

    # ── JWT ───────────────────────────────────────────────────
    SECRET_KEY: str = "change-me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080   # 7 days
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # ── OTP ───────────────────────────────────────────────────
    OTP_EXPIRE_MINUTES: int = 10
    OTP_LENGTH: int = 6
    OTP_BYPASS: bool = False
    OTP_BYPASS_CODE: str = "123456"
    # Toggle OTP endpoints and behavior (useful to decommission SMS OTP without removing code)
    OTP_ENABLED: bool = False

    # ── SMS ───────────────────────────────────────────────────
    SMS_PROVIDER: str = "console"      # console | fast2sms | twilio | msg91
    FAST2SMS_API_KEY: str = ""

    # ── Weather ───────────────────────────────────────────────
    OPENWEATHER_API_KEY: str = ""
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_PHONE_NUMBER: str = ""

    # ── Email / SMTP ──────────────────────────────────────────
    EMAIL_PROVIDER: str = "smtp"    # console | smtp
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = "aswinramesh04@gmail.com"
    SMTP_PASS: str = "xhsx ezkn hctl gmie"
    EMAIL_FROM: str = "aswinramesh04@gmail.com"
    # ── Password reset ────────────────────────────────────────
    PASSWORD_RESET_EXPIRE_MINUTES: int = 60
    # Frontend URL used in password reset emails. Set to your frontend origin.
    FRONTEND_URL: str = "https://paddy-care-ai.netlify.app/"

    # ── File Upload ───────────────────────────────────────────
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE_MB: int = 10
    ALLOWED_IMAGE_TYPES: str = "image/jpeg,image/png,image/webp"

    # ── Model ─────────────────────────────────────────────────
    MODEL_PATH: str = "model/paddy_model.h5"
    MODEL_INPUT_SIZE: int = 224
    MODEL_CONFIDENCE_THRESHOLD: float = 0.5
    # Optional URL to download the model at startup if not present in the image
    MODEL_URL: str = ""

    # Clean common misconfiguration where an env var was set as "MODEL_PATH=..."
    @field_validator("MODEL_PATH", mode="before")
    def _sanitize_model_path(cls, v):
        try:
            if isinstance(v, str) and "=" in v:
                # Some hosts allow entering NAME=VALUE as the value; handle that gracefully
                return v.split("=", 1)[1].strip()
        except Exception:
            pass
        return v

    # ── CORS ──────────────────────────────────────────────────
    ALLOWED_ORIGINS: str = "*"

    # ── Logging ───────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "logs"

    # ── Derived properties ────────────────────────────────────
    @property
    def allowed_origins_list(self) -> List[str]:
        if self.ALLOWED_ORIGINS == "*":
            return ["*"]
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",")]

    @property
    def allowed_image_types_list(self) -> List[str]:
        return [t.strip() for t in self.ALLOWED_IMAGE_TYPES.split(",")]

    @property
    def max_file_size_bytes(self) -> int:
        return self.MAX_FILE_SIZE_MB * 1024 * 1024

    @property
    def is_sqlite(self) -> bool:
        return self.DATABASE_URL.startswith("sqlite")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()