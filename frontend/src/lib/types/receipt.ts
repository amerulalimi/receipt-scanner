export type {
  ReceiptDetail,
  ReceiptFlagRead as ReceiptFlag,
  ReceiptLineItem,
  ReceiptListData as PaginatedReceipts,
  ReceiptListItem as Receipt,
  ReceiptListData,
  ReceiptUpdatePayload as UpdateReceiptData,
  ReceiptUploadData as UploadResponse,
} from "@/lib/api/types";

export type ReceiptFilters = {
  tax_year?: number;
  category?: string;
  status?: string;
  page?: number;
  limit?: number;
  sort?: string;
};

export const DEFAULT_RECEIPT_FILTERS: Required<
  Pick<ReceiptFilters, "page" | "limit" | "sort">
> = {
  page: 1,
  limit: 20,
  sort: "created_at:desc",
};

export const RECEIPT_MAX_FILE_BYTES = 10 * 1024 * 1024;

export const RECEIPT_ALLOWED_MIME_TYPES = [
  "image/jpeg",
  "image/png",
  "application/pdf",
] as const;

export type ReceiptAllowedMimeType = (typeof RECEIPT_ALLOWED_MIME_TYPES)[number];

export function isAllowedReceiptMimeType(type: string): type is ReceiptAllowedMimeType {
  return (RECEIPT_ALLOWED_MIME_TYPES as readonly string[]).includes(type);
}

export function isValidReceiptFileSize(size: number): boolean {
  return size > 0 && size <= RECEIPT_MAX_FILE_BYTES;
}
