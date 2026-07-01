import "server-only";

import { cookies } from "next/headers";

import { env } from "@/env";

export async function getAdminSessionCookieHeader(): Promise<string | null> {
  const cookieStore = await cookies();
  const session = cookieStore.get(env.ADMIN_SESSION_COOKIE_NAME);
  if (!session?.value) {
    return null;
  }
  return `${env.ADMIN_SESSION_COOKIE_NAME}=${session.value}`;
}

export async function requireAdminSessionCookieHeader(): Promise<string> {
  const cookie = await getAdminSessionCookieHeader();
  if (!cookie) {
    throw new Error("UNAUTHORIZED");
  }
  return cookie;
}

export async function clearAdminSessionCookie(): Promise<void> {
  const cookieStore = await cookies();
  cookieStore.delete(env.ADMIN_SESSION_COOKIE_NAME);
}
