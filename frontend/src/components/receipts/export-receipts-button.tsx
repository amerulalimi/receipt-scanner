"use client";

import { Download } from "lucide-react";

import { getExportZipUrl } from "@/lib/api/export-urls";
import { Button } from "@/components/ui/button";
import { useTranslations } from "@/lib/i18n/use-translations";

type ExportReceiptsButtonProps = {
  taxYear: number;
};

export function ExportReceiptsButton({ taxYear }: ExportReceiptsButtonProps) {
  const t = useTranslations("export");

  return (
    <Button variant="outline" size="sm" render={<a href={getExportZipUrl(taxYear)} download />} nativeButton={false}>
      <Download className="size-4" />
      {t("zipButton")}
    </Button>
  );
}
