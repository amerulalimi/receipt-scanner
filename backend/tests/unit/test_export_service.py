import io
import uuid
import zipfile
from decimal import Decimal
from unittest.mock import patch

import pytest

from app.services.export import ExportService
from tests.conftest import seed_approved_receipt, seed_organisation, seed_relief_limits


@pytest.mark.asyncio
async def test_build_receipts_zip_structure(db_session, test_user):
    await seed_relief_limits(db_session)
    await seed_approved_receipt(
        db_session,
        user_id=test_user.id,
        category="perubatan",
        claimed_amount=Decimal("320.00"),
        merchant_name="Klinik ABC",
    )
    await seed_approved_receipt(
        db_session,
        user_id=test_user.id,
        category="gaya_hidup",
        claimed_amount=Decimal("150.00"),
        merchant_name="Bookstore",
    )

    fake_content = b"fake-image-bytes"
    with patch(
        "app.services.export.get_receipt_storage",
    ) as mock_storage_factory:
        mock_storage = mock_storage_factory.return_value
        mock_storage.read_receipt_file.return_value = fake_content

        service = ExportService(db_session)
        content, filename = await service.build_receipts_zip(
            test_user,
            tax_year=2025,
        )

    assert filename.startswith("ResitCukai_BE_2025_")
    assert filename.endswith(".zip")

    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        names = archive.namelist()
        assert any(name.startswith("Perubatan") or "Perubatan" in name for name in names)
        assert f"Ringkasan_Tuntutan_2025.txt" in names
        summary = archive.read(f"Ringkasan_Tuntutan_2025.txt").decode("utf-8")
        assert "Jumlah Keseluruhan" in summary
        assert "470.00" in summary
        assert "manifest.csv" not in names


@pytest.mark.asyncio
async def test_build_receipts_zip_not_found(db_session, test_user):
    await seed_relief_limits(db_session)
    service = ExportService(db_session)

    with pytest.raises(Exception) as exc_info:
        await service.build_receipts_zip(test_user, tax_year=2025)

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_build_org_payroll_csv(db_session):
    org, admin = await seed_organisation(db_session)
    await seed_relief_limits(db_session)
    from app.repositories.user import UserRepository

    user_repo = UserRepository(db_session)
    employee = await user_repo.create(
        email="csv@example.com",
        password_hash="hashed",
        full_name="CSV Emp",
        role="employee",
        org_id=org.id,
        account_type="corporate",
        org_employee_code="CSV01",
    )
    receipt = await seed_approved_receipt(
        db_session,
        user_id=employee.id,
        category="perubatan",
        claimed_amount=Decimal("200.00"),
    )
    receipt.org_id = org.id
    await db_session.commit()

    service = ExportService(db_session)
    content, filename = await service.build_org_payroll_csv(org.id, tax_year=2025)
    assert "CSV01" in content
    assert filename.startswith("Syarikat")
    assert "_payroll.csv" in filename
