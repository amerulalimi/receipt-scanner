import { PageLoader, PageSkeleton } from "@/components/ui/page-loader";

export default function DashboardLoading() {
  return (
    <main className="w-full">
      <PageLoader />
      <PageSkeleton />
    </main>
  );
}
