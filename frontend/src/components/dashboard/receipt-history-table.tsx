"use client";

import { ChevronDownIcon, ChevronRightIcon } from "lucide-react";
import { Fragment, useCallback, useState } from "react";

import { getReceiptDetailAction } from "@/actions/receipt";
import { ReceiptScanDetailPanel } from "@/components/dashboard/receipt-scan-detail-panel";
import { Button } from "@/components/ui/button";
import {
  getCategoryLabel,
  getReceiptScanStatus,
  getReceiptScanStatusBadgeClass,
  getScanStatusLabel,
  getStatusLabel,
} from "@/lib/constants/receipts";
import type { ReceiptDetail, ReceiptListItem } from "@/lib/api/types";
import {
  formatReceiptDate,
  formatRinggit,
  getStatusBadgeClass,
} from "@/lib/receipt-format";

const COLUMN_COUNT = 8;

type ReceiptHistoryTableProps = {
  items: ReceiptListItem[];
  categoryLabels: Record<string, string>;
};

function getMerchantLabel(item: ReceiptListItem): string {
  const scanStatus = getReceiptScanStatus(item);

  if (item.merchant_name) {
    return item.merchant_name;
  }

  switch (scanStatus) {
    case "processing":
      return "Processing…";
    case "failed":
      return "AI processing failed";
    case "waiting":
      return "Waiting for processing";
    default:
      return "Unnamed receipt";
  }
}

export function ReceiptHistoryTable({
  items,
  categoryLabels,
}: ReceiptHistoryTableProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [detailCache, setDetailCache] = useState<Record<string, ReceiptDetail>>(
    {},
  );
  const [loadingId, setLoadingId] = useState<string | null>(null);
  const [errorById, setErrorById] = useState<Record<string, string>>({});

  const loadDetail = useCallback(
    async (receiptId: string) => {
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
    },
    [detailCache],
  );

  const toggleRow = useCallback(
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

  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[720px] text-sm">
        <thead>
          <tr className="border-b text-left text-muted-foreground">
            <th className="w-10 pb-3 pr-2 font-medium">No.</th>
            <th className="w-10 pb-3 pr-2 font-medium">
              <span className="sr-only">Details</span>
            </th>
            <th className="pb-3 pr-4 font-medium">Merchant</th>
            <th className="pb-3 pr-4 font-medium">Category</th>
            <th className="pb-3 pr-4 font-medium">Date</th>
            <th className="pb-3 pr-4 text-right font-medium">Amount</th>
            <th className="pb-3 pr-4 font-medium">Status</th>
            <th className="pb-3 font-medium">Scan</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item, index) => {
            const scanStatus = getReceiptScanStatus(item);
            const merchantLabel = getMerchantLabel(item);
            const isExpanded = expandedId === item.id;
            const panelId = `receipt-scan-detail-${item.id}`;

            return (
              <Fragment key={item.id}>
                <tr className="border-b last:border-b-0">
                  <td className="py-3 pr-2 tabular-nums text-muted-foreground">
                    {index + 1}
                  </td>
                  <td className="py-3 pr-2">
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon-xs"
                      aria-expanded={isExpanded}
                      aria-controls={panelId}
                      aria-label="View scan details"
                      onClick={() => toggleRow(item)}
                    >
                      {isExpanded ? (
                        <ChevronDownIcon className="size-4" />
                      ) : (
                        <ChevronRightIcon className="size-4" />
                      )}
                    </Button>
                  </td>
                  <td className="py-3 pr-4 font-medium">{merchantLabel}</td>
                  <td className="py-3 pr-4 text-muted-foreground">
                    {item.category
                      ? getCategoryLabel(item.category, categoryLabels)
                      : "Not classified yet"}
                  </td>
                  <td className="py-3 pr-4 text-muted-foreground">
                    {formatReceiptDate(item.receipt_date ?? item.created_at)}
                  </td>
                  <td className="py-3 pr-4 text-right font-medium tabular-nums">
                    {formatRinggit(item.claimed_amount ?? item.total_amount)}
                  </td>
                  <td className="py-3 pr-4">
                    <span className={getStatusBadgeClass(item.status)}>
                      {getStatusLabel(item.status)}
                    </span>
                  </td>
                  <td className="py-3">
                    <span
                      className={getReceiptScanStatusBadgeClass(scanStatus)}
                    >
                      {getScanStatusLabel(scanStatus)}
                    </span>
                  </td>
                </tr>

                {isExpanded ? (
                  <tr className="border-b last:border-b-0">
                    <td colSpan={COLUMN_COUNT} className="px-2 pb-4 pt-0">
                      <div
                        id={panelId}
                        className="rounded-lg border bg-muted/30 p-4"
                      >
                        <p className="mb-3 text-xs font-medium uppercase tracking-wide text-muted-foreground">
                          AI scan details
                        </p>
                        <ReceiptScanDetailPanel
                          item={item}
                          detail={detailCache[item.id] ?? null}
                          scanStatus={scanStatus}
                          loading={loadingId === item.id}
                          error={errorById[item.id] ?? null}
                          categoryLabels={categoryLabels}
                        />
                      </div>
                    </td>
                  </tr>
                ) : null}
              </Fragment>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
