import { DashboardError } from "@/components/dashboard/dashboard-error";
import { DashboardYearFilter } from "@/components/dashboard/dashboard-year-filter";
import { OrgAnalyticsSection } from "@/components/org/org-analytics-section";
import { OrgExportSection } from "@/components/org/org-export-section";
import { fetchOrgAnalytics } from "@/lib/api/org";
import {
  loadOrgPageContext,
  requireOrgAdmin,
} from "@/lib/org/page-context";

export const metadata = {
  title: "Org Analytics",
};

type AnalyticsPageProps = {
  searchParams: Promise<{ tax_year?: string }>;
};

export default async function OrgAnalyticsPage({
  searchParams,
}: AnalyticsPageProps) {
  const context = requireOrgAdmin(
    await loadOrgPageContext("/dashboard/org/analytics"),
  );
  const params = await searchParams;
  const taxYear = params.tax_year
    ? Number.parseInt(params.tax_year, 10)
    : context.org.policy.tax_year;

  let analyticsResult;

  try {
    analyticsResult = await fetchOrgAnalytics(taxYear);
  } catch {
    return <DashboardError message="Unable to load analytics." />;
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold">Analytics</h2>
          <p className="text-sm text-muted-foreground">
            Organization-wide claim trends and forecasts.
          </p>
        </div>
        <DashboardYearFilter
          defaultYear={context.org.policy.tax_year}
          label="Tax year"
        />
      </div>

      {analyticsResult.body.success ? (
        <OrgAnalyticsSection
          analytics={analyticsResult.body.data}
          categoryLabels={context.categoryLabels}
        />
      ) : (
        <DashboardError message="Failed to load analytics." />
      )}

      <OrgExportSection defaultTaxYear={taxYear} />
    </div>
  );
}
