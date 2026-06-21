import "server-only";

import { apiFetch } from "@/lib/api/client";
import { requireSessionCookieHeader } from "@/lib/api/session";
import type {
  NotificationListData,
  NotificationPreferenceData,
} from "@/lib/api/types";

export async function fetchNotifications() {
  const cookie = await requireSessionCookieHeader();
  return apiFetch<NotificationListData>("/api/v1/notifications", { cookie });
}

export async function fetchNotificationPreferences() {
  const cookie = await requireSessionCookieHeader();
  return apiFetch<NotificationPreferenceData>(
    "/api/v1/notifications/preferences",
    { cookie },
  );
}

export async function updateNotificationPreferencesWithFastApi(payload: {
  email_enabled?: boolean;
  in_app_enabled?: boolean;
  digest_frequency?: "off" | "monthly";
}) {
  const cookie = await requireSessionCookieHeader();
  return apiFetch<NotificationPreferenceData>(
    "/api/v1/notifications/preferences",
    {
      method: "PATCH",
      body: payload,
      cookie,
    },
  );
}

export async function dismissNotificationWithFastApi(notificationId: string) {
  const cookie = await requireSessionCookieHeader();
  return apiFetch<null>(
    `/api/v1/notifications/${notificationId}/dismiss`,
    {
      method: "POST",
      cookie,
    },
  );
}
