"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import type { DashboardWsEvent, WSEvent } from "@/lib/api/types";
import { getDashboardWebSocketUrl } from "@/lib/upload-session-utils";

const MAX_RECONNECT_ATTEMPTS = 3;
const RECONNECT_DELAY_MS = 2000;

type UseUploadSessionWebSocketOptions = {
  token?: string | null;
  enabled?: boolean;
  onSubscribed?: () => void;
  onReceiptAdded?: () => void;
  onReceiptScanUpdated?: (receiptId: string, scanStatus: string) => void;
  onReceiptFailed?: (jobId: string, reason: string) => void;
  onSessionWarned?: (secondsRemaining: number) => void;
  onSessionExpired?: (reason: string) => void;
  onSessionClosed?: (uploadsCount: number, totalAmount: number) => void;
  onError?: (message: string) => void;
};

function toWSEvent(message: DashboardWsEvent): WSEvent | null {
  if (message.type === "subscribed" || message.type === "error") {
    return null;
  }
  return message;
}

export function useUploadSessionWebSocket({
  token = null,
  enabled = true,
  onSubscribed,
  onReceiptAdded,
  onReceiptScanUpdated,
  onReceiptFailed,
  onSessionWarned,
  onSessionExpired,
  onSessionClosed,
  onError,
}: UseUploadSessionWebSocketOptions = {}) {
  const [isConnected, setIsConnected] = useState(false);
  const [lastEvent, setLastEvent] = useState<WSEvent | null>(null);
  const [activeToken, setActiveToken] = useState<string | null>(token);
  const callbacksRef = useRef({
    onSubscribed,
    onReceiptAdded,
    onReceiptScanUpdated,
    onReceiptFailed,
    onSessionWarned,
    onSessionExpired,
    onSessionClosed,
    onError,
  });

  callbacksRef.current = {
    onSubscribed,
    onReceiptAdded,
    onReceiptScanUpdated,
    onReceiptFailed,
    onSessionWarned,
    onSessionExpired,
    onSessionClosed,
    onError,
  };

  const subscribe = useCallback((nextToken: string) => {
    setActiveToken(nextToken);
  }, []);

  useEffect(() => {
    if (token !== null && token !== undefined) {
      setActiveToken(token);
    }
  }, [token]);

  useEffect(() => {
    if (!enabled || !activeToken) {
      setIsConnected(false);
      return;
    }

    let ws: WebSocket | null = null;
    let reconnectAttempts = 0;
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
    let disposed = false;

    const handleMessage = (message: DashboardWsEvent) => {
      const event = toWSEvent(message);
      if (event) {
        setLastEvent(event);
      }

      switch (message.type) {
        case "subscribed":
          reconnectAttempts = 0;
          setIsConnected(true);
          callbacksRef.current.onSubscribed?.();
          break;
        case "receipt_added":
          callbacksRef.current.onReceiptAdded?.();
          break;
        case "receipt_scan_updated":
          callbacksRef.current.onReceiptScanUpdated?.(
            message.data.receipt_id,
            message.data.scan_status,
          );
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

    const connect = () => {
      if (disposed) {
        return;
      }

      ws = new WebSocket(getDashboardWebSocketUrl());

      ws.onopen = () => {
        ws?.send(
          JSON.stringify({
            type: "subscribe",
            upload_session_token: activeToken,
          }),
        );
      };

      ws.onmessage = (event) => {
        try {
          handleMessage(JSON.parse(event.data) as DashboardWsEvent);
        } catch {
          callbacksRef.current.onError?.("Mesej WebSocket tidak sah.");
        }
      };

      ws.onerror = () => {
        callbacksRef.current.onError?.("Sambungan masa nyata gagal.");
      };

      ws.onclose = () => {
        setIsConnected(false);
        if (disposed || reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
          return;
        }
        reconnectAttempts += 1;
        reconnectTimer = setTimeout(connect, RECONNECT_DELAY_MS);
      };
    };

    connect();

    return () => {
      disposed = true;
      if (reconnectTimer) {
        clearTimeout(reconnectTimer);
      }
      ws?.close();
      setIsConnected(false);
    };
  }, [activeToken, enabled]);

  return { isConnected, lastEvent, subscribe };
}
