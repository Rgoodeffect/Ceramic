import invoke from "./client";
import type { PaymentStatus, SupplierDeliveryOrderRef } from "@/types";

export interface PaymentResult {
	name: string;
	paid_amount: number;
	/** The invoice's balance *after* this payment - saved a follow-up call. */
	payment_status: PaymentStatus;
}

/** `paidAmount` omitted settles the invoice in full; a smaller amount records
 * a part payment and leaves the rest as the customer's debt, which a later
 * call against the same invoice can pay off. */
export function createPayment(
	salesInvoice: string,
	modeOfPayment?: string,
	paidAmount?: number,
): Promise<PaymentResult> {
	return invoke<PaymentResult>("retail_suite.api.fulfillment.create_payment", {
		sales_invoice: salesInvoice,
		mode_of_payment: modeOfPayment,
		paid_amount: paidAmount,
	});
}

export function getPaymentStatus(salesInvoice: string): Promise<PaymentStatus> {
	return invoke<PaymentStatus>("retail_suite.api.fulfillment.get_payment_status", {
		sales_invoice: salesInvoice,
	});
}

export function createDeliveryNote(salesInvoice: string): Promise<{ name: string }> {
	return invoke<{ name: string }>("retail_suite.api.fulfillment.create_delivery_note", {
		sales_invoice: salesInvoice,
	});
}

/** One order per supplier on the invoice - each covering only that supplier's
 * own lines, and each printed separately. */
export function createSupplierDeliveries(
	salesInvoice: string,
	deliveryDate?: string,
): Promise<{ orders: SupplierDeliveryOrderRef[] }> {
	return invoke<{ orders: SupplierDeliveryOrderRef[] }>(
		"retail_suite.api.fulfillment.create_supplier_deliveries",
		{
			sales_invoice: salesInvoice,
			delivery_date: deliveryDate,
		},
	);
}
