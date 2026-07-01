import { AdminLoginForm } from "@/components/admin/admin-login-form";

export const metadata = {
  title: "Admin Login",
};

type AdminLoginPageProps = {
  searchParams: Promise<{
    redirect?: string;
  }>;
};

export default async function AdminLoginPage({ searchParams }: AdminLoginPageProps) {
  const params = await searchParams;

  return (
    <div className="flex min-h-svh flex-col items-center justify-center gap-6 bg-muted/30 px-4 py-10">
      <div className="text-center">
        <p className="text-lg font-semibold tracking-tight">Resit.my</p>
        <p className="text-sm text-muted-foreground">Platform administration</p>
      </div>
      <AdminLoginForm redirectTo={params.redirect} />
    </div>
  );
}
