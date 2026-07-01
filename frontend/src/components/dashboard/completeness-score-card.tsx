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
import { cn } from "@/lib/utils";

type CompletenessScoreCardProps = {
  score: CompletenessScoreData;
  locale: Locale;
};

const CRITERION_LABELS: Record<string, { en: string; ms: string }> = {
  approved_receipt: {
    en: "At least 1 approved receipt",
    ms: "Sekurang-kurangnya 1 resit diluluskan",
  },
  multi_category: {
    en: "Claims in 3+ categories",
    ms: "Tuntutan dalam 3+ kategori",
  },
  total_claimed_1000: {
    en: "Total claimed over RM1,000",
    ms: "Jumlah tuntutan melebihi RM1,000",
  },
  category_utilization_50: {
    en: "Any category at 50%+ of limit",
    ms: "Mana-mana kategori ≥50% had",
  },
  profile_complete: {
    en: "Profile complete (name + tax bracket)",
    ms: "Profil lengkap (nama + kadar cukai)",
  },
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
  const breakdown = score.breakdown ?? [];

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
              {score.score}/100
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

        {score.next_action ? (
          <p className="text-sm text-muted-foreground">
            <span className="font-medium text-foreground">
              {t("completeness", "nextAction")}:
            </span>{" "}
            {score.next_action}
          </p>
        ) : null}

        {breakdown.length > 0 ? (
          <div className="space-y-2">
            <p className="text-sm font-medium">{t("completeness", "breakdownTitle")}</p>
            <ul className="space-y-2">
              {breakdown.map((item) => {
                const label =
                  CRITERION_LABELS[item.criterion]?.[locale] ??
                  item.criterion;
                return (
                  <li
                    key={item.criterion}
                    className="flex items-center justify-between gap-3 rounded-md border px-3 py-2 text-sm"
                  >
                    <span className={cn(!item.achieved && "text-muted-foreground")}>
                      {label}
                    </span>
                    <span
                      className={cn(
                        "rounded-full px-2 py-0.5 text-xs font-medium",
                        item.achieved
                          ? "bg-primary/10 text-primary"
                          : "bg-muted text-muted-foreground",
                      )}
                    >
                      {item.achieved
                        ? t("completeness", "criterionAchieved", {
                            points: item.points,
                          })
                        : t("completeness", "criterionPending")}
                    </span>
                  </li>
                );
              })}
            </ul>
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}
