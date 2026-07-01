import {
  DASHBOARD_RECEIPT_HISTORY_LIMITS,
  dashboardReceiptHistorySchema,
  parseDashboardReceiptHistorySearchParams,
} from "@/lib/validations/receipt";

describe("dashboard receipt history params", () => {
  it("defaults history_limit to 5", () => {
    const parsed = parseDashboardReceiptHistorySearchParams({});
    expect(parsed.success).toBe(true);
    if (parsed.success) {
      expect(parsed.data.history_limit).toBe(5);
    }
  });

  it("accepts configured history limits including 5", () => {
    for (const limit of DASHBOARD_RECEIPT_HISTORY_LIMITS) {
      const result = dashboardReceiptHistorySchema.safeParse({ history_limit: limit });
      expect(result.success).toBe(true);
    }
  });

  it("parses tax_year from search params", () => {
    const parsed = parseDashboardReceiptHistorySearchParams({ tax_year: "2024" });
    expect(parsed.success).toBe(true);
    if (parsed.success) {
      expect(parsed.data.tax_year).toBe(2024);
    }
  });
});

jest.mock("@/env", () => ({
  env: {
    FASTAPI_URL: "http://localhost:8000",
    NODE_ENV: "test",
  },
}));

jest.mock("@/lib/api/session", () => ({
  requireSessionCookieHeader: jest.fn().mockResolvedValue("resit_sess=test"),
}));

const mockedCreateSession = jest.fn();
jest.mock("@/lib/api/upload-sessions", () => ({
  createUploadSessionWithFastApi: (...args: unknown[]) =>
    mockedCreateSession(...args),
}));

import { createUploadSessionAction } from "@/actions/upload-session";

describe("dashboard upload actions", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("createUploadSessionAction posts to upload session endpoint", async () => {
    mockedCreateSession.mockResolvedValue({
      response: { status: 201 },
      body: {
        success: true,
        data: {
          token: "abc",
          qr_data: "qr",
          upload_url: "http://localhost/upload/abc",
          inactivity_timeout: 300,
        },
      },
    });

    const result = await createUploadSessionAction(2025);
    expect(result.data?.token).toBe("abc");
    expect(mockedCreateSession).toHaveBeenCalledWith(2025);
  });
});
