"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { Camera, CheckCircle2, Clock } from "lucide-react";
import {
  startTransition,
  useActionState,
  useCallback,
  useEffect,
  useRef,
  useState,
  useTransition,
} from "react";
import { Controller, useForm } from "react-hook-form";

import {
  mobileCloseSessionAction,
  mobileKeepAliveAction,
  mobileUploadAction,
  mobileValidateSessionAction,
} from "@/actions/upload-session";
import { initialMobileUploadState } from "@/actions/upload-session.types";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";
import type { UploadSessionValidateData } from "@/lib/api/types";
import { formatCountdown } from "@/lib/upload-session-utils";
import {
  receiptUploadSchema,
  type ReceiptUploadFormValues,
} from "@/lib/validations/receipt";

type MobileUploadSessionProps = {
  token: string;
  initialData: UploadSessionValidateData;
};

const POLL_INTERVAL_MS = 30_000;

export function MobileUploadSession({
  token,
  initialData,
}: MobileUploadSessionProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploadsCount, setUploadsCount] = useState(initialData.uploads_so_far);
  const [remainingSeconds, setRemainingSeconds] = useState(
    initialData.inactivity_remaining,
  );
  const [isExpired, setIsExpired] = useState(false);
  const [isDone, setIsDone] = useState(false);
  const [doneMessage, setDoneMessage] = useState<string | null>(null);
  const [localError, setLocalError] = useState<string | null>(null);
  const [showUploadAgain, setShowUploadAgain] = useState(false);
  const [isKeepingAlive, startKeepAlive] = useTransition();
  const [isClosing, startClose] = useTransition();

  const [state, submitAction, isPending] = useActionState(
    mobileUploadAction,
    initialMobileUploadState,
  );

  const form = useForm<ReceiptUploadFormValues>({
    resolver: zodResolver(receiptUploadSchema),
    defaultValues: {},
  });

  const pollSession = useCallback(async () => {
    const result = await mobileValidateSessionAction(token);
    if (result.error) {
      setIsExpired(true);
      return;
    }
    if (result.valid) {
      setUploadsCount(result.uploadsSoFar);
      setRemainingSeconds(result.inactivityRemaining);
      setIsExpired(false);
    }
  }, [token]);

  useEffect(() => {
    if (remainingSeconds <= 0) {
      setIsExpired(true);
      return;
    }

    const timer = window.setInterval(() => {
      setRemainingSeconds((current) => {
        if (current <= 1) {
          setIsExpired(true);
          return 0;
        }
        return current - 1;
      });
    }, 1000);

    return () => window.clearInterval(timer);
  }, [remainingSeconds]);

  useEffect(() => {
    const pollTimer = window.setInterval(() => {
      void pollSession();
    }, POLL_INTERVAL_MS);

    return () => window.clearInterval(pollTimer);
  }, [pollSession]);

  useEffect(() => {
    if (!state.fieldErrors) {
      return;
    }

    for (const [field, messages] of Object.entries(state.fieldErrors)) {
      if (messages[0]) {
        form.setError(field as keyof ReceiptUploadFormValues, {
          message: messages[0],
        });
      }
    }
  }, [state.fieldErrors, form]);

  useEffect(() => {
    if (state.error) {
      setLocalError(state.error);
    }
  }, [state.error]);

  useEffect(() => {
    if (!state.success) {
      return;
    }

    setLocalError(null);
    setUploadsCount((count) => count + 1);
    setShowUploadAgain(true);
    if (state.inactivityRemaining !== undefined) {
      setRemainingSeconds(state.inactivityRemaining);
      setIsExpired(false);
    }

    form.reset();
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  }, [state.success, state.inactivityRemaining, form]);

  const openCamera = useCallback(() => {
    setShowUploadAgain(false);
    fileInputRef.current?.click();
  }, []);

  function onSubmit(values: ReceiptUploadFormValues) {
    const formData = new FormData();
    formData.set("token", token);
    formData.set("file", values.file);

    startTransition(() => {
      submitAction(formData);
    });
  }

  function handleKeepAlive() {
    startKeepAlive(async () => {
      const result = await mobileKeepAliveAction(token);
      if (result.error || result.inactivityRemaining === undefined) {
        setLocalError(result.error ?? "Tidak dapat kekalkan sesi.");
        return;
      }
      setRemainingSeconds(result.inactivityRemaining);
      setIsExpired(false);
      setLocalError(null);
    });
  }

  function handleDone() {
    startClose(async () => {
      const result = await mobileCloseSessionAction(token);
      if (
        result.error ||
        result.uploadsCount === undefined ||
        result.message === undefined
      ) {
        setLocalError(result.error ?? "Tidak dapat menutup sesi.");
        return;
      }
      setIsDone(true);
      setDoneMessage(result.message);
      setUploadsCount(result.uploadsCount);
    });
  }

  if (isDone) {
    return (
      <main className="mx-auto flex min-h-dvh max-w-md flex-col items-center justify-center gap-4 px-4 py-8">
        <CheckCircle2 className="size-16 text-primary" aria-hidden />
        <h1 className="text-center text-2xl font-semibold">Terima kasih!</h1>
        <p className="text-center text-muted-foreground">
          {doneMessage ?? "Sambung di desktop anda."}
        </p>
        <p className="text-sm text-muted-foreground">
          {uploadsCount} resit dimuat naik
        </p>
      </main>
    );
  }

  if (isExpired) {
    return (
      <main className="mx-auto flex min-h-dvh max-w-md flex-col items-center justify-center gap-4 px-4 py-8 text-center">
        <Clock className="size-12 text-muted-foreground" aria-hidden />
        <h1 className="text-xl font-semibold">Sesi tamat</h1>
        <p className="text-muted-foreground">
          Sila imbas QR baru di desktop anda.
        </p>
      </main>
    );
  }

  const isWarning = remainingSeconds <= 120;
  const progressValue = Math.min(
    100,
    Math.max(0, (remainingSeconds / initialData.inactivity_remaining) * 100),
  );

  return (
    <main className="mx-auto min-h-dvh max-w-md px-4 py-6">
      <header className="mb-6 space-y-1 text-center">
        <p className="text-sm text-muted-foreground">Muat naik untuk</p>
        <h1 className="text-2xl font-semibold">{initialData.user_name}</h1>
      </header>

      {isWarning ? (
        <Alert className="mb-4 border-amber-500/40 bg-amber-500/10">
          <AlertTitle>Sesi akan tamat</AlertTitle>
          <AlertDescription className="space-y-3">
            <p>Sesi akan tamat dalam {formatCountdown(remainingSeconds)}.</p>
            <Button
              type="button"
              variant="outline"
              size="sm"
              disabled={isKeepingAlive}
              onClick={handleKeepAlive}
            >
              {isKeepingAlive ? "..." : "Kekalkan Aktif"}
            </Button>
          </AlertDescription>
        </Alert>
      ) : null}

      <Card>
        <CardHeader className="text-center">
          <CardTitle>Muat Naik Resit</CardTitle>
          <CardDescription>
            Ambil gambar resit anda menggunakan kamera telefon.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between rounded-lg border bg-muted/30 px-4 py-3 text-sm">
            <span className="text-muted-foreground">Resit dimuat naik</span>
            <span className="font-semibold">{uploadsCount} resit dimuat naik</span>
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Masa berbaki</span>
              <span className="font-mono font-semibold">
                {formatCountdown(remainingSeconds)}
              </span>
            </div>
            <Progress value={progressValue} />
          </div>

          {localError ? (
            <Alert variant="destructive">
              <AlertDescription>{localError}</AlertDescription>
            </Alert>
          ) : null}

          {state.success && state.message ? (
            <Alert>
              <AlertDescription className="space-y-3">
                <p>{state.message}</p>
                {showUploadAgain ? (
                  <Button type="button" variant="outline" onClick={openCamera}>
                    Muat naik lagi?
                  </Button>
                ) : null}
              </AlertDescription>
            </Alert>
          ) : null}

          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <Controller
              name="file"
              control={form.control}
              render={({ field: { onChange, ref, name, onBlur }, fieldState }) => (
                <>
                  <Input
                    ref={(node) => {
                      ref(node);
                      fileInputRef.current = node;
                    }}
                    name={name}
                    type="file"
                    accept="image/*"
                    capture="environment"
                    className="sr-only"
                    aria-invalid={!!fieldState.error}
                    onBlur={onBlur}
                    onChange={(event) => {
                      const file = event.target.files?.[0];
                      if (!file) {
                        return;
                      }
                      onChange(file);
                      form.handleSubmit(onSubmit)();
                    }}
                  />
                  {fieldState.error ? (
                    <p className="text-sm text-destructive">
                      {fieldState.error.message}
                    </p>
                  ) : null}
                </>
              )}
            />

            <Button
              type="button"
              className="h-14 w-full text-base"
              disabled={isPending}
              onClick={openCamera}
            >
              <Camera className="size-5" aria-hidden />
              {isPending ? "Memuat naik…" : "Ambil Gambar"}
            </Button>
          </form>

          <div className="grid grid-cols-2 gap-3">
            <Button
              type="button"
              variant="outline"
              disabled={isKeepingAlive || isPending}
              onClick={handleKeepAlive}
            >
              {isKeepingAlive ? "..." : "Kekalkan Aktif"}
            </Button>
            <Button
              type="button"
              variant="secondary"
              disabled={isClosing || isPending}
              onClick={handleDone}
            >
              {isClosing ? "..." : "Selesai"}
            </Button>
          </div>
        </CardContent>
      </Card>
    </main>
  );
}
