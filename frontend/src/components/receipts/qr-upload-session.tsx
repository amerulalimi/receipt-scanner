"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState, useTransition } from "react";
import { Camera, Link2, RefreshCw } from "lucide-react";
import { QRCodeSVG } from "qrcode.react";

import {
  createUploadSessionAction,
  revalidateDashboardAction,
} from "@/actions/upload-session";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useReceiptSync } from "@/hooks/use-receipt-sync";
import type { UploadSessionCreateData } from "@/lib/api/types";
import { formatCountdown } from "@/lib/upload-session-utils";
import { useTranslations } from "@/lib/i18n/use-translations";

type QrUploadSessionProps = {
  selectedTaxYear: number;
  variant?: "card" | "plain";
  autoStart?: boolean;
};

export function QrUploadSession({
  selectedTaxYear,
  variant = "card",
  autoStart = false,
}: QrUploadSessionProps) {
  const t = useTranslations("dashboard");
  const router = useRouter();
  const [session, setSession] = useState<UploadSessionCreateData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [isCreating, startCreateTransition] = useTransition();
  const [autoStarted, setAutoStarted] = useState(false);

  const handleReceiptAdded = useCallback(() => {
    setStatusMessage(t("qrReceiptAdded"));
    void revalidateDashboardAction();
    router.refresh();
  }, [router, t]);

  const handleSessionClosed = useCallback(
    (uploadsCount: number, totalAmount: number) => {
      setStatusMessage(
        t("qrSessionComplete", {
          count: uploadsCount,
          amount: totalAmount.toFixed(2),
        }),
      );
      setSession(null);
      void revalidateDashboardAction();
      router.refresh();
    },
    [router, t],
  );

  const startSession = useCallback(() => {
    setError(null);
    setStatusMessage(null);

    startCreateTransition(async () => {
      const result = await createUploadSessionAction(selectedTaxYear);
      if (result.error || !result.data) {
        setError(result.error ?? t("apiUnavailable"));
        setSession(null);
        return;
      }
      setSession(result.data);
    });
  }, [selectedTaxYear, t]);

  const handleSessionExpired = useCallback(() => {
    setStatusMessage(t("qrSessionExpired"));
    startSession();
  }, [startSession, t]);

  useEffect(() => {
    if (autoStart && !autoStarted && !session && !isCreating) {
      setAutoStarted(true);
      startSession();
    }
  }, [autoStart, autoStarted, session, isCreating, startSession]);

  const { isConnected, receivedCount, sessionWarning } = useReceiptSync({
    uploadSessionToken: session?.token ?? null,
    enabled: !!session,
    onReceiptAdded: handleReceiptAdded,
    onSessionClosed: handleSessionClosed,
    onSessionExpired: handleSessionExpired,
    onError: (message) => setError(message),
  });

  const sessionContent = (
    <div className="space-y-4">
      {error ? (
        <p
          role="alert"
          className="rounded-lg border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive"
        >
          {error}
        </p>
      ) : null}

      {statusMessage ? (
        <p
          role="status"
          className="rounded-lg border border-primary/20 bg-primary/5 px-3 py-2 text-sm text-foreground"
        >
          {statusMessage}
        </p>
      ) : null}

      {!session ? (
        <Button type="button" onClick={startSession} disabled={isCreating}>
          {isCreating ? t("qrGenerating") : t("qrGenerate")}
        </Button>
      ) : (
        <div className="flex flex-col items-center gap-4 sm:flex-row sm:items-start">
          <div className="rounded-xl border bg-white p-4">
            <QRCodeSVG
              value={session.qr_data}
              size={200}
              level="M"
              includeMargin
              aria-label="QR code for receipt upload"
            />
          </div>

          <div className="space-y-3 text-sm">
            <p className="text-muted-foreground">{t("qrDescription")}</p>

            {receivedCount > 0 ? (
              <p className="font-medium text-foreground">
                {t("qrReceivedCount", { count: receivedCount })}
              </p>
            ) : null}

            <div className="flex items-start gap-2 rounded-lg border bg-muted/40 p-3">
              <Link2 className="mt-0.5 size-4 shrink-0 text-muted-foreground" />
              <a
                href={session.upload_url}
                target="_blank"
                rel="noopener noreferrer"
                className="break-all text-primary underline-offset-4 hover:underline"
              >
                {session.upload_url}
              </a>
            </div>

            <ul className="space-y-1 text-muted-foreground">
              <li>
                {t("qrExpiresInLabel")}:{" "}
                <span className="font-medium text-foreground">
                  {formatCountdown(session.inactivity_timeout)}
                </span>
              </li>
              <li>
                {t("qrConnectionStatus")}:{" "}
                <span className="font-medium text-foreground">
                  {isConnected ? t("qrConnected") : t("qrWaiting")}
                </span>
              </li>
              {sessionWarning ? (
                <li className="text-amber-600 dark:text-amber-400">
                  {t("qrExpiresIn", {
                    time: formatCountdown(sessionWarning.secondsRemaining),
                  })}
                </li>
              ) : null}
            </ul>

            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={startSession}
              disabled={isCreating}
            >
              <RefreshCw className="size-4" aria-hidden />
              {t("qrRegenerate")}
            </Button>
          </div>
        </div>
      )}
    </div>
  );

  if (variant === "plain") {
    return sessionContent;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Camera className="size-5" aria-hidden />
          {t("qrTitle")}
        </CardTitle>
        <CardDescription>{t("qrDescription")}</CardDescription>
      </CardHeader>
      <CardContent>{sessionContent}</CardContent>
    </Card>
  );
}
