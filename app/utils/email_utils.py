"""Email sending utilities (console dev / SMTP prod)."""
from __future__ import annotations

import smtplib
from email.message import EmailMessage
from typing import Optional

from app.core.config import settings


def send_email(to: str, subject: str, body: str, html: Optional[str] = None) -> None:
    provider = settings.EMAIL_PROVIDER.lower()
    if provider == "console":
        print(f"\n--- EMAIL to: {to} ---\nSubject: {subject}\n\n{body}\n----------------\n")
        return

    # SMTP
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.EMAIL_FROM
    msg["To"] = to
    if html:
        msg.set_content(body)
        msg.add_alternative(html, subtype="html")
    else:
        msg.set_content(body)

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
        server.starttls()
        if settings.SMTP_USER and settings.SMTP_PASS:
            server.login(settings.SMTP_USER, settings.SMTP_PASS)
        server.send_message(msg)
