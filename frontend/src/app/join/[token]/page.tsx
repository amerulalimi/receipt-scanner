import Link from "next/link";

import { JoinInviteForm } from "@/components/org/join-invite-form";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { validateInviteWithFastApi } from "@/lib/api/org";

export const metadata = {
  title: "Join Organization",
};

type JoinPageProps = {
  params: Promise<{ token: string }>;
};

export default async function JoinPage({ params }: JoinPageProps) {
  const { token } = await params;

  let validateResult;

  try {
    validateResult = await validateInviteWithFastApi(token);
  } catch {
    return (
      <main className="flex min-h-[100svh] items-center justify-center px-4 py-12">
        <Card className="w-full max-w-md">
          <CardHeader>
            <CardTitle>Connection error</CardTitle>
            <CardDescription>
              Unable to reach the server. Make sure FastAPI is running.
            </CardDescription>
          </CardHeader>
        </Card>
      </main>
    );
  }

  const { body } = validateResult;

  if (!body.success || !body.data.valid) {
    return (
      <main className="flex min-h-[100svh] items-center justify-center px-4 py-12">
        <Card className="w-full max-w-md">
          <CardHeader>
            <CardTitle>Invalid invitation</CardTitle>
            <CardDescription>
              This invitation link is invalid, has already been used, or has
              expired.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button render={<Link href="/login" />}>Log in</Button>
          </CardContent>
        </Card>
      </main>
    );
  }

  return (
    <main className="flex min-h-[100svh] items-center justify-center px-4 py-12">
      <JoinInviteForm token={token} invite={body.data} />
    </main>
  );
}
