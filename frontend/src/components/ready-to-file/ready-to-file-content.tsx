import Link from "next/link";

import { ReadyToFilePrintButton } from "@/components/ready-to-file/ready-to-file-print-button";
import { DashboardYearFilter } from "@/components/dashboard/dashboard-year-filter";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import type { ReadyToFileData } from "@/lib/api/types";
import { getCategoryLabel } from "@/lib/constants/receipts";
import { getCurrencyFormatter, getDictionary } from "@/lib/i18n/get-dictionary";
import { createServerTranslator } from "@/lib/i18n/translate";
import type { Locale } from "@/lib/i18n/locales";

type ReadyToFileContentProps = {
  data: ReadyToFileData;
  categoryLabels: Record<string, string>;
  locale: Locale;
};

export async function ReadyToFileContent({
  data,
  categoryLabels,
  locale,
}: ReadyToFileContentProps) {
  const dictionary = await getDictionary(locale);
  const t = createServerTranslator(dictionary);
  const formatRinggit = getCurrencyFormatter(locale);

  return (
    <div className="ready-to-file-print space-y-8">
      <header className="flex flex-wrap items-end justify-between gap-4 print:block">
        <div className="space-y-1">
          <h1 className="text-2xl font-semibold tracking-tight">
            {t("readyToFile", "title")}
          </h1>
          <p className="text-sm text-muted-foreground">
            {t("readyToFile", "subtitle", { year: data.tax_year })}
          </p>
        </div>
        <div className="flex flex-wrap items-end gap-3 print:hidden">
          <DashboardYearFilter
            defaultYear={data.tax_year}
            label={t("dashboard", "taxYear")}
          />
          <ReadyToFilePrintButton />
        </div>
      </header>

      {data.pending_review_count > 0 ? (
        <div className="rounded-lg border border-amber-500/40 bg-amber-500/10 px-4 py-3 text-sm print:hidden">
          {t("readyToFile", "pendingNotice", {
            count: data.pending_review_count,
          })}
        </div>
      ) : null}

      <div className="grid gap-4 sm:grid-cols-2">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>{t("readyToFile", "totalApproved")}</CardDescription>
            <CardTitle className="text-2xl tabular-nums">
              {formatRinggit.format(Number(data.total_claimed))}
            </CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>
              {t("readyToFile", "estimatedSavings")}
            </CardDescription>
            <CardTitle className="text-2xl tabular-nums">
              {formatRinggit.format(Number(data.estimated_savings))}
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-0 text-xs text-muted-foreground">
            {t("dashboard", "estimatedSavingsHint", {
              bracket: data.tax_bracket.toFixed(0),
            })}
          </CardContent>
        </Card>
      </div>

      <section className="space-y-4">
        <div>
          <h2 className="text-lg font-medium">{t("readyToFile", "fieldsTitle")}</h2>
          <p className="text-sm text-muted-foreground">
            {t("readyToFile", "fieldsHint")}
          </p>
        </div>

        {data.fields.length === 0 ? (
          <Card>
            <CardContent className="py-10 text-center text-sm text-muted-foreground">
              {t("readyToFile", "noApprovedClaims")}
              <div className="mt-4 print:hidden">
                <Button render={<Link href="/dashboard/receipts" />} variant="outline">
                  {t("readyToFile", "viewReceipts")}
                </Button>
              </div>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-3">
            {data.fields.map((field) => (
              <Card key={field.category}>
                <CardHeader className="pb-2">
                  <div className="flex flex-wrap items-start justify-between gap-2">
                    <div>
                      <CardDescription>
                        {t("readyToFile", "stepLabel", { step: field.step })} ·{" "}
                        {field.lhdn_section} · {field.be_seksyen}
                      </CardDescription>
                      <CardTitle className="text-base">
                        {field.lhdn_field_en}
                      </CardTitle>
                    </div>
                    <p className="text-xl font-semibold tabular-nums">
                      {formatRinggit.format(Number(field.amount))}
                    </p>
                  </div>
                </CardHeader>
                <CardContent className="pt-0 text-xs text-muted-foreground">
                  {getCategoryLabel(field.category, categoryLabels)} ·{" "}
                  {t("readyToFile", "receiptCount", {
                    count: field.receipt_count,
                  })}
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </section>

      <section className="space-y-4">
        <div>
          <h2 className="text-lg font-medium">
            {t("readyToFile", "checklistTitle")}
          </h2>
          <p className="text-sm text-muted-foreground">
            {t("readyToFile", "checklistHint")}
          </p>
        </div>

        <Card>
          <CardContent className="py-4">
            <ol className="list-decimal space-y-3 pl-5 text-sm">
              {data.checklist.map((item) => (
                <li key={item.order}>
                  {item.text_en}
                </li>
              ))}
            </ol>
          </CardContent>
        </Card>
      </section>

      <p className="text-xs text-muted-foreground">
        {t("readyToFile", "disclaimer")}
      </p>
    </div>
  );
}
