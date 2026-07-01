"use client";

import { useForm } from "@tanstack/react-form";
import { Eye, EyeOff, Shield } from "lucide-react";
import {
  startTransition,
  useActionState,
  useEffect,
  useState,
} from "react";

import { adminLoginAction } from "@/actions/admin-auth";
import { initialAdminAuthState } from "@/actions/admin-auth.types";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
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
  adminLoginSchema,
  type AdminLoginFormValues,
} from "@/lib/validations/admin-auth";

type AdminLoginFormProps = {
  redirectTo?: string;
};

export function AdminLoginForm({ redirectTo }: AdminLoginFormProps) {
  const [showPassword, setShowPassword] = useState(false);
  const [state, submitAction, isPending] = useActionState(
    adminLoginAction,
    initialAdminAuthState,
  );

  const form = useForm({
    defaultValues: {
      email: "",
      password: "",
    } satisfies AdminLoginFormValues,
    validators: {
      onChange: adminLoginSchema,
    },
    onSubmit: async ({ value }) => {
      const formData = new FormData();
      formData.set("email", value.email);
      formData.set("password", value.password);
      if (redirectTo) {
        formData.set("redirect", redirectTo);
      }
      startTransition(() => {
        submitAction(formData);
      });
    },
  });

  useEffect(() => {
    if (!state.fieldErrors) {
      return;
    }

    for (const [field, messages] of Object.entries(state.fieldErrors)) {
      if (messages[0] && (field === "email" || field === "password")) {
        form.setFieldMeta(field, (prev) => ({
          ...prev,
          errorMap: {
            ...prev.errorMap,
            onServer: messages[0],
          },
        }));
      }
    }
  }, [state.fieldErrors, form]);

  const serverError =
    state.errorCode === "INVALID_CREDENTIALS"
      ? "E-mel atau kata laluan tidak sah."
      : state.error;

  return (
    <Card className="w-full max-w-md">
      <CardHeader className="text-center">
        <div className="mx-auto mb-2 flex size-10 items-center justify-center rounded-lg bg-primary text-primary-foreground">
          <Shield className="size-5" />
        </div>
        <CardTitle>Admin Resit.my</CardTitle>
        <CardDescription>Log masuk ke panel pentadbir platform</CardDescription>
      </CardHeader>
      <CardContent>
        <form
          onSubmit={(event) => {
            event.preventDefault();
            event.stopPropagation();
            void form.handleSubmit();
          }}
        >
          <FieldGroup>
            <form.Field name="email">
              {(field) => (
                <Field data-invalid={field.state.meta.errors.length > 0}>
                  <FieldLabel htmlFor={field.name}>E-mel</FieldLabel>
                  <Input
                    id={field.name}
                    type="email"
                    autoComplete="username"
                    value={field.state.value}
                    onBlur={field.handleBlur}
                    onChange={(event) => field.handleChange(event.target.value)}
                  />
                  <FieldError>
                    {field.state.meta.errors[0]?.toString() ??
                      (typeof field.state.meta.errorMap.onServer === "string"
                        ? field.state.meta.errorMap.onServer
                        : undefined)}
                  </FieldError>
                </Field>
              )}
            </form.Field>

            <form.Field name="password">
              {(field) => (
                <Field data-invalid={field.state.meta.errors.length > 0}>
                  <FieldLabel htmlFor={field.name}>Kata laluan</FieldLabel>
                  <div className="relative">
                    <Input
                      id={field.name}
                      type={showPassword ? "text" : "password"}
                      autoComplete="current-password"
                      value={field.state.value}
                      onBlur={field.handleBlur}
                      onChange={(event) =>
                        field.handleChange(event.target.value)
                      }
                      className="pr-10"
                    />
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      className="absolute top-0 right-0 h-full px-3 hover:bg-transparent"
                      onClick={() => setShowPassword((current) => !current)}
                      aria-label={
                        showPassword ? "Sembunyikan kata laluan" : "Tunjuk kata laluan"
                      }
                    >
                      {showPassword ? (
                        <EyeOff className="size-4" />
                      ) : (
                        <Eye className="size-4" />
                      )}
                    </Button>
                  </div>
                  <FieldError>
                    {field.state.meta.errors[0]?.toString() ??
                      (typeof field.state.meta.errorMap.onServer === "string"
                        ? field.state.meta.errorMap.onServer
                        : undefined)}
                  </FieldError>
                </Field>
              )}
            </form.Field>

            {serverError ? (
              <p className="text-sm text-destructive" role="alert">
                {serverError}
              </p>
            ) : null}

            <Button type="submit" className="w-full" disabled={isPending}>
              {isPending ? "Log masuk…" : "Log masuk"}
            </Button>
          </FieldGroup>
        </form>
      </CardContent>
    </Card>
  );
}
