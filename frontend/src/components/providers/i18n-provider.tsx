"use client";

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  type ReactNode,
} from "react";

import type { Locale } from "@/lib/i18n/locales";
import { translate } from "@/lib/i18n/translate";
import type {
  Dictionary,
  DictionaryNamespaceName,
} from "@/lib/i18n/types";

type I18nContextValue = {
  locale: Locale;
  dictionary: Dictionary;
};

const I18nContext = createContext<I18nContextValue | null>(null);

export function I18nProvider({
  locale,
  dictionary,
  children,
}: {
  locale: Locale;
  dictionary: Dictionary;
  children: ReactNode;
}) {
  const value = useMemo(
    () => ({
      locale,
      dictionary,
    }),
    [locale, dictionary],
  );

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n() {
  const context = useContext(I18nContext);

  if (!context) {
    throw new Error("useI18n must be used within I18nProvider");
  }

  return context;
}

export function useTranslations(namespace: DictionaryNamespaceName) {
  const { dictionary } = useI18n();

  return useCallback(
    (key: string, params?: Record<string, string | number>) =>
      translate(dictionary, namespace, key, params),
    [dictionary, namespace],
  );
}

export function useLocale() {
  return useI18n().locale;
}
