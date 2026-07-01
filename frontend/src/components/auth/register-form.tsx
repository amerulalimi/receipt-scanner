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
import { toast } from "sonner";

import { registerAction } from "@/actions/auth";
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
  FieldDescription,
  FieldError,
  FieldGroup,
  FieldLabel,
} from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  registerSchema,
  type RegisterFormValues,
} from "@/lib/validations/auth";
import { useTranslations } from "@/lib/i18n/use-translations";

export function RegisterForm() {
  const t = useTranslations("auth");
  const [showPassword, setShowPassword] = useState(false);
  const [state, submitAction, isPending] = useActionState(
    registerAction,
    initialAuthState,
  );

  const form = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      email: "",
      password: "",
      full_name: "",
      account_type: "individual",
    },
  });

  useEffect(() => {
    if (!state.fieldErrors) {
      return;
    }

    for (const [field, messages] of Object.entries(state.fieldErrors)) {
      if (messages[0]) {
        form.setError(field as keyof RegisterFormValues, {
          message: messages[0],
        });
      }
    }
  }, [state.fieldErrors, form]);

  useEffect(() => {
    if (state.errorCode === "EMAIL_EXISTS") {
      toast.error(state.error);
    }
  }, [state.error, state.errorCode]);

  function onSubmit(values: RegisterFormValues) {
    const formData = new FormData();
    formData.set("email", values.email);
    formData.set("password", values.password);
    formData.set("full_name", values.full_name);
    formData.set("account_type", values.account_type);

    startTransition(() => {
      submitAction(formData);
    });
  }

  return (
    <Card className="w-full max-w-md">
      <CardHeader>
        <CardTitle>{t("registerTitle")}</CardTitle>
        <CardDescription>{t("registerSubtitle")}</CardDescription>
      </CardHeader>
      <CardContent>
        {state.error && state.errorCode !== "EMAIL_EXISTS" ? (
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
              name="full_name"
              control={form.control}
              render={({ field, fieldState }) => (
                <Field data-invalid={!!fieldState.error}>
                  <FieldLabel htmlFor="register-full-name">
                    {t("full_name")}
                  </FieldLabel>
                  <Input
                    id="register-full-name"
                    type="text"
                    autoComplete="name"
                    placeholder="Ahmad bin Ali"
                    aria-invalid={!!fieldState.error}
                    {...field}
                  />
                  <FieldError errors={[fieldState.error]} />
                </Field>
              )}
            />

            <Controller
              name="email"
              control={form.control}
              render={({ field, fieldState }) => (
                <Field data-invalid={!!fieldState.error}>
                  <FieldLabel htmlFor="register-email">{t("email")}</FieldLabel>
                  <Input
                    id="register-email"
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
                  <FieldLabel htmlFor="register-password">
                    {t("password")}
                  </FieldLabel>
                  <div className="relative">
                    <Input
                      id="register-password"
                      type={showPassword ? "text" : "password"}
                      autoComplete="new-password"
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
                  <FieldDescription>{t("password_min")}</FieldDescription>
                  <FieldError errors={[fieldState.error]} />
                </Field>
              )}
            />

            <Controller
              name="account_type"
              control={form.control}
              render={({ field, fieldState }) => (
                <Field data-invalid={!!fieldState.error}>
                  <FieldLabel>{t("account_type")}</FieldLabel>
                  <Tabs
                    value={field.value}
                    onValueChange={(value) =>
                      field.onChange(value as RegisterFormValues["account_type"])
                    }
                    className="w-full"
                  >
                    <TabsList className="grid h-auto w-full grid-cols-2">
                      <TabsTrigger value="individual" className="py-2">
                        {t("individual")}
                      </TabsTrigger>
                      <TabsTrigger value="corporate" className="py-2">
                        {t("corporate")}
                      </TabsTrigger>
                    </TabsList>
                  </Tabs>
                  <FieldError errors={[fieldState.error]} />
                </Field>
              )}
            />

            <Button type="submit" className="w-full" disabled={isPending}>
              {isPending ? t("registering") : t("registerButton")}
            </Button>
          </FieldGroup>
        </form>
      </CardContent>
      <CardFooter className="justify-center text-sm text-muted-foreground">
        {t("hasAccount")}{" "}
        <Link
          href="/login"
          className="ml-1 font-medium text-primary hover:underline"
        >
          {t("loginButton")}
        </Link>
      </CardFooter>
    </Card>
  );
}
