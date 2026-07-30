import invoke from "./client";
import type { SupplySource } from "@/types";

export interface SalesInvoiceItemInput {
	item_code: string;
	required_area_sqm: number;
	supply_source: SupplySource;
}

export function createSalesInvoice(
	customer: string,
	showroom: string,
	items: SalesInvoiceItemInput[],
	priceList: string,
): Promise<{ name: string }> {
	return invoke<{ name: string }>("retail_suite.api.sales.create_sales_invoice", {
		customer,
		showroom,
		items: JSON.stringify(items),
		price_list: priceList,
	});
}

export function createSalesInvoiceFromQuotation(
	quotation: string,
	supplySourceByItem: Record<string, SupplySource>,
): Promise<{ name: string }> {
	return invoke<{ name: string }>("retail_suite.api.sales.create_sales_invoice_from_quotation", {
		quotation,
		supply_source_by_item: JSON.stringify(supplySourceByItem),
	});
}
