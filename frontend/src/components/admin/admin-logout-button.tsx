"use client";

import { LogOutIcon } from "lucide-react";
import { useTransition } from "react";

import { adminLogoutAction } from "@/actions/admin-auth";
import { Button } from "@/components/ui/button";

type AdminLogoutButtonProps = {
  className?: string;
  showIcon?: boolean;
};

export function AdminLogoutButton({
  className,
  showIcon = true,
}: AdminLogoutButtonProps) {
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
          void adminLogoutAction();
        });
      }}
    >
      {showIcon ? <LogOutIcon className="size-4" /> : null}
      {isPending ? "Log keluar…" : "Log keluar"}
    </Button>
  );
}
