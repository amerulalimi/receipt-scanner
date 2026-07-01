"use server";

import { revalidatePath } from "next/cache";

import type { SettingsActionState } from "@/actions/settings.types";
import { getSessionCookieHeader } from "@/lib/api/session";
import {
  fetchSessionsWithFastApi,
  revokeSessionWithFastApi,
  updateMeWithFastApi,
} from "@/lib/api/auth";
import {
  parseNotificationPreferencesFormData,
  parseRevokeSessionFormData,
  parseSettingsProfileFormData,
} from "@/lib/validations/settings";
import { updateNotificationPreferencesWithFastApi } from "@/lib/api/notifications";

function flattenFieldErrors(
  fieldErrors: Record<string, string[] | undefined>,
): Record<string, string[]> {
  return Object.fromEntries(
    Object.entries(fieldErrors)
      .filter((entry): entry is [string, string[]] => !!entry[1]?.length)
      .map(([key, messages]) => [key, messages]),
  );
}

function revalidateSettingsPaths() {
  revalidatePath("/dashboard");
  revalidatePath("/dashboard/settings");
}

export async function updateSettingsProfileAction(
  _prevState: SettingsActionState,
  formData: FormData,
): Promise<SettingsActionState> {
  const parsed = parseSettingsProfileFormData(formData);

  if (!parsed.success) {
    return {
      fieldErrors: flattenFieldErrors(parsed.error.flatten().fieldErrors),
    };
  }

  const cookie = await getSessionCookieHeader();
  if (!cookie) {
    return { error: "Please log in again." };
  }

  const body = await updateMeWithFastApi(cookie, parsed.data);
  if (!body.success) {
    return { error: body.message };
  }

  revalidateSettingsPaths();
  return { success: true, message: body.message ?? "Settings saved." };
}

export async function revokeSessionAction(
  _prevState: SettingsActionState,
  formData: FormData,
): Promise<SettingsActionState> {
  const parsed = parseRevokeSessionFormData(formData);
  if (!parsed.success) {
    return { error: "Invalid session." };
  }

  const cookie = await getSessionCookieHeader();
  if (!cookie) {
    return { error: "Please log in again." };
  }

  const { body } = await revokeSessionWithFastApi(cookie, parsed.data.session_id);
  if (!body.success) {
    return { error: body.message };
  }

  revalidateSettingsPaths();
  return { success: true, message: body.message ?? "Session ended." };
}

export async function getSessionsForSettings() {
  const cookie = await getSessionCookieHeader();
  if (!cookie) {
    throw new Error("UNAUTHORIZED");
  }
  return fetchSessionsWithFastApi(cookie);
}

export async function updateNotificationPreferencesAction(
  _prevState: SettingsActionState,
  formData: FormData,
): Promise<SettingsActionState> {
  const parsed = parseNotificationPreferencesFormData(formData);

  if (!parsed.success) {
    return {
      fieldErrors: flattenFieldErrors(parsed.error.flatten().fieldErrors),
    };
  }

  const { body } = await updateNotificationPreferencesWithFastApi(parsed.data);
  if (!body.success) {
    return { error: body.message };
  }

  revalidateSettingsPaths();
  return { success: true, message: body.message ?? "Notification preferences saved." };
}
