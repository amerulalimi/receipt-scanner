"use client";

import { LogOutIcon } from "lucide-react";
import { useTransition } from "react";

import { logoutAction } from "@/actions/auth";
import { Button } from "@/components/ui/button";
import { useTranslations } from "@/lib/i18n/use-translations";

type LogoutButtonProps = {
  className?: string;
  showIcon?: boolean;
};

export function LogoutButton({ className, showIcon = true }: LogoutButtonProps) {
  const t = useTranslations("nav");
  const [isPending, startTransition] = useTransition();

  return (
    <Button
      type="button"
      variant="outline"
      size="sm"
      className={className}
      disabled={isPending}
      onClick={() => {
        startTransition(() => {
          void logoutAction();
        });
      }}
    >
      {showIcon ? <LogOutIcon className="size-4" /> : null}
      {isPending ? `${t("logout")}…` : t("logout")}
    </Button>
  );
}
