export type SettingsActionState = {
  error?: string;
  fieldErrors?: Record<string, string[]>;
  success?: boolean;
  message?: string;
};

export const initialSettingsActionState: SettingsActionState = {};
