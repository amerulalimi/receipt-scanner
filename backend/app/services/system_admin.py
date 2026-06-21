import uuid
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AppError
from app.core.secret_keys import CONFIG_DEFAULTS
from app.core.redis import get_redis
from app.models.audit_log import AuditLog
from app.repositories.relief_limit import ReliefLimitRepository
from app.schemas.system_admin import (
    ReliefCategoryItem,
    ReliefLimitCreateRequest,
    ReliefLimitItem,
    ReliefLimitUpdateRequest,
    SystemOverviewData,
)
from app.services.system_config import SystemConfigService


class SystemAdminService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._limits = ReliefLimitRepository(db)
        self._config = SystemConfigService(db)

    async def _get_int_config(self, key: str) -> int:
        raw = await self._config.get(key) or CONFIG_DEFAULTS.get(key, "0")
        try:
            return int(raw)
        except ValueError as exc:
            raise AppError(
                message=f"Konfigurasi '{key}' tidak sah.",
                code="VALIDATION_ERROR",
                status_code=422,
            ) from exc

    @staticmethod
    def _to_item(item) -> ReliefLimitItem:
        return ReliefLimitItem(
            id=item.id,
            category=item.category,
            be_seksyen=item.be_seksyen,
            limit_amount=float(item.limit_amount),
            description_my=item.description_my,
            sort_order=item.sort_order,
            is_active=item.is_active,
            updated_at=item.updated_at,
        )

    async def list_relief_limits(self) -> list[ReliefLimitItem]:
        items = await self._limits.list_all()
        return [self._to_item(item) for item in items]

    async def list_relief_categories(self) -> list[ReliefCategoryItem]:
        items = await self._limits.list_active()
        return [
            ReliefCategoryItem(
                category=item.category,
                label=item.description_my or item.category,
                be_seksyen=item.be_seksyen,
            )
            for item in items
        ]

    async def create_relief_limit(
        self,
        payload: ReliefLimitCreateRequest,
        *,
        updated_by: uuid.UUID,
    ) -> ReliefLimitItem:
        if await self._limits.category_exists(payload.category):
            raise AppError(
                message=f"Kategori '{payload.category}' sudah wujud.",
                code="VALIDATION_ERROR",
                status_code=422,
            )

        created = await self._limits.create(
            category=payload.category,
            limit_amount=payload.limit_amount,
            be_seksyen=payload.be_seksyen,
            description_my=payload.description_my,
            sort_order=payload.sort_order,
            updated_by=updated_by,
        )
        return self._to_item(created)

    async def update_relief_limit(
        self,
        category: str,
        payload: ReliefLimitUpdateRequest,
        *,
        updated_by: uuid.UUID,
    ) -> ReliefLimitItem:
        item = await self._limits.get_by_category(category)
        if item is None:
            raise AppError(
                message="Had pelepasan tidak dijumpai.",
                code="NOT_FOUND",
                status_code=404,
            )

        if payload.is_active is False and item.is_active:
            receipt_count = await self._limits.count_receipts_for_category(category)
            if receipt_count > 0:
                raise AppError(
                    message=(
                        f"Kategori '{category}' masih digunakan oleh "
                        f"{receipt_count} resit. Nyahaktif tidak dibenarkan."
                    ),
                    code="VALIDATION_ERROR",
                    status_code=422,
                )

        updated = await self._limits.update(
            item,
            limit_amount=payload.limit_amount,
            be_seksyen=payload.be_seksyen,
            description_my=payload.description_my,
            is_active=payload.is_active,
            sort_order=payload.sort_order,
            updated_by=updated_by,
        )
        return self._to_item(updated)

    async def deactivate_relief_limit(
        self,
        category: str,
        *,
        updated_by: uuid.UUID,
    ) -> ReliefLimitItem:
        return await self.update_relief_limit(
            category,
            ReliefLimitUpdateRequest(is_active=False),
            updated_by=updated_by,
        )

    async def get_overview(self) -> SystemOverviewData:
        count_result = await self._db.execute(
            select(func.count()).select_from(AuditLog),
        )
        total_audit_logs = int(count_result.scalar_one())

        redis = get_redis()
        queue_depth = await redis.llen(settings.receipt_queue_key)

        return SystemOverviewData(
            auth_rate_limit_max=await self._get_int_config("auth_rate_limit_max"),
            auth_rate_limit_window_seconds=await self._get_int_config(
                "auth_rate_limit_window_seconds",
            ),
            audit_retention_days=await self._get_int_config("audit_retention_days"),
            receipt_retention_days=await self._get_int_config("receipt_retention_days"),
            receipt_queue_depth=int(queue_depth),
            total_audit_logs=total_audit_logs,
        )
