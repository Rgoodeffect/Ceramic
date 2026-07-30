import invoke from "./client";
import type { CalculationPreview } from "@/types";

export function previewRow(
	itemCode: string,
	requiredAreaSqm: number,
	priceList: string,
): Promise<CalculationPreview> {
	return invoke<CalculationPreview>("retail_suite.api.calculation.preview_row", {
		item_code: itemCode,
		required_area_sqm: requiredAreaSqm,
		price_list: priceList,
	});
}
