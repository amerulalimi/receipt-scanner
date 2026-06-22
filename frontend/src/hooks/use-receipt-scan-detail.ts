"use client";

import { useCallback, useState } from "react";

import { getReceiptDetailAction } from "@/actions/receipt";
import { getReceiptScanStatus } from "@/lib/constants/receipts";
import type { ReceiptDetail, ReceiptListItem } from "@/lib/api/types";

export function useReceiptScanDetail() {
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [detailCache, setDetailCache] = useState<Record<string, ReceiptDetail>>(
    {},
  );
  const [loadingId, setLoadingId] = useState<string | null>(null);
  const [errorById, setErrorById] = useState<Record<string, string>>({});

  const loadDetail = useCallback(async (receiptId: string) => {
    if (detailCache[receiptId]) {
      return;
    }

    setLoadingId(receiptId);
    setErrorById((prev) => {
      const next = { ...prev };
      delete next[receiptId];
      return next;
    });

    const result = await getReceiptDetailAction(receiptId);

    setLoadingId((current) => (current === receiptId ? null : current));

    if (result.error || !result.data) {
      setErrorById((prev) => ({
        ...prev,
        [receiptId]: result.error ?? "Failed to load scan details.",
      }));
      return;
    }

    setDetailCache((prev) => ({
      ...prev,
      [receiptId]: result.data!,
    }));
  }, [detailCache]);

  const toggleExpand = useCallback(
    (item: ReceiptListItem) => {
      const isExpanded = expandedId === item.id;

      if (isExpanded) {
        setExpandedId(null);
        return;
      }

      setExpandedId(item.id);

      const scanStatus = getReceiptScanStatus(item);
      if (scanStatus === "success" || scanStatus === "failed") {
        void loadDetail(item.id);
      }
    },
    [expandedId, loadDetail],
  );

  return {
    expandedId,
    detailCache,
    loadingId,
    errorById,
    toggleExpand,
  };
}
