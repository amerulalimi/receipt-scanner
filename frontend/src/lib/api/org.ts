import "server-only";

import { apiFetch, forwardSessionCookie } from "@/lib/api/client";
import { requireSessionCookieHeader } from "@/lib/api/session";
import { env } from "@/env";
import type {
  InviteAcceptData,
  InviteCreateData,
  InviteValidateData,
  OrgAnalyticsData,
  OrgEmployeeBulkImportData,
  OrgEmployeeListData,
  OrgBulkApproveData,
  OrgMeData,
  OrgPendingReceiptListData,
  OrgPolicyData,
  OrgRegisterData,
} from "@/lib/api/types";

export async function fetchOrgMe() {
  const cookie = await requireSessionCookieHeader();
  return apiFetch<OrgMeData>("/api/v1/org/me", { cookie });
}

export async function registerOrgWithFastApi(payload: {
  name: string;
  ssm_number: string;
  email_domain: string;
}) {
  const cookie = await requireSessionCookieHeader();
  return apiFetch<OrgRegisterData>("/api/v1/org/register", {
    method: "POST",
    body: payload,
    cookie,
  });
}

export async function updateOrgPolicyWithFastApi(payload: {
  allowed_categories: string[];
  require_hr_approval: boolean;
  max_receipts_per_month: number;
  tax_year: number;
}) {
  const cookie = await requireSessionCookieHeader();
  return apiFetch<OrgPolicyData>("/api/v1/org/policy", {
    method: "PATCH",
    body: payload,
    cookie,
  });
}

export async function fetchOrgEmployees(params?: {
  search?: string;
  status?: string;
  page?: number;
  limit?: number;
}) {
  const cookie = await requireSessionCookieHeader();
  const searchParams = new URLSearchParams({
    page: String(params?.page ?? 1),
    limit: String(params?.limit ?? 20),
  });
  if (params?.search) {
    searchParams.set("search", params.search);
  }
  if (params?.status) {
    searchParams.set("status", params.status);
  }

  return apiFetch<OrgEmployeeListData>(
    `/api/v1/org/employees?${searchParams.toString()}`,
    { cookie },
  );
}

export async function fetchOrgPendingReceipts(params?: {
  tax_year?: number;
  page?: number;
  limit?: number;
}) {
  const cookie = await requireSessionCookieHeader();
  const searchParams = new URLSearchParams({
    page: String(params?.page ?? 1),
    limit: String(params?.limit ?? 20),
  });
  if (params?.tax_year) {
    searchParams.set("tax_year", String(params.tax_year));
  }

  return apiFetch<OrgPendingReceiptListData>(
    `/api/v1/org/pending-receipts?${searchParams.toString()}`,
    { cookie },
  );
}

export async function reviewReceiptWithFastApi(
  receiptId: string,
  payload: { action: "approve" | "reject"; comment?: string },
) {
  const cookie = await requireSessionCookieHeader();
  return apiFetch(`/api/v1/receipts/${receiptId}/review`, {
    method: "POST",
    body: payload,
    cookie,
  });
}

export async function bulkApproveOrgPendingWithFastApi(taxYear?: number) {
  const cookie = await requireSessionCookieHeader();
  const query = taxYear ? `?tax_year=${taxYear}` : "";
  return apiFetch<OrgBulkApproveData>(
    `/api/v1/org/pending-receipts/bulk-approve${query}`,
    {
      method: "POST",
      cookie,
    },
  );
}

export async function updateOrgEmployeeWithFastApi(
  userId: string,
  payload: { is_active: boolean },
) {
  const cookie = await requireSessionCookieHeader();
  return apiFetch(`/api/v1/org/employees/${userId}`, {
    method: "PATCH",
    body: payload,
    cookie,
  });
}

export async function removeOrgEmployeeWithFastApi(userId: string) {
  const cookie = await requireSessionCookieHeader();
  return apiFetch<null>(`/api/v1/org/employees/${userId}`, {
    method: "DELETE",
    cookie,
  });
}

export async function inviteEmployeesWithFastApi(payload: {
  type: "link" | "email";
  emails?: string[];
}) {
  const cookie = await requireSessionCookieHeader();
  return apiFetch<InviteCreateData>("/api/v1/invites/employees", {
    method: "POST",
    body: payload,
    cookie,
  });
}

export async function inviteHrAdminWithFastApi(payload: { email: string }) {
  const cookie = await requireSessionCookieHeader();
  return apiFetch<InviteCreateData>("/api/v1/invites/hr-admin", {
    method: "POST",
    body: payload,
    cookie,
  });
}

export async function validateInviteWithFastApi(token: string) {
  return apiFetch<InviteValidateData>(`/api/v1/invites/validate/${token}`);
}

export async function acceptInviteWithFastApi(payload: {
  token: string;
  email: string;
  password: string;
  full_name: string;
}) {
  const { response, body } = await apiFetch<InviteAcceptData>(
    "/api/v1/invites/accept",
    {
      method: "POST",
      body: payload,
    },
  );

  if (body.success) {
    await forwardSessionCookie(response);
  }

  return { response, body };
}

export async function fetchOrgAnalytics(taxYear?: number) {
  const cookie = await requireSessionCookieHeader();
  const query = taxYear ? `?tax_year=${taxYear}` : "";
  return apiFetch<OrgAnalyticsData>(`/api/v1/org/analytics${query}`, { cookie });
}

export { getOrgExportCsvUrl } from "@/lib/api/export-urls";

export async function bulkImportEmployeesWithFastApi(payload: {
  employees: Array<{
    email: string;
    full_name?: string | null;
    employee_code?: string | null;
  }>;
}) {
  const cookie = await requireSessionCookieHeader();
  return apiFetch<OrgEmployeeBulkImportData>(
    "/api/v1/org/employees/bulk-import",
    {
      method: "POST",
      body: payload,
      cookie,
    },
  );
}

export async function exportPayrollCsvWithFastApi(
  taxYear: number,
  template: "generic" | "sql_payroll" | "kakitangan" = "generic",
) {
  const cookie = await requireSessionCookieHeader();
  const params = new URLSearchParams({
    tax_year: String(taxYear),
    template,
  });
  const response = await fetch(
    `${env.FASTAPI_URL}/api/v1/org/export/csv?${params.toString()}`,
    {
      headers: { Cookie: cookie },
      cache: "no-store",
    },
  );

  if (!response.ok) {
    throw new Error("Failed to export payroll CSV.");
  }

  return response.blob();
}

export const registerOrg = registerOrgWithFastApi;
export const getOrgDetails = fetchOrgMe;
export const updateOrgPolicy = updateOrgPolicyWithFastApi;
export const getEmployees = fetchOrgEmployees;
export const bulkApprove = bulkApproveOrgPendingWithFastApi;
export const reviewReceipt = reviewReceiptWithFastApi;
export const getAnalytics = fetchOrgAnalytics;
export const exportPayrollCsv = exportPayrollCsvWithFastApi;
export const validateInvite = validateInviteWithFastApi;
export const acceptInvite = acceptInviteWithFastApi;
export const createHrInvite = inviteHrAdminWithFastApi;
export const createEmployeeInvites = inviteEmployeesWithFastApi;
