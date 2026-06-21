import { cookies } from "next/headers";
import { NextRequest, NextResponse } from "next/server";

import { env } from "@/env";

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

function resolveRedirectPath(value: string | null): string {
  if (
    value &&
    ALLOWED_REDIRECTS.includes(value as (typeof ALLOWED_REDIRECTS)[number])
  ) {
    return value;
  }
  return "/dashboard";
}

export async function GET(request: NextRequest) {
  const cookieStore = await cookies();
  cookieStore.delete(env.SESSION_COOKIE_NAME);

  const redirectPath = resolveRedirectPath(
    request.nextUrl.searchParams.get("redirect"),
  );
  const loginUrl = new URL("/login", request.url);
  loginUrl.searchParams.set("redirect", redirectPath);

  return NextResponse.redirect(loginUrl);
}
