import "server-only";

import { apiFetch } from "@/lib/api/client";
import { requireSessionCookieHeader } from "@/lib/api/session";
import type {
  AuditLogListData,
  ReliefCategoryItem,
  ReliefLimitItem,
  RetentionPurgeData,
  SystemOverviewData,
} from "@/lib/api/types";

export async function fetchSystemOverview() {
  const cookie = await requireSessionCookieHeader();
  return apiFetch<SystemOverviewData>("/api/v1/config/system/overview", {
    cookie,
  });
}

export async function fetchReliefLimits() {
  const cookie = await requireSessionCookieHeader();
  return apiFetch<ReliefLimitItem[]>("/api/v1/config/relief-limits", {
    cookie,
  });
}

export async function fetchReliefCategories() {
  const cookie = await requireSessionCookieHeader();
  return apiFetch<ReliefCategoryItem[]>("/api/v1/config/relief-categories", {
    cookie,
  });
}

export async function createReliefLimitWithFastApi(payload: {
  category: string;
  limit_amount: number;
  be_seksyen?: string | null;
  description_my: string;
  sort_order?: number;
}) {
  const cookie = await requireSessionCookieHeader();
  return apiFetch<ReliefLimitItem>("/api/v1/config/relief-limits", {
    method: "POST",
    body: payload,
    cookie,
  });
}

export async function updateReliefLimitWithFastApi(
  category: string,
  payload: {
    limit_amount?: number;
    be_seksyen?: string | null;
    description_my?: string | null;
    is_active?: boolean;
    sort_order?: number;
  },
) {
  const cookie = await requireSessionCookieHeader();
  return apiFetch<ReliefLimitItem>(`/api/v1/config/relief-limits/${category}`, {
    method: "PATCH",
    body: payload,
    cookie,
  });
}

export async function deactivateReliefLimitWithFastApi(category: string) {
  const cookie = await requireSessionCookieHeader();
  return apiFetch<ReliefLimitItem>(
    `/api/v1/config/relief-limits/${category}`,
    {
      method: "DELETE",
      cookie,
    },
  );
}

export async function fetchAuditLogs(params?: {
  action?: string;
  page?: number;
  limit?: number;
}) {
  const cookie = await requireSessionCookieHeader();
  const searchParams = new URLSearchParams({
    page: String(params?.page ?? 1),
    limit: String(params?.limit ?? 50),
  });
  if (params?.action) {
    searchParams.set("action", params.action);
  }

  return apiFetch<AuditLogListData>(
    `/api/v1/config/audit-logs?${searchParams.toString()}`,
    { cookie },
  );
}

export async function purgeRetentionWithFastApi() {
  const cookie = await requireSessionCookieHeader();
  return apiFetch<RetentionPurgeData>("/api/v1/config/system/purge-retention", {
    method: "POST",
    cookie,
  });
}
