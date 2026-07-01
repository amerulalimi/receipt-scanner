import { DashboardError } from "@/components/dashboard/dashboard-error";
import { DashboardYearFilter } from "@/components/dashboard/dashboard-year-filter";
import { OrgPendingApprovalsSection } from "@/components/org/org-pending-approvals-section";
import { fetchOrgPendingReceipts } from "@/lib/api/org";
import {
  loadOrgPageContext,
  requireOrgAdmin,
} from "@/lib/org/page-context";

export const metadata = {
  title: "HR Approvals",
};

type PendingPageProps = {
  searchParams: Promise<{ tax_year?: string; page?: string }>;
};

export default async function OrgPendingPage({ searchParams }: PendingPageProps) {
  const context = requireOrgAdmin(await loadOrgPageContext("/dashboard/org/pending"));
  const params = await searchParams;
  const taxYear = params.tax_year
    ? Number.parseInt(params.tax_year, 10)
    : context.org.policy.tax_year;
  const page = params.page ? Number.parseInt(params.page, 10) : 1;

  let pendingResult;

  try {
    pendingResult = await fetchOrgPendingReceipts({
      tax_year: taxYear,
      page,
      limit: 20,
    });
  } catch {
    return <DashboardError message="Unable to load pending receipts." />;
  }

  if (!pendingResult.body.success) {
    return (
      <DashboardError message="Failed to load pending receipts." />
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold">HR approvals</h2>
          <p className="text-sm text-muted-foreground">
            Review employee receipt submissions.
          </p>
        </div>
        <DashboardYearFilter
          defaultYear={context.org.policy.tax_year}
          label="Tax year"
        />
      </div>
      <OrgPendingApprovalsSection
        pending={pendingResult.body.data}
        categoryLabels={context.categoryLabels}
        taxYear={taxYear}
      />
    </div>
  );
}
