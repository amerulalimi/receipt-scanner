"use client";

import {
  startTransition,
  useActionState,
  useEffect,
  useState,
} from "react";

import {
  bulkApproveOrgPendingAction,
  initialOrgActionState,
  reviewOrgReceiptAction,
} from "@/actions/org";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  getCategoryLabel,
  getReceiptStatusLabels,
} from "@/lib/constants/receipts";
import { formatReceiptDate, formatRinggit, getStatusBadgeClass } from "@/lib/receipt-format";
import type { OrgPendingReceiptListData } from "@/lib/api/types";
import { useTranslations } from "@/lib/i18n/use-translations";

export function OrgPendingApprovalsSection({
  pending,
  categoryLabels,
  taxYear,
}: {
  pending: OrgPendingReceiptListData;
  categoryLabels: Record<string, string>;
  taxYear: number;
}) {
  const t = useTranslations("org");
  const tReceipts = useTranslations("receipts");
  const statusLabels = getReceiptStatusLabels((key) => tReceipts(key));

  const [reviewState, reviewAction, isReviewPending] = useActionState(
    reviewOrgReceiptAction,
    initialOrgActionState,
  );
  const [bulkState, bulkAction, isBulkPending] = useActionState(
    bulkApproveOrgPendingAction,
    initialOrgActionState,
  );
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    const nextMessage =
      reviewState.message ?? reviewState.error ?? bulkState.message ?? bulkState.error;
    if (nextMessage) {
      setMessage(nextMessage);
    }
  }, [reviewState, bulkState]);

  function reviewReceipt(receiptId: string, action: "approve" | "reject") {
    const formData = new FormData();
    formData.set("receipt_id", receiptId);
    formData.set("action", action);
    startTransition(() => {
      reviewAction(formData);
    });
  }

  function bulkApprove() {
    const formData = new FormData();
    formData.set("tax_year", String(taxYear));
    startTransition(() => {
      bulkAction(formData);
    });
  }

  if (pending.items.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">{t("pendingApprovalsTitle")}</CardTitle>
          <CardDescription>{t("pendingApprovalsEmpty")}</CardDescription>
        </CardHeader>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <CardTitle className="text-base">{t("pendingApprovalsTitle")}</CardTitle>
            <CardDescription>
              {t("pendingApprovalsDescription", { total: pending.total })}
            </CardDescription>
          </div>
          <Button
            type="button"
            size="sm"
            disabled={isBulkPending || isReviewPending}
            onClick={bulkApprove}
          >
            {isBulkPending ? t("bulkApproving") : t("bulkApprove")}
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {message ? (
          <p
            className={
              reviewState.error || bulkState.error
                ? "text-sm text-destructive"
                : "text-sm text-emerald-600"
            }
          >
            {message}
          </p>
        ) : null}

        {pending.items.map((item) => (
          <div
            key={item.id}
            className="flex flex-col gap-3 rounded-lg border px-3 py-3 lg:flex-row lg:items-center lg:justify-between"
          >
            <div className="min-w-0 space-y-1">
              <p className="font-medium">
                {item.merchant_name ?? t("unnamedReceipt")}
              </p>
              <p className="text-sm text-muted-foreground">
                {item.employee_name ?? item.employee_email} ·{" "}
                {item.category
                  ? getCategoryLabel(item.category, categoryLabels)
                  : tReceipts("categoryManualReview")}
                {" · "}
                {formatReceiptDate(item.receipt_date ?? item.created_at)}
              </p>
              <span className={getStatusBadgeClass(item.status)}>
                {statusLabels[item.status as keyof typeof statusLabels] ??
                  item.status}
              </span>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <p className="text-sm font-medium tabular-nums">
                {formatRinggit(item.claimed_amount)}
              </p>
              <div className="flex gap-2">
                <Button
                  type="button"
                  size="sm"
                  disabled={isReviewPending || isBulkPending}
                  onClick={() => reviewReceipt(item.id, "approve")}
                >
                  {t("approve")}
                </Button>
                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  disabled={isReviewPending || isBulkPending}
                  onClick={() => reviewReceipt(item.id, "reject")}
                >
                  {t("reject")}
                </Button>
              </div>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
