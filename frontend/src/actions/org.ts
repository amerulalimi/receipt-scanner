"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import type { OrgActionState } from "@/actions/org.types";
import { initialOrgActionState } from "@/actions/org.types";
import {
  bulkApproveOrgPendingWithFastApi,
  bulkImportEmployeesWithFastApi,
  inviteEmployeesWithFastApi,
  inviteHrAdminWithFastApi,
  registerOrgWithFastApi,
  removeOrgEmployeeWithFastApi,
  reviewReceiptWithFastApi,
  updateOrgEmployeeWithFastApi,
  updateOrgPolicyWithFastApi,
} from "@/lib/api/org";
import {
  parseOrgEmployeeRemoveFormData,
  parseOrgEmployeeStatusFormData,
  parseOrgBulkImportFormData,
  parseOrgInviteEmployeesFormData,
  parseOrgInviteHrAdminFormData,
  parseOrgPolicyUpdateFormData,
  parseOrgRegisterFormData,
} from "@/lib/validations/org";
import { parseReceiptReviewFormData } from "@/lib/validations/receipt";

function flattenFieldErrors(
  fieldErrors: Record<string, string[] | undefined>,
): Record<string, string[]> {
  return Object.fromEntries(
    Object.entries(fieldErrors)
      .filter((entry): entry is [string, string[]] => !!entry[1]?.length)
      .map(([key, messages]) => [key, messages]),
  );
}

function revalidateOrgPaths() {
  revalidatePath("/dashboard/org");
}

export async function registerOrgAction(
  _prevState: OrgActionState,
  formData: FormData,
): Promise<OrgActionState> {
  const parsed = parseOrgRegisterFormData(formData);

  if (!parsed.success) {
    return {
      fieldErrors: flattenFieldErrors(parsed.error.flatten().fieldErrors),
    };
  }

  const { body } = await registerOrgWithFastApi(parsed.data);

  if (!body.success) {
    return { error: body.message };
  }

  revalidateOrgPaths();
  redirect("/dashboard/org");
}

export async function updateOrgPolicyAction(
  _prevState: OrgActionState,
  formData: FormData,
): Promise<OrgActionState> {
  const parsed = parseOrgPolicyUpdateFormData(formData);

  if (!parsed.success) {
    return {
      fieldErrors: flattenFieldErrors(parsed.error.flatten().fieldErrors),
    };
  }

  const { body } = await updateOrgPolicyWithFastApi(parsed.data);

  if (!body.success) {
    return { error: body.message };
  }

  revalidateOrgPaths();
  return { success: true, message: "Organization policy updated." };
}

export async function inviteEmployeesAction(
  _prevState: OrgActionState,
  formData: FormData,
): Promise<OrgActionState> {
  const parsed = parseOrgInviteEmployeesFormData(formData);

  if (!parsed.success) {
    return {
      fieldErrors: flattenFieldErrors(parsed.error.flatten().fieldErrors),
    };
  }

  const payload =
    parsed.data.type === "link"
      ? { type: "link" as const }
      : { type: "email" as const, emails: parsed.data.emails };

  const { body } = await inviteEmployeesWithFastApi(payload);

  if (!body.success) {
    return { error: body.message };
  }

  revalidateOrgPaths();
  return {
    success: true,
    message:
      parsed.data.type === "link"
        ? "Invite link generated. Copy the link below."
        : `${body.data?.invited_count ?? 1} invitation(s) sent (dev: check backend log).`,
    inviteUrl: body.data?.invite_url ?? undefined,
  };
}

export async function inviteHrAdminAction(
  _prevState: OrgActionState,
  formData: FormData,
): Promise<OrgActionState> {
  const parsed = parseOrgInviteHrAdminFormData(formData);

  if (!parsed.success) {
    return {
      fieldErrors: flattenFieldErrors(parsed.error.flatten().fieldErrors),
    };
  }

  const { body } = await inviteHrAdminWithFastApi({
    email: parsed.data.email.toLowerCase(),
  });

  if (!body.success) {
    return { error: body.message };
  }

  revalidateOrgPaths();
  return {
    success: true,
    message: "HR admin invitation sent (dev: check backend log).",
    inviteUrl: body.data?.invite_url ?? undefined,
  };
}

export async function updateOrgEmployeeAction(
  _prevState: OrgActionState,
  formData: FormData,
): Promise<OrgActionState> {
  const parsed = parseOrgEmployeeStatusFormData(formData);

  if (!parsed.success) {
    return { error: "Invalid request." };
  }

  const { body } = await updateOrgEmployeeWithFastApi(parsed.data.user_id, {
    is_active: parsed.data.is_active,
  });

  if (!body.success) {
    return { error: body.message };
  }

  revalidateOrgPaths();
  return {
    success: true,
    message: parsed.data.is_active
      ? "Employee activated."
      : "Employee deactivated.",
  };
}

export async function removeOrgEmployeeAction(
  _prevState: OrgActionState,
  formData: FormData,
): Promise<OrgActionState> {
  const parsed = parseOrgEmployeeRemoveFormData(formData);

  if (!parsed.success) {
    return { error: "Invalid request." };
  }

  const { body } = await removeOrgEmployeeWithFastApi(parsed.data.user_id);

  if (!body.success) {
    return { error: body.message };
  }

  revalidateOrgPaths();
  return {
    success: true,
    message: body.message ?? "Employee removed from organization.",
  };
}

export async function reviewOrgReceiptAction(
  _prevState: OrgActionState,
  formData: FormData,
): Promise<OrgActionState> {
  const parsed = parseReceiptReviewFormData(formData);

  if (!parsed.success) {
    return {
      error: parsed.error.issues[0]?.message ?? "Invalid request.",
    };
  }

  const { body } = await reviewReceiptWithFastApi(parsed.data.receipt_id, {
    action: parsed.data.action,
    comment: parsed.data.comment,
  });

  if (!body.success) {
    return { error: body.message };
  }

  revalidateOrgPaths();
  revalidatePath("/dashboard");
  revalidatePath("/dashboard/receipts");

  return {
    success: true,
    message:
      parsed.data.action === "approve"
        ? "Receipt approved."
        : "Receipt rejected.",
  };
}

export async function bulkApproveOrgPendingAction(
  _prevState: OrgActionState,
  formData: FormData,
): Promise<OrgActionState> {
  const taxYearRaw = formData.get("tax_year");
  const taxYear =
    typeof taxYearRaw === "string" && taxYearRaw.length > 0
      ? Number.parseInt(taxYearRaw, 10)
      : undefined;

  const { body } = await bulkApproveOrgPendingWithFastApi(
    Number.isNaN(taxYear) ? undefined : taxYear,
  );

  if (!body.success) {
    return { error: body.message };
  }

  revalidateOrgPaths();
  revalidatePath("/dashboard");

  const { approved_count, skipped_count } = body.data;
  return {
    success: true,
    message: `${approved_count} receipt(s) approved${skipped_count > 0 ? `, ${skipped_count} skipped` : ""}.`,
  };
}

export async function bulkImportEmployeesAction(
  _prevState: OrgActionState,
  formData: FormData,
): Promise<OrgActionState> {
  const parsed = parseOrgBulkImportFormData(formData);

  if (!parsed.success) {
    return {
      fieldErrors: flattenFieldErrors(parsed.error.flatten().fieldErrors),
      error: parsed.error.issues[0]?.message ?? "Invalid employee data.",
    };
  }

  const { body } = await bulkImportEmployeesWithFastApi({
    employees: parsed.data.employees,
  });

  if (!body.success) {
    return { error: body.message };
  }

  revalidateOrgPaths();
  return {
    success: true,
    message: `${body.data.invited_count} employee(s) invited.`,
    inviteUrl: body.data.invite_url ?? undefined,
  };
}

export { initialOrgActionState };
