import "server-only";

import { apiFetch } from "@/lib/api/client";
import { requireSessionCookieHeader } from "@/lib/api/session";
import type {
  ClaimSuggestionData,
  HouseholdOverviewData,
} from "@/lib/api/types";

export async function fetchHouseholdOverview() {
  const cookie = await requireSessionCookieHeader();
  return apiFetch<HouseholdOverviewData>("/api/v1/household", { cookie });
}

export async function requestSpouseLinkWithFastApi(payload: {
  partner_email: string;
}) {
  const cookie = await requireSessionCookieHeader();
  return apiFetch<{ link_id: string; status: string }>(
    "/api/v1/household/spouse-link",
    {
      method: "POST",
      body: payload,
      cookie,
    },
  );
}

export async function respondSpouseLinkWithFastApi(
  linkId: string,
  payload: { action: "accept" | "reject" },
) {
  const cookie = await requireSessionCookieHeader();
  return apiFetch<{ link_id: string; status: string }>(
    `/api/v1/household/spouse-link/${linkId}/respond`,
    {
      method: "POST",
      body: payload,
      cookie,
    },
  );
}

export async function dissolveSpouseLinkWithFastApi(linkId: string) {
  const cookie = await requireSessionCookieHeader();
  return apiFetch<null>(`/api/v1/household/spouse-link/${linkId}`, {
    method: "DELETE",
    cookie,
  });
}

export async function reassignReceiptWithFastApi(
  receiptId: string,
  payload: { target_user_id: string },
) {
  const cookie = await requireSessionCookieHeader();
  return apiFetch<null>(
    `/api/v1/household/receipts/${receiptId}/reassign`,
    {
      method: "POST",
      body: payload,
      cookie,
    },
  );
}

export async function fetchClaimSuggestion(receiptId: string) {
  const cookie = await requireSessionCookieHeader();
  return apiFetch<ClaimSuggestionData>(
    `/api/v1/household/receipts/${receiptId}/claim-suggestion`,
    { cookie },
  );
}
