"use client";

import { useId, useState } from "react";
import { UploadIcon } from "lucide-react";

import { ReceiptUploadForm } from "@/components/receipts/receipt-upload-form";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { RECEIPT_UPLOAD_MAX_FILES } from "@/lib/constants/receipts";
import { useTranslations } from "@/lib/i18n/use-translations";

type ReceiptUploadDialogProps = {
  defaultTaxYear: number;
};

export function ReceiptUploadDialog({ defaultTaxYear }: ReceiptUploadDialogProps) {
  const [open, setOpen] = useState(false);
  const fileInputId = useId();
  const t = useTranslations("dashboard");
  const tCommon = useTranslations("common");

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger
        render={
          <Button size="sm">
            <UploadIcon className="size-4" aria-hidden />
            {tCommon("uploadReceipt")}
          </Button>
        }
      />
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{t("uploadTitle")}</DialogTitle>
          <DialogDescription>
            {t("uploadDescription", { max: RECEIPT_UPLOAD_MAX_FILES })}
          </DialogDescription>
        </DialogHeader>
        <ReceiptUploadForm
          defaultTaxYear={defaultTaxYear}
          variant="plain"
          fileInputId={fileInputId}
          onSuccess={() => setOpen(false)}
        />
      </DialogContent>
    </Dialog>
  );
}
