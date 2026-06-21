export type HouseholdActionState = {
  error?: string;
  fieldErrors?: Record<string, string[]>;
  success?: boolean;
  message?: string;
};

export const initialHouseholdActionState: HouseholdActionState = {};
