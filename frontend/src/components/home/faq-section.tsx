import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";

import { FAQ_CONTENT } from "./content";
import { FadeIn } from "./fade-in";
import { SectionHeading } from "./section-heading";

export function FaqSection() {
  return (
    <section id="faq" className="scroll-mt-20 bg-[var(--marketing-muted)]/50 py-16 md:py-24">
      <div className="mx-auto max-w-3xl px-4 sm:px-6 lg:px-8">
        <FadeIn>
          <SectionHeading title={FAQ_CONTENT.headline} />
        </FadeIn>

        <FadeIn delay={100}>
          <Accordion className="rounded-xl border border-[var(--marketing-border)] bg-white px-4 md:px-6">
            {FAQ_CONTENT.items.map((item, index) => (
              <AccordionItem key={item.question} value={`faq-${index}`}>
                <AccordionTrigger className="py-5 text-left text-base font-medium text-[var(--marketing-primary)] hover:no-underline">
                  {item.question}
                </AccordionTrigger>
                <AccordionContent className="pb-5 text-[var(--marketing-muted-foreground)]">
                  {item.answer}
                </AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        </FadeIn>
      </div>
    </section>
  );
}
