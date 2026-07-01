import { createEnv } from "@t3-oss/env-nextjs";
import { z } from "zod";

export const env = createEnv({
  server: {
    NODE_ENV: z.enum(["development", "test", "production"]),
    FASTAPI_URL: z
      .string()
      .url()
      .describe("FastAPI base URL (server-only, no trailing slash)"),
    SESSION_COOKIE_NAME: z
      .string()
      .min(1)
      .default("resit_sess")
      .describe("HttpOnly session cookie name forwarded to FastAPI"),
    SESSION_TTL_SECONDS: z.coerce
      .number()
      .int()
      .positive()
      .default(28800)
      .describe("Session cookie max-age in seconds (match backend)"),
    ADMIN_SESSION_COOKIE_NAME: z
      .string()
      .min(1)
      .default("admin_resit_sess")
      .describe("HttpOnly admin session cookie name forwarded to FastAPI"),
    ADMIN_SESSION_TTL_SECONDS: z.coerce
      .number()
      .int()
      .positive()
      .default(28800)
      .describe("Admin session cookie max-age in seconds (match backend)"),
  },
  client: {
    NEXT_PUBLIC_APP_URL: z
      .string()
      .url()
      .describe("Public app URL for absolute links and CORS alignment"),
  },
  runtimeEnv: {
    NODE_ENV: process.env.NODE_ENV,
    FASTAPI_URL: process.env.FASTAPI_URL,
    SESSION_COOKIE_NAME: process.env.SESSION_COOKIE_NAME,
    SESSION_TTL_SECONDS: process.env.SESSION_TTL_SECONDS,
    ADMIN_SESSION_COOKIE_NAME: process.env.ADMIN_SESSION_COOKIE_NAME,
    ADMIN_SESSION_TTL_SECONDS: process.env.ADMIN_SESSION_TTL_SECONDS,
    NEXT_PUBLIC_APP_URL: process.env.NEXT_PUBLIC_APP_URL,
  },
  emptyStringAsUndefined: true,
  skipValidation: process.env.SKIP_ENV_VALIDATION === "true",
});
