import { DashboardError } from "@/components/dashboard/dashboard-error";
import { ExportReceiptsButton } from "@/components/receipts/export-receipts-button";
import { ReceiptUploadActions } from "@/components/receipts/receipt-upload-actions";
import { ManualReceiptForm } from "@/components/receipts/manual-receipt-form";
import { ReceiptsFilters } from "@/components/receipts/receipts-filters";
import { ReceiptsListSection } from "@/components/receipts/receipts-list-section";
import { ReceiptsPagination } from "@/components/receipts/receipts-pagination";
import { fetchReceipts } from "@/lib/api/receipts";
import { fetchReliefCategories } from "@/lib/api/admin-system";
import { getMeWithFastApi } from "@/lib/api/auth-me";
import { redirectAfterSessionExpired } from "@/lib/auth/session-expired-redirect";
import {
  buildCategoryLabelMap,
  getCategoryOptions,
  mergeCategoryLabels,
} from "@/lib/receipt-categories";
import { getDictionary, getLocale } from "@/lib/i18n/get-dictionary";
import { createServerTranslator } from "@/lib/i18n/translate";
import type { ApiErrorResponse } from "@/lib/api/types";
import { parseReceiptListSearchParams } from "@/lib/validations/receipt";

export const metadata = {
  title: "Receipts",
};

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

type ReceiptsPageProps = {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
};

export default async function ReceiptsPage({ searchParams }: ReceiptsPageProps) {
  const rawParams = await searchParams;
  const parsedFilters = parseReceiptListSearchParams(rawParams);
  const locale = await getLocale();
  const dictionary = await getDictionary(locale);
  const t = createServerTranslator(dictionary);

  if (!parsedFilters.success) {
    return (
      <DashboardError message={t("receipts", "invalidFilters")} />
    );
  }

  let meResult;
  try {
    meResult = await getMeWithFastApi();
  } catch {
    return <DashboardError message={t("dashboard", "apiUnavailable")} />;
  }

  if (!meResult.body.success || meResult.response.status >= 400) {
    redirectAfterSessionExpired("/dashboard/receipts");
  }

  const defaultTaxYear = meResult.body.data.tax_year;

  let receiptsResult;
  let categoriesResult;

  try {
    [receiptsResult, categoriesResult] = await Promise.all([
      fetchReceipts(parsedFilters.data),
      fetchReliefCategories(),
    ]);
  } catch {
    return (
      <DashboardError message={t("dashboard", "apiUnavailable")} />
    );
  }

  const { response, body } = receiptsResult;

  if (isUnauthorized(response.status, body)) {
    redirectAfterSessionExpired("/dashboard/receipts");
  }

  if (!body.success || response.status >= 400) {
    const errorMessage =
      "message" in body && typeof body.message === "string"
        ? body.message
        : t("receipts", "loadError");

    return <DashboardError message={errorMessage} />;
  }

  const reliefCategories = categoriesResult.body.success
    ? categoriesResult.body.data
    : [];
  const categoryLabels = mergeCategoryLabels(
    buildCategoryLabelMap(reliefCategories),
  );
  const categoryOptions = getCategoryOptions(reliefCategories).map((item) => ({
    value: item.category,
    label: categoryLabels[item.category] ?? item.label,
  }));

  const selectedTaxYear = parsedFilters.data.tax_year ?? defaultTaxYear;

  return (
    <main className="w-full space-y-6 py-8">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div className="space-y-1">
          <h1 className="text-2xl font-semibold tracking-tight">
            {t("receipts", "title")}
          </h1>
          <p className="text-sm text-muted-foreground">
            {t("receipts", "subtitle")}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <ExportReceiptsButton taxYear={selectedTaxYear} />
          <ReceiptUploadActions defaultTaxYear={selectedTaxYear} />
        </div>
      </header>

      <ManualReceiptForm
        defaultTaxYear={defaultTaxYear}
        categoryOptions={categoryOptions}
      />

      <ReceiptsFilters
        categoryOptions={categoryOptions}
        defaultTaxYear={defaultTaxYear}
      />

      <ReceiptsListSection
        receipts={body.data}
        categoryLabels={categoryLabels}
        categoryOptions={categoryOptions}
        locale={locale}
      />

      <ReceiptsPagination
        total={body.data.total}
        page={body.data.page}
        limit={body.data.limit}
      />
    </main>
  );
}
