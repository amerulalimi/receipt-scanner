import { z } from "zod";

export const uploadSessionTokenSchema = z
  .string()
  .min(16, "Invalid session token")
  .max(128, "Invalid session token")
  .regex(/^[A-Za-z0-9_-]+$/, "Invalid session token");

export type UploadSessionToken = z.infer<typeof uploadSessionTokenSchema>;

export function parseUploadSessionToken(value: string) {
  return uploadSessionTokenSchema.safeParse(value);
}
