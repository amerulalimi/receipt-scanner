"use client";

import { BellIcon, XIcon } from "lucide-react";
import Link from "next/link";
import type { Route } from "next";
import { startTransition, useActionState } from "react";

import { dismissNotificationAction } from "@/actions/notifications";
import { initialDismissNotificationState } from "@/actions/notifications.types";
import { Button } from "@/components/ui/button";
import type { NotificationItem } from "@/lib/api/types";
import { useTranslations } from "@/lib/i18n/use-translations";
import type { Locale } from "@/lib/i18n/locales";
import { cn } from "@/lib/utils";

export function SmartRemindersPanel({
  notifications,
}: {
  notifications: NotificationItem[];
  locale?: Locale;
}) {
  const t = useTranslations("notifications");
  const [, dismissAction, isPending] = useActionState(
    dismissNotificationAction,
    initialDismissNotificationState,
  );

  if (notifications.length === 0) {
    return null;
  }

  function dismissNotification(notificationId: string) {
    const formData = new FormData();
    formData.set("notification_id", notificationId);
    startTransition(() => {
      dismissAction(formData);
    });
  }

  return (
    <section className="space-y-3">
      <div className="flex items-center gap-2">
        <BellIcon className="size-4 text-muted-foreground" />
        <h2 className="text-sm font-medium">{t("panelTitle")}</h2>
      </div>

      <div className="space-y-2">
        {notifications.map((item) => {
          const title = item.title_en;
          const message = item.message_en;

          return (
            <div
              key={item.id}
              className={cn(
                "flex gap-3 rounded-lg border px-4 py-3 text-sm",
                item.severity === "warning"
                  ? "border-amber-500/40 bg-amber-500/10 text-amber-950 dark:text-amber-100"
                  : "border-primary/20 bg-primary/5",
              )}
            >
              <div className="min-w-0 flex-1 space-y-1">
                <p className="font-medium">{title}</p>
                <p className="text-muted-foreground">{message}</p>
                {item.action_href ? (
                  <Link
                    href={item.action_href as Route}
                    className="text-xs font-medium text-primary underline-offset-4 hover:underline"
                  >
                    {t("viewAction")}
                  </Link>
                ) : null}
              </div>
              <Button
                type="button"
                variant="ghost"
                size="icon-sm"
                disabled={isPending}
                aria-label={t("dismiss")}
                onClick={() => dismissNotification(item.id)}
              >
                <XIcon className="size-4" />
              </Button>
            </div>
          );
        })}
      </div>
    </section>
  );
}
