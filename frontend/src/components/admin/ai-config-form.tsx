"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { startTransition, useActionState, useEffect } from "react";
import { Controller, useForm } from "react-hook-form";

import { updateAiConfigAction } from "@/actions/admin-config";
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { SecretSettingMasked, SystemConfigItem } from "@/lib/api/types";
import {
  aiConfigSchema,
  type AiConfigFormValues,
} from "@/lib/validations/admin-config";

const initialState: AdminActionState = {};

type AiConfigFormProps = {
  settings: SystemConfigItem[];
  secrets: SecretSettingMasked[];
};

function getSettingValue(settings: SystemConfigItem[], key: string) {
  return settings.find((item) => item.key === key)?.value ?? "";
}

export function AiConfigForm({ settings, secrets }: AiConfigFormProps) {
  const openrouterConfigured = secrets.some(
    (item) => item.key === "openrouter_api_key" && item.is_configured,
  );

  const [state, submitAction, isPending] = useActionState(
    updateAiConfigAction,
    initialState,
  );

  const form = useForm<AiConfigFormValues>({
    resolver: zodResolver(aiConfigSchema),
    defaultValues: {
      openrouter_vision_model: getSettingValue(
        settings,
        "openrouter_vision_model",
      ),
      receipt_processing_enabled: getSettingValue(
        settings,
        "receipt_processing_enabled",
      ) as "true" | "false",
    },
  });

  useEffect(() => {
    if (!state.fieldErrors) {
      return;
    }

    for (const [field, messages] of Object.entries(state.fieldErrors)) {
      if (messages[0]) {
        form.setError(field as keyof AiConfigFormValues, {
          message: messages[0],
        });
      }
    }
  }, [state.fieldErrors, form]);

  function onSubmit(values: AiConfigFormValues) {
    const formData = new FormData();
    formData.set("openrouter_vision_model", values.openrouter_vision_model);
    formData.set(
      "receipt_processing_enabled",
      values.receipt_processing_enabled,
    );

    startTransition(() => {
      submitAction(formData);
    });
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>AI Configuration</CardTitle>
        <CardDescription>
          Vision model for OCR + receipt classification. API keys are managed on
          the API Secrets page.
        </CardDescription>
      </CardHeader>
      <CardContent>
        {!openrouterConfigured ? (
          <p
            role="status"
            className="mb-4 rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-sm text-amber-900 dark:text-amber-100"
          >
            OpenRouter API key is not configured. Add one on{" "}
            <a href="/admin/secrets" className="underline">
              API Secrets
            </a>{" "}
            before processing receipts.
          </p>
        ) : null}

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
              AI settings updated successfully.
            </p>
          ) : null}

          <FieldGroup>
            <Controller
              name="openrouter_vision_model"
              control={form.control}
              render={({ field, fieldState }) => (
                <Field data-invalid={fieldState.invalid}>
                  <FieldLabel htmlFor="openrouter_vision_model">
                    Model Vision (OpenRouter)
                  </FieldLabel>
                  <Input
                    {...field}
                    id="openrouter_vision_model"
                    placeholder="google/gemini-2.5-flash"
                  />
                  <FieldError errors={[fieldState.error]} />
                </Field>
              )}
            />

            <Controller
              name="receipt_processing_enabled"
              control={form.control}
              render={({ field, fieldState }) => (
                <Field data-invalid={fieldState.invalid}>
                  <FieldLabel htmlFor="receipt_processing_enabled">
                    Receipt processing
                  </FieldLabel>
                  <Select value={field.value} onValueChange={field.onChange}>
                    <SelectTrigger id="receipt_processing_enabled">
                      <SelectValue placeholder="Select status" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="true">Enabled</SelectItem>
                      <SelectItem value="false">Disabled</SelectItem>
                    </SelectContent>
                  </Select>
                  <FieldError errors={[fieldState.error]} />
                </Field>
              )}
            />
          </FieldGroup>

          <Button type="submit" disabled={isPending}>
            {isPending ? "Saving…" : "Save settings"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
