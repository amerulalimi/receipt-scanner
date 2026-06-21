import "server-only";

import { apiFetch } from "@/lib/api/client";
import { requireSessionCookieHeader } from "@/lib/api/session";
import type { MeData } from "@/lib/api/types";

export async function getMeWithFastApi() {
  const cookie = await requireSessionCookieHeader();
  return apiFetch<MeData>("/api/v1/auth/me", { cookie });
}
