from __future__ import annotations

import secrets
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AppError
from app.core.security import hash_password
from app.models.invite_token import InviteToken
from app.models.user import User
from app.repositories.invite_token import InviteTokenRepository
from app.repositories.org_policy import OrgPolicyRepository
from app.repositories.organisation import OrganisationRepository
from app.repositories.receipt import ReceiptRepository
from app.repositories.relief_limit import ReliefLimitRepository
from app.repositories.user import UserRepository
from app.schemas.org import (
    InviteAcceptRequest,
    InviteAcceptResponseData,
    InviteCreateResponseData,
    InviteEmployeesRequest,
    InviteHrAdminRequest,
    InviteValidateResponseData,
    OrgEmployeeBulkImportRequest,
    OrgEmployeeBulkImportResponse,
    OrgEmployeeItem,
    OrgEmployeeListResponse,
    OrgEmployeeUpdateRequest,
    OrgMeResponseData,
    OrgPendingReceiptItem,
    OrgPendingReceiptListResponse,
    OrgPolicyData,
    OrgPolicyUpdateRequest,
    OrgRegisterRequest,
    OrgRegisterResponseData,
)
from app.services.email import send_invite_email
from app.services.session import create_session
from app.services.audit import AuditService


def normalize_email_domain(domain: str) -> str:
    value = domain.strip().lower()
    if value.startswith("@"):
        value = value[1:]
    return value


def email_matches_domain(email: str, domain: str) -> bool:
    return email.split("@")[-1].lower() == domain.lower()


class OrgService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._orgs = OrganisationRepository(db)
        self._policies = OrgPolicyRepository(db)
        self._users = UserRepository(db)
        self._invites = InviteTokenRepository(db)
        self._relief_limits = ReliefLimitRepository(db)
        self._receipts = ReceiptRepository(db)

    async def register_org(
        self,
        user: User,
        payload: OrgRegisterRequest,
    ) -> OrgRegisterResponseData:
        if user.org_id is not None:
            raise AppError(
                message="Anda sudah berada dalam organisasi.",
                code="VALIDATION_ERROR",
                status_code=422,
            )
        if user.account_type != "corporate":
            raise AppError(
                message="Hanya akaun korporat boleh mendaftar organisasi.",
                code="FORBIDDEN",
                status_code=403,
            )
        if user.role != "individual":
            raise AppError(
                message="Hanya akaun individu boleh mendaftar organisasi.",
                code="VALIDATION_ERROR",
                status_code=422,
            )

        email_domain = normalize_email_domain(payload.email_domain)
        if not email_matches_domain(user.email, email_domain):
            raise AppError(
                message=(
                    f"E-mel anda mesti menggunakan domain @{email_domain} "
                    "untuk mendaftar organisasi ini."
                ),
                code="VALIDATION_ERROR",
                status_code=422,
            )

        existing_ssm = await self._orgs.get_by_ssm(payload.ssm_number.strip())
        if existing_ssm is not None:
            raise AppError(
                message="Nombor SSM ini sudah didaftarkan.",
                code="VALIDATION_ERROR",
                status_code=422,
            )

        existing_domain = await self._orgs.get_by_email_domain(email_domain)
        if existing_domain is not None:
            raise AppError(
                message="Domain e-mel ini sudah didaftarkan.",
                code="VALIDATION_ERROR",
                status_code=422,
            )

        org = await self._orgs.create_with_policy(
            name=payload.name,
            ssm_number=payload.ssm_number,
            email_domain=email_domain,
            updated_by=user.id,
        )
        await self._users.assign_to_org(
            user.id,
            org_id=org.id,
            role="superadmin",
        )

        await AuditService(self._db).log(
            action="org.registered",
            user_id=user.id,
            org_id=org.id,
            resource="organisation",
            resource_id=org.id,
            metadata={"name": org.name, "email_domain": org.email_domain},
        )

        return OrgRegisterResponseData(
            org_id=org.id,
            name=org.name,
            email_domain=org.email_domain,
            domain_verified=org.domain_verified,
        )

    async def get_my_org(self, user: User) -> OrgMeResponseData:
        if user.account_type != "corporate":
            raise AppError(
                message="Akses organisasi hanya untuk akaun korporat.",
                code="FORBIDDEN",
                status_code=403,
            )
        if user.org_id is None:
            raise AppError(
                message="Anda bukan ahli organisasi.",
                code="NOT_FOUND",
                status_code=404,
            )

        org = await self._orgs.get_by_id_with_policy(user.org_id)
        if org is None or org.org_policy is None:
            raise AppError(
                message="Organisasi tidak dijumpai.",
                code="NOT_FOUND",
                status_code=404,
            )

        total_employees = await self._orgs.count_employees(org.id)
        policy = org.org_policy

        return OrgMeResponseData(
            org_id=org.id,
            name=org.name,
            ssm_number=org.ssm_number,
            email_domain=org.email_domain,
            domain_verified=org.domain_verified,
            total_employees=total_employees,
            policy=OrgPolicyData(
                allowed_categories=list(policy.allowed_categories),
                require_hr_approval=policy.require_hr_approval,
                max_receipts_per_month=policy.max_receipts_per_month,
                tax_year=policy.tax_year,
            ),
        )

    async def update_policy(
        self,
        user: User,
        payload: OrgPolicyUpdateRequest,
    ) -> OrgPolicyData:
        if user.org_id is None:
            raise AppError(
                message="Organisasi tidak dijumpai.",
                code="NOT_FOUND",
                status_code=404,
            )

        policy = await self._policies.get_by_org_id(user.org_id)
        if policy is None:
            raise AppError(
                message="Dasar organisasi tidak dijumpai.",
                code="NOT_FOUND",
                status_code=404,
            )

        if payload.allowed_categories is not None:
            active_categories = {
                item.category for item in await self._relief_limits.list_active()
            }
            invalid = [
                c for c in payload.allowed_categories if c not in active_categories
            ]
            if invalid:
                raise AppError(
                    message=f"Kategori tidak sah: {', '.join(invalid)}",
                    code="VALIDATION_ERROR",
                    status_code=422,
                )

        updated = await self._policies.update(
            policy,
            allowed_categories=payload.allowed_categories,
            require_hr_approval=payload.require_hr_approval,
            max_receipts_per_month=payload.max_receipts_per_month,
            tax_year=payload.tax_year,
            updated_by=user.id,
        )

        return OrgPolicyData(
            allowed_categories=list(updated.allowed_categories),
            require_hr_approval=updated.require_hr_approval,
            max_receipts_per_month=updated.max_receipts_per_month,
            tax_year=updated.tax_year,
        )

    async def list_employees(
        self,
        user: User,
        *,
        search: str | None,
        status: str | None,
        page: int,
        limit: int,
    ) -> OrgEmployeeListResponse:
        if user.org_id is None:
            raise AppError(
                message="Organisasi tidak dijumpai.",
                code="NOT_FOUND",
                status_code=404,
            )

        rows, total = await self._users.list_org_employees(
            user.org_id,
            search=search,
            status=status,
            page=page,
            limit=limit,
        )

        items = [
            OrgEmployeeItem(
                user_id=member.id,
                full_name=member.full_name,
                email=member.email,
                role=member.role,
                is_active=member.is_active,
                receipts_count=receipts_count,
                total_claimed=float(total_claimed),
                pending_count=pending_count,
            )
            for member, receipts_count, total_claimed, pending_count in rows
        ]

        return OrgEmployeeListResponse(
            items=items,
            total=total,
            page=page,
            limit=limit,
        )

    async def list_pending_receipts(
        self,
        user: User,
        *,
        tax_year: int | None,
        page: int,
        limit: int,
    ) -> OrgPendingReceiptListResponse:
        if user.org_id is None:
            raise AppError(
                message="Organisasi tidak dijumpai.",
                code="NOT_FOUND",
                status_code=404,
            )

        rows, total = await self._receipts.list_pending_for_org(
            org_id=user.org_id,
            tax_year=tax_year,
            page=page,
            limit=limit,
        )

        items = [
            OrgPendingReceiptItem(
                id=receipt.id,
                user_id=receipt.user_id,
                employee_name=employee.full_name,
                employee_email=employee.email,
                merchant_name=receipt.merchant_name,
                receipt_date=receipt.receipt_date,
                claimed_amount=float(receipt.claimed_amount)
                if receipt.claimed_amount is not None
                else None,
                category=receipt.category,
                be_seksyen=receipt.be_seksyen,
                status=receipt.status,
                scan_status=receipt.scan_status,
                created_at=receipt.created_at,
            )
            for receipt, employee in rows
        ]

        return OrgPendingReceiptListResponse(
            items=items,
            total=total,
            page=page,
            limit=limit,
        )

    async def update_employee(
        self,
        user: User,
        employee_id: uuid.UUID,
        payload: OrgEmployeeUpdateRequest,
    ) -> OrgEmployeeItem:
        if user.org_id is None:
            raise AppError(
                message="Organisasi tidak dijumpai.",
                code="NOT_FOUND",
                status_code=404,
            )

        if employee_id == user.id:
            raise AppError(
                message="Anda tidak boleh mengubah status akaun sendiri.",
                code="VALIDATION_ERROR",
                status_code=422,
            )

        employee = await self._users.get_org_member(user.org_id, employee_id)
        if employee is None:
            raise AppError(
                message="Pekerja tidak dijumpai.",
                code="NOT_FOUND",
                status_code=404,
            )

        if employee.role == "superadmin" and user.role != "superadmin":
            raise AppError(
                message="Hanya superadmin boleh mengurus superadmin lain.",
                code="FORBIDDEN",
                status_code=403,
            )

        updated = await self._users.set_active(
            employee_id,
            is_active=payload.is_active,
        )
        if updated is None:
            raise AppError(
                message="Pekerja tidak dijumpai.",
                code="NOT_FOUND",
                status_code=404,
            )

        rows, _ = await self._users.list_org_employees(
            user.org_id,
            search=None,
            status=None,
            page=1,
            limit=1,
        )
        # Re-fetch stats for this employee only via list with search by email
        rows, _ = await self._users.list_org_employees(
            user.org_id,
            search=updated.email,
            status=None,
            page=1,
            limit=1,
        )
        if rows:
            member, receipts_count, total_claimed, pending_count = rows[0]
            return OrgEmployeeItem(
                user_id=member.id,
                full_name=member.full_name,
                email=member.email,
                role=member.role,
                is_active=member.is_active,
                receipts_count=receipts_count,
                total_claimed=float(total_claimed),
                pending_count=pending_count,
            )

        return OrgEmployeeItem(
            user_id=updated.id,
            full_name=updated.full_name,
            email=updated.email,
            role=updated.role,
            is_active=updated.is_active,
            receipts_count=0,
            total_claimed=0.0,
            pending_count=0,
        )

    async def remove_employee_from_org(
        self,
        user: User,
        employee_id: uuid.UUID,
    ) -> None:
        if user.org_id is None:
            raise AppError(
                message="Organisasi tidak dijumpai.",
                code="NOT_FOUND",
                status_code=404,
            )

        if employee_id == user.id:
            raise AppError(
                message="Anda tidak boleh mengeluarkan diri sendiri.",
                code="VALIDATION_ERROR",
                status_code=422,
            )

        employee = await self._users.get_org_member(user.org_id, employee_id)
        if employee is None:
            raise AppError(
                message="Pekerja tidak dijumpai.",
                code="NOT_FOUND",
                status_code=404,
            )

        if employee.role == "superadmin":
            raise AppError(
                message="Superadmin organisasi tidak boleh dikeluarkan.",
                code="FORBIDDEN",
                status_code=403,
            )

        removed = await self._users.remove_from_org(employee_id)
        if removed is None:
            raise AppError(
                message="Pekerja tidak dijumpai.",
                code="NOT_FOUND",
                status_code=404,
            )

        await AuditService(self._db).log(
            action="org.employee_removed",
            user_id=user.id,
            org_id=user.org_id,
            resource="user",
            resource_id=employee_id,
            metadata={"email": removed.email},
        )

    def _invite_expires_at(self) -> datetime:
        return datetime.now(UTC) + timedelta(seconds=settings.invite_ttl_seconds)

    def _build_invite_url(self, token: str) -> str:
        return f"{settings.frontend_url.rstrip('/')}/join/{token}"

    async def _create_invite(
        self,
        *,
        org_id: uuid.UUID,
        invited_by: uuid.UUID,
        role: str,
        invite_type: str,
        invited_email: str | None,
    ) -> InviteToken:
        token = secrets.token_urlsafe(32)
        invite = InviteToken(
            token=token,
            org_id=org_id,
            invited_email=invited_email.lower() if invited_email else None,
            invited_by=invited_by,
            role=role,
            invite_type=invite_type,
            expires_at=self._invite_expires_at(),
        )
        return await self._invites.create(invite)

    async def invite_hr_admin(
        self,
        user: User,
        payload: InviteHrAdminRequest,
    ) -> InviteCreateResponseData:
        if user.org_id is None:
            raise AppError(
                message="Organisasi tidak dijumpai.",
                code="NOT_FOUND",
                status_code=404,
            )

        org = await self._orgs.get_by_id(user.org_id)
        if org is None:
            raise AppError(
                message="Organisasi tidak dijumpai.",
                code="NOT_FOUND",
                status_code=404,
            )

        email = payload.email.lower().strip()
        if not email_matches_domain(email, org.email_domain):
            raise AppError(
                message=f"E-mel mesti menggunakan domain @{org.email_domain}.",
                code="VALIDATION_ERROR",
                status_code=422,
            )

        existing = await self._users.get_by_email(email)
        if existing is not None:
            raise AppError(
                message="E-mel ini sudah didaftarkan.",
                code="VALIDATION_ERROR",
                status_code=422,
            )

        invite = await self._create_invite(
            org_id=org.id,
            invited_by=user.id,
            role="hr_admin",
            invite_type="email",
            invited_email=email,
        )
        invite_url = self._build_invite_url(invite.token)
        await send_invite_email(email=email, invite_url=invite_url, org_name=org.name)

        return InviteCreateResponseData(
            invite_id=invite.id,
            email=email,
            type="email",
            invite_url=invite_url,
            expires_at=invite.expires_at,
            invited_count=1,
        )

    async def invite_employees(
        self,
        user: User,
        payload: InviteEmployeesRequest,
    ) -> InviteCreateResponseData:
        if user.org_id is None:
            raise AppError(
                message="Organisasi tidak dijumpai.",
                code="NOT_FOUND",
                status_code=404,
            )

        org = await self._orgs.get_by_id(user.org_id)
        if org is None:
            raise AppError(
                message="Organisasi tidak dijumpai.",
                code="NOT_FOUND",
                status_code=404,
            )

        expires_at = self._invite_expires_at()

        if payload.type == "link":
            invite = await self._create_invite(
                org_id=org.id,
                invited_by=user.id,
                role="employee",
                invite_type="link",
                invited_email=None,
            )
            invite_url = self._build_invite_url(invite.token)
            await send_invite_email(
                email=None,
                invite_url=invite_url,
                org_name=org.name,
            )
            return InviteCreateResponseData(
                type="link",
                invite_url=invite_url,
                expires_at=invite.expires_at,
                invited_count=1,
            )

        if not payload.emails:
            raise AppError(
                message="Sekurang-kurangnya satu e-mel diperlukan.",
                code="VALIDATION_ERROR",
                status_code=422,
            )

        invited_count = 0
        last_invite: InviteToken | None = None
        for raw_email in payload.emails:
            email = raw_email.lower().strip()
            if not email:
                continue
            if not email_matches_domain(email, org.email_domain):
                raise AppError(
                    message=f"E-mel {email} mesti menggunakan domain @{org.email_domain}.",
                    code="VALIDATION_ERROR",
                    status_code=422,
                )
            existing = await self._users.get_by_email(email)
            if existing is not None:
                raise AppError(
                    message=f"E-mel {email} sudah didaftarkan.",
                    code="VALIDATION_ERROR",
                    status_code=422,
                )
            last_invite = await self._create_invite(
                org_id=org.id,
                invited_by=user.id,
                role="employee",
                invite_type="email",
                invited_email=email,
            )
            invite_url = self._build_invite_url(last_invite.token)
            await send_invite_email(
                email=email,
                invite_url=invite_url,
                org_name=org.name,
            )
            invited_count += 1

        if invited_count == 0 or last_invite is None:
            raise AppError(
                message="Tiada jemputan dihantar.",
                code="VALIDATION_ERROR",
                status_code=422,
            )

        return InviteCreateResponseData(
            invite_id=last_invite.id,
            email=last_invite.invited_email,
            type="email",
            invite_url=self._build_invite_url(last_invite.token),
            expires_at=last_invite.expires_at,
            invited_count=invited_count,
        )

    async def validate_invite(self, token: str) -> InviteValidateResponseData:
        invite = await self._invites.get_by_token(token)
        if invite is None or invite.used:
            return InviteValidateResponseData(valid=False)

        if invite.expires_at < datetime.now(UTC):
            return InviteValidateResponseData(valid=False)

        org_name = invite.organisation.name if invite.organisation else None
        return InviteValidateResponseData(
            valid=True,
            org_name=org_name,
            role=invite.role,
            invited_email=invite.invited_email,
            expires_at=invite.expires_at,
        )

    async def accept_invite(
        self,
        payload: InviteAcceptRequest,
        *,
        client_ip: str,
        user_agent: str,
        redis,
    ) -> tuple[InviteAcceptResponseData, str]:
        invite = await self._invites.get_by_token(payload.token)
        if invite is None or invite.used:
            raise AppError(
                message="Jemputan tidak sah atau telah digunakan.",
                code="VALIDATION_ERROR",
                status_code=422,
            )

        if invite.expires_at < datetime.now(UTC):
            raise AppError(
                message="Jemputan telah tamat tempoh.",
                code="VALIDATION_ERROR",
                status_code=422,
            )

        email = payload.email.lower().strip()
        if invite.invited_email and invite.invited_email != email:
            raise AppError(
                message="E-mel tidak sepadan dengan jemputan.",
                code="VALIDATION_ERROR",
                status_code=422,
            )

        org = invite.organisation
        if org is None:
            raise AppError(
                message="Organisasi tidak dijumpai.",
                code="NOT_FOUND",
                status_code=404,
            )

        if not email_matches_domain(email, org.email_domain):
            raise AppError(
                message=f"E-mel mesti menggunakan domain @{org.email_domain}.",
                code="VALIDATION_ERROR",
                status_code=422,
            )

        existing = await self._users.get_by_email(email)
        if existing is not None:
            raise AppError(
                message="E-mel ini sudah didaftarkan.",
                code="VALIDATION_ERROR",
                status_code=422,
            )

        user = await self._users.create(
            email=email,
            password_hash=hash_password(payload.password),
            full_name=payload.full_name.strip(),
            role=invite.role,
            org_id=org.id,
            account_type="corporate",
        )
        await self._invites.mark_used(invite, used_by=user.id)

        session_id = await create_session(
            redis,
            user_id=user.id,
            role=user.role,
            org_id=user.org_id,
            email=user.email,
            ip=client_ip,
            user_agent=user_agent,
        )

        return (
            InviteAcceptResponseData(
                user_id=user.id,
                email=user.email,
                role=user.role,
                org_id=org.id,
            ),
            session_id,
        )

    async def bulk_import_employees(
        self,
        user: User,
        payload: OrgEmployeeBulkImportRequest,
    ) -> OrgEmployeeBulkImportResponse:
        emails = [row.email.lower().strip() for row in payload.employees if row.email.strip()]
        invite_result = await self.invite_employees(
            user,
            InviteEmployeesRequest(type="email", emails=emails),
        )
        return OrgEmployeeBulkImportResponse(
            invited_count=invite_result.invited_count,
            invite_url=invite_result.invite_url,
        )
