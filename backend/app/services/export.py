from __future__ import annotations

import csv
import io
import uuid
import zipfile
from datetime import date
from decimal import Decimal

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.models.receipt import Receipt
from app.models.user import User
from app.repositories.receipt import ReceiptRepository
from app.services.storage import get_receipt_storage

PAYROLL_TEMPLATES = frozenset({"generic", "sql_payroll", "kakitangan"})


class ExportService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._receipts = ReceiptRepository(db)

    async def build_receipts_zip(
        self,
        user: User,
        *,
        tax_year: int,
    ) -> tuple[bytes, str]:
        items = await self._list_approved_for_user(user.id, tax_year)
        if not items:
            raise AppError(
                message="Tiada resit diluluskan untuk dieksport.",
                code="NOT_FOUND",
                status_code=404,
            )

        storage = get_receipt_storage()
        buffer = io.BytesIO()
        manifest_rows: list[dict[str, str]] = []

        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
            for receipt in items:
                content = storage.read_receipt_file(receipt.image_key)
                if content is None:
                    continue
                ext = receipt.file_type or "jpg"
                filename = receipt.file_name or f"{receipt.id}.{ext}"
                archive.writestr(f"receipts/{filename}", content)
                manifest_rows.append(
                    {
                        "receipt_id": str(receipt.id),
                        "merchant": receipt.merchant_name or "",
                        "receipt_date": str(receipt.receipt_date or ""),
                        "category": receipt.category or "",
                        "claimed_amount": str(receipt.claimed_amount or "0"),
                        "status": receipt.status,
                    },
                )

            manifest_csv = self._rows_to_csv(manifest_rows)
            archive.writestr("manifest.csv", manifest_csv)

        filename = f"resit-{tax_year}-{user.id.hex[:8]}.zip"
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

        filename = f"payroll-claims-{tax_year}-{template}.csv"
        return content, filename

    async def _list_approved_for_user(
        self,
        user_id: uuid.UUID,
        tax_year: int,
    ) -> list[Receipt]:
        result = await self._db.execute(
            select(Receipt)
            .where(
                Receipt.user_id == user_id,
                Receipt.tax_year == tax_year,
                Receipt.status == "approved",
                Receipt.deleted_at.is_(None),
            )
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
        if not rows:
            return ""
        columns = fieldnames or list(rows[0].keys())
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
        return output.getvalue()
