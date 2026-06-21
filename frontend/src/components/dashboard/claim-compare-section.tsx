import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { ClaimCompareData } from "@/lib/api/types";
import { getCategoryLabel } from "@/lib/constants/receipts";
import { getCurrencyFormatter, getDictionary } from "@/lib/i18n/get-dictionary";
import { createServerTranslator } from "@/lib/i18n/translate";
import type { Locale } from "@/lib/i18n/locales";
import { cn } from "@/lib/utils";

type ClaimCompareSectionProps = {
  comparison: ClaimCompareData;
  categoryLabels: Record<string, string>;
  locale: Locale;
};

function sumClaimed(categories: ClaimCompareData["current"]["categories"]) {
  return categories.reduce((total, category) => total + category.claimed, 0);
}

function formatDelta(delta: number, formatRinggit: Intl.NumberFormat) {
  if (delta === 0) {
    return formatRinggit.format(0);
  }

  const prefix = delta > 0 ? "+" : "−";
  return `${prefix}${formatRinggit.format(Math.abs(delta))}`;
}

export async function ClaimCompareSection({
  comparison,
  categoryLabels,
  locale,
}: ClaimCompareSectionProps) {
  const dictionary = await getDictionary(locale);
  const t = createServerTranslator(dictionary);
  const formatRinggit = getCurrencyFormatter(locale);

  const currentTotal = sumClaimed(comparison.current.categories);
  const previousTotal = sumClaimed(comparison.previous.categories);
  const claimedDelta = currentTotal - previousTotal;
  const savingsDelta =
    comparison.current.estimated_savings - comparison.previous.estimated_savings;

  const categoryMap = new Map(
    comparison.current.categories.map((category) => [category.category, category]),
  );
  for (const category of comparison.previous.categories) {
    if (!categoryMap.has(category.category)) {
      categoryMap.set(category.category, category);
    }
  }

  const rows = [...categoryMap.values()]
    .map((currentCategory) => {
      const previousCategory = comparison.previous.categories.find(
        (item) => item.category === currentCategory.category,
      );
      const currentClaimed =
        comparison.current.categories.find(
          (item) => item.category === currentCategory.category,
        )?.claimed ?? 0;
      const previousClaimed = previousCategory?.claimed ?? 0;

      return {
        category: currentCategory.category,
        be_seksyen: currentCategory.be_seksyen ?? previousCategory?.be_seksyen,
        currentClaimed,
        previousClaimed,
        delta: currentClaimed - previousClaimed,
      };
    })
    .filter((row) => row.currentClaimed > 0 || row.previousClaimed > 0)
    .sort((a, b) => b.currentClaimed - a.currentClaimed);

  if (previousTotal === 0 && currentTotal === 0) {
    return null;
  }

  return (
    <section className="space-y-4">
      <div>
        <h2 className="text-lg font-medium">
          {t("dashboard", "compareTitle")}
        </h2>
        <p className="text-sm text-muted-foreground">
          {t("dashboard", "compareHint", {
            current: comparison.current_year,
            previous: comparison.previous_year,
          })}
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>
              {t("dashboard", "compareTotalClaimed")}
            </CardDescription>
            <CardTitle className="text-2xl tabular-nums">
              {formatRinggit.format(currentTotal)}
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-0 text-xs text-muted-foreground">
            {t("dashboard", "compareVsPrevious", {
              year: comparison.previous_year,
              amount: formatRinggit.format(previousTotal),
              delta: formatDelta(claimedDelta, formatRinggit),
            })}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription>
              {t("dashboard", "compareEstimatedSavings")}
            </CardDescription>
            <CardTitle className="text-2xl tabular-nums">
              {formatRinggit.format(comparison.current.estimated_savings)}
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-0 text-xs text-muted-foreground">
            {t("dashboard", "compareVsPrevious", {
              year: comparison.previous_year,
              amount: formatRinggit.format(comparison.previous.estimated_savings),
              delta: formatDelta(savingsDelta, formatRinggit),
            })}
          </CardContent>
        </Card>
      </div>

      {rows.length > 0 ? (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">
              {t("dashboard", "compareByCategory")}
            </CardTitle>
            <CardDescription>
              {t("dashboard", "compareByCategoryHint")}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            {rows.map((row) => (
              <div
                key={row.category}
                className="flex flex-col gap-1 rounded-md border px-3 py-2 sm:flex-row sm:items-center sm:justify-between"
              >
                <div>
                  <p className="text-sm font-medium">
                    {getCategoryLabel(row.category, categoryLabels)}
                  </p>
                  {row.be_seksyen ? (
                    <p className="text-xs text-muted-foreground">
                      {row.be_seksyen}
                    </p>
                  ) : null}
                </div>
                <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm tabular-nums">
                  <span>
                    {comparison.current_year}:{" "}
                    {formatRinggit.format(row.currentClaimed)}
                  </span>
                  <span className="text-muted-foreground">
                    {comparison.previous_year}:{" "}
                    {formatRinggit.format(row.previousClaimed)}
                  </span>
                  <span
                    className={cn(
                      "font-medium",
                      row.delta > 0
                        ? "text-emerald-600 dark:text-emerald-400"
                        : row.delta < 0
                          ? "text-destructive"
                          : "text-muted-foreground",
                    )}
                  >
                    {formatDelta(row.delta, formatRinggit)}
                  </span>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      ) : null}
    </section>
  );
}
