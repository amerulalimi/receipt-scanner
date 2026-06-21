import uuid
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.repositories.claim_summary import ClaimSummaryRepository
from app.repositories.relief_limit import ReliefLimitRepository
from app.schemas.receipt import ReliefStatusInfo

WARNING_THRESHOLD = Decimal("0.90")
NON_CLAIMABLE_CATEGORIES = frozenset({"tidak_layak", "semak_manual"})


@dataclass(frozen=True)
class ReliefCheckResult:
    relief_status: ReliefStatusInfo
    would_exceed: bool


class ClaimLimitService:
    def __init__(self, db: AsyncSession) -> None:
        self._claims = ClaimSummaryRepository(db)
        self._limits = ReliefLimitRepository(db)

    async def get_effective_claimed(
        self,
        *,
        user_id: uuid.UUID,
        tax_year: int,
        category: str,
        exclude_receipt_id: uuid.UUID | None = None,
        subtract_approved: Decimal = Decimal("0"),
    ) -> Decimal:
        approved = await self._claims.get_approved_total(
            user_id=user_id,
            tax_year=tax_year,
            category=category,
        )
        approved = max(Decimal("0"), approved - subtract_approved)
        pending = await self._claims.sum_pending_claimed(
            user_id=user_id,
            tax_year=tax_year,
            category=category,
            exclude_receipt_id=exclude_receipt_id,
        )
        return approved + pending

    async def check_claim(
        self,
        *,
        user_id: uuid.UUID,
        tax_year: int,
        category: str,
        new_claimed_amount: Decimal,
        exclude_receipt_id: uuid.UUID | None = None,
        subtract_approved: Decimal = Decimal("0"),
        raise_on_exceed: bool = True,
    ) -> ReliefCheckResult:
        if category in NON_CLAIMABLE_CATEGORIES:
            relief_status = ReliefStatusInfo(
                category=category,
                be_seksyen=None,
                limit_amount=Decimal("0"),
                total_claimed=Decimal("0"),
                remaining=Decimal("0"),
                percentage=0.0,
                status="ok",
            )
            return ReliefCheckResult(relief_status=relief_status, would_exceed=False)

        relief_limit = await self._limits.get_active(category=category)
        if relief_limit is None:
            raise AppError(
                message=f"Had pelepasan untuk kategori '{category}' tidak dijumpai.",
                code="NOT_FOUND",
                status_code=404,
            )

        current_claimed = await self.get_effective_claimed(
            user_id=user_id,
            tax_year=tax_year,
            category=category,
            exclude_receipt_id=exclude_receipt_id,
            subtract_approved=subtract_approved,
        )
        projected_total = current_claimed + new_claimed_amount
        limit_amount = relief_limit.limit_amount
        remaining = max(Decimal("0"), limit_amount - projected_total)
        percentage = float(
            (projected_total / limit_amount * 100).quantize(Decimal("0.1"))
            if limit_amount > 0
            else Decimal("0"),
        )

        if projected_total > limit_amount:
            status: str = "full"
            would_exceed = True
        elif projected_total >= limit_amount * WARNING_THRESHOLD:
            status = "warning"
            would_exceed = False
        else:
            status = "ok"
            would_exceed = False

        relief_status = ReliefStatusInfo(
            category=category,
            be_seksyen=relief_limit.be_seksyen,
            limit_amount=limit_amount,
            total_claimed=projected_total,
            remaining=remaining,
            percentage=percentage,
            status=status,  # type: ignore[arg-type]
        )

        if would_exceed and raise_on_exceed:
            raise AppError(
                message=(
                    f"Had pelepasan {category} telah melebihi. "
                    f"Baki: RM{max(Decimal('0'), limit_amount - current_claimed):.2f}, "
                    f"cuba tuntut: RM{new_claimed_amount:.2f}."
                ),
                code="LIMIT_EXCEEDED",
                status_code=409,
            )

        return ReliefCheckResult(relief_status=relief_status, would_exceed=would_exceed)

    async def get_be_seksyen(self, *, category: str) -> str | None:
        relief_limit = await self._limits.get_active(category=category)
        if relief_limit is None:
            return None
        return relief_limit.be_seksyen
