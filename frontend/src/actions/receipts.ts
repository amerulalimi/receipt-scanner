"use server";

import {
  deleteReceiptAction as deleteReceiptFormAction,
  updateReceiptAction as updateReceiptFormAction,
  uploadReceiptAction,
} from "@/actions/receipt";
import type {
  ReceiptDeleteActionState,
  ReceiptUpdateActionState,
  ReceiptUploadActionState,
} from "@/actions/receipt.types";
import type { ReceiptDetail } from "@/lib/api/types";

export type ActionResult<T> = {
  success: boolean;
  data?: T;
  error?: string;
};

export async function uploadReceiptsAction(
  formData: FormData,
): Promise<ActionResult<{ job_ids: string[]; message: string }>> {
  const result: ReceiptUploadActionState = await uploadReceiptAction(
    { success: false },
    formData,
  );
  if (!result.success) {
    return { success: false, error: result.error ?? "Upload failed" };
  }
  return {
    success: true,
    data: {
      job_ids: result.jobIds ?? [],
      message: result.message ?? "",
    },
  };
}

export async function deleteReceiptAction(
  receiptId: string,
): Promise<ActionResult<void>> {
  const formData = new FormData();
  formData.set("receiptId", receiptId);
  const result: ReceiptDeleteActionState = await deleteReceiptFormAction(
    { success: false },
    formData,
  );
  if (!result.success) {
    return { success: false, error: result.error ?? "Delete failed" };
  }
  return { success: true };
}

export async function updateReceiptAction(
  receiptId: string,
  data: Record<string, unknown>,
): Promise<ActionResult<ReceiptDetail>> {
  const formData = new FormData();
  formData.set("receiptId", receiptId);
  if (data.notes !== undefined) {
    formData.set("notes", String(data.notes));
  }
  if (data.category !== undefined) {
    formData.set("category", String(data.category));
  }
  if (data.claimed_amount !== undefined) {
    formData.set("claimed_amount", String(data.claimed_amount));
  }

  const result: ReceiptUpdateActionState = await updateReceiptFormAction(
    { success: false },
    formData,
  );
  if (!result.success) {
    return { success: false, error: result.error ?? "Update failed" };
  }
  return { success: true, data: result.receipt };
}
