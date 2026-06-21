import "server-only";

import { getMeWithFastApi } from "@/lib/api/auth-me";
import { redirectAfterSessionExpired } from "@/lib/auth/session-expired-redirect";
import type { MeData } from "@/lib/api/types";

export async function requireAuth(redirectPath = "/dashboard"): Promise<MeData> {
  try {
    const { response, body } = await getMeWithFastApi();

    if (response.status === 401 || !body.success) {
      redirectAfterSessionExpired(redirectPath);
    }

    return body.data;
  } catch {
    redirectAfterSessionExpired(redirectPath);
  }
}
