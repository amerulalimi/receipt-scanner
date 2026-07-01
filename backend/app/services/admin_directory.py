from __future__ import annotations

import math
import uuid
from datetime import date, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.repositories.organisation import OrganisationRepository
from app.repositories.user import UserRepository
from app.schemas.admin_directory import (
    AdminOrganizationDeleteData,
    AdminOrganizationListItem,
    AdminPaginatedOrganizationsData,
    AdminPaginatedUsersData,
    AdminUserDeleteData,
    AdminUserListItem,
    RegistrationStatsData,
)
from app.services.admin_directory_stats import (
    build_registration_stats_with_previous,
    default_stats_range,
)
from app.services.audit import AuditService

DEFAULT_LIMIT = 50
MAX_LIMIT = 100


class AdminDirectoryService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._users = UserRepository(db)
        self._orgs = OrganisationRepository(db)

    async def list_users(
        self,
        *,
        page: int = 1,
        limit: int = DEFAULT_LIMIT,
        search: str | None = None,
    ) -> AdminPaginatedUsersData:
        safe_limit = min(max(limit, 1), MAX_LIMIT)
        safe_page = max(page, 1)
        rows, total = await self._users.list_paginated(
            search=search,
            page=safe_page,
            limit=safe_limit,
        )
        total_pages = max(1, math.ceil(total / safe_limit)) if total else 1
        return AdminPaginatedUsersData(
            items=[
                AdminUserListItem(
                    id=user.id,
                    full_name=user.full_name,
                    account_type=user.account_type,
                    email=user.email,
                    created_at=user.created_at,
                    is_active=user.is_active,
                )
                for user in rows
            ],
            page=safe_page,
            limit=safe_limit,
            total=total,
            total_pages=total_pages,
        )

    async def list_organizations(
        self,
        *,
        page: int = 1,
        limit: int = DEFAULT_LIMIT,
        search: str | None = None,
    ) -> AdminPaginatedOrganizationsData:
        safe_limit = min(max(limit, 1), MAX_LIMIT)
        safe_page = max(page, 1)
        rows, total = await self._orgs.list_paginated(
            search=search,
            page=safe_page,
            limit=safe_limit,
        )
        total_pages = max(1, math.ceil(total / safe_limit)) if total else 1
        return AdminPaginatedOrganizationsData(
            items=[
                AdminOrganizationListItem(
                    id=org.id,
                    name=org.name,
                    email_domain=org.email_domain,
                    status=org.status,
                    employee_count=employee_count,
                    created_at=org.created_at,
                )
                for org, employee_count in rows
            ],
            page=safe_page,
            limit=safe_limit,
            total=total,
            total_pages=total_pages,
        )

    async def get_user_registration_stats(
        self,
        *,
        granularity: str = "month",
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> RegistrationStatsData:
        return await self._registration_stats(
            entity="users",
            granularity=granularity,
            from_date=from_date,
            to_date=to_date,
        )

    async def get_organization_registration_stats(
        self,
        *,
        granularity: str = "month",
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> RegistrationStatsData:
        return await self._registration_stats(
            entity="organizations",
            granularity=granularity,
            from_date=from_date,
            to_date=to_date,
        )

    async def _registration_stats(
        self,
        *,
        entity: str,
        granularity: str,
        from_date: date | None,
        to_date: date | None,
    ) -> RegistrationStatsData:
        if granularity == "custom" and from_date and to_date:
            range_start, range_end = from_date, to_date
            chart_granularity = "day"
        else:
            safe_granularity = granularity if granularity in {"month", "week"} else "month"
            range_start, range_end = default_stats_range(safe_granularity)
            chart_granularity = safe_granularity

        repo = self._users if entity == "users" else self._orgs
        rows = await repo.registration_counts_by_period(
            granularity=chart_granularity,
            from_date=range_start,
            to_date=range_end,
        )

        previous_total = 0
        if granularity == "custom" and from_date and to_date:
            span_days = (to_date - from_date).days + 1
            prev_end = from_date - timedelta(days=1)
            prev_start = prev_end - timedelta(days=span_days - 1)
            previous_total = await repo.count_created_in_range(
                from_date=prev_start,
                to_date=prev_end,
            )
            stats_granularity = "custom"
        else:
            stats_granularity = chart_granularity

        return build_registration_stats_with_previous(
            rows,
            previous_total,
            granularity=stats_granularity,
            from_date=from_date,
            to_date=to_date,
        )

    async def deactivate_user(
        self,
        user_id: uuid.UUID,
        *,
        admin_id: uuid.UUID,
    ) -> AdminUserDeleteData:
        user = await self._users.get_by_id(user_id)
        if user is None:
            raise AppError(
                message="Pengguna tidak dijumpai.",
                code="NOT_FOUND",
                status_code=404,
            )
        if not user.is_active:
            return AdminUserDeleteData(id=user.id, is_active=False)

        updated = await self._users.set_active(user_id, is_active=False)
        if updated is None:
            raise AppError(
                message="Pengguna tidak dijumpai.",
                code="NOT_FOUND",
                status_code=404,
            )

        await AuditService(self._db).log(
            action="admin.user.deactivated",
            user_id=admin_id,
            resource="user",
            resource_id=user_id,
            metadata={"email": user.email},
        )
        return AdminUserDeleteData(id=updated.id, is_active=updated.is_active)

    async def suspend_organization(
        self,
        org_id: uuid.UUID,
        *,
        admin_id: uuid.UUID,
    ) -> AdminOrganizationDeleteData:
        org = await self._orgs.get_by_id(org_id)
        if org is None:
            raise AppError(
                message="Organisasi tidak dijumpai.",
                code="NOT_FOUND",
                status_code=404,
            )
        if org.status == "suspended":
            return AdminOrganizationDeleteData(id=org.id, status=org.status)

        updated = await self._orgs.set_status(org_id, status="suspended")
        if updated is None:
            raise AppError(
                message="Organisasi tidak dijumpai.",
                code="NOT_FOUND",
                status_code=404,
            )

        await AuditService(self._db).log(
            action="admin.organization.suspended",
            user_id=admin_id,
            org_id=org_id,
            resource="organisation",
            resource_id=org_id,
            metadata={"name": org.name},
        )
        return AdminOrganizationDeleteData(id=updated.id, status=updated.status)
