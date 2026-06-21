import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { OrgMeData } from "@/lib/api/types";
import { getCategoryLabel } from "@/lib/constants/receipts";

const ROLE_LABELS: Record<string, string> = {
  superadmin: "Superadmin",
  hr_admin: "HR Admin",
  employee: "Employee",
};

export function OrgOverviewSection({
  org,
  categoryLabels,
}: {
  org: OrgMeData;
  categoryLabels: Record<string, string>;
}) {
  return (
    <Card>
      <CardHeader>
        <div className="flex flex-wrap items-start justify-between gap-2">
          <div>
            <CardTitle>{org.name}</CardTitle>
            <CardDescription>
              SSM {org.ssm_number} · @{org.email_domain}
            </CardDescription>
          </div>
          <span
            className={
              org.domain_verified
                ? "rounded-full bg-primary/10 px-2.5 py-0.5 text-xs font-medium text-primary"
                : "rounded-full bg-muted px-2.5 py-0.5 text-xs font-medium text-muted-foreground"
            }
          >
            {org.domain_verified ? "Domain verified" : "Domain not verified"}
          </span>
        </div>
      </CardHeader>
      <CardContent className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div>
          <p className="text-sm text-muted-foreground">Total employees</p>
          <p className="text-2xl font-semibold">{org.total_employees}</p>
        </div>
        <div>
          <p className="text-sm text-muted-foreground">Tax year</p>
          <p className="text-2xl font-semibold">{org.policy.tax_year}</p>
        </div>
        <div>
          <p className="text-sm text-muted-foreground">Receipt limit/month</p>
          <p className="text-2xl font-semibold">
            {org.policy.max_receipts_per_month}
          </p>
        </div>
        <div>
          <p className="text-sm text-muted-foreground">HR approval</p>
          <p className="text-2xl font-semibold">
            {org.policy.require_hr_approval ? "Yes" : "No"}
          </p>
        </div>
        <div className="sm:col-span-2 lg:col-span-4">
          <p className="text-sm text-muted-foreground">Allowed categories</p>
          <div className="mt-2 flex flex-wrap gap-2">
            {org.policy.allowed_categories.map((category) => (
              <span
                key={category}
                className="rounded-full border px-2.5 py-0.5 text-xs font-medium"
              >
                {getCategoryLabel(category, categoryLabels)}
              </span>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export function getOrgRoleLabel(role: string): string {
  return ROLE_LABELS[role] ?? role;
}
