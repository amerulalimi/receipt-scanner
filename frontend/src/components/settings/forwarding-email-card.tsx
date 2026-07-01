"use client";

import { useCallback, useState } from "react";
import { Copy } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useTranslations } from "@/lib/i18n/use-translations";

type ForwardingEmailCardProps = {
  forwardingToken: string;
};

export function ForwardingEmailCard({ forwardingToken }: ForwardingEmailCardProps) {
  const t = useTranslations("settings");
  const [copied, setCopied] = useState(false);
  const address = `${forwardingToken}@receipts.resit.my`;

  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(address);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      setCopied(false);
    }
  }, [address]);

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("forwardingTitle")}</CardTitle>
        <CardDescription>{t("forwardingDescription")}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex flex-wrap items-center gap-2">
          <p className="rounded-md border bg-muted/40 px-3 py-2 font-mono text-sm">
            {address}
          </p>
          <Button type="button" variant="outline" size="sm" onClick={handleCopy}>
            <Copy className="size-4" aria-hidden />
            {copied ? t("forwardingCopied") : t("forwardingCopy")}
          </Button>
        </div>
        <p className="text-xs text-muted-foreground">{t("forwardingComingSoon")}</p>
      </CardContent>
    </Card>
  );
}
