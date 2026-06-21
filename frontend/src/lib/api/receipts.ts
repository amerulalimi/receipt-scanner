import "server-only";

import { apiFetch, apiUploadFetch } from "@/lib/api/client";
import { requireSessionCookieHeader } from "@/lib/api/session";
import type {
  ReceiptDetail,
  ReceiptListData,
  ReceiptUpdatePayload,
  ReceiptUploadData,
} from "@/lib/api/types";
import type { ReceiptListFilters } from "@/lib/validations/receipt";

function buildReceiptListQuery(filters: ReceiptListFilters): string {
  const params = new URLSearchParams({
    page: String(filters.page),
    limit: String(filters.limit),
    sort: filters.sort,
  });

  if (filters.category) {
    params.set("category", filters.category);
  }
  if (filters.status) {
    params.set("status", filters.status);
  }
  if (filters.tax_year) {
    params.set("tax_year", String(filters.tax_year));
  }

  return params.toString();
}

export async function uploadReceiptWithFastApi(files: File[], taxYear: number) {
  const cookie = await requireSessionCookieHeader();
  const formData = new FormData();
  for (const file of files) {
    formData.append("files", file);
  }
  formData.append("tax_year", String(taxYear));

  return apiUploadFetch<ReceiptUploadData>("/api/v1/receipts/upload", {
    formData,
    cookie,
  });
}

export async function fetchReceipts(filters: ReceiptListFilters) {
  const cookie = await requireSessionCookieHeader();
  const query = buildReceiptListQuery(filters);

  return apiFetch<ReceiptListData>(`/api/v1/receipts?${query}`, { cookie });
}

export async function fetchRecentReceipts(limit = 10, taxYear?: number) {
  const cookie = await requireSessionCookieHeader();
  const params = new URLSearchParams({
    page: "1",
    limit: String(limit),
    sort: "created_at:desc",
  });

  if (taxYear) {
    params.set("tax_year", String(taxYear));
  }

  return apiFetch<ReceiptListData>(`/api/v1/receipts?${params.toString()}`, {
    cookie,
  });
}

export async function fetchReceiptById(receiptId: string) {
  const cookie = await requireSessionCookieHeader();

  return apiFetch<ReceiptDetail>(`/api/v1/receipts/${receiptId}`, { cookie });
}

export async function updateReceiptWithFastApi(
  receiptId: string,
  payload: ReceiptUpdatePayload,
) {
  const cookie = await requireSessionCookieHeader();

  return apiFetch<ReceiptDetail>(`/api/v1/receipts/${receiptId}`, {
    method: "PATCH",
    body: payload,
    cookie,
  });
}

export async function deleteReceiptWithFastApi(receiptId: string) {
  const cookie = await requireSessionCookieHeader();

  return apiFetch<null>(`/api/v1/receipts/${receiptId}`, {
    method: "DELETE",
    cookie,
  });
}

export async function createManualReceiptWithFastApi(payload: {
  merchant_name: string;
  receipt_date: string;
  total_amount: number;
  category: string;
  claimed_amount?: number;
  notes?: string | null;
  tax_year?: number;
}) {
  const cookie = await requireSessionCookieHeader();

  return apiFetch<ReceiptDetail>("/api/v1/receipts/manual", {
    method: "POST",
    body: payload,
    cookie,
  });
}

export async function reprocessReceiptWithFastApi(receiptId: string) {
  const cookie = await requireSessionCookieHeader();

  return apiFetch<ReceiptDetail>(`/api/v1/receipts/${receiptId}/reprocess`, {
    method: "POST",
    cookie,
  });
}
