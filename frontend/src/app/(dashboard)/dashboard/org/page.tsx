import { DashboardError } from "@/components/dashboard/dashboard-error";
import { OrgAnalyticsSection } from "@/components/org/org-analytics-section";
import { OrgBulkImportSection } from "@/components/org/org-bulk-import-section";
import { OrgEmployeesSection } from "@/components/org/org-employees-section";
import { OrgExportSection } from "@/components/org/org-export-section";
import { OrgInviteSection } from "@/components/org/org-invite-section";
import { OrgOverviewSection } from "@/components/org/org-overview-section";
import { OrgPendingApprovalsSection } from "@/components/org/org-pending-approvals-section";
import { OrgPolicyForm } from "@/components/org/org-policy-form";
import { OrgRegisterForm } from "@/components/org/org-register-form";
import { fetchOrgEmployees, fetchOrgMe, fetchOrgPendingReceipts, fetchOrgAnalytics } from "@/lib/api/org";
import { fetchReliefCategories } from "@/lib/api/admin-system";
import { requireAuth } from "@/lib/auth/require-auth";
import { buildCategoryLabelMap, mergeCategoryLabels } from "@/lib/receipt-categories";
import { canAccessOrgFeatures } from "@/lib/auth/account-access";
import { redirectAfterSessionExpired } from "@/lib/auth/session-expired-redirect";
import type { ApiErrorResponse } from "@/lib/api/types";
import { redirect } from "next/navigation";

export const metadata = {
  title: "Organization",
};

function isUnauthorized(
  status: number,
  body: unknown,
): body is ApiErrorResponse {
  return (
    status === 401 ||
    (typeof body === "object" &&
      body !== null &&
      "success" in body &&
      (body as ApiErrorResponse).success === false &&
      (body as ApiErrorResponse).code === "UNAUTHORIZED")
  );
}

export default async function OrgPage() {
  const user = await requireAuth("/dashboard/org");

  if (!canAccessOrgFeatures(user)) {
    redirect("/dashboard");
  }

  let orgResult;
  let categoriesResult;

  try {
    [orgResult, categoriesResult] = await Promise.all([
      fetchOrgMe(),
      fetchReliefCategories(),
    ]);
  } catch {
    return (
      <DashboardError message="Unable to reach the API server. Make sure FastAPI is running." />
    );
  }

  const { response, body } = orgResult;

  if (isUnauthorized(response.status, body)) {
    redirectAfterSessionExpired("/dashboard/org");
  }

  const canRegisterOrg =
    user.account_type === "corporate" &&
    user.org_id === null &&
    user.role === "individual";

  if (!body.success && response.status === 404 && canRegisterOrg) {
    return (
      <main className="w-full space-y-4 py-8">
        <header className="space-y-1">
          <h1 className="text-2xl font-semibold tracking-tight">Organization</h1>
          <p className="text-sm text-muted-foreground">
            Register your company to start managing employees.
          </p>
        </header>
        <OrgRegisterForm userEmail={user.email} />
      </main>
    );
  }

  if (!body.success) {
    const errorBody = body as ApiErrorResponse;
    return (
      <DashboardError
        message={errorBody.message ?? "Organization not found."}
      />
    );
  }

  const org = body.data;
  const isOrgAdmin = user.role === "hr_admin" || user.role === "superadmin";
  const isOrgSuperadmin = user.role === "superadmin";
  const reliefCategories = categoriesResult.body.success
    ? categoriesResult.body.data
    : [];
  const categoryLabels = mergeCategoryLabels(
    buildCategoryLabelMap(reliefCategories),
  );

  let employeesResult = null;
  let pendingResult = null;
  let analyticsResult = null;

  if (isOrgAdmin) {
    try {
      [employeesResult, pendingResult, analyticsResult] = await Promise.all([
        fetchOrgEmployees({ page: 1, limit: 50 }),
        fetchOrgPendingReceipts({
          page: 1,
          limit: 20,
          tax_year: org.policy.tax_year,
        }),
        fetchOrgAnalytics(org.policy.tax_year),
      ]);
    } catch {
      return (
        <DashboardError message="Unable to load employee list." />
      );
    }

    if (
      isUnauthorized(employeesResult.response.status, employeesResult.body)
    ) {
      redirectAfterSessionExpired("/dashboard/org");
    }
  }

  return (
    <main className="w-full space-y-6 py-8">
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold tracking-tight">Organization</h1>
        <p className="text-sm text-muted-foreground">
          Manage company settings and employees.
        </p>
      </header>

      <OrgOverviewSection org={org} categoryLabels={categoryLabels} />

      {isOrgSuperadmin ? (
        <OrgPolicyForm
          policy={org.policy}
          availableCategories={reliefCategories}
          categoryLabels={categoryLabels}
        />
      ) : null}

      {isOrgAdmin ? (
        <>
          {analyticsResult?.body.success ? (
            <OrgAnalyticsSection
              analytics={analyticsResult.body.data}
              categoryLabels={categoryLabels}
            />
          ) : null}
          <OrgExportSection defaultTaxYear={org.policy.tax_year} />
          <OrgBulkImportSection emailDomain={org.email_domain} />
          {pendingResult?.body.success ? (
            <OrgPendingApprovalsSection
              pending={pendingResult.body.data}
              categoryLabels={categoryLabels}
              taxYear={org.policy.tax_year}
            />
          ) : null}
          <OrgInviteSection
            emailDomain={org.email_domain}
            isSuperadmin={isOrgSuperadmin}
          />
          {employeesResult?.body.success ? (
            <OrgEmployeesSection
              employees={employeesResult.body.data}
              currentUserId={user.user_id}
            />
          ) : employeesResult ? (
            <DashboardError message="Failed to load employee list." />
          ) : null}
        </>
      ) : null}
    </main>
  );
}
