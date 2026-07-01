import { OrgOverviewSection } from "@/components/org/org-overview-section";
import { OrgRegisterForm } from "@/components/org/org-register-form";
import { fetchReliefCategories } from "@/lib/api/admin-system";
import { loadOrgPageContext } from "@/lib/org/page-context";
import { buildCategoryLabelMap, mergeCategoryLabels } from "@/lib/receipt-categories";

export const metadata = {
  title: "Organization",
};

export default async function OrgOverviewPage() {
  const context = await loadOrgPageContext("/dashboard/org");

  if (context.kind === "register") {
    return (
      <div className="space-y-4">
        <header className="space-y-1">
          <h1 className="text-2xl font-semibold tracking-tight">Organization</h1>
          <p className="text-sm text-muted-foreground">
            Register your company to start managing employees.
          </p>
        </header>
        <OrgRegisterForm userEmail={context.user.email} />
      </div>
    );
  }

  const categoriesResult = await fetchReliefCategories();
  const reliefCategories = categoriesResult.body.success
    ? categoriesResult.body.data
    : [];
  const categoryLabels = mergeCategoryLabels(
    buildCategoryLabelMap(reliefCategories),
  );

  return <OrgOverviewSection org={context.org} categoryLabels={categoryLabels} />;
}
