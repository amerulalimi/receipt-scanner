"use server";

import { revalidatePath } from "next/cache";

import {
  bulkUpsertSettingsWithFastApi,
  upsertSecretWithFastApi,
} from "@/lib/api/admin-config";
import {
  parseAiConfigFormData,
  parseSecretFormData,
} from "@/lib/validations/admin-config";

export type AdminActionState = {
  success?: boolean;
  error?: string;
  message?: string;
  fieldErrors?: Record<string, string[]>;
};

function flattenFieldErrors(
  fieldErrors: Record<string, string[] | undefined>,
): Record<string, string[]> {
  return Object.fromEntries(
    Object.entries(fieldErrors)
      .filter((entry): entry is [string, string[]] => !!entry[1]?.length)
      .map(([key, messages]) => [key, messages]),
  );
}

export async function updateSecretAction(
  _prevState: AdminActionState,
  formData: FormData,
): Promise<AdminActionState> {
  const parsed = parseSecretFormData(formData);

  if (!parsed.success) {
    return {
      fieldErrors: flattenFieldErrors(parsed.error.flatten().fieldErrors),
    };
  }

  const { body } = await upsertSecretWithFastApi(
    parsed.data.key,
    parsed.data.value,
  );

  if (!body.success) {
    return { error: body.message };
  }

  revalidatePath("/admin/secrets");
  revalidatePath("/admin/ai");
  return { success: true };
}

export async function updateAiConfigAction(
  _prevState: AdminActionState,
  formData: FormData,
): Promise<AdminActionState> {
  const parsed = parseAiConfigFormData(formData);

  if (!parsed.success) {
    return {
      fieldErrors: flattenFieldErrors(parsed.error.flatten().fieldErrors),
    };
  }

  const { body } = await bulkUpsertSettingsWithFastApi({
    openrouter_vision_model: parsed.data.openrouter_vision_model,
    receipt_processing_enabled: parsed.data.receipt_processing_enabled,
  });

  if (!body.success) {
    return { error: body.message };
  }

  revalidatePath("/admin/ai");
  return { success: true };
}
