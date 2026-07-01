"use client";

import {
  deleteAdminUserAction,
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
  AdminPaginatedUsersData,
  RegistrationStatsData,
} from "@/lib/api/types";

const initialDeleteState: AdminDirectoryActionState = {};

function formatDateTime(value: string): string {
  return new Intl.DateTimeFormat("en-MY", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

type AdminUsersSectionProps = {
  users: AdminPaginatedUsersData;
  stats: RegistrationStatsData;
};

export function AdminUsersSection({ users, stats }: AdminUsersSectionProps) {
  const { page, goToPage } = useAdminDirectoryPagination(users.total_pages);

  return (
    <div className="space-y-6">
      <AdminRegistrationChart
        stats={stats}
        title="User registrations"
        description="New user sign-ups over time."
      />

      <Card>
        <CardHeader>
          <CardTitle>All users</CardTitle>
          <CardDescription>
            {users.total} registered users · page {users.page} of {users.total_pages}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <AdminDirectoryToolbar searchPlaceholder="Search by name or email…" />

          <div className="overflow-x-auto rounded-lg border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-12">No</TableHead>
                  <TableHead>Client name</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Email</TableHead>
                  <TableHead>Created at</TableHead>
                  <TableHead className="text-right">Action</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {users.items.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} className="py-8 text-center text-muted-foreground">
                      No users found.
                    </TableCell>
                  </TableRow>
                ) : (
                  users.items.map((user, index) => {
                    const rowNumber = (users.page - 1) * users.limit + index + 1;
                    return (
                      <TableRow key={user.id}>
                        <TableCell>{rowNumber}</TableCell>
                        <TableCell className="font-medium">
                          {user.full_name ?? "—"}
                          {!user.is_active ? (
                            <Badge variant="outline" className="ml-2">
                              Inactive
                            </Badge>
                          ) : null}
                        </TableCell>
                        <TableCell>
                          <Badge variant="secondary">{user.account_type}</Badge>
                        </TableCell>
                        <TableCell>{user.email}</TableCell>
                        <TableCell>{formatDateTime(user.created_at)}</TableCell>
                        <TableCell className="text-right">
                          {user.is_active ? (
                            <AdminDeleteDialog
                              id={user.id}
                              label="Delete"
                              title="Deactivate user?"
                              description={`This will deactivate ${user.email}. The account data will be kept but the user cannot sign in.`}
                              confirmLabel="Deactivate"
                              action={deleteAdminUserAction}
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
              Showing {users.items.length} of {users.total}
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
                disabled={page >= users.total_pages}
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
