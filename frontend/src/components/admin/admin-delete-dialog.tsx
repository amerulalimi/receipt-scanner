"use client";

import { useRouter } from "next/navigation";
import { startTransition, useActionState, useEffect, useState } from "react";

import type { AdminDirectoryActionState } from "@/actions/admin-directory";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

type AdminDeleteDialogProps = {
  id: string;
  label: string;
  title: string;
  description: string;
  confirmLabel: string;
  action: (
    prevState: AdminDirectoryActionState,
    formData: FormData,
  ) => Promise<AdminDirectoryActionState>;
  initialState: AdminDirectoryActionState;
};

export function AdminDeleteDialog({
  id,
  label,
  title,
  description,
  confirmLabel,
  action,
  initialState,
}: AdminDeleteDialogProps) {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [state, submitAction, isPending] = useActionState(action, initialState);

  useEffect(() => {
    if (state.success) {
      router.refresh();
    }
  }, [state.success, router]);

  function handleConfirm() {
    const formData = new FormData();
    formData.set("id", id);
    startTransition(() => {
      submitAction(formData);
    });
    setOpen(false);
  }

  return (
    <>
      <Button
        type="button"
        variant="destructive"
        size="sm"
        onClick={() => setOpen(true)}
        disabled={isPending}
      >
        {label}
      </Button>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{title}</DialogTitle>
            <DialogDescription>{description}</DialogDescription>
          </DialogHeader>
          {state.error ? (
            <p className="text-sm text-destructive" role="alert">
              {state.error}
            </p>
          ) : null}
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => setOpen(false)}>
              Cancel
            </Button>
            <Button
              type="button"
              variant="destructive"
              disabled={isPending}
              onClick={handleConfirm}
            >
              {isPending ? "Processing…" : confirmLabel}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
