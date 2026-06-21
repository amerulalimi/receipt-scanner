"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "next/navigation";
import { startTransition, useActionState, useEffect } from "react";
import { Controller, useForm } from "react-hook-form";
import { toast } from "sonner";

import {
  createManualReceiptAction,
} from "@/actions/receipt";
import { initialReceiptManualState } from "@/actions/receipt.types";
import { TaxYearSelect } from "@/components/shared/tax-year-select";
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
import { useTranslations } from "@/lib/i18n/use-translations";
import {
  manualReceiptFormSchema,
  type ManualReceiptFormValues,
} from "@/lib/validations/receipt";

type ManualReceiptFormProps = {
  defaultTaxYear: number;
  categoryOptions: Array<{ value: string; label: string }>;
};

export function ManualReceiptForm({
  defaultTaxYear,
  categoryOptions,
}: ManualReceiptFormProps) {
  const router = useRouter();
  const t = useTranslations("manualReceipt");
  const [state, submitAction, isPending] = useActionState(
    createManualReceiptAction,
    initialReceiptManualState,
  );

  const form = useForm<ManualReceiptFormValues>({
    resolver: zodResolver(manualReceiptFormSchema),
    defaultValues: {
      merchant_name: "",
      receipt_date: "",
      total_amount: "",
      category: categoryOptions[0]?.value ?? "semak_manual",
      claimed_amount: "",
      notes: "",
      tax_year: defaultTaxYear,
    },
  });

  useEffect(() => {
    form.setValue("tax_year", defaultTaxYear);
  }, [defaultTaxYear, form]);

  useEffect(() => {
    if (!state.fieldErrors) {
      return;
    }

    for (const [key, messages] of Object.entries(state.fieldErrors)) {
      const message = messages[0];
      if (message) {
        form.setError(key as keyof ManualReceiptFormValues, { message });
      }
    }
  }, [state.fieldErrors, form]);

  useEffect(() => {
    if (state.success) {
      toast.success(state.message ?? t("success"));
      form.reset({
        merchant_name: "",
        receipt_date: "",
        total_amount: "",
        category: categoryOptions[0]?.value ?? "semak_manual",
        claimed_amount: "",
        notes: "",
        tax_year: defaultTaxYear,
      });
      router.refresh();
    }
    if (state.error) {
      toast.error(state.error);
    }
  }, [state, form, router, defaultTaxYear, categoryOptions, t]);

  function onSubmit(values: ManualReceiptFormValues) {
    const formData = new FormData();
    formData.set("merchant_name", values.merchant_name);
    formData.set("receipt_date", values.receipt_date);
    formData.set("total_amount", values.total_amount);
    formData.set("category", values.category);
    if (values.claimed_amount && values.claimed_amount.length > 0) {
      formData.set("claimed_amount", values.claimed_amount);
    }
    if (values.notes && values.notes.length > 0) {
      formData.set("notes", values.notes);
    }
    formData.set("tax_year", String(values.tax_year));
    startTransition(() => submitAction(formData));
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("title")}</CardTitle>
        <CardDescription>{t("description")}</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={form.handleSubmit(onSubmit)}>
          <FieldGroup>
            <Field>
              <FieldLabel htmlFor="merchant_name">{t("merchant")}</FieldLabel>
              <Input id="merchant_name" {...form.register("merchant_name")} />
              <FieldError errors={[form.formState.errors.merchant_name]} />
            </Field>

            <div className="grid gap-4 sm:grid-cols-2">
              <Field>
                <FieldLabel htmlFor="receipt_date">{t("date")}</FieldLabel>
                <Input id="receipt_date" type="date" {...form.register("receipt_date")} />
                <FieldError errors={[form.formState.errors.receipt_date]} />
              </Field>

              <Field>
                <FieldLabel htmlFor="total_amount">{t("totalAmount")}</FieldLabel>
                <Input
                  id="total_amount"
                  inputMode="decimal"
                  placeholder="0.00"
                  {...form.register("total_amount")}
                />
                <FieldError errors={[form.formState.errors.total_amount]} />
              </Field>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <Field>
                <FieldLabel>{t("category")}</FieldLabel>
                <Controller
                  control={form.control}
                  name="category"
                  render={({ field }) => (
                    <Select
                      value={field.value}
                      onValueChange={field.onChange}
                      items={categoryOptions}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {categoryOptions.map((option) => (
                          <SelectItem key={option.value} value={option.value}>
                            {option.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  )}
                />
                <FieldError errors={[form.formState.errors.category]} />
              </Field>

              <Field>
                <FieldLabel htmlFor="claimed_amount">{t("claimedAmount")}</FieldLabel>
                <Input
                  id="claimed_amount"
                  inputMode="decimal"
                  placeholder={t("claimedAmountOptional")}
                  {...form.register("claimed_amount")}
                />
                <FieldError errors={[form.formState.errors.claimed_amount]} />
              </Field>
            </div>

            <Controller
              control={form.control}
              name="tax_year"
              render={({ field }) => (
                <TaxYearSelect
                  value={field.value}
                  onValueChange={field.onChange}
                  label={t("taxYear")}
                  anchorYear={defaultTaxYear}
                />
              )}
            />

            <Field>
              <FieldLabel htmlFor="notes">{t("notes")}</FieldLabel>
              <textarea
                id="notes"
                rows={3}
                className="flex min-h-[80px] w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-xs outline-none focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50"
                {...form.register("notes")}
              />
              <FieldError errors={[form.formState.errors.notes]} />
            </Field>

            <Button type="submit" disabled={isPending}>
              {isPending ? t("saving") : t("submit")}
            </Button>
          </FieldGroup>
        </form>
      </CardContent>
    </Card>
  );
}
