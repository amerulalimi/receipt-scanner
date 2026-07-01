import { z } from "zod";

export const SYSTEM_CONFIG_KEYS = [
  "auth_rate_limit_max",
  "auth_rate_limit_window_seconds",
  "audit_retention_days",
  "receipt_retention_days",
] as const;

export const systemSettingsSchema = z.object({
  auth_rate_limit_max: z.number().int().min(0).max(100),
  auth_rate_limit_window_seconds: z.number().int().min(60).max(86400),
  audit_retention_days: z.number().int().min(1).max(3650),
  receipt_retention_days: z.number().int().min(1).max(3650),
});

export type SystemSettingsFormValues = z.infer<typeof systemSettingsSchema>;

const categorySlugSchema = z
  .string()
  .trim()
  .min(2, "Category slug is required")
  .max(50)
  .regex(
    /^[a-z][a-z0-9_]{1,48}$/,
    "Slug must be lowercase letters, numbers, or underscores (e.g. perubatan)",
  );

export const reliefLimitCreateSchema = z.object({
  category: categorySlugSchema,
  limit_amount: z.number().positive(),
  be_seksyen: z.string().trim().max(20).optional(),
  description_my: z.string().trim().min(1, "Description is required").max(2000),
  sort_order: z.number().int().min(0).max(9999).optional(),
});

export const reliefLimitUpdateSchema = z.object({
  category: z.string().min(1),
  limit_amount: z.number().positive(),
  be_seksyen: z.string().trim().max(20).optional(),
  description_my: z.string().trim().max(2000).optional(),
  is_active: z.boolean().optional(),
  sort_order: z.number().int().min(0).max(9999).optional(),
});

export type ReliefLimitCreateFormValues = z.infer<typeof reliefLimitCreateSchema>;
export type ReliefLimitUpdateFormValues = z.infer<typeof reliefLimitUpdateSchema>;

export function parseSystemSettingsFormData(formData: FormData) {
  return systemSettingsSchema.safeParse({
    auth_rate_limit_max: Number(formData.get("auth_rate_limit_max")),
    auth_rate_limit_window_seconds: Number(
      formData.get("auth_rate_limit_window_seconds"),
    ),
    audit_retention_days: Number(formData.get("audit_retention_days")),
    receipt_retention_days: Number(formData.get("receipt_retention_days")),
  });
}

export function parseReliefLimitCreateFormData(formData: FormData) {
  const beSeksyen = formData.get("be_seksyen");
  const sortOrder = formData.get("sort_order");

  return reliefLimitCreateSchema.safeParse({
    category: formData.get("category"),
    limit_amount: Number(formData.get("limit_amount")),
    be_seksyen:
      typeof beSeksyen === "string" && beSeksyen.length > 0 ? beSeksyen : undefined,
    description_my: formData.get("description_my"),
    sort_order:
      typeof sortOrder === "string" && sortOrder.length > 0
        ? Number(sortOrder)
        : undefined,
  });
}

export function parseReliefLimitUpdateFormData(formData: FormData) {
  const description = formData.get("description_my");
  const beSeksyen = formData.get("be_seksyen");
  const isActive = formData.get("is_active");
  const sortOrder = formData.get("sort_order");

  return reliefLimitUpdateSchema.safeParse({
    category: formData.get("category"),
    limit_amount: Number(formData.get("limit_amount")),
    be_seksyen:
      typeof beSeksyen === "string" && beSeksyen.length > 0 ? beSeksyen : undefined,
    description_my:
      typeof description === "string" && description.length > 0
        ? description
        : undefined,
    is_active:
      typeof isActive === "string" && isActive.length > 0
        ? isActive === "true"
        : undefined,
    sort_order:
      typeof sortOrder === "string" && sortOrder.length > 0
        ? Number(sortOrder)
        : undefined,
  });
}
