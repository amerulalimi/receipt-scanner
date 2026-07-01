import Link from "next/link";

import { Button } from "@/components/ui/button";

export const metadata = {
  title: "Demo",
};

export default function DemoPage() {
  return (
    <main className="home-marketing flex min-h-screen flex-col items-center justify-center px-4 text-center">
      <h1 className="text-3xl font-bold text-[var(--marketing-primary)]">
        Demo Resit.my
      </h1>
      <p className="mt-4 max-w-md text-[var(--marketing-muted-foreground)]">
        Halaman demo akan datang. Sementara ini, daftar percuma untuk mula
        mengimbas resit anda.
      </p>
      <Button
        render={<Link href="/register" />}
        nativeButton={false}
        className="mt-8 bg-[var(--marketing-accent)] text-[var(--marketing-accent-foreground)]"
      >
        Daftar Sekarang
      </Button>
    </main>
  );
}
