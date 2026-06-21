"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { Camera, CheckCircle2, Clock, Upload } from "lucide-react";
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
} from "@/actions/upload-session";
import { initialMobileUploadState } from "@/actions/upload-session.types";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
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
        setLocalError(result.error ?? "Unable to keep session alive.");
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
        setLocalError(result.error ?? "Unable to close session.");
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
        <h1 className="text-center text-2xl font-semibold">Done!</h1>
        <p className="text-center text-muted-foreground">
          {doneMessage ?? "Continue on your desktop."}
        </p>
        <p className="text-sm text-muted-foreground">
          {uploadsCount} receipt(s) uploaded in this session.
        </p>
      </main>
    );
  }

  if (isExpired) {
    return (
      <main className="mx-auto flex min-h-dvh max-w-md flex-col items-center justify-center gap-4 px-4 py-8 text-center">
        <Clock className="size-12 text-muted-foreground" aria-hidden />
        <h1 className="text-xl font-semibold">Session expired</h1>
        <p className="text-muted-foreground">
          Scan a new QR code on your desktop to continue uploading.
        </p>
      </main>
    );
  }

  const isWarning = remainingSeconds <= 120;

  return (
    <main className="mx-auto min-h-dvh max-w-md px-4 py-6">
      <header className="mb-6 space-y-1 text-center">
        <p className="text-sm text-muted-foreground">Uploading for</p>
        <h1 className="text-2xl font-semibold">{initialData.user_name}</h1>
      </header>

      <Card>
        <CardHeader className="text-center">
          <CardTitle>Capture Receipt</CardTitle>
          <CardDescription>
            Open the camera and take a photo of your receipt.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between rounded-lg border bg-muted/30 px-4 py-3 text-sm">
            <span className="text-muted-foreground">Receipts uploaded</span>
            <span className="font-semibold">{uploadsCount}</span>
          </div>

          <div
            className={`flex items-center justify-between rounded-lg border px-4 py-3 text-sm ${
              isWarning
                ? "border-amber-500/40 bg-amber-500/10 text-amber-700 dark:text-amber-300"
                : "bg-muted/30"
            }`}
          >
            <span>Time remaining</span>
            <span className="font-mono font-semibold">
              {formatCountdown(remainingSeconds)}
            </span>
          </div>

          {localError ? (
            <p
              role="alert"
              className="rounded-lg border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive"
            >
              {localError}
            </p>
          ) : null}

          {state.success && state.message ? (
            <p
              role="status"
              className="rounded-lg border border-primary/20 bg-primary/5 px-3 py-2 text-sm"
            >
              {state.message}
            </p>
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
              {isPending ? "Uploading…" : "Open camera"}
            </Button>
          </form>

          <div className="grid grid-cols-2 gap-3">
            <Button
              type="button"
              variant="outline"
              disabled={isKeepingAlive || isPending}
              onClick={handleKeepAlive}
            >
              <Upload className="size-4" aria-hidden />
              {isKeepingAlive ? "..." : "Keep alive"}
            </Button>
            <Button
              type="button"
              variant="secondary"
              disabled={isClosing || isPending}
              onClick={handleDone}
            >
              {isClosing ? "..." : "Done"}
            </Button>
          </div>
        </CardContent>
      </Card>
    </main>
  );
}
