"use server";

import { redirect } from "next/navigation";
import { revalidatePath } from "next/cache";

import type { AuthActionState } from "@/actions/auth.types";
import {
  loginWithFastApi,
  logoutWithFastApi,
  registerWithFastApi,
  resendVerificationWithFastApi,
  verifyEmailWithFastApi,
} from "@/lib/api/auth";
import { getSessionCookieHeader, clearSessionCookie } from "@/lib/api/session";
import {
  parseLoginFormData,
  parseRegisterFormData,
  parseVerifyEmailFormData,
} from "@/lib/validations/auth";

const ALLOWED_REDIRECTS = [
  "/dashboard",
  "/dashboard/receipts",
  "/dashboard/org",
  "/dashboard/settings",
  "/admin",
  "/admin/secrets",
  "/admin/ai",
  "/admin/system",
] as const;

type AllowedRedirect = (typeof ALLOWED_REDIRECTS)[number];

function resolveRedirectPath(value: FormDataEntryValue | null): AllowedRedirect {
  if (
    typeof value === "string" &&
    ALLOWED_REDIRECTS.includes(value as AllowedRedirect)
  ) {
    return value as AllowedRedirect;
  }
  return "/dashboard";
}

function flattenFieldErrors(
  fieldErrors: Record<string, string[] | undefined>,
): Record<string, string[]> {
  return Object.fromEntries(
    Object.entries(fieldErrors)
      .filter((entry): entry is [string, string[]] => !!entry[1]?.length)
      .map(([key, messages]) => [key, messages]),
  );
}

export async function loginAction(
  _prevState: AuthActionState,
  formData: FormData,
): Promise<AuthActionState> {
  const parsed = parseLoginFormData(formData);

  if (!parsed.success) {
    return {
      fieldErrors: flattenFieldErrors(parsed.error.flatten().fieldErrors),
    };
  }

  const { body } = await loginWithFastApi({
    email: parsed.data.email.toLowerCase(),
    password: parsed.data.password,
  });

  if (!body.success) {
    return { error: body.message };
  }

  redirect(resolveRedirectPath(formData.get("redirect")));
}

export async function registerAction(
  _prevState: AuthActionState,
  formData: FormData,
): Promise<AuthActionState> {
  const parsed = parseRegisterFormData(formData);

  if (!parsed.success) {
    return {
      fieldErrors: flattenFieldErrors(parsed.error.flatten().fieldErrors),
    };
  }

  const { body } = await registerWithFastApi({
    email: parsed.data.email.toLowerCase(),
    password: parsed.data.password,
    full_name: parsed.data.full_name.trim(),
    account_type: parsed.data.account_type,
  });

  if (!body.success) {
    return { error: body.message };
  }

  redirect("/login?registered=1");
}

export async function logoutAction() {
  const cookie = await getSessionCookieHeader();

  if (cookie) {
    try {
      await logoutWithFastApi(cookie);
    } catch {
      // Still clear local cookie if API unreachable.
    }
  }

  await clearSessionCookie();
  redirect("/login");
}

export type VerifyEmailActionState = {
  error?: string;
  success?: boolean;
};

export async function verifyEmailAction(
  _prevState: VerifyEmailActionState,
  formData: FormData,
): Promise<VerifyEmailActionState> {
  const parsed = parseVerifyEmailFormData(formData);

  if (!parsed.success) {
    return { error: "Invalid verification token." };
  }

  const { body } = await verifyEmailWithFastApi(parsed.data.token);

  if (!body.success) {
    return { error: body.message };
  }

  return { success: true };
}

export type ResendVerificationActionState = {
  error?: string;
  success?: boolean;
  message?: string;
};

export async function resendVerificationAction(): Promise<ResendVerificationActionState> {
  const cookie = await getSessionCookieHeader();
  if (!cookie) {
    return { error: "Please log in again." };
  }

  const { body } = await resendVerificationWithFastApi(cookie);

  if (!body.success) {
    return { error: body.message };
  }

  revalidatePath("/dashboard");
  return { success: true, message: body.message ?? "Verification email resent." };
}
