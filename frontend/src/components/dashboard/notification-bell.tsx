"use client";

import { AlertTriangleIcon, BellIcon, InfoIcon, XIcon } from "lucide-react";
import Link from "next/link";
import type { Route } from "next";
import { startTransition, useActionState } from "react";

import { dismissNotificationAction } from "@/actions/notifications";
import { initialDismissNotificationState } from "@/actions/notifications.types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import type { NotificationItem } from "@/lib/api/types";
import { useTranslations } from "@/lib/i18n/use-translations";
import { cn } from "@/lib/utils";

type NotificationBellProps = {
  notifications: NotificationItem[];
};

export function NotificationBell({ notifications }: NotificationBellProps) {
  const t = useTranslations("notifications");
  const [, dismissAction, isPending] = useActionState(
    dismissNotificationAction,
    initialDismissNotificationState,
  );

  function dismissNotification(notificationId: string) {
    const formData = new FormData();
    formData.set("notification_id", notificationId);
    startTransition(() => {
      dismissAction(formData);
    });
  }

  return (
    <Popover>
      <PopoverTrigger
        render={
          <Button
            type="button"
            variant="ghost"
            size="icon-sm"
            className="relative"
            aria-label={t("panelTitle")}
          >
            <BellIcon className="size-4" />
            {notifications.length > 0 ? (
              <Badge
                variant="destructive"
                className="absolute -right-1 -top-1 flex size-4 items-center justify-center rounded-full p-0 text-[10px]"
              >
                {notifications.length}
              </Badge>
            ) : null}
          </Button>
        }
      />
      <PopoverContent align="end" className="w-80 p-0">
        <div className="border-b px-4 py-3">
          <p className="text-sm font-medium">{t("panelTitle")}</p>
        </div>
        {notifications.length === 0 ? (
          <p className="px-4 py-6 text-center text-sm text-muted-foreground">
            {t("emptyState")}
          </p>
        ) : (
          <ul className="max-h-80 overflow-y-auto">
            {notifications.map((item) => (
              <li
                key={item.id}
                className={cn(
                  "flex gap-3 border-b px-4 py-3 text-sm last:border-b-0",
                  item.severity === "warning" && "bg-amber-500/5",
                )}
              >
                {item.severity === "warning" ? (
                  <AlertTriangleIcon className="mt-0.5 size-4 shrink-0 text-amber-500" />
                ) : (
                  <InfoIcon className="mt-0.5 size-4 shrink-0 text-primary" />
                )}
                <div className="min-w-0 flex-1 space-y-1">
                  <p className="font-medium">{item.title_my}</p>
                  <p className="text-muted-foreground">{item.message_my}</p>
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
              </li>
            ))}
          </ul>
        )}
      </PopoverContent>
    </Popover>
  );
}
