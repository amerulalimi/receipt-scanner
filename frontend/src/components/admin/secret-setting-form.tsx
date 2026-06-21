"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { startTransition, useActionState, useEffect } from "react";
import { Controller, useForm } from "react-hook-form";

import { updateSecretAction } from "@/actions/admin-config";
import type { AdminActionState } from "@/actions/admin-config";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
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
import type { SecretSettingMasked } from "@/lib/api/types";
import {
  secretUpdateSchema,
  type SecretUpdateFormValues,
} from "@/lib/validations/admin-config";

const initialState: AdminActionState = {};

type SecretSettingFormProps = {
  setting: SecretSettingMasked;
};

export function SecretSettingForm({ setting }: SecretSettingFormProps) {
  const [state, submitAction, isPending] = useActionState(
    updateSecretAction,
    initialState,
  );

  const form = useForm<SecretUpdateFormValues>({
    resolver: zodResolver(secretUpdateSchema),
    defaultValues: {
      key: setting.key as SecretUpdateFormValues["key"],
      value: "",
    },
  });

  useEffect(() => {
    if (!state.fieldErrors) {
      return;
    }

    for (const [field, messages] of Object.entries(state.fieldErrors)) {
      if (messages[0]) {
        form.setError(field as keyof SecretUpdateFormValues, {
          message: messages[0],
        });
      }
    }
  }, [state.fieldErrors, form]);

  useEffect(() => {
    if (state.success) {
      form.reset({
        key: setting.key as SecretUpdateFormValues["key"],
        value: "",
      });
    }
  }, [state.success, form, setting.key]);

  function onSubmit(values: SecretUpdateFormValues) {
    const formData = new FormData();
    formData.set("key", values.key);
    formData.set("value", values.value);

    startTransition(() => {
      submitAction(formData);
    });
  }

  const label =
    setting.key === "openrouter_api_key"
      ? "OpenRouter API Key"
      : setting.key;

  return (
    <Card>
      <CardHeader>
        <CardTitle>{label}</CardTitle>
        <CardDescription>
          {setting.is_configured
            ? `Stored: ${setting.masked_value ?? "****"}`
            : "Not configured"}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
          {state.error ? (
            <p
              role="alert"
              className="rounded-lg border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive"
            >
              {state.error}
            </p>
          ) : null}

          {state.success ? (
            <p
              role="status"
              className="rounded-lg border border-primary/20 bg-primary/5 px-3 py-2 text-sm"
            >
              Secret updated successfully.
            </p>
          ) : null}

          <input type="hidden" {...form.register("key")} />

          <FieldGroup>
            <Controller
              name="value"
              control={form.control}
              render={({ field, fieldState }) => (
                <Field data-invalid={fieldState.invalid}>
                  <FieldLabel htmlFor={`secret-${setting.key}`}>
                    New value
                  </FieldLabel>
                  <Input
                    {...field}
                    id={`secret-${setting.key}`}
                    type="password"
                    autoComplete="off"
                    placeholder="sk-or-..."
                  />
                  <FieldError errors={[fieldState.error]} />
                </Field>
              )}
            />
          </FieldGroup>

          <Button type="submit" disabled={isPending}>
            {isPending ? "Saving…" : "Save secret"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
