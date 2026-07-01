import Link from "next/link";

import { Button } from "@/components/ui/button";

export const metadata = {
  title: "Untuk Syarikat",
};

export default function ForBusinessPage() {
  return (
    <main className="home-marketing flex min-h-screen flex-col items-center justify-center px-4 text-center">
      <h1 className="text-3xl font-bold text-[var(--marketing-primary)]">
        Resit.my untuk Syarikat
      </h1>
      <p className="mt-4 max-w-md text-[var(--marketing-muted-foreground)]">
        Urus tuntutan pekerja, kelulusan HR, dan eksport data penggajian — semua
        dalam satu platform. Halaman penuh akan datang.
      </p>
      <Button
        render={<Link href="/register" />}
        nativeButton={false}
        className="mt-8 bg-[var(--marketing-primary)] text-[var(--marketing-primary-foreground)]"
      >
        Daftar Syarikat
      </Button>
    </main>
  );
}
