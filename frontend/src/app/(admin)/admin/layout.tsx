import { AdminShell } from "@/components/admin/admin-shell";
import { requireSuperadmin } from "@/lib/auth/require-superadmin";

export const metadata = {
  title: "Admin",
};

export default async function AdminLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const user = await requireSuperadmin();

  return (
    <AdminShell userName={user.full_name ?? user.email} userEmail={user.email}>
      {children}
    </AdminShell>
  );
}
