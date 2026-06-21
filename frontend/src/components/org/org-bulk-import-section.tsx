"use client";

import { CopyIcon } from "lucide-react";
import { startTransition, useActionState, useEffect, useState } from "react";

import {
  bulkImportEmployeesAction,
  initialOrgActionState,
} from "@/actions/org";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useTranslations } from "@/lib/i18n/use-translations";
import type { OrgEmployeeBulkImportRow } from "@/lib/api/types";

type OrgBulkImportSectionProps = {
  emailDomain: string;
};

function parseCsvText(text: string): OrgEmployeeBulkImportRow[] {
  const lines = text
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);

  if (lines.length === 0) {
    return [];
  }

  const rows: OrgEmployeeBulkImportRow[] = [];

  for (const line of lines) {
    const parts = line.split(",").map((part) => part.trim().replace(/^"|"$/g, ""));
    const [email, fullName, employeeCode] = parts;

    if (!email || !email.includes("@")) {
      continue;
    }

    rows.push({
      email: email.toLowerCase(),
      full_name: fullName && fullName.length > 0 ? fullName : undefined,
      employee_code:
        employeeCode && employeeCode.length > 0 ? employeeCode : undefined,
    });
  }

  return rows;
}

export function OrgBulkImportSection({ emailDomain }: OrgBulkImportSectionProps) {
  const t = useTranslations("orgBulkImport");
  const [state, submitAction, isPending] = useActionState(
    bulkImportEmployeesAction,
    initialOrgActionState,
  );
  const [csvText, setCsvText] = useState("");
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (state.success) {
      setCsvText("");
    }
  }, [state.success]);

  async function copyInviteUrl(url: string) {
    await navigator.clipboard.writeText(url);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 2000);
  }

  function handleFileUpload(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }

    const reader = new FileReader();
    reader.onload = () => {
      if (typeof reader.result === "string") {
        setCsvText(reader.result);
      }
    };
    reader.readAsText(file);
    event.target.value = "";
  }

  function handleSubmit() {
    const employees = parseCsvText(csvText);
    const formData = new FormData();
    formData.set("employees", JSON.stringify(employees));
    startTransition(() => submitAction(formData));
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("title")}</CardTitle>
        <CardDescription>
          {t("description", { domain: emailDomain })}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <p className="text-sm font-medium">{t("formatHint")}</p>
          <p className="font-mono text-xs text-muted-foreground">
            email,full_name,employee_code
          </p>
        </div>

        <textarea
          value={csvText}
          onChange={(event) => setCsvText(event.target.value)}
          placeholder={`employee@${emailDomain},Ahmad Ali,EMP001`}
          rows={6}
          className="flex min-h-[120px] w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-xs outline-none focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50"
        />

        <div className="flex flex-wrap gap-3">
          <Input
            type="file"
            accept=".csv,text/csv"
            onChange={handleFileUpload}
            className="max-w-xs"
          />
          <Button
            type="button"
            disabled={isPending || csvText.trim().length === 0}
            onClick={handleSubmit}
          >
            {isPending ? t("importing") : t("import")}
          </Button>
        </div>

        {state.error ? (
          <p className="text-sm text-destructive">{state.error}</p>
        ) : null}

        {state.success && state.message ? (
          <p className="text-sm text-primary">{state.message}</p>
        ) : null}

        {state.inviteUrl ? (
          <div className="flex flex-wrap items-center gap-2 rounded-md border bg-muted/40 p-3 text-sm">
            <span className="truncate font-mono">{state.inviteUrl}</span>
            <Button
              type="button"
              size="sm"
              variant="outline"
              onClick={() => copyInviteUrl(state.inviteUrl!)}
            >
              <CopyIcon className="size-4" />
              {copied ? t("copied") : t("copyLink")}
            </Button>
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}
