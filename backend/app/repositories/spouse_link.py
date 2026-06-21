import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.spouse_link import SpouseLink


class SpouseLinkRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_by_id(self, link_id: uuid.UUID) -> SpouseLink | None:
        result = await self._db.execute(
            select(SpouseLink).where(SpouseLink.id == link_id),
        )
        return result.scalar_one_or_none()

    async def get_accepted_for_user(self, user_id: uuid.UUID) -> SpouseLink | None:
        result = await self._db.execute(
            select(SpouseLink).where(
                SpouseLink.status == "accepted",
                (SpouseLink.requester_id == user_id) | (SpouseLink.partner_id == user_id),
            ),
        )
        return result.scalar_one_or_none()

    async def get_pending_for_email(self, email: str) -> list[SpouseLink]:
        result = await self._db.execute(
            select(SpouseLink)
            .options(selectinload(SpouseLink.requester))
            .where(
                SpouseLink.status == "pending",
                SpouseLink.partner_email == email.lower(),
            )
            .order_by(SpouseLink.created_at.desc()),
        )
        return list(result.scalars().all())

    async def get_pending_outgoing(self, user_id: uuid.UUID) -> SpouseLink | None:
        result = await self._db.execute(
            select(SpouseLink).where(
                SpouseLink.requester_id == user_id,
                SpouseLink.status == "pending",
            ),
        )
        return result.scalar_one_or_none()

    async def create(self, link: SpouseLink) -> SpouseLink:
        self._db.add(link)
        await self._db.flush()
        await self._db.refresh(link)
        return link
