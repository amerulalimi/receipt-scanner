import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { ReceiptDeleteButton } from "@/components/receipts/receipt-delete-button";
import { ReceiptEditSheet } from "@/components/receipts/receipt-edit-sheet";
import { ReceiptThumbnail } from "@/components/receipts/receipt-thumbnail";
import {
  getCategoryLabel,
  getReceiptScanStatus,
  getReceiptScanStatusBadgeClass,
  getReceiptScanStatusLabels,
  getReceiptStatusLabels,
} from "@/lib/constants/receipts";
import {
  formatReceiptDate,
  formatRinggit,
  getStatusBadgeClass,
} from "@/lib/receipt-format";
import type { ReceiptListData } from "@/lib/api/types";
import { getDictionary } from "@/lib/i18n/get-dictionary";
import { createServerTranslator } from "@/lib/i18n/translate";
import type { Locale } from "@/lib/i18n/locales";

type ReceiptsListSectionProps = {
  receipts: ReceiptListData;
  categoryLabels: Record<string, string>;
  categoryOptions: Array<{ value: string; label: string }>;
  locale: Locale;
};

function getMerchantLabel(
  item: ReceiptListData["items"][number],
  t: ReturnType<typeof createServerTranslator>,
): string {
  const scanStatus = getReceiptScanStatus(item);

  if (item.merchant_name) {
    return item.merchant_name;
  }

  switch (scanStatus) {
    case "processing":
      return t("receipts", "merchantProcessing");
    case "failed":
      return t("receipts", "merchantFailed");
    case "waiting":
      return t("receipts", "merchantWaiting");
    default:
      return t("receipts", "merchantUnnamed");
  }
}

export async function ReceiptsListSection({
  receipts,
  categoryLabels,
  categoryOptions,
  locale,
}: ReceiptsListSectionProps) {
  const dictionary = await getDictionary(locale);
  const t = createServerTranslator(dictionary);
  const statusLabels = getReceiptStatusLabels((key) => t("receipts", key));
  const scanStatusLabels = getReceiptScanStatusLabels((key) => t("receipts", key));

  if (receipts.items.length === 0) {
    return (
      <Card>
        <CardContent className="py-10 text-center text-sm text-muted-foreground">
          {t("receipts", "noReceiptsHint")}
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base">
          {t("receipts", "listSectionTitle")}
        </CardTitle>
        <CardDescription>
          {t("receipts", "listSectionDescription", { total: receipts.total })}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {receipts.items.map((item) => {
          const scanStatus = getReceiptScanStatus(item);
          const merchantLabel = getMerchantLabel(item, t);

          return (
            <div
              key={item.id}
              className="flex flex-col gap-3 rounded-lg border px-3 py-3 sm:flex-row sm:items-start sm:justify-between"
            >
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
                        : t("receipts", "categoryManualReview")}
                      {" · "}
                      {formatReceiptDate(item.receipt_date ?? item.created_at)}
                    </p>
                  </div>

                  <div className="flex flex-wrap gap-2">
                    <span className={getStatusBadgeClass(item.status)}>
                      {statusLabels[item.status] ?? item.status}
                    </span>
                    <span className={getReceiptScanStatusBadgeClass(scanStatus)}>
                      {scanStatusLabels[scanStatus]}
                    </span>
                  </div>
                </div>
              </div>

              <div className="flex flex-col items-start gap-3 sm:items-end">
                <p className="text-sm font-medium tabular-nums">
                  {formatRinggit(item.claimed_amount ?? item.total_amount)}
                </p>

                <div className="flex flex-wrap gap-2">
                  <ReceiptEditSheet
                    item={item}
                    categoryOptions={categoryOptions}
                  />
                  <ReceiptDeleteButton
                    receiptId={item.id}
                    merchantLabel={merchantLabel}
                  />
                </div>
              </div>
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}
