import type { MeData } from "@/lib/api/types";

export function canAccessOrgFeatures(user: MeData): boolean {
  return (
    (user.active_context === "corporate" && user.active_org_id !== null) ||
    (user.account_type === "corporate" &&
      user.org_id === null &&
      user.role === "individual")
  );
}

export function canAccessHouseholdFeatures(user: MeData): boolean {
  return user.active_context === "individual";
}
