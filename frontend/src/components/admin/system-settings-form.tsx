"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { startTransition, useActionState, useEffect } from "react";
import { Controller, useForm } from "react-hook-form";

import { updateSystemSettingsAction } from "@/actions/admin-system";
import type { AdminActionState } from "@/actions/admin-config";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Field, FieldError, FieldGroup, FieldLabel } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import type { SystemOverviewData } from "@/lib/api/types";
import {
  systemSettingsSchema,
  type SystemSettingsFormValues,
} from "@/lib/validations/admin-system";

const initialState: AdminActionState = {};

export function SystemSettingsForm({ overview }: { overview: SystemOverviewData }) {
  const [state, submitAction, isPending] = useActionState(
    updateSystemSettingsAction,
    initialState,
  );

  const form = useForm<SystemSettingsFormValues>({
    resolver: zodResolver(systemSettingsSchema),
    defaultValues: {
      auth_rate_limit_max: overview.auth_rate_limit_max,
      auth_rate_limit_window_seconds: overview.auth_rate_limit_window_seconds,
      audit_retention_days: overview.audit_retention_days,
      receipt_retention_days: overview.receipt_retention_days,
    },
  });

  useEffect(() => {
    if (!state.fieldErrors) {
      return;
    }
    for (const [field, messages] of Object.entries(state.fieldErrors)) {
      if (messages[0]) {
        form.setError(field as keyof SystemSettingsFormValues, {
          message: messages[0],
        });
      }
    }
  }, [state.fieldErrors, form]);

  function onSubmit(values: SystemSettingsFormValues) {
    const formData = new FormData();
    formData.set("auth_rate_limit_max", String(values.auth_rate_limit_max));
    formData.set(
      "auth_rate_limit_window_seconds",
      String(values.auth_rate_limit_window_seconds),
    );
    formData.set("audit_retention_days", String(values.audit_retention_days));
    formData.set("receipt_retention_days", String(values.receipt_retention_days));

    startTransition(() => {
      submitAction(formData);
    });
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Rate Limit & Retention</CardTitle>
        <CardDescription>
          Login/register rate limits and audit/receipt data retention periods.
        </CardDescription>
      </CardHeader>
      <form onSubmit={form.handleSubmit(onSubmit)}>
        <CardContent>
          <FieldGroup>
            <div className="grid gap-4 sm:grid-cols-2">
              <Controller
                control={form.control}
                name="auth_rate_limit_max"
                render={({ field, fieldState }) => (
                  <Field data-invalid={fieldState.invalid}>
                    <FieldLabel htmlFor="auth-rate-max">
                      Auth max attempts
                    </FieldLabel>
                    <Input
                      id="auth-rate-max"
                      type="number"
                      min={1}
                      max={100}
                      value={field.value}
                      onChange={(event) =>
                        field.onChange(Number(event.target.value))
                      }
                    />
                    <FieldError errors={[fieldState.error]} />
                  </Field>
                )}
              />
              <Controller
                control={form.control}
                name="auth_rate_limit_window_seconds"
                render={({ field, fieldState }) => (
                  <Field data-invalid={fieldState.invalid}>
                    <FieldLabel htmlFor="auth-rate-window">
                      Auth window (seconds)
                    </FieldLabel>
                    <Input
                      id="auth-rate-window"
                      type="number"
                      min={60}
                      max={86400}
                      value={field.value}
                      onChange={(event) =>
                        field.onChange(Number(event.target.value))
                      }
                    />
                    <FieldError errors={[fieldState.error]} />
                  </Field>
                )}
              />
              <Controller
                control={form.control}
                name="audit_retention_days"
                render={({ field, fieldState }) => (
                  <Field data-invalid={fieldState.invalid}>
                    <FieldLabel htmlFor="audit-retention">
                      Keep audit (days)
                    </FieldLabel>
                    <Input
                      id="audit-retention"
                      type="number"
                      min={1}
                      max={3650}
                      value={field.value}
                      onChange={(event) =>
                        field.onChange(Number(event.target.value))
                      }
                    />
                    <FieldError errors={[fieldState.error]} />
                  </Field>
                )}
              />
              <Controller
                control={form.control}
                name="receipt_retention_days"
                render={({ field, fieldState }) => (
                  <Field data-invalid={fieldState.invalid}>
                    <FieldLabel htmlFor="receipt-retention">
                      Keep deleted receipts (days)
                    </FieldLabel>
                    <Input
                      id="receipt-retention"
                      type="number"
                      min={1}
                      max={3650}
                      value={field.value}
                      onChange={(event) =>
                        field.onChange(Number(event.target.value))
                      }
                    />
                    <FieldError errors={[fieldState.error]} />
                  </Field>
                )}
              />
            </div>
            {state.error ? (
              <p className="text-sm text-destructive">{state.error}</p>
            ) : null}
            {state.success ? (
              <p className="text-sm text-emerald-600">Settings saved.</p>
            ) : null}
          </FieldGroup>
        </CardContent>
        <CardFooter>
          <Button type="submit" disabled={isPending}>
            {isPending ? "Saving…" : "Save system settings"}
          </Button>
        </CardFooter>
      </form>
    </Card>
  );
}
