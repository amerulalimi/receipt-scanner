import asyncio
import os
import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, date, datetime
from decimal import Decimal
from io import BytesIO
from unittest.mock import AsyncMock, patch

import fakeredis.aioredis
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from PIL import Image
from redis.asyncio import Redis
from sqlalchemy import ARRAY, JSON
from sqlalchemy.dialects.postgresql import INET, JSONB
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["REDIS_URL"] = "redis://localhost:6379/15"
os.environ["SESSION_SECRET"] = "changeme-min-32-chars-for-dev-only"
os.environ["FRONTEND_URL"] = "http://localhost:3000"
os.environ["CORS_ORIGINS"] = "http://localhost:3000"
os.environ["ENVIRONMENT"] = "test"
os.environ["DEBUG"] = "true"
os.environ["MASTER_ENCRYPTION_KEY"] = "CesYEr9a5zRu9D1Ff6V7JPTI4pf3Mpr1OLy-B6ddsVI="
os.environ["RUN_IN_PROCESS_WORKER"] = "false"

from app.core.config import get_settings
from app.core.database import Base
from app.core import deps
from app.models.claim_summary import ClaimSummary
from app.models.invite_token import InviteToken
from app.models.notification_preference import NotificationPreference
from app.models.org_policy import OrgPolicy
from app.models.organisation import Organisation
from app.models.platform_admin import PlatformAdmin
from app.models.receipt import Receipt
from app.models.receipt_flag import ReceiptFlag
from app.models.receipt_line_item import ReceiptLineItem
from app.models.relief_limit import ReliefLimit
from app.models.spouse_link import SpouseLink
from app.models.system_config import SystemConfig
from app.models.system_setting import SystemSetting
from app.models.upload_session import UploadSession
from app.models.user import User
from app.models.user_notification import UserNotification
from app.models.audit_log import AuditLog
from app.schemas.vision_llm import VisionClassificationResult

get_settings.cache_clear()


def _sqlite_compat_metadata():
    for table in Base.metadata.tables.values():
        for column in table.columns:
            if isinstance(column.type, (JSONB, ARRAY)):
                column.type = JSON()
                default = column.server_default
                if default is not None and "ARRAY[" in str(getattr(default, "arg", "")):
                    column.server_default = None
            if isinstance(column.type, INET):
                from sqlalchemy import String

                column.type = String(45)
        for index in list(table.indexes):
            if getattr(index, "dialect_options", {}).get("postgresql"):
                index.dialect_options.pop("postgresql", None)
    return [
        Organisation.__table__,
        OrgPolicy.__table__,
        InviteToken.__table__,
        User.__table__,
        ReliefLimit.__table__,
        Receipt.__table__,
        ReceiptFlag.__table__,
        ReceiptLineItem.__table__,
        ClaimSummary.__table__,
        UploadSession.__table__,
        SpouseLink.__table__,
        NotificationPreference.__table__,
        UserNotification.__table__,
        SystemConfig.__table__,
        SystemSetting.__table__,
        AuditLog.__table__,
        PlatformAdmin.__table__,
    ]


def make_test_jpeg() -> bytes:
    image = Image.new("RGB", (8, 8), color="white")
    buffer = BytesIO()
    image.save(buffer, format="JPEG")
    return buffer.getvalue()


MOCK_VISION_RESULT = VisionClassificationResult(
    merchant_name="Klinik Test",
    receipt_date=date(2025, 6, 14),
    total_amount=Decimal("320.0"),
    kategori="perubatan",
    seksyen="S.46(1)(b)",
    jumlah_claim=Decimal("320.0"),
    confidence=0.97,
    nota="Perubatan",
)

MOCK_AI_SUCCESS = {
    "scan_status": "success",
    "merchant_name": "Klinik Test",
    "receipt_date": "2025-06-14",
    "total_amount": 320.0,
    "ocr_confidence": 0.94,
    "category": "perubatan",
    "be_seksyen": "S.46(1)(b)",
    "claimed_amount": 320.0,
    "excluded_amount": 0,
    "ai_confidence": 0.97,
    "ai_nota": "Perubatan",
    "is_mixed": False,
    "line_items": [],
    "flags": [],
    "ocr_raw": {},
}


RELIEF_SEED = [
    ("perubatan", "S.46(1)(b)", "8000.00", "Medical & Dental", "Perubatan & Pergigian", 1),
    ("gaya_hidup", "S.46(1)(k)", "3000.00", "Lifestyle", "Gaya Hidup", 2),
    ("sukan", "S.46(1)(k)", "500.00", "Sports Equipment", "Peralatan Sukan", 3),
    ("pendidikan", "S.46(1)(f)", "7000.00", "Self Education", "Pendidikan Diri", 4),
    ("sspn", "S.46(1)(l)", "8000.00", "SSPN", "SSPN", 5),
    ("ev_charging", "S.46(1)(p)", "2500.00", "EV Charging", "Pembelian / Pasang EV Charging", 6),
    ("tidak_layak", None, "0.00", "Not Eligible", "Tidak Layak", 99),
]

_test_engine = create_async_engine(
    "sqlite+aiosqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False,
)
TestSessionLocal = async_sessionmaker(
    bind=_test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@pytest_asyncio.fixture
async def fake_redis() -> AsyncGenerator[Redis, None]:
    redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    yield redis
    await redis.flushall()
    await redis.aclose()


@pytest_asyncio.fixture(autouse=True)
async def clear_redis() -> AsyncGenerator[None, None]:
    redis: Redis | None = None
    try:
        redis = Redis.from_url(os.environ["REDIS_URL"], decode_responses=True)
        await redis.flushdb()
    except Exception:
        pass
    finally:
        if redis is not None:
            await redis.aclose()
    yield


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    tables = _sqlite_compat_metadata()
    async with _test_engine.begin() as conn:
        await conn.run_sync(lambda sync_conn: Base.metadata.create_all(sync_conn, tables=tables))

    async with TestSessionLocal() as session:
        yield session

    async with _test_engine.begin() as conn:
        await conn.run_sync(lambda sync_conn: Base.metadata.drop_all(sync_conn, tables=tables))


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    user = User(
        id=uuid.uuid4(),
        email="qr-test@example.com",
        password_hash="hashed",
        full_name="QR Tester",
        role="individual",
        account_type="individual",
        tax_year=2025,
        email_verified=True,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def auth_client(
    fake_redis: Redis,
) -> AsyncGenerator[AsyncClient, None]:
    async with _test_engine.begin() as conn:
        await conn.run_sync(
            lambda sync_conn: Base.metadata.create_all(
                sync_conn,
                tables=[User.__table__],
            ),
        )

    async def _redis_client() -> AsyncGenerator[Redis, None]:
        yield fake_redis

    with (
        patch("app.main.init_redis", new_callable=AsyncMock, return_value=fake_redis),
        patch("app.main.close_redis", new_callable=AsyncMock),
        patch("app.main.ws_events_subscriber_loop", new_callable=AsyncMock),
        patch("app.main.ensure_upload_root"),
        patch("app.main.run_migrations"),
        patch("app.main.run_startup_checks", new_callable=AsyncMock),
        patch("app.core.redis.get_redis", return_value=fake_redis),
        patch("app.services.auth.AuditService.log", new_callable=AsyncMock),
        patch("app.services.admin_auth.AuditService.log", new_callable=AsyncMock),
    ):
        from app.main import app
        from app.core import deps

        app.dependency_overrides[deps.get_db] = override_get_db
        app.dependency_overrides[deps.get_redis_client] = _redis_client

        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            yield client

        app.dependency_overrides.clear()

    async with _test_engine.begin() as conn:
        await conn.run_sync(
            lambda sync_conn: Base.metadata.drop_all(
                sync_conn,
                tables=[User.__table__],
            ),
        )


@pytest_asyncio.fixture
async def seeded_platform_admin(db_session: AsyncSession) -> PlatformAdmin:
    return await seed_platform_admin(db_session)


@pytest_asyncio.fixture
async def admin_auth_client(
    fake_redis: Redis,
    seeded_platform_admin: PlatformAdmin,
) -> AsyncGenerator[AsyncClient, None]:
    async with _test_engine.begin() as conn:
        await conn.run_sync(
            lambda sync_conn: Base.metadata.create_all(
                sync_conn,
                tables=[PlatformAdmin.__table__],
            ),
        )

    async def _redis_client() -> AsyncGenerator[Redis, None]:
        yield fake_redis

    with (
        patch("app.main.init_redis", new_callable=AsyncMock, return_value=fake_redis),
        patch("app.main.close_redis", new_callable=AsyncMock),
        patch("app.main.ws_events_subscriber_loop", new_callable=AsyncMock),
        patch("app.main.ensure_upload_root"),
        patch("app.main.run_migrations"),
        patch("app.main.run_startup_checks", new_callable=AsyncMock),
        patch("app.core.redis.get_redis", return_value=fake_redis),
        patch("app.services.admin_auth.AuditService.log", new_callable=AsyncMock),
    ):
        from app.main import app
        from app.core import deps

        app.dependency_overrides[deps.get_db] = override_get_db
        app.dependency_overrides[deps.get_redis_client] = _redis_client

        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            yield client

        app.dependency_overrides.clear()

    async with _test_engine.begin() as conn:
        await conn.run_sync(
            lambda sync_conn: Base.metadata.drop_all(
                sync_conn,
                tables=[PlatformAdmin.__table__],
            ),
        )


@pytest_asyncio.fixture
async def receipt_client(
    fake_redis: Redis,
) -> AsyncGenerator[AsyncClient, None]:
    tables = _sqlite_compat_metadata()
    async with _test_engine.begin() as conn:
        await conn.run_sync(lambda sync_conn: Base.metadata.create_all(sync_conn, tables=tables))

    async with TestSessionLocal() as session:
        now = datetime.now(UTC)
        for row in RELIEF_SEED:
            session.add(
                ReliefLimit(
                    id=uuid.uuid4(),
                    category=row[0],
                    be_seksyen=row[1],
                    limit_amount=Decimal(row[2]),
                    description_en=row[3],
                    description_my=row[4],
                    sort_order=row[5],
                    is_active=True,
                    updated_at=now,
                ),
            )
        await session.commit()

    async def _redis_client() -> AsyncGenerator[Redis, None]:
        yield fake_redis

    with (
        patch("app.main.init_redis", new_callable=AsyncMock, return_value=fake_redis),
        patch("app.main.close_redis", new_callable=AsyncMock),
        patch("app.main.ws_events_subscriber_loop", new_callable=AsyncMock),
        patch("app.main.receipt_worker_loop", new_callable=AsyncMock),
        patch("app.main.ensure_upload_root"),
        patch("app.main.run_migrations"),
        patch("app.main.run_startup_checks", new_callable=AsyncMock),
        patch("app.core.redis.get_redis", return_value=fake_redis),
        patch("app.services.job_queue.create_worker_redis", return_value=fake_redis),
        patch("app.services.job_queue.AsyncSessionLocal", TestSessionLocal),
        patch(
            "app.services.job_queue.process_receipt_job",
            side_effect=_mock_process_receipt_job,
        ),
        patch("app.services.auth.AuditService.log", new_callable=AsyncMock),
        patch("app.services.admin_auth.AuditService.log", new_callable=AsyncMock),
        patch(
            "app.services.receipt_processor.get_openrouter_credentials",
            new_callable=AsyncMock,
            return_value=("test-openrouter-key", "google/gemini-2.5-flash"),
        ),
        patch(
            "app.services.vision_llm.classify_receipt_async",
            new_callable=AsyncMock,
            return_value=MOCK_VISION_RESULT,
        ),
        patch(
            "app.services.receipt_pipeline.classify_receipt",
            new_callable=AsyncMock,
            return_value=MOCK_AI_SUCCESS,
        ),
        patch(
            "app.services.vision_llm.classify_receipt",
            new_callable=AsyncMock,
            return_value=MOCK_AI_SUCCESS,
        ),
    ):
        from app.main import app
        from app.core import deps

        app.dependency_overrides[deps.get_db] = override_get_db
        app.dependency_overrides[deps.get_redis_client] = _redis_client

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            client.fake_redis = fake_redis  # type: ignore[attr-defined]
            yield client

        app.dependency_overrides.clear()

    async with _test_engine.begin() as conn:
        await conn.run_sync(lambda sync_conn: Base.metadata.drop_all(sync_conn, tables=tables))


async def _mock_process_receipt_job(redis: Redis, job) -> None:
    from app.repositories.receipt import ReceiptRepository
    from app.services.job_queue import update_job_status

    await update_job_status(redis, job.job_id, "processing")
    async with TestSessionLocal() as db:
        repo = ReceiptRepository(db)
        receipt = await repo.get_by_id(job.receipt_id)
        if receipt is None:
            await update_job_status(redis, job.job_id, "failed")
            return
        receipt.scan_status = "success"
        receipt.merchant_name = MOCK_VISION_RESULT.merchant_name
        receipt.category = MOCK_VISION_RESULT.kategori
        receipt.total_amount = MOCK_VISION_RESULT.total_amount
        receipt.claimed_amount = MOCK_VISION_RESULT.jumlah_claim
        await db.commit()
        await update_job_status(redis, job.job_id, "completed")


async def register_and_login(client: AsyncClient, email: str = "receipts@example.com") -> None:
    payload = {
        "email": email,
        "password": "password123",
        "full_name": "Receipt Tester",
        "account_type": "individual",
    }
    await client.post("/api/v1/auth/register", json=payload)


async def seed_relief_limits(session: AsyncSession) -> None:
    now = datetime.now(UTC)
    for row in RELIEF_SEED:
        session.add(
            ReliefLimit(
                id=uuid.uuid4(),
                category=row[0],
                be_seksyen=row[1],
                limit_amount=Decimal(row[2]),
                description_en=row[3],
                description_my=row[4],
                sort_order=row[5],
                is_active=True,
                updated_at=now,
            ),
        )
    await session.commit()


async def seed_claim_summary(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
    tax_year: int,
    category: str,
    total_claimed: Decimal,
    receipt_count: int = 1,
) -> ClaimSummary:
    summary = ClaimSummary(
        id=uuid.uuid4(),
        user_id=user_id,
        tax_year=tax_year,
        category=category,
        total_claimed=total_claimed,
        receipt_count=receipt_count,
        last_updated=datetime.now(UTC),
    )
    session.add(summary)
    await session.commit()
    await session.refresh(summary)
    return summary


async def seed_approved_receipt(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
    tax_year: int = 2025,
    category: str = "perubatan",
    claimed_amount: Decimal = Decimal("500.00"),
    merchant_name: str = "Klinik Test",
) -> Receipt:
    receipt_id = uuid.uuid4()
    receipt = Receipt(
        id=receipt_id,
        user_id=user_id,
        tax_year=tax_year,
        image_key=f"test/{receipt_id}.jpg",
        image_hash=uuid.uuid4().hex,
        file_name="receipt.jpg",
        file_type="jpg",
        merchant_name=merchant_name,
        receipt_date=date(2025, 6, 14),
        total_amount=claimed_amount,
        claimed_amount=claimed_amount,
        category=category,
        status="approved",
        scan_status="success",
    )
    session.add(receipt)
    await session.commit()
    await session.refresh(receipt)
    return receipt


async def register_corporate_user(
    client: AsyncClient,
    email: str = "corp@example.com",
    *,
    account_type: str = "corporate",
) -> None:
    payload = {
        "email": email,
        "password": "password123",
        "full_name": "Corp User",
        "account_type": account_type,
    }
    await client.post("/api/v1/auth/register", json=payload)


async def register_corporate_and_login(
    client: AsyncClient,
    email: str = "corp@example.com",
) -> None:
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "password123",
            "full_name": "Corp User",
            "account_type": "corporate",
        },
    )
    assert response.status_code == 201, response.text


async def setup_org_via_api(
    client: AsyncClient,
    *,
    email: str = "founder@example.com",
    org_name: str = "Acme Sdn Bhd",
    ssm_number: str = "123456-A",
    email_domain: str = "example.com",
) -> dict:
    await register_corporate_and_login(client, email=email)
    response = await client.post(
        "/api/v1/org/register",
        json={
            "name": org_name,
            "ssm_number": ssm_number,
            "email_domain": email_domain,
        },
    )
    assert response.status_code == 201
    return response.json()["data"]


async def seed_organisation(
    session: AsyncSession,
    *,
    superadmin_email: str = "admin@example.com",
    org_name: str = "Acme Sdn Bhd",
    email_domain: str = "example.com",
    ssm_number: str = "123456-A",
) -> tuple[Organisation, User]:
    from app.repositories.user import UserRepository
    from app.repositories.organisation import OrganisationRepository

    user_repo = UserRepository(session)
    user = await user_repo.get_by_email(superadmin_email)
    if user is None:
        user = User(
            id=uuid.uuid4(),
            email=superadmin_email,
            password_hash="hashed",
            full_name="Org Admin",
            role="individual",
            account_type="corporate",
            email_verified=True,
            is_active=True,
        )
        session.add(user)
        await session.flush()

    org_repo = OrganisationRepository(session)
    org = await org_repo.create_with_policy(
        name=org_name,
        ssm_number=ssm_number,
        email_domain=email_domain,
        updated_by=user.id,
    )
    user.org_id = org.id
    user.role = "superadmin"
    await session.commit()
    await session.refresh(org)
    await session.refresh(user)
    return org, user


@pytest_asyncio.fixture
async def org_client(
    fake_redis: Redis,
) -> AsyncGenerator[AsyncClient, None]:
    tables = _sqlite_compat_metadata()
    async with _test_engine.begin() as conn:
        await conn.run_sync(lambda sync_conn: Base.metadata.create_all(sync_conn, tables=tables))

    async with TestSessionLocal() as session:
        now = datetime.now(UTC)
        for row in RELIEF_SEED:
            session.add(
                ReliefLimit(
                    id=uuid.uuid4(),
                    category=row[0],
                    be_seksyen=row[1],
                    limit_amount=Decimal(row[2]),
                    description_en=row[3],
                    description_my=row[4],
                    sort_order=row[5],
                    is_active=True,
                    updated_at=now,
                ),
            )
        await session.commit()

    async def _redis_client() -> AsyncGenerator[Redis, None]:
        yield fake_redis

    with (
        patch("app.main.init_redis", new_callable=AsyncMock, return_value=fake_redis),
        patch("app.main.close_redis", new_callable=AsyncMock),
        patch("app.main.ws_events_subscriber_loop", new_callable=AsyncMock),
        patch("app.main.receipt_worker_loop", new_callable=AsyncMock),
        patch("app.main.ensure_upload_root"),
        patch("app.main.run_migrations"),
        patch("app.main.run_startup_checks", new_callable=AsyncMock),
        patch("app.core.redis.get_redis", return_value=fake_redis),
        patch("app.services.auth.AuditService.log", new_callable=AsyncMock),
        patch("app.services.admin_auth.AuditService.log", new_callable=AsyncMock),
        patch("app.services.org.send_invite_email", new_callable=AsyncMock),
        patch("app.services.email.send_invite_email", new_callable=AsyncMock),
    ):
        from app.main import app

        app.dependency_overrides[deps.get_db] = override_get_db
        app.dependency_overrides[deps.get_redis_client] = _redis_client

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client

        app.dependency_overrides.clear()

    async with _test_engine.begin() as conn:
        await conn.run_sync(lambda sync_conn: Base.metadata.drop_all(sync_conn, tables=tables))


async def wait_for_receipt_processed(
    client: AsyncClient,
    receipt_id: str,
    *,
    max_attempts: int = 100,
) -> dict:
    fake_redis = getattr(client, "fake_redis", None)
    for _ in range(max_attempts):
        if fake_redis is not None:
            from app.services.job_queue import process_receipt_job, try_dequeue_receipt_job

            job = await try_dequeue_receipt_job(fake_redis)
            if job is not None:
                await process_receipt_job(fake_redis, job)

        response = await client.get(f"/api/v1/receipts/{receipt_id}")
        if response.status_code == 200:
            data = response.json()["data"]
            if data["scan_status"] not in {"waiting", "processing"}:
                return data
        await asyncio.sleep(0.05)
    raise TimeoutError(f"Receipt {receipt_id} was not processed in time")


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    mock_redis = AsyncMock()
    mock_redis.ping = AsyncMock(return_value=True)

    with (
        patch("app.main.init_redis", new_callable=AsyncMock, return_value=mock_redis),
        patch("app.main.close_redis", new_callable=AsyncMock),
        patch("app.main.ws_events_subscriber_loop", new_callable=AsyncMock),
        patch("app.main.ensure_upload_root"),
        patch("app.main.run_migrations"),
        patch("app.main.run_startup_checks", new_callable=AsyncMock),
    ):
        from app.main import app

        app.dependency_overrides[deps.get_db] = override_get_db

        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            yield client

        app.dependency_overrides.clear()


async def seed_user(
    session: AsyncSession,
    *,
    email: str,
    full_name: str = "Test User",
    role: str = "individual",
    account_type: str = "individual",
    tax_bracket: Decimal | None = Decimal("24"),
    tax_year: int = 2025,
) -> User:
    user = User(
        id=uuid.uuid4(),
        email=email,
        password_hash="hashed",
        full_name=full_name,
        role=role,
        account_type=account_type,
        tax_year=tax_year,
        tax_bracket=tax_bracket,
        email_verified=True,
        is_active=True,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def seed_platform_superadmin(session: AsyncSession) -> User:
    return await seed_user(
        session,
        email="platform-admin@example.com",
        full_name="Platform Admin",
        role="superadmin",
    )


async def seed_platform_admin(
    session: AsyncSession,
    *,
    email: str = "admin@admin.com",
    password: str = "Senario@123",
    full_name: str = "Platform Admin",
) -> PlatformAdmin:
    from app.core.security import hash_password

    admin = PlatformAdmin(
        id=uuid.uuid4(),
        email=email,
        password_hash=hash_password(password),
        full_name=full_name,
        is_active=True,
    )
    session.add(admin)
    await session.commit()
    await session.refresh(admin)
    return admin


@pytest_asyncio.fixture
async def phase6_client(
    fake_redis: Redis,
) -> AsyncGenerator[AsyncClient, None]:
    tables = _sqlite_compat_metadata()
    async with _test_engine.begin() as conn:
        await conn.run_sync(lambda sync_conn: Base.metadata.create_all(sync_conn, tables=tables))

    async with TestSessionLocal() as session:
        await seed_relief_limits(session)

    async def _redis_client() -> AsyncGenerator[Redis, None]:
        yield fake_redis

    with (
        patch("app.main.init_redis", new_callable=AsyncMock, return_value=fake_redis),
        patch("app.main.close_redis", new_callable=AsyncMock),
        patch("app.main.ws_events_subscriber_loop", new_callable=AsyncMock),
        patch("app.main.receipt_worker_loop", new_callable=AsyncMock),
        patch("app.main.ensure_upload_root"),
        patch("app.main.run_migrations"),
        patch("app.main.run_startup_checks", new_callable=AsyncMock),
        patch("app.core.redis.get_redis", return_value=fake_redis),
        patch("app.services.auth.AuditService.log", new_callable=AsyncMock),
        patch("app.services.admin_auth.AuditService.log", new_callable=AsyncMock),
    ):
        from app.main import app

        app.dependency_overrides[deps.get_db] = override_get_db
        app.dependency_overrides[deps.get_redis_client] = _redis_client

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client

        app.dependency_overrides.clear()

    async with _test_engine.begin() as conn:
        await conn.run_sync(lambda sync_conn: Base.metadata.drop_all(sync_conn, tables=tables))
