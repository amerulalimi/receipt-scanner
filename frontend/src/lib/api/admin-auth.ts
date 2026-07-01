import "server-only";

import { apiFetch, forwardAdminSessionCookie } from "./client";
import type { AdminMeData } from "./types";
import {
  getAdminSessionCookieHeader,
  requireAdminSessionCookieHeader,
} from "./admin-session";

export async function loginAdminWithFastApi(credentials: {
  email: string;
  password: string;
}) {
  const { response, body } = await apiFetch<AdminMeData>(
    "/api/v1/admin/auth/login",
    {
      method: "POST",
      body: credentials,
    },
  );

  if (body.success) {
    await forwardAdminSessionCookie(response);
  }

  return { response, body };
}

export async function getAdminMeWithFastApi() {
  const cookie = await getAdminSessionCookieHeader();
  return apiFetch<AdminMeData>("/api/v1/admin/auth/me", { cookie: cookie ?? undefined });
}

export async function logoutAdminWithFastApi(cookie: string) {
  return apiFetch<null>("/api/v1/admin/auth/logout", {
    method: "POST",
    cookie,
  });
}

export async function requireAdminMeWithFastApi() {
  const cookie = await requireAdminSessionCookieHeader();
  return apiFetch<AdminMeData>("/api/v1/admin/auth/me", { cookie });
}
