import { z } from "zod";

export const ORG_POLICY_CATEGORIES = [
  "perubatan",
  "gaya_hidup",
  "sukan",
  "pendidikan",
  "sspn",
  "ev_charging",
] as const;

export const orgRegisterSchema = z.object({
  name: z.string().trim().min(1, "Company name is required").max(255),
  ssm_number: z
    .string()
    .trim()
    .min(5, "SSM number must be at least 5 characters")
    .max(20),
  email_domain: z
    .string()
    .trim()
    .min(3, "Email domain is required")
    .max(100)
    .transform((value) => value.replace(/^@/, "").toLowerCase()),
});

export type OrgRegisterFormValues = z.infer<typeof orgRegisterSchema>;

export const orgPolicyUpdateSchema = z.object({
  allowed_categories: z
    .array(z.string().trim().min(1).max(50))
    .min(1, "Select at least one category"),
  require_hr_approval: z.boolean(),
  max_receipts_per_month: z.number().int().min(1, "Minimum 1 receipt").max(500),
  tax_year: z.number().int().min(2000).max(2100),
});

export type OrgPolicyUpdateFormValues = z.infer<typeof orgPolicyUpdateSchema>;

export const orgInviteEmployeesSchema = z.discriminatedUnion("type", [
  z.object({
    type: z.literal("link"),
  }),
  z.object({
    type: z.literal("email"),
    emails: z
      .string()
      .trim()
      .min(1, "Enter at least one email")
      .transform((value) =>
        value
          .split(/[\n,;]+/)
          .map((email) => email.trim().toLowerCase())
          .filter(Boolean),
      )
      .pipe(z.array(z.string().email()).min(1, "Invalid email address")),
  }),
]);

export type OrgInviteEmployeesFormValues = z.infer<
  typeof orgInviteEmployeesSchema
>;

export const orgInviteHrAdminSchema = z.object({
  email: z.string().trim().email("Invalid email address"),
});

export type OrgInviteHrAdminFormValues = z.infer<typeof orgInviteHrAdminSchema>;

export const inviteAcceptSchema = z.object({
  token: z.string().min(1),
  email: z.string().trim().email("Invalid email address"),
  password: z.string().min(8, "Password must be at least 8 characters"),
  full_name: z.string().trim().min(1, "Full name is required").max(255),
});

export type InviteAcceptFormValues = z.infer<typeof inviteAcceptSchema>;

export function parseOrgRegisterFormData(formData: FormData) {
  return orgRegisterSchema.safeParse({
    name: formData.get("name"),
    ssm_number: formData.get("ssm_number"),
    email_domain: formData.get("email_domain"),
  });
}

export function parseOrgPolicyUpdateFormData(formData: FormData) {
  const categories = formData.getAll("allowed_categories").map(String);
  return orgPolicyUpdateSchema.safeParse({
    allowed_categories: categories,
    require_hr_approval: formData.get("require_hr_approval") === "true",
    max_receipts_per_month: Number(formData.get("max_receipts_per_month")),
    tax_year: Number(formData.get("tax_year")),
  });
}

export function parseOrgInviteEmployeesFormData(formData: FormData) {
  const type = formData.get("type");
  if (type === "link") {
    return orgInviteEmployeesSchema.safeParse({ type: "link" });
  }
  return orgInviteEmployeesSchema.safeParse({
    type: "email",
    emails: formData.get("emails"),
  });
}

export function parseOrgInviteHrAdminFormData(formData: FormData) {
  return orgInviteHrAdminSchema.safeParse({
    email: formData.get("email"),
  });
}

export function parseInviteAcceptFormData(formData: FormData) {
  return inviteAcceptSchema.safeParse({
    token: formData.get("token"),
    email: formData.get("email"),
    password: formData.get("password"),
    full_name: formData.get("full_name"),
  });
}

export function parseOrgEmployeeStatusFormData(formData: FormData) {
  return z
    .object({
      user_id: z.string().uuid(),
      is_active: z.enum(["true", "false"]).transform((v) => v === "true"),
    })
    .safeParse({
      user_id: formData.get("user_id"),
      is_active: formData.get("is_active"),
    });
}

export function parseOrgEmployeeRemoveFormData(formData: FormData) {
  return z
    .object({
      user_id: z.string().uuid(),
    })
    .safeParse({
      user_id: formData.get("user_id"),
    });
}

export const orgEmployeeBulkImportRowSchema = z.object({
  email: z.string().trim().email("Invalid email address"),
  full_name: z
    .string()
    .trim()
    .max(255)
    .optional()
    .transform((value) => (value && value.length > 0 ? value : undefined)),
  employee_code: z
    .string()
    .trim()
    .max(50)
    .optional()
    .transform((value) => (value && value.length > 0 ? value : undefined)),
});

export const orgEmployeeBulkImportSchema = z.object({
  employees: z
    .array(orgEmployeeBulkImportRowSchema)
    .min(1, "At least one employee is required")
    .max(200, "Maximum 200 employees per import"),
});

export type OrgEmployeeBulkImportFormValues = z.infer<
  typeof orgEmployeeBulkImportSchema
>;

export function parseOrgBulkImportFormData(formData: FormData) {
  const raw = formData.get("employees");
  if (typeof raw !== "string" || raw.trim().length === 0) {
    return orgEmployeeBulkImportSchema.safeParse({ employees: [] });
  }

  try {
    const parsed = JSON.parse(raw) as unknown;
    return orgEmployeeBulkImportSchema.safeParse({ employees: parsed });
  } catch {
    return orgEmployeeBulkImportSchema.safeParse({ employees: [] });
  }
}
