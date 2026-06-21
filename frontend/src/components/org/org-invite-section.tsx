"use client";

import { CopyIcon } from "lucide-react";
import {
  startTransition,
  useActionState,
  useEffect,
  useState,
} from "react";
import { useForm } from "react-hook-form";

import {
  initialOrgActionState,
  inviteEmployeesAction,
  inviteHrAdminAction,
} from "@/actions/org";
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
  FieldDescription,
  FieldError,
  FieldGroup,
  FieldLabel,
} from "@/components/ui/field";
import { Input } from "@/components/ui/input";

export function OrgInviteSection({
  emailDomain,
  isSuperadmin,
}: {
  emailDomain: string;
  isSuperadmin: boolean;
}) {
  const [employeeState, employeeAction, employeePending] = useActionState(
    inviteEmployeesAction,
    initialOrgActionState,
  );
  const [hrState, hrAction, hrPending] = useActionState(
    inviteHrAdminAction,
    initialOrgActionState,
  );
  const [copied, setCopied] = useState(false);

  const employeeForm = useForm<{ emails: string }>({
    defaultValues: { emails: "" },
  });
  const hrForm = useForm<{ email: string }>({
    defaultValues: { email: "" },
  });

  useEffect(() => {
    if (employeeState.fieldErrors?.emails?.[0]) {
      employeeForm.setError("emails", {
        message: employeeState.fieldErrors.emails[0],
      });
    }
  }, [employeeState.fieldErrors, employeeForm]);

  useEffect(() => {
    if (hrState.fieldErrors?.email?.[0]) {
      hrForm.setError("email", { message: hrState.fieldErrors.email[0] });
    }
  }, [hrState.fieldErrors, hrForm]);

  async function copyInviteUrl(url: string) {
    await navigator.clipboard.writeText(url);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 2000);
  }

  function createLinkInvite() {
    const formData = new FormData();
    formData.set("type", "link");
    startTransition(() => {
      employeeAction(formData);
    });
  }

  function submitEmailInvites(values: { emails: string }) {
    const formData = new FormData();
    formData.set("type", "email");
    formData.set("emails", values.emails);
    startTransition(() => {
      employeeAction(formData);
    });
  }

  function submitHrInvite(values: { email: string }) {
    const formData = new FormData();
    formData.set("email", values.email);
    startTransition(() => {
      hrAction(formData);
    });
  }

  const latestInviteUrl =
    employeeState.inviteUrl ?? hrState.inviteUrl ?? null;

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Invite Employees</CardTitle>
          <CardDescription>
            Employee emails must use the @{emailDomain} domain.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <p className="text-sm font-medium">Open invitation link</p>
            <p className="text-sm text-muted-foreground">
              Generate a link to share with new employees.
            </p>
            <Button
              type="button"
              variant="outline"
              disabled={employeePending}
              onClick={createLinkInvite}
            >
              {employeePending ? "Generating…" : "Generate invitation link"}
            </Button>
          </div>

          <form
            className="space-y-3 border-t pt-4"
            onSubmit={employeeForm.handleSubmit(submitEmailInvites)}
          >
            <FieldGroup>
              <Field>
                <FieldLabel htmlFor="employee-emails">
                  Invite by email
                </FieldLabel>
                <textarea
                  id="employee-emails"
                  className="min-h-24 w-full rounded-md border bg-background px-3 py-2 text-sm"
                  placeholder={`jane@${emailDomain}\njohn@${emailDomain}`}
                  {...employeeForm.register("emails")}
                />
                <FieldDescription>
                  One email per line, or separate with commas.
                </FieldDescription>
                <FieldError
                  errors={[employeeForm.formState.errors.emails]}
                />
              </Field>
              {employeeState.error ? (
                <p className="text-sm text-destructive">{employeeState.error}</p>
              ) : null}
              {employeeState.success ? (
                <p className="text-sm text-emerald-600">
                  {employeeState.message}
                </p>
              ) : null}
              <Button type="submit" disabled={employeePending}>
                {employeePending ? "Sending…" : "Send invitations"}
              </Button>
            </FieldGroup>
          </form>
        </CardContent>
      </Card>

      {isSuperadmin ? (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Invite HR Admin</CardTitle>
            <CardDescription>
              HR admins can manage employees and approve receipts.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form
              className="space-y-3"
              onSubmit={hrForm.handleSubmit(submitHrInvite)}
            >
              <FieldGroup>
                <Field>
                  <FieldLabel htmlFor="hr-email">HR admin email</FieldLabel>
                  <Input
                    id="hr-email"
                    type="email"
                    placeholder={`hr@${emailDomain}`}
                    {...hrForm.register("email")}
                  />
                  <FieldError errors={[hrForm.formState.errors.email]} />
                </Field>
                {hrState.error ? (
                  <p className="text-sm text-destructive">{hrState.error}</p>
                ) : null}
                {hrState.success ? (
                  <p className="text-sm text-emerald-600">{hrState.message}</p>
                ) : null}
                <Button type="submit" disabled={hrPending}>
                  {hrPending ? "Sending…" : "Invite HR admin"}
                </Button>
              </FieldGroup>
            </form>
          </CardContent>
        </Card>
      ) : null}

      {latestInviteUrl ? (
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-base">Invitation Link</CardTitle>
            <CardDescription>
              Copy this link and share it with employees (dev: also in the
              backend log).
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-3 sm:flex-row sm:items-center">
            <code className="flex-1 break-all rounded-md bg-muted px-3 py-2 text-sm">
              {latestInviteUrl}
            </code>
            <Button
              type="button"
              variant="outline"
              onClick={() => copyInviteUrl(latestInviteUrl)}
            >
              <CopyIcon className="mr-2 size-4" />
              {copied ? "Copied" : "Copy"}
            </Button>
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}
