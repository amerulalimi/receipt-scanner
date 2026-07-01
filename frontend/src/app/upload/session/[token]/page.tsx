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
      <h1 className="text-xl font-semibold">Sesi tidak tersedia</h1>
      <p className="text-muted-foreground">{message}</p>
    </main>
  );
}

export const metadata = {
  title: "Muat Naik Resit",
};

export default async function QrUploadSessionPage({
  params,
}: QrUploadSessionPageProps) {
  const { token } = await params;
  const parsed = parseUploadSessionToken(token);

  if (!parsed.success) {
    return <SessionErrorView message="Pautan muat naik tidak sah." />;
  }

  let result;
  try {
    result = await validateUploadSessionWithFastApi(parsed.data);
  } catch {
    return (
      <SessionErrorView message="Tidak dapat menghubungi pelayan. Sila cuba lagi." />
    );
  }

  const { response, body } = result;

  if (!body.success || response.status === 401) {
    return (
      <SessionErrorView
        message={
          body.success === false
            ? body.message
            : "Sesi tamat. Sila imbas QR baru."
        }
      />
    );
  }

  if (response.status >= 400) {
    return (
      <SessionErrorView message="Sesi muat naik tidak dijumpai atau telah tamat." />
    );
  }

  return <MobileUploadSession token={parsed.data} initialData={body.data} />;
}
