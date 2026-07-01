import "server-only";

import { redirect } from "next/navigation";

import { fetchOrgMe } from "@/lib/api/org";
import { fetchReliefCategories } from "@/lib/api/admin-system";
import type { ApiErrorResponse, OrgMeData } from "@/lib/api/types";
import { requireAuth } from "@/lib/auth/require-auth";
import { canAccessOrgFeatures } from "@/lib/auth/account-access";
import { redirectAfterSessionExpired } from "@/lib/auth/session-expired-redirect";
import { buildCategoryLabelMap, mergeCategoryLabels } from "@/lib/receipt-categories";

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

export type OrgPageContext =
  | {
      kind: "register";
      user: Awaited<ReturnType<typeof requireAuth>>;
    }
  | {
      kind: "org";
      user: Awaited<ReturnType<typeof requireAuth>>;
      org: OrgMeData;
      categoryLabels: Record<string, string>;
      isOrgAdmin: boolean;
      isOrgSuperadmin: boolean;
    };

export async function loadOrgPageContext(
  returnPath: string,
): Promise<OrgPageContext> {
  const user = await requireAuth(returnPath);

  if (!canAccessOrgFeatures(user)) {
    redirect("/dashboard");
  }

  let orgResult;
  let categoriesResult;

  try {
    [orgResult, categoriesResult] = await Promise.all([
      fetchOrgMe(),
      fetchReliefCategories(),
    ]);
  } catch {
    throw new Error("API_UNAVAILABLE");
  }

  const { response, body } = orgResult;

  if (isUnauthorized(response.status, body)) {
    redirectAfterSessionExpired(returnPath);
  }

  const canRegisterOrg =
    user.account_type === "corporate" &&
    user.org_id === null &&
    user.active_role === "individual";

  if (!body.success && response.status === 404 && canRegisterOrg) {
    return { kind: "register", user };
  }

  if (!body.success) {
    throw new Error(
      (body as ApiErrorResponse).message ?? "Organization not found.",
    );
  }

  const reliefCategories = categoriesResult.body.success
    ? categoriesResult.body.data
    : [];

  return {
    kind: "org",
    user,
    org: body.data,
    categoryLabels: mergeCategoryLabels(buildCategoryLabelMap(reliefCategories)),
    isOrgAdmin: user.active_role === "hr_admin" || user.active_role === "superadmin",
    isOrgSuperadmin: user.active_role === "superadmin",
  };
}

export function requireOrgAdmin(context: OrgPageContext) {
  if (context.kind !== "org" || !context.isOrgAdmin) {
    redirect("/dashboard/org");
  }
  return context;
}

export function requireOrgSuperadmin(context: OrgPageContext) {
  if (context.kind !== "org" || !context.isOrgSuperadmin) {
    redirect("/dashboard/org");
  }
  return context;
}
