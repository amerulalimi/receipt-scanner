export function getExportZipUrl(taxYear: number): string {
  return `/api/claims/export-zip?tax_year=${taxYear}`;
}

export function getOrgExportCsvUrl(
  taxYear: number,
  template: "generic" | "sql_payroll" | "kakitangan",
): string {
  const params = new URLSearchParams({
    tax_year: String(taxYear),
    template,
  });
  return `/api/org/export/csv?${params.toString()}`;
}
