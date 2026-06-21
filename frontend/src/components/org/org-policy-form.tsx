"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import {
  startTransition,
  useActionState,
  useEffect,
} from "react";
import { Controller, useForm } from "react-hook-form";

import {
  initialOrgActionState,
  updateOrgPolicyAction,
} from "@/actions/org";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Field,
  FieldError,
  FieldGroup,
  FieldLabel,
} from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { getCategoryLabel } from "@/lib/constants/receipts";
import type { OrgPolicyData, ReliefCategoryItem } from "@/lib/api/types";
import {
  orgPolicyUpdateSchema,
  type OrgPolicyUpdateFormValues,
} from "@/lib/validations/org";

export function OrgPolicyForm({
  policy,
  availableCategories,
  categoryLabels,
}: {
  policy: OrgPolicyData;
  availableCategories: ReliefCategoryItem[];
  categoryLabels: Record<string, string>;
}) {
  const [state, submitAction, isPending] = useActionState(
    updateOrgPolicyAction,
    initialOrgActionState,
  );

  const form = useForm<OrgPolicyUpdateFormValues>({
    resolver: zodResolver(orgPolicyUpdateSchema),
    defaultValues: {
      allowed_categories: policy.allowed_categories.filter((category) =>
        availableCategories.some((item) => item.category === category),
      ),
      require_hr_approval: policy.require_hr_approval,
      max_receipts_per_month: policy.max_receipts_per_month,
      tax_year: policy.tax_year,
    },
  });

  useEffect(() => {
    if (!state.fieldErrors) {
      return;
    }

    for (const [field, messages] of Object.entries(state.fieldErrors)) {
      if (messages[0]) {
        form.setError(field as keyof OrgPolicyUpdateFormValues, {
          message: messages[0],
        });
      }
    }
  }, [state.fieldErrors, form]);

  function onSubmit(values: OrgPolicyUpdateFormValues) {
    const formData = new FormData();
    for (const category of values.allowed_categories) {
      formData.append("allowed_categories", category);
    }
    formData.set(
      "require_hr_approval",
      values.require_hr_approval ? "true" : "false",
    );
    formData.set(
      "max_receipts_per_month",
      String(values.max_receipts_per_month),
    );
    formData.set("tax_year", String(values.tax_year));

    startTransition(() => {
      submitAction(formData);
    });
  }

  const selectedCategories = form.watch("allowed_categories");

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Organization Policy</CardTitle>
        <CardDescription>
          Set claim categories and receipt limits for employees.
        </CardDescription>
      </CardHeader>
      <form onSubmit={form.handleSubmit(onSubmit)}>
        <CardContent className="space-y-6">
          <FieldGroup>
            <Field>
              <FieldLabel>Allowed categories</FieldLabel>
              <div className="grid gap-3 sm:grid-cols-2">
                {availableCategories.map((category) => {
                  const checked = selectedCategories.includes(category.category);
                  return (
                    <div key={category.category} className="flex items-center gap-2">
                      <input
                        id={`policy-${category.category}`}
                        type="checkbox"
                        className="size-4 rounded border"
                        checked={checked}
                        onChange={(event) => {
                          const current = form.getValues("allowed_categories");
                          if (event.target.checked) {
                            form.setValue("allowed_categories", [
                              ...current,
                              category.category,
                            ]);
                          } else {
                            form.setValue(
                              "allowed_categories",
                              current.filter((item) => item !== category.category),
                            );
                          }
                        }}
                      />
                      <Label htmlFor={`policy-${category.category}`}>
                        {getCategoryLabel(category.category, categoryLabels)}
                      </Label>
                    </div>
                  );
                })}
              </div>
              <FieldError errors={[form.formState.errors.allowed_categories]} />
            </Field>

            <Controller
              control={form.control}
              name="require_hr_approval"
              render={({ field }) => (
                <Field>
                  <div className="flex items-center gap-2">
                    <input
                      id="require-hr-approval"
                      type="checkbox"
                      className="size-4 rounded border"
                      checked={field.value}
                      onChange={(event) =>
                        field.onChange(event.target.checked)
                      }
                    />
                    <Label htmlFor="require-hr-approval">
                      Require HR approval before receipts are approved
                    </Label>
                  </div>
                </Field>
              )}
            />

            <div className="grid gap-4 sm:grid-cols-2">
              <Controller
                control={form.control}
                name="max_receipts_per_month"
                render={({ field, fieldState }) => (
                  <Field data-invalid={fieldState.invalid}>
                    <FieldLabel htmlFor="max-receipts">
                      Monthly receipt limit
                    </FieldLabel>
                    <Input
                      id="max-receipts"
                      type="number"
                      min={1}
                      max={500}
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
                name="tax_year"
                render={({ field, fieldState }) => (
                  <Field data-invalid={fieldState.invalid}>
                    <FieldLabel htmlFor="tax-year">Tax year</FieldLabel>
                    <Input
                      id="tax-year"
                      type="number"
                      min={2000}
                      max={2100}
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
              <p className="text-sm text-emerald-600">{state.message}</p>
            ) : null}
          </FieldGroup>
        </CardContent>
        <CardFooter>
          <Button type="submit" disabled={isPending}>
            {isPending ? "Saving…" : "Save policy"}
          </Button>
        </CardFooter>
      </form>
    </Card>
  );
}
