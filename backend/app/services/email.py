from __future__ import annotations

import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


async def send_verification_email(*, email: str, token: str) -> None:
    verify_url = f"{settings.frontend_url.rstrip('/')}/verify-email?token={token}"
    logger.info(
        "E-mel pengesahan untuk %s — buka pautan ini (dev): %s",
        email,
        verify_url,
    )


async def send_invite_email(
    *,
    email: str | None,
    invite_url: str,
    org_name: str,
) -> None:
    if email:
        logger.info(
            "Jemputan ke %s untuk %s — buka pautan ini (dev): %s",
            org_name,
            email,
            invite_url,
        )
    else:
        logger.info(
            "Pautan jemputan pekerja untuk %s (dev): %s",
            org_name,
            invite_url,
        )


async def send_reminder_email(
    *,
    email: str,
    title_my: str,
    title_en: str,
    message_my: str,
    message_en: str,
) -> None:
    logger.info(
        "Peringatan e-mel untuk %s — %s / %s\nMY: %s\nEN: %s",
        email,
        title_my,
        title_en,
        message_my,
        message_en,
    )


async def send_monthly_digest_email(
    *,
    email: str,
    body_my: str,
    body_en: str,
) -> None:
    logger.info(
        "Digest bulanan untuk %s (dev):\n--- BM ---\n%s\n--- EN ---\n%s",
        email,
        body_my,
        body_en,
    )


async def send_org_export_email(
    *,
    org_name: str,
    filename: str,
    csv_content: str,
) -> None:
    logger.info(
        "Eksport payroll CSV untuk %s — %s (%s bytes) (dev)",
        org_name,
        filename,
        len(csv_content),
    )
