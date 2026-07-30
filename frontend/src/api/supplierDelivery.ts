import invoke from "./client";

export interface RecordAvailabilityConfirmationInput {
	supplier: string;
	showroom: string;
	contact_person: string;
	phone_number: string;
	status: "Pending" | "Confirmed" | "Rejected";
	item?: string;
	confirmation_date?: string;
	confirmation_time?: string;
	remarks?: string;
}

export function recordAvailabilityConfirmation(
	input: RecordAvailabilityConfirmationInput,
): Promise<{ name: string; status: string }> {
	return invoke("retail_suite.api.supplier_delivery.record_availability_confirmation", { ...input });
}

export interface CreateSupplierDeliveryOrderInput {
	sales_invoice: string;
	supplier_availability_confirmation: string;
	delivery_date: string;
	customer_address?: string;
	remarks?: string;
}

export function createSupplierDeliveryOrder(
	input: CreateSupplierDeliveryOrderInput,
): Promise<{ name: string }> {
	return invoke("retail_suite.api.supplier_delivery.create_supplier_delivery_order", { ...input });
}
