"use server";

import { revalidatePath } from "next/cache";

import { deleteAdminOrganizationWithFastApi } from "@/lib/api/admin-organizations";
import { deleteAdminUserWithFastApi } from "@/lib/api/admin-users";
import { parseAdminDeleteFormData } from "@/lib/validations/admin-directory";

export type AdminDirectoryActionState = {
  success?: boolean;
  error?: string;
  message?: string;
};

export async function deleteAdminUserAction(
  _prevState: AdminDirectoryActionState,
  formData: FormData,
): Promise<AdminDirectoryActionState> {
  const parsed = parseAdminDeleteFormData(formData);
  if (!parsed.success) {
    return { error: parsed.error.issues[0]?.message ?? "Invalid request." };
  }

  const { body } = await deleteAdminUserWithFastApi(parsed.data.id);
  if (!body.success) {
    return { error: body.message };
  }

  revalidatePath("/admin/users");
  return { success: true, message: "User deactivated successfully." };
}

export async function deleteAdminOrganizationAction(
  _prevState: AdminDirectoryActionState,
  formData: FormData,
): Promise<AdminDirectoryActionState> {
  const parsed = parseAdminDeleteFormData(formData);
  if (!parsed.success) {
    return { error: parsed.error.issues[0]?.message ?? "Invalid request." };
  }

  const { body } = await deleteAdminOrganizationWithFastApi(parsed.data.id);
  if (!body.success) {
    return { error: body.message };
  }

  revalidatePath("/admin/organizations");
  return { success: true, message: "Organization suspended successfully." };
}
