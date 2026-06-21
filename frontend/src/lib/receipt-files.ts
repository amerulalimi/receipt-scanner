export function getReceiptThumbnailUrl(receiptId: string): string {
  return `/api/receipts/${receiptId}/thumbnail`;
}

export function getReceiptFileUrl(receiptId: string): string {
  return `/api/receipts/${receiptId}/file`;
}

export function isPreviewableReceiptFile(fileType: string | null | undefined): boolean {
  if (!fileType) {
    return false;
  }
  return fileType !== "pdf";
}
