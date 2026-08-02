"""
Custom exception hierarchy for PaddyCare AI.
All domain exceptions inherit from PaddyCareException so they can be
caught globally in the exception handlers registered in main.py.
"""
from typing import Any, Dict, Optional


class PaddyCareException(Exception):
    """Base exception for all application errors."""

    status_code: int = 500
    error_code: str = "INTERNAL_ERROR"
    message: str = "An unexpected error occurred."

    def __init__(
        self,
        message: Optional[str] = None,
        detail: Optional[Any] = None,
    ) -> None:
        self.message = message or self.__class__.message
        self.detail = detail
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "error_code": self.error_code,
            "message": self.message,
        }
        if self.detail is not None:
            payload["detail"] = self.detail
        return payload


# ── 400 Bad Request ───────────────────────────────────────────
class BadRequestException(PaddyCareException):
    status_code = 400
    error_code = "BAD_REQUEST"
    message = "Bad request."


class InvalidFileTypeException(BadRequestException):
    error_code = "INVALID_FILE_TYPE"
    message = "Uploaded file type is not allowed."


class FileTooLargeException(BadRequestException):
    error_code = "FILE_TOO_LARGE"
    message = "Uploaded file exceeds the maximum allowed size."


class InvalidOTPException(BadRequestException):
    error_code = "INVALID_OTP"
    message = "The OTP entered is incorrect or has expired."


# ── 401 Unauthorized ──────────────────────────────────────────
class UnauthorizedException(PaddyCareException):
    status_code = 401
    error_code = "UNAUTHORIZED"
    message = "Authentication is required."


class InvalidTokenException(UnauthorizedException):
    error_code = "INVALID_TOKEN"
    message = "The provided token is invalid or has expired."


# ── 403 Forbidden ─────────────────────────────────────────────
class ForbiddenException(PaddyCareException):
    status_code = 403
    error_code = "FORBIDDEN"
    message = "You do not have permission to perform this action."


# ── 404 Not Found ─────────────────────────────────────────────
class NotFoundException(PaddyCareException):
    status_code = 404
    error_code = "NOT_FOUND"
    message = "The requested resource was not found."


class UserNotFoundException(NotFoundException):
    error_code = "USER_NOT_FOUND"
    message = "User not found."


class PredictionNotFoundException(NotFoundException):
    error_code = "PREDICTION_NOT_FOUND"
    message = "Prediction record not found."


class DiseaseNotFoundException(NotFoundException):
    error_code = "DISEASE_NOT_FOUND"
    message = "Disease information not found."


# ── 409 Conflict ──────────────────────────────────────────────
class ConflictException(PaddyCareException):
    status_code = 409
    error_code = "CONFLICT"
    message = "A conflict occurred with the current state."


class UserAlreadyExistsException(ConflictException):
    error_code = "USER_ALREADY_EXISTS"
    message = "A user with this phone number already exists."


# ── 422 Unprocessable ─────────────────────────────────────────
class ValidationException(PaddyCareException):
    status_code = 422
    error_code = "VALIDATION_ERROR"
    message = "Input validation failed."


# ── 429 Rate Limit ────────────────────────────────────────────
# ── 503 Service Unavailable ───────────────────────────────────
class ModelNotLoadedException(PaddyCareException):
    status_code = 503
    error_code = "MODEL_NOT_LOADED"
    message = "The AI model is not available. Please try again shortly."


class InvalidPaddyImageException(BadRequestException):
    error_code = "INVALID_PADDY_IMAGE"
    message = "Please upload a clear paddy leaf image."
