import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.organisation import Organisation
from app.models.org_policy import DEFAULT_ALLOWED_CATEGORIES, OrgPolicy
from app.models.user import User


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

    async def create_with_policy(
        self,
        *,
        name: str,
        ssm_number: str,
        email_domain: str,
        updated_by: uuid.UUID,
    ) -> Organisation:
        org = Organisation(
            name=name.strip(),
            ssm_number=ssm_number.strip(),
            email_domain=email_domain.lower().strip(),
            domain_verified=False,
            status="active",
        )
        self._db.add(org)
        await self._db.flush()

        policy = OrgPolicy(
            org_id=org.id,
            allowed_categories=list(DEFAULT_ALLOWED_CATEGORIES),
            require_hr_approval=True,
            max_receipts_per_month=50,
            tax_year=2025,
            updated_by=updated_by,
        )
        self._db.add(policy)
        await self._db.flush()
        await self._db.refresh(org)
        return org
