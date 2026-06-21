export type AuthActionState = {
  error?: string;
  fieldErrors?: Record<string, string[]>;
};

export const initialAuthState: AuthActionState = {};
