import type {
  AuditLogItem,
  ReliefLimitItem,
  SystemOverviewData,
} from "@/lib/api/types";

describe("admin types", () => {
  it("system overview has required health fields", () => {
    const overview: SystemOverviewData = {
      auth_rate_limit_max: 5,
      auth_rate_limit_window_seconds: 60,
      audit_retention_days: 90,
      receipt_retention_days: 30,
      receipt_queue_depth: 0,
      total_audit_logs: 10,
      total_users: 100,
      total_receipts: 500,
      total_orgs: 3,
      receipts_today: 12,
      storage_backend: "local",
      worker_status: "running",
      redis_connected: true,
      db_connected: true,
    };

    expect(overview.redis_connected).toBe(true);
    expect(overview.db_connected).toBe(true);
    expect(overview.worker_status).toBe("running");
  });

  it("relief limit has limit_amount as number", () => {
    const limit: ReliefLimitItem = {
      id: "limit-1",
      category: "perubatan",
      be_seksyen: "S.46(1)(b)",
      limit_amount: 8000,
      description_my: "Perubatan",
      sort_order: 1,
      is_active: true,
      updated_at: "2025-01-01T00:00:00Z",
    };

    expect(typeof limit.limit_amount).toBe("number");
  });

  it("audit log has action and created_at fields", () => {
    const log: AuditLogItem = {
      id: 1,
      user_id: "user-1",
      org_id: null,
      action: "system.retention_purge",
      resource: "system",
      resource_id: null,
      metadata: null,
      ip_address: "127.0.0.1",
      created_at: "2025-06-01T12:00:00Z",
    };

    expect(log.action).toBe("system.retention_purge");
    expect(log.created_at).toBeTruthy();
  });
});
