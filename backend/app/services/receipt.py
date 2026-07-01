import hashlib
import uuid
from datetime import UTC, datetime
from decimal import Decimal

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import UserInSession
from app.core.exceptions import AppError
from app.core.file_validator import get_safe_filename, validate_file
from app.core.storage import (
    build_receipt_download_url,
    build_receipt_file_url,
    build_receipt_thumbnail_url,
    MIME_BY_FILE_TYPE,
)
from app.services.storage import (
    build_receipt_storage_key,
    get_receipt_storage,
    get_storage,
    save_receipt_via_legacy_local,
)
from app.models.receipt import Receipt
from app.models.receipt_flag import ReceiptFlag
from app.models.user import User
from app.repositories.claim_summary import ClaimSummaryRepository
from app.repositories.org_policy import OrgPolicyRepository
from app.repositories.receipt import ReceiptRepository
from app.repositories.receipt_line_item import ReceiptLineItemRepository
from app.schemas.receipt import (
    ReceiptCreateRequest,
    ReceiptCreateResponse,
    ReceiptDetail,
    ReceiptDownloadData,
    ReceiptLineItemRead,
    ReceiptLineItemUpdate,
    ReceiptListItem,
    ReceiptListResponse,
    ReceiptManualCreateRequest,
    ReceiptReviewRequest,
    ReceiptUpdateRequest,
    ReceiptUploadFileError,
    ReceiptUploadResponse,
    ReliefStatusInfo,
)
from app.services.claim_limit import ClaimLimitService, NON_CLAIMABLE_CATEGORIES, ReliefCheckResult
from app.services.dedup import check_duplicate, compute_hash, derive_duplicate_image_hash
from app.services.job_queue import enqueue_receipt_job
from app.services.line_item_claims import (
    category_amounts_from_line_items,
    sync_receipt_header_from_line_items,
)
from app.services.tax_year import tax_year_from_receipt_date


class ReceiptService:
    ALLOWED_SORT_FIELDS = frozenset({"created_at", "receipt_date", "total_amount", "claimed_amount"})
    ORG_ADMIN_ROLES = frozenset({"hr_admin", "superadmin"})
    ALLOWED_UPLOAD_MIME = {
        "image/jpeg": "jpg",
        "image/png": "png",
        "application/pdf": "pdf",
    }

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._receipts = ReceiptRepository(db)
        self._line_items = ReceiptLineItemRepository(db)
        self._claims = ClaimSummaryRepository(db)
        self._limits = ClaimLimitService(db)

    @staticmethod
    def _context_type(session: UserInSession) -> str:
        return "corporate" if session.active_context == "corporate" and session.org_id is not None else "individual"

    @classmethod
    def _active_org_id(cls, session: UserInSession) -> uuid.UUID | None:
        return session.org_id if cls._context_type(session) == "corporate" else None

    async def list_receipts(
        self,
        user: User,
        session: UserInSession,
        *,
        tax_year: int | None,
        category: str | None,
        status: str | None,
        page: int,
        limit: int,
        sort: str,
    ) -> ReceiptListResponse:
        sort_field, sort_order = self._parse_sort(sort)
        items, total = await self._receipts.list_for_user(
            user_id=user.id,
            org_id=self._active_org_id(session),
            tax_year=tax_year,
            category=category,
            status=status,
            page=page,
            limit=limit,
            sort_field=sort_field,
            sort_order=sort_order,
        )

        return ReceiptListResponse(
            items=[self._to_list_item(receipt) for receipt in items],
            total=total,
            page=page,
            limit=limit,
        )

    async def get_receipt(self, user: User, session: UserInSession, receipt_id: uuid.UUID) -> ReceiptDetail:
        receipt = await self._get_owned_receipt(
            user.id,
            self._active_org_id(session),
            receipt_id,
            include_flags=True,
            include_line_items=True,
        )
        relief_status = await self._build_relief_status_for_receipt(user, session, receipt)
        return self._to_detail(receipt, relief_status=relief_status)

    async def create_receipt(
        self,
        user: User,
        session: UserInSession,
        payload: ReceiptCreateRequest,
    ) -> ReceiptCreateResponse:
        existing = await self._receipts.get_by_image_hash(payload.image_hash)
        if existing is not None:
            raise AppError(
                message="Resit dengan imej yang sama sudah wujud.",
                code="DUPLICATE_RECEIPT",
                status_code=409,
            )

        tax_year = tax_year_from_receipt_date(
            payload.receipt_date,
            payload.tax_year or user.tax_year,
        )
        claimed_amount = payload.claimed_amount or payload.total_amount

        if payload.category not in NON_CLAIMABLE_CATEGORIES:
            check = await self._limits.check_claim(
                user_id=user.id,
                tax_year=tax_year,
                category=payload.category,
                new_claimed_amount=claimed_amount,
                context_type=self._context_type(session),
                org_id=self._active_org_id(session),
            )
        else:
            check = ReliefCheckResult(
                relief_status=ReliefStatusInfo(
                    category=payload.category,
                    be_seksyen=None,
                    limit_amount=Decimal("0"),
                    total_claimed=Decimal("0"),
                    remaining=Decimal("0"),
                    percentage=0.0,
                    status="ok",
                ),
                would_exceed=False,
            )

        be_seksyen = await self._limits.get_be_seksyen(
            category=payload.category,
        )

        status = "pending"
        if check.relief_status.status == "warning":
            status = "flagged"

        receipt = Receipt(
            user_id=user.id,
            org_id=self._active_org_id(session),
            tax_year=tax_year,
            image_key=payload.image_key,
            image_hash=payload.image_hash,
            file_name=payload.file_name,
            file_type=payload.file_type,
            file_size_bytes=payload.file_size_bytes,
            merchant_name=payload.merchant_name,
            receipt_date=payload.receipt_date,
            total_amount=payload.total_amount,
            category=payload.category,
            be_seksyen=be_seksyen,
            claimed_amount=claimed_amount,
            excluded_amount=payload.excluded_amount,
            ai_confidence=payload.ai_confidence,
            ai_nota=payload.ai_nota,
            ocr_confidence=payload.ocr_confidence,
            status=status,
            scan_status="success",
        )
        receipt = await self._receipts.create(receipt)

        if check.relief_status.status == "warning":
            await self._add_flag(
                receipt,
                flag_type="limit_exceeded",
                message=(
                    f"Tuntutan hampir mencapai had pelepasan "
                    f"({check.relief_status.percentage:.1f}% daripada "
                    f"RM{check.relief_status.limit_amount:.2f})."
                ),
            )
            await self._db.refresh(receipt)

        detail = self._to_detail(receipt, relief_status=check.relief_status)
        return ReceiptCreateResponse(receipt=detail, relief_status=check.relief_status)

    async def upload_receipt(
        self,
        user: User,
        session: UserInSession,
        *,
        filename: str | None,
        content_type: str | None,
        content: bytes,
        upload_session_token: str | None = None,
        tax_year: int | None = None,
        redis: Redis | None = None,
    ) -> ReceiptUploadResponse:
        receipt_id, job_id = await self._create_receipt_from_upload(
            user,
            session,
            filename=filename,
            content_type=content_type,
            content=content,
            upload_session_token=upload_session_token,
            tax_year=tax_year,
            redis=redis,
        )
        return ReceiptUploadResponse(
            job_ids=[job_id],
            receipt_ids=[receipt_id],
            message="1 resit sedang diproses",
        )

    async def upload_receipts(
        self,
        user: User,
        session: UserInSession,
        *,
        uploads: list[tuple[str | None, str | None, bytes]],
        tax_year: int | None = None,
        redis: Redis | None = None,
    ) -> ReceiptUploadResponse:
        if not uploads:
            raise AppError(
                message="Tiada fail diterima.",
                code="VALIDATION_ERROR",
                status_code=422,
            )

        if len(uploads) > settings.max_upload_files:
            raise AppError(
                message=f"Maksimum {settings.max_upload_files} fail setiap muat naik.",
                code="VALIDATION_ERROR",
                status_code=422,
            )

        job_ids: list[uuid.UUID] = []
        receipt_ids: list[uuid.UUID] = []
        errors: list[ReceiptUploadFileError] = []

        for filename, content_type, content in uploads:
            try:
                receipt_id, job_id = await self._create_receipt_from_upload(
                    user,
                    session,
                    filename=filename,
                    content_type=content_type,
                    content=content,
                    tax_year=tax_year,
                    redis=redis,
                )
                job_ids.append(job_id)
                receipt_ids.append(receipt_id)
            except AppError as exc:
                errors.append(
                    ReceiptUploadFileError(
                        filename=filename,
                        code=exc.code,
                        message=exc.message,
                    )
                )

        if not job_ids:
            first_error = errors[0]
            raise AppError(
                message=(
                    first_error.message
                    if len(errors) == 1
                    else f"Semua {len(errors)} fail gagal dimuat naik."
                ),
                code=first_error.code,
                status_code=409 if first_error.code == "DUPLICATE_RECEIPT" else 422,
            )

        success_count = len(job_ids)
        total_count = len(uploads)
        if errors:
            message = f"{success_count} daripada {total_count} resit sedang diproses"
        elif success_count == 1:
            message = "1 resit sedang diproses"
        else:
            message = f"{success_count} resit sedang diproses"

        return ReceiptUploadResponse(
            job_ids=job_ids,
            receipt_ids=receipt_ids,
            message=message,
            errors=errors,
        )

    async def _create_receipt_from_upload(
        self,
        user: User,
        session: UserInSession,
        *,
        filename: str | None,
        content_type: str | None,
        content: bytes,
        upload_session_token: str | None = None,
        tax_year: int | None = None,
        redis: Redis | None = None,
    ) -> tuple[uuid.UUID, uuid.UUID]:
        if not content:
            raise AppError(
                message="Fail kosong.",
                code="VALIDATION_ERROR",
                status_code=422,
            )

        if len(content) > settings.max_upload_size_bytes:
            raise AppError(
                message="Saiz fail melebihi 10MB.",
                code="VALIDATION_ERROR",
                status_code=422,
            )

        if content_type not in self.ALLOWED_UPLOAD_MIME:
            raise AppError(
                message="Jenis fail tidak disokong. Gunakan JPG, PNG, atau PDF.",
                code="VALIDATION_ERROR",
                status_code=422,
            )

        if not validate_file(content, filename or "upload", content_type or ""):
            raise AppError(
                message="Kandungan fail tidak sepadan dengan jenis fail yang diisytiharkan.",
                code="VALIDATION_ERROR",
                status_code=422,
            )

        safe_filename = get_safe_filename(filename or "upload")

        if redis is None:
            raise AppError(
                message="Redis tidak tersedia untuk pemprosesan resit.",
                code="INTERNAL_ERROR",
                status_code=500,
            )

        await self._enforce_org_monthly_upload_limit(user, session)

        file_ext = self.ALLOWED_UPLOAD_MIME[content_type]
        normalized_type = file_ext.lower().lstrip(".")
        content_hash = await compute_hash(content)
        existing = await check_duplicate(self._db, content_hash, user.id)

        if existing is not None:
            duplicate = await self._create_duplicate_receipt(
                user,
                session,
                filename=filename,
                file_type=normalized_type,
                file_size=len(content),
                content_hash=content_hash,
                original=existing,
                tax_year=tax_year or user.tax_year,
            )
            return duplicate.id, duplicate.id

        backend_name = settings.storage_backend.strip().lower()
        if backend_name in {"s3", "r2"}:
            storage_key = build_receipt_storage_key(user.id, normalized_type)
            mime = MIME_BY_FILE_TYPE.get(normalized_type, "application/octet-stream")
            active_storage = get_storage()
            storage_key = await active_storage.upload_file(content, storage_key, mime)
        else:
            storage_key = save_receipt_via_legacy_local(
                user_id=str(user.id),
                content=content,
                file_ext=normalized_type,
            )

        receipt = Receipt(
            user_id=user.id,
            org_id=self._active_org_id(session),
            tax_year=tax_year or user.tax_year,
            image_key=storage_key,
            image_hash=content_hash,
            file_name=safe_filename,
            file_type=normalized_type,
            file_size_bytes=len(content),
            category="tidak_layak",
            status="pending",
            scan_status="waiting",
        )
        receipt = await self._receipts.create_receipt(receipt)
        await self._db.flush()

        job_id_str = await enqueue_receipt_job(
            redis,
            receipt_id=receipt.id,
            user_id=user.id,
            upload_session_token=upload_session_token,
        )
        return receipt.id, uuid.UUID(job_id_str)

    async def _create_duplicate_receipt(
        self,
        user: User,
        session: UserInSession,
        *,
        filename: str | None,
        file_type: str,
        file_size: int,
        content_hash: str,
        original: Receipt,
        tax_year: int,
    ) -> Receipt:
        from io import BytesIO

        from PIL import Image

        placeholder = Image.new("RGB", (2, 2), color="white")
        buffer = BytesIO()
        placeholder.save(buffer, format="PNG")
        tiny_png = buffer.getvalue()
        placeholder_key = save_receipt_via_legacy_local(
            user_id=str(user.id),
            content=tiny_png,
            file_ext="png",
        )
        receipt = Receipt(
            user_id=user.id,
            org_id=self._active_org_id(session),
            tax_year=tax_year,
            image_key=placeholder_key,
            image_hash=derive_duplicate_image_hash(content_hash),
            file_name=filename,
            file_type=file_type,
            file_size_bytes=file_size,
            category=original.category,
            status="duplicate",
            scan_status="failed",
            merchant_name=original.merchant_name,
            total_amount=original.total_amount,
            claimed_amount=original.claimed_amount,
        )
        receipt = await self._receipts.create_receipt(receipt)
        await self._receipts.create_flag(
            receipt.id,
            "duplicate_suspected",
            f"Duplikat resit asal: {original.id}",
        )
        await self._db.flush()
        return receipt

    async def create_manual_receipt(
        self,
        user: User,
        session: UserInSession,
        payload: ReceiptManualCreateRequest,
    ) -> ReceiptDetail:
        from io import BytesIO

        from PIL import Image

        placeholder = Image.new("RGB", (2, 2), color="white")
        buffer = BytesIO()
        placeholder.save(buffer, format="PNG")
        content = buffer.getvalue()
        image_hash = hashlib.sha256(content + str(uuid.uuid4()).encode()).hexdigest()

        storage = get_receipt_storage()
        image_key = storage.save_receipt_file(
            user_id=str(user.id),
            content=content,
            file_ext="png",
        )

        tax_year = tax_year_from_receipt_date(
            payload.receipt_date,
            payload.tax_year or user.tax_year,
        )
        claimed = payload.claimed_amount or payload.total_amount

        receipt = Receipt(
            user_id=user.id,
            org_id=self._active_org_id(session),
            tax_year=tax_year,
            image_key=image_key,
            image_hash=image_hash,
            file_name="manual-entry.png",
            file_type="png",
            file_size_bytes=len(content),
            merchant_name=payload.merchant_name,
            receipt_date=payload.receipt_date,
            total_amount=payload.total_amount,
            category=payload.category,
            claimed_amount=claimed,
            notes=payload.notes,
            status="pending",
            scan_status="success",
            ai_nota="Kemasukan manual — tiada OCR.",
        )
        receipt.be_seksyen = await self._limits.get_be_seksyen(category=payload.category)
        receipt = await self._receipts.create(receipt)

        from app.services.rule_engine import apply_rules

        rules = await apply_rules(
            self._db,
            user.id,
            tax_year,
            {
                "category": payload.category,
                "claimed_amount": claimed,
                "ocr_confidence": 1.0,
                "ai_confidence": 1.0,
                "is_mixed": False,
            },
        )
        receipt.claimed_amount = rules["claimed_amount"]
        receipt.category = rules["category"]
        receipt.be_seksyen = rules.get("be_seksyen") or receipt.be_seksyen
        if rules["flags"]:
            receipt.status = "flagged"
            for flag_type in rules["flags"]:
                await self._add_flag(receipt, flag_type=flag_type, message=None)

        await self._db.flush()
        loaded = await self._receipts.get_receipt_with_details(
            receipt.id,
            user.id,
            self._active_org_id(session),
        )
        assert loaded is not None
        relief_status = await self._build_relief_status_for_receipt(user, session, loaded)
        return self._to_detail(loaded, relief_status=relief_status)

    async def reprocess_receipt(
        self,
        user: User,
        session: UserInSession,
        receipt_id: uuid.UUID,
        *,
        redis: Redis,
    ) -> ReceiptDetail:
        del redis
        receipt = await self._get_owned_receipt(
            user.id,
            self._active_org_id(session),
            receipt_id,
            include_flags=True,
        )
        storage = get_receipt_storage()
        file_bytes = storage.read_receipt_file(receipt.image_key)
        if file_bytes is None:
            raise AppError(
                message="Fail resit tidak dijumpai.",
                code="NOT_FOUND",
                status_code=404,
            )

        if receipt.file_type == "pdf":
            from app.services.vision_llm import classify_receipt

            ai_result = await classify_receipt(file_bytes, "pdf", db=self._db)
            receipt.scan_status = "failed"
            receipt.status = "pending"
            receipt.ai_nota = ai_result.get("ai_nota")
            await self._db.flush()
        else:
            from app.services.vision_llm import classify_receipt
            from app.services.rule_engine import apply_rules

            ai_result = await classify_receipt(
                file_bytes,
                receipt.file_type or "jpg",
                db=self._db,
            )
            if ai_result.get("scan_status") == "failed":
                receipt.scan_status = "failed"
                receipt.status = "flagged"
                receipt.ai_nota = ai_result.get("ai_nota")
            else:
                rules = await apply_rules(
                    self._db,
                    user.id,
                    receipt.tax_year,
                    ai_result,
                )
                receipt.merchant_name = ai_result.get("merchant_name")
                receipt.receipt_date = ai_result.get("receipt_date")
                receipt.total_amount = ai_result.get("total_amount")
                receipt.category = rules["category"]
                receipt.be_seksyen = rules.get("be_seksyen")
                receipt.claimed_amount = rules["claimed_amount"]
                receipt.ai_confidence = Decimal(str(rules.get("ai_confidence", 0)))
                receipt.ocr_confidence = Decimal(str(rules.get("ocr_confidence", 0)))
                receipt.ai_nota = rules.get("ai_nota")
                receipt.scan_status = "success"
                receipt.status = "flagged" if rules["flags"] else "pending"
            await self._db.flush()

        relief_status = await self._build_relief_status_for_receipt(user, session, receipt)
        return self._to_detail(receipt, relief_status=relief_status)

    async def update_receipt(
        self,
        user: User,
        session: UserInSession,
        receipt_id: uuid.UUID,
        payload: ReceiptUpdateRequest,
    ) -> ReceiptDetail:
        receipt = await self._get_owned_receipt(
            user.id,
            self._active_org_id(session),
            receipt_id,
            include_flags=True,
            include_line_items=True,
        )

        if payload.line_items is not None:
            return await self._update_receipt_line_items(user, session, receipt, payload.line_items)

        if payload.notes is not None:
            receipt.notes = payload.notes

        if payload.category is None and payload.claimed_amount is None:
            if payload.notes is not None:
                await self._db.flush()
                await self._db.refresh(receipt, attribute_names=["flags", "line_items"])
            relief_status = await self._build_relief_status_for_receipt(user, session, receipt)
            return self._to_detail(receipt, relief_status=relief_status)

        new_category = payload.category or receipt.category
        new_claimed = payload.claimed_amount or receipt.claimed_amount or Decimal("0")

        if new_category is None:
            raise AppError(
                message="Kategori resit diperlukan.",
                code="VALIDATION_ERROR",
                status_code=422,
            )

        old_category = receipt.category
        old_claimed = receipt.claimed_amount or Decimal("0")
        old_status = receipt.status
        category_changed = payload.category is not None and payload.category != old_category
        amount_changed = payload.claimed_amount is not None and payload.claimed_amount != old_claimed

        if new_category not in NON_CLAIMABLE_CATEGORIES:
            if old_status in ("pending", "flagged"):
                subtract_approved = Decimal("0")
                exclude_id = receipt.id
            elif category_changed:
                subtract_approved = Decimal("0")
                exclude_id = None
            else:
                subtract_approved = old_claimed
                exclude_id = None

            check = await self._limits.check_claim(
                user_id=user.id,
                tax_year=receipt.tax_year,
                category=new_category,
                new_claimed_amount=new_claimed,
                context_type=self._context_type(session),
                org_id=self._active_org_id(session),
                exclude_receipt_id=exclude_id,
                subtract_approved=subtract_approved,
            )
        else:
            check = None

        if payload.category is not None:
            receipt.category = payload.category
            receipt.be_seksyen = await self._limits.get_be_seksyen(
                category=payload.category,
            )
        if payload.claimed_amount is not None:
            receipt.claimed_amount = payload.claimed_amount

        if old_status == "approved" and (category_changed or amount_changed):
            await self._sync_approved_receipt_change(
                receipt=receipt,
                old_category=old_category,
                old_claimed=old_claimed,
                category_changed=category_changed,
            )

        if check is not None and check.relief_status.status == "warning" and receipt.status != "approved":
            receipt.status = "flagged"
            await self._add_flag(
                receipt,
                flag_type="limit_exceeded",
                message=(
                    f"Tuntutan hampir mencapai had pelepasan "
                    f"({check.relief_status.percentage:.1f}% daripada "
                    f"RM{check.relief_status.limit_amount:.2f})."
                ),
            )
        elif check is not None and check.relief_status.status == "ok" and receipt.status == "flagged":
            receipt.status = "pending"

        await self._db.flush()
        await self._db.refresh(receipt)

        relief_status = check.relief_status if check else await self._build_relief_status_for_receipt(
            user,
            session,
            receipt,
        )
        return self._to_detail(receipt, relief_status=relief_status)

    async def delete_receipt(self, user: User, session: UserInSession, receipt_id: uuid.UUID) -> None:
        receipt = await self._get_owned_receipt(
            user.id,
            self._active_org_id(session),
            receipt_id,
            include_line_items=True,
        )

        if receipt.status == "approved":
            await self._remove_approved_claims(receipt)

        await self._receipts.soft_delete(receipt)

    async def review_receipt(
        self,
        reviewer: User,
        reviewer_session: UserInSession,
        receipt_id: uuid.UUID,
        payload: ReceiptReviewRequest,
    ) -> ReceiptDetail:
        receipt = await self._get_receipt_for_org_review(reviewer_session, receipt_id)

        if receipt.status in ("approved", "rejected", "duplicate"):
            raise AppError(
                message="Resit ini telah disemak.",
                code="VALIDATION_ERROR",
                status_code=422,
            )

        if payload.action == "approve":
            if not receipt.category or receipt.category in NON_CLAIMABLE_CATEGORIES:
                raise AppError(
                    message="Resit memerlukan kategori sah sebelum diluluskan.",
                    code="VALIDATION_ERROR",
                    status_code=422,
                )
            if not receipt.claimed_amount or receipt.claimed_amount <= 0:
                raise AppError(
                    message="Resit memerlukan jumlah tuntutan sebelum diluluskan.",
                    code="VALIDATION_ERROR",
                    status_code=422,
                )

            receipt.status = "approved"
            await self._apply_approved_claims(receipt)
        else:
            receipt.status = "rejected"

        receipt.reviewed_by = reviewer.id
        receipt.reviewed_at = datetime.now(UTC)
        receipt.review_comment = payload.comment

        await self._db.flush()
        await self._db.refresh(receipt, attribute_names=["flags"])

        owner = await self._get_receipt_owner(receipt.user_id)
        relief_status = await self._build_relief_status_for_receipt(
            owner,
            reviewer_session,
            receipt,
        )
        return self._to_detail(receipt, relief_status=relief_status)

    async def bulk_approve_org_pending(
        self,
        reviewer: User,
        reviewer_session: UserInSession,
        *,
        tax_year: int | None = None,
    ) -> tuple[int, int]:
        if reviewer_session.org_id is None or reviewer_session.role not in self.ORG_ADMIN_ROLES:
            raise AppError(
                message="Akses ditolak. Hanya HR admin dibenarkan.",
                code="FORBIDDEN",
                status_code=403,
            )

        pending = await self._receipts.list_all_pending_for_org(
            org_id=reviewer_session.org_id,
            tax_year=tax_year,
        )

        approved_count = 0
        skipped_count = 0

        for receipt in pending:
            try:
                await self.review_receipt(
                    reviewer,
                    reviewer_session,
                    receipt.id,
                    ReceiptReviewRequest(action="approve"),
                )
                approved_count += 1
            except AppError:
                skipped_count += 1

        return approved_count, skipped_count

    async def get_receipt_file(
        self,
        user: User,
        session: UserInSession,
        receipt_id: uuid.UUID,
    ) -> tuple[bytes, str, str | None]:
        receipt = await self._get_owned_receipt(user.id, self._active_org_id(session), receipt_id)
        storage = get_receipt_storage()
        content = storage.read_receipt_file(receipt.image_key)
        if content is None:
            raise AppError(
                message="Fail resit tidak dijumpai.",
                code="NOT_FOUND",
                status_code=404,
            )

        file_type = (receipt.file_type or "jpg").lower()
        media_type = MIME_BY_FILE_TYPE.get(file_type, "application/octet-stream")
        return content, media_type, receipt.file_name

    async def get_receipt_thumbnail(
        self,
        user: User,
        session: UserInSession,
        receipt_id: uuid.UUID,
    ) -> tuple[bytes, str]:
        receipt = await self._get_owned_receipt(user.id, self._active_org_id(session), receipt_id)
        storage = get_receipt_storage()
        content = storage.read_thumbnail(receipt.image_key)
        if content is None:
            raise AppError(
                message="Thumbnail resit tidak dijumpai.",
                code="NOT_FOUND",
                status_code=404,
            )
        return content, "image/jpeg"

    async def get_receipt_download(
        self,
        user: User,
        session: UserInSession,
        receipt_id: uuid.UUID,
    ) -> ReceiptDownloadData:
        receipt = await self._get_owned_receipt(user.id, self._active_org_id(session), receipt_id)
        storage = get_receipt_storage()
        if not storage.receipt_file_exists(receipt.image_key):
            raise AppError(
                message="Fail resit tidak dijumpai.",
                code="NOT_FOUND",
                status_code=404,
            )

        return ReceiptDownloadData(
            download_url=build_receipt_download_url(str(receipt.id)),
            expires_in=settings.session_ttl_seconds,
            file_name=receipt.file_name,
        )

    async def _get_owned_receipt(
        self,
        user_id: uuid.UUID,
        org_id: uuid.UUID | None,
        receipt_id: uuid.UUID,
        *,
        include_flags: bool = False,
        include_line_items: bool = False,
    ) -> Receipt:
        receipt = await self._receipts.get_by_id_for_user(
            receipt_id,
            user_id,
            org_id=org_id,
            include_flags=include_flags,
            include_line_items=include_line_items,
        )
        if receipt is None:
            raise AppError(
                message="Resit tidak dijumpai.",
                code="NOT_FOUND",
                status_code=404,
            )
        return receipt

    async def _enforce_org_monthly_upload_limit(self, user: User, session: UserInSession) -> None:
        org_id = self._active_org_id(session)
        if org_id is None:
            return

        policy = await OrgPolicyRepository(self._db).get_by_org_id(org_id)
        if policy is None:
            return

        today = datetime.now(UTC).date()
        month_start = today.replace(day=1)
        count = await self._receipts.count_uploads_this_month(
            user_id=user.id,
            org_id=org_id,
            month_start=month_start,
            month_end=today,
        )
        if count >= policy.max_receipts_per_month:
            raise AppError(
                message=(
                    f"Had muat naik bulanan ({policy.max_receipts_per_month} resit) "
                    "telah dicapai."
                ),
                code="VALIDATION_ERROR",
                status_code=422,
            )

    async def _get_receipt_for_org_review(
        self,
        reviewer: UserInSession,
        receipt_id: uuid.UUID,
    ) -> Receipt:
        if reviewer.org_id is None or reviewer.role not in self.ORG_ADMIN_ROLES:
            raise AppError(
                message="Akses ditolak. Hanya HR admin dibenarkan.",
                code="FORBIDDEN",
                status_code=403,
            )

        receipt = await self._receipts.get_by_id(
            receipt_id,
            include_flags=True,
            include_line_items=True,
        )
        if receipt is None or receipt.org_id != reviewer.org_id:
            raise AppError(
                message="Resit tidak dijumpai.",
                code="NOT_FOUND",
                status_code=404,
            )

        return receipt

    async def _get_receipt_owner(self, user_id: uuid.UUID) -> User:
        from app.repositories.user import UserRepository

        user = await UserRepository(self._db).get_by_id(user_id)
        if user is None:
            raise AppError(
                message="Pemilik resit tidak dijumpai.",
                code="NOT_FOUND",
                status_code=404,
            )
        return user

    async def _update_receipt_line_items(
        self,
        user: User,
        session: UserInSession,
        receipt: Receipt,
        updates: list[ReceiptLineItemUpdate],
    ) -> ReceiptDetail:
        if not receipt.line_items:
            raise AppError(
                message="Resit ini tidak mempunyai pecahan item.",
                code="VALIDATION_ERROR",
                status_code=422,
            )

        item_map = {item.id: item for item in receipt.line_items}
        if len(updates) != len(item_map):
            raise AppError(
                message="Semua item resit mesti dikemas kini.",
                code="VALIDATION_ERROR",
                status_code=422,
            )

        old_by_category = (
            category_amounts_from_line_items(receipt.line_items)
            if receipt.status == "approved"
            else {}
        )

        for update in updates:
            item = item_map.get(update.id)
            if item is None:
                raise AppError(
                    message="Item resit tidak sah.",
                    code="VALIDATION_ERROR",
                    status_code=422,
                )
            item.included_in_claim = update.included_in_claim
            if update.category is not None:
                item.category = update.category

        sync_receipt_header_from_line_items(receipt, receipt.line_items)

        if receipt.category:
            receipt.be_seksyen = await self._limits.get_be_seksyen(category=receipt.category)

        if receipt.status == "approved":
            new_by_category = category_amounts_from_line_items(receipt.line_items)
            await self._sync_line_item_claim_delta(
                receipt,
                old_by_category=old_by_category,
                new_by_category=new_by_category,
            )
        elif receipt.status in ("pending", "flagged"):
            await self._apply_line_item_limit_flags(receipt, user, session)

        await self._db.flush()
        await self._db.refresh(receipt, attribute_names=["flags", "line_items"])

        relief_status = await self._build_relief_status_for_receipt(user, session, receipt)
        return self._to_detail(receipt, relief_status=relief_status)

    async def _apply_line_item_limit_flags(self, receipt: Receipt, user: User, session: UserInSession) -> None:
        by_category = category_amounts_from_line_items(receipt.line_items)
        receipt.status = "pending"

        for category, claimed in by_category.items():
            check = await self._limits.check_claim(
                user_id=user.id,
                tax_year=receipt.tax_year,
                category=category,
                new_claimed_amount=claimed,
                context_type=self._context_type(session),
                org_id=self._active_org_id(session),
                exclude_receipt_id=receipt.id,
                raise_on_exceed=False,
            )
            if check.would_exceed or check.relief_status.status == "warning":
                receipt.status = "flagged"
                await self._add_flag(
                    receipt,
                    flag_type="limit_exceeded",
                    message=(
                        f"Tuntutan {category} melebihi atau hampir had pelepasan."
                    ),
                )
                break

    async def _apply_approved_claims(self, receipt: Receipt) -> None:
        context_type = "corporate" if receipt.org_id is not None else "individual"
        if self._has_itemised_claim(receipt):
            by_category = category_amounts_from_line_items(receipt.line_items)
            for category, amount in by_category.items():
                await self._claims.adjust(
                    user_id=receipt.user_id,
                    tax_year=receipt.tax_year,
                    category=category,
                    amount_delta=amount,
                    count_delta=1,
                    context_type=context_type,
                    org_id=receipt.org_id,
                )
            return

        if receipt.category and receipt.claimed_amount:
            await self._claims.adjust(
                user_id=receipt.user_id,
                tax_year=receipt.tax_year,
                category=receipt.category,
                amount_delta=receipt.claimed_amount,
                count_delta=1,
                context_type=context_type,
                org_id=receipt.org_id,
            )

    async def _remove_approved_claims(self, receipt: Receipt) -> None:
        context_type = "corporate" if receipt.org_id is not None else "individual"
        if self._has_itemised_claim(receipt):
            by_category = category_amounts_from_line_items(receipt.line_items)
            for category, amount in by_category.items():
                await self._claims.adjust(
                    user_id=receipt.user_id,
                    tax_year=receipt.tax_year,
                    category=category,
                    amount_delta=-amount,
                    count_delta=-1,
                    context_type=context_type,
                    org_id=receipt.org_id,
                )
            return

        if receipt.category and receipt.claimed_amount:
            await self._claims.adjust(
                user_id=receipt.user_id,
                tax_year=receipt.tax_year,
                category=receipt.category,
                amount_delta=-receipt.claimed_amount,
                count_delta=-1,
                context_type=context_type,
                org_id=receipt.org_id,
            )

    async def _sync_line_item_claim_delta(
        self,
        receipt: Receipt,
        *,
        old_by_category: dict[str, Decimal],
        new_by_category: dict[str, Decimal],
    ) -> None:
        categories = set(old_by_category) | set(new_by_category)
        for category in categories:
            old_amount = old_by_category.get(category, Decimal("0"))
            new_amount = new_by_category.get(category, Decimal("0"))
            amount_delta = new_amount - old_amount
            count_delta = 0
            if old_amount > 0 and new_amount <= 0:
                count_delta = -1
            elif old_amount <= 0 and new_amount > 0:
                count_delta = 1

            if amount_delta != 0 or count_delta != 0:
                await self._claims.adjust(
                    user_id=receipt.user_id,
                    tax_year=receipt.tax_year,
                    category=category,
                    amount_delta=amount_delta,
                    count_delta=count_delta,
                    context_type="corporate" if receipt.org_id is not None else "individual",
                    org_id=receipt.org_id,
                )

    @staticmethod
    def _has_itemised_claim(receipt: Receipt) -> bool:
        return bool(receipt.line_items and len(receipt.line_items) >= 2)

    async def _sync_approved_receipt_change(
        self,
        *,
        receipt: Receipt,
        old_category: str | None,
        old_claimed: Decimal,
        category_changed: bool,
    ) -> None:
        if self._has_itemised_claim(receipt):
            return

        if category_changed and old_category:
            await self._claims.adjust(
                user_id=receipt.user_id,
                tax_year=receipt.tax_year,
                category=old_category,
                amount_delta=-old_claimed,
                count_delta=-1,
                context_type="corporate" if receipt.org_id is not None else "individual",
                org_id=receipt.org_id,
            )

        if receipt.category and receipt.claimed_amount:
            await self._claims.adjust(
                user_id=receipt.user_id,
                tax_year=receipt.tax_year,
                category=receipt.category,
                amount_delta=receipt.claimed_amount if category_changed else receipt.claimed_amount - old_claimed,
                count_delta=1 if category_changed else 0,
                context_type="corporate" if receipt.org_id is not None else "individual",
                org_id=receipt.org_id,
            )

    async def _build_relief_status_for_receipt(
        self,
        user: User,
        session: UserInSession,
        receipt: Receipt,
    ):
        if not receipt.category or receipt.category in NON_CLAIMABLE_CATEGORIES:
            return None

        claimed = receipt.claimed_amount or Decimal("0")
        context_type = "corporate" if receipt.org_id is not None else "individual"
        active_org_id = receipt.org_id if context_type == "corporate" else None
        result = await self._limits.check_claim(
            user_id=user.id,
            tax_year=receipt.tax_year,
            category=receipt.category,
            new_claimed_amount=claimed,
            context_type=context_type,
            org_id=active_org_id,
            exclude_receipt_id=receipt.id if receipt.status in ("pending", "flagged") else None,
            raise_on_exceed=False,
        )

        if receipt.status == "approved":
            approved_total = await self._claims.get_approved_total(
                user_id=user.id,
                tax_year=receipt.tax_year,
                category=receipt.category,
                context_type=context_type,
                org_id=active_org_id,
            )
            relief_limit = result.relief_status.limit_amount
            remaining = max(Decimal("0"), relief_limit - approved_total)
            percentage = float(
                (approved_total / relief_limit * 100).quantize(Decimal("0.1"))
                if relief_limit > 0
                else Decimal("0"),
            )
            if approved_total > relief_limit:
                status = "full"
            elif approved_total >= relief_limit * Decimal("0.80"):
                status = "warning"
            else:
                status = "ok"

            return ReliefStatusInfo(
                category=receipt.category,
                be_seksyen=result.relief_status.be_seksyen,
                limit_amount=relief_limit,
                total_claimed=approved_total,
                remaining=remaining,
                percentage=percentage,
                status=status,  # type: ignore[arg-type]
            )

        return result.relief_status

    async def _add_flag(
        self,
        receipt: Receipt,
        *,
        flag_type: str,
        message: str | None,
    ) -> None:
        await self._receipts.create_flag(
            receipt.id,
            flag_type,
            message,
        )

    def _parse_sort(self, sort: str) -> tuple[str, str]:
        if ":" in sort:
            field, order = sort.split(":", 1)
        else:
            field, order = sort, "desc"

        field = field.strip()
        order = order.strip().lower()
        if field not in self.ALLOWED_SORT_FIELDS:
            field = "created_at"
        if order not in {"asc", "desc"}:
            order = "desc"
        return field, order

    def _file_urls(self, receipt: Receipt) -> tuple[str | None, str | None]:
        storage = get_receipt_storage()
        if not storage.receipt_file_exists(receipt.image_key):
            return None, None

        receipt_id = str(receipt.id)
        thumbnail_url = build_receipt_thumbnail_url(receipt_id)
        if receipt.file_type == "pdf":
            thumbnail_url = None

        return thumbnail_url, build_receipt_file_url(receipt_id)

    def _to_list_item(self, receipt: Receipt) -> ReceiptListItem:
        thumbnail_url, _ = self._file_urls(receipt)
        return ReceiptListItem(
            id=receipt.id,
            merchant_name=receipt.merchant_name,
            receipt_date=receipt.receipt_date,
            total_amount=receipt.total_amount,
            claimed_amount=receipt.claimed_amount,
            category=receipt.category,
            be_seksyen=receipt.be_seksyen,
            status=receipt.status,
            scan_status=receipt.scan_status,
            ai_confidence=receipt.ai_confidence,
            file_type=receipt.file_type,
            thumbnail_url=thumbnail_url,
            created_at=receipt.created_at,
        )

    def _to_detail(
        self,
        receipt: Receipt,
        *,
        relief_status=None,
    ) -> ReceiptDetail:
        from app.schemas.receipt import ReceiptFlagRead

        flags = [ReceiptFlagRead.model_validate(flag) for flag in receipt.flags] if receipt.flags else []
        line_items = (
            [ReceiptLineItemRead.model_validate(item) for item in receipt.line_items]
            if receipt.line_items
            else []
        )
        thumbnail_url, image_url = self._file_urls(receipt)

        return ReceiptDetail(
            id=receipt.id,
            merchant_name=receipt.merchant_name,
            receipt_date=receipt.receipt_date,
            total_amount=receipt.total_amount,
            claimed_amount=receipt.claimed_amount,
            excluded_amount=receipt.excluded_amount,
            category=receipt.category,
            be_seksyen=receipt.be_seksyen,
            status=receipt.status,
            scan_status=receipt.scan_status,
            ai_confidence=receipt.ai_confidence,
            ai_nota=receipt.ai_nota,
            ocr_confidence=receipt.ocr_confidence,
            image_url=image_url,
            flags=flags,
            line_items=line_items,
            notes=receipt.notes,
            reviewed_by=receipt.reviewed_by,
            reviewed_at=receipt.reviewed_at,
            created_at=receipt.created_at,
            relief_status=relief_status,
        )
