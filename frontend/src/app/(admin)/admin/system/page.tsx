import {
  AuditLogsSection,
  SystemOverviewCards,
} from "@/components/admin/system-admin-sections";
import { ReliefLimitsSection } from "@/components/admin/relief-limits-section";
import { SystemSettingsForm } from "@/components/admin/system-settings-form";
import {
  fetchAuditLogs,
  fetchReliefLimits,
  fetchSystemOverview,
} from "@/lib/api/admin-system";

export const metadata = {
  title: "System Admin",
};

export default async function AdminSystemPage() {
  const [overviewResult, limitsResult, auditResult] = await Promise.all([
    fetchSystemOverview(),
    fetchReliefLimits(),
    fetchAuditLogs({ page: 1, limit: 30 }),
  ]);

  const overview = overviewResult.body.success
    ? overviewResult.body.data
    : null;
  const limits = limitsResult.body.success ? limitsResult.body.data : [];
  const auditLogs = auditResult.body.success ? auditResult.body.data.items : [];

  if (!overview) {
    return (
      <main className="space-y-4">
        <p className="text-sm text-destructive">
          Failed to load system overview.
        </p>
      </main>
    );
  }

  return (
    <main className="space-y-6">
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold tracking-tight">System</h1>
        <p className="text-sm text-muted-foreground">
          Audit log, relief limits, rate limits, and data retention.
        </p>
      </header>

      <SystemOverviewCards overview={overview} />

      <div className="grid gap-6 xl:grid-cols-2">
        <SystemSettingsForm overview={overview} />
        <ReliefLimitsSection limits={limits} />
      </div>

      <AuditLogsSection logs={auditLogs} />
    </main>
  );
}
