"use server";

import { revalidatePath } from "next/cache";

import type {
  CreateUploadSessionResult,
  MobileCloseSessionResult,
  MobileKeepAliveResult,
  MobileUploadActionState,
} from "@/actions/upload-session.types";
import {
  closeUploadSessionWithFastApi,
  createUploadSessionWithFastApi,
  keepAliveUploadSessionWithFastApi,
  uploadViaSessionWithFastApi,
} from "@/lib/api/upload-sessions";
import { getActionMessage } from "@/lib/i18n/server-action-messages";
import { parseReceiptUploadFormData } from "@/lib/validations/receipt";
import { parseUploadSessionToken } from "@/lib/validations/upload-session";

function flattenFieldErrors(
  fieldErrors: Record<string, string[] | undefined>,
): Record<string, string[]> {
  return Object.fromEntries(
    Object.entries(fieldErrors)
      .filter((entry): entry is [string, string[]] => !!entry[1]?.length)
      .map(([key, messages]) => [key, messages]),
  );
}

export async function createUploadSessionAction(
  taxYear?: number,
): Promise<CreateUploadSessionResult> {
  try {
    const { body } = await createUploadSessionWithFastApi(taxYear);

    if (!body.success) {
      return { error: body.message };
    }

    return { data: body.data };
  } catch {
    return {
      error: await getActionMessage("errors", "sessionExpired"),
    };
  }
}

export async function mobileUploadAction(
  _prevState: MobileUploadActionState,
  formData: FormData,
): Promise<MobileUploadActionState> {
  const tokenResult = parseUploadSessionToken(String(formData.get("token") ?? ""));
  if (!tokenResult.success) {
    return { error: await getActionMessage("errors", "invalidSessionToken") };
  }

  const parsed = parseReceiptUploadFormData(formData);
  if (!parsed.success) {
    return {
      fieldErrors: flattenFieldErrors(parsed.error.flatten().fieldErrors),
    };
  }

  try {
    const { body } = await uploadViaSessionWithFastApi(
      tokenResult.data,
      parsed.data.file,
    );

    if (!body.success) {
      return { error: body.message };
    }

    return {
      success: true,
      message: "Receipt is being processed.",
      jobId: body.data.job_id,
      inactivityRemaining: body.data.new_inactivity_remaining,
      uploadsCount: undefined,
    };
  } catch {
    return {
      error: await getActionMessage("errors", "uploadFailed"),
    };
  }
}

export async function mobileKeepAliveAction(
  token: string,
): Promise<MobileKeepAliveResult> {
  const tokenResult = parseUploadSessionToken(token);
  if (!tokenResult.success) {
    return { error: await getActionMessage("errors", "invalidSessionToken") };
  }

  try {
    const { body } = await keepAliveUploadSessionWithFastApi(tokenResult.data);

    if (!body.success) {
      return { error: body.message };
    }

    return { inactivityRemaining: body.data.inactivity_remaining };
  } catch {
    return { error: "Unable to keep session alive." };
  }
}

export async function mobileCloseSessionAction(
  token: string,
): Promise<MobileCloseSessionResult> {
  const tokenResult = parseUploadSessionToken(token);
  if (!tokenResult.success) {
    return { error: await getActionMessage("errors", "invalidSessionToken") };
  }

  try {
    const { body } = await closeUploadSessionWithFastApi(tokenResult.data);

    if (!body.success) {
      return { error: body.message };
    }

    return {
      uploadsCount: body.data.uploads_count,
      message: body.data.message,
    };
  } catch {
    return { error: "Unable to close session." };
  }
}

export async function revalidateDashboardAction(): Promise<void> {
  revalidatePath("/dashboard");
}
