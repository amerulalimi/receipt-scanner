import { z } from "zod";

export const settingsProfileSchema = z.object({
  full_name: z
    .string()
    .trim()
    .min(1, "Full name is required")
    .max(255, "Name is too long"),
  tax_year: z.number().int().min(2000).max(2100),
  tax_bracket: z.union([z.number().min(0).max(100), z.null()]),
});

export type SettingsProfileFormValues = z.infer<typeof settingsProfileSchema>;

export function parseSettingsProfileFormData(formData: FormData) {
  const rawTaxBracket = formData.get("tax_bracket");
  const taxBracketValue =
    typeof rawTaxBracket === "string" && rawTaxBracket.trim().length > 0
      ? Number(rawTaxBracket)
      : null;

  return settingsProfileSchema.safeParse({
    full_name: formData.get("full_name"),
    tax_year: Number(formData.get("tax_year")),
    tax_bracket: taxBracketValue,
  });
}

export function parseRevokeSessionFormData(formData: FormData) {
  return z
    .object({
      session_id: z.string().min(1, "Invalid session"),
    })
    .safeParse({
      session_id: formData.get("session_id"),
    });
}

export const notificationPreferencesSchema = z.object({
  email_enabled: z.boolean(),
  in_app_enabled: z.boolean(),
  digest_frequency: z.enum(["off", "monthly"]),
});

export type NotificationPreferencesFormValues = z.infer<
  typeof notificationPreferencesSchema
>;

export function parseNotificationPreferencesFormData(formData: FormData) {
  return notificationPreferencesSchema.safeParse({
    email_enabled: formData.get("email_enabled") === "true",
    in_app_enabled: formData.get("in_app_enabled") === "true",
    digest_frequency: formData.get("digest_frequency"),
  });
}
