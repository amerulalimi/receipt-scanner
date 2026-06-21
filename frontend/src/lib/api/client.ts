import "server-only";

import { cookies } from "next/headers";

import { env } from "@/env";

import type { ApiResponse } from "./types";

const SESSION_MAX_AGE = env.SESSION_TTL_SECONDS;

type FetchOptions = {
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  body?: unknown;
  cookie?: string;
};

export async function apiFetch<T>(
  path: string,
  options: FetchOptions = {},
): Promise<{ response: Response; body: ApiResponse<T> }> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };

  if (options.cookie) {
    headers.Cookie = options.cookie;
  }

  const response = await fetch(`${env.FASTAPI_URL}${path}`, {
    method: options.method ?? "GET",
    headers,
    body: options.body ? JSON.stringify(options.body) : undefined,
    cache: "no-store",
  });

  const body = (await response.json()) as ApiResponse<T>;
  return { response, body };
}

type UploadFetchOptions = {
  formData: FormData;
  cookie: string;
};

export async function apiUploadFetch<T>(
  path: string,
  options: UploadFetchOptions,
): Promise<{ response: Response; body: ApiResponse<T> }> {
  const response = await fetch(`${env.FASTAPI_URL}${path}`, {
    method: "POST",
    headers: {
      Cookie: options.cookie,
    },
    body: options.formData,
    cache: "no-store",
  });

  const body = (await response.json()) as ApiResponse<T>;
  return { response, body };
}

export async function apiPublicUploadFetch<T>(
  path: string,
  formData: FormData,
): Promise<{ response: Response; body: ApiResponse<T> }> {
  const response = await fetch(`${env.FASTAPI_URL}${path}`, {
    method: "POST",
    body: formData,
    cache: "no-store",
  });

  const body = (await response.json()) as ApiResponse<T>;
  return { response, body };
}

export async function forwardSessionCookie(response: Response): Promise<void> {
  const cookieStore = await cookies();
  const setCookieHeaders =
    typeof response.headers.getSetCookie === "function"
      ? response.headers.getSetCookie()
      : [];

  const fallback = response.headers.get("set-cookie");
  if (setCookieHeaders.length === 0 && fallback) {
    setCookieHeaders.push(fallback);
  }

  for (const header of setCookieHeaders) {
    if (!header.startsWith(`${env.SESSION_COOKIE_NAME}=`)) {
      continue;
    }

    const [nameValue] = header.split(";");
    const value = nameValue.slice(env.SESSION_COOKIE_NAME.length + 1);

    cookieStore.set(env.SESSION_COOKIE_NAME, value, {
      httpOnly: true,
      secure: env.NODE_ENV === "production",
      sameSite: "lax",
      path: "/",
      maxAge: SESSION_MAX_AGE,
    });
    return;
  }
}

export function buildSessionCookieHeader(sessionId: string): string {
  return `${env.SESSION_COOKIE_NAME}=${sessionId}`;
}
