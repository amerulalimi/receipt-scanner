import {
  formatOpenRouterModelPricing,
  buildModelOptions,
} from "@/lib/format/openrouter-pricing";
import type { OpenRouterModelOption } from "@/lib/api/types";

describe("formatOpenRouterModelPricing", () => {
  const model: OpenRouterModelOption = {
    id: "google/gemini-2.5-flash",
    name: "Gemini 2.5 Flash",
    prompt_price_per_million_usd: 0.15,
    completion_price_per_million_usd: 0.6,
    image_token_price_per_million_usd: 0,
  };

  it("formats input and output prices per million tokens", () => {
    expect(formatOpenRouterModelPricing(model)).toBe(
      "$0.15 / 1M input · $0.60 / 1M output",
    );
  });

  it("includes image token pricing when non-zero", () => {
    expect(
      formatOpenRouterModelPricing({
        ...model,
        image_token_price_per_million_usd: 1.25,
      }),
    ).toContain("$1.25 / 1M image");
  });
});

describe("buildModelOptions", () => {
  const models: OpenRouterModelOption[] = [
    {
      id: "google/gemini-2.5-flash",
      name: "Gemini 2.5 Flash",
      prompt_price_per_million_usd: 0.15,
      completion_price_per_million_usd: 0.6,
      image_token_price_per_million_usd: 0,
    },
  ];

  it("prepends the current model when it is not in the fetched list", () => {
    const result = buildModelOptions(models, "custom/legacy-model");
    expect(result).toHaveLength(2);
    expect(result[0]?.id).toBe("custom/legacy-model");
  });
});
