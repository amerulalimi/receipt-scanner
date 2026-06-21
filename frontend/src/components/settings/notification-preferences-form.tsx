"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { startTransition, useActionState, useEffect } from "react";
import { Controller, useForm } from "react-hook-form";

import { updateNotificationPreferencesAction } from "@/actions/settings";
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
import {
  Field,
  FieldDescription,
  FieldError,
  FieldGroup,
  FieldLabel,
} from "@/components/ui/field";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { NotificationPreferenceData } from "@/lib/api/types";
import { useTranslations } from "@/lib/i18n/use-translations";
import {
  notificationPreferencesSchema,
  type NotificationPreferencesFormValues,
} from "@/lib/validations/settings";

export function NotificationPreferencesForm({
  preferences,
}: {
  preferences: NotificationPreferenceData;
}) {
  const t = useTranslations("settings");
  const [state, submitAction, isPending] = useActionState(
    updateNotificationPreferencesAction,
    initialSettingsActionState,
  );

  const form = useForm<NotificationPreferencesFormValues>({
    resolver: zodResolver(notificationPreferencesSchema),
    defaultValues: preferences,
  });

  useEffect(() => {
    if (!state.fieldErrors) {
      return;
    }

    for (const [field, messages] of Object.entries(state.fieldErrors)) {
      if (messages[0]) {
        form.setError(field as keyof NotificationPreferencesFormValues, {
          message: messages[0],
        });
      }
    }
  }, [state.fieldErrors, form]);

  function onSubmit(values: NotificationPreferencesFormValues) {
    const formData = new FormData();
    formData.set("email_enabled", String(values.email_enabled));
    formData.set("in_app_enabled", String(values.in_app_enabled));
    formData.set("digest_frequency", values.digest_frequency);

    startTransition(() => {
      submitAction(formData);
    });
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("notificationsTitle")}</CardTitle>
        <CardDescription>{t("notificationsDescription")}</CardDescription>
      </CardHeader>
      <form onSubmit={form.handleSubmit(onSubmit)}>
        <CardContent>
          <FieldGroup>
            <Controller
              control={form.control}
              name="in_app_enabled"
              render={({ field }) => (
                <Field orientation="horizontal">
                  <div className="flex-1 space-y-1">
                    <FieldLabel htmlFor="in-app-enabled">
                      {t("inAppEnabled")}
                    </FieldLabel>
                    <FieldDescription>{t("inAppEnabledHint")}</FieldDescription>
                  </div>
                  <input
                    id="in-app-enabled"
                    type="checkbox"
                    className="size-4 rounded border"
                    checked={field.value}
                    onChange={(event) => field.onChange(event.target.checked)}
                  />
                </Field>
              )}
            />

            <Controller
              control={form.control}
              name="email_enabled"
              render={({ field }) => (
                <Field orientation="horizontal">
                  <div className="flex-1 space-y-1">
                    <FieldLabel htmlFor="email-enabled">
                      {t("emailEnabled")}
                    </FieldLabel>
                    <FieldDescription>{t("emailEnabledHint")}</FieldDescription>
                  </div>
                  <input
                    id="email-enabled"
                    type="checkbox"
                    className="size-4 rounded border"
                    checked={field.value}
                    onChange={(event) => field.onChange(event.target.checked)}
                  />
                </Field>
              )}
            />

            <Controller
              control={form.control}
              name="digest_frequency"
              render={({ field, fieldState }) => (
                <Field>
                  <FieldLabel htmlFor="digest-frequency">
                    {t("digestFrequency")}
                  </FieldLabel>
                  <Select
                    value={field.value}
                    onValueChange={field.onChange}
                    items={[
                      { value: "monthly", label: t("digestMonthly") },
                      { value: "off", label: t("digestOff") },
                    ]}
                  >
                    <SelectTrigger id="digest-frequency">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="monthly">{t("digestMonthly")}</SelectItem>
                      <SelectItem value="off">{t("digestOff")}</SelectItem>
                    </SelectContent>
                  </Select>
                  <FieldDescription>{t("digestFrequencyHint")}</FieldDescription>
                  <FieldError errors={[fieldState.error]} />
                </Field>
              )}
            />

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
            {isPending ? t("savingNotifications") : t("saveNotifications")}
          </Button>
        </CardFooter>
      </form>
    </Card>
  );
}
