import "server-only";

import { apiFetch } from "@/lib/api/client";
import { requireSessionCookieHeader } from "@/lib/api/session";
import type {
  ClaimCompareData,
  ClaimSummaryData,
  CompletenessScoreData,
  ReadyToFileData,
} from "@/lib/api/types";

export async function fetchClaimSummary(taxYear?: number) {
  const cookie = await requireSessionCookieHeader();
  const query = taxYear ? `?tax_year=${taxYear}` : "";

  const result = await apiFetch<ClaimSummaryData>(`/api/v1/claims/summary${query}`, {
    cookie,
  });

  return result;
}

export async function fetchClaimComparison(taxYear?: number) {
  const cookie = await requireSessionCookieHeader();
  const query = taxYear ? `?tax_year=${taxYear}` : "";

  const result = await apiFetch<ClaimCompareData>(`/api/v1/claims/compare${query}`, {
    cookie,
  });

  return result;
}

export async function fetchReadyToFile(taxYear?: number) {
  const cookie = await requireSessionCookieHeader();
  const query = taxYear ? `?tax_year=${taxYear}` : "";

  return apiFetch<ReadyToFileData>(`/api/v1/claims/ready-to-file${query}`, {
    cookie,
  });
}

export async function fetchCompletenessScore(taxYear?: number) {
  const cookie = await requireSessionCookieHeader();
  const query = taxYear ? `?tax_year=${taxYear}` : "";

  return apiFetch<CompletenessScoreData>(`/api/v1/claims/completeness${query}`, {
    cookie,
  });
}

export const getClaimSummary = fetchClaimSummary;
export const getYearComparison = fetchClaimComparison;
export const getReadyToFile = fetchReadyToFile;
export const getCompletenessScore = fetchCompletenessScore;

export { exportZip } from "@/lib/types/claims";
export { getExportZipUrl } from "@/lib/api/export-urls";
