import { Clock } from "lucide-react";

import { MobileUploadSession } from "@/components/receipts/mobile-upload-session";
import { validateUploadSessionWithFastApi } from "@/lib/api/upload-sessions";
import { parseUploadSessionToken } from "@/lib/validations/upload-session";

interface QrUploadSessionPageProps {
  params: Promise<{ token: string }>;
}

function SessionErrorView({ message }: { message: string }) {
  return (
    <main className="mx-auto flex min-h-dvh max-w-md flex-col items-center justify-center gap-4 px-4 py-8 text-center">
      <Clock className="size-12 text-muted-foreground" aria-hidden />
      <h1 className="text-xl font-semibold">Session unavailable</h1>
      <p className="text-muted-foreground">{message}</p>
    </main>
  );
}

export const metadata = {
  title: "Upload Receipt",
};

export default async function QrUploadSessionPage({
  params,
}: QrUploadSessionPageProps) {
  const { token } = await params;
  const parsed = parseUploadSessionToken(token);

  if (!parsed.success) {
    return <SessionErrorView message="Invalid upload link." />;
  }

  let result;
  try {
    result = await validateUploadSessionWithFastApi(parsed.data);
  } catch {
    return (
      <SessionErrorView message="Unable to reach the server. Please try again." />
    );
  }

  const { response, body } = result;

  if (!body.success || response.status === 401) {
    return (
      <SessionErrorView
        message={
          body.success === false
            ? body.message
            : "Session expired. Please scan a new QR code."
        }
      />
    );
  }

  if (response.status >= 400) {
    return (
      <SessionErrorView message="Upload session not found or has expired." />
    );
  }

  return <MobileUploadSession token={parsed.data} initialData={body.data} />;
}
