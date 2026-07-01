import "server-only";

import { cookies } from "next/headers";

import { env } from "@/env";

import type { ApiErrorResponse, ApiResponse } from "./types";

const SESSION_MAX_AGE = env.SESSION_TTL_SECONDS;
const BASE_URL = env.FASTAPI_URL;

export class ApiClientError extends Error {
  code: string;

  constructor(message: string, code: string) {
    super(message);
    this.name = "ApiClientError";
    this.code = code;
  }
}

type ApiClientOptions = {
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  body?: unknown;
  cookie?: string;
  headers?: Record<string, string>;
};

export async function apiClient<T>(
  path: string,
  options: ApiClientOptions = {},
): Promise<ApiResponse<T>> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...options.headers,
  };

  if (options.cookie) {
    headers.Cookie = options.cookie;
  }

  const response = await fetch(`${BASE_URL}${path}`, {
    method: options.method ?? "GET",
    headers,
    body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
    cache: "no-store",
    credentials: "include",
  });

  const body = (await response.json()) as ApiResponse<T>;

  if (!response.ok || !body.success) {
    const errorBody = body as ApiErrorResponse;
    throw new ApiClientError(
      errorBody.message ?? "Request failed",
      errorBody.code ?? "INTERNAL_ERROR",
    );
  }

  return body;
}

export async function get<T>(path: string, cookie?: string) {
  return apiClient<T>(path, { method: "GET", cookie });
}

export async function post<T>(path: string, body?: unknown, cookie?: string) {
  return apiClient<T>(path, { method: "POST", body, cookie });
}

export async function patch<T>(path: string, body?: unknown, cookie?: string) {
  return apiClient<T>(path, { method: "PATCH", body, cookie });
}

export async function del<T>(path: string, cookie?: string) {
  return apiClient<T>(path, { method: "DELETE", cookie });
}

type LegacyFetchOptions = {
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  body?: unknown;
  cookie?: string;
};

/** @deprecated Prefer get/post/patch/del — kept for modules not yet migrated */
export async function apiFetch<T>(
  path: string,
  options: LegacyFetchOptions = {},
): Promise<{ response: Response; body: ApiResponse<T> }> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };

  if (options.cookie) {
    headers.Cookie = options.cookie;
  }

  const response = await fetch(`${BASE_URL}${path}`, {
    method: options.method ?? "GET",
    headers,
    body: options.body ? JSON.stringify(options.body) : undefined,
    cache: "no-store",
    credentials: "include",
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
  const response = await fetch(`${BASE_URL}${path}`, {
    method: "POST",
    headers: {
      Cookie: options.cookie,
    },
    body: options.formData,
    cache: "no-store",
    credentials: "include",
  });

  const body = (await response.json()) as ApiResponse<T>;
  return { response, body };
}

export async function apiPublicUploadFetch<T>(
  path: string,
  formData: FormData,
): Promise<{ response: Response; body: ApiResponse<T> }> {
  const response = await fetch(`${BASE_URL}${path}`, {
    method: "POST",
    body: formData,
    cache: "no-store",
    credentials: "include",
  });

  const body = (await response.json()) as ApiResponse<T>;
  return { response, body };
}

export async function forwardSessionCookie(response: Response): Promise<void> {
  await forwardNamedSessionCookie(
    response,
    env.SESSION_COOKIE_NAME,
    SESSION_MAX_AGE,
  );
}

export async function forwardAdminSessionCookie(response: Response): Promise<void> {
  await forwardNamedSessionCookie(
    response,
    env.ADMIN_SESSION_COOKIE_NAME,
    env.ADMIN_SESSION_TTL_SECONDS,
  );
}

async function forwardNamedSessionCookie(
  response: Response,
  cookieName: string,
  maxAge: number,
): Promise<void> {
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
    if (!header.startsWith(`${cookieName}=`)) {
      continue;
    }

    const [nameValue] = header.split(";");
    const value = nameValue.slice(cookieName.length + 1);

    cookieStore.set(cookieName, value, {
      httpOnly: true,
      secure: env.NODE_ENV === "production",
      sameSite: "lax",
      path: "/",
      maxAge,
    });
    return;
  }

  if (setCookieHeaders.length > 0) {
    const header = setCookieHeaders[0];
    const equalsIndex = header.indexOf("=");
    if (equalsIndex > 0) {
      const semicolonIndex = header.indexOf(";");
      const value =
        semicolonIndex === -1
          ? header.slice(equalsIndex + 1)
          : header.slice(equalsIndex + 1, semicolonIndex);

      cookieStore.set(cookieName, value, {
        httpOnly: true,
        secure: env.NODE_ENV === "production",
        sameSite: "lax",
        path: "/",
        maxAge,
      });
    }
  }
}

export function buildSessionCookieHeader(sessionId: string): string {
  return `${env.SESSION_COOKIE_NAME}=${sessionId}`;
}
