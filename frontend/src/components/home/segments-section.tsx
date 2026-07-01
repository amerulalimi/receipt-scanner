"use client";

import Link from "next/link";

import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

import { ROUTES, SEGMENTS_CONTENT } from "./content";
import { FadeIn } from "./fade-in";
import { SectionHeading } from "./section-heading";

export function SegmentsSection() {
  const defaultTab = SEGMENTS_CONTENT.items[0]?.id ?? "individu";

  return (
    <section
      id="segments"
      className="scroll-mt-20 bg-[var(--marketing-muted)]/50 py-16 md:py-24"
    >
      <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
        <FadeIn>
          <SectionHeading title={SEGMENTS_CONTENT.headline} />
        </FadeIn>

        <FadeIn delay={100}>
          <Tabs defaultValue={defaultTab} className="w-full">
            <TabsList className="mx-auto mb-8 flex h-auto w-full max-w-3xl flex-wrap gap-1 bg-white p-1 shadow-sm">
              {SEGMENTS_CONTENT.items.map((segment) => (
                <TabsTrigger
                  key={segment.id}
                  value={segment.id}
                  className="flex-1 px-3 py-2 text-xs sm:text-sm"
                >
                  {segment.label}
                </TabsTrigger>
              ))}
            </TabsList>

            {SEGMENTS_CONTENT.items.map((segment) => {
              const Icon = segment.icon;
              return (
                <TabsContent key={segment.id} value={segment.id}>
                  <div className="mx-auto flex max-w-2xl flex-col items-center rounded-2xl border border-[var(--marketing-border)] bg-white p-8 text-center shadow-sm md:p-12">
                    <div className="flex size-16 items-center justify-center rounded-2xl bg-[var(--marketing-primary)]/10">
                      <Icon
                        className="size-8 text-[var(--marketing-primary)]"
                        aria-hidden
                      />
                    </div>
                    <h3 className="mt-6 text-xl font-semibold text-[var(--marketing-primary)]">
                      {segment.label}
                    </h3>
                    <p className="mt-4 text-base leading-relaxed text-[var(--marketing-muted-foreground)]">
                      {segment.description}
                    </p>
                  </div>
                </TabsContent>
              );
            })}
          </Tabs>

          <div className="mt-10 flex flex-col items-center justify-center gap-3 sm:flex-row">
            <Button
              render={<Link href={ROUTES.forIndividual} />}
              nativeButton={false}
              variant="outline"
              className="h-10 min-w-[180px] border-[var(--marketing-primary)] text-[var(--marketing-primary)] hover:bg-[var(--marketing-primary)]/5"
            >
              {SEGMENTS_CONTENT.individualCta}
            </Button>
            <Button
              render={<Link href={ROUTES.forBusiness} />}
              nativeButton={false}
              className="h-10 min-w-[180px] bg-[var(--marketing-primary)] text-[var(--marketing-primary-foreground)] hover:bg-[var(--marketing-primary)]/90"
            >
              {SEGMENTS_CONTENT.businessCta}
            </Button>
          </div>
        </FadeIn>
      </div>
    </section>
  );
}
