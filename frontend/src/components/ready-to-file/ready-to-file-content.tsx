import Link from "next/link";

import { ReadyToFileExportButton } from "@/components/ready-to-file/ready-to-file-export-button";
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
import { getCurrencyFormatter, getDictionary } from "@/lib/i18n/get-dictionary";
import { createServerTranslator } from "@/lib/i18n/translate";
import type { Locale } from "@/lib/i18n/locales";
import { cn } from "@/lib/utils";

type ReadyToFileContentProps = {
  data: ReadyToFileData;
  categoryLabels: Record<string, string>;
  locale: Locale;
};

function statusBadgeClass(status: string): string {
  if (status === "ready") {
    return "bg-emerald-500/10 text-emerald-700 dark:text-emerald-400";
  }
  if (status === "partial") {
    return "bg-amber-500/10 text-amber-700 dark:text-amber-400";
  }
  return "bg-muted text-muted-foreground";
}

export async function ReadyToFileContent({
  data,
  categoryLabels,
  locale,
}: ReadyToFileContentProps) {
  const dictionary = await getDictionary(locale);
  const t = createServerTranslator(dictionary);
  const formatRinggit = getCurrencyFormatter(locale);
  const filingChecklist = data.filing_checklist ?? [];
  const totalRelief = Number(data.total_relief ?? data.total_claimed);

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
          <ReadyToFileExportButton taxYear={data.tax_year} />
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
            <CardDescription>{t("readyToFile", "totalRelief")}</CardDescription>
            <CardTitle className="text-2xl tabular-nums">
              {formatRinggit.format(totalRelief)}
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
          <h2 className="text-lg font-medium">{t("readyToFile", "filingTableTitle")}</h2>
          <p className="text-sm text-muted-foreground">
            {t("readyToFile", "filingTableHint")}
          </p>
        </div>

        {filingChecklist.length === 0 ? (
          <Card>
            <CardContent className="py-10 text-center text-sm text-muted-foreground">
              {t("readyToFile", "noApprovedClaims")}
            </CardContent>
          </Card>
        ) : (
          <div className="overflow-x-auto rounded-xl border">
            <table className="w-full min-w-[640px] text-sm">
              <thead className="border-b bg-muted/40 text-left">
                <tr>
                  <th className="px-4 py-3 font-medium">{t("readyToFile", "colSection")}</th>
                  <th className="px-4 py-3 font-medium">{t("readyToFile", "colDescription")}</th>
                  <th className="px-4 py-3 font-medium">{t("readyToFile", "colAmount")}</th>
                  <th className="px-4 py-3 font-medium">{t("readyToFile", "colReceipts")}</th>
                  <th className="px-4 py-3 font-medium">{t("readyToFile", "colStatus")}</th>
                </tr>
              </thead>
              <tbody>
                {filingChecklist.map((item, index) => (
                  <tr key={`${item.be_seksyen}-${index}`} className="border-b last:border-0">
                    <td className="px-4 py-3 align-top">
                      <div className="font-medium">{item.be_field}</div>
                      <div className="text-xs text-muted-foreground">{item.be_seksyen}</div>
                    </td>
                    <td className="px-4 py-3 align-top">{item.description}</td>
                    <td className="px-4 py-3 align-top tabular-nums">
                      {formatRinggit.format(Number(item.amount_to_enter))}
                    </td>
                    <td className="px-4 py-3 align-top">{item.receipt_count}</td>
                    <td className="px-4 py-3 align-top">
                      <span
                        className={cn(
                          "inline-flex rounded-full px-2 py-0.5 text-xs font-medium",
                          statusBadgeClass(item.status),
                        )}
                      >
                        {item.status === "ready"
                          ? t("readyToFile", "statusReady")
                          : item.status === "partial"
                            ? t("readyToFile", "statusPartial")
                            : t("readyToFile", "statusEmpty")}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {data.fields.length === 0 ? (
          <div className="print:hidden">
            <Button render={<Link href="/dashboard/receipts" />} variant="outline">
              {t("readyToFile", "viewReceipts")}
            </Button>
          </div>
        ) : null}
      </section>

      <section className="space-y-4 print:hidden">
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
                  {locale === "ms" ? item.text_my : item.text_en}
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
