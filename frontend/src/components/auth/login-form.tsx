"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { Eye, EyeOff } from "lucide-react";
import Link from "next/link";
import {
  startTransition,
  useActionState,
  useEffect,
  useState,
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
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
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
  const [showPassword, setShowPassword] = useState(false);
  const [state, submitAction, isPending] = useActionState(
    loginAction,
    initialAuthState,
  );

  const form = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: "",
      password: "",
      login_context: "individual",
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

  const serverError =
    state.errorCode === "INVALID_CREDENTIALS" ? t("login_error") : state.error;

  function onSubmit(values: LoginFormValues) {
    const formData = new FormData();
    formData.set("email", values.email);
    formData.set("password", values.password);
    formData.set("login_context", values.login_context);
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
            {t("register_success")}
          </p>
        ) : null}

        {serverError ? (
          <p
            role="alert"
            className="mb-4 rounded-lg border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive"
          >
            {serverError}
          </p>
        ) : null}

        <form onSubmit={form.handleSubmit(onSubmit)}>
          <FieldGroup>
            <Controller
              name="login_context"
              control={form.control}
              render={({ field }) => (
                <Field>
                  <FieldLabel>Pilih jenis log masuk</FieldLabel>
                  <Tabs
                    value={field.value}
                    onValueChange={(value) =>
                      field.onChange(value as LoginFormValues["login_context"])
                    }
                    className="w-full"
                  >
                    <TabsList className="grid h-auto w-full grid-cols-2">
                      <TabsTrigger value="individual" className="py-2">
                        Individual
                      </TabsTrigger>
                      <TabsTrigger value="corporate" className="py-2">
                        Corporate
                      </TabsTrigger>
                    </TabsList>
                  </Tabs>
                </Field>
              )}
            />

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
                    placeholder="anda@example.com"
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
                  <div className="relative">
                    <Input
                      id="login-password"
                      type={showPassword ? "text" : "password"}
                      autoComplete="current-password"
                      aria-invalid={!!fieldState.error}
                      className="pr-10"
                      {...field}
                    />
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      className="absolute right-0 top-0 h-full px-3 hover:bg-transparent"
                      onClick={() => setShowPassword((v) => !v)}
                      aria-label={
                        showPassword ? t("hidePassword") : t("showPassword")
                      }
                    >
                      {showPassword ? (
                        <EyeOff className="size-4" />
                      ) : (
                        <Eye className="size-4" />
                      )}
                    </Button>
                  </div>
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
