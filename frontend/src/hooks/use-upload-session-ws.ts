"use client";

import { useEffect, useRef } from "react";

import type { DashboardWsEvent } from "@/lib/api/types";
import { getDashboardWebSocketUrl } from "@/lib/upload-session-utils";

type UseUploadSessionWebSocketOptions = {
  token: string | null;
  enabled: boolean;
  onSubscribed?: () => void;
  onReceiptAdded?: () => void;
  onReceiptFailed?: (jobId: string, reason: string) => void;
  onSessionWarned?: (secondsRemaining: number) => void;
  onSessionExpired?: (reason: string) => void;
  onSessionClosed?: (uploadsCount: number, totalAmount: number) => void;
  onError?: (message: string) => void;
};

export function useUploadSessionWebSocket({
  token,
  enabled,
  onSubscribed,
  onReceiptAdded,
  onReceiptFailed,
  onSessionWarned,
  onSessionExpired,
  onSessionClosed,
  onError,
}: UseUploadSessionWebSocketOptions) {
  const callbacksRef = useRef({
    onSubscribed,
    onReceiptAdded,
    onReceiptFailed,
    onSessionWarned,
    onSessionExpired,
    onSessionClosed,
    onError,
  });

  callbacksRef.current = {
    onSubscribed,
    onReceiptAdded,
    onReceiptFailed,
    onSessionWarned,
    onSessionExpired,
    onSessionClosed,
    onError,
  };

  useEffect(() => {
    if (!enabled || !token) {
      return;
    }

    const ws = new WebSocket(getDashboardWebSocketUrl());
    let subscribed = false;

    ws.onopen = () => {
      ws.send(
        JSON.stringify({
          type: "subscribe",
          upload_session_token: token,
        }),
      );
    };

    ws.onmessage = (event) => {
      let message: DashboardWsEvent;
      try {
        message = JSON.parse(event.data) as DashboardWsEvent;
      } catch {
        callbacksRef.current.onError?.("Invalid WebSocket message.");
        return;
      }

      switch (message.type) {
        case "subscribed":
          subscribed = true;
          callbacksRef.current.onSubscribed?.();
          break;
        case "receipt_added":
          callbacksRef.current.onReceiptAdded?.();
          break;
        case "receipt_failed":
          callbacksRef.current.onReceiptFailed?.(
            message.data.job_id,
            message.data.reason,
          );
          break;
        case "session_warned":
          callbacksRef.current.onSessionWarned?.(message.data.seconds_remaining);
          break;
        case "session_expired":
          callbacksRef.current.onSessionExpired?.(message.data.reason);
          break;
        case "session_closed":
          callbacksRef.current.onSessionClosed?.(
            message.data.uploads_count,
            message.data.total_amount,
          );
          break;
        case "error":
          callbacksRef.current.onError?.(message.data.message);
          break;
        default:
          break;
      }
    };

    ws.onerror = () => {
      if (!subscribed) {
        callbacksRef.current.onError?.("Real-time connection failed.");
      }
    };

    return () => {
      ws.close();
    };
  }, [enabled, token]);
}
