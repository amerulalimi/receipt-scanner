"use server";

import { revalidatePath } from "next/cache";

import type { AdminActionState } from "@/actions/admin-config";
import { bulkUpsertSettingsWithFastApi } from "@/lib/api/admin-config";
import {
  createReliefLimitWithFastApi,
  deactivateReliefLimitWithFastApi,
  purgeRetentionWithFastApi,
  updateReliefLimitWithFastApi,
} from "@/lib/api/admin-system";
import {
  parseReliefLimitCreateFormData,
  parseReliefLimitUpdateFormData,
  parseSystemSettingsFormData,
} from "@/lib/validations/admin-system";

function flattenFieldErrors(
  fieldErrors: Record<string, string[] | undefined>,
): Record<string, string[]> {
  return Object.fromEntries(
    Object.entries(fieldErrors)
      .filter((entry): entry is [string, string[]] => !!entry[1]?.length)
      .map(([key, messages]) => [key, messages]),
  );
}

function revalidateSystemPaths() {
  revalidatePath("/admin/system");
  revalidatePath("/admin");
  revalidatePath("/dashboard");
  revalidatePath("/dashboard/receipts");
  revalidatePath("/dashboard/org");
}

export async function updateSystemSettingsAction(
  _prevState: AdminActionState,
  formData: FormData,
): Promise<AdminActionState> {
  const parsed = parseSystemSettingsFormData(formData);

  if (!parsed.success) {
    return {
      fieldErrors: flattenFieldErrors(parsed.error.flatten().fieldErrors),
    };
  }

  const { body } = await bulkUpsertSettingsWithFastApi({
    auth_rate_limit_max: String(parsed.data.auth_rate_limit_max),
    auth_rate_limit_window_seconds: String(
      parsed.data.auth_rate_limit_window_seconds,
    ),
    audit_retention_days: String(parsed.data.audit_retention_days),
    receipt_retention_days: String(parsed.data.receipt_retention_days),
  });

  if (!body.success) {
    return { error: body.message };
  }

  revalidateSystemPaths();
  return { success: true };
}

export async function createReliefLimitAction(
  _prevState: AdminActionState,
  formData: FormData,
): Promise<AdminActionState> {
  const parsed = parseReliefLimitCreateFormData(formData);

  if (!parsed.success) {
    return {
      fieldErrors: flattenFieldErrors(parsed.error.flatten().fieldErrors),
    };
  }

  const { body } = await createReliefLimitWithFastApi({
    category: parsed.data.category,
    limit_amount: parsed.data.limit_amount,
    be_seksyen: parsed.data.be_seksyen ?? null,
    description_my: parsed.data.description_my,
    sort_order: parsed.data.sort_order,
  });

  if (!body.success) {
    return { error: body.message };
  }

  revalidateSystemPaths();
  return { success: true, message: "Relief limit added." };
}

export async function updateReliefLimitAction(
  _prevState: AdminActionState,
  formData: FormData,
): Promise<AdminActionState> {
  const parsed = parseReliefLimitUpdateFormData(formData);

  if (!parsed.success) {
    return {
      fieldErrors: flattenFieldErrors(parsed.error.flatten().fieldErrors),
    };
  }

  const { body } = await updateReliefLimitWithFastApi(parsed.data.category, {
    limit_amount: parsed.data.limit_amount,
    be_seksyen: parsed.data.be_seksyen ?? null,
    description_my: parsed.data.description_my ?? null,
    is_active: parsed.data.is_active,
    sort_order: parsed.data.sort_order,
  });

  if (!body.success) {
    return { error: body.message };
  }

  revalidateSystemPaths();
  return { success: true, message: "Relief limit updated." };
}

export async function deactivateReliefLimitAction(
  _prevState: AdminActionState,
  formData: FormData,
): Promise<AdminActionState> {
  const category = formData.get("category");
  if (typeof category !== "string" || category.length === 0) {
    return { error: "Category is required." };
  }

  const { body } = await deactivateReliefLimitWithFastApi(category);

  if (!body.success) {
    return { error: body.message };
  }

  revalidateSystemPaths();
  return { success: true, message: "Relief limit deactivated." };
}

export async function purgeRetentionAction(
  _prevState: AdminActionState,
): Promise<AdminActionState> {
  void _prevState;
  const { body } = await purgeRetentionWithFastApi();

  if (!body.success) {
    return { error: body.message };
  }

  revalidateSystemPaths();
  return {
    success: true,
    message: `${body.data.audit_logs_deleted} audit logs and ${body.data.receipts_deleted} receipts deleted.`,
  };
}
