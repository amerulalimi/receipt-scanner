import "server-only";

import { redirect } from "next/navigation";

import { getAdminMeWithFastApi } from "@/lib/api/admin-auth";
import type { AdminMeData } from "@/lib/api/types";

export async function requireAdmin(): Promise<AdminMeData> {
  try {
    const { response, body } = await getAdminMeWithFastApi();

    if (response.status === 401) {
      redirectAfterAdminSessionExpired("/admin");
    }

    if (!body.success) {
      redirect("/admin/login");
    }

    return body.data;
  } catch {
    redirectAfterAdminSessionExpired("/admin");
  }
}

export function redirectAfterAdminSessionExpired(redirectPath: string): never {
  redirect(
    `/api/admin/clear-session?redirect=${encodeURIComponent(redirectPath)}`,
  );
}
