import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { ReceiptsListItems } from "@/components/receipts/receipt-list-item";
import {
  getReceiptScanStatusLabels,
  getReceiptStatusLabels,
} from "@/lib/constants/receipts";
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
      <CardContent>
        <ReceiptsListItems
          items={receipts.items}
          categoryLabels={categoryLabels}
          categoryOptions={categoryOptions}
          labels={{
            merchantProcessing: t("receipts", "merchantProcessing"),
            merchantFailed: t("receipts", "merchantFailed"),
            merchantWaiting: t("receipts", "merchantWaiting"),
            merchantUnnamed: t("receipts", "merchantUnnamed"),
            categoryManualReview: t("receipts", "categoryManualReview"),
            scanDetailsTitle: t("receipts", "scanDetailsTitle"),
            viewScanDetails: t("receipts", "viewScanDetails"),
            statusLabels,
            scanStatusLabels,
          }}
        />
      </CardContent>
    </Card>
  );
}
