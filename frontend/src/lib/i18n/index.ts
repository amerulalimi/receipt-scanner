import type { Locale } from "./locales";

type Dictionary = Record<string, unknown>;

export async function getDictionary(locale: Locale): Promise<Dictionary> {
  void locale;
  // Phase 0 shell — load from dictionaries/ in a later phase
  return {};
}
