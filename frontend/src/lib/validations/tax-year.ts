import { z } from "zod";

import { TAX_YEAR_MAX, TAX_YEAR_MIN } from "@/lib/tax-year";

export const taxYearSchema = z
  .number({ error: "Invalid tax year" })
  .int()
  .min(TAX_YEAR_MIN, "Invalid tax year")
  .max(TAX_YEAR_MAX, "Invalid tax year");

export const taxYearQuerySchema = z
  .union([z.string(), z.number()])
  .transform((value) => (typeof value === "string" ? Number(value) : value))
  .pipe(taxYearSchema);

export const optionalTaxYearQuerySchema = z
  .union([z.string(), z.number()])
  .transform((value) => (typeof value === "string" ? Number(value) : value))
  .pipe(taxYearSchema)
  .optional();

export type TaxYear = z.infer<typeof taxYearSchema>;
