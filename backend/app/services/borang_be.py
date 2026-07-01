from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import UserInSession
from app.models.receipt import Receipt
from app.models.user import User
from app.repositories.claim_summary import ClaimSummaryRepository
from app.repositories.relief_limit import ReliefLimitRepository
from app.schemas.claims import (
    ReadyToFileChecklistItem,
    ReadyToFileData,
    ReadyToFileField,
    ReadyToFileFilingItem,
)


BORANG_BE_FIELDS: tuple[dict[str, str | int], ...] = (
    {
        "step": 1,
        "category": "perubatan",
        "be_seksyen": "S.46(1)(b)",
        "lhdn_section": "Pelepasan Individu",
        "lhdn_field_my": "Perbelanjaan perubatan, pergigian dan pemeriksaan kesihatan",
        "lhdn_field_en": "Medical, dental and health examination expenses",
    },
    {
        "step": 2,
        "category": "pendidikan",
        "be_seksyen": "S.46(1)(f)",
        "lhdn_section": "Pelepasan Individu",
        "lhdn_field_my": "Pendidikan diri (kursus yang diluluskan)",
        "lhdn_field_en": "Self-education (approved courses)",
    },
    {
        "step": 3,
        "category": "sspn",
        "be_seksyen": "S.46(1)(l)",
        "lhdn_section": "Pelepasan Individu",
        "lhdn_field_my": "Caruman SSPN (Skim Simpanan Pendidikan Nasional)",
        "lhdn_field_en": "SSPN net contributions",
    },
    {
        "step": 4,
        "category": "gaya_hidup",
        "be_seksyen": "S.46(1)(k)",
        "lhdn_section": "Pelepasan Individu",
        "lhdn_field_my": "Gaya hidup (peralatan sukan, alat bacaan, internet, dll.)",
        "lhdn_field_en": "Lifestyle (sports equipment, reading materials, internet, etc.)",
    },
    {
        "step": 5,
        "category": "sukan",
        "be_seksyen": "S.46(1)(k)",
        "lhdn_section": "Pelepasan Individu",
        "lhdn_field_my": "Peralatan sukan (termasuk dalam had gaya hidup)",
        "lhdn_field_en": "Sports equipment (within lifestyle limit)",
    },
    {
        "step": 6,
        "category": "ev_charging",
        "be_seksyen": "S.46(1)(p)",
        "lhdn_section": "Pelepasan Individu",
        "lhdn_field_my": "Pembelian / sewaan EV charging facility",
        "lhdn_field_en": "EV charging facility purchase or rental",
    },
)

CHECKLIST_MY: tuple[str, ...] = (
    "Log masuk ke MyTax (https://mytax.hasil.gov.my) dengan ID pengguna anda.",
    "Pilih Borang BE untuk tahun taksiran {year}.",
    "Navigasi ke bahagian Pelepasan / Reliefs dalam borang e-Filing.",
    "Isi setiap medan pelepasan di bawah mengikut jumlah yang ditunjukkan.",
    "Sediakan resit asal/digital sebagai bukti sokongan (simpanan 7 tahun).",
    "Semak semula jumlah sebelum hantar — Resit.my tidak menghantar borang ke LHDN.",
)

CHECKLIST_EN: tuple[str, ...] = (
    "Log in to MyTax (https://mytax.hasil.gov.my) with your credentials.",
    "Select Borang BE for assessment year {year}.",
    "Navigate to the Reliefs section in the e-Filing form.",
    "Fill each relief field below using the amounts shown.",
    "Keep original/digital receipts as supporting evidence (7-year retention).",
    "Review totals before submitting — Resit.my does not submit to LHDN.",
)


class BorangBeService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._claims = ClaimSummaryRepository(db)
        self._limits = ReliefLimitRepository(db)

    async def get_ready_to_file(
        self,
        user: User,
        session: UserInSession | None = None,
        *,
        tax_year: int | None = None,
    ) -> ReadyToFileData:
        year = tax_year or user.tax_year
        active_context = session.active_context if session is not None else "individual"
        active_org_id = (
            session.org_id if session is not None and session.active_context == "corporate" else None
        )
        summaries = await self._claims.list_for_user(
            user_id=user.id,
            tax_year=year,
            context_type=active_context,
            org_id=active_org_id,
        )
        summary_by_category = {item.category: item for item in summaries}
        active_limits = await self._limits.list_active()
        active_slugs = {item.category for item in active_limits}

        fields: list[ReadyToFileField] = []
        total_claimed = Decimal("0")

        for field_def in BORANG_BE_FIELDS:
            category = str(field_def["category"])
            if category not in active_slugs:
                continue

            summary = summary_by_category.get(category)
            amount = summary.total_claimed if summary else Decimal("0")
            receipt_count = summary.receipt_count if summary else 0

            if amount <= 0:
                continue

            limit_row = next(
                (item for item in active_limits if item.category == category),
                None,
            )
            be_seksyen = (
                limit_row.be_seksyen if limit_row and limit_row.be_seksyen else str(field_def["be_seksyen"])
            )

            fields.append(
                ReadyToFileField(
                    step=int(field_def["step"]),
                    category=category,
                    be_seksyen=be_seksyen,
                    lhdn_section=str(field_def["lhdn_section"]),
                    lhdn_field_my=str(field_def["lhdn_field_my"]),
                    lhdn_field_en=str(field_def["lhdn_field_en"]),
                    amount=amount,
                    receipt_count=receipt_count,
                ),
            )
            total_claimed += amount

        pending_review_count = await self._count_pending_receipts(
            user_id=user.id,
            org_id=active_org_id,
            tax_year=year,
        )

        tax_bracket = user.tax_bracket or Decimal("0")
        estimated_savings = (
            total_claimed * tax_bracket / Decimal("100")
        ).quantize(Decimal("0.01"))

        checklist = [
            ReadyToFileChecklistItem(
                order=index + 1,
                text_my=item.format(year=year),
                text_en=CHECKLIST_EN[index].format(year=year),
            )
            for index, item in enumerate(CHECKLIST_MY)
        ]

        filing_checklist = await self._build_filing_checklist(
            user_id=user.id,
            org_id=active_org_id,
            context_type=active_context,
            tax_year=year,
            active_limits=active_limits,
            summary_by_category=summary_by_category,
        )

        return ReadyToFileData(
            tax_year=year,
            total_claimed=total_claimed,
            total_relief=total_claimed,
            estimated_savings=estimated_savings,
            tax_bracket=float(tax_bracket),
            pending_review_count=pending_review_count,
            fields=fields,
            filing_checklist=filing_checklist,
            checklist=checklist,
        )

    async def _build_filing_checklist(
        self,
        *,
        user_id: uuid.UUID,
        org_id: uuid.UUID | None,
        context_type: str,
        tax_year: int,
        active_limits,
        summary_by_category: dict,
    ) -> list[ReadyToFileFilingItem]:
        field_by_category = {str(item["category"]): item for item in BORANG_BE_FIELDS}
        pending_by_category = await self._count_pending_by_category(
            user_id=user_id,
            org_id=org_id,
            tax_year=tax_year,
        )

        items: list[ReadyToFileFilingItem] = []
        for limit in active_limits:
            category = limit.category
            field_def = field_by_category.get(category)
            summary = summary_by_category.get(category)
            amount = summary.total_claimed if summary else Decimal("0")
            receipt_count = summary.receipt_count if summary else 0
            pending_count = pending_by_category.get(category, 0)

            if amount > 0 and receipt_count > 0 and pending_count == 0:
                status = "ready"
            elif amount > 0 or pending_count > 0:
                status = "partial"
            else:
                status = "empty"

            description = (
                str(field_def["lhdn_field_my"])
                if field_def
                else (limit.description_my or category)
            )
            be_field = (
                str(field_def["lhdn_section"])
                if field_def
                else (limit.description_my or category)
            )
            be_seksyen = limit.be_seksyen or (
                str(field_def["be_seksyen"]) if field_def else ""
            )

            items.append(
                ReadyToFileFilingItem(
                    be_field=be_field,
                    be_seksyen=be_seksyen,
                    description=description,
                    amount_to_enter=amount,
                    receipt_count=receipt_count,
                    status=status,
                ),
            )
        return items

    async def _count_pending_by_category(
        self,
        *,
        user_id: uuid.UUID,
        org_id: uuid.UUID | None,
        tax_year: int,
    ) -> dict[str, int]:
        conditions = [
            Receipt.user_id == user_id,
            Receipt.tax_year == tax_year,
            Receipt.deleted_at.is_(None),
            Receipt.status.in_(("pending", "flagged")),
            Receipt.category.is_not(None),
        ]
        if org_id is None:
            conditions.append(Receipt.org_id.is_(None))
        else:
            conditions.append(Receipt.org_id == org_id)
        result = await self._db.execute(
            select(Receipt.category, func.count()).where(*conditions).group_by(Receipt.category),
        )
        return {category: int(count) for category, count in result.all() if category}

    async def _count_pending_receipts(
        self,
        *,
        user_id: uuid.UUID,
        org_id: uuid.UUID | None,
        tax_year: int,
    ) -> int:
        conditions = [
            Receipt.user_id == user_id,
            Receipt.tax_year == tax_year,
            Receipt.deleted_at.is_(None),
            Receipt.status.in_(("pending", "flagged")),
        ]
        if org_id is None:
            conditions.append(Receipt.org_id.is_(None))
        else:
            conditions.append(Receipt.org_id == org_id)
        result = await self._db.execute(
            select(func.count()).select_from(Receipt).where(*conditions),
        )
        return int(result.scalar_one())
