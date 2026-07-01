import "server-only";

import { apiFetch } from "@/lib/api/client";
import { requireAdminSessionCookieHeader } from "@/lib/api/admin-session";
import type { OpenRouterHealthData, OpenRouterModelsData, SecretSettingMasked, SystemConfigItem } from "@/lib/api/types";

export async function listSecretsWithFastApi() {
  const cookie = await requireAdminSessionCookieHeader();
  return apiFetch<SecretSettingMasked[]>("/api/v1/config/secrets", { cookie });
}

export async function fetchOpenRouterHealth() {
  const cookie = await requireAdminSessionCookieHeader();
  return apiFetch<OpenRouterHealthData>(
    "/api/v1/config/secrets/openrouter/health",
    { cookie },
  );
}

export async function fetchOpenRouterModels() {
  const cookie = await requireAdminSessionCookieHeader();
  return apiFetch<OpenRouterModelsData>(
    "/api/v1/config/secrets/openrouter/models",
    { cookie },
  );
}

export async function upsertSecretWithFastApi(key: string, value: string) {
  const cookie = await requireAdminSessionCookieHeader();
  return apiFetch<SecretSettingMasked>(`/api/v1/config/secrets/${key}`, {
    method: "PUT",
    body: { value },
    cookie,
  });
}

export async function listSettingsWithFastApi() {
  const cookie = await requireAdminSessionCookieHeader();
  return apiFetch<SystemConfigItem[]>("/api/v1/config/settings", { cookie });
}

export async function upsertSettingWithFastApi(key: string, value: string) {
  const cookie = await requireAdminSessionCookieHeader();
  return apiFetch<SystemConfigItem>(`/api/v1/config/settings/${key}`, {
    method: "PUT",
    body: { value },
    cookie,
  });
}

export async function bulkUpsertSettingsWithFastApi(
  settings: Record<string, string>,
) {
  const cookie = await requireAdminSessionCookieHeader();
  return apiFetch<SystemConfigItem[]>("/api/v1/config/settings", {
    method: "PATCH",
    body: { settings },
    cookie,
  });
}
