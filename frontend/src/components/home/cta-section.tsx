import Link from "next/link";

import { Button } from "@/components/ui/button";

import { CTA_CONTENT, ROUTES } from "./content";
import { FadeIn } from "./fade-in";

export function CtaSection() {
  return (
    <section className="bg-[var(--marketing-primary)] py-16 md:py-20">
      <div className="mx-auto max-w-3xl px-4 text-center sm:px-6 lg:px-8">
        <FadeIn>
          <h2 className="text-3xl font-bold tracking-tight text-[var(--marketing-primary-foreground)] md:text-4xl">
            {CTA_CONTENT.headline}
          </h2>
          <p className="mt-4 text-base leading-relaxed text-[var(--marketing-primary-foreground)]/80 md:text-lg">
            {CTA_CONTENT.subtext}
          </p>
          <Button
            render={<Link href={ROUTES.signup} />}
            nativeButton={false}
            size="lg"
            className="mt-8 h-11 bg-[var(--marketing-accent)] px-8 text-[var(--marketing-accent-foreground)] hover:bg-[var(--marketing-accent)]/90"
          >
            {CTA_CONTENT.button}
          </Button>
        </FadeIn>
      </div>
    </section>
  );
}
