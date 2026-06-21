"use client";

import { startTransition, useActionState } from "react";

import {
  resendVerificationAction,
  type ResendVerificationActionState,
} from "@/actions/auth";
import { Button } from "@/components/ui/button";
import { useTranslations } from "@/lib/i18n/use-translations";

const initialState: ResendVerificationActionState = {};

async function resendVerificationFormAction(
  _prevState: ResendVerificationActionState,
): Promise<ResendVerificationActionState> {
  void _prevState;
  return resendVerificationAction();
}

type EmailVerificationBannerProps = {
  email: string;
};

export function EmailVerificationBanner({ email }: EmailVerificationBannerProps) {
  const t = useTranslations("auth");
  const [state, action, isPending] = useActionState(
    resendVerificationFormAction,
    initialState,
  );

  return (
    <div className="rounded-lg border border-amber-500/40 bg-amber-500/10 px-4 py-3 text-sm">
      <p className="font-medium text-amber-950 dark:text-amber-100">
        {t("verifyEmailPendingTitle")}
      </p>
      <p className="mt-1 text-amber-900/90 dark:text-amber-100/90">
        {t("verifyEmailPendingHint", { email })}
      </p>
      {state.error ? (
        <p className="mt-2 text-destructive">{state.error}</p>
      ) : null}
      {state.success && state.message ? (
        <p className="mt-2 text-emerald-700 dark:text-emerald-300">
          {state.message}
        </p>
      ) : null}
      <Button
        type="button"
        variant="outline"
        size="sm"
        className="mt-3"
        disabled={isPending}
        onClick={() => {
          startTransition(() => action());
        }}
      >
        {isPending ? t("resendingVerification") : t("resendVerification")}
      </Button>
    </div>
  );
}
