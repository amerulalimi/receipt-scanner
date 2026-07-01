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
  dismissNotificationWithFastApi,
  fetchNotificationPreferences,
  fetchNotifications,
  updateNotificationPreferencesWithFastApi,
} from "@/lib/api/notifications";

describe("notification API", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("getNotifications returns array", async () => {
    mockedApiFetch.mockResolvedValue({
      body: {
        success: true,
        data: { items: [{ id: "n1" }], total: 1 },
      },
    });

    const { body } = await fetchNotifications();
    expect(body.success).toBe(true);
    if (body.success) {
      expect(Array.isArray(body.data.items)).toBe(true);
    }
  });

  it("dismissNotification calls POST endpoint", async () => {
    mockedApiFetch.mockResolvedValue({
      body: { success: true, data: null },
    });

    await dismissNotificationWithFastApi("n1");
    expect(mockedApiFetch).toHaveBeenCalledWith(
      "/api/v1/notifications/n1/dismiss",
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("getPreferences returns defaults", async () => {
    mockedApiFetch.mockResolvedValue({
      body: {
        success: true,
        data: {
          email_enabled: true,
          in_app_enabled: true,
          digest_frequency: "monthly",
        },
      },
    });

    const { body } = await fetchNotificationPreferences();
    if (body.success) {
      expect(body.data.email_enabled).toBe(true);
    }
  });

  it("updatePreferences returns updated fields", async () => {
    mockedApiFetch.mockResolvedValue({
      body: {
        success: true,
        data: {
          email_enabled: false,
          in_app_enabled: true,
          digest_frequency: "off",
        },
      },
    });

    const { body } = await updateNotificationPreferencesWithFastApi({
      email_enabled: false,
      digest_frequency: "off",
    });
    if (body.success) {
      expect(body.data.email_enabled).toBe(false);
      expect(body.data.digest_frequency).toBe("off");
    }
  });
});
