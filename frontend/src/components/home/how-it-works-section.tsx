import { HOW_IT_WORKS_CONTENT } from "./content";
import { FadeIn } from "./fade-in";
import { SectionHeading } from "./section-heading";

export function HowItWorksSection() {
  return (
    <section
      id="how-it-works"
      className="scroll-mt-20 bg-[var(--marketing-muted)]/50 py-16 md:py-24"
    >
      <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
        <FadeIn>
          <SectionHeading title={HOW_IT_WORKS_CONTENT.headline} />
        </FadeIn>

        <div className="relative grid gap-10 md:grid-cols-3 md:gap-8">
          <div
            className="pointer-events-none absolute top-8 right-[16.67%] left-[16.67%] hidden h-0.5 bg-[var(--marketing-border)] md:block"
            aria-hidden
          />

          {HOW_IT_WORKS_CONTENT.steps.map((step, index) => (
            <FadeIn key={step.step} delay={index * 100}>
              <div className="relative flex flex-col items-center text-center">
                <div className="relative z-10 flex size-12 items-center justify-center rounded-full bg-[var(--marketing-primary)] text-lg font-bold text-[var(--marketing-primary-foreground)] shadow-md">
                  {step.step}
                </div>
                <h3 className="mt-5 text-lg font-semibold text-[var(--marketing-primary)]">
                  {step.title}
                </h3>
                <p className="mt-3 max-w-xs text-sm leading-relaxed text-[var(--marketing-muted-foreground)]">
                  {step.description}
                </p>
              </div>
            </FadeIn>
          ))}
        </div>
      </div>
    </section>
  );
}
