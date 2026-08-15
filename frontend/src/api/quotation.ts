import invoke from "./client";

export interface QuotationItemInput {
	item_code: string;
	/** Set for ceramic items (mutually exclusive with `qty`). */
	required_area_sqm?: number;
	/** Set for everything else - a plain quantity in the item's own UOM. */
	qty?: number;
}

export function createQuotation(
	customer: string,
	showroom: string,
	items: QuotationItemInput[],
	priceList: string,
): Promise<{ name: string }> {
	return invoke<{ name: string }>("retail_suite.api.quotation.create_quotation", {
		customer,
		showroom,
		items: JSON.stringify(items),
		price_list: priceList,
	});
}
