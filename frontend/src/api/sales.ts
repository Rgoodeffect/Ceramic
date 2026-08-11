import invoke from "./client";
import type { SupplySource } from "@/types";

export interface SalesInvoiceItemInput {
	item_code: string;
	/** Set for ceramic items (mutually exclusive with `qty`). */
	required_area_sqm?: number;
	/** Set for everything else - a plain quantity in the item's own UOM. */
	qty?: number;
	supply_source: SupplySource;
	/** Required when supply_source is "Supplier" - picked directly at the
	 * point of sale, no Supplier Availability Confirmation needed by default. */
	supplier?: string;
}

export type SupplySourceSelection = SupplySource | { supply_source: SupplySource; supplier?: string };

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

export function submitSalesInvoice(salesInvoice: string): Promise<{ name: string; docstatus: number }> {
	return invoke<{ name: string; docstatus: number }>("retail_suite.api.sales.submit_sales_invoice", {
		sales_invoice: salesInvoice,
	});
}

export function createSalesInvoiceFromQuotation(
	quotation: string,
	supplySourceByItem: Record<string, SupplySourceSelection>,
): Promise<{ name: string }> {
	return invoke<{ name: string }>("retail_suite.api.sales.create_sales_invoice_from_quotation", {
		quotation,
		supply_source_by_item: JSON.stringify(supplySourceByItem),
	});
}
