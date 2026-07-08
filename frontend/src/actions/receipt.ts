"use server";

import { revalidatePath } from "next/cache";

import type {
  ReceiptDeleteActionState,
  ReceiptManualActionState,
  ReceiptUpdateActionState,
  ReceiptUploadActionState,
} from "@/actions/receipt.types";
import {
  deleteReceiptWithFastApi,
  fetchReceiptById,
  createManualReceiptWithFastApi,
  updateReceiptWithFastApi,
  uploadReceiptWithFastApi,
} from "@/lib/api/receipts";
import { getActionMessage } from "@/lib/i18n/server-action-messages";
import type { ReceiptDetail } from "@/lib/api/types";
import {
  parseReceiptDeleteFormData,
  parseReceiptLineItemsUpdateFormData,
  parseManualReceiptFormData,
  parseReceiptUpdateFormData,
  parseReceiptBulkUploadFormData,
} from "@/lib/validations/receipt";

function flattenFieldErrors(
  fieldErrors: Record<string, string[] | undefined>,
): Record<string, string[]> {
  return Object.fromEntries(
    Object.entries(fieldErrors)
      .filter((entry): entry is [string, string[]] => !!entry[1]?.length)
      .map(([key, messages]) => [key, messages]),
  );
}

function revalidateReceiptPaths() {
  revalidatePath("/dashboard");
  revalidatePath("/dashboard/receipts");
}

export async function uploadReceiptAction(
  _prevState: ReceiptUploadActionState,
  formData: FormData,
): Promise<ReceiptUploadActionState> {
  const parsed = parseReceiptBulkUploadFormData(formData);

  if (!parsed.success) {
    return {
      fieldErrors: flattenFieldErrors(parsed.error.flatten().fieldErrors),
    };
  }

  try {
    const body = await uploadReceiptWithFastApi(
      parsed.data.files,
      parsed.data.tax_year,
    );

    if (!body.success) {
      return { error: body.message };
    }

    revalidateReceiptPaths();

    const uploadErrors = body.data.errors?.map((item) => ({
      filename: item.filename,
      message: item.message,
    }));

    return {
      success: true,
      message: body.data.message,
      jobIds: body.data.job_ids,
      uploadErrors: uploadErrors?.length ? uploadErrors : undefined,
    };
  } catch {
    return {
      error: await getActionMessage("errors", "sessionExpired"),
    };
  }
}

export async function getReceiptDetailAction(
  receiptId: string,
): Promise<{ data?: ReceiptDetail; error?: string }> {
  try {
    const { body, response } = await fetchReceiptById(receiptId);

    if (!body.success || response.status >= 400) {
      return {
        error: body.success ? "Receipt not found." : body.message,
      };
    }

    return { data: body.data };
  } catch {
    return {
      error: await getActionMessage("errors", "sessionExpired"),
    };
  }
}

export async function updateReceiptAction(
  _prevState: ReceiptUpdateActionState,
  formData: FormData,
): Promise<ReceiptUpdateActionState> {
  const updateMode = formData.get("update_mode");

  if (updateMode === "line_items") {
    const parsed = parseReceiptLineItemsUpdateFormData(formData);

    if (!parsed.success) {
      return {
        fieldErrors: flattenFieldErrors(parsed.error.flatten().fieldErrors),
        error: "Invalid line item selection.",
      };
    }

    try {
      const { body } = await updateReceiptWithFastApi(parsed.data.receipt_id, {
        line_items: parsed.data.line_items,
      });

      if (!body.success) {
        return { error: body.message };
      }

      revalidateReceiptPaths();
      return { success: true, receipt: body.data };
    } catch {
      return {
        error: await getActionMessage("errors", "sessionExpired"),
      };
    }
  }

  const parsed = parseReceiptUpdateFormData(formData);

  if (!parsed.success) {
    return {
      fieldErrors: flattenFieldErrors(parsed.error.flatten().fieldErrors),
    };
  }

  try {
    const payload: { category: string; claimed_amount?: number } = {
      category: parsed.data.category,
    };

    if (parsed.data.claimed_amount !== undefined) {
      payload.claimed_amount = parsed.data.claimed_amount;
    }

    const { body } = await updateReceiptWithFastApi(
      parsed.data.receipt_id,
      payload,
    );

    if (!body.success) {
      return { error: body.message };
    }

    revalidateReceiptPaths();
    return { success: true, receipt: body.data };
  } catch {
    return {
      error: await getActionMessage("errors", "sessionExpired"),
    };
  }
}

export async function deleteReceiptAction(
  _prevState: ReceiptDeleteActionState,
  formData: FormData,
): Promise<ReceiptDeleteActionState> {
  const parsed = parseReceiptDeleteFormData(formData);

  if (!parsed.success) {
    return { error: "Invalid receipt ID." };
  }

  try {
    const { body } = await deleteReceiptWithFastApi(parsed.data.receipt_id);

    if (!body.success) {
      return { error: body.message };
    }

    revalidateReceiptPaths();
    return { success: true };
  } catch {
    return {
      error: await getActionMessage("errors", "sessionExpired"),
    };
  }
}

export async function createManualReceiptAction(
  _prevState: ReceiptManualActionState,
  formData: FormData,
): Promise<ReceiptManualActionState> {
  const parsed = parseManualReceiptFormData(formData);

  if (!parsed.success) {
    return {
      fieldErrors: flattenFieldErrors(parsed.error.flatten().fieldErrors),
    };
  }

  try {
    const { body } = await createManualReceiptWithFastApi({
      merchant_name: parsed.data.merchant_name,
      receipt_date: parsed.data.receipt_date,
      total_amount: parsed.data.total_amount,
      category: parsed.data.category,
      claimed_amount: parsed.data.claimed_amount,
      notes: parsed.data.notes,
      tax_year: parsed.data.tax_year,
    });

    if (!body.success) {
      return { error: body.message };
    }

    revalidateReceiptPaths();
    return {
      success: true,
      message: "Manual receipt created.",
      receiptId: body.data.id,
    };
  } catch {
    return {
      error: await getActionMessage("errors", "sessionExpired"),
    };
  }
}
