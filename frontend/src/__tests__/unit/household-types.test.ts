import {
  isHouseholdLinked,
  SPOUSE_LINK_STATUSES,
  type ClaimSuggestion,
  type HouseholdOverview,
} from "@/lib/types/household";

describe("household types", () => {
  it("SpouseLink status values are valid", () => {
    expect(SPOUSE_LINK_STATUSES).toEqual([
      "pending",
      "accepted",
      "rejected",
      "dissolved",
    ]);
  });

  it("HouseholdOverview linked field is boolean", () => {
    const unlinked: HouseholdOverview = {
      accepted_link_id: null,
      partner: null,
      combined: null,
      incoming_requests: [],
      outgoing_request: null,
      linked: false,
    };
    const linked: HouseholdOverview = {
      ...unlinked,
      accepted_link_id: "link-1",
      partner: {
        user_id: "u2",
        full_name: "Spouse",
        email: "spouse@example.com",
        tax_year: 2025,
        tax_bracket: 24,
        total_claimed: 0,
        categories: [],
      },
      linked: true,
    };

    expect(isHouseholdLinked(unlinked)).toBe(false);
    expect(isHouseholdLinked(linked)).toBe(true);
  });

  it("ClaimSuggestion suggestion is self or spouse", () => {
    const selfSuggestion: ClaimSuggestion = {
      receipt_id: "r1",
      category: "perubatan",
      suggested_user_id: "u1",
      suggestion: "self",
      reason_my: "BM",
      reason_en: "EN",
      reason: "BM",
      user_remaining: 5000,
      spouse_remaining: 3000,
      my_bracket: 24,
      spouse_bracket: 11,
    };

    expect(["self", "spouse"]).toContain(selfSuggestion.suggestion);
  });
});
