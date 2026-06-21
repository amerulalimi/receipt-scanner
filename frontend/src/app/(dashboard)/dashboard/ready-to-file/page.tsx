import { DashboardError } from "@/components/dashboard/dashboard-error";
import { ReadyToFileContent } from "@/components/ready-to-file/ready-to-file-content";
import { fetchReadyToFile } from "@/lib/api/claims";
import { fetchReliefCategories } from "@/lib/api/admin-system";
import { getMeWithFastApi } from "@/lib/api/auth-me";
import { redirectAfterSessionExpired } from "@/lib/auth/session-expired-redirect";
import { getDictionary, getLocale } from "@/lib/i18n/get-dictionary";
import { createServerTranslator } from "@/lib/i18n/translate";
import type { ApiErrorResponse } from "@/lib/api/types";
import {
  buildCategoryLabelMap,
  mergeCategoryLabels,
} from "@/lib/receipt-categories";
import { resolveTaxYear } from "@/lib/tax-year";
import { parseDashboardReceiptHistorySearchParams } from "@/lib/validations/receipt";

export async function generateMetadata() {
  const locale = await getLocale();
  const dictionary = await getDictionary(locale);
  const t = createServerTranslator(dictionary);

  return {
    title: t("readyToFile", "title"),
  };
}

function isUnauthorized(
  status: number,
  body: unknown,
): body is ApiErrorResponse {
  return (
    status === 401 ||
    (typeof body === "object" &&
      body !== null &&
      "success" in body &&
      (body as ApiErrorResponse).success === false &&
      (body as ApiErrorResponse).code === "UNAUTHORIZED")
  );
}

export default async function ReadyToFilePage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const rawParams = await searchParams;
  const parsedHistory = parseDashboardReceiptHistorySearchParams(rawParams);
  const locale = await getLocale();
  const dictionary = await getDictionary(locale);
  const t = createServerTranslator(dictionary);

  let meResult;
  try {
    meResult = await getMeWithFastApi();
  } catch {
    return (
      <DashboardError message={t("dashboard", "apiUnavailable")} />
    );
  }

  if (!meResult.body.success || meResult.response.status >= 400) {
    redirectAfterSessionExpired("/dashboard/ready-to-file");
  }

  const defaultTaxYear = meResult.body.data.tax_year;
  const selectedTaxYear = resolveTaxYear(
    parsedHistory.success ? parsedHistory.data.tax_year : undefined,
    defaultTaxYear,
  );

  let readyResult;
  let categoriesResult;

  try {
    [readyResult, categoriesResult] = await Promise.all([
      fetchReadyToFile(selectedTaxYear),
      fetchReliefCategories(),
    ]);
  } catch {
    return (
      <DashboardError message={t("dashboard", "apiUnavailable")} />
    );
  }

  if (isUnauthorized(readyResult.response.status, readyResult.body)) {
    redirectAfterSessionExpired("/dashboard/ready-to-file");
  }

  if (!readyResult.body.success || readyResult.response.status >= 400) {
    const errorMessage =
      "message" in readyResult.body && typeof readyResult.body.message === "string"
        ? readyResult.body.message
        : t("readyToFile", "loadError");

    return <DashboardError message={errorMessage} />;
  }

  const reliefCategories = categoriesResult.body.success
    ? categoriesResult.body.data
    : [];
  const categoryLabels = mergeCategoryLabels(
    buildCategoryLabelMap(reliefCategories),
  );

  return (
    <main className="w-full py-8">
      <ReadyToFileContent
        data={readyResult.body.data}
        categoryLabels={categoryLabels}
        locale={locale}
      />
    </main>
  );
}
