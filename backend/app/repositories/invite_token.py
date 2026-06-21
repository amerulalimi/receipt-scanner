import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.invite_token import InviteToken


class InviteTokenRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, invite: InviteToken) -> InviteToken:
        self._db.add(invite)
        await self._db.flush()
        await self._db.refresh(invite)
        return invite

    async def get_by_token(self, token: str) -> InviteToken | None:
        result = await self._db.execute(
            select(InviteToken)
            .options(selectinload(InviteToken.organisation))
            .where(InviteToken.token == token),
        )
        return result.scalar_one_or_none()

    async def mark_used(
        self,
        invite: InviteToken,
        *,
        used_by: uuid.UUID,
    ) -> InviteToken:
        invite.used = True
        invite.used_by = used_by
        invite.used_at = datetime.now(UTC)
        await self._db.flush()
        await self._db.refresh(invite)
        return invite
