"use client";

import { ChevronDownIcon, ChevronRightIcon } from "lucide-react";
import { useCallback } from "react";

import { ReceiptScanDetailPanel } from "@/components/dashboard/receipt-scan-detail-panel";
import { ReceiptDeleteButton } from "@/components/receipts/receipt-delete-button";
import { ReceiptEditSheet } from "@/components/receipts/receipt-edit-sheet";
import { ReceiptThumbnail } from "@/components/receipts/receipt-thumbnail";
import { Button } from "@/components/ui/button";
import { useReceiptScanDetail } from "@/hooks/use-receipt-scan-detail";
import {
  getCategoryLabel,
  getReceiptScanStatus,
  getReceiptScanStatusBadgeClass,
} from "@/lib/constants/receipts";
import type { ReceiptListItem } from "@/lib/api/types";
import {
  formatReceiptDate,
  formatRinggit,
  getStatusBadgeClass,
} from "@/lib/receipt-format";

type ReceiptListItemLabels = {
  merchantProcessing: string;
  merchantFailed: string;
  merchantWaiting: string;
  merchantUnnamed: string;
  categoryManualReview: string;
  scanDetailsTitle: string;
  viewScanDetails: string;
  statusLabels: Record<string, string>;
  scanStatusLabels: Record<string, string>;
};

type ReceiptListItemProps = {
  item: ReceiptListItem;
  categoryLabels: Record<string, string>;
  categoryOptions: Array<{ value: string; label: string }>;
  labels: ReceiptListItemLabels;
  isExpanded: boolean;
  onToggle: () => void;
  detail: ReturnType<typeof useReceiptScanDetail>["detailCache"][string] | null;
  loading: boolean;
  error: string | null;
};

function getMerchantLabel(
  item: ReceiptListItem,
  labels: ReceiptListItemLabels,
): string {
  const scanStatus = getReceiptScanStatus(item);

  if (item.merchant_name) {
    return item.merchant_name;
  }

  switch (scanStatus) {
    case "processing":
      return labels.merchantProcessing;
    case "failed":
      return labels.merchantFailed;
    case "waiting":
      return labels.merchantWaiting;
    default:
      return labels.merchantUnnamed;
  }
}

export function ReceiptListItem({
  item,
  categoryLabels,
  categoryOptions,
  labels,
  isExpanded,
  onToggle,
  detail,
  loading,
  error,
}: ReceiptListItemProps) {
  const scanStatus = getReceiptScanStatus(item);
  const merchantLabel = getMerchantLabel(item, labels);
  const panelId = `receipt-scan-detail-${item.id}`;

  return (
    <div className="rounded-lg border">
      <div className="flex flex-col gap-3 px-3 py-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex min-w-0 gap-2">
          <Button
            type="button"
            variant="ghost"
            size="icon-xs"
            className="mt-0.5 shrink-0"
            aria-expanded={isExpanded}
            aria-controls={panelId}
            aria-label={labels.viewScanDetails}
            onClick={onToggle}
          >
            {isExpanded ? (
              <ChevronDownIcon className="size-4" />
            ) : (
              <ChevronRightIcon className="size-4" />
            )}
          </Button>

          <div className="flex min-w-0 gap-3">
            <ReceiptThumbnail
              receiptId={item.id}
              fileType={item.file_type}
              merchantName={merchantLabel}
              size="sm"
            />

            <div className="min-w-0 space-y-2">
              <div className="space-y-1">
                <p className="font-medium">{merchantLabel}</p>
                <p className="text-sm text-muted-foreground">
                  {item.category
                    ? getCategoryLabel(item.category, categoryLabels)
                    : labels.categoryManualReview}
                  {" · "}
                  {formatReceiptDate(item.receipt_date ?? item.created_at)}
                </p>
              </div>

              <div className="flex flex-wrap gap-2">
                <span className={getStatusBadgeClass(item.status)}>
                  {labels.statusLabels[item.status] ?? item.status}
                </span>
                <span className={getReceiptScanStatusBadgeClass(scanStatus)}>
                  {labels.scanStatusLabels[scanStatus]}
                </span>
              </div>
            </div>
          </div>
        </div>

        <div className="flex flex-col items-start gap-3 pl-9 sm:items-end sm:pl-0">
          <p className="text-sm font-medium tabular-nums">
            {formatRinggit(item.claimed_amount ?? item.total_amount)}
          </p>

          <div className="flex flex-wrap gap-2">
            <ReceiptEditSheet item={item} categoryOptions={categoryOptions} />
            <ReceiptDeleteButton
              receiptId={item.id}
              merchantLabel={merchantLabel}
            />
          </div>
        </div>
      </div>

      {isExpanded ? (
        <div className="border-t px-3 pb-4 pt-3">
          <div
            id={panelId}
            className="rounded-lg border bg-muted/30 p-4"
          >
            <p className="mb-3 text-xs font-medium uppercase tracking-wide text-muted-foreground">
              {labels.scanDetailsTitle}
            </p>
            <ReceiptScanDetailPanel
              item={item}
              detail={detail}
              scanStatus={scanStatus}
              loading={loading}
              error={error}
              categoryLabels={categoryLabels}
            />
          </div>
        </div>
      ) : null}
    </div>
  );
}

type ReceiptsListItemsProps = {
  items: ReceiptListItem[];
  categoryLabels: Record<string, string>;
  categoryOptions: Array<{ value: string; label: string }>;
  labels: ReceiptListItemLabels;
};

export function ReceiptsListItems({
  items,
  categoryLabels,
  categoryOptions,
  labels,
}: ReceiptsListItemsProps) {
  const { expandedId, detailCache, loadingId, errorById, toggleExpand } =
    useReceiptScanDetail();

  const handleToggle = useCallback(
    (item: ReceiptListItem) => {
      toggleExpand(item);
    },
    [toggleExpand],
  );

  return (
    <div className="space-y-3">
      {items.map((item) => (
        <ReceiptListItem
          key={item.id}
          item={item}
          categoryLabels={categoryLabels}
          categoryOptions={categoryOptions}
          labels={labels}
          isExpanded={expandedId === item.id}
          onToggle={() => handleToggle(item)}
          detail={detailCache[item.id] ?? null}
          loading={loadingId === item.id}
          error={errorById[item.id] ?? null}
        />
      ))}
    </div>
  );
}
