import {
  WSEventType,
  type QRSession,
  type QRValidation,
} from "@/lib/types/qr";

describe("QR types", () => {
  it("WSEventType enum values are correct", () => {
    expect(WSEventType.receiptAdded).toBe("receipt_added");
    expect(WSEventType.receiptScanUpdated).toBe("receipt_scan_updated");
    expect(WSEventType.receiptFailed).toBe("receipt_failed");
    expect(WSEventType.sessionWarned).toBe("session_warned");
    expect(WSEventType.sessionExpired).toBe("session_expired");
    expect(WSEventType.sessionClosed).toBe("session_closed");
  });

  it("QRSession type shape", () => {
    const session: QRSession = {
      token: "abc",
      upload_url: "http://localhost/upload/session/abc",
      qr_data: "http://localhost/upload/session/abc",
      inactivity_timeout: 600,
      expires_at: "2026-06-29T00:00:00Z",
    };

    expect(session.token).toBe("abc");
    expect(session.inactivity_timeout).toBe(600);
  });

  it("QRValidation type shape", () => {
    const validation: QRValidation = {
      valid: true,
      user_name: "Ali",
      uploads_so_far: 2,
      inactivity_remaining: 500,
    };

    expect(validation.valid).toBe(true);
    expect(validation.uploads_so_far).toBe(2);
  });
});
