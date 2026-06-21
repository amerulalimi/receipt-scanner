import { z } from "zod";

export const ALLOWED_SECRET_KEYS = ["openrouter_api_key"] as const;

export const secretUpdateSchema = z.object({
  key: z.enum(ALLOWED_SECRET_KEYS),
  value: z
    .string()
    .min(1, "Secret value is required.")
    .max(4096)
    .refine((value) => !/https?:\/\//i.test(value), {
      message:
        "This looks like a URL, not an API key. Use a key from openrouter.ai/keys (sk-or-v1-...).",
    })
    .refine((value) => value.startsWith("sk-or-"), {
      message: "OpenRouter API key must start with sk-or-.",
    }),
});

export type SecretUpdateFormValues = z.infer<typeof secretUpdateSchema>;

export const aiConfigSchema = z.object({
  openrouter_vision_model: z
    .string()
    .min(1, "Model is required.")
    .max(256),
  receipt_processing_enabled: z.enum(["true", "false"]),
});

export type AiConfigFormValues = z.infer<typeof aiConfigSchema>;

export function parseSecretFormData(formData: FormData) {
  return secretUpdateSchema.safeParse({
    key: formData.get("key"),
    value: formData.get("value"),
  });
}

export function parseAiConfigFormData(formData: FormData) {
  return aiConfigSchema.safeParse({
    openrouter_vision_model: formData.get("openrouter_vision_model"),
    receipt_processing_enabled: formData.get("receipt_processing_enabled"),
  });
}
