import type { DictionaryNamespaceName } from "@/lib/i18n/types";
import type { Dictionary } from "@/lib/i18n/types";

export function translate(
  dictionary: Dictionary,
  namespace: DictionaryNamespaceName,
  key: string,
  params?: Record<string, string | number>,
): string {
  const template = dictionary[namespace][key] ?? key;

  if (!params) {
    return template;
  }

  return Object.entries(params).reduce(
    (result, [paramKey, paramValue]) =>
      result.replaceAll(`{${paramKey}}`, String(paramValue)),
    template,
  );
}

export function createServerTranslator(dictionary: Dictionary) {
  return (
    namespace: DictionaryNamespaceName,
    key: string,
    params?: Record<string, string | number>,
  ) => translate(dictionary, namespace, key, params);
}
