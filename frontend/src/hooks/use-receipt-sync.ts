"use client";



import { useEffect, useRef, useState } from "react";



import type { ReceiptDetail, WSEvent } from "@/lib/api/types";

import { useUploadSessionWebSocket } from "@/hooks/use-upload-session-ws";



type SessionWarning = {

  secondsRemaining: number;

};



type SessionCompletion = {

  uploadsCount: number;

  totalAmount: number;

};



type UseReceiptSyncOptions = {

  uploadSessionToken?: string | null;

  enabled?: boolean;

  onReceiptAdded?: () => void;

  onSessionClosed?: (uploadsCount: number, totalAmount: number) => void;

  onSessionExpired?: () => void;

  onError?: (message: string) => void;

};



export function useReceiptSync({

  uploadSessionToken = null,

  enabled = true,

  onReceiptAdded,

  onSessionClosed,

  onSessionExpired,

  onError,

}: UseReceiptSyncOptions = {}) {

  const [latestReceipt, setLatestReceipt] = useState<ReceiptDetail | null>(null);

  const [receivedCount, setReceivedCount] = useState(0);

  const [sessionWarning, setSessionWarning] = useState<SessionWarning | null>(

    null,

  );

  const [sessionCompletion, setSessionCompletion] =

    useState<SessionCompletion | null>(null);

  const [lastEvent, setLastEvent] = useState<WSEvent | null>(null);



  const onReceiptAddedRef = useRef(onReceiptAdded);

  const onSessionClosedRef = useRef(onSessionClosed);

  const onSessionExpiredRef = useRef(onSessionExpired);

  const onErrorRef = useRef(onError);



  useEffect(() => {

    onReceiptAddedRef.current = onReceiptAdded;

    onSessionClosedRef.current = onSessionClosed;

    onSessionExpiredRef.current = onSessionExpired;

    onErrorRef.current = onError;

  });



  const { isConnected, lastEvent: wsLastEvent, subscribe } =

    useUploadSessionWebSocket({

      token: uploadSessionToken,

      enabled,

      onSessionWarned: (secondsRemaining) => {

        setSessionWarning({ secondsRemaining });

      },

      onSessionClosed: (uploadsCount, totalAmount) => {

        setSessionCompletion({ uploadsCount, totalAmount });

        onSessionClosedRef.current?.(uploadsCount, totalAmount);

      },

      onSessionExpired: () => {

        onSessionExpiredRef.current?.();

      },

      onReceiptAdded: () => {

        onReceiptAddedRef.current?.();

      },

      onError: (message) => {

        onErrorRef.current?.(message);

      },

    });



  useEffect(() => {

    if (!wsLastEvent) {

      return;

    }

    setLastEvent(wsLastEvent);

    if (wsLastEvent.type === "receipt_added") {

      setLatestReceipt(wsLastEvent.data.receipt as ReceiptDetail);

      setReceivedCount((count) => count + 1);

    }

  }, [wsLastEvent]);



  return {

    isConnected,

    lastEvent,

    latestReceipt,

    receivedCount,

    sessionWarning,

    sessionCompletion,

    subscribe,

  };

}

