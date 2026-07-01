import {
  closeQRSession,
  createQRSession,
  keepAliveQRSession,
  uploadViaQR,
  validateQRSession,
} from "@/lib/api/upload-sessions";

jest.mock("@/env", () => ({
  env: {
    FASTAPI_URL: "http://localhost:8000",
    SESSION_COOKIE_NAME: "resit_sess",
  },
}));

jest.mock("@/lib/api/client", () => ({
  apiFetch: jest.fn(),
  apiPublicUploadFetch: jest.fn(),
}));

jest.mock("@/lib/api/session", () => ({
  requireSessionCookieHeader: jest.fn(async () => "resit_sess=test"),
}));

import { apiFetch, apiPublicUploadFetch } from "@/lib/api/client";

const mockedApiFetch = apiFetch as jest.MockedFunction<typeof apiFetch>;
const mockedPublicUpload = apiPublicUploadFetch as jest.MockedFunction<
  typeof apiPublicUploadFetch
>;

describe("upload session API", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("createQRSession returns token and qr_data", async () => {
    mockedApiFetch.mockResolvedValue({
      response: { status: 201, ok: true } as Response,
      body: {
        success: true,
        data: {
          token: "token-1",
          upload_url: "http://localhost/upload/session/token-1",
          qr_data: "http://localhost/upload/session/token-1",
          inactivity_timeout: 600,
          expires_at: "2026-06-29T00:00:00Z",
        },
      },
    });

    const result = await createQRSession(2025);
    expect(result.body.success).toBe(true);
    if (result.body.success) {
      expect(result.body.data.token).toBe("token-1");
      expect(result.body.data.qr_data).toContain("token-1");
    }
  });

  it("validateQRSession returns valid=true", async () => {
    mockedApiFetch.mockResolvedValue({
      response: { status: 200, ok: true } as Response,
      body: {
        success: true,
        data: {
          valid: true,
          user_name: "Ali",
          uploads_so_far: 0,
          inactivity_remaining: 600,
        },
      },
    });

    const result = await validateQRSession("token-1");
    expect(result.body.success).toBe(true);
    if (result.body.success) {
      expect(result.body.data.valid).toBe(true);
    }
  });

  it("keepAliveQRSession calls correct endpoint", async () => {
    mockedApiFetch.mockResolvedValue({
      response: { status: 200, ok: true } as Response,
      body: {
        success: true,
        data: { inactivity_remaining: 600 },
      },
    });

    await keepAliveQRSession("token-1");
    expect(mockedApiFetch).toHaveBeenCalledWith(
      "/api/v1/upload-sessions/token-1/keep-alive",
      { method: "POST" },
    );
  });

  it("closeQRSession calls correct endpoint", async () => {
    mockedApiFetch.mockResolvedValue({
      response: { status: 200, ok: true } as Response,
      body: {
        success: true,
        data: { uploads_count: 2, message: "Sesi selesai." },
      },
    });

    await closeQRSession("token-1");
    expect(mockedApiFetch).toHaveBeenCalledWith(
      "/api/v1/upload-sessions/token-1/close",
      { method: "POST" },
    );
  });

  it("uploadViaQR sends multipart form data", async () => {
    mockedPublicUpload.mockResolvedValue({
      response: { status: 202, ok: true } as Response,
      body: {
        success: true,
        data: {
          job_id: "job-1",
          session_inactivity_reset: true,
          new_inactivity_remaining: 600,
        },
      },
    });

    const file = new File(["abc"], "receipt.jpg", { type: "image/jpeg" });
    await uploadViaQR("token-1", file);

    expect(mockedPublicUpload).toHaveBeenCalled();
    const [path, formData] = mockedPublicUpload.mock.calls[0];
    expect(path).toBe("/api/v1/upload-sessions/token-1/upload");
    expect(formData).toBeInstanceOf(FormData);
  });
});
