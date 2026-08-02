import invoke from "./client";

export function createPayment(
	salesInvoice: string,
	modeOfPayment?: string,
): Promise<{ name: string }> {
	return invoke<{ name: string }>("retail_suite.api.fulfillment.create_payment", {
		sales_invoice: salesInvoice,
		mode_of_payment: modeOfPayment,
	});
}

export function createDeliveryNote(salesInvoice: string): Promise<{ name: string }> {
	return invoke<{ name: string }>("retail_suite.api.fulfillment.create_delivery_note", {
		sales_invoice: salesInvoice,
	});
}

export function createSupplierDelivery(
	salesInvoice: string,
	deliveryDate?: string,
): Promise<{ name: string }> {
	return invoke<{ name: string }>("retail_suite.api.fulfillment.create_supplier_delivery", {
		sales_invoice: salesInvoice,
		delivery_date: deliveryDate,
	});
}
