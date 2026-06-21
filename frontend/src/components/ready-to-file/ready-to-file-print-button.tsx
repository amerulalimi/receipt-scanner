"use client";

import { PrinterIcon } from "lucide-react";

import { Button } from "@/components/ui/button";
import { useTranslations } from "@/lib/i18n/use-translations";

export function ReadyToFilePrintButton() {
  const t = useTranslations("readyToFile");

  return (
    <Button type="button" variant="outline" onClick={() => window.print()}>
      <PrinterIcon className="mr-2 size-4" />
      {t("printChecklist")}
    </Button>
  );
}
