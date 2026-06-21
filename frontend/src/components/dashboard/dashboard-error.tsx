import Link from "next/link";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

type DashboardErrorProps = {
  title?: string;
  message: string;
};

export function DashboardError({
  title = "Unable to load dashboard",
  message,
}: DashboardErrorProps) {
  return (
    <main className="mx-auto w-full max-w-2xl py-8">
      <Card>
        <CardHeader>
          <CardTitle>{title}</CardTitle>
          <CardDescription>
            Make sure the API server is running and try again.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-destructive" role="alert">
            {message}
          </p>
          <Button variant="outline" render={<Link href="/dashboard" />}>
            Try again
          </Button>
        </CardContent>
      </Card>
    </main>
  );
}
