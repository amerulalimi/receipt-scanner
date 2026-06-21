import Link from "next/link";

import { ReceiptHistoryLimitSelect } from "@/components/dashboard/receipt-history-limit-select";
import { ReceiptHistoryTable } from "@/components/dashboard/receipt-history-table";
import { ReceiptScanToasts } from "@/components/dashboard/receipt-scan-toasts";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { getReceiptScanStatus } from "@/lib/constants/receipts";
import type { ReceiptListData } from "@/lib/api/types";
import { getDictionary } from "@/lib/i18n/get-dictionary";
import { createServerTranslator } from "@/lib/i18n/translate";
import type { Locale } from "@/lib/i18n/locales";

type ReceiptHistorySectionProps = {
  receipts: ReceiptListData;
  historyLimit: number;
  categoryLabels: Record<string, string>;
  taxYear: number;
  locale: Locale;
};

export async function ReceiptHistorySection({
  receipts,
  historyLimit,
  categoryLabels,
  taxYear,
  locale,
}: ReceiptHistorySectionProps) {
  const dictionary = await getDictionary(locale);
  const t = createServerTranslator(dictionary);

  const hasProcessing = receipts.items.some(
    (item) => getReceiptScanStatus(item) === "processing",
  );
  const hasWaiting = receipts.items.some(
    (item) => getReceiptScanStatus(item) === "waiting",
  );
  const failedCount = receipts.items.filter(
    (item) => getReceiptScanStatus(item) === "failed",
  ).length;

  return (
    <section className="space-y-4">
      <ReceiptScanToasts failedCount={failedCount} />
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="text-lg font-medium">
            {t("dashboard", "receiptHistory")}
          </h2>
          <p className="text-sm text-muted-foreground">
            {receipts.total === 0
              ? t("dashboard", "receiptHistoryEmpty")
              : t("dashboard", "receiptHistoryCount", {
                  count: receipts.total,
                  year: taxYear,
                })}
          </p>
        </div>

        <div className="flex flex-wrap items-end gap-3">
          {receipts.total > 0 ? (
            <ReceiptHistoryLimitSelect value={historyLimit} />
          ) : null}
          {receipts.total > 0 ? (
            <Button
              variant="outline"
              size="sm"
              render={<Link href="/dashboard/receipts" />}
            >
              {t("common", "viewAll")}
            </Button>
          ) : null}
        </div>
      </div>

      {hasProcessing ? (
        <p className="rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-sm text-amber-900 dark:text-amber-100">
          {t("dashboard", "processingNotice", {
            command: "python -m app.worker",
          })}
        </p>
      ) : null}

      {hasWaiting ? (
        <p className="rounded-lg border px-3 py-2 text-sm text-muted-foreground">
          {t("dashboard", "waitingNotice")}
        </p>
      ) : null}

      {receipts.items.length === 0 ? (
        <Card>
          <CardContent className="py-8 text-center text-sm text-muted-foreground">
            {t("dashboard", "noReceiptsYet")}
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">
              {t("dashboard", "listTitle")}
            </CardTitle>
            <CardDescription>
              {t("dashboard", "listDescription", {
                count: Math.min(receipts.items.length, historyLimit),
              })}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ReceiptHistoryTable
              items={receipts.items}
              categoryLabels={categoryLabels}
            />
          </CardContent>
        </Card>
      )}
    </section>
  );
}
