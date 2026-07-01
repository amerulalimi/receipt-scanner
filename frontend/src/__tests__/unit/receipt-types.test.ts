import {
  DEFAULT_RECEIPT_FILTERS,
  isAllowedReceiptMimeType,
  isValidReceiptFileSize,
  RECEIPT_ALLOWED_MIME_TYPES,
  RECEIPT_MAX_FILE_BYTES,
  type Receipt,
  type ReceiptFilters,
} from "@/lib/types/receipt";

describe("receipt types", () => {
  it("Receipt type has required fields", () => {
    const receipt: Receipt = {
      id: "uuid",
      merchant_name: "Klinik",
      receipt_date: "2025-06-14",
      total_amount: 100,
      claimed_amount: 100,
      category: "perubatan",
      be_seksyen: "S.46(1)(b)",
      status: "pending",
      scan_status: "success",
      ai_confidence: 0.9,
      file_type: "jpg",
      thumbnail_url: null,
      created_at: "2025-06-14T10:00:00Z",
    };
    expect(receipt.id).toBe("uuid");
    expect(receipt.status).toBe("pending");
  });

  it("ReceiptFilters defaults are correct", () => {
    const filters: ReceiptFilters = {};
    expect(filters.page ?? DEFAULT_RECEIPT_FILTERS.page).toBe(1);
    expect(filters.limit ?? DEFAULT_RECEIPT_FILTERS.limit).toBe(20);
    expect(filters.sort ?? DEFAULT_RECEIPT_FILTERS.sort).toBe("created_at:desc");
  });

  it("file size validation rejects over 10MB", () => {
    expect(isValidReceiptFileSize(RECEIPT_MAX_FILE_BYTES)).toBe(true);
    expect(isValidReceiptFileSize(RECEIPT_MAX_FILE_BYTES + 1)).toBe(false);
    expect(isValidReceiptFileSize(0)).toBe(false);
  });

  it("file type validation allows jpg png pdf only", () => {
    expect(isAllowedReceiptMimeType("image/jpeg")).toBe(true);
    expect(isAllowedReceiptMimeType("image/png")).toBe(true);
    expect(isAllowedReceiptMimeType("application/pdf")).toBe(true);
    expect(isAllowedReceiptMimeType("image/webp")).toBe(false);
    expect(RECEIPT_ALLOWED_MIME_TYPES).toHaveLength(3);
  });
});
