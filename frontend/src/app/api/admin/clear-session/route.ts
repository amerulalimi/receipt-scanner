import { cookies } from "next/headers";
import { NextRequest, NextResponse } from "next/server";

import { env } from "@/env";

const ALLOWED_REDIRECTS = [
  "/admin",
  "/admin/secrets",
  "/admin/ai",
  "/admin/system",
] as const;

function resolveRedirectPath(value: string | null): string {
  if (
    value &&
    ALLOWED_REDIRECTS.includes(value as (typeof ALLOWED_REDIRECTS)[number])
  ) {
    return value;
  }
  return "/admin";
}

export async function GET(request: NextRequest) {
  const cookieStore = await cookies();
  cookieStore.delete(env.ADMIN_SESSION_COOKIE_NAME);

  const redirectPath = resolveRedirectPath(
    request.nextUrl.searchParams.get("redirect"),
  );
  const loginUrl = new URL("/admin/login", request.url);
  loginUrl.searchParams.set("redirect", redirectPath);

  return NextResponse.redirect(loginUrl);
}
