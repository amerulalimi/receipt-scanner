import uuid
from decimal import Decimal

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.receipt import Receipt
from app.models.user import User


class UserRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_by_email(self, email: str) -> User | None:
        result = await self._db.execute(
            select(User).where(User.email == email),
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        result = await self._db.execute(
            select(User).where(User.id == user_id),
        )
        return result.scalar_one_or_none()

    async def get_by_id_with_org(self, user_id: uuid.UUID) -> User | None:
        result = await self._db.execute(
            select(User)
            .options(selectinload(User.organisation))
            .where(User.id == user_id),
        )
        return result.scalar_one_or_none()

    async def update_role(self, user_id: uuid.UUID, role: str) -> User | None:
        user = await self.get_by_id(user_id)
        if user is None:
            return None
        user.role = role
        await self._db.flush()
        await self._db.refresh(user)
        return user

    async def create(
        self,
        *,
        email: str,
        password_hash: str,
        full_name: str,
        role: str,
        org_id: uuid.UUID | None = None,
        account_type: str = "individual",
    ) -> User:
        user = User(
            email=email,
            password_hash=password_hash,
            full_name=full_name,
            role=role,
            org_id=org_id,
            account_type=account_type,
        )
        self._db.add(user)
        await self._db.flush()
        await self._db.refresh(user)
        return user

    async def list_active_verified(self) -> list[User]:
        result = await self._db.execute(
            select(User).where(
                User.is_active.is_(True),
                User.email_verified.is_(True),
            ),
        )
        return list(result.scalars().all())

    async def assign_to_org(
        self,
        user_id: uuid.UUID,
        *,
        org_id: uuid.UUID,
        role: str,
    ) -> User | None:
        user = await self.get_by_id(user_id)
        if user is None:
            return None
        user.org_id = org_id
        user.role = role
        await self._db.flush()
        await self._db.refresh(user)
        return user

    async def remove_from_org(self, user_id: uuid.UUID) -> User | None:
        user = await self.get_by_id(user_id)
        if user is None:
            return None
        user.org_id = None
        user.role = "individual"
        user.account_type = "individual"
        await self._db.flush()
        await self._db.refresh(user)
        return user

    async def set_active(
        self,
        user_id: uuid.UUID,
        *,
        is_active: bool,
    ) -> User | None:
        user = await self.get_by_id(user_id)
        if user is None:
            return None
        user.is_active = is_active
        await self._db.flush()
        await self._db.refresh(user)
        return user

    async def get_org_member(
        self,
        org_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> User | None:
        result = await self._db.execute(
            select(User).where(
                User.id == user_id,
                User.org_id == org_id,
                User.role.in_(("employee", "hr_admin", "superadmin")),
            ),
        )
        return result.scalar_one_or_none()

    async def list_org_employees(
        self,
        org_id: uuid.UUID,
        *,
        search: str | None,
        status: str | None,
        page: int,
        limit: int,
    ) -> tuple[list[tuple[User, int, Decimal, int]], int]:
        receipt_stats = (
            select(
                Receipt.user_id.label("user_id"),
                func.count(Receipt.id).label("receipts_count"),
                func.coalesce(func.sum(Receipt.claimed_amount), 0).label(
                    "total_claimed",
                ),
                func.count(Receipt.id)
                .filter(Receipt.status == "pending")
                .label("pending_count"),
            )
            .where(Receipt.deleted_at.is_(None))
            .group_by(Receipt.user_id)
            .subquery()
        )

        conditions = [
            User.org_id == org_id,
            User.role.in_(("employee", "hr_admin", "superadmin")),
        ]
        if search:
            pattern = f"%{search.strip()}%"
            conditions.append(
                or_(
                    User.full_name.ilike(pattern),
                    User.email.ilike(pattern),
                ),
            )
        if status == "active":
            conditions.append(User.is_active.is_(True))
        elif status == "inactive":
            conditions.append(User.is_active.is_(False))

        count_result = await self._db.execute(
            select(func.count()).select_from(User).where(*conditions),
        )
        total = int(count_result.scalar_one())

        offset = (page - 1) * limit
        result = await self._db.execute(
            select(
                User,
                func.coalesce(receipt_stats.c.receipts_count, 0),
                func.coalesce(receipt_stats.c.total_claimed, 0),
                func.coalesce(receipt_stats.c.pending_count, 0),
            )
            .outerjoin(receipt_stats, User.id == receipt_stats.c.user_id)
            .where(*conditions)
            .order_by(User.full_name.asc().nulls_last(), User.email.asc())
            .offset(offset)
            .limit(limit),
        )
        rows = [
            (row[0], int(row[1]), Decimal(str(row[2])), int(row[3]))
            for row in result.all()
        ]
        return rows, total

    async def mark_email_verified(self, user_id: uuid.UUID) -> User | None:
        user = await self.get_by_id(user_id)
        if user is None:
            return None
        user.email_verified = True
        await self._db.flush()
        await self._db.refresh(user)
        return user

    async def update_profile(
        self,
        user_id: uuid.UUID,
        *,
        full_name: str,
        tax_year: int,
        tax_bracket: Decimal | None,
    ) -> User | None:
        user = await self.get_by_id(user_id)
        if user is None:
            return None
        user.full_name = full_name
        user.tax_year = tax_year
        user.tax_bracket = tax_bracket
        await self._db.flush()
        await self._db.refresh(user)
        return user
