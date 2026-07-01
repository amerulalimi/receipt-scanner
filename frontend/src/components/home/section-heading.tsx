import { cn } from "@/lib/utils";

type SectionHeadingProps = {
  title: string;
  subtitle?: string;
  className?: string;
  align?: "left" | "center";
};

export function SectionHeading({
  title,
  subtitle,
  className,
  align = "center",
}: SectionHeadingProps) {
  return (
    <div
      className={cn(
        "mb-10 md:mb-14",
        align === "center" && "mx-auto max-w-3xl text-center",
        className,
      )}
    >
      <h2 className="text-3xl font-bold tracking-tight text-[var(--marketing-primary)] md:text-4xl">
        {title}
      </h2>
      {subtitle ? (
        <p className="mt-4 text-base text-[var(--marketing-muted-foreground)] md:text-lg">
          {subtitle}
        </p>
      ) : null}
    </div>
  );
}
