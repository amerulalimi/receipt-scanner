import "server-only";

import { apiFetch } from "@/lib/api/client";
import { requireAdminSessionCookieHeader } from "@/lib/api/admin-session";
import type {
  AdminPaginatedOrganizationsData,
  RegistrationStatsData,
} from "@/lib/api/types";

type ListParams = {
  page?: number;
  limit?: number;
  search?: string;
};

type StatsParams = {
  granularity?: "month" | "week" | "custom";
  from?: string;
  to?: string;
};

function buildQuery(params: Record<string, string | number | undefined>) {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== "") {
      query.set(key, String(value));
    }
  }
  const serialized = query.toString();
  return serialized ? `?${serialized}` : "";
}

export async function listAdminOrganizationsWithFastApi(params: ListParams = {}) {
  const cookie = await requireAdminSessionCookieHeader();
  const query = buildQuery({
    page: params.page ?? 1,
    limit: params.limit ?? 50,
    search: params.search,
  });
  return apiFetch<AdminPaginatedOrganizationsData>(
    `/api/v1/admin/organizations${query}`,
    { cookie },
  );
}

export async function fetchAdminOrganizationStatsWithFastApi(
  params: StatsParams = {},
) {
  const cookie = await requireAdminSessionCookieHeader();
  const query = buildQuery({
    granularity: params.granularity ?? "month",
    from: params.from,
    to: params.to,
  });
  return apiFetch<RegistrationStatsData>(
    `/api/v1/admin/organizations/stats${query}`,
    { cookie },
  );
}

export async function deleteAdminOrganizationWithFastApi(orgId: string) {
  const cookie = await requireAdminSessionCookieHeader();
  return apiFetch<{ id: string; status: string }>(
    `/api/v1/admin/organizations/${orgId}`,
    { method: "DELETE", cookie },
  );
}
