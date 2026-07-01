import { AdminUsersSection } from "@/components/admin/admin-users-section";
import {
  fetchAdminUserStatsWithFastApi,
  listAdminUsersWithFastApi,
} from "@/lib/api/admin-users";
import { parseAdminDirectorySearchParams } from "@/lib/validations/admin-directory";

export const metadata = {
  title: "Users — Admin",
};

type AdminUsersPageProps = {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
};

export default async function AdminUsersPage({ searchParams }: AdminUsersPageProps) {
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

  const [usersResult, statsResult] = await Promise.all([
    listAdminUsersWithFastApi({
      page: query.page,
      limit: 50,
      search: query.search || undefined,
    }),
    fetchAdminUserStatsWithFastApi(statsParams),
  ]);

  const users =
    usersResult.body.success && usersResult.body.data
      ? usersResult.body.data
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
        <h1 className="text-2xl font-semibold tracking-tight">Users</h1>
        <p className="text-sm text-muted-foreground">
          Platform user directory and registration trends.
        </p>
      </header>

      <AdminUsersSection users={users} stats={stats} />
    </main>
  );
}
