import "server-only";

import { cookies } from "next/headers";

import { env } from "@/env";

export async function getSessionCookieHeader(): Promise<string | null> {
  const cookieStore = await cookies();
  const session = cookieStore.get(env.SESSION_COOKIE_NAME);
  if (!session?.value) {
    return null;
  }
  return `${env.SESSION_COOKIE_NAME}=${session.value}`;
}

export async function requireSessionCookieHeader(): Promise<string> {
  const cookie = await getSessionCookieHeader();
  if (!cookie) {
    throw new Error("UNAUTHORIZED");
  }
  return cookie;
}

export async function clearSessionCookie(): Promise<void> {
  const cookieStore = await cookies();
  cookieStore.delete(env.SESSION_COOKIE_NAME);
}
