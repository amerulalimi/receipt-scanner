import "server-only";

import { apiFetch, apiUploadFetch } from "@/lib/api/client";
import { requireSessionCookieHeader } from "@/lib/api/session";
import type {
  ReceiptDetail,
  ReceiptListData,
  ReceiptUpdatePayload,
  ReceiptUploadData,
} from "@/lib/api/types";
import type { ReceiptFilters } from "@/lib/types/receipt";
import { DEFAULT_RECEIPT_FILTERS } from "@/lib/types/receipt";

type ReceiptDownloadData = {
  download_url: string;
};

function buildReceiptListQuery(filters: ReceiptFilters): string {
  const params = new URLSearchParams({
    page: String(filters.page ?? DEFAULT_RECEIPT_FILTERS.page),
    limit: String(filters.limit ?? DEFAULT_RECEIPT_FILTERS.limit),
    sort: filters.sort ?? DEFAULT_RECEIPT_FILTERS.sort,
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

export async function uploadReceipts(files: File[], taxYear?: number) {
  const cookie = await requireSessionCookieHeader();
  const formData = new FormData();
  for (const file of files) {
    formData.append("files", file);
  }
  if (taxYear !== undefined) {
    formData.append("tax_year", String(taxYear));
  }

  const { body } = await apiUploadFetch<ReceiptUploadData>("/api/v1/receipts/upload", {
    formData,
    cookie,
  });
  return body;
}

export async function getReceipts(filters: ReceiptFilters = {}) {
  const cookie = await requireSessionCookieHeader();
  const query = buildReceiptListQuery(filters);
  return apiFetch<ReceiptListData>(`/api/v1/receipts?${query}`, { cookie });
}

export async function fetchRecentReceipts(limit: number, taxYear?: number) {
  const cookie = await requireSessionCookieHeader();
  const params = new URLSearchParams({
    page: "1",
    limit: String(limit),
    sort: DEFAULT_RECEIPT_FILTERS.sort,
  });
  if (taxYear !== undefined) {
    params.set("tax_year", String(taxYear));
  }
  return apiFetch<ReceiptListData>(`/api/v1/receipts?${params}`, { cookie });
}

export async function getReceipt(id: string) {
  const cookie = await requireSessionCookieHeader();
  return apiFetch<ReceiptDetail>(`/api/v1/receipts/${id}`, { cookie });
}

export async function updateReceipt(id: string, data: ReceiptUpdatePayload) {
  const cookie = await requireSessionCookieHeader();
  return apiFetch<ReceiptDetail>(`/api/v1/receipts/${id}`, {
    method: "PATCH",
    body: data,
    cookie,
  });
}

export async function deleteReceipt(id: string) {
  const cookie = await requireSessionCookieHeader();
  return apiFetch<null>(`/api/v1/receipts/${id}`, {
    method: "DELETE",
    cookie,
  });
}

export async function downloadReceipt(id: string) {
  const cookie = await requireSessionCookieHeader();
  const { body } = await apiFetch<ReceiptDownloadData>(
    `/api/v1/receipts/${id}/download`,
    { cookie },
  );
  return { download_url: body.success ? body.data.download_url : "" };
}

export async function createManualReceipt(payload: {
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

export async function reprocessReceipt(id: string) {
  const cookie = await requireSessionCookieHeader();
  return apiFetch<ReceiptDetail>(`/api/v1/receipts/${id}/reprocess`, {
    method: "POST",
    cookie,
  });
}

// Backward-compatible exports
export const uploadReceiptWithFastApi = uploadReceipts;
export const fetchReceipts = getReceipts;
export const fetchReceiptById = getReceipt;
export const updateReceiptWithFastApi = updateReceipt;
export const deleteReceiptWithFastApi = deleteReceipt;
export const createManualReceiptWithFastApi = createManualReceipt;
export const reprocessReceiptWithFastApi = reprocessReceipt;

