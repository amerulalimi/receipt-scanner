import { PageSkeleton } from "@/components/ui/page-loader";

export default function ReceiptsLoading() {
  return (
    <main className="w-full py-8">
      <PageSkeleton />
    </main>
  );
}
