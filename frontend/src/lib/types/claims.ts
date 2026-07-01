export type {
  ClaimCategorySummary,
  ClaimSummaryData,
  ClaimCompareData,
  CompletenessScoreData,
  CompletenessBreakdownItem,
  ReadyToFileData,
  ReadyToFileField,
  ReadyToFileFilingItem,
} from "@/lib/api/types";

import type { ClaimCategorySummary } from "@/lib/api/types";

export type ClaimCategory = ClaimCategorySummary["category"];
export type ClaimSummary = import("@/lib/api/types").ClaimSummaryData;
export type YearComparison = import("@/lib/api/types").ClaimCompareData;
export type ReadyToFileItem = import("@/lib/api/types").ReadyToFileFilingItem;
export type ReadyToFile = import("@/lib/api/types").ReadyToFileData;
export type CompletenessScore = import("@/lib/api/types").CompletenessScoreData;

export type CategoryStatus = ClaimCategorySummary["status"];

const ringgitFormatter = new Intl.NumberFormat("ms-MY", {
  style: "currency",
  currency: "MYR",
  minimumFractionDigits: 2,
});

export function formatRinggit(amount: number): string {
  return ringgitFormatter.format(amount);
}

export function computeCategoryStatus(percentage: number): CategoryStatus {
  if (percentage >= 100) {
    return "full";
  }
  if (percentage >= 80) {
    return "warning";
  }
  return "ok";
}

export async function exportZip(taxYear: number): Promise<Blob> {
  const response = await fetch(`/api/claims/export-zip?tax_year=${taxYear}`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error("Failed to export receipts.");
  }

  return response.blob();
}
