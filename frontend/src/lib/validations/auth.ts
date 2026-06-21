import { z } from "zod";

export const loginSchema = z.object({
  email: z
    .string()
    .min(1, "Email is required")
    .email("Invalid email format"),
  password: z
    .string()
    .min(1, "Password is required")
    .max(128, "Password is too long"),
});

export const registerSchema = z.object({
  email: z
    .string()
    .min(1, "Email is required")
    .email("Invalid email format"),
  password: z
    .string()
    .min(8, "Password must be at least 8 characters")
    .max(128, "Password is too long"),
  full_name: z
    .string()
    .min(1, "Full name is required")
    .max(255, "Name is too long"),
  account_type: z.enum(["individual", "corporate"], {
    message: "Account type is required",
  }),
});

export type LoginFormValues = z.infer<typeof loginSchema>;
export type RegisterFormValues = z.infer<typeof registerSchema>;

export function parseLoginFormData(formData: FormData) {
  return loginSchema.safeParse({
    email: formData.get("email"),
    password: formData.get("password"),
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
