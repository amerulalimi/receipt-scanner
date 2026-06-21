"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import {
  startTransition,
  useActionState,
  useEffect,
} from "react";
import { Controller, useForm } from "react-hook-form";

import {
  acceptInviteAction,
  initialInviteAcceptActionState,
} from "@/actions/invite";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Field,
  FieldError,
  FieldGroup,
  FieldLabel,
} from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import type { InviteValidateData } from "@/lib/api/types";
import {
  inviteAcceptSchema,
  type InviteAcceptFormValues,
} from "@/lib/validations/org";
import { getOrgRoleLabel } from "@/components/org/org-overview-section";

export function JoinInviteForm({
  token,
  invite,
}: {
  token: string;
  invite: InviteValidateData;
}) {
  const [state, submitAction, isPending] = useActionState(
    acceptInviteAction,
    initialInviteAcceptActionState,
  );

  const form = useForm<InviteAcceptFormValues>({
    resolver: zodResolver(inviteAcceptSchema),
    defaultValues: {
      token,
      email: invite.invited_email ?? "",
      password: "",
      full_name: "",
    },
  });

  useEffect(() => {
    if (!state.fieldErrors) {
      return;
    }

    for (const [field, messages] of Object.entries(state.fieldErrors)) {
      if (messages[0]) {
        form.setError(field as keyof InviteAcceptFormValues, {
          message: messages[0],
        });
      }
    }
  }, [state.fieldErrors, form]);

  function onSubmit(values: InviteAcceptFormValues) {
    const formData = new FormData();
    formData.set("token", values.token);
    formData.set("email", values.email);
    formData.set("password", values.password);
    formData.set("full_name", values.full_name);

    startTransition(() => {
      submitAction(formData);
    });
  }

  return (
    <Card className="w-full max-w-md">
      <CardHeader>
        <CardTitle>Join {invite.org_name}</CardTitle>
        <CardDescription>
          Register as {getOrgRoleLabel(invite.role ?? "employee")} to start
          managing your tax receipts.
        </CardDescription>
      </CardHeader>
      <form onSubmit={form.handleSubmit(onSubmit)}>
        <CardContent>
          <FieldGroup>
            <input type="hidden" {...form.register("token")} />

            <Controller
              control={form.control}
              name="full_name"
              render={({ field, fieldState }) => (
                <Field data-invalid={fieldState.invalid}>
                  <FieldLabel htmlFor="join-full-name">Full name</FieldLabel>
                  <Input id="join-full-name" {...field} />
                  <FieldError errors={[fieldState.error]} />
                </Field>
              )}
            />

            <Controller
              control={form.control}
              name="email"
              render={({ field, fieldState }) => (
                <Field data-invalid={fieldState.invalid}>
                  <FieldLabel htmlFor="join-email">Email</FieldLabel>
                  <Input
                    id="join-email"
                    type="email"
                    readOnly={Boolean(invite.invited_email)}
                    {...field}
                  />
                  <FieldError errors={[fieldState.error]} />
                </Field>
              )}
            />

            <Controller
              control={form.control}
              name="password"
              render={({ field, fieldState }) => (
                <Field data-invalid={fieldState.invalid}>
                  <FieldLabel htmlFor="join-password">Password</FieldLabel>
                  <Input
                    id="join-password"
                    type="password"
                    autoComplete="new-password"
                    {...field}
                  />
                  <FieldError errors={[fieldState.error]} />
                </Field>
              )}
            />

            {state.error ? (
              <p className="text-sm text-destructive">{state.error}</p>
            ) : null}
          </FieldGroup>
        </CardContent>
        <CardFooter>
          <Button type="submit" className="w-full" disabled={isPending}>
            {isPending ? "Registering…" : "Join organization"}
          </Button>
        </CardFooter>
      </form>
    </Card>
  );
}
