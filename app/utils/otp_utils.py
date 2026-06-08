"""
OTP SMS delivery abstraction.
Supports: console (dev), Fast2SMS, Twilio, MSG91.
Configured via SMS_PROVIDER in settings.
"""
from __future__ import annotations

import httpx
from loguru import logger

from app.core.config import settings
from app.core.exceptions import SMSDeliveryException


async def send_otp_sms(phone: str, otp: str) -> bool:
    """
    Send OTP SMS using the configured provider.
    Returns True on success, raises SMSDeliveryException on failure.
    """
    provider = settings.SMS_PROVIDER.lower()

    if provider == "console":
        return _send_console(phone, otp)
    elif provider == "fast2sms":
        return await _send_fast2sms(phone, otp)
    elif provider == "twilio":
        return await _send_twilio(phone, otp)
    else:
        logger.warning(f"Unknown SMS provider '{provider}', falling back to console.")
        return _send_console(phone, otp)


def _send_console(phone: str, otp: str) -> bool:
    """Print OTP to console (development mode)."""
    logger.info(f"[DEV OTP] Phone: {phone} | OTP: {otp}")
    print(f"\n{'='*40}\n  OTP for {phone}: {otp}\n{'='*40}\n")
    return True


async def _send_fast2sms(phone: str, otp: str) -> bool:
    """Send OTP via Fast2SMS DLT route."""
    if not settings.FAST2SMS_API_KEY:
        raise SMSDeliveryException(message="Fast2SMS API key not configured.")

    # Strip country code for Fast2SMS (expects 10-digit Indian number)
    local_phone = phone.lstrip("+").lstrip("91")[-10:]

    url = "https://www.fast2sms.com/dev/bulkV2"
    headers = {"authorization": settings.FAST2SMS_API_KEY}
    params = {
        "variables_values": otp,
        "route": "otp",
        "numbers": local_phone,
    }
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, headers=headers, params=params)
            data = resp.json()
            if data.get("return") is True:
                logger.info(f"Fast2SMS OTP sent to {phone}")
                return True
            logger.error(f"Fast2SMS error: {data}")
            raise SMSDeliveryException(detail=data)
    except httpx.RequestError as exc:
        logger.error(f"Fast2SMS request error: {exc}")
        raise SMSDeliveryException(detail=str(exc)) from exc


async def _send_twilio(phone: str, otp: str) -> bool:
    """Send OTP via Twilio Verify / Messaging."""
    if not all([settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN, settings.TWILIO_PHONE_NUMBER]):
        raise SMSDeliveryException(message="Twilio credentials not fully configured.")

    url = (
        f"https://api.twilio.com/2010-04-01/Accounts/"
        f"{settings.TWILIO_ACCOUNT_SID}/Messages.json"
    )
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                url,
                auth=(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN),
                data={
                    "From": settings.TWILIO_PHONE_NUMBER,
                    "To": phone,
                    "Body": f"Your PaddyCare AI OTP is: {otp}. Valid for {settings.OTP_EXPIRE_MINUTES} minutes.",
                },
            )
            if resp.status_code in (200, 201):
                logger.info(f"Twilio OTP sent to {phone}")
                return True
            logger.error(f"Twilio error {resp.status_code}: {resp.text}")
            raise SMSDeliveryException(detail=resp.text)
    except httpx.RequestError as exc:
        logger.error(f"Twilio request error: {exc}")
        raise SMSDeliveryException(detail=str(exc)) from exc