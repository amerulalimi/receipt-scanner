"use client";

import {
  Building2,
  FileText,
  HeartHandshake,
  LayoutDashboard,
  Receipt,
  Settings,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { LogoutButton } from "@/components/auth/logout-button";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarRail,
} from "@/components/ui/sidebar";
import { useTranslations } from "@/lib/i18n/use-translations";

const NAV_ITEMS = [
  {
    key: "dashboard",
    href: "/dashboard",
    icon: LayoutDashboard,
    exact: true,
  },
  {
    key: "receipts",
    href: "/dashboard/receipts",
    icon: Receipt,
    exact: false,
  },
  {
    key: "readyToFile",
    href: "/dashboard/ready-to-file",
    icon: FileText,
    exact: false,
  },
  {
    key: "household",
    href: "/dashboard/household",
    icon: HeartHandshake,
    exact: false,
    individualOnly: true,
  },
  {
    key: "organization",
    href: "/dashboard/org",
    icon: Building2,
    exact: false,
    corporateOnly: true,
  },
  {
    key: "settings",
    href: "/dashboard/settings",
    icon: Settings,
    exact: false,
  },
] as const;

function isNavActive(pathname: string, href: string, exact: boolean) {
  if (exact) {
    return pathname === href;
  }
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function AppSidebar({
  userName,
  userEmail,
  showOrgNav,
  showHouseholdNav,
}: {
  userName: string;
  userEmail: string;
  showOrgNav: boolean;
  showHouseholdNav: boolean;
}) {
  const pathname = usePathname();
  const t = useTranslations("nav");
  const tCommon = useTranslations("common");

  const navItems = NAV_ITEMS.filter((item) => {
    if ("corporateOnly" in item && item.corporateOnly) {
      return showOrgNav;
    }
    if ("individualOnly" in item && item.individualOnly) {
      return showHouseholdNav;
    }
    return true;
  });

  return (
    <Sidebar collapsible="icon">
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton
              size="lg"
              render={<Link href="/dashboard" />}
              tooltip={tCommon("appName")}
            >
              <span className="flex size-8 items-center justify-center rounded-lg bg-primary text-sm font-bold text-primary-foreground">
                R
              </span>
              <span className="truncate font-semibold">{tCommon("appName")}</span>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>{t("navigation")}</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {navItems.map((item) => (
                <SidebarMenuItem key={item.href}>
                  <SidebarMenuButton
                    isActive={isNavActive(pathname, item.href, item.exact)}
                    render={<Link href={item.href} />}
                    tooltip={t(item.key)}
                  >
                    <item.icon />
                    <span>{t(item.key)}</span>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter>
        <SidebarGroup>
          <SidebarGroupLabel>{t("account")}</SidebarGroupLabel>
          <SidebarGroupContent className="space-y-3 px-2 pb-2">
            <div className="truncate text-xs text-muted-foreground">
              <p className="font-medium text-foreground">{userName}</p>
              <p>{userEmail}</p>
            </div>
            <LogoutButton />
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarFooter>

      <SidebarRail />
    </Sidebar>
  );
}
