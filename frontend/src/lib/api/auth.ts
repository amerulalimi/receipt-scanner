import "server-only";

import { apiFetch, forwardSessionCookie, get, patch, post } from "./client";
import type {
  LoginData,
  MeData,
  RegisterData,
  SessionInfo,
} from "./types";
import { getSessionCookieHeader } from "./session";

export async function loginWithFastApi(credentials: {
  email: string;
  password: string;
  login_context: "individual" | "corporate";
}) {
  const { response, body } = await apiFetch<LoginData>("/api/v1/auth/login", {
    method: "POST",
    body: credentials,
  });

  if (body.success) {
    await forwardSessionCookie(response);
  }

  return { response, body };
}

export async function registerWithFastApi(payload: {
  email: string;
  password: string;
  full_name: string;
  account_type: "individual" | "corporate";
}) {
  const { response, body } = await apiFetch<RegisterData>(
    "/api/v1/auth/register",
    {
      method: "POST",
      body: payload,
    },
  );

  if (body.success) {
    await forwardSessionCookie(response);
  }

  return { response, body };
}

export async function logoutWithFastApi(cookie: string) {
  return apiFetch<null>("/api/v1/auth/logout", {
    method: "POST",
    cookie,
  });
}

export async function refreshSessionWithFastApi(cookie: string) {
  const { response, body } = await apiFetch<null>("/api/v1/auth/refresh", {
    method: "POST",
    cookie,
  });

  if (body.success) {
    await forwardSessionCookie(response);
  }

  return { response, body };
}

export async function verifyEmailWithFastApi(token: string) {
  return post<null>("/api/v1/auth/verify-email", { token });
}

export async function resendVerificationWithFastApi(cookie: string) {
  return post<null>("/api/v1/auth/resend-verification", undefined, cookie);
}

export async function fetchMeWithFastApi(cookie: string) {
  return get<MeData>("/api/v1/auth/me", cookie);
}

export async function updateMeWithFastApi(
  cookie: string,
  payload: {
    full_name?: string;
    tax_year?: number;
    tax_bracket?: number | null;
  },
) {
  return patch<MeData>("/api/v1/auth/me", payload, cookie);
}

export async function fetchSessionsWithFastApi(cookie: string) {
  return apiFetch<SessionInfo[]>("/api/v1/auth/sessions", { cookie });
}

export async function revokeSessionWithFastApi(
  cookie: string,
  sessionId: string,
) {
  return apiFetch<null>(`/api/v1/auth/sessions/${sessionId}`, {
    method: "DELETE",
    cookie,
  });
}

export async function refreshSessionIfPresent() {
  const cookie = await getSessionCookieHeader();
  if (!cookie) {
    return null;
  }

  return refreshSessionWithFastApi(cookie);
}
