export type ApiAmount = number | string | null | undefined;

export function parseApiAmount(value: ApiAmount): number | null {
  if (value === null || value === undefined) {
    return null;
  }

  if (typeof value === "number") {
    return Number.isFinite(value) ? value : null;
  }

  const parsed = Number.parseFloat(value);
  return Number.isFinite(parsed) ? parsed : null;
}

export function formatAmountForInput(value: ApiAmount): string {
  const amount = parseApiAmount(value);
  return amount === null ? "" : amount.toFixed(2);
}

export function formatRinggit(value: ApiAmount): string {
  const amount = parseApiAmount(value);
  if (amount === null) {
    return "—";
  }

  return new Intl.NumberFormat("ms-MY", {
    style: "currency",
    currency: "MYR",
    minimumFractionDigits: 2,
  }).format(amount);
}
export function formatReceiptDate(value: string | null): string {
  if (!value) {
    return "—";
  }

  return new Intl.DateTimeFormat("ms-MY", {
    dateStyle: "medium",
  }).format(new Date(value));
}

export function getStatusBadgeClass(status: string): string {
  switch (status) {
    case "approved":
      return "rounded-full bg-emerald-500/10 px-2 py-0.5 text-xs font-medium text-emerald-700 dark:text-emerald-300";
    case "rejected":
      return "rounded-full bg-destructive/10 px-2 py-0.5 text-xs font-medium text-destructive";
    case "flagged":
      return "rounded-full border border-amber-500/40 bg-amber-500/10 px-2 py-0.5 text-xs font-medium text-amber-900 dark:text-amber-100";
    case "duplicate":
      return "rounded-full bg-secondary px-2 py-0.5 text-xs font-medium text-secondary-foreground";
    default:
      return "rounded-full border px-2 py-0.5 text-xs font-medium text-muted-foreground";
  }
}
