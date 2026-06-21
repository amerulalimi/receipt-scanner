import { DashboardError } from "@/components/dashboard/dashboard-error";
import { HouseholdContent } from "@/components/household/household-content";
import { fetchHouseholdOverview } from "@/lib/api/household";
import { fetchReliefCategories } from "@/lib/api/admin-system";
import { requireAuth } from "@/lib/auth/require-auth";
import { redirectAfterSessionExpired } from "@/lib/auth/session-expired-redirect";
import {
  buildCategoryLabelMap,
  mergeCategoryLabels,
} from "@/lib/receipt-categories";
import { getDictionary, getLocale } from "@/lib/i18n/get-dictionary";
import { createServerTranslator } from "@/lib/i18n/translate";
import type { ApiErrorResponse } from "@/lib/api/types";
import { redirect } from "next/navigation";

export async function generateMetadata() {
  const dictionary = await getDictionary(await getLocale());
  return {
    title: dictionary.household.title,
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

export default async function HouseholdPage() {
  const locale = await getLocale();
  const dictionary = await getDictionary(locale);
  const t = createServerTranslator(dictionary);
  const user = await requireAuth("/dashboard/household");

  if (user.account_type !== "individual") {
    redirect("/dashboard");
  }

  let householdResult;
  let categoriesResult;

  try {
    [householdResult, categoriesResult] = await Promise.all([
      fetchHouseholdOverview(),
      fetchReliefCategories(),
    ]);
  } catch {
    return <DashboardError message={t("dashboard", "apiUnavailable")} />;
  }

  const { response, body } = householdResult;

  if (isUnauthorized(response.status, body)) {
    redirectAfterSessionExpired("/dashboard/household");
  }

  if (!body.success || response.status >= 400) {
    const errorMessage =
      "message" in body && typeof body.message === "string"
        ? body.message
        : t("household", "loadError");

    return <DashboardError message={errorMessage} />;
  }

  const reliefCategories = categoriesResult.body.success
    ? categoriesResult.body.data
    : [];
  const categoryLabels = mergeCategoryLabels(
    buildCategoryLabelMap(reliefCategories),
  );

  return (
    <main className="w-full space-y-6 py-8">
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold tracking-tight">
          {t("household", "title")}
        </h1>
        <p className="text-sm text-muted-foreground">
          {t("household", "subtitle")}
        </p>
      </header>

      <HouseholdContent
        household={body.data}
        currentUserId={user.user_id}
        categoryLabels={categoryLabels}
      />
    </main>
  );
}
