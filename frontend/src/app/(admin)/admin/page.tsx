import Link from "next/link";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { listSecretsWithFastApi, listSettingsWithFastApi } from "@/lib/api/admin-config";

export default async function AdminOverviewPage() {
  const [secretsResult, settingsResult] = await Promise.all([
    listSecretsWithFastApi(),
    listSettingsWithFastApi(),
  ]);

  const secrets = secretsResult.body.success ? secretsResult.body.data : [];
  const settings = settingsResult.body.success ? settingsResult.body.data : [];

  const openrouterConfigured = secrets.some(
    (item) => item.key === "openrouter_api_key" && item.is_configured,
  );
  const visionModel =
    settings.find((item) => item.key === "openrouter_vision_model")?.value ??
    "google/gemini-2.5-flash";
  const processingEnabled =
    settings.find((item) => item.key === "receipt_processing_enabled")?.value ??
    "true";

  return (
    <main className="space-y-6">
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold tracking-tight">
          Admin Panel
        </h1>
        <p className="text-sm text-muted-foreground">
          Manage system configuration, API secrets, and AI settings.
        </p>
      </header>

      <div className="grid gap-4 sm:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>OpenRouter</CardTitle>
            <CardDescription>API key & vision model status</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <p>
              API Key:{" "}
              <span
                className={
                  openrouterConfigured ? "text-green-600" : "text-amber-600"
                }
              >
                {openrouterConfigured ? "Configured" : "Not set"}
              </span>
            </p>
            <p>Model: {visionModel}</p>
            <p>
              Processing:{" "}
              {processingEnabled === "true" ? "Enabled" : "Disabled"}
            </p>
            <Link href="/admin/secrets" className="text-primary underline">
              Manage secrets →
            </Link>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Quick Links</CardTitle>
            <CardDescription>Admin configuration pages</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <p>
              <Link href="/admin/secrets" className="text-primary underline">
                API Secrets
              </Link>
            </p>
            <p>
              <Link href="/admin/ai" className="text-primary underline">
                AI & Processing
              </Link>
            </p>
            <p>
              <Link href="/admin/system" className="text-primary underline">
                System & Audit
              </Link>
            </p>
            <p>
              <Link href="/dashboard" className="text-primary underline">
                User dashboard
              </Link>
            </p>
          </CardContent>
        </Card>
      </div>
    </main>
  );
}
