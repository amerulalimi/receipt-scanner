"use client";

import { useEffect, useRef } from "react";
import { toast } from "sonner";

const FAILED_TOAST_SESSION_KEY = "resit-scan-failed-toast-shown";

type ReceiptScanToastsProps = {
  failedCount: number;
};

export function ReceiptScanToasts({ failedCount }: ReceiptScanToastsProps) {
  const hasShownRef = useRef(false);

  useEffect(() => {
    if (failedCount === 0 || hasShownRef.current) {
      return;
    }

    if (sessionStorage.getItem(FAILED_TOAST_SESSION_KEY) === "1") {
      return;
    }

    hasShownRef.current = true;
    sessionStorage.setItem(FAILED_TOAST_SESSION_KEY, "1");

    toast.error(
      failedCount === 1
        ? "1 receipt failed AI processing. Check status in the list or re-upload."
        : `${failedCount} receipts failed AI processing. Check status in the list or re-upload.`,
      { duration: 8000 },
    );
  }, [failedCount]);

  return null;
}
