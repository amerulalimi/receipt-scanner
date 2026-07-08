import { renderHook, waitFor } from "@testing-library/react";

import { useUploadSessionWebSocket } from "@/hooks/use-upload-session-ws";

class MockWebSocket {
  static instances: MockWebSocket[] = [];
  onopen: (() => void) | null = null;
  onmessage: ((event: { data: string }) => void) | null = null;
  onerror: (() => void) | null = null;
  onclose: (() => void) | null = null;
  sent: string[] = [];

  constructor(url: string) {
    void url;
    MockWebSocket.instances.push(this);
    queueMicrotask(() => this.onopen?.());
  }

  send(data: string) {
    this.sent.push(data);
  }

  close() {
    this.onclose?.();
  }

  emitMessage(data: unknown) {
    this.onmessage?.({ data: JSON.stringify(data) });
  }
}

describe("useUploadSessionWebSocket", () => {
  beforeEach(() => {
    MockWebSocket.instances = [];
    global.WebSocket = MockWebSocket as unknown as typeof WebSocket;
  });

  it("connects on mount", async () => {
    const { result } = renderHook(() =>
      useUploadSessionWebSocket({ token: "abc", enabled: true }),
    );

    await waitFor(() => {
      expect(MockWebSocket.instances.length).toBe(1);
    });

    expect(result.current.isConnected).toBe(false);
  });

  it("sends subscribe message with token", async () => {
    renderHook(() => useUploadSessionWebSocket({ token: "abc", enabled: true }));

    await waitFor(() => {
      expect(MockWebSocket.instances[0]?.sent.length).toBeGreaterThan(0);
    });

    const payload = JSON.parse(MockWebSocket.instances[0].sent[0]);
    expect(payload).toEqual({
      type: "subscribe",
      upload_session_token: "abc",
    });
  });

  it("calls handler on message received", async () => {
    const onSessionWarned = jest.fn();
    renderHook(() =>
      useUploadSessionWebSocket({
        token: "abc",
        enabled: true,
        onSessionWarned,
      }),
    );

    await waitFor(() => {
      expect(MockWebSocket.instances[0]).toBeDefined();
    });

    MockWebSocket.instances[0].emitMessage({
      type: "session_warned",
      data: { seconds_remaining: 120 },
    });

    expect(onSessionWarned).toHaveBeenCalledWith(120);
  });

  it("attempts reconnect on disconnect", async () => {
    renderHook(() => useUploadSessionWebSocket({ token: "abc", enabled: true }));

    await waitFor(() => {
      expect(MockWebSocket.instances[0]).toBeDefined();
    });

    MockWebSocket.instances[0].close();

    await waitFor(
      () => {
        expect(MockWebSocket.instances.length).toBeGreaterThan(1);
      },
      { timeout: 5000 },
    );
  });
});
