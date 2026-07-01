export type {
  OrgAnalyticsData,
  OrgBulkApproveData,
  OrgEmployeeItem,
  OrgEmployeeListData,
  OrgMeData,
  OrgPendingReceiptItem,
  OrgPendingReceiptListData,
  OrgPolicyData,
  OrgRegisterData,
  InviteAcceptData,
  InviteCreateData,
  InviteValidateData,
} from "@/lib/api/types";

import type { OrgEmployeeItem } from "@/lib/api/types";

export type Organisation = import("@/lib/api/types").OrgMeData;
export type OrgPolicy = import("@/lib/api/types").OrgPolicyData;
export type Employee = OrgEmployeeItem;
export type InviteToken = import("@/lib/api/types").InviteCreateData;
export type PendingReceipt = import("@/lib/api/types").OrgPendingReceiptItem;
export type OrgAnalytics = import("@/lib/api/types").OrgAnalyticsData;

export type EmployeeStatus = "active" | "inactive";

export function computeEmployeeStatus(employee: OrgEmployeeItem): EmployeeStatus {
  return employee.is_active ? "active" : "inactive";
}

export function formatPayrollFilename(orgName: string, taxYear: number): string {
  const sanitized = orgName.replace(/[^a-zA-Z0-9]/g, "");
  return `Syarikat${sanitized}_BE_${taxYear}_payroll.csv`;
}

export async function exportPayrollCsv(
  taxYear: number,
  template: "generic" | "sql_payroll" | "kakitangan" = "generic",
): Promise<Blob> {
  const params = new URLSearchParams({
    tax_year: String(taxYear),
    template,
  });
  const response = await fetch(`/api/org/export/csv?${params.toString()}`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error("Failed to export payroll CSV.");
  }

  return response.blob();
}
