"use client";

import { Download } from "lucide-react";
import { useState } from "react";

import { getOrgExportCsvUrl } from "@/lib/api/export-urls";
import { TaxYearSelect } from "@/components/shared/tax-year-select";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useTranslations } from "@/lib/i18n/use-translations";

const TEMPLATE_OPTIONS = [
  { value: "generic", labelKey: "templateGeneric" },
  { value: "sql_payroll", labelKey: "templateSqlPayroll" },
  { value: "kakitangan", labelKey: "templateKakitangan" },
] as const;

type OrgExportSectionProps = {
  defaultTaxYear: number;
};

export function OrgExportSection({ defaultTaxYear }: OrgExportSectionProps) {
  const t = useTranslations("orgExport");
  const [taxYear, setTaxYear] = useState(defaultTaxYear);
  const [template, setTemplate] =
    useState<(typeof TEMPLATE_OPTIONS)[number]["value"]>("generic");

  const exportUrl = getOrgExportCsvUrl(taxYear, template);
  const templateOptions = TEMPLATE_OPTIONS.map((option) => ({
    value: option.value,
    label: t(option.labelKey),
  }));

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("title")}</CardTitle>
        <CardDescription>{t("description")}</CardDescription>
      </CardHeader>
      <CardContent className="flex flex-wrap items-end gap-4">
        <TaxYearSelect
          value={taxYear}
          onValueChange={setTaxYear}
          label={t("taxYear")}
          anchorYear={defaultTaxYear}
        />

        <div className="space-y-1.5">
          <p className="text-xs font-medium text-muted-foreground">{t("template")}</p>
          <Select
            value={template}
            onValueChange={(value) => {
              if (
                value === "generic" ||
                value === "sql_payroll" ||
                value === "kakitangan"
              ) {
                setTemplate(value);
              }
            }}
            items={templateOptions}
          >
            <SelectTrigger className="min-w-[200px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {templateOptions.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <Button variant="outline" render={<a href={exportUrl} download />} nativeButton={false}>
          <Download className="size-4" />
          {t("download")}
        </Button>
      </CardContent>
    </Card>
  );
}
