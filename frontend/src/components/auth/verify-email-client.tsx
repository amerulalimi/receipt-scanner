"use client";

import Link from "next/link";
import { startTransition, useActionState, useEffect } from "react";

import {
  verifyEmailAction,
  type VerifyEmailActionState,
} from "@/actions/auth";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

const initialState: VerifyEmailActionState = {};

type VerifyEmailClientProps = {
  token: string | null;
};

export function VerifyEmailClient({ token }: VerifyEmailClientProps) {
  const [state, submitAction, isPending] = useActionState(
    verifyEmailAction,
    initialState,
  );

  useEffect(() => {
    if (!token || state.success || state.error) {
      return;
    }

    const formData = new FormData();
    formData.set("token", token);
    startTransition(() => submitAction(formData));
  }, [token, state.success, state.error, submitAction]);

  if (!token) {
    return (
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Token not found</CardTitle>
          <CardDescription>
            The verification link is invalid. Request a new email after signing
            in.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button render={<Link href="/login" />}>Log in</Button>
        </CardContent>
      </Card>
    );
  }

  if (isPending) {
    return (
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Verifying email…</CardTitle>
        </CardHeader>
      </Card>
    );
  }

  if (state.success) {
    return (
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Email verified</CardTitle>
          <CardDescription>
            Your account has been verified. You can log in and start using
            Resit.my.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button render={<Link href="/login" />}>Log in</Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-full max-w-md">
      <CardHeader>
        <CardTitle>Verification failed</CardTitle>
        <CardDescription>
          {state.error ??
            "Invalid or expired token. Log in and resend the verification email."}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Button render={<Link href="/login" />}>Log in</Button>
      </CardContent>
    </Card>
  );
}
