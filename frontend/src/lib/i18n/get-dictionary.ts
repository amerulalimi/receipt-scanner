import "server-only";

import { defaultLocale, type Locale } from "@/lib/i18n/locales";
import type { Dictionary } from "@/lib/i18n/types";

export async function getLocale(): Promise<Locale> {
  return defaultLocale;
}

export async function getDictionary(_locale?: Locale): Promise<Dictionary> {
  const module = await import("@/messages/en.json");
  return module.default;
}

export function getCurrencyFormatter(_locale?: Locale): Intl.NumberFormat {
  return new Intl.NumberFormat("en-MY", {
    style: "currency",
    currency: "MYR",
    minimumFractionDigits: 2,
  });
}
