"use server";

import { redirect } from "next/navigation";

import type { InviteAcceptActionState } from "@/actions/org.types";
import { initialInviteAcceptActionState } from "@/actions/org.types";
import { acceptInviteWithFastApi } from "@/lib/api/org";
import { parseInviteAcceptFormData } from "@/lib/validations/org";

function flattenFieldErrors(
  fieldErrors: Record<string, string[] | undefined>,
): Record<string, string[]> {
  return Object.fromEntries(
    Object.entries(fieldErrors)
      .filter((entry): entry is [string, string[]] => !!entry[1]?.length)
      .map(([key, messages]) => [key, messages]),
  );
}

export async function acceptInviteAction(
  _prevState: InviteAcceptActionState,
  formData: FormData,
): Promise<InviteAcceptActionState> {
  const parsed = parseInviteAcceptFormData(formData);

  if (!parsed.success) {
    return {
      fieldErrors: flattenFieldErrors(parsed.error.flatten().fieldErrors),
    };
  }

  const { body } = await acceptInviteWithFastApi({
    token: parsed.data.token,
    email: parsed.data.email.toLowerCase(),
    password: parsed.data.password,
    full_name: parsed.data.full_name.trim(),
  });

  if (!body.success) {
    return { error: body.message };
  }

  redirect("/dashboard");
}

export { initialInviteAcceptActionState };
