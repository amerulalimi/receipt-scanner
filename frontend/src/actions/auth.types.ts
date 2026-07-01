export type AuthActionState<T = unknown> = {
  success?: boolean;
  data?: T;
  error?: string;
  errorCode?: string;
  fieldErrors?: Record<string, string[]>;
};

export const initialAuthState: AuthActionState = {};
