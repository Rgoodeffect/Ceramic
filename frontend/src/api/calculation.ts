import invoke from "./client";
import type { CalculationPreview, SimpleCalculationPreview } from "@/types";

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

/** Preview for a non-area item (no Area Per Box configured) - plain qty x rate
 * in the item's own stock UOM. */
export function previewSimpleRow(
	itemCode: string,
	qty: number,
	priceList: string,
): Promise<SimpleCalculationPreview> {
	return invoke<SimpleCalculationPreview>("retail_suite.api.calculation.preview_simple_row", {
		item_code: itemCode,
		qty,
		price_list: priceList,
	});
}
