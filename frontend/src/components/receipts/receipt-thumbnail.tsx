import { FileTextIcon } from "lucide-react";

import {
  getReceiptFileUrl,
  getReceiptThumbnailUrl,
  isPreviewableReceiptFile,
} from "@/lib/receipt-files";
import { cn } from "@/lib/utils";

type ReceiptThumbnailProps = {
  receiptId: string;
  fileType: string | null;
  merchantName?: string | null;
  className?: string;
  size?: "sm" | "md";
};

export function ReceiptThumbnail({
  receiptId,
  fileType,
  merchantName,
  className,
  size = "md",
}: ReceiptThumbnailProps) {
  const dimensions = size === "sm" ? "size-14" : "size-20";

  if (!isPreviewableReceiptFile(fileType)) {
    return (
      <a
        href={getReceiptFileUrl(receiptId)}
        target="_blank"
        rel="noopener noreferrer"
        className={cn(
          "flex shrink-0 items-center justify-center rounded-lg border bg-muted/40 text-muted-foreground",
          dimensions,
          className,
        )}
        title="Open PDF"
      >
        <FileTextIcon className="size-6" />
      </a>
    );
  }

  return (
    <a
      href={getReceiptFileUrl(receiptId)}
      target="_blank"
      rel="noopener noreferrer"
      className={cn("block shrink-0 overflow-hidden rounded-lg border", className)}
      title={merchantName ?? "View receipt"}
    >
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={getReceiptThumbnailUrl(receiptId)}
        alt={merchantName ?? "Receipt thumbnail"}
        className={cn("object-cover", dimensions)}
        loading="lazy"
      />
    </a>
  );
}
