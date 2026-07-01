import { DashboardShell } from "@/components/dashboard/dashboard-shell";
import { requireAuth } from "@/lib/auth/require-auth";
import {
  canAccessOrgFeatures,
  canAccessHouseholdFeatures,
} from "@/lib/auth/account-access";
import { fetchNotifications } from "@/lib/api/notifications";

export default async function DashboardLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const user = await requireAuth("/dashboard");

  let notifications: import("@/lib/api/types").NotificationItem[] = [];
  try {
    const { body } = await fetchNotifications();
    if (body.success) {
      notifications = body.data.items;
    }
  } catch {
    notifications = [];
  }

  return (
    <DashboardShell
      userName={user.full_name ?? user.email}
      userEmail={user.email}
      showOrgNav={canAccessOrgFeatures(user)}
      showHouseholdNav={canAccessHouseholdFeatures(user)}
      showOrgHrNav={
        canAccessOrgFeatures(user) &&
        (user.role === "hr_admin" || user.role === "superadmin")
      }
      isOrgSuperadmin={user.role === "superadmin"}
      notifications={notifications}
    >
      {children}
    </DashboardShell>
  );
}
