import type { Locale } from "@/lib/i18n/locales";

export const TAX_YEAR_MIN = 2000;
export const TAX_YEAR_MAX = 2100;
export const TAX_YEAR_RANGE_BACK = 5;
export const TAX_YEAR_RANGE_FORWARD = 1;

export function getCurrentCalendarYear(): number {
  return new Date().getFullYear();
}

export function getTaxYearOptions(anchorYear?: number): number[] {
  const current = getCurrentCalendarYear();
  const center = anchorYear ?? current;
  const start = Math.min(center, current) - TAX_YEAR_RANGE_BACK;
  const end = Math.max(center, current) + TAX_YEAR_RANGE_FORWARD;
  const years: number[] = [];

  for (let year = end; year >= start; year -= 1) {
    if (year >= TAX_YEAR_MIN && year <= TAX_YEAR_MAX) {
      years.push(year);
    }
  }

  return years;
}

export function resolveTaxYear(
  value: number | null | undefined,
  fallback: number,
): number {
  if (
    typeof value === "number" &&
    value >= TAX_YEAR_MIN &&
    value <= TAX_YEAR_MAX
  ) {
    return value;
  }

  return fallback;
}

export type YearEndReminderInfo = {
  show: boolean;
  deadline: Date;
};

/** Show reminder from 1 Dec (tax year) until 28 Feb (following year). */
export function getYearEndReminderInfo(
  taxYear: number,
  now: Date = new Date(),
): YearEndReminderInfo {
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const reminderStart = new Date(taxYear, 11, 1);
  const deadline = new Date(taxYear + 1, 1, 28);

  return {
    show: today >= reminderStart && today <= deadline,
    deadline,
  };
}

export function formatDeadlineDate(date: Date, locale?: Locale): string {
  const resolvedLocale = locale === "en" ? "en-MY" : "ms-MY";

  return new Intl.DateTimeFormat(resolvedLocale, {
    day: "numeric",
    month: "long",
    year: "numeric",
  }).format(date);
}
