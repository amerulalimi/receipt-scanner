"use client";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

type FilterSelectOption = {
  value: string;
  label: string;
};

type FilterSelectProps = {
  label: string;
  value: string;
  onValueChange: (value: string | null) => void;
  options: FilterSelectOption[];
  triggerClassName?: string;
};

export function FilterSelect({
  label,
  value,
  onValueChange,
  options,
  triggerClassName,
}: FilterSelectProps) {
  return (
    <div className="space-y-1.5">
      <p className="text-xs font-medium text-muted-foreground">{label}</p>
      <Select value={value} onValueChange={onValueChange} items={options}>
        <SelectTrigger className={triggerClassName ?? "min-w-[160px]"}>
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
