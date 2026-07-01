import { Check } from "lucide-react";

import { TRUST_CONTENT } from "./content";
import { FadeIn } from "./fade-in";
import { SectionHeading } from "./section-heading";

export function TrustSection() {
  return (
    <section className="bg-white py-16 md:py-24">
      <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
        <FadeIn>
          <SectionHeading title={TRUST_CONTENT.headline} />
        </FadeIn>

        <div className="grid gap-6 sm:grid-cols-2">
          {TRUST_CONTENT.items.map((item, index) => (
            <FadeIn key={item.title} delay={index * 80}>
              <div className="flex gap-4 rounded-xl border border-[var(--marketing-border)] bg-[var(--marketing-muted)]/30 p-6 transition-shadow hover:shadow-sm">
                <div className="flex size-8 shrink-0 items-center justify-center rounded-full bg-[var(--marketing-accent)]/20">
                  <Check
                    className="size-4 text-[var(--marketing-accent)]"
                    aria-hidden
                  />
                </div>
                <div>
                  <h3 className="font-semibold text-[var(--marketing-primary)]">
                    {item.title}
                  </h3>
                  <p className="mt-2 text-sm leading-relaxed text-[var(--marketing-muted-foreground)]">
                    {item.description}
                  </p>
                </div>
              </div>
            </FadeIn>
          ))}
        </div>
      </div>
    </section>
  );
}
