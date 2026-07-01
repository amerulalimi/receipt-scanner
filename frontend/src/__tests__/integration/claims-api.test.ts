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

jest.mock("@/lib/api/client", () => ({
  apiFetch: (...args: unknown[]) => mockedApiFetch(...args),
}));

import {
  fetchClaimComparison,
  fetchClaimSummary,
  fetchCompletenessScore,
  fetchReadyToFile,
  getClaimSummary,
  getCompletenessScore,
  getReadyToFile,
  getYearComparison,
} from "@/lib/api/claims";

describe("claims API", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("fetchClaimSummary calls summary endpoint", async () => {
    mockedApiFetch.mockResolvedValue({
      response: { status: 200 },
      body: { success: true, data: { tax_year: 2025, categories: [] } },
    });

    await fetchClaimSummary(2025);

    expect(mockedApiFetch).toHaveBeenCalledWith(
      "/api/v1/claims/summary?tax_year=2025",
      expect.objectContaining({ cookie: "resit_sess=test" }),
    );
  });

  it("aliases point to the same fetch functions", () => {
    expect(getClaimSummary).toBe(fetchClaimSummary);
    expect(getYearComparison).toBe(fetchClaimComparison);
    expect(getReadyToFile).toBe(fetchReadyToFile);
    expect(getCompletenessScore).toBe(fetchCompletenessScore);
  });

  it("fetchClaimComparison calls compare endpoint", async () => {
    mockedApiFetch.mockResolvedValue({
      response: { status: 200 },
      body: { success: true, data: {} },
    });

    await fetchClaimComparison(2025);
    expect(mockedApiFetch).toHaveBeenCalledWith(
      "/api/v1/claims/compare?tax_year=2025",
      expect.any(Object),
    );
  });

  it("fetchReadyToFile calls ready-to-file endpoint", async () => {
    mockedApiFetch.mockResolvedValue({
      response: { status: 200 },
      body: { success: true, data: {} },
    });

    await fetchReadyToFile(2025);
    expect(mockedApiFetch).toHaveBeenCalledWith(
      "/api/v1/claims/ready-to-file?tax_year=2025",
      expect.any(Object),
    );
  });

  it("fetchCompletenessScore calls completeness endpoint", async () => {
    mockedApiFetch.mockResolvedValue({
      response: { status: 200 },
      body: { success: true, data: { score: 40 } },
    });

    await fetchCompletenessScore(2025);
    expect(mockedApiFetch).toHaveBeenCalledWith(
      "/api/v1/claims/completeness?tax_year=2025",
      expect.any(Object),
    );
  });
});

describe("exportZip", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("exportZip returns blob from proxy route", async () => {
    const blob = new Blob(["zip"], { type: "application/zip" });
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      blob: async () => blob,
    }) as jest.Mock;

    const { exportZip } = await import("@/lib/types/claims");
    const result = await exportZip(2025);

    expect(global.fetch).toHaveBeenCalledWith(
      "/api/claims/export-zip?tax_year=2025",
      { cache: "no-store" },
    );
    expect(result).toBe(blob);
  });
});
