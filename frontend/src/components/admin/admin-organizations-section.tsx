"use client";

import {
  deleteAdminOrganizationAction,
  type AdminDirectoryActionState,
} from "@/actions/admin-directory";
import { AdminDeleteDialog } from "@/components/admin/admin-delete-dialog";
import {
  AdminDirectoryToolbar,
  useAdminDirectoryPagination,
} from "@/components/admin/admin-directory-toolbar";
import { AdminRegistrationChart } from "@/components/admin/admin-registration-chart";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type {
  AdminPaginatedOrganizationsData,
  RegistrationStatsData,
} from "@/lib/api/types";

const initialDeleteState: AdminDirectoryActionState = {};

function formatDateTime(value: string): string {
  return new Intl.DateTimeFormat("en-MY", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

type AdminOrganizationsSectionProps = {
  organizations: AdminPaginatedOrganizationsData;
  stats: RegistrationStatsData;
};

export function AdminOrganizationsSection({
  organizations,
  stats,
}: AdminOrganizationsSectionProps) {
  const { page, goToPage } = useAdminDirectoryPagination(
    organizations.total_pages,
  );

  return (
    <div className="space-y-6">
      <AdminRegistrationChart
        stats={stats}
        title="Organization registrations"
        description="New organizations created over time."
      />

      <Card>
        <CardHeader>
          <CardTitle>All organizations</CardTitle>
          <CardDescription>
            {organizations.total} organizations · page {organizations.page} of{" "}
            {organizations.total_pages}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <AdminDirectoryToolbar searchPlaceholder="Search by name, SSM, or domain…" />

          <div className="overflow-x-auto rounded-lg border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-12">No</TableHead>
                  <TableHead>Organization name</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Email domain</TableHead>
                  <TableHead>Employees</TableHead>
                  <TableHead>Created at</TableHead>
                  <TableHead className="text-right">Action</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {organizations.items.length === 0 ? (
                  <TableRow>
                    <TableCell
                      colSpan={7}
                      className="py-8 text-center text-muted-foreground"
                    >
                      No organizations found.
                    </TableCell>
                  </TableRow>
                ) : (
                  organizations.items.map((org, index) => {
                    const rowNumber =
                      (organizations.page - 1) * organizations.limit + index + 1;
                    return (
                      <TableRow key={org.id}>
                        <TableCell>{rowNumber}</TableCell>
                        <TableCell className="font-medium">{org.name}</TableCell>
                        <TableCell>
                          <Badge
                            variant={
                              org.status === "active" ? "secondary" : "outline"
                            }
                          >
                            {org.status}
                          </Badge>
                        </TableCell>
                        <TableCell>{org.email_domain}</TableCell>
                        <TableCell>{org.employee_count}</TableCell>
                        <TableCell>{formatDateTime(org.created_at)}</TableCell>
                        <TableCell className="text-right">
                          {org.status === "active" ? (
                            <AdminDeleteDialog
                              id={org.id}
                              label="Delete"
                              title="Suspend organization?"
                              description={`This will suspend ${org.name}. Employees remain linked but the organization is marked inactive.`}
                              confirmLabel="Suspend"
                              action={deleteAdminOrganizationAction}
                              initialState={initialDeleteState}
                            />
                          ) : (
                            <span className="text-xs text-muted-foreground">—</span>
                          )}
                        </TableCell>
                      </TableRow>
                    );
                  })
                )}
              </TableBody>
            </Table>
          </div>

          <div className="flex items-center justify-between gap-3">
            <p className="text-sm text-muted-foreground">
              Showing {organizations.items.length} of {organizations.total}
            </p>
            <div className="flex gap-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                disabled={page <= 1}
                onClick={() => goToPage(page - 1)}
              >
                Previous
              </Button>
              <Button
                type="button"
                variant="outline"
                size="sm"
                disabled={page >= organizations.total_pages}
                onClick={() => goToPage(page + 1)}
              >
                Next
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
