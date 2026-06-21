"use client";

import { AppSidebar } from "@/components/dashboard/app-sidebar";
import { Separator } from "@/components/ui/separator";
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar";

type DashboardShellProps = {
  children: React.ReactNode;
  userName: string;
  userEmail: string;
  showOrgNav: boolean;
  showHouseholdNav: boolean;
};

export function DashboardShell({
  children,
  userName,
  userEmail,
  showOrgNav,
  showHouseholdNav,
}: DashboardShellProps) {
  return (
    <SidebarProvider>
      <AppSidebar
        userName={userName}
        userEmail={userEmail}
        showOrgNav={showOrgNav}
        showHouseholdNav={showHouseholdNav}
      />
      <SidebarInset>
        <header className="flex h-14 shrink-0 items-center gap-2 border-b px-4">
          <SidebarTrigger className="-ml-1" />
          <Separator
            orientation="vertical"
            className="mr-2 data-[orientation=vertical]:h-4"
          />
          <span className="truncate text-sm font-medium text-muted-foreground">
            {userName}
          </span>
        </header>
        <div className="flex min-h-[calc(100svh-3.5rem)] flex-1 flex-col items-center px-4 sm:px-6">
          <div className="w-full max-w-6xl flex-1">{children}</div>
        </div>
      </SidebarInset>
    </SidebarProvider>
  );
}
