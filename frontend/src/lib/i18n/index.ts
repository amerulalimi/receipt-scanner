import type { Locale } from "./locales";

type Dictionary = Record<string, unknown>;

export async function getDictionary(_locale: Locale): Promise<Dictionary> {
  // Phase 0 shell — load from dictionaries/ in a later phase
  return {};
}
