import type { ReactNode } from "react";

import {
  getCategoryLabel,
  getFlagLabel,
  getReceiptScanStatusBadgeClass,
  getScanStatusLabel,
  type ReceiptScanStatus,
} from "@/lib/constants/receipts";
import type { ReceiptDetail, ReceiptListItem } from "@/lib/api/types";
import { ReceiptLineItemsSummary } from "@/components/receipts/receipt-line-items-summary";
import { formatReceiptDate, formatRinggit } from "@/lib/receipt-format";

type ReceiptScanDetailPanelProps = {
  item: ReceiptListItem;
  detail: ReceiptDetail | null;
  scanStatus: ReceiptScanStatus;
  loading: boolean;
  error: string | null;
  categoryLabels: Record<string, string>;
};

function formatConfidence(value: number | null | undefined): string {
  if (value === null || value === undefined) {
    return "—";
  }

  return `${Math.round(value * 100)}%`;
}

function DetailField({
  label,
  value,
}: {
  label: string;
  value: ReactNode;
}) {
  return (
    <div className="space-y-0.5">
      <dt className="text-xs text-muted-foreground">{label}</dt>
      <dd className="text-sm">{value}</dd>
    </div>
  );
}

export function ReceiptScanDetailPanel({
  item,
  detail,
  scanStatus,
  loading,
  error,
  categoryLabels,
}: ReceiptScanDetailPanelProps) {
  if (loading) {
    return (
      <p className="text-sm text-muted-foreground">Loading details…</p>
    );
  }

  if (error) {
    return <p className="text-sm text-destructive">{error}</p>;
  }

  if (scanStatus === "processing") {
    return (
      <p className="text-sm text-muted-foreground">
        The receipt is being processed by AI. Scan details will be available
        once processing completes.
      </p>
    );
  }

  if (scanStatus === "waiting") {
    return (
      <p className="text-sm text-muted-foreground">
        The receipt is waiting for processing or manual review. Scan details
        are not available yet.
      </p>
    );
  }

  const merchantName =
    detail?.merchant_name ?? item.merchant_name ?? "Unnamed receipt";
  const receiptDate = detail?.receipt_date ?? item.receipt_date;
  const totalAmount = detail?.total_amount ?? item.total_amount;
  const claimedAmount = detail?.claimed_amount ?? item.claimed_amount;
  const category = detail?.category ?? item.category;
  const beSeksyen = detail?.be_seksyen ?? item.be_seksyen;
  const aiConfidence = detail?.ai_confidence ?? item.ai_confidence;
  const aiNota = detail?.ai_nota;
  const flags = detail?.flags ?? [];
  const lineItems = detail?.line_items ?? [];

  if (scanStatus === "failed" && !detail) {
    return (
      <p className="text-sm text-destructive">
        Scan processing failed. Please re-upload or review the receipt manually.
      </p>
    );
  }

  return (
    <dl className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <DetailField label="Merchant" value={merchantName} />
      <DetailField
        label="Receipt date"
        value={formatReceiptDate(receiptDate ?? item.created_at)}
      />
      <DetailField label="Total amount" value={formatRinggit(totalAmount)} />
      <DetailField
        label="Claimed amount"
        value={formatRinggit(claimedAmount ?? totalAmount)}
      />
      <DetailField
        label="Ineligible amount"
        value={formatRinggit(detail?.excluded_amount ?? 0)}
      />
      <DetailField
        label="Category"
        value={
          category ? getCategoryLabel(category, categoryLabels) : "Not classified yet"
        }
      />
      <DetailField label="Tax section" value={beSeksyen ?? "—"} />
      <DetailField
        label="AI confidence"
        value={formatConfidence(aiConfidence)}
      />
      <DetailField
        label="OCR confidence"
        value={formatConfidence(detail?.ocr_confidence)}
      />
      <DetailField
        label="Scan status"
        value={
          <span className={getReceiptScanStatusBadgeClass(scanStatus)}>
            {getScanStatusLabel(scanStatus)}
          </span>
        }
      />

      {aiNota ? (
        <div className="space-y-0.5 sm:col-span-2 lg:col-span-3">
          <dt className="text-xs text-muted-foreground">AI notes</dt>
          <dd className="rounded-md border-l-2 border-muted-foreground/30 bg-background/50 px-3 py-2 text-sm text-muted-foreground">
            {aiNota}
          </dd>
        </div>
      ) : null}

      <ReceiptLineItemsSummary
        lineItems={lineItems}
        categoryLabels={categoryLabels}
        title="Itemised breakdown"
      />

      {flags.length > 0 ? (
        <div className="space-y-1 sm:col-span-2 lg:col-span-3">
          <dt className="text-xs text-muted-foreground">Flags</dt>
          <dd className="flex flex-wrap gap-2">
            {flags.map((flag) => (
              <span
                key={flag.id}
                className="rounded-full border border-amber-500/40 bg-amber-500/10 px-2 py-0.5 text-xs font-medium text-amber-900 dark:text-amber-100"
                title={flag.message ?? undefined}
              >
                {getFlagLabel(flag.flag_type)}
                {flag.message ? `: ${flag.message}` : ""}
              </span>
            ))}
          </dd>
        </div>
      ) : null}

      {scanStatus === "failed" ? (
        <div className="sm:col-span-2 lg:col-span-3">
          <p className="text-sm text-destructive">
            Scan processing failed. Check the AI notes or re-upload the receipt.
          </p>
        </div>
      ) : null}
    </dl>
  );
}
