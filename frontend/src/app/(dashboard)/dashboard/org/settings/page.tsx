import { OrgPolicyForm } from "@/components/org/org-policy-form";
import { fetchReliefCategories } from "@/lib/api/admin-system";
import {
  loadOrgPageContext,
  requireOrgSuperadmin,
} from "@/lib/org/page-context";
import { buildCategoryLabelMap, mergeCategoryLabels } from "@/lib/receipt-categories";

export const metadata = {
  title: "Org Settings",
};

export default async function OrgSettingsPage() {
  const context = requireOrgSuperadmin(
    await loadOrgPageContext("/dashboard/org/settings"),
  );

  const categoriesResult = await fetchReliefCategories();
  const reliefCategories = categoriesResult.body.success
    ? categoriesResult.body.data
    : [];
  const categoryLabels = mergeCategoryLabels(
    buildCategoryLabelMap(reliefCategories),
  );

  return (
    <div className="space-y-4">
      <div className="space-y-1">
        <h2 className="text-lg font-semibold">Organization settings</h2>
        <p className="text-sm text-muted-foreground">
          Configure policy rules for all employees.
        </p>
      </div>
      <OrgPolicyForm
        policy={context.org.policy}
        availableCategories={reliefCategories}
        categoryLabels={categoryLabels}
      />
    </div>
  );
}
