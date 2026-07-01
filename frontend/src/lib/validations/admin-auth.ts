import { z } from "zod";

export const adminLoginSchema = z.object({
  email: z.string().email("E-mel tidak sah"),
  password: z.string().min(1, "Kata laluan diperlukan"),
});

export type AdminLoginFormValues = z.infer<typeof adminLoginSchema>;

const ADMIN_ALLOWED_REDIRECTS = [
  "/admin",
  "/admin/secrets",
  "/admin/ai",
  "/admin/system",
] as const;

export type AdminAllowedRedirect = (typeof ADMIN_ALLOWED_REDIRECTS)[number];

export function resolveAdminRedirectPath(
  value: FormDataEntryValue | null,
): AdminAllowedRedirect {
  if (
    typeof value === "string" &&
    ADMIN_ALLOWED_REDIRECTS.includes(value as AdminAllowedRedirect)
  ) {
    return value as AdminAllowedRedirect;
  }
  return "/admin";
}

export function parseAdminLoginFormData(formData: FormData) {
  return adminLoginSchema.safeParse({
    email: formData.get("email"),
    password: formData.get("password"),
  });
}
