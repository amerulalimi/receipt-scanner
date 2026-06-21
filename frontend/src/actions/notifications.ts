"use server";

import { revalidatePath } from "next/cache";

import type { DismissNotificationState } from "@/actions/notifications.types";
import { dismissNotificationWithFastApi } from "@/lib/api/notifications";

export async function dismissNotificationAction(
  _prevState: DismissNotificationState,
  formData: FormData,
): Promise<DismissNotificationState> {
  const notificationId = formData.get("notification_id");
  if (typeof notificationId !== "string" || notificationId.length === 0) {
    return { error: "Invalid notification." };
  }

  const { body } = await dismissNotificationWithFastApi(notificationId);
  if (!body.success) {
    return { error: body.message };
  }

  revalidatePath("/dashboard");
  return { success: true };
}
