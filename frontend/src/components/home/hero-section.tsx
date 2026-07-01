import Link from "next/link";
import { ImageIcon } from "lucide-react";

import { Button } from "@/components/ui/button";

import { HERO_CONTENT, ROUTES } from "./content";
import { FadeIn } from "./fade-in";

export function HeroSection() {
  return (
    <section className="relative overflow-hidden bg-gradient-to-b from-[var(--marketing-muted)] to-white py-16 md:py-24 lg:py-28">
      <div className="pointer-events-none absolute -top-24 right-0 h-96 w-96 rounded-full bg-[var(--marketing-accent)]/10 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-24 left-0 h-80 w-80 rounded-full bg-[var(--marketing-primary)]/5 blur-3xl" />

      <div className="relative mx-auto grid max-w-6xl items-center gap-12 px-4 sm:px-6 lg:grid-cols-2 lg:gap-16 lg:px-8">
        <FadeIn>
          <div>
            <h1 className="text-4xl font-bold leading-tight tracking-tight text-[var(--marketing-primary)] sm:text-5xl lg:text-[3.25rem] lg:leading-[1.1]">
              {HERO_CONTENT.headline}
            </h1>
            <p className="mt-6 max-w-xl text-base leading-relaxed text-[var(--marketing-muted-foreground)] md:text-lg">
              {HERO_CONTENT.subheadline}
            </p>

            <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:items-center">
              <Button
                render={<Link href={ROUTES.signup} />}
                nativeButton={false}
                size="lg"
                className="h-11 bg-[var(--marketing-accent)] px-6 text-[var(--marketing-accent-foreground)] hover:bg-[var(--marketing-accent)]/90"
              >
                {HERO_CONTENT.primaryCta}
              </Button>
              <Button
                render={<Link href={ROUTES.demo} />}
                nativeButton={false}
                variant="outline"
                size="lg"
                className="h-11 border-[var(--marketing-border)] px-6 text-[var(--marketing-primary)] hover:bg-[var(--marketing-muted)]"
              >
                {HERO_CONTENT.secondaryCta}
              </Button>
            </div>

            <p className="mt-6 text-sm text-[var(--marketing-muted-foreground)]">
              {HERO_CONTENT.trustLine}
            </p>
          </div>
        </FadeIn>

        <FadeIn delay={150}>
          <div
            className="relative mx-auto flex aspect-[4/3] w-full max-w-lg items-center justify-center overflow-hidden rounded-2xl border border-[var(--marketing-border)] bg-gradient-to-br from-[var(--marketing-primary)]/10 via-white to-[var(--marketing-accent)]/15 shadow-xl shadow-[var(--marketing-primary)]/5 lg:max-w-none"
            role="img"
            aria-label="Pratonton produk Resit.my — placeholder screenshot"
          >
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_20%,var(--marketing-accent)_0%,transparent_50%)] opacity-30" />
            <div className="relative flex flex-col items-center gap-3 text-center">
              <div className="flex size-16 items-center justify-center rounded-2xl bg-white/80 shadow-sm backdrop-blur-sm">
                <ImageIcon
                  className="size-8 text-[var(--marketing-primary)]/60"
                  aria-hidden
                />
              </div>
              <span className="text-sm font-medium text-[var(--marketing-muted-foreground)]">
                [Screenshot Placeholder]
              </span>
            </div>
          </div>
        </FadeIn>
      </div>
    </section>
  );
}
