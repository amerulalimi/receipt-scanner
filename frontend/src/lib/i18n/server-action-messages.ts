import "server-only";

import { getDictionary, getLocale } from "@/lib/i18n/get-dictionary";
import { createServerTranslator } from "@/lib/i18n/translate";

export async function getActionMessage(
  namespace: "errors" | "settings" | "auth" | "dashboard",
  key: string,
) {
  const dictionary = await getDictionary(await getLocale());
  const t = createServerTranslator(dictionary);
  return t(namespace, key);
}
