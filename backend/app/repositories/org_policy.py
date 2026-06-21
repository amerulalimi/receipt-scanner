import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.org_policy import OrgPolicy


class OrgPolicyRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_by_org_id(self, org_id: uuid.UUID) -> OrgPolicy | None:
        result = await self._db.execute(
            select(OrgPolicy).where(OrgPolicy.org_id == org_id),
        )
        return result.scalar_one_or_none()

    async def update(
        self,
        policy: OrgPolicy,
        *,
        allowed_categories: list[str] | None,
        require_hr_approval: bool | None,
        max_receipts_per_month: int | None,
        tax_year: int | None,
        updated_by: uuid.UUID,
    ) -> OrgPolicy:
        if allowed_categories is not None:
            policy.allowed_categories = allowed_categories
        if require_hr_approval is not None:
            policy.require_hr_approval = require_hr_approval
        if max_receipts_per_month is not None:
            policy.max_receipts_per_month = max_receipts_per_month
        if tax_year is not None:
            policy.tax_year = tax_year
        policy.updated_by = updated_by
        await self._db.flush()
        await self._db.refresh(policy)
        return policy
