import { DashboardError } from "@/components/dashboard/dashboard-error";
import { OrgNav } from "@/components/org/org-nav";
import { loadOrgPageContext } from "@/lib/org/page-context";

export default async function OrgLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  let context;

  try {
    context = await loadOrgPageContext("/dashboard/org");
  } catch (error) {
    const message =
      error instanceof Error && error.message === "API_UNAVAILABLE"
        ? "Unable to reach the API server. Make sure FastAPI is running."
        : error instanceof Error
          ? error.message
          : "Organization not found.";

    return <DashboardError message={message} />;
  }

  if (context.kind === "register") {
    return <div className="w-full py-8">{children}</div>;
  }

  return (
    <div className="w-full space-y-6 py-8">
      <header className="space-y-4">
        <div className="space-y-1">
          <h1 className="text-2xl font-semibold tracking-tight">
            {context.org.name}
          </h1>
          <p className="text-sm text-muted-foreground">
            @{context.org.email_domain} · {context.org.total_employees} employees
          </p>
        </div>
        {context.isOrgAdmin ? (
          <OrgNav isSuperadmin={context.isOrgSuperadmin} />
        ) : null}
      </header>
      {children}
    </div>
  );
}
