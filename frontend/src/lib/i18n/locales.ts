export const locales = ["ms", "en"] as const;

export type Locale = (typeof locales)[number];

export const defaultLocale: Locale = "ms";

export function isLocale(value: string): value is Locale {
  return locales.includes(value as Locale);
}
