"use client";

import { QRCodeSVG } from "qrcode.react";
import { useRouter } from "next/navigation";
import { useCallback, useState, useTransition } from "react";
import { Camera, Link2, RefreshCw } from "lucide-react";

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
import { useUploadSessionWebSocket } from "@/hooks/use-upload-session-ws";
import type { UploadSessionCreateData } from "@/lib/api/types";
import { formatCountdown } from "@/lib/upload-session-utils";
import { useTranslations } from "@/lib/i18n/use-translations";

export function QrUploadSession({
  selectedTaxYear,
}: {
  selectedTaxYear: number;
}) {
  const t = useTranslations("dashboard");
  const router = useRouter();
  const [session, setSession] = useState<UploadSessionCreateData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [wsConnected, setWsConnected] = useState(false);
  const [warnSeconds, setWarnSeconds] = useState<number | null>(null);
  const [isCreating, startCreateTransition] = useTransition();

  const startSession = useCallback(() => {
    setError(null);
    setStatusMessage(null);
    setWarnSeconds(null);
    setWsConnected(false);

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

  const handleSessionClosed = useCallback(
    (uploadsCount: number, totalAmount: number) => {
      setStatusMessage(
        `Session complete — ${uploadsCount} receipt(s) (RM ${totalAmount.toFixed(2)}).`,
      );
      setSession(null);
      setWsConnected(false);
      void revalidateDashboardAction();
      router.refresh();
    },
    [router],
  );

  const handleSessionExpired = useCallback(() => {
      setStatusMessage("Session expired. Generating new QR code...");
      startSession();
    },
    [startSession],
  );

  useUploadSessionWebSocket({
    token: session?.token ?? null,
    enabled: !!session,
    onSubscribed: () => setWsConnected(true),
    onReceiptAdded: () => {
      setStatusMessage("Receipt processed successfully.");
      void revalidateDashboardAction();
      router.refresh();
    },
    onReceiptFailed: (_jobId, reason) => {
      setError(reason);
    },
    onSessionWarned: (secondsRemaining) => setWarnSeconds(secondsRemaining),
    onSessionExpired: handleSessionExpired,
    onSessionClosed: handleSessionClosed,
    onError: (message) => setError(message),
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Camera className="size-5" aria-hidden />
          Upload from Phone
        </CardTitle>
        <CardDescription>
          Scan the QR code with your phone to capture receipts directly from the camera.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
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
            {isCreating ? "Generating QR…" : "Use phone camera"}
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
              <p className="text-muted-foreground">
                Scan this QR code with your phone, or share the link below.
              </p>

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
                  Inactivity timeout:{" "}
                  <span className="font-medium text-foreground">
                    {formatCountdown(session.inactivity_timeout)}
                  </span>
                </li>
                <li>
                  Connection status:{" "}
                  <span className="font-medium text-foreground">
                    {wsConnected ? "Connected" : "Connecting…"}
                  </span>
                </li>
                {warnSeconds !== null ? (
                  <li className="text-amber-600 dark:text-amber-400">
                    Warning: session expires in {formatCountdown(warnSeconds)}
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
                Generate new QR code
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
