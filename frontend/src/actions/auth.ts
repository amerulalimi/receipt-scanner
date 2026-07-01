"use server";

import { redirect } from "next/navigation";
import { revalidatePath } from "next/cache";

import type { AuthActionState } from "@/actions/auth.types";
import {
  loginWithFastApi,
  logoutWithFastApi,
  registerWithFastApi,
  resendVerificationWithFastApi,
  fetchMeWithFastApi,
  updateMeWithFastApi,
  verifyEmailWithFastApi,
} from "@/lib/api/auth";
import { ApiClientError } from "@/lib/api/client";
import type { MeData } from "@/lib/api/types";
import { getSessionCookieHeader, clearSessionCookie } from "@/lib/api/session";
import {
  parseLoginFormData,
  parseRegisterFormData,
  parseVerifyEmailFormData,
  updateProfileSchema,
} from "@/lib/validations/auth";

const ALLOWED_REDIRECTS = [
  "/dashboard",
  "/dashboard/receipts",
  "/dashboard/org",
  "/dashboard/settings",
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

function resolvePostLoginDefault(activeContext: "individual" | "corporate"): AllowedRedirect {
  return activeContext === "corporate" ? "/dashboard/org" : "/dashboard";
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
      success: false,
      fieldErrors: flattenFieldErrors(parsed.error.flatten().fieldErrors),
    };
  }

  let loginResult;
  try {
    loginResult = await loginWithFastApi({
      email: parsed.data.email.toLowerCase(),
      password: parsed.data.password,
      login_context: parsed.data.login_context,
    });
  } catch (err) {
    if (err instanceof ApiClientError) {
      const message =
        err.code === "INVALID_CREDENTIALS"
          ? "E-mel atau kata laluan tidak sah"
          : err.message;
      return { success: false, error: message, errorCode: err.code };
    }
    return { success: false, error: "Ralat log masuk. Sila cuba lagi." };
  }

  const { body } = loginResult;

  if (!body.success) {
    return {
      success: false,
      error: body.message,
      errorCode: body.code,
    };
  }

  const requestedRedirect = formData.get("redirect");
  const redirectTarget =
    typeof requestedRedirect === "string" && requestedRedirect.length > 0
      ? resolveRedirectPath(requestedRedirect)
      : resolvePostLoginDefault(body.data.active_context);

  redirect(redirectTarget);
}

export async function registerAction(
  _prevState: AuthActionState,
  formData: FormData,
): Promise<AuthActionState> {
  const parsed = parseRegisterFormData(formData);

  if (!parsed.success) {
    return {
      success: false,
      fieldErrors: flattenFieldErrors(parsed.error.flatten().fieldErrors),
    };
  }

  let registerResult;
  try {
    registerResult = await registerWithFastApi({
      email: parsed.data.email.toLowerCase(),
      password: parsed.data.password,
      full_name: parsed.data.full_name.trim(),
      account_type: parsed.data.account_type,
    });
  } catch (err) {
    if (err instanceof ApiClientError) {
      return { success: false, error: err.message, errorCode: err.code };
    }
    return { success: false, error: "Ralat pendaftaran. Sila cuba lagi." };
  }

  const { body } = registerResult;

  if (!body.success) {
    return {
      success: false,
      error: body.message,
      errorCode: body.code,
    };
  }

  redirect(
    parsed.data.account_type === "corporate"
      ? "/dashboard/org?registered=1"
      : "/dashboard?registered=1",
  );
}

export async function logoutAction(): Promise<void> {
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

export async function getMeAction(): Promise<AuthActionState<MeData>> {
  const cookie = await getSessionCookieHeader();
  if (!cookie) {
    return { success: false, error: "Sesi tidak sah." };
  }

  try {
    const body = await fetchMeWithFastApi(cookie);
    return { success: true, data: body.data };
  } catch (err) {
    if (err instanceof ApiClientError) {
      return { success: false, error: err.message, errorCode: err.code };
    }
    return { success: false, error: "Gagal memuatkan profil." };
  }
}

export async function updateProfileAction(
  _prevState: AuthActionState<MeData>,
  formData: FormData,
): Promise<AuthActionState<MeData>> {
  const parsed = updateProfileSchema.safeParse({
    full_name: formData.get("full_name") || undefined,
    tax_year: formData.get("tax_year")
      ? Number(formData.get("tax_year"))
      : undefined,
    tax_bracket: formData.get("tax_bracket")
      ? Number(formData.get("tax_bracket"))
      : undefined,
  });

  if (!parsed.success) {
    return {
      success: false,
      fieldErrors: flattenFieldErrors(parsed.error.flatten().fieldErrors),
    };
  }

  const cookie = await getSessionCookieHeader();
  if (!cookie) {
    return { success: false, error: "Sesi tidak sah." };
  }

  try {
    const body = await updateMeWithFastApi(cookie, parsed.data);
    revalidatePath("/dashboard/settings");
    return { success: true, data: body.data };
  } catch (err) {
    if (err instanceof ApiClientError) {
      return { success: false, error: err.message, errorCode: err.code };
    }
    return { success: false, error: "Gagal mengemas kini profil." };
  }
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

  try {
    await verifyEmailWithFastApi(parsed.data.token);
    return { success: true };
  } catch (err) {
    if (err instanceof ApiClientError) {
      return { error: err.message };
    }
    return { error: "Verification failed." };
  }
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

  try {
    const body = await resendVerificationWithFastApi(cookie);
    revalidatePath("/dashboard");
    return {
      success: true,
      message: body.message ?? "Verification email resent.",
    };
  } catch (err) {
    if (err instanceof ApiClientError) {
      return { error: err.message };
    }
    return { error: "Failed to resend verification email." };
  }
}
