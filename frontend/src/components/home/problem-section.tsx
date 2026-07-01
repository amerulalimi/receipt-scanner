import { Card, CardContent } from "@/components/ui/card";

import { PROBLEM_CONTENT } from "./content";
import { FadeIn } from "./fade-in";
import { SectionHeading } from "./section-heading";

export function ProblemSection() {
  return (
    <section className="bg-white py-16 md:py-24">
      <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
        <FadeIn>
          <SectionHeading title={PROBLEM_CONTENT.headline} />
        </FadeIn>

        <div className="grid gap-6 sm:grid-cols-2">
          {PROBLEM_CONTENT.items.map((item, index) => {
            const Icon = item.icon;
            return (
              <FadeIn key={item.problem} delay={index * 80}>
                <Card className="h-full border-[var(--marketing-border)] bg-[var(--marketing-muted)]/40 py-0 shadow-none transition-shadow hover:shadow-md">
                  <CardContent className="flex flex-col gap-4 p-6">
                    <div className="flex size-11 items-center justify-center rounded-xl bg-[var(--marketing-primary)]/10">
                      <Icon
                        className="size-5 text-[var(--marketing-primary)]"
                        aria-hidden
                      />
                    </div>
                    <div>
                      <h3 className="text-base font-semibold text-[var(--marketing-primary)]">
                        {item.problem}
                      </h3>
                      <p className="mt-2 text-sm text-[var(--marketing-muted-foreground)]">
                        {item.impact}
                      </p>
                    </div>
                  </CardContent>
                </Card>
              </FadeIn>
            );
          })}
        </div>

        <FadeIn delay={200}>
          <p className="mt-12 text-center text-lg font-bold text-[var(--marketing-primary)] md:text-xl">
            {PROBLEM_CONTENT.closing}
          </p>
        </FadeIn>
      </div>
    </section>
  );
}
