export type ReceiptUploadActionState = {
  error?: string;
  fieldErrors?: Record<string, string[]>;
  success?: boolean;
  message?: string;
  uploadErrors?: Array<{
    filename: string | null;
    message: string;
  }>;
};

export type ReceiptUpdateActionState = {
  error?: string;
  fieldErrors?: Record<string, string[]>;
  success?: boolean;
};

export type ReceiptDeleteActionState = {
  error?: string;
  success?: boolean;
};

export type ReceiptManualActionState = {
  error?: string;
  fieldErrors?: Record<string, string[]>;
  success?: boolean;
  message?: string;
  receiptId?: string;
};

export const initialReceiptUploadState: ReceiptUploadActionState = {};
export const initialReceiptUpdateState: ReceiptUpdateActionState = {};
export const initialReceiptDeleteState: ReceiptDeleteActionState = {};
export const initialReceiptManualState: ReceiptManualActionState = {};
