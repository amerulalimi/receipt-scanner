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

const mockedApiUploadFetch = jest.fn();
const mockedApiFetch = jest.fn();

jest.mock("@/lib/api/client", () => ({
  apiUploadFetch: (...args: unknown[]) => mockedApiUploadFetch(...args),
  apiFetch: (...args: unknown[]) => mockedApiFetch(...args),
}));

import { deleteReceipt, getReceipts, updateReceipt, uploadReceipts } from "@/lib/api/receipts";

describe("receipt API integration", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("uploadReceipts success returns job_ids", async () => {
    mockedApiUploadFetch.mockResolvedValue({
      response: { status: 202, headers: { getSetCookie: () => [] } },
      body: {
        success: true,
        data: { job_ids: ["id-1"], message: "1 resit sedang diproses" },
      },
    });

    const file = new File(["jpeg"], "receipt.jpg", { type: "image/jpeg" });
    const result = await uploadReceipts([file], 2025);

    expect(result.success).toBe(true);
    expect(result.data?.job_ids).toEqual(["id-1"]);
    expect(mockedApiUploadFetch).toHaveBeenCalled();
  });

  it("uploadReceipts with oversized file fails validation client-side", async () => {
    const huge = new File([new ArrayBuffer(10 * 1024 * 1024 + 1)], "big.jpg", {
      type: "image/jpeg",
    });
    const { isValidReceiptFileSize } = await import("@/lib/types/receipt");
    expect(isValidReceiptFileSize(huge.size)).toBe(false);
  });

  it("deleteReceipt success", async () => {
    mockedApiFetch.mockResolvedValue({
      response: { status: 200 },
      body: { success: true, data: null, message: null },
    });
    const result = await deleteReceipt("receipt-1");
    expect(result.body.success).toBe(true);
    expect(mockedApiFetch).toHaveBeenCalledWith(
      "/api/v1/receipts/receipt-1",
      expect.objectContaining({
        method: "DELETE",
        cookie: "resit_sess=test",
      }),
    );
  });

  it("updateReceipt success returns envelope", async () => {
    mockedApiFetch.mockResolvedValue({
      response: { status: 200 },
      body: {
        success: true,
        data: { id: "receipt-1", notes: "Updated" },
        message: null,
      },
    });
    const result = await updateReceipt("receipt-1", { notes: "Updated" });
    expect(result.body.success).toBe(true);
    expect(mockedApiFetch).toHaveBeenCalledWith(
      "/api/v1/receipts/receipt-1",
      expect.objectContaining({
        method: "PATCH",
        cookie: "resit_sess=test",
      }),
    );
  });

  it("getReceipts calls list endpoint with session cookie", async () => {
    mockedApiFetch.mockResolvedValue({
      response: { status: 200 },
      body: {
        success: true,
        data: { items: [], total: 0, page: 1, limit: 20 },
        message: null,
      },
    });
    await getReceipts({ page: 1, limit: 20 });
    expect(mockedApiFetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/v1/receipts?"),
      expect.objectContaining({ cookie: "resit_sess=test" }),
    );
  });
});
