"use client";

import { parseAsInteger, parseAsString, useQueryStates } from "nuqs";

import { Input } from "@/components/ui/input";

const filterParsers = {
  search: parseAsString.withDefault(""),
  page: parseAsInteger.withDefault(1),
};

type AdminDirectoryToolbarProps = {
  searchPlaceholder: string;
};

export function AdminDirectoryToolbar({
  searchPlaceholder,
}: AdminDirectoryToolbarProps) {
  const [filters, setFilters] = useQueryStates(filterParsers);

  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
      <div className="flex-1 space-y-1.5">
        <label
          htmlFor="admin-directory-search"
          className="text-xs font-medium text-muted-foreground"
        >
          Search
        </label>
        <Input
          id="admin-directory-search"
          value={filters.search}
          placeholder={searchPlaceholder}
          onChange={(event) => {
            void setFilters({ search: event.target.value, page: 1 });
          }}
        />
      </div>
    </div>
  );
}

export function useAdminDirectoryPagination(totalPages: number) {
  const [filters, setFilters] = useQueryStates(filterParsers);

  function goToPage(page: number) {
    const nextPage = Math.min(Math.max(page, 1), totalPages);
    void setFilters({ page: nextPage });
  }

  return {
    page: filters.page,
    goToPage,
  };
}
