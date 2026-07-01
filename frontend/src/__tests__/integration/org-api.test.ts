jest.mock("@/env", () => ({
  env: {
    FASTAPI_URL: "http://localhost:8000",
    NODE_ENV: "test",
  },
}));

jest.mock("@/lib/api/session", () => ({
  requireSessionCookieHeader: jest.fn().mockResolvedValue("resit_sess=test"),
  forwardSessionCookie: jest.fn(),
}));

const mockedApiFetch = jest.fn();
const mockedFetch = jest.fn();

jest.mock("@/lib/api/client", () => ({
  apiFetch: (...args: unknown[]) => mockedApiFetch(...args),
  forwardSessionCookie: jest.fn(),
}));

global.fetch = mockedFetch as typeof fetch;

import {
  bulkApproveOrgPendingWithFastApi,
  createEmployeeInvites,
  createHrInvite,
  exportPayrollCsv,
  fetchOrgEmployees,
  getAnalytics,
  getEmployees,
  registerOrg,
  registerOrgWithFastApi,
  reviewReceipt,
  reviewReceiptWithFastApi,
} from "@/lib/api/org";

describe("org API", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("registerOrg calls register endpoint", async () => {
    mockedApiFetch.mockResolvedValue({
      response: { status: 201 },
      body: { success: true, data: {} },
    });

    await registerOrg({
      name: "Acme",
      ssm_number: "123456-A",
      email_domain: "example.com",
    });

    expect(mockedApiFetch).toHaveBeenCalledWith(
      "/api/v1/org/register",
      expect.objectContaining({
        method: "POST",
        cookie: "resit_sess=test",
      }),
    );
    expect(registerOrg).toBe(registerOrgWithFastApi);
  });

  it("getEmployees fetches employee list", async () => {
    mockedApiFetch.mockResolvedValue({
      response: { status: 200 },
      body: { success: true, data: { items: [], total: 0, page: 1, limit: 20 } },
    });

    await getEmployees({ page: 2, search: "ali" });

    expect(mockedApiFetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/v1/org/employees?"),
      expect.any(Object),
    );
    expect(getEmployees).toBe(fetchOrgEmployees);
  });

  it("bulkApprove posts bulk approve endpoint", async () => {
    mockedApiFetch.mockResolvedValue({
      response: { status: 200 },
      body: { success: true, data: { approved_count: 1, skipped_count: 0 } },
    });

    await bulkApproveOrgPendingWithFastApi(2025);

    expect(mockedApiFetch).toHaveBeenCalledWith(
      "/api/v1/org/pending-receipts/bulk-approve?tax_year=2025",
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("reviewReceipt posts review endpoint", async () => {
    mockedApiFetch.mockResolvedValue({
      response: { status: 200 },
      body: { success: true, data: {} },
    });

    await reviewReceipt("receipt-1", { action: "approve" });

    expect(mockedApiFetch).toHaveBeenCalledWith(
      "/api/v1/receipts/receipt-1/review",
      expect.objectContaining({
        method: "POST",
        body: { action: "approve" },
      }),
    );
    expect(reviewReceipt).toBe(reviewReceiptWithFastApi);
  });

  it("exportPayrollCsv fetches csv blob", async () => {
    mockedFetch.mockResolvedValue({
      ok: true,
      blob: async () => new Blob(["csv"]),
    });

    const blob = await exportPayrollCsv(2025);
    expect(blob).toBeInstanceOf(Blob);
    expect(mockedFetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/v1/org/export/csv?"),
      expect.objectContaining({
        headers: { Cookie: "resit_sess=test" },
      }),
    );
  });

  it("invite helpers call invite endpoints", async () => {
    mockedApiFetch.mockResolvedValue({
      response: { status: 201 },
      body: { success: true, data: { type: "link" } },
    });

    await createEmployeeInvites({ type: "link" });
    expect(mockedApiFetch).toHaveBeenCalledWith(
      "/api/v1/invites/employees",
      expect.objectContaining({ method: "POST" }),
    );

    await createHrInvite({ email: "hr@example.com" });
    expect(mockedApiFetch).toHaveBeenCalledWith(
      "/api/v1/invites/hr-admin",
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("getAnalytics alias points to fetchOrgAnalytics", async () => {
    mockedApiFetch.mockResolvedValue({
      response: { status: 200 },
      body: { success: true, data: {} },
    });

    await getAnalytics(2025);
    expect(mockedApiFetch).toHaveBeenCalledWith(
      "/api/v1/org/analytics?tax_year=2025",
      expect.any(Object),
    );
  });
});
