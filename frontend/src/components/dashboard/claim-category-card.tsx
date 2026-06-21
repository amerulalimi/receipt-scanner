import { getCurrencyFormatter, getDictionary } from "@/lib/i18n/get-dictionary";
import { createServerTranslator } from "@/lib/i18n/translate";
import type { Locale } from "@/lib/i18n/locales";
import { cn } from "@/lib/utils";
import { getCategoryLabel } from "@/lib/constants/receipts";
import type { ClaimCategorySummary } from "@/lib/api/types";

type ClaimCategoryCardProps = {
  category: ClaimCategorySummary;
  categoryLabels: Record<string, string>;
  locale: Locale;
};

const WARNING_THRESHOLD = 80;

function getProgressTone(category: ClaimCategorySummary): string {
  if (category.status === "full" || category.percentage >= 100) {
    return "bg-destructive";
  }
  if (category.status === "warning" || category.percentage >= WARNING_THRESHOLD) {
    return "bg-amber-500";
  }
  return "bg-primary";
}

export async function ClaimCategoryCard({
  category,
  categoryLabels,
  locale,
}: ClaimCategoryCardProps) {
  const dictionary = await getDictionary(locale);
  const t = createServerTranslator(dictionary);
  const formatRinggit = getCurrencyFormatter(locale);

  const progressWidth = Math.min(category.percentage, 100);
  const showWarning =
    category.status === "warning" ||
    category.status === "full" ||
    category.percentage >= WARNING_THRESHOLD;

  return (
    <article className="rounded-xl border bg-card p-4 shadow-sm ring-1 ring-foreground/5">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="font-medium text-foreground">
            {getCategoryLabel(category.category, categoryLabels)}
          </h3>
          {category.be_seksyen ? (
            <p className="mt-0.5 text-xs text-muted-foreground">
              {category.be_seksyen}
            </p>
          ) : null}
        </div>
        {showWarning ? (
          <span
            className={cn(
              "rounded-full px-2 py-0.5 text-xs font-medium",
              category.status === "full"
                ? "bg-destructive/10 text-destructive"
                : "bg-amber-500/10 text-amber-700 dark:text-amber-400",
            )}
          >
            {category.status === "full"
              ? t("dashboard", "statusFull")
              : t("dashboard", "statusAlmostFull")}
          </span>
        ) : null}
      </div>

      <div className="mt-4 space-y-2">
        <div className="flex items-end justify-between text-sm">
          <span className="text-muted-foreground">
            {t("dashboard", "claimed")}
          </span>
          <span className="font-medium tabular-nums">
            {formatRinggit.format(category.claimed)}{" "}
            <span className="font-normal text-muted-foreground">
              / {formatRinggit.format(category.limit)}
            </span>
          </span>
        </div>

        <div
          className="h-2 overflow-hidden rounded-full bg-muted"
          role="progressbar"
          aria-valuenow={progressWidth}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label={`${getCategoryLabel(category.category, categoryLabels)} — ${category.percentage.toFixed(0)}%`}
        >
          <div
            className={cn("h-full rounded-full transition-all", getProgressTone(category))}
            style={{ width: `${progressWidth}%` }}
          />
        </div>

        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <span>
            {t("dashboard", "remaining", {
              amount: formatRinggit.format(category.remaining),
            })}
          </span>
          <span>
            {category.percentage.toFixed(0)}% ·{" "}
            {t("dashboard", "receiptCount", { count: category.receipt_count })}
          </span>
        </div>
      </div>
    </article>
  );
}
