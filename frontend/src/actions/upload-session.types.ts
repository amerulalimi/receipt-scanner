import type { UploadSessionCreateData } from "@/lib/api/types";

export type CreateUploadSessionResult =
  | { data: UploadSessionCreateData; error?: undefined }
  | { error: string; data?: undefined };

export type MobileUploadActionState = {
  fieldErrors?: Record<string, string[]>;
  error?: string;
  success?: boolean;
  message?: string;
  jobId?: string;
  inactivityRemaining?: number;
  uploadsCount?: number;
};

export const initialMobileUploadState: MobileUploadActionState = {};

export type MobileKeepAliveResult =
  | { inactivityRemaining: number; error?: undefined }
  | { error: string; inactivityRemaining?: undefined };

export type MobileCloseSessionResult =
  | { uploadsCount: number; message: string; error?: undefined }
  | { error: string; uploadsCount?: undefined; message?: undefined };

export type MobileValidateResult =
  | {
      valid: true;
      uploadsSoFar: number;
      inactivityRemaining: number;
      error?: undefined;
    }
  | { error: string; valid?: undefined };
