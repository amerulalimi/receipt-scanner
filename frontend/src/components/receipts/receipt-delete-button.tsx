"use client";

import { Trash2Icon } from "lucide-react";
import { startTransition, useActionState, useEffect, useState } from "react";

import { deleteReceiptAction } from "@/actions/receipt";
import { initialReceiptDeleteState } from "@/actions/receipt.types";
import { Button } from "@/components/ui/button";

type ReceiptDeleteButtonProps = {
  receiptId: string;
  merchantLabel: string;
};

export function ReceiptDeleteButton({
  receiptId,
  merchantLabel,
}: ReceiptDeleteButtonProps) {
  const [confirming, setConfirming] = useState(false);
  const [state, submitAction, isPending] = useActionState(
    deleteReceiptAction,
    initialReceiptDeleteState,
  );

  useEffect(() => {
    if (state.success) {
      setConfirming(false);
    }
  }, [state.success]);

  if (confirming) {
    return (
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-xs text-muted-foreground">
          Delete &quot;{merchantLabel}&quot;?
        </span>
        <Button
          type="button"
          variant="destructive"
          size="sm"
          disabled={isPending}
          onClick={() => {
            const formData = new FormData();
            formData.set("receipt_id", receiptId);
            startTransition(() => submitAction(formData));
          }}
        >
          {isPending ? "Deleting…" : "Confirm"}
        </Button>
        <Button
          type="button"
          variant="outline"
          size="sm"
          disabled={isPending}
          onClick={() => setConfirming(false)}
        >
          Cancel
        </Button>
        {state.error ? (
          <span className="text-xs text-destructive">{state.error}</span>
        ) : null}
      </div>
    );
  }

  return (
    <Button
      type="button"
      variant="outline"
      size="sm"
      onClick={() => setConfirming(true)}
    >
      <Trash2Icon className="size-4" />
      Delete
    </Button>
  );
}
