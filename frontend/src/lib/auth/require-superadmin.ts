import "server-only";

import { redirect } from "next/navigation";

import { getMeWithFastApi } from "@/lib/api/auth-me";
import { redirectAfterSessionExpired } from "@/lib/auth/session-expired-redirect";
import type { MeData } from "@/lib/api/types";

export async function requireSuperadmin(): Promise<MeData> {
  try {
    const { response, body } = await getMeWithFastApi();

    if (response.status === 401) {
      redirectAfterSessionExpired("/admin");
    }

    if (!body.success) {
      redirect("/dashboard");
    }

    if (body.data.role !== "superadmin") {
      redirect("/dashboard");
    }

    return body.data;
  } catch {
    redirectAfterSessionExpired("/admin");
  }
}
