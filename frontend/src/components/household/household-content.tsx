"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { startTransition, useActionState, useEffect } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";

import {
  dissolveSpouseLinkAction,
  initialHouseholdActionState,
  requestSpouseLinkAction,
  respondSpouseLinkAction,
} from "@/actions/household";
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
import type { HouseholdOverviewData } from "@/lib/api/types";
import { getCategoryLabel } from "@/lib/constants/receipts";
import { useTranslations } from "@/lib/i18n/use-translations";
import {
  spouseLinkRequestSchema,
  type SpouseLinkRequestFormValues,
} from "@/lib/validations/household";

type HouseholdContentProps = {
  household: HouseholdOverviewData;
  currentUserId: string;
  categoryLabels: Record<string, string>;
};

function formatRinggit(value: number | string): string {
  return new Intl.NumberFormat("en-MY", {
    style: "currency",
    currency: "MYR",
    minimumFractionDigits: 2,
  }).format(Number(value));
}

function formatDate(value: string): string {
  return new Intl.DateTimeFormat("en-MY", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export function HouseholdContent({
  household,
  currentUserId,
  categoryLabels,
}: HouseholdContentProps) {
  const t = useTranslations("household");
  const [requestState, requestAction, requestPending] = useActionState(
    requestSpouseLinkAction,
    initialHouseholdActionState,
  );
  const [respondState, respondAction, respondPending] = useActionState(
    respondSpouseLinkAction,
    initialHouseholdActionState,
  );
  const [dissolveState, dissolveAction, dissolvePending] = useActionState(
    dissolveSpouseLinkAction,
    initialHouseholdActionState,
  );

  const form = useForm<SpouseLinkRequestFormValues>({
    resolver: zodResolver(spouseLinkRequestSchema),
    defaultValues: { partner_email: "" },
  });

  useEffect(() => {
    if (requestState.fieldErrors?.partner_email?.[0]) {
      form.setError("partner_email", {
        message: requestState.fieldErrors.partner_email[0],
      });
    }
  }, [requestState.fieldErrors, form]);

  useEffect(() => {
    if (requestState.success && requestState.message) {
      toast.success(requestState.message);
      form.reset();
    }
    if (requestState.error) {
      toast.error(requestState.error);
    }
  }, [requestState, form]);

  useEffect(() => {
    if (respondState.success && respondState.message) {
      toast.success(respondState.message);
    }
    if (respondState.error) {
      toast.error(respondState.error);
    }
  }, [respondState]);

  useEffect(() => {
    if (dissolveState.success && dissolveState.message) {
      toast.success(dissolveState.message);
    }
    if (dissolveState.error) {
      toast.error(dissolveState.error);
    }
  }, [dissolveState]);

  function submitLinkRequest(values: SpouseLinkRequestFormValues) {
    const formData = new FormData();
    formData.set("partner_email", values.partner_email);
    startTransition(() => requestAction(formData));
  }

  function submitRespond(linkId: string, action: "accept" | "reject") {
    const formData = new FormData();
    formData.set("link_id", linkId);
    formData.set("action", action);
    startTransition(() => respondAction(formData));
  }

  function submitDissolve(linkId: string) {
    const formData = new FormData();
    formData.set("link_id", linkId);
    startTransition(() => dissolveAction(formData));
  }

  const selfMember = household.combined?.members.find(
    (member) => member.user_id === currentUserId,
  );
  const partnerMember =
    household.partner ??
    household.combined?.members.find(
      (member) => member.user_id !== currentUserId,
    ) ??
    null;

  return (
    <div className="space-y-6">
      {household.incoming_requests.length > 0 ? (
        <Card>
          <CardHeader>
            <CardTitle>{t("incomingTitle")}</CardTitle>
            <CardDescription>{t("incomingDescription")}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {household.incoming_requests.map((request) => (
              <div
                key={request.id}
                className="flex flex-wrap items-center justify-between gap-3 rounded-lg border p-3"
              >
                <div>
                  <p className="font-medium">
                    {request.requester_name ?? request.requester_email}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    {request.requester_email} · {formatDate(request.created_at)}
                  </p>
                </div>
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    disabled={respondPending}
                    onClick={() => submitRespond(request.id, "accept")}
                  >
                    {t("accept")}
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={respondPending}
                    onClick={() => submitRespond(request.id, "reject")}
                  >
                    {t("reject")}
                  </Button>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      ) : null}

      {household.outgoing_request ? (
        <Card>
          <CardHeader>
            <CardTitle>{t("outgoingTitle")}</CardTitle>
            <CardDescription>{t("outgoingDescription")}</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="font-medium">{household.outgoing_request.partner_email}</p>
              <p className="text-sm text-muted-foreground">
                {formatDate(household.outgoing_request.created_at)}
              </p>
            </div>
            <Button
              size="sm"
              variant="outline"
              disabled={dissolvePending}
              onClick={() => submitDissolve(household.outgoing_request!.id)}
            >
              {t("cancelRequest")}
            </Button>
          </CardContent>
        </Card>
      ) : null}

      {!household.partner && !household.outgoing_request ? (
        <Card>
          <CardHeader>
            <CardTitle>{t("linkTitle")}</CardTitle>
            <CardDescription>{t("linkDescription")}</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={form.handleSubmit(submitLinkRequest)}>
              <FieldGroup>
                <Field>
                  <FieldLabel htmlFor="partner_email">{t("partnerEmail")}</FieldLabel>
                  <Input
                    id="partner_email"
                    type="email"
                    placeholder="spouse@example.com"
                    {...form.register("partner_email")}
                  />
                  <FieldError errors={[form.formState.errors.partner_email]} />
                </Field>
                <Button type="submit" disabled={requestPending}>
                  {requestPending ? t("sending") : t("sendRequest")}
                </Button>
              </FieldGroup>
            </form>
          </CardContent>
        </Card>
      ) : null}

      {household.partner && household.accepted_link_id ? (
        <Card>
          <CardHeader className="flex flex-row items-start justify-between gap-3">
            <div>
              <CardTitle>{t("linkedTitle")}</CardTitle>
              <CardDescription>
                {household.partner.full_name ?? household.partner.email}
              </CardDescription>
            </div>
            <Button
              size="sm"
              variant="outline"
              disabled={dissolvePending}
              onClick={() => submitDissolve(household.accepted_link_id!)}
            >
              {t("unlink")}
            </Button>
          </CardHeader>
          <CardContent className="space-y-4">
            {household.combined ? (
              <div className="rounded-lg border bg-muted/30 p-4">
                <p className="text-sm text-muted-foreground">
                  {t("combinedTotal", { year: household.combined.tax_year })}
                </p>
                <p className="text-2xl font-semibold tabular-nums">
                  {formatRinggit(household.combined.combined_total_claimed)}
                </p>
              </div>
            ) : null}

            <div className="grid gap-4 md:grid-cols-2">
              {[selfMember, partnerMember]
                .filter((member): member is NonNullable<typeof member> => member !== null)
                .map((member) => (
                  <div key={member.user_id} className="rounded-lg border p-4">
                    <p className="font-medium">
                      {member.full_name ?? member.email}
                      {member.user_id === currentUserId ? (
                        <span className="ml-2 text-xs text-muted-foreground">
                          ({t("you")})
                        </span>
                      ) : null}
                    </p>
                    <p className="text-sm text-muted-foreground">{member.email}</p>
                    <p className="mt-2 text-lg font-semibold tabular-nums">
                      {formatRinggit(member.total_claimed)}
                    </p>
                    {member.categories.length > 0 ? (
                      <ul className="mt-3 space-y-1 text-sm">
                        {member.categories.map((category) => (
                          <li
                            key={`${member.user_id}-${category.category}`}
                            className="flex justify-between gap-2"
                          >
                            <span>
                              {getCategoryLabel(category.category, categoryLabels)}
                            </span>
                            <span className="tabular-nums text-muted-foreground">
                              {formatRinggit(category.claimed)} ({category.receipt_count})
                            </span>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="mt-2 text-sm text-muted-foreground">
                        {t("noCategories")}
                      </p>
                    )}
                  </div>
                ))}
            </div>
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}
