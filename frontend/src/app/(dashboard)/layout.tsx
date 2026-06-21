import { DashboardShell } from "@/components/dashboard/dashboard-shell";
import { requireAuth } from "@/lib/auth/require-auth";
import { canAccessOrgFeatures, canAccessHouseholdFeatures } from "@/lib/auth/account-access";

export default async function DashboardLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const user = await requireAuth("/dashboard");

  return (
    <DashboardShell
      userName={user.full_name ?? user.email}
      userEmail={user.email}
      showOrgNav={canAccessOrgFeatures(user)}
      showHouseholdNav={canAccessHouseholdFeatures(user)}
    >
      {children}
    </DashboardShell>
  );
}
