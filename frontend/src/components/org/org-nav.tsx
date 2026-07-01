"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { cn } from "@/lib/utils";
import { useTranslations } from "@/lib/i18n/use-translations";

const ORG_NAV_ITEMS = [
  { key: "overview", href: "/dashboard/org", exact: true },
  { key: "employees", href: "/dashboard/org/employees", exact: false },
  { key: "pending", href: "/dashboard/org/pending", exact: false },
  { key: "analytics", href: "/dashboard/org/analytics", exact: false },
  { key: "settings", href: "/dashboard/org/settings", exact: false, superadminOnly: true },
] as const;

function isActive(pathname: string, href: string, exact: boolean) {
  if (exact) {
    return pathname === href;
  }
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function OrgNav({ isSuperadmin }: { isSuperadmin: boolean }) {
  const pathname = usePathname();
  const t = useTranslations("orgNav");

  const items = ORG_NAV_ITEMS.filter(
    (item) => !("superadminOnly" in item && item.superadminOnly) || isSuperadmin,
  );

  return (
    <nav className="flex flex-wrap gap-2">
      {items.map((item) => {
        const active = isActive(pathname, item.href, item.exact);
        return (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              "rounded-md px-3 py-1.5 text-sm font-medium transition-colors",
              active
                ? "bg-primary text-primary-foreground"
                : "bg-muted text-muted-foreground hover:text-foreground",
            )}
          >
            {t(item.key)}
          </Link>
        );
      })}
    </nav>
  );
}
