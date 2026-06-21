"use client";

import { parseAsInteger, useQueryState } from "nuqs";

import { TaxYearSelect } from "@/components/shared/tax-year-select";

type DashboardYearFilterProps = {
  defaultYear: number;
  label: string;
};

export function DashboardYearFilter({
  defaultYear,
  label,
}: DashboardYearFilterProps) {
  const [taxYear, setTaxYear] = useQueryState(
    "tax_year",
    parseAsInteger.withDefault(defaultYear),
  );

  return (
    <TaxYearSelect
      label={label}
      value={taxYear}
      anchorYear={defaultYear}
      onValueChange={(year) => {
        void setTaxYear(year);
      }}
    />
  );
}
