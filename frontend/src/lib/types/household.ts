export type {
  ClaimSuggestionData,
  HouseholdCategorySummary,
  HouseholdCombinedSummary,
  HouseholdMemberSummary,
  HouseholdOverviewData,
  SpouseIncomingRequest,
  SpouseOutgoingRequest,
} from "@/lib/api/types";

export type SpouseLinkStatus = "pending" | "accepted" | "rejected" | "dissolved";

export type SpouseLink = {
  id: string;
  requester_id: string;
  partner_id: string | null;
  partner_email: string;
  status: SpouseLinkStatus;
  created_at: string;
  responded_at: string | null;
};

export type HouseholdOverview = import("@/lib/api/types").HouseholdOverviewData & {
  linked: boolean;
};

export type ClaimSuggestion = import("@/lib/api/types").ClaimSuggestionData & {
  suggestion: "self" | "spouse";
  reason: string;
  my_remaining: number | string;
  spouse_remaining: number | string;
  my_bracket: number | null;
  spouse_bracket: number | null;
};

export function isHouseholdLinked(
  overview: import("@/lib/api/types").HouseholdOverviewData,
): boolean {
  return overview.partner !== null && overview.accepted_link_id !== null;
}

export const SPOUSE_LINK_STATUSES: SpouseLinkStatus[] = [
  "pending",
  "accepted",
  "rejected",
  "dissolved",
];
