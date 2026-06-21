"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { startTransition, useActionState, useEffect } from "react";
import { Controller, useForm } from "react-hook-form";

import { updateSettingsProfileAction } from "@/actions/settings";
import { initialSettingsActionState } from "@/actions/settings.types";
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
import type { MeData } from "@/lib/api/types";
import {
  settingsProfileSchema,
  type SettingsProfileFormValues,
} from "@/lib/validations/settings";
import { useTranslations } from "@/lib/i18n/use-translations";

export function SettingsProfileForm({ user }: { user: MeData }) {
  const t = useTranslations("settings");
  const [state, submitAction, isPending] = useActionState(
    updateSettingsProfileAction,
    initialSettingsActionState,
  );

  const form = useForm<SettingsProfileFormValues>({
    resolver: zodResolver(settingsProfileSchema),
    defaultValues: {
      full_name: user.full_name ?? "",
      tax_year: user.tax_year,
      tax_bracket: user.tax_bracket,
    },
  });

  useEffect(() => {
    if (!state.fieldErrors) {
      return;
    }

    for (const [field, messages] of Object.entries(state.fieldErrors)) {
      if (messages[0]) {
        form.setError(field as keyof SettingsProfileFormValues, {
          message: messages[0],
        });
      }
    }
  }, [state.fieldErrors, form]);

  function onSubmit(values: SettingsProfileFormValues) {
    const formData = new FormData();
    formData.set("full_name", values.full_name);
    formData.set("tax_year", String(values.tax_year));
    formData.set(
      "tax_bracket",
      values.tax_bracket === null ? "" : String(values.tax_bracket),
    );

    startTransition(() => {
      submitAction(formData);
    });
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("profileTitle")}</CardTitle>
        <CardDescription>{t("profileDescription")}</CardDescription>
      </CardHeader>
      <form onSubmit={form.handleSubmit(onSubmit)}>
        <CardContent>
          <FieldGroup>
            <Controller
              control={form.control}
              name="full_name"
              render={({ field, fieldState }) => (
                <Field data-invalid={fieldState.invalid}>
                  <FieldLabel htmlFor="settings-full-name">{t("fullName")}</FieldLabel>
                  <Input id="settings-full-name" {...field} />
                  <FieldError errors={[fieldState.error]} />
                </Field>
              )}
            />

            <Field>
              <FieldLabel htmlFor="settings-email">Email</FieldLabel>
              <Input id="settings-email" value={user.email} readOnly />
            </Field>

            <div className="grid gap-4 sm:grid-cols-2">
              <Controller
                control={form.control}
                name="tax_year"
                render={({ field, fieldState }) => (
                  <Field data-invalid={fieldState.invalid}>
                    <FieldLabel htmlFor="settings-tax-year">{t("taxYear")}</FieldLabel>
                    <Input
                      id="settings-tax-year"
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

              <Controller
                control={form.control}
                name="tax_bracket"
                render={({ field, fieldState }) => (
                  <Field data-invalid={fieldState.invalid}>
                    <FieldLabel htmlFor="settings-tax-bracket">
                      {t("taxBracket")}
                    </FieldLabel>
                    <Input
                      id="settings-tax-bracket"
                      type="number"
                      min={0}
                      max={100}
                      step="0.01"
                      value={field.value ?? ""}
                      onChange={(event) =>
                        field.onChange(
                          event.target.value === ""
                            ? null
                            : Number(event.target.value),
                        )
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
            {state.success && state.message ? (
              <p className="text-sm text-emerald-600">{state.message}</p>
            ) : null}
          </FieldGroup>
        </CardContent>
        <CardFooter>
          <Button type="submit" disabled={isPending}>
            {isPending ? `${t("saveProfile")}…` : t("saveProfile")}
          </Button>
        </CardFooter>
      </form>
    </Card>
  );
}
