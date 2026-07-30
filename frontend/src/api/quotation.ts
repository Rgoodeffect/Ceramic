import invoke from "./client";

export interface QuotationItemInput {
	item_code: string;
	required_area_sqm: number;
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
