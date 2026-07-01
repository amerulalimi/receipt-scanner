import { AdminOrganizationsSection } from "@/components/admin/admin-organizations-section";
import {
  fetchAdminOrganizationStatsWithFastApi,
  listAdminOrganizationsWithFastApi,
} from "@/lib/api/admin-organizations";
import { parseAdminDirectorySearchParams } from "@/lib/validations/admin-directory";

export const metadata = {
  title: "Organizations — Admin",
};

type AdminOrganizationsPageProps = {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
};

export default async function AdminOrganizationsPage({
  searchParams,
}: AdminOrganizationsPageProps) {
  const rawParams = await searchParams;
  const parsed = parseAdminDirectorySearchParams(rawParams);
  const query = parsed.success
    ? parsed.data
    : {
        page: 1,
        search: "",
        granularity: "month" as const,
        from: undefined,
        to: undefined,
      };

  const statsParams =
    query.granularity === "custom" && query.from && query.to
      ? {
          granularity: "custom" as const,
          from: query.from,
          to: query.to,
        }
      : { granularity: query.granularity };

  const [orgsResult, statsResult] = await Promise.all([
    listAdminOrganizationsWithFastApi({
      page: query.page,
      limit: 50,
      search: query.search || undefined,
    }),
    fetchAdminOrganizationStatsWithFastApi(statsParams),
  ]);

  const organizations =
    orgsResult.body.success && orgsResult.body.data
      ? orgsResult.body.data
      : {
          items: [],
          page: 1,
          limit: 50,
          total: 0,
          total_pages: 1,
        };

  const stats =
    statsResult.body.success && statsResult.body.data
      ? statsResult.body.data
      : {
          series: [],
          growth_percent: 0,
          growth_label: "vs bulan lepas",
          total_in_range: 0,
        };

  return (
    <main className="space-y-6">
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold tracking-tight">Organizations</h1>
        <p className="text-sm text-muted-foreground">
          Corporate organizations and registration trends.
        </p>
      </header>

      <AdminOrganizationsSection organizations={organizations} stats={stats} />
    </main>
  );
}
