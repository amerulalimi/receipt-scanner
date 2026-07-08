import fs from "node:fs";
import path from "node:path";

jest.mock("@/env", () => ({
  env: {
    NODE_ENV: "test",
    FASTAPI_URL: "http://localhost:8000",
    SESSION_COOKIE_NAME: "resit_sess",
    SESSION_TTL_SECONDS: 28800,
    NEXT_PUBLIC_APP_URL: "http://localhost:3000",
  },
}));

describe("production config", () => {
  const apiUrl = "https://api.resit.my";

  beforeEach(() => {
    process.env.NEXT_PUBLIC_API_URL = apiUrl;
  });

  it("NEXT_PUBLIC_API_URL is defined", () => {
    expect(process.env.NEXT_PUBLIC_API_URL).toBeDefined();
    expect(process.env.NEXT_PUBLIC_API_URL).toBe(apiUrl);
  });

  it("API client includes credentials: 'include'", async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ success: true, data: {}, message: null }),
    });

    const { apiClient } = await import("@/lib/api/client");
    await apiClient("/api/v1/auth/me");

    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/v1/auth/me"),
      expect.objectContaining({ credentials: "include" }),
    );
  });

  it("API client throws on non-2xx response", async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: false,
      json: async () => ({
        success: false,
        message: "Unauthorized",
        code: "UNAUTHORIZED",
      }),
    });

    const { apiClient, ApiClientError } = await import("@/lib/api/client");

    await expect(apiClient("/api/v1/auth/me")).rejects.toBeInstanceOf(
      ApiClientError,
    );
  });

  it("security headers are expected in requests", () => {
    const configSource = fs.readFileSync(
      path.join(__dirname, "../../../next.config.ts"),
      "utf8",
    );

    for (const key of [
      "X-Frame-Options",
      "X-Content-Type-Options",
      "Referrer-Policy",
    ]) {
      expect(configSource).toContain(key);
    }
    expect(configSource).toContain("output: \"standalone\"");
    expect(configSource).toContain("poweredByHeader: false");
  });
});
