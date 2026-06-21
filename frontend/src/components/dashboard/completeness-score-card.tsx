import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { CompletenessScoreData } from "@/lib/api/types";
import { getCurrencyFormatter, getDictionary } from "@/lib/i18n/get-dictionary";
import { createServerTranslator } from "@/lib/i18n/translate";
import type { Locale } from "@/lib/i18n/locales";

type CompletenessScoreCardProps = {
  score: CompletenessScoreData;
  locale: Locale;
};

function getScoreTone(score: number): string {
  if (score >= 80) {
    return "text-primary";
  }
  if (score >= 50) {
    return "text-amber-600 dark:text-amber-400";
  }
  return "text-muted-foreground";
}

export async function CompletenessScoreCard({
  score,
  locale,
}: CompletenessScoreCardProps) {
  const dictionary = await getDictionary(locale);
  const t = createServerTranslator(dictionary);
  const formatRinggit = getCurrencyFormatter(locale);

  const claimedTotal = Number(score.total_claimed);
  const savingsTotal = Number(score.estimated_savings);

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle>{t("completeness", "title")}</CardTitle>
        <CardDescription>
          {t("completeness", "subtitle", { year: score.tax_year })}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className={`text-4xl font-semibold tabular-nums ${getScoreTone(score.score)}`}>
              {score.score}%
            </p>
            <p className="text-sm text-muted-foreground">
              {t("completeness", "categoriesTracked", {
                tracked: score.categories_with_claims,
                total: score.total_categories,
              })}
            </p>
          </div>
          <div className="text-right text-sm">
            <p className="text-muted-foreground">{t("completeness", "totalClaimed")}</p>
            <p className="font-medium tabular-nums">
              {formatRinggit.format(claimedTotal)}
            </p>
            <p className="mt-1 text-muted-foreground">
              {t("completeness", "estimatedSavings")}
            </p>
            <p className="font-medium tabular-nums">
              {formatRinggit.format(savingsTotal)}
            </p>
          </div>
        </div>

        <div className="h-2 overflow-hidden rounded-full bg-muted">
          <div
            className="h-full rounded-full bg-primary transition-all"
            style={{ width: `${Math.min(100, Math.max(0, score.score))}%` }}
          />
        </div>

        {score.milestone_message ? (
          <p className="rounded-md border bg-muted/40 px-3 py-2 text-sm">
            {score.milestone_message}
          </p>
        ) : null}
      </CardContent>
    </Card>
  );
}
