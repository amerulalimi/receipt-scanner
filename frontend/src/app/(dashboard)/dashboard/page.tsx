import { ClaimCompareSection } from "@/components/dashboard/claim-compare-section";
import { ClaimSummarySection } from "@/components/dashboard/claim-summary-section";
import { CompletenessScoreCard } from "@/components/dashboard/completeness-score-card";
import { DashboardError } from "@/components/dashboard/dashboard-error";
import { DashboardYearFilter } from "@/components/dashboard/dashboard-year-filter";
import { EmailVerificationBanner } from "@/components/dashboard/email-verification-banner";
import { ReceiptHistorySection } from "@/components/dashboard/receipt-history-section";
import { SmartRemindersPanel } from "@/components/dashboard/smart-reminders-panel";
import { YearEndReminderBanner } from "@/components/dashboard/year-end-reminder-banner";
import { QrUploadSession } from "@/components/receipts/qr-upload-session";
import { ReceiptUploadForm } from "@/components/receipts/receipt-upload-form";
import { fetchClaimComparison, fetchClaimSummary, fetchCompletenessScore } from "@/lib/api/claims";
import { fetchNotifications } from "@/lib/api/notifications";
import { fetchReliefCategories } from "@/lib/api/admin-system";
import { getMeWithFastApi } from "@/lib/api/auth-me";
import { fetchRecentReceipts } from "@/lib/api/receipts";
import { redirectAfterSessionExpired } from "@/lib/auth/session-expired-redirect";
import { getDictionary, getLocale } from "@/lib/i18n/get-dictionary";
import { createServerTranslator } from "@/lib/i18n/translate";
import type { ApiErrorResponse } from "@/lib/api/types";
import { resolveTaxYear } from "@/lib/tax-year";
import {
  mergeCategoryLabels,
  buildCategoryLabelMap,
} from "@/lib/receipt-categories";
import { parseDashboardReceiptHistorySearchParams } from "@/lib/validations/receipt";

export const metadata = {
  title: "Dashboard",
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

export default async function DashboardPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const rawParams = await searchParams;
  const parsedHistory = parseDashboardReceiptHistorySearchParams(rawParams);
  const historyLimit = parsedHistory.success
    ? parsedHistory.data.history_limit
    : 10;

  const locale = await getLocale();
  const dictionary = await getDictionary(locale);
  const t = createServerTranslator(dictionary);

  let summaryResult;
  let comparisonResult;
  let completenessResult;
  let notificationsResult;
  let receiptsResult;
  let meResult;
  let categoriesResult;

  try {
    meResult = await getMeWithFastApi();
  } catch {
    return (
      <DashboardError message={t("dashboard", "apiUnavailable")} />
    );
  }

  if (!meResult.body.success || meResult.response.status >= 400) {
    redirectAfterSessionExpired("/dashboard");
  }

  const defaultTaxYear = meResult.body.data.tax_year;
  const selectedTaxYear = resolveTaxYear(
    parsedHistory.success ? parsedHistory.data.tax_year : undefined,
    defaultTaxYear,
  );

  try {
    [summaryResult, comparisonResult, completenessResult, notificationsResult, receiptsResult, categoriesResult] =
      await Promise.all([
        fetchClaimSummary(selectedTaxYear),
        fetchClaimComparison(selectedTaxYear),
        fetchCompletenessScore(selectedTaxYear),
        fetchNotifications(),
        fetchRecentReceipts(historyLimit, selectedTaxYear),
        fetchReliefCategories(),
      ]);
  } catch {
    return (
      <DashboardError message={t("dashboard", "apiUnavailable")} />
    );
  }

  const { response, body } = summaryResult;

  if (isUnauthorized(response.status, body)) {
    redirectAfterSessionExpired("/dashboard");
  }

  if (!body.success || response.status >= 400) {
    const errorMessage =
      "message" in body && typeof body.message === "string"
        ? body.message
        : response.status === 404
          ? t("dashboard", "claimsNotFound")
          : t("dashboard", "claimsLoadError");

    return <DashboardError message={errorMessage} />;
  }

  const receiptsData =
    receiptsResult.body.success && receiptsResult.response.status < 400
      ? receiptsResult.body.data
      : { items: [], total: 0, page: 1, limit: historyLimit };

  const reliefCategories = categoriesResult.body.success
    ? categoriesResult.body.data
    : [];
  const categoryLabels = mergeCategoryLabels(
    buildCategoryLabelMap(reliefCategories),
  );

  const comparisonData =
    comparisonResult.body.success && comparisonResult.response.status < 400
      ? comparisonResult.body.data
      : null;

  const completenessData =
    completenessResult.body.success && completenessResult.response.status < 400
      ? completenessResult.body.data
      : null;

  const notificationsData =
    notificationsResult.body.success &&
    notificationsResult.response.status < 400
      ? notificationsResult.body.data.items
      : [];

  return (
    <main className="w-full space-y-8 py-8">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div className="space-y-1">
          <h1 className="text-2xl font-semibold tracking-tight">
            {t("dashboard", "title")}
          </h1>
          <p className="text-sm text-muted-foreground">
            {t("dashboard", "subtitle", { year: selectedTaxYear })}
          </p>
        </div>
        <DashboardYearFilter
          defaultYear={defaultTaxYear}
          label={t("dashboard", "taxYear")}
        />
      </header>

      {!meResult.body.data.email_verified ? (
        <EmailVerificationBanner email={meResult.body.data.email} />
      ) : null}

      <YearEndReminderBanner taxYear={selectedTaxYear} locale={locale} />

      <SmartRemindersPanel
        notifications={notificationsData}
        locale={locale}
      />

      {completenessData ? (
        <CompletenessScoreCard score={completenessData} locale={locale} />
      ) : null}

      <ClaimSummarySection
        summary={body.data}
        categoryLabels={categoryLabels}
        locale={locale}
      />

      {comparisonData ? (
        <ClaimCompareSection
          comparison={comparisonData}
          categoryLabels={categoryLabels}
          locale={locale}
        />
      ) : null}

      <ReceiptHistorySection
        receipts={receiptsData}
        historyLimit={historyLimit}
        categoryLabels={categoryLabels}
        taxYear={selectedTaxYear}
        locale={locale}
      />

      <div className="grid gap-6 lg:grid-cols-2">
        <ReceiptUploadForm defaultTaxYear={selectedTaxYear} />
        <QrUploadSession selectedTaxYear={selectedTaxYear} />
      </div>
    </main>
  );
}
