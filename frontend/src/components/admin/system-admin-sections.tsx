"use client";

import { startTransition, useActionState } from "react";

import { purgeRetentionAction } from "@/actions/admin-system";
import type { AdminActionState } from "@/actions/admin-config";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { AuditLogItem, SystemOverviewData } from "@/lib/api/types";

const initialState: AdminActionState = {};

function formatDateTime(value: string): string {
  return new Intl.DateTimeFormat("en-MY", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export function AuditLogsSection({ logs }: { logs: AuditLogItem[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Audit Log</CardTitle>
        <CardDescription>
          Important system activity (login, settings updates, org, etc.).
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {logs.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No audit logs found.
          </p>
        ) : null}

        {logs.map((log) => (
          <div key={log.id} className="rounded-lg border px-3 py-3 space-y-1">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <p className="font-medium">{log.action}</p>
              <p className="text-xs text-muted-foreground">
                {formatDateTime(log.created_at)}
              </p>
            </div>
            <p className="text-sm text-muted-foreground">
              {log.resource ?? "—"}
              {log.ip_address ? ` · IP ${log.ip_address}` : ""}
            </p>
            {log.metadata ? (
              <pre className="overflow-x-auto rounded bg-muted px-2 py-1 text-xs">
                {JSON.stringify(log.metadata, null, 2)}
              </pre>
            ) : null}
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

export function SystemOverviewCards({
  overview,
}: {
  overview: SystemOverviewData;
}) {
  const [state, submitAction, isPending] = useActionState(
    purgeRetentionAction,
    initialState,
  );

  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Receipt Queue</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-2xl font-semibold">{overview.receipt_queue_depth}</p>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Audit Log</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-2xl font-semibold">{overview.total_audit_logs}</p>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Auth Rate Limit</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            {overview.auth_rate_limit_max} /{" "}
            {Math.round(overview.auth_rate_limit_window_seconds / 60)} min
          </p>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Retention</CardTitle>
          <CardDescription>
            Audit {overview.audit_retention_days}d · Receipts{" "}
            {overview.receipt_retention_days}d
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-2">
          <Button
            type="button"
            variant="outline"
            size="sm"
            disabled={isPending}
            onClick={() => startTransition(() => submitAction())}
          >
            {isPending ? "Cleaning up…" : "Run purge"}
          </Button>
          {state.error ? (
            <p className="text-sm text-destructive">{state.error}</p>
          ) : null}
          {state.success && state.message ? (
            <p className="text-sm text-emerald-600">{state.message}</p>
          ) : null}
        </CardContent>
      </Card>
    </div>
  );
}
