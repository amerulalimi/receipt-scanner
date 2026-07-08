import "server-only";

import { defaultLocale, type Locale } from "@/lib/i18n/locales";
import type { Dictionary } from "@/lib/i18n/types";

const dictionaryLoaders: Record<Locale, () => Promise<{ default: Partial<Dictionary> }>> = {
  ms: () => import("@/lib/i18n/dictionaries/ms.json"),
  en: () => import("@/lib/i18n/dictionaries/en.json"),
};

export async function getLocale(): Promise<Locale> {
  return defaultLocale;
}

export async function getDictionary(locale?: Locale): Promise<Dictionary> {
  const resolved = locale ?? defaultLocale;
  const [dictionaryModule, legacyModule] = await Promise.all([
    dictionaryLoaders[resolved](),
    import("@/messages/en.json"),
  ]);

  return {
    ...legacyModule.default,
    ...dictionaryModule.default,
    auth: {
      ...legacyModule.default.auth,
      ...dictionaryModule.default.auth,
    },
    common: {
      ...legacyModule.default.common,
      ...dictionaryModule.default.common,
    },
  } as Dictionary;
}

export function getCurrencyFormatter(locale?: Locale): Intl.NumberFormat {
  const resolvedLocale = locale === "en" ? "en-MY" : "ms-MY";

  return new Intl.NumberFormat(resolvedLocale, {
    style: "currency",
    currency: "MYR",
    minimumFractionDigits: 2,
  });
}
