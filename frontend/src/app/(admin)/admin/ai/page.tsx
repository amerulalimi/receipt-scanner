import { AiConfigForm } from "@/components/admin/ai-config-form";
import {
  fetchOpenRouterModels,
  listSecretsWithFastApi,
  listSettingsWithFastApi,
} from "@/lib/api/admin-config";
import type { OpenRouterModelOption } from "@/lib/api/types";

export const metadata = {
  title: "AI & Processing — Admin",
};

export default async function AdminAiPage() {
  const [settingsResult, secretsResult, modelsResult] = await Promise.all([
    listSettingsWithFastApi(),
    listSecretsWithFastApi(),
    fetchOpenRouterModels(),
  ]);

  const settings = settingsResult.body.success ? settingsResult.body.data : [];
  const secrets = secretsResult.body.success ? secretsResult.body.data : [];
  const models: OpenRouterModelOption[] =
    modelsResult.body.success && modelsResult.body.data
      ? modelsResult.body.data.models
      : [];
  const modelsMessage =
    modelsResult.body.success && modelsResult.body.data
      ? modelsResult.body.data.message
      : modelsResult.body.message ?? null;

  return (
    <main className="space-y-6">
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold tracking-tight">
          AI & Processing
        </h1>
        <p className="text-sm text-muted-foreground">
          Configure the OpenRouter vision model for OCR and receipt classification.
        </p>
      </header>

      <AiConfigForm
        settings={settings}
        secrets={secrets}
        models={models}
        modelsMessage={modelsMessage}
      />
    </main>
  );
}
