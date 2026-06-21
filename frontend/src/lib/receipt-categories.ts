import type { ReliefCategoryItem } from "@/lib/api/types";
import { RECEIPT_CATEGORY_LABELS } from "@/lib/constants/receipts";

export function buildCategoryLabelMap(
  categories: ReliefCategoryItem[],
): Record<string, string> {
  return Object.fromEntries(
    categories.map((item) => [item.category, item.label]),
  );
}

export function mergeCategoryLabels(
  dynamicLabels: Record<string, string>,
): Record<string, string> {
  return { ...RECEIPT_CATEGORY_LABELS, ...dynamicLabels };
}

export function getCategoryOptions(categories: ReliefCategoryItem[]) {
  const systemCategories = [
    { category: "tidak_layak", label: RECEIPT_CATEGORY_LABELS.tidak_layak },
    { category: "semak_manual", label: RECEIPT_CATEGORY_LABELS.semak_manual },
  ];

  return [...categories, ...systemCategories];
}
