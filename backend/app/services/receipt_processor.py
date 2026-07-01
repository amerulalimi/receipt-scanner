from __future__ import annotations

import logging
from decimal import Decimal

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.storage import get_receipt_storage
from app.models.receipt import Receipt
from app.models.receipt_flag import ReceiptFlag
from app.models.user import User
from app.repositories.org_policy import OrgPolicyRepository
from app.repositories.receipt import ReceiptRepository
from app.repositories.receipt_line_item import ReceiptLineItemRepository
from app.repositories.relief_limit import ReliefLimitRepository
from app.repositories.user import UserRepository
from app.schemas.receipt_job import ReceiptJobPayload
from app.schemas.vision_llm import VisionClassificationResult, VisionLineItem
from app.services.claim_limit import NON_CLAIMABLE_CATEGORIES, ClaimLimitService
from app.services.job_queue import get_openrouter_credentials, publish_ws_event
from app.services.receipt import ReceiptService
from app.services.line_item_claims import sync_receipt_header_from_line_items
from app.services.tax_year import tax_year_from_receipt_date
from app.services.vision_llm import classify_receipt_async

logger = logging.getLogger(__name__)

LOW_OCR_CONFIDENCE = 0.70
LOW_AI_CONFIDENCE = 0.70
CRITICAL_FLAG_TYPES = frozenset(
    {"manual_review", "low_ocr_confidence", "limit_exceeded"},
)


class ReceiptProcessor:
    def __init__(self, db: AsyncSession, redis: Redis) -> None:
        self._db = db
        self._redis = redis
        self._receipts = ReceiptRepository(db)
        self._users = UserRepository(db)
        self._relief_limits = ReliefLimitRepository(db)
        self._limits = ClaimLimitService(db)
        self._receipt_service = ReceiptService(db)
        self._org_policies = OrgPolicyRepository(db)

    async def process(self, job: ReceiptJobPayload) -> None:
        receipt = await self._receipts.get_by_id(job.receipt_id, include_flags=True)
        if receipt is None:
            logger.warning("Receipt %s not found, skipping job", job.receipt_id)
            return

        user = await self._users.get_by_id(job.user_id)
        if user is None:
            logger.warning("User %s not found for receipt %s", job.user_id, job.receipt_id)
            return

        try:
            receipt.scan_status = "processing"
            await self._db.flush()
            await self._publish_scan_updated(receipt, job.upload_session_token)
            await self._process_receipt(receipt, user, job)
        except Exception as exc:
            logger.exception("Failed to process receipt %s", job.receipt_id)
            await self._handle_failure(receipt, job, str(exc))

    async def _publish_scan_updated(
        self,
        receipt: Receipt,
        upload_session_token: str | None,
    ) -> None:
        if not upload_session_token:
            return
        await publish_ws_event(
            self._redis,
            upload_session_token=upload_session_token,
            event={
                "type": "receipt_scan_updated",
                "data": {
                    "receipt_id": str(receipt.id),
                    "scan_status": receipt.scan_status,
                },
            },
        )

    async def _process_receipt(
        self,
        receipt: Receipt,
        user: User,
        job: ReceiptJobPayload,
    ) -> None:
        upload_session_token = job.upload_session_token
        if receipt.file_type == "pdf":
            await self._apply_pdf_manual_review(receipt)
        else:
            await self._apply_vision_classification(receipt)

        self._resolve_tax_year_from_receipt_date(receipt, user)
        await self._apply_rule_engine(receipt, user)
        await self._apply_org_category_policy(receipt, user)
        await self._maybe_auto_approve(receipt, user)
        await self._db.flush()
        await self._db.refresh(receipt, attribute_names=["flags"])
        await self._publish_scan_updated(receipt, upload_session_token)

        if upload_session_token:
            detail = await self._receipt_service.get_receipt(user, receipt.id)
            await publish_ws_event(
                self._redis,
                upload_session_token=upload_session_token,
                event={
                    "type": "receipt_added",
                    "data": {"receipt": detail.model_dump(mode="json")},
                },
            )

    async def _apply_pdf_manual_review(self, receipt: Receipt) -> None:
        receipt.category = "semak_manual"
        receipt.status = "pending"
        receipt.scan_status = "failed"
        self._add_flag(
            receipt,
            flag_type="manual_review",
            message="PDF memerlukan semakan manual — tiada OCR automatik lagi.",
        )

    async def _apply_vision_classification(self, receipt: Receipt) -> None:
        credentials = await get_openrouter_credentials(self._db)
        if credentials is None:
            raise RuntimeError("OpenRouter API key tidak dikonfigurasi.")

        api_key, model = credentials
        storage = get_receipt_storage()
        image_bytes = storage.read_receipt_file(receipt.image_key)
        if image_bytes is None:
            raise FileNotFoundError(f"Fail resit tidak dijumpai: {receipt.image_key}")

        active_limits = await self._relief_limits.list_active()
        active_slugs = {item.category for item in active_limits}

        result = await classify_receipt_async(
            image_bytes=image_bytes,
            file_type=receipt.file_type or "jpg",
            api_key=api_key,
            model=model,
            categories=[
                (item.category, item.description_my) for item in active_limits
            ],
        )

        if (
            result.kategori not in NON_CLAIMABLE_CATEGORIES
            and result.kategori not in active_slugs
        ):
            result.kategori = "semak_manual"
            result.nota = (
                result.nota or "Kategori tidak dikenali atau tidak aktif — semak manual."
            )

        receipt.merchant_name = result.merchant_name
        receipt.receipt_date = result.receipt_date
        receipt.total_amount = result.total_amount
        receipt.category = result.kategori
        receipt.be_seksyen = result.seksyen
        receipt.claimed_amount = result.jumlah_claim or result.total_amount
        receipt.excluded_amount = result.jumlah_tidak_layak
        receipt.ai_confidence = Decimal(str(round(result.confidence, 3)))
        receipt.ocr_confidence = Decimal(str(round(result.confidence, 3)))
        receipt.ai_nota = result.nota
        receipt.status = "pending"
        if result.confidence == 0 and result.kategori == "semak_manual":
            receipt.scan_status = "failed"
        else:
            receipt.scan_status = "success"

        has_itemised = await self._persist_line_items(
            receipt,
            result=result,
            active_slugs=active_slugs,
        )

        if result.confidence < LOW_OCR_CONFIDENCE:
            self._add_flag(
                receipt,
                flag_type="low_ocr_confidence",
                message=f"Keyakinan OCR rendah ({result.confidence:.0%}).",
            )
        if result.confidence < LOW_AI_CONFIDENCE:
            self._add_flag(
                receipt,
                flag_type="low_ai_confidence",
                message=f"Keyakinan AI rendah ({result.confidence:.0%}).",
            )
        if result.mixed_items and not has_itemised:
            self._add_flag(
                receipt,
                flag_type="mixed_items",
                message="Resit mengandungi item campuran — semak jumlah tuntutan.",
            )
        if result.kategori == "semak_manual":
            self._add_flag(
                receipt,
                flag_type="manual_review",
                message=result.nota or "Resit memerlukan semakan manual.",
            )

    async def _persist_line_items(
        self,
        receipt: Receipt,
        *,
        result: VisionClassificationResult,
        active_slugs: set[str],
    ) -> bool:
        parsed_items = self._normalise_line_items(result.line_items, active_slugs)
        if len(parsed_items) < 2 and not result.mixed_items:
            return False

        line_repo = ReceiptLineItemRepository(self._db)
        await line_repo.delete_for_receipt(receipt.id)
        created = await line_repo.create_many(receipt.id, parsed_items)
        receipt.line_items = created
        sync_receipt_header_from_line_items(receipt, created)

        if result.seksyen and receipt.category:
            receipt.be_seksyen = result.seksyen

        return True

    @staticmethod
    def _normalise_line_items(
        items: list[VisionLineItem],
        active_slugs: set[str],
    ) -> list[dict]:
        parsed: list[dict] = []
        for item in items:
            if item.amount <= 0:
                continue

            category = item.kategori
            if category not in active_slugs and category not in NON_CLAIMABLE_CATEGORIES:
                category = "semak_manual"

            ai_claimable = item.claimable and category not in NON_CLAIMABLE_CATEGORIES
            parsed.append(
                {
                    "description": item.description.strip()[:500],
                    "amount": item.amount,
                    "category": category,
                    "ai_claimable": ai_claimable,
                    "included_in_claim": ai_claimable,
                },
            )
        return parsed

    @staticmethod
    def _resolve_tax_year_from_receipt_date(receipt: Receipt, user: User) -> None:
        receipt.tax_year = tax_year_from_receipt_date(
            receipt.receipt_date,
            receipt.tax_year or user.tax_year,
        )

    async def _apply_rule_engine(self, receipt: Receipt, user: User) -> None:
        if receipt.line_items and len(receipt.line_items) >= 2:
            await self._apply_rule_engine_for_line_items(receipt, user)
            return

        category = receipt.category
        if not category or category in NON_CLAIMABLE_CATEGORIES:
            return

        claimed = receipt.claimed_amount or Decimal("0")
        check = await self._limits.check_claim(
            user_id=user.id,
            tax_year=receipt.tax_year,
            category=category,
            new_claimed_amount=claimed,
            exclude_receipt_id=receipt.id,
            raise_on_exceed=False,
        )

        if not receipt.be_seksyen:
            receipt.be_seksyen = await self._limits.get_be_seksyen(
                category=category,
            )

        if check.would_exceed:
            receipt.status = "flagged"
            self._add_flag(
                receipt,
                flag_type="limit_exceeded",
                message="Tuntutan melebihi had pelepasan untuk kategori ini.",
            )
        elif check.relief_status.status == "warning":
            receipt.status = "flagged"
            self._add_flag(
                receipt,
                flag_type="limit_exceeded",
                message=(
                    f"Tuntutan hampir mencapai had pelepasan "
                    f"({check.relief_status.percentage:.1f}% daripada "
                    f"RM{check.relief_status.limit_amount:.2f})."
                ),
            )

    async def _apply_rule_engine_for_line_items(
        self,
        receipt: Receipt,
        user: User,
    ) -> None:
        from app.services.line_item_claims import category_amounts_from_line_items

        by_category = category_amounts_from_line_items(receipt.line_items)
        if not by_category:
            return

        for category, claimed in by_category.items():
            check = await self._limits.check_claim(
                user_id=user.id,
                tax_year=receipt.tax_year,
                category=category,
                new_claimed_amount=claimed,
                exclude_receipt_id=receipt.id,
                raise_on_exceed=False,
            )

            if not receipt.be_seksyen:
                receipt.be_seksyen = await self._limits.get_be_seksyen(category=category)

            if check.would_exceed:
                receipt.status = "flagged"
                self._add_flag(
                    receipt,
                    flag_type="limit_exceeded",
                    message=(
                        f"Tuntutan {category} melebihi had pelepasan untuk kategori ini."
                    ),
                )
                return
            if check.relief_status.status == "warning":
                receipt.status = "flagged"
                self._add_flag(
                    receipt,
                    flag_type="limit_exceeded",
                    message=(
                        f"Tuntutan {category} hampir mencapai had pelepasan "
                        f"({check.relief_status.percentage:.1f}% daripada "
                        f"RM{check.relief_status.limit_amount:.2f})."
                    ),
                )
                return

    async def _apply_org_category_policy(self, receipt: Receipt, user: User) -> None:
        if user.org_id is None or not receipt.category:
            return

        policy = await self._org_policies.get_by_org_id(user.org_id)
        if policy is None:
            return

        allowed = set(policy.allowed_categories)
        if (
            receipt.category not in allowed
            and receipt.category not in NON_CLAIMABLE_CATEGORIES
        ):
            receipt.status = "flagged"
            self._add_flag(
                receipt,
                flag_type="category_not_allowed",
                message=(
                    f"Kategori {receipt.category} tidak dibenarkan oleh polisi organisasi."
                ),
            )

    async def _maybe_auto_approve(self, receipt: Receipt, user: User) -> None:
        if user.org_id is not None:
            policy = await self._org_policies.get_by_org_id(user.org_id)
            if policy is None or policy.require_hr_approval:
                return
        elif user.role != "individual":
            return
        if receipt.status == "flagged":
            return
        if receipt.category in NON_CLAIMABLE_CATEGORIES:
            return

        flag_types = {flag.flag_type for flag in receipt.flags}
        if flag_types & CRITICAL_FLAG_TYPES:
            return

        receipt.status = "approved"
        if receipt.line_items and len(receipt.line_items) >= 2:
            from app.repositories.claim_summary import ClaimSummaryRepository
            from app.services.line_item_claims import category_amounts_from_line_items

            by_category = category_amounts_from_line_items(receipt.line_items)
            claims = ClaimSummaryRepository(self._db)
            for category, amount in by_category.items():
                await claims.adjust(
                    user_id=user.id,
                    tax_year=receipt.tax_year,
                    category=category,
                    amount_delta=amount,
                    count_delta=1,
                )
            return

        if receipt.category and receipt.claimed_amount:
            from app.repositories.claim_summary import ClaimSummaryRepository

            await ClaimSummaryRepository(self._db).adjust(
                user_id=user.id,
                tax_year=receipt.tax_year,
                category=receipt.category,
                amount_delta=receipt.claimed_amount,
                count_delta=1,
            )

    async def _handle_failure(
        self,
        receipt: Receipt,
        job: ReceiptJobPayload,
        reason: str,
    ) -> None:
        receipt.category = "semak_manual"
        receipt.status = "flagged"
        receipt.scan_status = "failed"
        receipt.ai_nota = reason[:500]
        user_message = reason
        if "401" in reason or "Authentication" in reason or "OpenRouter" in reason:
            user_message = (
                "Gagal klasifikasi AI — OpenRouter API key tidak sah. "
                "Semak /admin/secrets dan jalankan health check."
            )
        self._add_flag(
            receipt,
            flag_type="manual_review",
            message=f"Gagal memproses resit: {user_message[:200]}",
        )
        await self._db.flush()

        if job.upload_session_token:
            await publish_ws_event(
                self._redis,
                upload_session_token=job.upload_session_token,
                event={
                    "type": "receipt_failed",
                    "data": {
                        "job_id": job.job_id,
                        "reason": user_message[:200],
                    },
                },
            )
            await self._publish_scan_updated(receipt, job.upload_session_token)

    def _add_flag(
        self,
        receipt: Receipt,
        *,
        flag_type: str,
        message: str,
    ) -> None:
        existing = {flag.flag_type for flag in receipt.flags}
        if flag_type in existing:
            return
        flag = ReceiptFlag(
            receipt_id=receipt.id,
            flag_type=flag_type,
            message=message,
        )
        self._db.add(flag)
        receipt.flags.append(flag)
