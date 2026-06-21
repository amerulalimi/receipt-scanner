import { Skeleton } from "@/components/ui/skeleton";

export default function ReceiptsLoading() {
  return (
    <main className="w-full space-y-6 py-8">
      <div className="space-y-2">
        <Skeleton className="h-8 w-32" />
        <Skeleton className="h-4 w-64" />
      </div>
      <div className="flex flex-wrap gap-3">
        <Skeleton className="h-16 w-40" />
        <Skeleton className="h-16 w-40" />
        <Skeleton className="h-16 w-40" />
      </div>
      <Skeleton className="h-64 w-full rounded-xl" />
    </main>
  );
}
