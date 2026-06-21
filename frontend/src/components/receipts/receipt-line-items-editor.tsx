"use client";

import { useEffect, useMemo, useState } from "react";

import { getCategoryLabel } from "@/lib/constants/receipts";
import type { ReceiptLineItem } from "@/lib/api/types";
import { useTranslations } from "@/lib/i18n/use-translations";
import { formatRinggit } from "@/lib/receipt-format";
import { cn } from "@/lib/utils";

type ReceiptLineItemsEditorProps = {
  lineItems: ReceiptLineItem[];
  categoryLabels: Record<string, string>;
  disabled?: boolean;
  onChange: (items: ReceiptLineItem[]) => void;
};

function parseAmount(value: number | string): number {
  if (typeof value === "number") {
    return value;
  }
  const parsed = Number.parseFloat(value);
  return Number.isFinite(parsed) ? parsed : 0;
}

export function ReceiptLineItemsEditor({
  lineItems,
  categoryLabels,
  disabled = false,
  onChange,
}: ReceiptLineItemsEditorProps) {
  const t = useTranslations("receipts");
  const [items, setItems] = useState(lineItems);

  useEffect(() => {
    setItems(lineItems);
  }, [lineItems]);

  const selectedTotal = useMemo(
    () =>
      items.reduce(
        (sum, item) =>
          item.included_in_claim ? sum + parseAmount(item.amount) : sum,
        0,
      ),
    [items],
  );

  const receiptTotal = useMemo(
    () => items.reduce((sum, item) => sum + parseAmount(item.amount), 0),
    [items],
  );

  function updateItems(next: ReceiptLineItem[]) {
    setItems(next);
    onChange(next);
  }

  function toggleItem(itemId: string, included: boolean) {
    updateItems(
      items.map((item) =>
        item.id === itemId ? { ...item, included_in_claim: included } : item,
      ),
    );
  }

  if (items.length < 2) {
    return null;
  }

  return (
    <section className="space-y-3 rounded-lg border bg-muted/20 p-3">
      <div className="space-y-1">
        <h3 className="text-sm font-medium">{t("lineItemsTitle")}</h3>
        <p className="text-xs text-muted-foreground">{t("lineItemsDescription")}</p>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full min-w-[28rem] text-sm">
          <thead>
            <tr className="border-b text-left text-xs text-muted-foreground">
              <th className="pb-2 pr-2 font-medium">{t("lineItemsInclude")}</th>
              <th className="pb-2 pr-2 font-medium">{t("lineItemsItem")}</th>
              <th className="pb-2 pr-2 font-medium">{t("category")}</th>
              <th className="pb-2 text-right font-medium">{t("amount")}</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={item.id} className="border-b border-border/60">
                <td className="py-2 pr-2 align-top">
                  <input
                    type="checkbox"
                    className="size-4 rounded border-input accent-primary"
                    checked={item.included_in_claim}
                    disabled={disabled}
                    aria-label={`${t("lineItemsInclude")}: ${item.description}`}
                    onChange={(event) =>
                      toggleItem(item.id, event.target.checked)
                    }
                  />
                </td>
                <td className="py-2 pr-2 align-top">
                  <p
                    className={cn(
                      "font-medium",
                      !item.included_in_claim && "text-muted-foreground",
                    )}
                  >
                    {item.description || "—"}
                  </p>
                  {!item.ai_claimable ? (
                    <p className="text-xs text-muted-foreground">
                      {t("lineItemsAiNotClaimable")}
                    </p>
                  ) : null}
                </td>
                <td className="py-2 pr-2 align-top text-muted-foreground">
                  {getCategoryLabel(item.category, categoryLabels)}
                </td>
                <td className="py-2 text-right align-top tabular-nums">
                  {formatRinggit(item.amount)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="flex flex-wrap justify-between gap-2 text-sm">
        <span className="text-muted-foreground">
          {t("lineItemsReceiptTotal")}: {formatRinggit(receiptTotal)}
        </span>
        <span className="font-medium">
          {t("lineItemsSelectedTotal")}: {formatRinggit(selectedTotal)}
        </span>
      </div>
    </section>
  );
}

export function buildLineItemsPayload(items: ReceiptLineItem[]) {
  return items.map((item) => ({
    id: item.id,
    included_in_claim: item.included_in_claim,
    category: item.category,
  }));
}
