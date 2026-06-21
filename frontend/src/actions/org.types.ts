export type OrgActionState = {
  error?: string;
  fieldErrors?: Record<string, string[]>;
  success?: boolean;
  message?: string;
  inviteUrl?: string;
};

export const initialOrgActionState: OrgActionState = {};

export type InviteAcceptActionState = {
  error?: string;
  fieldErrors?: Record<string, string[]>;
};

export const initialInviteAcceptActionState: InviteAcceptActionState = {};
