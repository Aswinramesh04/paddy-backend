"""Authentication service.
Handles user registration, password login, token refresh and password reset flow.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Tuple

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import get_logger
from app.core.security import create_access_token, create_refresh_token
from app.core.security import hash_password, verify_password
from app.models.password_reset import PasswordReset
import secrets
from datetime import timedelta
from app.utils.email_utils import send_email
from app.models.user import User
from app.core.exceptions import UnauthorizedException, ConflictException

log = get_logger(__name__)


class AuthService:
    @staticmethod
    def _get_user_by_email(db: Session, email: str) -> User | None:
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def refresh_tokens(db: Session, user_id: int) -> Tuple[str, str]:
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            raise UnauthorizedException()
        access_token = create_access_token(user.id, user.phone)
        refresh_token = create_refresh_token(user.id)
        return access_token, refresh_token

    @staticmethod
    def register_user(db: Session, email: str, password: str, name: str | None = None) -> Tuple[User, str, str]:
        """Create a new user with email/password and return user and tokens."""
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            from app.core.exceptions import ConflictException
            raise ConflictException(message="User with this email already exists.")

        user = User(email=email, name=name, is_active=True, is_verified=True)
        user.password_hash = hash_password(password)
        db.add(user)
        db.commit()
        db.refresh(user)

        access_token = create_access_token(user.id, user.phone or user.email or "")
        refresh_token = create_refresh_token(user.id)
        return user, access_token, refresh_token

    @staticmethod
    def login_with_password(db: Session, email: str, password: str) -> Tuple[User, str, str]:
        """Authenticate user by email/password and return user + tokens."""
        user = db.query(User).filter(User.email == email).first()
        if not user or not user.password_hash:
            raise UnauthorizedException()

        if not verify_password(password, user.password_hash):
            raise UnauthorizedException()

        access_token = create_access_token(user.id, user.phone or user.email or "")
        refresh_token = create_refresh_token(user.id)
        return user, access_token, refresh_token

    @staticmethod
    def create_password_reset(db: Session, email: str) -> str:
        """Create a password reset token and send it via email. Returns token (for testing)."""
        user = AuthService._get_user_by_email(db, email)
        if not user:
            return ""

        # Invalidate existing tokens for user
        db.query(PasswordReset).filter(PasswordReset.user_id == user.id, PasswordReset.is_used == False).update({
            "is_used": True
        })

        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.PASSWORD_RESET_EXPIRE_MINUTES)
        pr = PasswordReset(user_id=user.id, token=token, expires_at=expires_at, is_used=False)
        db.add(pr)
        db.commit()

        # send email (use configured frontend URL)
        reset_link = f"{settings.FRONTEND_URL.rstrip('/')}" + f"/reset-password?token={token}"
        subject = "PaddyCare AI — Password reset"
        body = f"You requested a password reset. Use this link to reset your password: {reset_link}\nIf you didn't request this, ignore."
        try:
            send_email(user.email, subject, body)
        except Exception:
            # Log and swallow; do not fail flow
            log.exception("Failed to send password reset email")

        return token

    @staticmethod
    def confirm_password_reset(db: Session, token: str, new_password: str) -> bool:
        """Validate reset token and set new password. Returns True on success."""
        pr = db.query(PasswordReset).filter(PasswordReset.token == token).first()
        if not pr or pr.is_used:
            return False

        now = datetime.now(timezone.utc)
        if pr.expires_at.replace(tzinfo=timezone.utc) < now:
            return False

        user = db.query(User).filter(User.id == pr.user_id).first()
        if not user:
            return False

        user.password_hash = hash_password(new_password)
        pr.is_used = True
        db.commit()
        return True