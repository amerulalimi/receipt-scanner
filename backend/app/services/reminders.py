from __future__ import annotations

import calendar
import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Literal

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.claim_summary import ClaimSummaryRepository
from app.repositories.org_policy import OrgPolicyRepository
from app.repositories.receipt import ReceiptRepository
from app.repositories.relief_limit import ReliefLimitRepository

CATEGORY_LABELS: dict[str, tuple[str, str]] = {
    "perubatan": ("Perubatan & Pergigian", "Medical & dental"),
    "gaya_hidup": ("Gaya Hidup", "Lifestyle"),
    "sukan": ("Peralatan Sukan", "Sports equipment"),
    "pendidikan": ("Pendidikan Diri", "Self-education"),
    "sspn": ("SSPN", "SSPN"),
    "ev_charging": ("EV Charging", "EV charging"),
}

YEAR_END_PRIORITY_CATEGORIES = frozenset({"perubatan", "pendidikan", "sspn"})


@dataclass(frozen=True)
class ReminderCandidate:
    reminder_key: str
    type: str
    severity: Literal["info", "warning"]
    title_my: str
    title_en: str
    message_my: str
    message_en: str
    action_href: str | None
    expires_at: datetime | None


class ReminderEngine:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._claims = ClaimSummaryRepository(db)
        self._limits = ReliefLimitRepository(db)
        self._receipts = ReceiptRepository(db)
        self._policies = OrgPolicyRepository(db)

    async def evaluate(self, user: User, *, now: datetime | None = None) -> list[ReminderCandidate]:
        current = now or datetime.now(UTC)
        today = current.date()
        tax_year = user.tax_year
        reminders: list[ReminderCandidate] = []

        limits = await self._limits.list_active()
        summaries = await self._claims.list_for_user(
            user_id=user.id,
            tax_year=tax_year,
            context_type="individual",
            org_id=None,
        )
        summary_by_category = {item.category: item for item in summaries}
        receipt_counts = await self._receipts.count_by_category_for_user_year(
            user_id=user.id,
            org_id=None,
            tax_year=tax_year,
        )

        reminders.extend(
            self._limit_warning_reminders(
                tax_year=tax_year,
                limits=limits,
                summary_by_category=summary_by_category,
            ),
        )
        reminders.extend(
            self._profile_incomplete_reminder(user=user, tax_year=tax_year),
        )
        reminders.extend(
            self._year_end_reminder(tax_year=tax_year, today=today),
        )
        reminders.extend(
            self._year_end_zero_category_reminders(
                tax_year=tax_year,
                today=today,
                limits=limits,
                summary_by_category=summary_by_category,
                receipt_counts=receipt_counts,
            ),
        )
        reminders.extend(
            self._calendar_nudges(
                today=today,
                tax_year=tax_year,
                summary_by_category=summary_by_category,
            ),
        )
        reminders.extend(
            await self._monthly_digest_reminder(
                user=user,
                today=today,
                tax_year=tax_year,
                limits=limits,
                summary_by_category=summary_by_category,
            ),
        )
        reminders.extend(
            await self._org_reimbursement_reminder(user=user, today=today),
        )

        return reminders

    def _limit_warning_reminders(
        self,
        *,
        tax_year: int,
        limits,
        summary_by_category,
    ) -> list[ReminderCandidate]:
        reminders: list[ReminderCandidate] = []
        for limit in limits:
            if limit.limit_amount <= 0:
                continue
            summary = summary_by_category.get(limit.category)
            claimed = summary.total_claimed if summary else Decimal("0")
            pct = float((claimed / limit.limit_amount) * 100)
            if pct < 80:
                continue
            label_my, label_en = CATEGORY_LABELS.get(
                limit.category,
                (limit.description_my or limit.category, limit.category),
            )
            reminders.append(
                ReminderCandidate(
                    reminder_key=f"limit_warning_{limit.category}_{tax_year}",
                    type="limit_warning",
                    severity="warning",
                    title_my=f"Had {label_my} hampir penuh",
                    title_en=f"{label_en} limit nearly full",
                    message_my=(
                        f"Anda telah menggunakan {pct:.0f}% daripada had {label_my}."
                    ),
                    message_en=(
                        f"You have used {pct:.0f}% of your {label_en} limit."
                    ),
                    action_href="/receipts",
                    expires_at=None,
                ),
            )
        return reminders

    def _profile_incomplete_reminder(
        self,
        *,
        user: User,
        tax_year: int,
    ) -> list[ReminderCandidate]:
        if user.tax_bracket is not None and user.full_name:
            return []
        return [
            ReminderCandidate(
                reminder_key=f"profile_incomplete_{tax_year}",
                type="profile_incomplete",
                severity="info",
                title_my="Profil tidak lengkap",
                title_en="Profile incomplete",
                message_my=(
                    "Tetapkan bracket cukai anda untuk pengiraan penjimatan yang tepat."
                ),
                message_en=(
                    "Set your tax bracket for accurate savings calculations."
                ),
                action_href="/settings",
                expires_at=None,
            ),
        ]

    def _year_end_reminder(
        self,
        *,
        tax_year: int,
        today: date,
    ) -> list[ReminderCandidate]:
        if today.month < 11:
            return []
        return [
            ReminderCandidate(
                reminder_key=f"year_end_{tax_year}",
                type="year_end",
                severity="warning",
                title_my=f"Tahun cukai {tax_year} akan berakhir",
                title_en=f"Tax year {tax_year} is ending",
                message_my=(
                    f"Pastikan semua resit dimuat naik sebelum 31 Disember {tax_year}."
                ),
                message_en=(
                    f"Make sure all receipts are uploaded before 31 December {tax_year}."
                ),
                action_href="/receipts",
                expires_at=None,
            ),
        ]

    def _year_end_zero_category_reminders(
        self,
        *,
        tax_year: int,
        today: date,
        limits,
        summary_by_category,
        receipt_counts: dict[str, int],
    ) -> list[ReminderCandidate]:
        if not self._is_year_end_window(tax_year, today):
            return []

        reminders: list[ReminderCandidate] = []
        deadline = date(tax_year + 1, 2, 28)

        for limit in limits:
            if limit.category not in YEAR_END_PRIORITY_CATEGORIES:
                continue

            count = receipt_counts.get(limit.category, 0)
            claimed = summary_by_category.get(limit.category)
            if count > 0 or (claimed and claimed.receipt_count > 0):
                continue

            label_my, label_en = CATEGORY_LABELS.get(
                limit.category,
                (limit.category, limit.category),
            )
            reminders.append(
                ReminderCandidate(
                    reminder_key=f"year_end:zero:{limit.category}:{tax_year}",
                    type="year_end_zero_category",
                    severity="warning",
                    title_my=f"Tiada resit {label_my}",
                    title_en=f"No {label_en} receipts",
                    message_my=(
                        f"Anda belum upload sebarang resit {label_my.lower()} "
                        f"untuk tahun cukai {tax_year}. Had pelepasan: "
                        f"RM{limit.limit_amount:,.2f}. Semak sebelum {deadline.strftime('%d/%m/%Y')}."
                    ),
                    message_en=(
                        f"You have not uploaded any {label_en.lower()} receipts "
                        f"for tax year {tax_year}. Relief limit: "
                        f"RM{limit.limit_amount:,.2f}. Review before {deadline.strftime('%d/%m/%Y')}."
                    ),
                    action_href="/dashboard",
                    expires_at=datetime(deadline.year, deadline.month, deadline.day, 23, 59, tzinfo=UTC),
                ),
            )

        return reminders

    def _calendar_nudges(
        self,
        *,
        today: date,
        tax_year: int,
        summary_by_category,
    ) -> list[ReminderCandidate]:
        reminders: list[ReminderCandidate] = []
        month_key = f"{today.year}-{today.month:02d}"

        if today.month == 1:
            sspn = summary_by_category.get("sspn")
            if sspn is None or sspn.total_claimed <= 0:
                reminders.append(
                    ReminderCandidate(
                        reminder_key=f"calendar:sspn:{month_key}",
                        type="calendar_nudge",
                        severity="info",
                        title_my="Masa untuk resit SSPN",
                        title_en="Time for SSPN receipts",
                        message_my=(
                            "Januari — pastikan resit caruman SSPN tahun ini "
                            "dimuat naik untuk tuntutan pelepasan."
                        ),
                        message_en=(
                            "January — upload your SSPN contribution receipts "
                            "for this tax year."
                        ),
                        action_href="/dashboard",
                        expires_at=datetime(today.year, today.month, 28, 23, 59, tzinfo=UTC),
                    ),
                )

        if today.month in (1, 6):
            pendidikan = summary_by_category.get("pendidikan")
            if pendidikan is None or pendidikan.total_claimed <= 0:
                month_label_my = "permulaan tahun persekolahan" if today.month == 1 else "pertengahan tahun"
                month_label_en = "school year start" if today.month == 1 else "mid-year school term"
                reminders.append(
                    ReminderCandidate(
                        reminder_key=f"calendar:pendidikan:{month_key}",
                        type="calendar_nudge",
                        severity="info",
                        title_my="Ingatkan resit pendidikan",
                        title_en="Education receipt reminder",
                        message_my=(
                            f"{month_label_my.capitalize()} — muat naik resit "
                            "kursus/pendidikan diri yang layak tuntutan."
                        ),
                        message_en=(
                            f"{month_label_en.capitalize()} — upload eligible "
                            "self-education course receipts."
                        ),
                        action_href="/dashboard",
                        expires_at=datetime(today.year, today.month, 28, 23, 59, tzinfo=UTC),
                    ),
                )

        return reminders

    async def _monthly_digest_reminder(
        self,
        *,
        user: User,
        today: date,
        tax_year: int,
        limits,
        summary_by_category,
    ) -> list[ReminderCandidate]:
        month_start = date(today.year, today.month, 1)
        last_day = calendar.monthrange(today.year, today.month)[1]
        month_end = date(today.year, today.month, last_day)

        total, _by_month = await self._receipts.sum_claimed_this_month(
            user_id=user.id,
            org_id=None,
            tax_year=tax_year,
            month_start=month_start,
            month_end=month_end,
        )

        top_category = None
        top_remaining = Decimal("0")
        top_limit = Decimal("0")
        top_label_my = ""
        top_label_en = ""

        for limit in limits:
            summary = summary_by_category.get(limit.category)
            claimed = summary.total_claimed if summary else Decimal("0")
            remaining = max(Decimal("0"), limit.limit_amount - claimed)
            if remaining > top_remaining:
                top_remaining = remaining
                top_limit = limit.limit_amount
                top_category = limit.category
                top_label_my, top_label_en = CATEGORY_LABELS.get(
                    limit.category,
                    (limit.description_my or limit.category, limit.category),
                )

        if total <= 0 and top_remaining <= 0:
            return []

        return [
            ReminderCandidate(
                reminder_key=f"digest:{today.year}-{today.month:02d}",
                type="monthly_digest",
                severity="info",
                title_my="Rumusan bulan ini",
                title_en="This month's summary",
                message_my=(
                    f"Anda telah claim RM{total:,.2f} bulan ini. "
                    f"RM{top_remaining:,.2f} lagi untuk had {top_label_my.lower()} "
                    f"(daripada RM{top_limit:,.2f})."
                    if top_category
                    else f"Anda telah claim RM{total:,.2f} bulan ini."
                ),
                message_en=(
                    f"You have claimed RM{total:,.2f} this month. "
                    f"RM{top_remaining:,.2f} remaining for {top_label_en.lower()} "
                    f"(of RM{top_limit:,.2f})."
                    if top_category
                    else f"You have claimed RM{total:,.2f} this month."
                ),
                action_href="/dashboard",
                expires_at=datetime(
                    today.year,
                    today.month,
                    last_day,
                    23,
                    59,
                    tzinfo=UTC,
                ),
            ),
        ]

    async def _org_reimbursement_reminder(
        self,
        *,
        user: User,
        today: date,
    ) -> list[ReminderCandidate]:
        if user.account_type != "corporate" or user.org_id is None:
            return []

        policy = await self._policies.get_by_org_id(user.org_id)
        if policy is None or not policy.require_hr_approval:
            return []

        last_day = calendar.monthrange(today.year, today.month)[1]
        if today.day < last_day - 4:
            return []

        return [
            ReminderCandidate(
                reminder_key=f"org:reimbursement:{today.year}-{today.month:02d}",
                type="reimbursement_window",
                severity="warning",
                title_my="Tempoh tuntutan hampir tamat",
                title_en="Reimbursement window closing",
                message_my=(
                    f"Hantar resit anda sebelum akhir bulan ({last_day} "
                    f"{today.strftime('%B')}) untuk kelulusan HR."
                ),
                message_en=(
                    f"Submit your receipts before month-end ({last_day} "
                    f"{today.strftime('%B')}) for HR approval."
                ),
                action_href="/dashboard/receipts",
                expires_at=datetime(today.year, today.month, last_day, 23, 59, tzinfo=UTC),
            ),
        ]

    @staticmethod
    def _is_year_end_window(tax_year: int, today: date) -> bool:
        reminder_start = date(tax_year, 12, 1)
        deadline = date(tax_year + 1, 2, 28)
        return reminder_start <= today <= deadline

    async def build_monthly_digest_email(
        self,
        user: User,
        *,
        today: date | None = None,
    ) -> tuple[str, str]:
        current = today or datetime.now(UTC).date()
        tax_year = user.tax_year
        month_start = date(current.year, current.month, 1)
        last_day = calendar.monthrange(current.year, current.month)[1]
        month_end = date(current.year, current.month, last_day)

        total, by_month = await self._receipts.sum_claimed_this_month(
            user_id=user.id,
            org_id=None,
            tax_year=tax_year,
            month_start=month_start,
            month_end=month_end,
        )

        limits = await self._limits.list_active()
        summaries = await self._claims.list_for_user(
            user_id=user.id,
            tax_year=tax_year,
            context_type="individual",
            org_id=None,
        )
        summary_by_category = {item.category: item for item in summaries}

        lines_my: list[str] = [
            f"Rumusan Resit.my — {current.strftime('%B %Y')}",
            f"Anda telah claim RM{total:,.2f} bulan ini.",
            "",
        ]
        lines_en: list[str] = [
            f"Resit.my summary — {current.strftime('%B %Y')}",
            f"You have claimed RM{total:,.2f} this month.",
            "",
        ]

        for limit in limits:
            label_my, label_en = CATEGORY_LABELS.get(
                limit.category,
                (limit.description_my or limit.category, limit.category),
            )
            summary = summary_by_category.get(limit.category)
            claimed_year = float(summary.total_claimed) if summary else 0.0
            remaining = max(0.0, float(limit.limit_amount) - claimed_year)
            month_claimed = by_month.get(limit.category, 0.0)
            if month_claimed <= 0 and remaining <= 0:
                continue
            lines_my.append(
                f"• {label_my}: RM{month_claimed:,.2f} bulan ini, "
                f"RM{remaining:,.2f} lagi untuk had tahunan."
            )
            lines_en.append(
                f"• {label_en}: RM{month_claimed:,.2f} this month, "
                f"RM{remaining:,.2f} remaining for the annual limit."
            )

        lines_my.append("")
        lines_my.append(f"Buka dashboard: /dashboard")
        lines_en.append("")
        lines_en.append("Open your dashboard: /dashboard")

        return "\n".join(lines_my), "\n".join(lines_en)
