"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { FileImage, X } from "lucide-react";
import { useRouter } from "next/navigation";
import { startTransition, useActionState, useEffect, useRef } from "react";
import { Controller, useForm } from "react-hook-form";
import { toast } from "sonner";

import {
  initialReceiptUploadState,
  type ReceiptUploadActionState,
} from "@/actions/receipt.types";
import { uploadReceiptAction } from "@/actions/receipt";
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
  RECEIPT_UPLOAD_ACCEPT,
  RECEIPT_UPLOAD_MAX_FILES,
} from "@/lib/constants/receipts";
import { useTranslations } from "@/lib/i18n/use-translations";
import {
  receiptBulkUploadSchema,
  type ReceiptBulkUploadFormValues,
} from "@/lib/validations/receipt";

function formatFileSize(bytes: number): string {
  if (bytes < 1024 * 1024) {
    return `${Math.round(bytes / 1024)} KB`;
  }

  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

type ReceiptUploadFormProps = {
  defaultTaxYear: number;
};

export function ReceiptUploadForm({ defaultTaxYear }: ReceiptUploadFormProps) {
  const router = useRouter();
  const t = useTranslations("dashboard");
  const tCommon = useTranslations("common");
  const [state, submitAction, isPending] = useActionState(
    uploadReceiptAction,
    initialReceiptUploadState,
  );

  const form = useForm<ReceiptBulkUploadFormValues>({
    resolver: zodResolver(receiptBulkUploadSchema),
    defaultValues: { files: [], tax_year: defaultTaxYear },
  });

  const selectedFiles = form.watch("files");
  const selectedTaxYear = form.watch("tax_year");
  const handledSuccessStateRef = useRef<ReceiptUploadActionState | null>(null);
  const handledErrorStateRef = useRef<ReceiptUploadActionState | null>(null);

  useEffect(() => {
    form.setValue("tax_year", defaultTaxYear);
  }, [defaultTaxYear, form]);

  useEffect(() => {
    if (!state.fieldErrors) {
      return;
    }

    for (const [field, messages] of Object.entries(state.fieldErrors)) {
      if (messages[0]) {
        form.setError(field as keyof ReceiptBulkUploadFormValues, {
          message: messages[0],
        });
      }
    }
  }, [state.fieldErrors, form]);

  useEffect(() => {
    if (!state.error) {
      handledErrorStateRef.current = null;
      return;
    }

    if (handledErrorStateRef.current === state) {
      return;
    }

    handledErrorStateRef.current = state;

    toast.error(state.error);
  }, [state]);

  useEffect(() => {
    if (!state.success) {
      handledSuccessStateRef.current = null;
      return;
    }

    if (handledSuccessStateRef.current === state) {
      return;
    }

    handledSuccessStateRef.current = state;

    form.reset({ files: [], tax_year: defaultTaxYear });
    const input = document.getElementById("receipt-file") as HTMLInputElement | null;
    if (input) {
      input.value = "";
    }

    if (state.message) {
      toast.success(t("uploadSuccess", { message: state.message }));
    }

    if (state.uploadErrors?.length) {
      for (const item of state.uploadErrors) {
        const label = item.filename ?? "Unnamed file";
        toast.warning(`${label}: ${item.message}`);
      }
    }

    sessionStorage.removeItem("resit-scan-failed-toast-shown");
    router.refresh();
  }, [state, defaultTaxYear, form, router, t]);

  function onSubmit(values: ReceiptBulkUploadFormValues) {
    const formData = new FormData();
    for (const file of values.files) {
      formData.append("files", file);
    }
    formData.append("tax_year", String(values.tax_year));

    startTransition(() => {
      submitAction(formData);
    });
  }

  function removeFile(index: number) {
    const nextFiles = selectedFiles.filter((_, i) => i !== index);
    form.setValue("files", nextFiles, { shouldValidate: true });
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("uploadTitle")}</CardTitle>
        <CardDescription>
          {t("uploadDescription", { max: RECEIPT_UPLOAD_MAX_FILES })}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={form.handleSubmit(onSubmit)}>
          <FieldGroup>
            <Controller
              name="tax_year"
              control={form.control}
              render={({ field, fieldState }) => (
                <Field data-invalid={!!fieldState.error}>
                  <TaxYearSelect
                    label={tCommon("taxYear")}
                    value={field.value}
                    anchorYear={defaultTaxYear}
                    onValueChange={field.onChange}
                  />
                  <FieldError errors={[fieldState.error]} />
                </Field>
              )}
            />

            <Controller
              name="files"
              control={form.control}
              render={({ field: { onChange, ref, name, onBlur }, fieldState }) => (
                <Field data-invalid={!!fieldState.error}>
                  <FieldLabel htmlFor="receipt-file">{t("uploadFilesLabel")}</FieldLabel>
                  <Input
                    id="receipt-file"
                    ref={ref}
                    name={name}
                    type="file"
                    multiple
                    accept={RECEIPT_UPLOAD_ACCEPT}
                    aria-invalid={!!fieldState.error}
                    onBlur={onBlur}
                    onChange={(event) => {
                      const fileList = event.target.files;
                      if (!fileList?.length) {
                        onChange([]);
                        return;
                      }
                      onChange(Array.from(fileList));
                    }}
                  />
                  <FieldError errors={[fieldState.error]} />
                </Field>
              )}
            />

            {selectedFiles.length > 0 ? (
              <ul className="space-y-2 rounded-lg border bg-muted/30 p-3">
                {selectedFiles.map((file, index) => (
                  <li
                    key={`${file.name}-${file.size}-${index}`}
                    className="flex items-center gap-3 text-sm"
                  >
                    <FileImage
                      className="size-4 shrink-0 text-muted-foreground"
                      aria-hidden
                    />
                    <span className="min-w-0 flex-1 truncate">{file.name}</span>
                    <span className="shrink-0 text-muted-foreground">
                      {formatFileSize(file.size)}
                    </span>
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      className="size-7 shrink-0"
                      disabled={isPending}
                      aria-label={t("removeFile", { name: file.name })}
                      onClick={() => removeFile(index)}
                    >
                      <X className="size-4" aria-hidden />
                    </Button>
                  </li>
                ))}
              </ul>
            ) : null}

            <Button type="submit" disabled={isPending || selectedFiles.length === 0}>
              {isPending
                ? t("uploading")
                : selectedFiles.length > 1
                  ? t("uploadMultiple", { count: selectedFiles.length })
                  : t("uploadSingle")}
            </Button>
            <p className="text-xs text-muted-foreground">
              {tCommon("taxYear")}: {selectedTaxYear}
            </p>
          </FieldGroup>
        </form>
      </CardContent>
    </Card>
  );
}
