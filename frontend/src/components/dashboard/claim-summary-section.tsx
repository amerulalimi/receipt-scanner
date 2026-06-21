import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { ClaimSummaryData } from "@/lib/api/types";
import { getCurrencyFormatter, getDictionary } from "@/lib/i18n/get-dictionary";
import { createServerTranslator } from "@/lib/i18n/translate";
import type { Locale } from "@/lib/i18n/locales";

import { ClaimCategoryCard } from "./claim-category-card";

type ClaimSummarySectionProps = {
  summary: ClaimSummaryData;
  categoryLabels: Record<string, string>;
  locale: Locale;
};

export async function ClaimSummarySection({
  summary,
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

  return (
    <section className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>{t("dashboard", "taxYear")}</CardDescription>
            <CardTitle className="text-2xl tabular-nums">
              {summary.tax_year}
            </CardTitle>
          </CardHeader>
        </Card>

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
