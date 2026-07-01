"use client";

import { parseAsInteger, parseAsString, useQueryStates } from "nuqs";

import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useTranslations } from "@/lib/i18n/use-translations";

const filterParsers = {
  search: parseAsString.withDefault(""),
  status: parseAsString.withDefault(""),
  page: parseAsInteger.withDefault(1),
};

export function OrgEmployeesToolbar() {
  const t = useTranslations("org");
  const [filters, setFilters] = useQueryStates(filterParsers);

  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
      <div className="flex-1 space-y-1.5">
        <label htmlFor="employee-search" className="text-xs font-medium text-muted-foreground">
          {t("searchEmployees")}
        </label>
        <Input
          id="employee-search"
          value={filters.search}
          placeholder={t("searchEmployeesPlaceholder")}
          onChange={(event) => {
            void setFilters({ search: event.target.value, page: 1 });
          }}
        />
      </div>

      <div className="space-y-1.5">
        <p className="text-xs font-medium text-muted-foreground">{t("statusFilter")}</p>
        <Select
          value={filters.status || "all"}
          onValueChange={(value) => {
            void setFilters({
              status: value === "all" ? "" : value,
              page: 1,
            });
          }}
          items={[
            { value: "all", label: t("statusAll") },
            { value: "active", label: t("statusActive") },
            { value: "inactive", label: t("statusInactive") },
          ]}
        >
          <SelectTrigger className="min-w-[160px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">{t("statusAll")}</SelectItem>
            <SelectItem value="active">{t("statusActive")}</SelectItem>
            <SelectItem value="inactive">{t("statusInactive")}</SelectItem>
          </SelectContent>
        </Select>
      </div>
    </div>
  );
}
