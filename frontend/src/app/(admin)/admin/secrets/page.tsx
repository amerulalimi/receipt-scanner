import { OpenRouterHealthCard } from "@/components/admin/openrouter-health-card";
import { SecretSettingForm } from "@/components/admin/secret-setting-form";
import {
  fetchOpenRouterHealth,
  listSecretsWithFastApi,
} from "@/lib/api/admin-config";

export const metadata = {
  title: "API Secrets — Admin",
};

export default async function AdminSecretsPage() {
  const [secretsResult, healthResult] = await Promise.all([
    listSecretsWithFastApi(),
    fetchOpenRouterHealth(),
  ]);
  const secrets = secretsResult.body.success ? secretsResult.body.data : [];
  const health =
    healthResult.body.success && healthResult.body.data
      ? healthResult.body.data
      : null;

  return (
    <main className="space-y-6">
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold tracking-tight">API Secrets</h1>
        <p className="text-sm text-muted-foreground">
          Store API keys securely. Values are encrypted in the database and only
          shown in masked form.
        </p>
      </header>

      {health ? <OpenRouterHealthCard health={health} /> : null}

      <div className="space-y-4">
        {secrets.map((setting) => (
          <SecretSettingForm key={setting.key} setting={setting} />
        ))}
      </div>
    </main>
  );
}
