"use client";

import { startTransition, useActionState, useEffect, useState } from "react";

import { revokeSessionAction } from "@/actions/settings";
import { initialSettingsActionState } from "@/actions/settings.types";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { SessionInfo } from "@/lib/api/types";
import { useTranslations } from "@/lib/i18n/use-translations";

function formatDateTime(value: string): string {
  return new Intl.DateTimeFormat("en-MY", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export function SessionsList({ sessions }: { sessions: SessionInfo[] }) {
  const t = useTranslations("settings");
  const [state, submitAction, isPending] = useActionState(
    revokeSessionAction,
    initialSettingsActionState,
  );
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    if (state.error) {
      setMessage(state.error);
      return;
    }
    if (state.success && state.message) {
      setMessage(state.message);
    }
  }, [state.error, state.message, state.success]);

  function revokeSession(sessionId: string) {
    const formData = new FormData();
    formData.set("session_id", sessionId);

    startTransition(() => {
      submitAction(formData);
    });
  }

  function getDeviceLabel(userAgent: string): string {
    if (!userAgent || userAgent === "Unknown device") {
      return t("unknownDevice");
    }
    return userAgent;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("sessionsTitle")}</CardTitle>
        <CardDescription>{t("sessionsDescription")}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {message ? (
          <p
            className={
              state.error
                ? "text-sm text-destructive"
                : "text-sm text-emerald-600"
            }
          >
            {message}
          </p>
        ) : null}

        {sessions.length === 0 ? (
          <p className="text-sm text-muted-foreground">{t("sessionsEmpty")}</p>
        ) : null}

        {sessions.map((session) => (
          <div
            key={session.session_id}
            className="flex flex-col gap-3 rounded-lg border px-3 py-3 sm:flex-row sm:items-start sm:justify-between"
          >
            <div className="min-w-0 space-y-1">
              <div className="flex flex-wrap items-center gap-2">
                <p className="font-medium">{getDeviceLabel(session.user_agent)}</p>
                <span
                  className={
                    session.is_current
                      ? "rounded-full bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary"
                      : "rounded-full border px-2 py-0.5 text-xs font-medium text-muted-foreground"
                  }
                >
                  {session.is_current ? t("sessionCurrent") : t("sessionOther")}
                </span>
              </div>
              <p className="text-sm text-muted-foreground">IP: {session.ip}</p>
              <p className="text-sm text-muted-foreground">
                {t("sessionLoginAt", {
                  date: formatDateTime(session.created_at),
                })}
              </p>
              <p className="text-sm text-muted-foreground">
                {t("sessionLastActive", {
                  date: formatDateTime(session.last_active),
                })}
              </p>
            </div>

            {!session.is_current ? (
              <Button
                type="button"
                variant="outline"
                size="sm"
                disabled={isPending}
                onClick={() => revokeSession(session.session_id)}
              >
                {t("sessionRevoke")}
              </Button>
            ) : null}
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
