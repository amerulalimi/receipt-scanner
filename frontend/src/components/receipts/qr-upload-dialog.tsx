"use client";

import { useState } from "react";
import { Camera } from "lucide-react";

import { QrUploadSession } from "@/components/receipts/qr-upload-session";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { useTranslations } from "@/lib/i18n/use-translations";

type QrUploadDialogProps = {
  defaultTaxYear: number;
};

export function QrUploadDialog({ defaultTaxYear }: QrUploadDialogProps) {
  const [open, setOpen] = useState(false);
  const t = useTranslations("dashboard");
  const tCommon = useTranslations("common");

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger
        render={
          <Button variant="outline" size="sm">
            <Camera className="size-4" aria-hidden />
            {tCommon("uploadFromPhone")}
          </Button>
        }
      />
      <DialogContent className="max-w-xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Camera className="size-5" aria-hidden />
            {tCommon("uploadFromPhone")}
          </DialogTitle>
          <DialogDescription>{t("qrDescription")}</DialogDescription>
        </DialogHeader>
        {open ? (
          <QrUploadSession
            selectedTaxYear={defaultTaxYear}
            variant="plain"
            autoStart
          />
        ) : null}
      </DialogContent>
    </Dialog>
  );
}
