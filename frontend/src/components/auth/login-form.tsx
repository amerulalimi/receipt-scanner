"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import Link from "next/link";
import {
  startTransition,
  useActionState,
  useEffect,
} from "react";
import { Controller, useForm } from "react-hook-form";

import { loginAction } from "@/actions/auth";
import { initialAuthState } from "@/actions/auth.types";
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
import {
  loginSchema,
  type LoginFormValues,
} from "@/lib/validations/auth";
import { useTranslations } from "@/lib/i18n/use-translations";

type LoginFormProps = {
  redirectTo?: string;
  registered?: boolean;
};

export function LoginForm({ redirectTo, registered }: LoginFormProps) {
  const t = useTranslations("auth");
  const [state, submitAction, isPending] = useActionState(
    loginAction,
    initialAuthState,
  );

  const form = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: "",
      password: "",
    },
  });

  useEffect(() => {
    if (!state.fieldErrors) {
      return;
    }

    for (const [field, messages] of Object.entries(state.fieldErrors)) {
      if (messages[0]) {
        form.setError(field as keyof LoginFormValues, { message: messages[0] });
      }
    }
  }, [state.fieldErrors, form]);

  function onSubmit(values: LoginFormValues) {
    const formData = new FormData();
    formData.set("email", values.email);
    formData.set("password", values.password);
    if (redirectTo) {
      formData.set("redirect", redirectTo);
    }

    startTransition(() => {
      submitAction(formData);
    });
  }

  return (
    <Card className="w-full max-w-md">
      <CardHeader>
        <CardTitle>{t("loginTitle")}</CardTitle>
        <CardDescription>{t("loginSubtitle")}</CardDescription>
      </CardHeader>
      <CardContent>
        {registered ? (
          <p
            role="status"
            className="mb-4 rounded-lg border border-primary/20 bg-primary/5 px-3 py-2 text-sm text-foreground"
          >
            {t("loginSuccessRegistered")}
          </p>
        ) : null}

        {state.error ? (
          <p
            role="alert"
            className="mb-4 rounded-lg border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive"
          >
            {state.error}
          </p>
        ) : null}

        <form onSubmit={form.handleSubmit(onSubmit)}>
          <FieldGroup>
            <Controller
              name="email"
              control={form.control}
              render={({ field, fieldState }) => (
                <Field data-invalid={!!fieldState.error}>
                  <FieldLabel htmlFor="login-email">{t("email")}</FieldLabel>
                  <Input
                    id="login-email"
                    type="email"
                    autoComplete="email"
                    placeholder="you@example.com"
                    aria-invalid={!!fieldState.error}
                    {...field}
                  />
                  <FieldError errors={[fieldState.error]} />
                </Field>
              )}
            />

            <Controller
              name="password"
              control={form.control}
              render={({ field, fieldState }) => (
                <Field data-invalid={!!fieldState.error}>
                  <FieldLabel htmlFor="login-password">{t("password")}</FieldLabel>
                  <Input
                    id="login-password"
                    type="password"
                    autoComplete="current-password"
                    aria-invalid={!!fieldState.error}
                    {...field}
                  />
                  <FieldError errors={[fieldState.error]} />
                </Field>
              )}
            />

            <Button type="submit" className="w-full" disabled={isPending}>
              {isPending ? t("loggingIn") : t("loginButton")}
            </Button>
          </FieldGroup>
        </form>
      </CardContent>
      <CardFooter className="justify-center text-sm text-muted-foreground">
        {t("noAccount")}{" "}
        <Link
          href="/register"
          className="ml-1 font-medium text-primary hover:underline"
        >
          {t("registerButton")}
        </Link>
      </CardFooter>
    </Card>
  );
}
