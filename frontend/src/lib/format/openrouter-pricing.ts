import type { OpenRouterModelOption } from "@/lib/api/types";

function formatUsdPerMillion(value: number): string {
  if (value === 0) {
    return "$0.00";
  }
  if (value >= 1) {
    return `$${value.toFixed(2)}`;
  }
  if (value >= 0.01) {
    return `$${value.toFixed(2)}`;
  }
  return `$${value.toFixed(4)}`;
}

export function formatOpenRouterModelPricing(model: OpenRouterModelOption): string {
  const parts = [
    `${formatUsdPerMillion(model.prompt_price_per_million_usd)} / 1M input`,
    `${formatUsdPerMillion(model.completion_price_per_million_usd)} / 1M output`,
  ];

  if (model.image_token_price_per_million_usd > 0) {
    parts.push(
      `${formatUsdPerMillion(model.image_token_price_per_million_usd)} / 1M image`,
    );
  }

  return parts.join(" · ");
}

export function buildModelOptions(
  models: OpenRouterModelOption[],
  selectedModelId: string,
): OpenRouterModelOption[] {
  if (!selectedModelId || models.some((model) => model.id === selectedModelId)) {
    return models;
  }

  return [
    {
      id: selectedModelId,
      name: selectedModelId,
      prompt_price_per_million_usd: 0,
      completion_price_per_million_usd: 0,
      image_token_price_per_million_usd: 0,
    },
    ...models,
  ];
}

export function findModelOption(
  models: OpenRouterModelOption[],
  modelId: string,
): OpenRouterModelOption | undefined {
  return models.find((model) => model.id === modelId);
}
