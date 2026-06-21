"use client";

import { parseAsInteger, parseAsString, useQueryStates } from "nuqs";

import { FilterSelect } from "@/components/shared/filter-select";
import {
  getReceiptSortLabels,
  getReceiptStatusLabels,
} from "@/lib/constants/receipts";
import { getTaxYearOptions } from "@/lib/tax-year";
import { useTranslations } from "@/lib/i18n/use-translations";
import {
  RECEIPT_SORT_OPTIONS,
  RECEIPT_STATUSES,
} from "@/lib/validations/receipt";

const ALL_VALUE = "all";

const receiptFilterParsers = {
  page: parseAsInteger.withDefault(1),
  category: parseAsString,
  status: parseAsString,
  sort: parseAsString.withDefault("created_at:desc"),
  tax_year: parseAsInteger,
};

type CategoryOption = {
  value: string;
  label: string;
};

type ReceiptsFiltersProps = {
  categoryOptions: CategoryOption[];
  defaultTaxYear: number;
};

export function ReceiptsFilters({
  categoryOptions,
  defaultTaxYear,
}: ReceiptsFiltersProps) {
  const t = useTranslations("receipts");
  const tCommon = useTranslations("common");
  const sortLabels = getReceiptSortLabels(t);
  const statusLabels = getReceiptStatusLabels(t);
  const [filters, setFilters] = useQueryStates(receiptFilterParsers);
  const taxYearOptions = [
    { value: ALL_VALUE, label: tCommon("allYears") },
    ...getTaxYearOptions(defaultTaxYear).map((year) => ({
      value: String(year),
      label: String(year),
    })),
  ];

  return (
    <div className="flex flex-wrap items-end gap-3">
      <FilterSelect
        label={t("filterTaxYear")}
        value={
          filters.tax_year ? String(filters.tax_year) : ALL_VALUE
        }
        onValueChange={(value) => {
          void setFilters({
            tax_year:
              !value || value === ALL_VALUE
                ? null
                : Number.parseInt(value, 10),
            page: 1,
          });
        }}
        options={taxYearOptions}
      />

      <FilterSelect
        label={t("filterCategory")}
        value={filters.category ?? ALL_VALUE}
        onValueChange={(value) => {
          void setFilters({
            category: !value || value === ALL_VALUE ? null : value,
            page: 1,
          });
        }}
        options={[
          { value: ALL_VALUE, label: t("allCategories") },
          ...categoryOptions,
        ]}
      />

      <FilterSelect
        label={t("filterStatus")}
        value={filters.status ?? ALL_VALUE}
        onValueChange={(value) => {
          void setFilters({
            status: !value || value === ALL_VALUE ? null : value,
            page: 1,
          });
        }}
        options={[
          { value: ALL_VALUE, label: t("allStatuses") },
          ...RECEIPT_STATUSES.map((key) => ({
            value: key,
            label: statusLabels[key] ?? key,
          })),
        ]}
      />

      <FilterSelect
        label={t("filterSort")}
        value={filters.sort}
        onValueChange={(value) => {
          void setFilters({ sort: value ?? "created_at:desc" });
        }}
        options={RECEIPT_SORT_OPTIONS.map((key) => ({
          value: key,
          label: sortLabels[key] ?? key,
        }))}
      />
    </div>
  );
}

export { receiptFilterParsers };
