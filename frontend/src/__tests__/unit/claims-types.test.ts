import { describe, expect, it } from "@jest/globals";

import {
  computeCategoryStatus,
  formatRinggit,
} from "@/lib/types/claims";

describe("claims types helpers", () => {
  it("computeCategoryStatus returns ok below 80%", () => {
    expect(computeCategoryStatus(0)).toBe("ok");
    expect(computeCategoryStatus(79.9)).toBe("ok");
  });

  it("computeCategoryStatus returns warning between 80 and 99%", () => {
    expect(computeCategoryStatus(80)).toBe("warning");
    expect(computeCategoryStatus(99)).toBe("warning");
  });

  it("computeCategoryStatus returns full at 100%+", () => {
    expect(computeCategoryStatus(100)).toBe("full");
    expect(computeCategoryStatus(120)).toBe("full");
  });

  it("formatRinggit formats MYR currency", () => {
    expect(formatRinggit(1000)).toContain("1");
    expect(formatRinggit(1000)).toMatch(/RM|MYR/);
  });
});
