import type { MeData } from "@/lib/api/types";

export function canAccessOrgFeatures(user: MeData): boolean {
  return user.account_type === "corporate";
}

export function canAccessHouseholdFeatures(user: MeData): boolean {
  return user.account_type === "individual";
}
