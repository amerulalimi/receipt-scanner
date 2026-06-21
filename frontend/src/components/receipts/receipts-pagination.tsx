"use client";

import { parseAsInteger, useQueryState } from "nuqs";

import { Button } from "@/components/ui/button";
import { useTranslations } from "@/lib/i18n/use-translations";

type ReceiptsPaginationProps = {
  total: number;
  page: number;
  limit: number;
};

export function ReceiptsPagination({
  total,
  page,
  limit,
}: ReceiptsPaginationProps) {
  const t = useTranslations("receipts");
  const [, setPage] = useQueryState(
    "page",
    parseAsInteger.withDefault(1),
  );

  const totalPages = Math.max(1, Math.ceil(total / limit));
  const from = total === 0 ? 0 : (page - 1) * limit + 1;
  const to = Math.min(page * limit, total);

  if (total === 0) {
    return null;
  }

  return (
    <div className="flex flex-wrap items-center justify-between gap-3">
      <p className="text-sm text-muted-foreground">
        {t("paginationRange", { from, to, total })}
      </p>

      <div className="flex items-center gap-2">
        <Button
          type="button"
          variant="outline"
          size="sm"
          disabled={page <= 1}
          onClick={() => {
            void setPage(Math.max(1, page - 1));
          }}
        >
          {t("previous")}
        </Button>
        <span className="text-sm tabular-nums text-muted-foreground">
          {t("pageOf", { page, total: totalPages })}
        </span>
        <Button
          type="button"
          variant="outline"
          size="sm"
          disabled={page >= totalPages}
          onClick={() => {
            void setPage(Math.min(totalPages, page + 1));
          }}
        >
          {t("next")}
        </Button>
      </div>
    </div>
  );
}
