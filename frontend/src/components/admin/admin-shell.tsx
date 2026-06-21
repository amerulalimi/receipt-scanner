"use client";

import { AdminSidebar } from "@/components/admin/admin-sidebar";
import { Separator } from "@/components/ui/separator";
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar";

type AdminShellProps = {
  children: React.ReactNode;
  userName: string;
  userEmail: string;
};

export function AdminShell({ children, userName, userEmail }: AdminShellProps) {
  return (
    <SidebarProvider>
      <AdminSidebar userEmail={userEmail} />
      <SidebarInset>
        <header className="flex h-14 shrink-0 items-center gap-2 border-b px-4">
          <SidebarTrigger className="-ml-1" />
          <Separator
            orientation="vertical"
            className="mr-2 data-[orientation=vertical]:h-4"
          />
          <span className="text-sm font-medium text-muted-foreground">
            Admin — {userName}
          </span>
        </header>
        <div className="flex min-h-[calc(100svh-3.5rem)] flex-1 flex-col items-center px-4 sm:px-6">
          <div className="w-full max-w-4xl flex-1 py-8">{children}</div>
        </div>
      </SidebarInset>
    </SidebarProvider>
  );
}
