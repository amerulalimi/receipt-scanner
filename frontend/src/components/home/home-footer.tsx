import Link from "next/link";

import { FOOTER_CONTENT } from "./content";

export function HomeFooter() {
  return (
    <footer className="border-t border-[var(--marketing-border)] bg-white py-12 md:py-16">
      <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
        <div className="grid gap-10 md:grid-cols-4">
          <div className="md:col-span-1">
            <Link
              href="/"
              className="text-lg font-bold text-[var(--marketing-primary)]"
            >
              Resit.my
            </Link>
            <p className="mt-3 text-sm leading-relaxed text-[var(--marketing-muted-foreground)]">
              {FOOTER_CONTENT.tagline}
            </p>
          </div>

          {FOOTER_CONTENT.columns.map((column) => (
            <div key={column.title}>
              <h3 className="text-sm font-semibold text-[var(--marketing-primary)]">
                {column.title}
              </h3>
              <ul className="mt-4 space-y-3">
                {column.links.map((link) => (
                  <li key={link.label}>
                    <Link
                      href={link.href}
                      className="text-sm text-[var(--marketing-muted-foreground)] transition-colors hover:text-[var(--marketing-primary)]"
                    >
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <p className="mt-12 border-t border-[var(--marketing-border)] pt-8 text-center text-sm text-[var(--marketing-muted-foreground)]">
          {FOOTER_CONTENT.copyright}
        </p>
      </div>
    </footer>
  );
}
