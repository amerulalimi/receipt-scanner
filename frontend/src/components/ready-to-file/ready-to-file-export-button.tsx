"use client";

import { useState, useTransition } from "react";
import { Download } from "lucide-react";

import { Button } from "@/components/ui/button";
import { exportZip } from "@/lib/types/claims";
import { useTranslations } from "@/lib/i18n/use-translations";

type ReadyToFileExportButtonProps = {
  taxYear: number;
};

export function ReadyToFileExportButton({ taxYear }: ReadyToFileExportButtonProps) {
  const t = useTranslations("readyToFile");
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  function handleDownload() {
    setError(null);
    startTransition(async () => {
      try {
        const blob = await exportZip(taxYear);
        const url = URL.createObjectURL(blob);
        const anchor = document.createElement("a");
        anchor.href = url;
        anchor.download = `ResitCukai_BE_${taxYear}.zip`;
        anchor.click();
        URL.revokeObjectURL(url);
      } catch {
        setError(t("exportFailed"));
      }
    });
  }

  return (
    <div className="space-y-2">
      <Button
        type="button"
        variant="outline"
        onClick={handleDownload}
        disabled={isPending}
        className="print:hidden"
      >
        <Download className="size-4" aria-hidden />
        {isPending ? t("exportingZip") : t("downloadZip")}
      </Button>
      {error ? (
        <p role="alert" className="text-sm text-destructive">
          {error}
        </p>
      ) : null}
    </div>
  );
}
