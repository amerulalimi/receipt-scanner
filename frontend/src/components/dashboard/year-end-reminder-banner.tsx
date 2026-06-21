import { AlertTriangleIcon } from "lucide-react";

import {
  formatDeadlineDate,
  getYearEndReminderInfo,
} from "@/lib/tax-year";
import { getDictionary } from "@/lib/i18n/get-dictionary";
import { createServerTranslator } from "@/lib/i18n/translate";
import type { Locale } from "@/lib/i18n/locales";

type YearEndReminderBannerProps = {
  taxYear: number;
  locale: Locale;
};

export async function YearEndReminderBanner({
  taxYear,
  locale,
}: YearEndReminderBannerProps) {
  const { show, deadline } = getYearEndReminderInfo(taxYear);

  if (!show) {
    return null;
  }

  const dictionary = await getDictionary(locale);
  const t = createServerTranslator(dictionary);
  const deadlineLabel = formatDeadlineDate(deadline, locale);

  return (
    <div
      role="status"
      className="flex gap-3 rounded-lg border border-amber-500/40 bg-amber-500/10 px-4 py-3 text-sm text-amber-950 dark:text-amber-100"
    >
      <AlertTriangleIcon className="mt-0.5 size-4 shrink-0 text-amber-600 dark:text-amber-400" />
      <p>
        {t("dashboard", "yearEndReminder", {
          year: taxYear,
          deadline: deadlineLabel,
        })}
      </p>
    </div>
  );
}
