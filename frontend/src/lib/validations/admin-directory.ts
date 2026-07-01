import { z } from "zod";

export const adminDirectoryGranularitySchema = z.enum(["month", "week", "custom"]);

export const adminDirectoryQuerySchema = z.object({
  page: z.coerce.number().int().min(1).default(1),
  search: z.string().max(200).default(""),
  granularity: adminDirectoryGranularitySchema.default("month"),
  from: z.string().optional(),
  to: z.string().optional(),
});

export type AdminDirectoryQuery = z.infer<typeof adminDirectoryQuerySchema>;

export const adminDeleteIdSchema = z.object({
  id: z.string().uuid("Invalid ID."),
});

export function parseAdminDeleteFormData(formData: FormData) {
  return adminDeleteIdSchema.safeParse({
    id: formData.get("id"),
  });
}

export function parseAdminDirectorySearchParams(
  params: Record<string, string | string[] | undefined>,
) {
  return adminDirectoryQuerySchema.safeParse({
    page: params.page,
    search: params.search,
    granularity: params.granularity,
    from: params.from,
    to: params.to,
  });
}
