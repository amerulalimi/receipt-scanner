import { z } from "zod";

export const loginSchema = z.object({
  email: z.string().email("E-mel tidak sah"),
  password: z.string().min(1, "Kata laluan diperlukan"),
  login_context: z.enum(["individual", "corporate"]),
});

export const registerSchema = z.object({
  email: z.string().email("E-mel tidak sah"),
  password: z.string().min(8, "Minimum 8 aksara"),
  full_name: z.string().min(1, "Nama diperlukan"),
  account_type: z.enum(["individual", "corporate"]),
});

export const updateProfileSchema = z.object({
  full_name: z.string().min(1).optional(),
  tax_year: z.number().int().optional(),
  tax_bracket: z.number().min(0).max(100).optional(),
});

export type LoginFormValues = z.infer<typeof loginSchema>;
export type RegisterFormValues = z.infer<typeof registerSchema>;
export type UpdateProfileFormValues = z.infer<typeof updateProfileSchema>;

export function parseLoginFormData(formData: FormData) {
  return loginSchema.safeParse({
    email: formData.get("email"),
    password: formData.get("password"),
    login_context: formData.get("login_context"),
  });
}

export function parseRegisterFormData(formData: FormData) {
  return registerSchema.safeParse({
    email: formData.get("email"),
    password: formData.get("password"),
    full_name: formData.get("full_name"),
    account_type: formData.get("account_type"),
  });
}

export const verifyEmailSchema = z.object({
  token: z.string().min(1, "Verification token is required"),
});

export function parseVerifyEmailFormData(formData: FormData) {
  return verifyEmailSchema.safeParse({
    token: formData.get("token"),
  });
}
