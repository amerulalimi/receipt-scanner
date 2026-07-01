from __future__ import annotations

import uuid

from app.core.deps import UserInSession
from app.core.exceptions import AppError


def is_corporate_context(session: UserInSession) -> bool:
    return session.active_context == "corporate" and session.org_id is not None


def ensure_individual_context(session: UserInSession) -> None:
    if session.active_context != "individual":
        raise AppError(
            message="Akses ini hanya tersedia dalam mod individu.",
            code="FORBIDDEN",
            status_code=403,
        )


def ensure_corporate_context(session: UserInSession) -> uuid.UUID:
    if not is_corporate_context(session):
        raise AppError(
            message="Akses ini hanya tersedia dalam mod korporat.",
            code="FORBIDDEN",
            status_code=403,
        )
    assert session.org_id is not None
    return session.org_id
