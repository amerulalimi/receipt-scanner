import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { ClaimSummaryData, CompletenessScoreData } from "@/lib/api/types";
import { getCurrencyFormatter, getDictionary } from "@/lib/i18n/get-dictionary";
import { createServerTranslator } from "@/lib/i18n/translate";
import type { Locale } from "@/lib/i18n/locales";

import { ClaimCategoryCard } from "./claim-category-card";

type ClaimSummarySectionProps = {
  summary: ClaimSummaryData;
  completeness?: CompletenessScoreData | null;
  categoryLabels: Record<string, string>;
  locale: Locale;
};

export async function ClaimSummarySection({
  summary,
  completeness,
  categoryLabels,
  locale,
}: ClaimSummarySectionProps) {
  const dictionary = await getDictionary(locale);
  const t = createServerTranslator(dictionary);
  const formatRinggit = getCurrencyFormatter(locale);

  const totalClaimed = summary.categories.reduce(
    (total, category) => total + category.claimed,
    0,
  );
  const totalReceipts = summary.categories.reduce(
    (total, category) => total + category.receipt_count,
    0,
  );

  return (
    <section className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>{t("dashboard", "totalClaimed")}</CardDescription>
            <CardTitle className="text-2xl tabular-nums">
              {formatRinggit.format(totalClaimed)}
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-0 text-xs text-muted-foreground">
            {t("dashboard", "totalClaimedHint")}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription>
              {t("dashboard", "estimatedSavings")}
            </CardDescription>
            <CardTitle className="text-2xl tabular-nums">
              {formatRinggit.format(summary.estimated_savings)}
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-0 text-xs text-muted-foreground">
            {t("dashboard", "estimatedSavingsHint", {
              bracket: summary.tax_bracket.toFixed(0),
            })}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription>{t("dashboard", "receiptsProcessed")}</CardDescription>
            <CardTitle className="text-2xl tabular-nums">
              {totalReceipts}
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-0 text-xs text-muted-foreground">
            {t("dashboard", "receiptsProcessedHint")}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription>{t("dashboard", "completenessScore")}</CardDescription>
            <CardTitle className="text-2xl tabular-nums">
              {completeness ? `${completeness.score}/100` : "—"}
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-0 text-xs text-muted-foreground">
            {t("dashboard", "completenessScoreHint")}
          </CardContent>
        </Card>
      </div>

      <div>
        <div className="mb-4">
          <h2 className="text-lg font-medium">
            {t("dashboard", "reliefLimitsTitle")}
          </h2>
          <p className="text-sm text-muted-foreground">
            {t("dashboard", "reliefLimitsHint")}
          </p>
        </div>

        {summary.categories.length === 0 ? (
          <Card>
            <CardContent className="py-8 text-center text-sm text-muted-foreground">
              {t("dashboard", "noReliefData")}
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {summary.categories.map((category) => (
              <ClaimCategoryCard
                key={category.category}
                category={category}
                categoryLabels={categoryLabels}
                locale={locale}
              />
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
