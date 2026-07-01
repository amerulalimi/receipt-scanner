import uuid
from datetime import UTC, date, datetime

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.organisation import Organisation
from app.models.org_policy import DEFAULT_ALLOWED_CATEGORIES, OrgPolicy
from app.models.receipt import Receipt
from app.models.user import User
from app.repositories.receipt import ReceiptRepository
from app.repositories.user import UserRepository
from app.utils.db_period import get_dialect_name, period_expression


class OrganisationRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_by_id(self, org_id: uuid.UUID) -> Organisation | None:
        result = await self._db.execute(
            select(Organisation).where(Organisation.id == org_id),
        )
        return result.scalar_one_or_none()

    async def get_by_id_with_policy(self, org_id: uuid.UUID) -> Organisation | None:
        result = await self._db.execute(
            select(Organisation)
            .options(selectinload(Organisation.org_policy))
            .where(Organisation.id == org_id),
        )
        return result.scalar_one_or_none()

    async def get_by_ssm(self, ssm_number: str) -> Organisation | None:
        result = await self._db.execute(
            select(Organisation).where(Organisation.ssm_number == ssm_number),
        )
        return result.scalar_one_or_none()

    async def get_by_email_domain(self, email_domain: str) -> Organisation | None:
        result = await self._db.execute(
            select(Organisation).where(Organisation.email_domain == email_domain),
        )
        return result.scalar_one_or_none()

    async def count_employees(self, org_id: uuid.UUID) -> int:
        result = await self._db.execute(
            select(func.count())
            .select_from(User)
            .where(
                User.org_id == org_id,
                User.role.in_(("employee", "hr_admin", "superadmin")),
            ),
        )
        return int(result.scalar_one())

    async def list_paginated(
        self,
        *,
        search: str | None,
        page: int,
        limit: int,
    ) -> tuple[list[tuple[Organisation, int]], int]:
        employee_count = (
            select(
                User.org_id.label("org_id"),
                func.count().label("employee_count"),
            )
            .where(
                User.org_id.is_not(None),
                User.role.in_(("employee", "hr_admin", "superadmin")),
            )
            .group_by(User.org_id)
            .subquery()
        )

        conditions = []
        if search:
            pattern = f"%{search.strip()}%"
            conditions.append(
                or_(
                    Organisation.name.ilike(pattern),
                    Organisation.ssm_number.ilike(pattern),
                    Organisation.email_domain.ilike(pattern),
                ),
            )

        count_query = select(func.count()).select_from(Organisation)
        if conditions:
            count_query = count_query.where(*conditions)
        total = int((await self._db.execute(count_query)).scalar_one())

        query = (
            select(
                Organisation,
                func.coalesce(employee_count.c.employee_count, 0),
            )
            .outerjoin(employee_count, Organisation.id == employee_count.c.org_id)
            .order_by(Organisation.created_at.desc())
        )
        if conditions:
            query = query.where(*conditions)

        offset = (page - 1) * limit
        result = await self._db.execute(query.offset(offset).limit(limit))
        rows = [(row[0], int(row[1])) for row in result.all()]
        return rows, total

    async def set_status(
        self,
        org_id: uuid.UUID,
        *,
        status: str,
    ) -> Organisation | None:
        org = await self.get_by_id(org_id)
        if org is None:
            return None
        org.status = status
        org.updated_at = datetime.now(UTC)
        await self._db.flush()
        await self._db.refresh(org)
        return org

    async def count_created_in_range(
        self,
        *,
        from_date: date,
        to_date: date,
    ) -> int:
        start = datetime.combine(from_date, datetime.min.time(), tzinfo=UTC)
        end = datetime.combine(to_date, datetime.max.time(), tzinfo=UTC)
        result = await self._db.execute(
            select(func.count())
            .select_from(Organisation)
            .where(Organisation.created_at >= start, Organisation.created_at <= end),
        )
        return int(result.scalar_one())

    async def registration_counts_by_period(
        self,
        *,
        granularity: str,
        from_date: date,
        to_date: date,
    ) -> list[tuple[datetime, int]]:
        start = datetime.combine(from_date, datetime.min.time(), tzinfo=UTC)
        end = datetime.combine(to_date, datetime.max.time(), tzinfo=UTC)
        dialect_name = await get_dialect_name(self._db)
        period = period_expression(
            Organisation.created_at,
            granularity,
            dialect_name=dialect_name,
        ).label("period")
        result = await self._db.execute(
            select(period, func.count())
            .where(Organisation.created_at >= start, Organisation.created_at <= end)
            .group_by(period)
            .order_by(period),
        )
        return [(row[0], int(row[1])) for row in result.all()]

    async def create_with_policy(
        self,
        *,
        name: str,
        ssm_number: str,
        email_domain: str,
        updated_by: uuid.UUID,
    ) -> Organisation:
        now = datetime.now(UTC)
        org = Organisation(
            id=uuid.uuid4(),
            name=name.strip(),
            ssm_number=ssm_number.strip(),
            email_domain=email_domain.lower().strip(),
            domain_verified=False,
            status="active",
            created_at=now,
            updated_at=now,
        )
        self._db.add(org)
        await self._db.flush()

        policy = OrgPolicy(
            id=uuid.uuid4(),
            org_id=org.id,
            allowed_categories=list(DEFAULT_ALLOWED_CATEGORIES),
            require_hr_approval=True,
            max_receipts_per_month=50,
            tax_year=2025,
            updated_by=updated_by,
            updated_at=now,
        )
        self._db.add(policy)
        await self._db.flush()
        await self._db.refresh(org)
        return org

    async def get_org_employees(
        self,
        org_id: uuid.UUID,
        *,
        search: str | None = None,
        status: str | None = None,
        page: int = 1,
        limit: int = 20,
    ):
        return await UserRepository(self._db).list_org_employees(
            org_id,
            search=search,
            status=status,
            page=page,
            limit=limit,
        )

    async def get_org_pending_receipts(
        self,
        org_id: uuid.UUID,
        *,
        tax_year: int | None = None,
        page: int = 1,
        limit: int = 20,
    ):
        return await ReceiptRepository(self._db).list_pending_for_org(
            org_id=org_id,
            tax_year=tax_year,
            page=page,
            limit=limit,
        )
