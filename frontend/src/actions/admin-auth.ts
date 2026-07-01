"use server";

import { redirect } from "next/navigation";

import type { AuthActionState } from "@/actions/auth.types";
import { ApiClientError } from "@/lib/api/client";
import {
  loginAdminWithFastApi,
  logoutAdminWithFastApi,
} from "@/lib/api/admin-auth";
import {
  clearAdminSessionCookie,
  requireAdminSessionCookieHeader,
} from "@/lib/api/admin-session";
import {
  parseAdminLoginFormData,
  resolveAdminRedirectPath,
} from "@/lib/validations/admin-auth";

function flattenFieldErrors(
  fieldErrors: Record<string, string[] | undefined>,
): Record<string, string[]> {
  return Object.fromEntries(
    Object.entries(fieldErrors)
      .filter((entry): entry is [string, string[]] => !!entry[1]?.length)
      .map(([key, messages]) => [key, messages]),
  );
}

export async function adminLoginAction(
  _prevState: AuthActionState,
  formData: FormData,
): Promise<AuthActionState> {
  const parsed = parseAdminLoginFormData(formData);

  if (!parsed.success) {
    return {
      success: false,
      fieldErrors: flattenFieldErrors(parsed.error.flatten().fieldErrors),
    };
  }

  try {
    const { body } = await loginAdminWithFastApi({
      email: parsed.data.email.toLowerCase(),
      password: parsed.data.password,
    });

    if (!body.success) {
      return {
        success: false,
        error: body.message,
        errorCode: body.code,
      };
    }
  } catch (error) {
    if (error instanceof ApiClientError) {
      return {
        success: false,
        error: error.message,
        errorCode: error.code,
      };
    }
    return {
      success: false,
      error: "Log masuk gagal. Sila cuba lagi.",
      errorCode: "INTERNAL_ERROR",
    };
  }

  redirect(resolveAdminRedirectPath(formData.get("redirect")));
}

export async function adminLogoutAction(): Promise<void> {
  try {
    const cookie = await requireAdminSessionCookieHeader();
    await logoutAdminWithFastApi(cookie);
  } catch {
    // Clear local cookie even if backend logout fails.
  }

  await clearAdminSessionCookie();
  redirect("/admin/login");
}
