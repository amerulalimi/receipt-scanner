export const RECEIPT_UPLOAD_MAX_BYTES = 10 * 1024 * 1024;

export const RECEIPT_UPLOAD_MAX_FILES = 20;



export const RECEIPT_UPLOAD_ACCEPTED_MIME_TYPES = [

  "image/jpeg",

  "image/png",

  "image/webp",

  "application/pdf",

] as const;



export type ReceiptUploadMimeType =

  (typeof RECEIPT_UPLOAD_ACCEPTED_MIME_TYPES)[number];



export const RECEIPT_UPLOAD_ACCEPT = RECEIPT_UPLOAD_ACCEPTED_MIME_TYPES.join(",");



export const RECEIPT_CATEGORY_LABELS: Record<string, string> = {
  perubatan: "Medical & Dental",
  gaya_hidup: "Lifestyle",
  sukan: "Sports equipment",
  pendidikan: "Self-education",
  sspn: "SSPN",
  ev_charging: "EV charging",
  tidak_layak: "Not eligible",
  semak_manual: "Manual review",
};



export function getCategoryLabel(
  category: string,
  labelsMap?: Record<string, string>,
): string {
  if (labelsMap?.[category]) {
    return labelsMap[category];
  }

  return RECEIPT_CATEGORY_LABELS[category] ?? category;
}



export const RECEIPT_STATUS_LABELS: Record<string, string> = {
  pending: "Pending",
  approved: "Approved",
  rejected: "Rejected",
  flagged: "Flagged",
  duplicate: "Duplicate",
};



export function getStatusLabel(status: string): string {

  return RECEIPT_STATUS_LABELS[status] ?? status;

}



export type ReceiptScanStatus = "waiting" | "processing" | "success" | "failed";



export const RECEIPT_SCAN_STATUS_LABELS: Record<ReceiptScanStatus, string> = {
  waiting: "Waiting",
  processing: "Processing",
  success: "Success",
  failed: "Failed",
};



export function getScanStatusLabel(scanStatus: string): string {

  if (scanStatus in RECEIPT_SCAN_STATUS_LABELS) {

    return RECEIPT_SCAN_STATUS_LABELS[scanStatus as ReceiptScanStatus];

  }

  return scanStatus;

}



function hasAiScanCompleted(item: {

  scan_status?: string;

  ai_confidence: number | null;

  merchant_name: string | null;

  category: string | null;

}): boolean {

  if (item.scan_status === "success") {

    return true;

  }



  if (item.ai_confidence !== null && item.ai_confidence > 0) {

    return true;

  }



  if (item.merchant_name) {

    return true;

  }



  return Boolean(item.category && item.category !== "semak_manual");

}



function hasAiScanFailed(item: {

  scan_status?: string;

  status: string;

  ai_confidence: number | null;

  category: string | null;

  merchant_name: string | null;

}): boolean {

  if (item.scan_status === "failed") {

    return true;

  }



  return (

    item.status === "flagged" &&

    item.category === "semak_manual" &&

    !item.merchant_name

  ) || (

    item.ai_confidence === 0 &&

    item.category === "semak_manual" &&

    !item.merchant_name

  );

}



export function getReceiptScanStatus(item: {

  scan_status?: string;

  status: string;

  category: string | null;

  merchant_name: string | null;

  ai_confidence: number | null;

}): ReceiptScanStatus {

  if (item.scan_status && item.scan_status in RECEIPT_SCAN_STATUS_LABELS) {

    return item.scan_status as ReceiptScanStatus;

  }



  if (hasAiScanFailed(item)) {

    return "failed";

  }



  if (hasAiScanCompleted(item)) {

    return "success";

  }



  if (

    item.status === "pending" &&

    (item.category === "semak_manual" || item.category === null) &&

    !item.merchant_name &&

    item.ai_confidence === null

  ) {

    return "processing";

  }



  return "waiting";

}



/** @deprecated Use getReceiptScanStatus instead */

export function isReceiptProcessing(item: {

  scan_status?: string;

  status: string;

  category: string | null;

  merchant_name: string | null;

  ai_confidence: number | null;

}): boolean {

  const scanStatus = getReceiptScanStatus(item);

  return scanStatus === "processing" || scanStatus === "waiting";

}



/** @deprecated Use getReceiptScanStatus instead */

export function isReceiptProcessingFailed(item: {

  scan_status?: string;

  status: string;

  category: string | null;

  merchant_name: string | null;

  ai_confidence: number | null;

}): boolean {

  return getReceiptScanStatus(item) === "failed";

}



export function getReceiptScanStatusBadgeClass(scanStatus: ReceiptScanStatus): string {

  switch (scanStatus) {

    case "processing":

      return "rounded-full bg-secondary px-2 py-0.5 text-xs font-medium text-secondary-foreground";

    case "waiting":

      return "rounded-full border border-amber-500/40 bg-amber-500/10 px-2 py-0.5 text-xs font-medium text-amber-900 dark:text-amber-100";

    case "success":

      return "rounded-full bg-emerald-500/10 px-2 py-0.5 text-xs font-medium text-emerald-700 dark:text-emerald-300";

    case "failed":

      return "rounded-full bg-destructive/10 px-2 py-0.5 text-xs font-medium text-destructive";

  }

}



export const RECEIPT_FLAG_LABELS: Record<string, string> = {
  low_ocr_confidence: "Low OCR confidence",
  low_ai_confidence: "Low AI confidence",
  mixed_items: "Mixed items",
  manual_review: "Manual review",
  limit_exceeded: "Relief limit exceeded",
};

export function getFlagLabel(
  flagType: string,
  labels?: Record<string, string>,
): string {
  if (labels?.[flagType]) {
    return labels[flagType];
  }

  return RECEIPT_FLAG_LABELS[flagType] ?? flagType;
}

type ReceiptLabelTranslator = (key: string) => string;

export function getReceiptSortLabels(t: ReceiptLabelTranslator): Record<string, string> {
  return {
    "created_at:desc": t("sortNewest"),
    "created_at:asc": t("sortOldest"),
    "receipt_date:desc": t("sortReceiptDate"),
    "total_amount:desc": t("sortHighestAmount"),
    "claimed_amount:desc": t("sortHighestClaim"),
  };
}

export function getReceiptStatusLabels(t: ReceiptLabelTranslator): Record<string, string> {
  return {
    pending: t("statusPending"),
    approved: t("statusApproved"),
    rejected: t("statusRejected"),
    flagged: t("statusFlagged"),
    duplicate: t("statusDuplicate"),
  };
}

export function getReceiptScanStatusLabels(
  t: ReceiptLabelTranslator,
): Record<ReceiptScanStatus, string> {
  return {
    waiting: t("scanWaiting"),
    processing: t("scanProcessing"),
    success: t("scanSuccess"),
    failed: t("scanFailed"),
  };
}

export function getReceiptCategoryLabels(
  t: ReceiptLabelTranslator,
): Record<string, string> {
  return {
    perubatan: t("categoryMedical"),
    gaya_hidup: t("categoryLifestyle"),
    sukan: t("categorySports"),
    pendidikan: t("categoryEducation"),
    sspn: t("categorySspn"),
    ev_charging: t("categoryEvCharging"),
    tidak_layak: t("categoryNotEligible"),
    semak_manual: t("categoryManualReview"),
  };
}

export function getReceiptFlagLabels(t: ReceiptLabelTranslator): Record<string, string> {
  return {
    low_ocr_confidence: t("flagLowOcr"),
    low_ai_confidence: t("flagLowAi"),
    mixed_items: t("flagMixedItems"),
    manual_review: t("flagManualReview"),
    limit_exceeded: t("flagLimitExceeded"),
  };
}

/** @deprecated Use getReceiptSortLabels with translations */
export const RECEIPT_SORT_LABELS: Record<string, string> = {
  "created_at:desc": "Newest",
  "created_at:asc": "Oldest",
  "receipt_date:desc": "Receipt date",
  "total_amount:desc": "Highest amount",
  "claimed_amount:desc": "Highest claim",
};

