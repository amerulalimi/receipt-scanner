"use client";

import {
  startTransition,
  useActionState,
  useEffect,
  useState,
} from "react";

import {
  initialOrgActionState,
  removeOrgEmployeeAction,
  updateOrgEmployeeAction,
} from "@/actions/org";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { formatRinggit } from "@/lib/receipt-format";
import type { OrgEmployeeListData } from "@/lib/api/types";
import { getOrgRoleLabel } from "@/components/org/org-overview-section";
import { useTranslations } from "@/lib/i18n/use-translations";
import { computeEmployeeStatus } from "@/lib/types/org";

export function OrgEmployeesSection({
  employees,
  currentUserId,
}: {
  employees: OrgEmployeeListData;
  currentUserId: string;
}) {
  const t = useTranslations("org");
  const [state, submitAction, isPending] = useActionState(
    updateOrgEmployeeAction,
    initialOrgActionState,
  );
  const [removeState, removeAction, isRemovePending] = useActionState(
    removeOrgEmployeeAction,
    initialOrgActionState,
  );
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    if (state.message) {
      setMessage(state.message);
    }
    if (state.error) {
      setMessage(state.error);
    }
  }, [state.message, state.error]);

  useEffect(() => {
    if (removeState.message) {
      setMessage(removeState.message);
    }
    if (removeState.error) {
      setMessage(removeState.error);
    }
  }, [removeState.message, removeState.error]);

  function removeEmployee(userId: string) {
    const formData = new FormData();
    formData.set("user_id", userId);

    startTransition(() => {
      removeAction(formData);
    });
  }

  function toggleEmployee(userId: string, isActive: boolean) {
    const formData = new FormData();
    formData.set("user_id", userId);
    formData.set("is_active", isActive ? "false" : "true");

    startTransition(() => {
      submitAction(formData);
    });
  }

  if (employees.items.length === 0) {
    return (
      <Card>
        <CardContent className="py-10 text-center text-sm text-muted-foreground">
          {t("employeesEmpty")}
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">{t("employeesTitle")}</CardTitle>
        <CardDescription>
          {t("employeesCount", { total: employees.total })}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {message ? (
          <p
            className={
              state.error || removeState.error
                ? "text-sm text-destructive"
                : "text-sm text-emerald-600"
            }
          >
            {message}
          </p>
        ) : null}

        {employees.items.map((employee) => {
          const isSelf = employee.user_id === currentUserId;

          return (
            <div
              key={employee.user_id}
              className="flex flex-col gap-3 rounded-lg border px-3 py-3 sm:flex-row sm:items-center sm:justify-between"
            >
              <div className="min-w-0 space-y-1">
                <p className="font-medium">
                  {employee.full_name ?? employee.email}
                </p>
                <p className="text-sm text-muted-foreground">
                  {employee.email} · {getOrgRoleLabel(employee.role)}
                </p>
                <p className="text-sm text-muted-foreground">
                  {employee.receipts_count} receipts ·{" "}
                  {formatRinggit(employee.total_claimed)} claimed ·{" "}
                  {employee.pending_count} pending
                </p>
              </div>

              <div className="flex items-center gap-2">
                <span
                  className={
                    computeEmployeeStatus(employee) === "active"
                      ? "rounded-full bg-emerald-500/10 px-2 py-0.5 text-xs font-medium text-emerald-700 dark:text-emerald-300"
                      : "rounded-full bg-muted px-2 py-0.5 text-xs font-medium text-muted-foreground"
                  }
                >
                  {employee.is_active ? t("statusActive") : t("statusInactive")}
                </span>
                {!isSelf && employee.role !== "superadmin" ? (
                  <>
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      disabled={isPending || isRemovePending}
                      onClick={() =>
                        toggleEmployee(employee.user_id, employee.is_active)
                      }
                    >
                      {employee.is_active ? "Deactivate" : "Activate"}
                    </Button>
                    <Button
                      type="button"
                      variant="destructive"
                      size="sm"
                      disabled={isPending || isRemovePending}
                      onClick={() => removeEmployee(employee.user_id)}
                    >
                      Remove
                    </Button>
                  </>
                ) : null}
              </div>
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}
