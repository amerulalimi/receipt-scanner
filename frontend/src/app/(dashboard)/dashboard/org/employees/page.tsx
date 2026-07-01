import { DashboardError } from "@/components/dashboard/dashboard-error";
import { OrgBulkImportSection } from "@/components/org/org-bulk-import-section";
import { OrgEmployeesSection } from "@/components/org/org-employees-section";
import { OrgEmployeesToolbar } from "@/components/org/org-employees-toolbar";
import { OrgInviteSection } from "@/components/org/org-invite-section";
import { fetchOrgEmployees } from "@/lib/api/org";
import {
  loadOrgPageContext,
  requireOrgAdmin,
} from "@/lib/org/page-context";

export const metadata = {
  title: "Employees",
};

type EmployeesPageProps = {
  searchParams: Promise<{
    search?: string;
    status?: string;
    page?: string;
  }>;
};

export default async function OrgEmployeesPage({
  searchParams,
}: EmployeesPageProps) {
  const context = requireOrgAdmin(
    await loadOrgPageContext("/dashboard/org/employees"),
  );
  const params = await searchParams;
  const page = params.page ? Number.parseInt(params.page, 10) : 1;

  let employeesResult;

  try {
    employeesResult = await fetchOrgEmployees({
      search: params.search,
      status: params.status,
      page,
      limit: 20,
    });
  } catch {
    return <DashboardError message="Unable to load employees." />;
  }

  if (!employeesResult.body.success) {
    return <DashboardError message="Failed to load employees." />;
  }

  return (
    <div className="space-y-6">
      <div className="space-y-1">
        <h2 className="text-lg font-semibold">Employees</h2>
        <p className="text-sm text-muted-foreground">
          Manage team members and invitations.
        </p>
      </div>

      <OrgEmployeesToolbar />

      <OrgEmployeesSection
        employees={employeesResult.body.data}
        currentUserId={context.user.user_id}
      />
      <OrgInviteSection
        emailDomain={context.org.email_domain}
        isSuperadmin={context.isOrgSuperadmin}
      />
      <OrgBulkImportSection emailDomain={context.org.email_domain} />
    </div>
  );
}
