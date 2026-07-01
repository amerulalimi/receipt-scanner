"use client";

import Link from "next/link";
import { Menu } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";

import { NAV_LINKS, ROUTES } from "./content";

export function HomeNavbar() {
  const [open, setOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 border-b border-[var(--marketing-border)] bg-white/90 backdrop-blur-md">
      <nav
        className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6 lg:px-8"
        aria-label="Navigasi utama"
      >
        <Link
          href="/"
          className="text-xl font-bold tracking-tight text-[var(--marketing-primary)] transition-opacity hover:opacity-80"
        >
          Resit.my
        </Link>

        <ul className="hidden items-center gap-8 md:flex">
          {NAV_LINKS.map((link) => (
            <li key={link.href}>
              <Link
                href={link.href}
                className="text-sm font-medium text-[var(--marketing-muted-foreground)] transition-colors hover:text-[var(--marketing-primary)]"
              >
                {link.label}
              </Link>
            </li>
          ))}
          <li>
            <Link
              href={ROUTES.login}
              className="text-sm font-medium text-[var(--marketing-muted-foreground)] transition-colors hover:text-[var(--marketing-primary)]"
            >
              Log Masuk
            </Link>
          </li>
        </ul>

        <div className="hidden md:block">
          <Button
            render={<Link href={ROUTES.signup} />}
            nativeButton={false}
            className="h-10 bg-[var(--marketing-accent)] px-5 text-[var(--marketing-accent-foreground)] hover:bg-[var(--marketing-accent)]/90"
          >
            Daftar Sekarang
          </Button>
        </div>

        <Sheet open={open} onOpenChange={setOpen}>
          <SheetTrigger
            render={
              <Button
                variant="ghost"
                size="icon"
                className="md:hidden"
                aria-label="Buka menu navigasi"
              >
                <Menu className="size-5" />
              </Button>
            }
          />
          <SheetContent side="right" className="w-72">
            <SheetHeader>
              <SheetTitle className="text-left text-[var(--marketing-primary)]">
                Resit.my
              </SheetTitle>
            </SheetHeader>
            <div className="mt-6 flex flex-col gap-4">
              {NAV_LINKS.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  onClick={() => setOpen(false)}
                  className="text-base font-medium text-[var(--marketing-primary)]"
                >
                  {link.label}
                </Link>
              ))}
              <Link
                href={ROUTES.login}
                onClick={() => setOpen(false)}
                className="text-base font-medium text-[var(--marketing-muted-foreground)]"
              >
                Log Masuk
              </Link>
              <Button
                render={<Link href={ROUTES.signup} />}
                nativeButton={false}
                className="mt-2 h-10 w-full bg-[var(--marketing-accent)] text-[var(--marketing-accent-foreground)] hover:bg-[var(--marketing-accent)]/90"
                onClick={() => setOpen(false)}
              >
                Daftar Sekarang
              </Button>
            </div>
          </SheetContent>
        </Sheet>
      </nav>
    </header>
  );
}
