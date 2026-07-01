jest.mock("@/env", () => ({
  env: {
    FASTAPI_URL: "http://localhost:8000",
    NODE_ENV: "test",
  },
}));

jest.mock("@/lib/api/session", () => ({
  requireSessionCookieHeader: jest.fn().mockResolvedValue("resit_sess=test"),
}));

const mockedApiFetch = jest.fn();

jest.mock("@/lib/api/client", () => ({
  apiFetch: (...args: unknown[]) => mockedApiFetch(...args),
}));

import {
  dissolveLink,
  getClaimSuggestion,
  getHouseholdOverview,
  requestSpouseLink,
  respondToLink,
} from "@/lib/api/household";

describe("household API", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("getHouseholdOverview returns linked=false for new user", async () => {
    mockedApiFetch.mockResolvedValue({
      body: {
        success: true,
        data: {
          accepted_link_id: null,
          partner: null,
          combined: null,
          incoming_requests: [],
          outgoing_request: null,
        },
      },
    });

    const overview = await getHouseholdOverview(2025);
    expect(overview.partner).toBeNull();
    expect(mockedApiFetch).toHaveBeenCalledWith(
      "/api/v1/household?tax_year=2025",
      expect.any(Object),
    );
  });

  it("requestSpouseLink returns SpouseLink with status=pending", async () => {
    mockedApiFetch.mockResolvedValue({
      body: {
        success: true,
        data: { link_id: "link-1", status: "pending" },
      },
    });

    const link = await requestSpouseLink("spouse@example.com");
    expect(link.status).toBe("pending");
  });

  it("respondToLink accept returns status=accepted", async () => {
    mockedApiFetch.mockResolvedValue({
      body: {
        success: true,
        data: { link_id: "link-1", status: "accepted" },
      },
    });

    const link = await respondToLink("link-1", "accept");
    expect(link.status).toBe("accepted");
  });

  it("dissolveLink calls correct endpoint", async () => {
    mockedApiFetch.mockResolvedValue({
      body: { success: true, data: null },
    });

    await dissolveLink("link-1");
    expect(mockedApiFetch).toHaveBeenCalledWith(
      "/api/v1/household/spouse-link/link-1",
      expect.objectContaining({ method: "DELETE" }),
    );
  });

  it("getClaimSuggestion returns suggestion and reason", async () => {
    mockedApiFetch.mockResolvedValue({
      body: {
        success: true,
        data: {
          receipt_id: "r1",
          category: "perubatan",
          suggested_user_id: "u1",
          suggestion: "self",
          reason_my: "Tiada pasangan dipaut.",
          reason_en: "No linked spouse.",
          reason: "Tiada pasangan dipaut.",
          user_remaining: 0,
          spouse_remaining: 0,
        },
      },
    });

    const suggestion = await getClaimSuggestion("r1");
    expect(suggestion.suggestion).toBe("self");
    expect(suggestion.reason).toBe("Tiada pasangan dipaut.");
  });
});
