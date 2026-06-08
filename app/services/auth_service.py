"""
Authentication service.
Handles OTP generation, verification, and token issuance.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Tuple

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import (
    InvalidOTPException,
    OTPExpiredException,
    SMSDeliveryException,
)
from app.core.logging import get_logger
from app.core.security import (
    create_access_token,
    create_refresh_token,
    generate_otp,
    hash_otp,
    verify_otp,
)
from app.models.otp import OTP
from app.models.user import User
from app.utils.otp_utils import send_otp_sms

log = get_logger(__name__)


class AuthService:

    @staticmethod
    def get_or_create_user(db: Session, phone: str) -> Tuple[User, bool]:
        """
        Fetch existing user or create a new one.
        Returns (user, is_new_user).
        """
        user = db.query(User).filter(User.phone == phone).first()
        if user:
            return user, False

        user = User(phone=phone, is_active=True, is_verified=False)
        db.add(user)
        db.commit()
        db.refresh(user)
        log.info(f"New user created: phone={phone} id={user.id}")
        return user, True

    @staticmethod
    async def send_otp(db: Session, phone: str) -> str:
        """
        Generate OTP, persist hashed version, and dispatch SMS.
        Returns the plain OTP (only used in test mode).
        """
        user, _ = AuthService.get_or_create_user(db, phone)

        db.query(OTP).filter(OTP.user_id == user.id, OTP.is_used == False).delete()  # noqa: E712
        db.flush()

        if settings.OTP_BYPASS:
            plain_otp = settings.OTP_BYPASS_CODE
            log.info(f"[OTP BYPASS] Using code {plain_otp} for {phone}")
        else:
            plain_otp = generate_otp()

        otp_record = OTP(
            user_id=user.id,
            otp_hash=hash_otp(plain_otp),
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=settings.OTP_EXPIRE_MINUTES),
            is_used=False,
        )
        db.add(otp_record)
        db.commit()

        if not settings.OTP_BYPASS:
            await send_otp_sms(phone, plain_otp)

        return plain_otp

    @staticmethod
    def verify_otp_and_login(
        db: Session, phone: str, plain_otp: str, name: str | None = None
    ) -> Tuple[User, str, str, bool]:
        """
        Verify OTP, mark user as verified, issue tokens.

        Returns: (user, access_token, refresh_token, is_new_user)
        Raises: InvalidOTPException | OTPExpiredException
        """
        user = db.query(User).filter(User.phone == phone).first()
        if not user:
            raise InvalidOTPException()

        otp_record = (
            db.query(OTP)
            .filter(OTP.user_id == user.id, OTP.is_used == False)  # noqa: E712
            .order_by(OTP.created_at.desc())
            .first()
        )

        if not otp_record:
            raise InvalidOTPException()

        now = datetime.now(timezone.utc)
        if otp_record.expires_at.replace(tzinfo=timezone.utc) < now:
            raise OTPExpiredException()

        if not verify_otp(plain_otp, otp_record.otp_hash):
            raise InvalidOTPException()

        # Mark OTP used
        otp_record.is_used = True
        otp_record.verified_at = now

        is_new_user = not user.is_verified

        # Update user
        user.is_verified = True
        if name and not user.name:
            user.name = name

        db.commit()
        db.refresh(user)

        access_token = create_access_token(user.id, user.phone)
        refresh_token = create_refresh_token(user.id)

        log.info(f"User logged in: id={user.id} phone={phone} new={is_new_user}")
        return user, access_token, refresh_token, is_new_user

    @staticmethod
    def refresh_tokens(db: Session, user_id: int) -> Tuple[str, str]:
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            from app.core.exceptions import UnauthorizedException
            raise UnauthorizedException()
        access_token = create_access_token(user.id, user.phone)
        refresh_token = create_refresh_token(user.id)
        return access_token, refresh_token