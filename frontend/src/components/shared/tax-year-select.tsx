"use client";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { getTaxYearOptions } from "@/lib/tax-year";

type TaxYearSelectProps = {
  value: number;
  onValueChange: (value: number) => void;
  label?: string;
  triggerClassName?: string;
  anchorYear?: number;
};

export function TaxYearSelect({
  value,
  onValueChange,
  label,
  triggerClassName,
  anchorYear,
}: TaxYearSelectProps) {
  const years = getTaxYearOptions(anchorYear ?? value);
  const options = years.map((year) => ({
    value: String(year),
    label: String(year),
  }));

  return (
    <div className="space-y-1.5">
      {label ? (
        <p className="text-xs font-medium text-muted-foreground">{label}</p>
      ) : null}
      <Select
        value={String(value)}
        onValueChange={(nextValue) => {
          if (!nextValue) {
            return;
          }

          const parsed = Number.parseInt(nextValue, 10);
          if (!Number.isNaN(parsed)) {
            onValueChange(parsed);
          }
        }}
        items={options}
      >
        <SelectTrigger className={triggerClassName ?? "min-w-[120px]"}>
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
