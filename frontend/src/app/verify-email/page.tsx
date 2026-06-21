import { VerifyEmailClient } from "@/components/auth/verify-email-client";

export const metadata = {
  title: "Verify email",
};

type VerifyEmailPageProps = {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
};

export default async function VerifyEmailPage({
  searchParams,
}: VerifyEmailPageProps) {
  const params = await searchParams;
  const rawToken = params.token;
  const token = Array.isArray(rawToken) ? rawToken[0] : rawToken ?? null;

  return (
    <main className="flex min-h-[100svh] items-center justify-center px-4 py-12">
      <VerifyEmailClient token={token} />
    </main>
  );
}
