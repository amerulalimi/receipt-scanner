"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { PencilIcon } from "lucide-react";
import { startTransition, useActionState, useEffect, useState } from "react";
import { Controller, useForm } from "react-hook-form";

import {
  getReceiptDetailAction,
  updateReceiptAction,
} from "@/actions/receipt";
import { initialReceiptUpdateState } from "@/actions/receipt.types";
import {
  buildLineItemsPayload,
  ReceiptLineItemsEditor,
} from "@/components/receipts/receipt-line-items-editor";
import { ReceiptThumbnail } from "@/components/receipts/receipt-thumbnail";
import { Button } from "@/components/ui/button";
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
import {
  Sheet,
  SheetClose,
  SheetContent,
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { formatReceiptDate, formatAmountForInput, formatRinggit } from "@/lib/receipt-format";
import { isPreviewableReceiptFile } from "@/lib/receipt-files";
import type { ReceiptDetail, ReceiptLineItem, ReceiptListItem } from "@/lib/api/types";
import {
  receiptUpdateFormSchema,
  type ReceiptUpdateFormValues,
} from "@/lib/validations/receipt";

type ReceiptEditSheetProps = {
  item: ReceiptListItem;
  categoryOptions: Array<{ value: string; label: string }>;
};

export function ReceiptEditSheet({
  item,
  categoryOptions,
}: ReceiptEditSheetProps) {
  const [open, setOpen] = useState(false);
  const [detail, setDetail] = useState<ReceiptDetail | null>(null);
  const [lineItems, setLineItems] = useState<ReceiptLineItem[]>([]);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [state, submitAction, isPending] = useActionState(
    updateReceiptAction,
    initialReceiptUpdateState,
  );

  const form = useForm<ReceiptUpdateFormValues>({
    resolver: zodResolver(receiptUpdateFormSchema),
    defaultValues: {
      receipt_id: item.id,
      category:
        (item.category as ReceiptUpdateFormValues["category"]) ?? "semak_manual",
      claimed_amount: formatAmountForInput(item.claimed_amount),
    },
  });

  useEffect(() => {
    if (!open) {
      return;
    }

    let cancelled = false;
    setLoading(true);
    setLoadError(null);

    void getReceiptDetailAction(item.id).then((result) => {
      if (cancelled) {
        return;
      }

      setLoading(false);

      if (result.error || !result.data) {
        setLoadError(result.error ?? "Failed to load receipt.");
        return;
      }

      setDetail(result.data);
      setLineItems(result.data.line_items ?? []);
      form.reset({
        receipt_id: result.data.id,
        category:
          (result.data.category as ReceiptUpdateFormValues["category"]) ??
          "semak_manual",
        claimed_amount: formatAmountForInput(result.data.claimed_amount),
      });
    });

    return () => {
      cancelled = true;
    };
  }, [open, item.id, form]);

  useEffect(() => {
    if (!state.fieldErrors) {
      return;
    }

    for (const [field, messages] of Object.entries(state.fieldErrors)) {
      if (messages[0]) {
        form.setError(field as keyof ReceiptUpdateFormValues, {
          message: messages[0],
        });
      }
    }
  }, [state.fieldErrors, form]);

  useEffect(() => {
    if (state.success) {
      setOpen(false);
    }
  }, [state.success]);

  const hasItemisedClaim = lineItems.length >= 2;
  const computedClaimedTotal = lineItems.reduce(
    (sum, item) =>
      item.included_in_claim
        ? sum +
          (typeof item.amount === "number"
            ? item.amount
            : Number.parseFloat(String(item.amount)) || 0)
        : sum,
    0,
  );

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger
        render={
          <Button type="button" variant="outline" size="sm">
            <PencilIcon className="size-4" />
            Edit
          </Button>
        }
      />

      <SheetContent className="overflow-y-auto sm:max-w-md">
        <SheetHeader>
          <SheetTitle>Edit receipt</SheetTitle>
          <SheetDescription>
            {hasItemisedClaim
              ? "Toggle claimable line items. Claimed amount is calculated automatically."
              : "Update category and claimed amount."}
          </SheetDescription>
        </SheetHeader>

        {loading ? (
          <p className="px-4 text-sm text-muted-foreground">Loading…</p>
        ) : loadError ? (
          <p className="px-4 text-sm text-destructive">{loadError}</p>
        ) : (
          <form
            className="space-y-6 px-4"
            onSubmit={form.handleSubmit((values) => {
              const formData = new FormData();
              formData.set("receipt_id", values.receipt_id);

              if (hasItemisedClaim) {
                formData.set(
                  "line_items",
                  JSON.stringify(buildLineItemsPayload(lineItems)),
                );
                formData.set("update_mode", "line_items");
              } else {
                formData.set("category", values.category);
                if (values.claimed_amount?.trim()) {
                  formData.set("claimed_amount", values.claimed_amount.trim());
                }
              }

              startTransition(() => submitAction(formData));
            })}
          >
            <div className="rounded-lg border bg-muted/30 p-3 text-sm">
              {(detail?.image_url ?? item.thumbnail_url) &&
              isPreviewableReceiptFile(item.file_type) ? (
                <div className="mb-3">
                  <ReceiptThumbnail
                    receiptId={item.id}
                    fileType={item.file_type}
                    merchantName={detail?.merchant_name ?? item.merchant_name}
                    size="md"
                    className="mx-auto"
                  />
                </div>
              ) : null}
              <p className="font-medium">
                {detail?.merchant_name ?? item.merchant_name ?? "Unnamed receipt"}
              </p>
              <p className="text-muted-foreground">
                {formatReceiptDate(
                  detail?.receipt_date ?? item.receipt_date ?? item.created_at,
                )}
                {" · "}
                Total:{" "}
                {formatRinggit(
                  detail?.total_amount ?? item.total_amount ?? item.claimed_amount,
                )}
              </p>
              {detail?.ai_nota ? (
                <p className="mt-2 text-muted-foreground">{detail.ai_nota}</p>
              ) : null}
            </div>

            {detail?.relief_status ? (
              <div className="rounded-lg border px-3 py-2 text-sm">
                <p>
                  Relief limit: {formatRinggit(detail.relief_status.limit_amount)}
                </p>
                <p>
                  Claimed: {formatRinggit(detail.relief_status.total_claimed)} (
                  {detail.relief_status.percentage.toFixed(1)}%)
                </p>
                {detail.relief_status.status === "warning" ? (
                  <p className="text-amber-700 dark:text-amber-300">
                    Approaching relief limit.
                  </p>
                ) : null}
              </div>
            ) : null}

            {hasItemisedClaim ? (
              <ReceiptLineItemsEditor
                lineItems={lineItems}
                categoryLabels={Object.fromEntries(
                  categoryOptions.map((option) => [option.value, option.label]),
                )}
                disabled={isPending}
                onChange={setLineItems}
              />
            ) : null}

            <FieldGroup>
              <input type="hidden" {...form.register("receipt_id")} />

              {!hasItemisedClaim ? (
                <>
              <Controller
                control={form.control}
                name="category"
                render={({ field, fieldState }) => (
                  <Field data-invalid={fieldState.invalid}>
                    <FieldLabel htmlFor="receipt-category">Category</FieldLabel>
                    <Select
                      value={field.value}
                      onValueChange={field.onChange}
                    >
                      <SelectTrigger id="receipt-category" className="w-full">
                        <SelectValue placeholder="Select category" />
                      </SelectTrigger>
                      <SelectContent>
                        {categoryOptions.map((option) => (
                          <SelectItem key={option.value} value={option.value}>
                            {option.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    {fieldState.error ? (
                      <FieldError>{fieldState.error.message}</FieldError>
                    ) : null}
                  </Field>
                )}
              />

              <Field data-invalid={!!form.formState.errors.claimed_amount}>
                <FieldLabel htmlFor="claimed-amount">
                  Claimed amount (RM)
                </FieldLabel>
                <Input
                  id="claimed-amount"
                  inputMode="decimal"
                  placeholder="e.g. 120.50"
                  {...form.register("claimed_amount")}
                />
                {form.formState.errors.claimed_amount ? (
                  <FieldError>
                    {form.formState.errors.claimed_amount.message}
                  </FieldError>
                ) : null}
              </Field>
                </>
              ) : (
                <div className="rounded-lg border px-3 py-2 text-sm">
                  <p>
                    Category:{" "}
                    {categoryOptions.find((option) => option.value === detail?.category)
                      ?.label ?? detail?.category ?? "—"}
                  </p>
                  <p>
                    Claimed amount: {formatRinggit(computedClaimedTotal)}
                  </p>
                </div>
              )}
            </FieldGroup>

            {state.error ? (
              <p className="text-sm text-destructive">{state.error}</p>
            ) : null}

            <SheetFooter className="px-0">
              <SheetClose render={<Button type="button" variant="outline" />}>
                Cancel
              </SheetClose>
              <Button type="submit" disabled={isPending}>
                {isPending ? "Saving…" : "Save"}
              </Button>
            </SheetFooter>
          </form>
        )}
      </SheetContent>
    </Sheet>
  );
}
