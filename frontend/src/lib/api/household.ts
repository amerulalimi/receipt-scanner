import "server-only";

import { apiFetch } from "@/lib/api/client";
import { requireSessionCookieHeader } from "@/lib/api/session";
import type {
  ClaimSuggestionData,
  HouseholdOverviewData,
} from "@/lib/api/types";
import type { SpouseLink } from "@/lib/types/household";

export async function fetchHouseholdOverview(taxYear?: number) {
  const cookie = await requireSessionCookieHeader();
  const query = taxYear ? `?tax_year=${taxYear}` : "";
  return apiFetch<HouseholdOverviewData>(`/api/v1/household${query}`, { cookie });
}

export async function getHouseholdOverview(taxYear: number) {
  const { body } = await fetchHouseholdOverview(taxYear);
  if (!body.success) {
    throw new Error(body.message);
  }
  return body.data;
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

export async function getClaimSuggestion(receiptId: string) {
  const { body } = await fetchClaimSuggestion(receiptId);
  if (!body.success) {
    throw new Error(body.message);
  }
  return body.data;
}

export async function requestSpouseLink(partnerEmail: string): Promise<SpouseLink> {
  const { body } = await requestSpouseLinkWithFastApi({ partner_email: partnerEmail });
  if (!body.success) {
    throw new Error(body.message);
  }
  return {
    id: body.data.link_id,
    requester_id: "",
    partner_id: null,
    partner_email: partnerEmail,
    status: body.data.status as SpouseLink["status"],
    created_at: new Date().toISOString(),
    responded_at: null,
  };
}

export async function respondToLink(
  linkId: string,
  action: "accept" | "reject",
): Promise<SpouseLink> {
  const { body } = await respondSpouseLinkWithFastApi(linkId, { action });
  if (!body.success) {
    throw new Error(body.message);
  }
  return {
    id: body.data.link_id,
    requester_id: "",
    partner_id: null,
    partner_email: "",
    status: body.data.status as SpouseLink["status"],
    created_at: new Date().toISOString(),
    responded_at: new Date().toISOString(),
  };
}

export async function dissolveLink(linkId: string): Promise<void> {
  const { body } = await dissolveSpouseLinkWithFastApi(linkId);
  if (!body.success) {
    throw new Error(body.message);
  }
}

export const getHouseholdOverviewFromApi = getHouseholdOverview;
