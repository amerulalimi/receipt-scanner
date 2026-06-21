import { z } from "zod";

import {
  RECEIPT_UPLOAD_ACCEPTED_MIME_TYPES,
  RECEIPT_UPLOAD_MAX_BYTES,
  RECEIPT_UPLOAD_MAX_FILES,
  type ReceiptUploadMimeType,
} from "@/lib/constants/receipts";
import { optionalTaxYearQuerySchema, taxYearSchema } from "@/lib/validations/tax-year";

export const RECEIPT_CATEGORIES = [
  "perubatan",
  "gaya_hidup",
  "sukan",
  "pendidikan",
  "sspn",
  "ev_charging",
  "tidak_layak",
  "semak_manual",
] as const;

const receiptCategorySchema = z
  .string()
  .trim()
  .min(1, "Category is required")
  .max(50, "Invalid category");

export const RECEIPT_STATUSES = [
  "pending",
  "approved",
  "rejected",
  "flagged",
  "duplicate",
] as const;

export const RECEIPT_SORT_OPTIONS = [
  "created_at:desc",
  "created_at:asc",
  "receipt_date:desc",
  "total_amount:desc",
  "claimed_amount:desc",
] as const;

export type ReceiptCategory = (typeof RECEIPT_CATEGORIES)[number];
export type ReceiptStatus = (typeof RECEIPT_STATUSES)[number];
export type ReceiptSortOption = (typeof RECEIPT_SORT_OPTIONS)[number];

const acceptedMimeSet = new Set<string>(RECEIPT_UPLOAD_ACCEPTED_MIME_TYPES);

function isAcceptedMimeType(value: string): value is ReceiptUploadMimeType {
  return acceptedMimeSet.has(value);
}

const receiptFileSchema = z
  .instanceof(File, { message: "Receipt file is required" })
  .refine((file) => file.size > 0, "File is empty")
  .refine(
    (file) => file.size <= RECEIPT_UPLOAD_MAX_BYTES,
    "Maximum file size is 10MB",
  )
  .refine(
    (file) => isAcceptedMimeType(file.type),
    "Unsupported file type. Use JPG, PNG, WEBP, or PDF.",
  );

export const receiptUploadSchema = z.object({
  file: receiptFileSchema,
});

export type ReceiptUploadFormValues = z.infer<typeof receiptUploadSchema>;

export const receiptBulkUploadSchema = z.object({
  files: z
    .array(receiptFileSchema)
    .min(1, "At least one file is required")
    .max(
      RECEIPT_UPLOAD_MAX_FILES,
      `Maximum ${RECEIPT_UPLOAD_MAX_FILES} files per upload`,
    ),
  tax_year: taxYearSchema,
});

export type ReceiptBulkUploadFormValues = z.infer<typeof receiptBulkUploadSchema>;

export function parseReceiptUploadFormData(formData: FormData) {
  return receiptUploadSchema.safeParse({
    file: formData.get("file"),
  });
}

export function parseReceiptBulkUploadFormData(formData: FormData) {
  const files = formData
    .getAll("files")
    .filter((item): item is File => item instanceof File);

  return receiptBulkUploadSchema.safeParse({
    files,
    tax_year: Number(formData.get("tax_year")),
  });
}

export const receiptLineItemUpdateSchema = z.object({
  id: z.string().uuid("Invalid line item ID"),
  included_in_claim: z.boolean(),
  category: receiptCategorySchema.optional(),
});

export const receiptLineItemsUpdateSchema = z.object({
  receipt_id: z.string().uuid("Invalid receipt ID"),
  line_items: z.array(receiptLineItemUpdateSchema).min(1, "Line items required"),
});

export type ReceiptLineItemsUpdateFormValues = z.infer<
  typeof receiptLineItemsUpdateSchema
>;

export function parseReceiptLineItemsUpdateFormData(formData: FormData) {
  const raw = formData.get("line_items");
  if (typeof raw !== "string" || raw.trim().length === 0) {
    return receiptLineItemsUpdateSchema.safeParse({
      receipt_id: formData.get("receipt_id"),
      line_items: [],
    });
  }

  try {
    const parsed = JSON.parse(raw) as unknown;
    return receiptLineItemsUpdateSchema.safeParse({
      receipt_id: formData.get("receipt_id"),
      line_items: parsed,
    });
  } catch {
    return receiptLineItemsUpdateSchema.safeParse({
      receipt_id: formData.get("receipt_id"),
      line_items: [],
    });
  }
}

export const receiptUpdateSchema = z.object({
  receipt_id: z.string().uuid("Invalid receipt ID"),
  category: receiptCategorySchema,
  claimed_amount: z
    .string()
    .trim()
    .optional()
    .refine(
      (value) => !value || /^\d+(\.\d{1,2})?$/.test(value),
      "Invalid amount",
    )
    .transform((value) =>
      value && value.length > 0 ? Number.parseFloat(value) : undefined,
    ),
});

export const receiptUpdateFormSchema = z.object({
  receipt_id: z.string().uuid("Invalid receipt ID"),
  category: receiptCategorySchema,
  claimed_amount: z.string().optional(),
});

export type ReceiptUpdateFormValues = z.infer<typeof receiptUpdateFormSchema>;

export function parseReceiptUpdateFormData(formData: FormData) {
  return receiptUpdateSchema.safeParse({
    receipt_id: formData.get("receipt_id"),
    category: formData.get("category"),
    claimed_amount: formData.get("claimed_amount") ?? undefined,
  });
}

export const receiptDeleteSchema = z.object({
  receipt_id: z.string().uuid("Invalid receipt ID"),
});

export function parseReceiptDeleteFormData(formData: FormData) {
  return receiptDeleteSchema.safeParse({
    receipt_id: formData.get("receipt_id"),
  });
}

export const receiptReviewSchema = z.object({
  receipt_id: z.string().uuid("Invalid receipt ID"),
  action: z.enum(["approve", "reject"]),
  comment: z
    .string()
    .trim()
    .max(1000, "Comment is too long")
    .optional()
    .transform((value) => (value && value.length > 0 ? value : undefined)),
});

export function parseReceiptReviewFormData(formData: FormData) {
  return receiptReviewSchema.safeParse({
    receipt_id: formData.get("receipt_id"),
    action: formData.get("action"),
    comment: formData.get("comment") ?? undefined,
  });
}

export const receiptListFiltersSchema = z.object({
  page: z.coerce.number().int().min(1).default(1),
  limit: z.coerce.number().int().min(1).max(100).default(20),
  category: receiptCategorySchema.optional(),
  status: z.enum(RECEIPT_STATUSES).optional(),
  sort: z.enum(RECEIPT_SORT_OPTIONS).default("created_at:desc"),
  tax_year: optionalTaxYearQuerySchema,
});

export type ReceiptListFilters = z.infer<typeof receiptListFiltersSchema>;

export const DASHBOARD_RECEIPT_HISTORY_LIMITS = [10, 20, 50] as const;

export type DashboardReceiptHistoryLimit =
  (typeof DASHBOARD_RECEIPT_HISTORY_LIMITS)[number];

export const dashboardReceiptHistorySchema = z.object({
  history_limit: z.coerce
    .number()
    .int()
    .refine(
      (value): value is DashboardReceiptHistoryLimit =>
        DASHBOARD_RECEIPT_HISTORY_LIMITS.includes(
          value as DashboardReceiptHistoryLimit,
        ),
      "Invalid history limit",
    )
    .default(10),
  tax_year: optionalTaxYearQuerySchema,
});

export type DashboardReceiptHistoryParams = z.infer<
  typeof dashboardReceiptHistorySchema
>;

function getSearchParamValue(
  value: string | string[] | undefined,
): string | undefined {
  if (Array.isArray(value)) {
    return value[0];
  }
  return value;
}

export function parseReceiptListSearchParams(
  searchParams: Record<string, string | string[] | undefined>,
) {
  return receiptListFiltersSchema.safeParse({
    page: getSearchParamValue(searchParams.page) ?? "1",
    limit: getSearchParamValue(searchParams.limit) ?? "20",
    category: getSearchParamValue(searchParams.category),
    status: getSearchParamValue(searchParams.status),
    sort: getSearchParamValue(searchParams.sort) ?? "created_at:desc",
    tax_year: getSearchParamValue(searchParams.tax_year),
  });
}

export function parseDashboardReceiptHistorySearchParams(
  searchParams: Record<string, string | string[] | undefined>,
) {
  return dashboardReceiptHistorySchema.safeParse({
    history_limit: getSearchParamValue(searchParams.history_limit) ?? "10",
    tax_year: getSearchParamValue(searchParams.tax_year),
  });
}

export const manualReceiptSchema = z.object({
  merchant_name: z
    .string()
    .trim()
    .min(1, "Merchant name is required")
    .max(255),
  receipt_date: z
    .string()
    .trim()
    .min(1, "Receipt date is required")
    .refine((value) => !Number.isNaN(Date.parse(value)), "Invalid date"),
  total_amount: z
    .string()
    .trim()
    .min(1, "Total amount is required")
    .refine(
      (value) => /^\d+(\.\d{1,2})?$/.test(value),
      "Invalid amount",
    )
    .transform((value) => Number.parseFloat(value)),
  category: receiptCategorySchema,
  claimed_amount: z
    .string()
    .trim()
    .optional()
    .refine(
      (value) => !value || /^\d+(\.\d{1,2})?$/.test(value),
      "Invalid amount",
    )
    .transform((value) =>
      value && value.length > 0 ? Number.parseFloat(value) : undefined,
    ),
  notes: z
    .string()
    .trim()
    .max(2000, "Notes are too long")
    .optional()
    .transform((value) => (value && value.length > 0 ? value : undefined)),
  tax_year: taxYearSchema,
});

export const manualReceiptFormSchema = z.object({
  merchant_name: z
    .string()
    .trim()
    .min(1, "Merchant name is required")
    .max(255),
  receipt_date: z
    .string()
    .trim()
    .min(1, "Receipt date is required")
    .refine((value) => !Number.isNaN(Date.parse(value)), "Invalid date"),
  total_amount: z
    .string()
    .trim()
    .min(1, "Total amount is required")
    .refine(
      (value) => /^\d+(\.\d{1,2})?$/.test(value),
      "Invalid amount",
    ),
  category: receiptCategorySchema,
  claimed_amount: z.string().trim().optional(),
  notes: z.string().trim().max(2000, "Notes are too long").optional(),
  tax_year: taxYearSchema,
});

export type ManualReceiptFormValues = z.infer<typeof manualReceiptFormSchema>;

export function parseManualReceiptFormData(formData: FormData) {
  return manualReceiptSchema.safeParse({
    merchant_name: formData.get("merchant_name"),
    receipt_date: formData.get("receipt_date"),
    total_amount: formData.get("total_amount"),
    category: formData.get("category"),
    claimed_amount: formData.get("claimed_amount") ?? undefined,
    notes: formData.get("notes") ?? undefined,
    tax_year: Number(formData.get("tax_year")),
  });
}
