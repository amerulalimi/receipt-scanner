"use client";

import { QrUploadDialog } from "@/components/receipts/qr-upload-dialog";
import { ReceiptUploadDialog } from "@/components/receipts/receipt-upload-dialog";

type ReceiptUploadActionsProps = {
  defaultTaxYear: number;
};

export function ReceiptUploadActions({
  defaultTaxYear,
}: ReceiptUploadActionsProps) {
  return (
    <div className="flex flex-wrap items-center gap-2">
      <ReceiptUploadDialog defaultTaxYear={defaultTaxYear} />
      <QrUploadDialog defaultTaxYear={defaultTaxYear} />
    </div>
  );
}
