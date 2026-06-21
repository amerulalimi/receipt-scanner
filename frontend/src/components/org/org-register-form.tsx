"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import {
  startTransition,
  useActionState,
  useEffect,
} from "react";
import { Controller, useForm } from "react-hook-form";

import {
  initialOrgActionState,
  registerOrgAction,
} from "@/actions/org";
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
  FieldDescription,
  FieldError,
  FieldGroup,
  FieldLabel,
} from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import {
  orgRegisterSchema,
  type OrgRegisterFormValues,
} from "@/lib/validations/org";

export function OrgRegisterForm({ userEmail }: { userEmail: string }) {
  const [state, submitAction, isPending] = useActionState(
    registerOrgAction,
    initialOrgActionState,
  );

  const emailDomain = userEmail.includes("@")
    ? userEmail.split("@")[1]
    : "";

  const form = useForm<OrgRegisterFormValues>({
    resolver: zodResolver(orgRegisterSchema),
    defaultValues: {
      name: "",
      ssm_number: "",
      email_domain: emailDomain,
    },
  });

  useEffect(() => {
    if (!state.fieldErrors) {
      return;
    }

    for (const [field, messages] of Object.entries(state.fieldErrors)) {
      if (messages[0]) {
        form.setError(field as keyof OrgRegisterFormValues, {
          message: messages[0],
        });
      }
    }
  }, [state.fieldErrors, form]);

  function onSubmit(values: OrgRegisterFormValues) {
    const formData = new FormData();
    formData.set("name", values.name);
    formData.set("ssm_number", values.ssm_number);
    formData.set("email_domain", values.email_domain);

    startTransition(() => {
      submitAction(formData);
    });
  }

  return (
    <Card className="max-w-xl">
      <CardHeader>
        <CardTitle>Register Organization</CardTitle>
        <CardDescription>
          Register your company to manage employees and tax claim policies.
          Your email ({userEmail}) must match the company domain.
        </CardDescription>
      </CardHeader>
      <form onSubmit={form.handleSubmit(onSubmit)}>
        <CardContent>
          <FieldGroup>
            <Controller
              control={form.control}
              name="name"
              render={({ field, fieldState }) => (
                <Field data-invalid={fieldState.invalid}>
                  <FieldLabel htmlFor="org-name">Company name</FieldLabel>
                  <Input
                    id="org-name"
                    placeholder="ABC Company Sdn Bhd"
                    {...field}
                  />
                  <FieldError errors={[fieldState.error]} />
                </Field>
              )}
            />

            <Controller
              control={form.control}
              name="ssm_number"
              render={({ field, fieldState }) => (
                <Field data-invalid={fieldState.invalid}>
                  <FieldLabel htmlFor="org-ssm">SSM number</FieldLabel>
                  <Input
                    id="org-ssm"
                    placeholder="202301012345"
                    {...field}
                  />
                  <FieldError errors={[fieldState.error]} />
                </Field>
              )}
            />

            <Controller
              control={form.control}
              name="email_domain"
              render={({ field, fieldState }) => (
                <Field data-invalid={fieldState.invalid}>
                  <FieldLabel htmlFor="org-domain">Email domain</FieldLabel>
                  <Input
                    id="org-domain"
                    placeholder="company.com.my"
                    {...field}
                  />
                  <FieldDescription>
                    Employees must use an @{field.value || "domain"} email.
                  </FieldDescription>
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
          <Button type="submit" disabled={isPending}>
            {isPending ? "Registering…" : "Register organization"}
          </Button>
        </CardFooter>
      </form>
    </Card>
  );
}
