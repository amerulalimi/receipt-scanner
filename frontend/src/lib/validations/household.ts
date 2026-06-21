import { z } from "zod";

export const spouseLinkRequestSchema = z.object({
  partner_email: z.string().trim().email("Invalid email address"),
});

export const spouseLinkRespondSchema = z.object({
  link_id: z.string().uuid("Invalid link ID"),
  action: z.enum(["accept", "reject"]),
});

export const spouseLinkDissolveSchema = z.object({
  link_id: z.string().uuid("Invalid link ID"),
});

export const receiptReassignSchema = z.object({
  receipt_id: z.string().uuid("Invalid receipt ID"),
  target_user_id: z.string().uuid("Invalid target user ID"),
});

export type SpouseLinkRequestFormValues = z.infer<typeof spouseLinkRequestSchema>;
export type SpouseLinkRespondFormValues = z.infer<typeof spouseLinkRespondSchema>;

export function parseSpouseLinkRequestFormData(formData: FormData) {
  return spouseLinkRequestSchema.safeParse({
    partner_email: formData.get("partner_email"),
  });
}

export function parseSpouseLinkRespondFormData(formData: FormData) {
  return spouseLinkRespondSchema.safeParse({
    link_id: formData.get("link_id"),
    action: formData.get("action"),
  });
}

export function parseSpouseLinkDissolveFormData(formData: FormData) {
  return spouseLinkDissolveSchema.safeParse({
    link_id: formData.get("link_id"),
  });
}

export function parseReceiptReassignFormData(formData: FormData) {
  return receiptReassignSchema.safeParse({
    receipt_id: formData.get("receipt_id"),
    target_user_id: formData.get("target_user_id"),
  });
}
