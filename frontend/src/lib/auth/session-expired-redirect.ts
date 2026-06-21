import "server-only";

import { redirect } from "next/navigation";

export function redirectAfterSessionExpired(redirectPath: string): never {
  redirect(
    `/api/auth/clear-session?redirect=${encodeURIComponent(redirectPath)}`,
  );
}
