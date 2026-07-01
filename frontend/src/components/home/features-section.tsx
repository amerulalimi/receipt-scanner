import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

import { FEATURES_CONTENT } from "./content";
import { FadeIn } from "./fade-in";
import { SectionHeading } from "./section-heading";

export function FeaturesSection() {
  return (
    <section id="features" className="scroll-mt-20 bg-white py-16 md:py-24">
      <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
        <FadeIn>
          <SectionHeading title={FEATURES_CONTENT.headline} />
        </FadeIn>

        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES_CONTENT.items.map((feature, index) => {
            const Icon = feature.icon;
            return (
              <FadeIn key={feature.title} delay={index * 60}>
                <Card className="h-full border-[var(--marketing-border)] py-0 shadow-none transition-all hover:border-[var(--marketing-accent)]/40 hover:shadow-md">
                  <CardHeader className="pb-2">
                    <div className="mb-3 flex size-11 items-center justify-center rounded-xl bg-[var(--marketing-accent)]/15">
                      <Icon
                        className="size-5 text-[var(--marketing-accent)]"
                        aria-hidden
                      />
                    </div>
                    <CardTitle className="text-base font-semibold text-[var(--marketing-primary)]">
                      {feature.title}
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <CardDescription className="text-sm leading-relaxed text-[var(--marketing-muted-foreground)]">
                      {feature.description}
                    </CardDescription>
                  </CardContent>
                </Card>
              </FadeIn>
            );
          })}
        </div>
      </div>
    </section>
  );
}
