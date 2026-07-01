jest.mock("@/env", () => ({
  env: {
    NODE_ENV: "test",
    FASTAPI_URL: "http://localhost:8000",
    SESSION_COOKIE_NAME: "resit_sess",
    SESSION_TTL_SECONDS: 28800,
    NEXT_PUBLIC_APP_URL: "http://localhost:3000",
  },
}));

jest.mock("@/lib/api/client", () => ({
  apiFetch: jest.fn(),
  forwardSessionCookie: jest.fn(),
}));

import {
  loginWithFastApi,
  logoutWithFastApi,
  registerWithFastApi,
} from "@/lib/api/auth";
import { apiFetch, forwardSessionCookie } from "@/lib/api/client";

const mockedApiFetch = apiFetch as jest.MockedFunction<typeof apiFetch>;
const mockedForwardCookie = forwardSessionCookie as jest.MockedFunction<
  typeof forwardSessionCookie
>;

describe("auth API integration", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("loginWithFastApi success forwards session cookie", async () => {
    mockedApiFetch.mockResolvedValue({
      response: {
        status: 200,
        headers: { getSetCookie: () => [] },
      } as unknown as Response,
      body: {
        success: true,
        data: {
          user_id: "1",
          email: "user@example.com",
          full_name: "User",
          role: "individual",
          org_id: null,
          tax_year: 2025,
          tax_bracket: null,
          email_verified: false,
        },
        message: null,
      },
    });

    const result = await loginWithFastApi({
      email: "user@example.com",
      password: "password123",
    });

    expect(result.body.success).toBe(true);
    expect(mockedForwardCookie).toHaveBeenCalled();
  });

  it("loginWithFastApi failure does not forward cookie", async () => {
    mockedApiFetch.mockResolvedValue({
      response: {
        status: 401,
        headers: { getSetCookie: () => [] },
      } as unknown as Response,
      body: {
        success: false,
        data: null,
        message: "Invalid credentials",
        code: "INVALID_CREDENTIALS",
      },
    });

    await loginWithFastApi({
      email: "user@example.com",
      password: "wrong",
    });

    expect(mockedForwardCookie).not.toHaveBeenCalled();
  });

  it("registerWithFastApi success forwards session cookie", async () => {
    mockedApiFetch.mockResolvedValue({
      response: {
        status: 201,
        headers: { getSetCookie: () => [] },
      } as unknown as Response,
      body: {
        success: true,
        data: {
          user_id: "1",
          email: "new@example.com",
          full_name: "New",
          role: "individual",
          org_id: null,
          tax_year: 2025,
          tax_bracket: null,
          email_verified: false,
        },
        message: null,
      },
    });

    await registerWithFastApi({
      email: "new@example.com",
      password: "password123",
      full_name: "New",
      account_type: "individual",
    });

    expect(mockedForwardCookie).toHaveBeenCalled();
  });

  it("registerWithFastApi duplicate email returns error envelope", async () => {
    mockedApiFetch.mockResolvedValue({
      response: {
        status: 400,
        headers: { getSetCookie: () => [] },
      } as unknown as Response,
      body: {
        success: false,
        data: null,
        message: "Email exists",
        code: "EMAIL_EXISTS",
      },
    });

    const result = await registerWithFastApi({
      email: "exists@example.com",
      password: "password123",
      full_name: "User",
      account_type: "individual",
    });

    expect(result.body.code).toBe("EMAIL_EXISTS");
  });

  it("logoutWithFastApi calls logout endpoint", async () => {
    mockedApiFetch.mockResolvedValue({
      response: {
        status: 200,
        headers: { getSetCookie: () => [] },
      } as unknown as Response,
      body: { success: true, data: null, message: null },
    });

    await logoutWithFastApi("resit_sess=abc");

    expect(mockedApiFetch).toHaveBeenCalledWith("/api/v1/auth/logout", {
      method: "POST",
      cookie: "resit_sess=abc",
    });
  });
});
