"use client";

import { parseAsInteger, useQueryState } from "nuqs";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useTranslations } from "@/lib/i18n/use-translations";
import { DASHBOARD_RECEIPT_HISTORY_LIMITS } from "@/lib/validations/receipt";

const parseHistoryLimit = parseAsInteger.withDefault(10);

type ReceiptHistoryLimitSelectProps = {
  value: number;
};

export function ReceiptHistoryLimitSelect({
  value,
}: ReceiptHistoryLimitSelectProps) {
  const t = useTranslations("common");
  const [, setHistoryLimit] = useQueryState("history_limit", parseHistoryLimit);
  const options = DASHBOARD_RECEIPT_HISTORY_LIMITS.map((limit) => ({
    value: String(limit),
    label: String(limit),
  }));

  return (
    <div className="space-y-1.5">
      <p className="text-xs font-medium text-muted-foreground">{t("show")}</p>
      <Select
        value={String(value)}
        onValueChange={(nextValue) => {
          if (!nextValue) {
            return;
          }

          const parsed = Number.parseInt(nextValue, 10);
          if (
            DASHBOARD_RECEIPT_HISTORY_LIMITS.includes(
              parsed as (typeof DASHBOARD_RECEIPT_HISTORY_LIMITS)[number],
            )
          ) {
            void setHistoryLimit(parsed);
          }
        }}
        items={options}
      >
        <SelectTrigger className="w-[100px]">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {options.map((option) => (
            <SelectItem key={option.value} value={option.value}>
              {option.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}
