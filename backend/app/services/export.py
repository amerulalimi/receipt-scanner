from __future__ import annotations

import io
import re
import uuid
import zipfile
from decimal import Decimal

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import UserInSession
from app.core.exceptions import AppError
from app.models.receipt import Receipt
from app.models.user import User
from app.repositories.claim_summary import ClaimSummaryRepository
from app.repositories.organisation import OrganisationRepository
from app.repositories.receipt import ReceiptRepository
from app.repositories.relief_limit import ReliefLimitRepository
from app.services.storage import get_receipt_storage

PAYROLL_TEMPLATES = frozenset({"generic", "sql_payroll", "kakitangan"})


def _sanitize_folder_name(label: str) -> str:
    cleaned = re.sub(r"[^\w\s-]", "", label, flags=re.UNICODE)
    cleaned = re.sub(r"\s+", "_", cleaned.strip())
    return cleaned or "Lain_lain"


def _sanitize_user_name(name: str | None) -> str:
    if not name or not name.strip():
        return "Pengguna"
    cleaned = re.sub(r"[^\w\s-]", "", name.strip(), flags=re.UNICODE)
    cleaned = re.sub(r"\s+", "_", cleaned)
    return cleaned[:40] or "Pengguna"


def _sanitize_org_name(name: str | None) -> str:
    if not name or not name.strip():
        return "ABC"
    cleaned = re.sub(r"[^\w\s-]", "", name.strip(), flags=re.UNICODE)
    cleaned = re.sub(r"\s+", "", cleaned)
    return cleaned[:40] or "ABC"


def _receipt_archive_name(receipt: Receipt) -> str:
    merchant = receipt.merchant_name or "Resit"
    merchant = re.sub(r"[^\w\s-]", "", merchant, flags=re.UNICODE)
    merchant = re.sub(r"\s+", "_", merchant.strip()) or "Resit"
    date_part = str(receipt.receipt_date or receipt.created_at.date())
    ext = receipt.file_type or "jpg"
    return f"{merchant}_{date_part}.{ext}"


class ExportService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._receipts = ReceiptRepository(db)
        self._claims = ClaimSummaryRepository(db)
        self._limits = ReliefLimitRepository(db)

    async def build_receipts_zip(
        self,
        user: User,
        session: UserInSession,
        *,
        tax_year: int,
    ) -> tuple[bytes, str]:
        items = await self._list_approved_for_user(
            user.id,
            tax_year,
            session.org_id if session.active_context == "corporate" else None,
        )
        if not items:
            raise AppError(
                message="Tiada resit diluluskan untuk dieksport.",
                code="NOT_FOUND",
                status_code=404,
            )

        active_limits = await self._limits.list_active()
        folder_by_category = {
            limit.category: _sanitize_folder_name(
                limit.description_my or limit.category.replace("_", " ").title(),
            )
            for limit in active_limits
        }

        storage = get_receipt_storage()
        buffer = io.BytesIO()
        category_totals: dict[str, Decimal] = {}

        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
            for receipt in items:
                content = storage.read_receipt_file(receipt.image_key)
                if content is None:
                    continue

                category = receipt.category or "lain"
                folder = folder_by_category.get(category, _sanitize_folder_name(category))
                filename = _receipt_archive_name(receipt)
                archive.writestr(f"{folder}/{filename}", content)

                amount = receipt.claimed_amount or Decimal("0")
                category_totals[category] = category_totals.get(category, Decimal("0")) + amount

            summary_lines = [
                f"Ringkasan Tuntutan Cukai Pendapatan — Tahun {tax_year}",
                f"Nama: {user.full_name or user.email}",
                "",
            ]
            grand_total = Decimal("0")
            for limit in active_limits:
                total = category_totals.get(limit.category, Decimal("0"))
                if total <= 0:
                    continue
                label = limit.description_my or limit.category
                summary_lines.append(f"{label}: RM {total:.2f}")
                grand_total += total

            summary_lines.extend(
                [
                    "",
                    f"Jumlah Keseluruhan: RM {grand_total:.2f}",
                    "",
                    "Dijana oleh Resit.my — simpan resit asal/digital selama 7 tahun.",
                ],
            )
            archive.writestr(
                f"Ringkasan_Tuntutan_{tax_year}.txt",
                "\n".join(summary_lines),
            )

        sanitized_name = _sanitize_user_name(user.full_name)
        filename = f"ResitCukai_BE_{tax_year}_{sanitized_name}.zip"
        return buffer.getvalue(), filename

    async def build_org_payroll_csv(
        self,
        org_id: uuid.UUID,
        *,
        tax_year: int,
        template: str = "generic",
    ) -> tuple[str, str]:
        if template not in PAYROLL_TEMPLATES:
            raise AppError(
                message="Template eksport tidak sah.",
                code="VALIDATION_ERROR",
                status_code=422,
            )

        rows = await self._list_approved_for_org(org_id, tax_year)
        if not rows:
            raise AppError(
                message="Tiada tuntutan diluluskan untuk dieksport.",
                code="NOT_FOUND",
                status_code=404,
            )

        import csv

        csv_rows: list[dict[str, str]] = []
        for receipt, employee, reviewer in rows:
            csv_rows.append(
                {
                    "employee_id": employee.org_employee_code or str(employee.id),
                    "employee_name": employee.full_name or "",
                    "employee_email": employee.email,
                    "category": receipt.category or "",
                    "amount": str(receipt.claimed_amount or "0"),
                    "approval_date": str(
                        receipt.reviewed_at.date() if receipt.reviewed_at else "",
                    ),
                    "approver": reviewer.full_name or reviewer.email if reviewer else "",
                    "merchant": receipt.merchant_name or "",
                    "receipt_date": str(receipt.receipt_date or ""),
                    "tax_year": str(tax_year),
                },
            )

        if template == "sql_payroll":
            fieldnames = [
                "employee_id",
                "employee_name",
                "claim_type",
                "amount",
                "approval_date",
            ]
            mapped = [
                {
                    "employee_id": row["employee_id"],
                    "employee_name": row["employee_name"],
                    "claim_type": row["category"],
                    "amount": row["amount"],
                    "approval_date": row["approval_date"],
                }
                for row in csv_rows
            ]
            content = self._rows_to_csv(mapped, fieldnames=fieldnames)
        elif template == "kakitangan":
            fieldnames = [
                "No_Pekerja",
                "Nama",
                "Kategori",
                "Amaun",
                "Tarikh_Lulus",
            ]
            mapped = [
                {
                    "No_Pekerja": row["employee_id"],
                    "Nama": row["employee_name"],
                    "Kategori": row["category"],
                    "Amaun": row["amount"],
                    "Tarikh_Lulus": row["approval_date"],
                }
                for row in csv_rows
            ]
            content = self._rows_to_csv(mapped, fieldnames=fieldnames)
        else:
            content = self._rows_to_csv(csv_rows)

        org = await OrganisationRepository(self._db).get_by_id(org_id)
        org_label = _sanitize_org_name(org.name if org else None)
        filename = f"Syarikat{org_label}_BE_{tax_year}_payroll.csv"
        return content, filename

    async def _list_approved_for_user(
        self,
        user_id: uuid.UUID,
        tax_year: int,
        org_id: uuid.UUID | None,
    ) -> list[Receipt]:
        conditions = [
            Receipt.user_id == user_id,
            Receipt.tax_year == tax_year,
            Receipt.status == "approved",
            Receipt.deleted_at.is_(None),
        ]
        if org_id is None:
            conditions.append(Receipt.org_id.is_(None))
        else:
            conditions.append(Receipt.org_id == org_id)
        result = await self._db.execute(
            select(Receipt)
            .where(*conditions)
            .order_by(desc(Receipt.receipt_date), desc(Receipt.created_at)),
        )
        return list(result.scalars().all())

    async def _list_approved_for_org(
        self,
        org_id: uuid.UUID,
        tax_year: int,
    ) -> list[tuple[Receipt, User, User | None]]:
        from sqlalchemy.orm import aliased

        Reviewer = aliased(User)
        result = await self._db.execute(
            select(Receipt, User, Reviewer)
            .join(User, Receipt.user_id == User.id)
            .outerjoin(Reviewer, Receipt.reviewed_by == Reviewer.id)
            .where(
                Receipt.org_id == org_id,
                Receipt.tax_year == tax_year,
                Receipt.status == "approved",
                Receipt.deleted_at.is_(None),
            )
            .order_by(desc(Receipt.reviewed_at), desc(Receipt.created_at)),
        )
        return list(result.all())

    @staticmethod
    def _rows_to_csv(
        rows: list[dict[str, str]],
        *,
        fieldnames: list[str] | None = None,
    ) -> str:
        import csv

        if not rows:
            return ""
        columns = fieldnames or list(rows[0].keys())
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
        return output.getvalue()
