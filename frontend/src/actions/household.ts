"use server";

import { revalidatePath } from "next/cache";

import type { HouseholdActionState } from "@/actions/household.types";
import {
  dissolveSpouseLinkWithFastApi,
  reassignReceiptWithFastApi,
  requestSpouseLinkWithFastApi,
  respondSpouseLinkWithFastApi,
} from "@/lib/api/household";
import { getActionMessage } from "@/lib/i18n/server-action-messages";
import {
  parseReceiptReassignFormData,
  parseSpouseLinkDissolveFormData,
  parseSpouseLinkRequestFormData,
  parseSpouseLinkRespondFormData,
} from "@/lib/validations/household";

function flattenFieldErrors(
  fieldErrors: Record<string, string[] | undefined>,
): Record<string, string[]> {
  return Object.fromEntries(
    Object.entries(fieldErrors)
      .filter((entry): entry is [string, string[]] => !!entry[1]?.length)
      .map(([key, messages]) => [key, messages]),
  );
}

function revalidateHouseholdPaths() {
  revalidatePath("/dashboard/household");
  revalidatePath("/dashboard");
  revalidatePath("/dashboard/receipts");
}

export async function requestSpouseLinkAction(
  _prevState: HouseholdActionState,
  formData: FormData,
): Promise<HouseholdActionState> {
  const parsed = parseSpouseLinkRequestFormData(formData);

  if (!parsed.success) {
    return {
      fieldErrors: flattenFieldErrors(parsed.error.flatten().fieldErrors),
    };
  }

  try {
    const { body } = await requestSpouseLinkWithFastApi({
      partner_email: parsed.data.partner_email.toLowerCase(),
    });

    if (!body.success) {
      return { error: body.message };
    }

    revalidateHouseholdPaths();
    return {
      success: true,
      message: "Spouse link request sent.",
    };
  } catch {
    return {
      error: await getActionMessage("errors", "sessionExpired"),
    };
  }
}

export async function respondSpouseLinkAction(
  _prevState: HouseholdActionState,
  formData: FormData,
): Promise<HouseholdActionState> {
  const parsed = parseSpouseLinkRespondFormData(formData);

  if (!parsed.success) {
    return { error: "Invalid request." };
  }

  try {
    const { body } = await respondSpouseLinkWithFastApi(parsed.data.link_id, {
      action: parsed.data.action,
    });

    if (!body.success) {
      return { error: body.message };
    }

    revalidateHouseholdPaths();
    return {
      success: true,
      message:
        parsed.data.action === "accept"
          ? "Spouse link accepted."
          : "Spouse link request declined.",
    };
  } catch {
    return {
      error: await getActionMessage("errors", "sessionExpired"),
    };
  }
}

export async function dissolveSpouseLinkAction(
  _prevState: HouseholdActionState,
  formData: FormData,
): Promise<HouseholdActionState> {
  const parsed = parseSpouseLinkDissolveFormData(formData);

  if (!parsed.success) {
    return { error: "Invalid request." };
  }

  try {
    const { body } = await dissolveSpouseLinkWithFastApi(parsed.data.link_id);

    if (!body.success) {
      return { error: body.message };
    }

    revalidateHouseholdPaths();
    return {
      success: true,
      message: body.message ?? "Spouse link removed.",
    };
  } catch {
    return {
      error: await getActionMessage("errors", "sessionExpired"),
    };
  }
}

export async function reassignReceiptAction(
  _prevState: HouseholdActionState,
  formData: FormData,
): Promise<HouseholdActionState> {
  const parsed = parseReceiptReassignFormData(formData);

  if (!parsed.success) {
    return { error: "Invalid request." };
  }

  try {
    const { body } = await reassignReceiptWithFastApi(parsed.data.receipt_id, {
      target_user_id: parsed.data.target_user_id,
    });

    if (!body.success) {
      return { error: body.message };
    }

    revalidateHouseholdPaths();
    return {
      success: true,
      message: body.message ?? "Receipt reassigned.",
    };
  } catch {
    return {
      error: await getActionMessage("errors", "sessionExpired"),
    };
  }
}
