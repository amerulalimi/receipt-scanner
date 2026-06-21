import { getCategoryLabel } from "@/lib/constants/receipts";
import type { ReceiptLineItem } from "@/lib/api/types";
import { formatRinggit } from "@/lib/receipt-format";
import { cn } from "@/lib/utils";

type ReceiptLineItemsSummaryProps = {
  lineItems: ReceiptLineItem[];
  categoryLabels: Record<string, string>;
  title: string;
};

function parseAmount(value: number | string): number {
  if (typeof value === "number") {
    return value;
  }
  const parsed = Number.parseFloat(value);
  return Number.isFinite(parsed) ? parsed : 0;
}

export function ReceiptLineItemsSummary({
  lineItems,
  categoryLabels,
  title,
}: ReceiptLineItemsSummaryProps) {
  if (lineItems.length < 2) {
    return null;
  }

  const selectedTotal = lineItems.reduce(
    (sum, item) =>
      item.included_in_claim ? sum + parseAmount(item.amount) : sum,
    0,
  );

  return (
    <div className="space-y-2 sm:col-span-2 lg:col-span-3">
      <dt className="text-xs text-muted-foreground">{title}</dt>
      <dd className="overflow-x-auto rounded-lg border">
        <table className="w-full min-w-[28rem] text-sm">
          <thead>
            <tr className="border-b bg-muted/30 text-left text-xs text-muted-foreground">
              <th className="px-3 py-2 font-medium">Item</th>
              <th className="px-3 py-2 font-medium">Category</th>
              <th className="px-3 py-2 text-right font-medium">Amount</th>
              <th className="px-3 py-2 font-medium">Claim</th>
            </tr>
          </thead>
          <tbody>
            {lineItems.map((item) => (
              <tr key={item.id} className="border-b border-border/60">
                <td
                  className={cn(
                    "px-3 py-2",
                    !item.included_in_claim && "text-muted-foreground",
                  )}
                >
                  {item.description || "—"}
                </td>
                <td className="px-3 py-2 text-muted-foreground">
                  {getCategoryLabel(item.category, categoryLabels)}
                </td>
                <td className="px-3 py-2 text-right tabular-nums">
                  {formatRinggit(item.amount)}
                </td>
                <td className="px-3 py-2">
                  {item.included_in_claim ? "Included" : "Excluded"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="border-t px-3 py-2 text-sm font-medium">
          Selected claim: {formatRinggit(selectedTotal)}
        </p>
      </dd>
    </div>
  );
}
