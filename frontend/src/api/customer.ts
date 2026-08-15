import { call } from "frappe-ui";
import invoke from "./client";
import type { CustomerRef } from "@/types";

export function quickCreateCustomer(
	customerName: string,
	mobileNo: string,
	address?: string,
	email?: string,
): Promise<{ name: string }> {
	return invoke<{ name: string }>("retail_suite.api.customer.quick_create_customer", {
		customer_name: customerName,
		mobile_no: mobileNo,
		address,
		email,
	});
}

/** Existing-customer search uses the standard Frappe list API directly
 * (frappe.client.get_list) rather than a retail_suite endpoint - it's a
 * plain, already-permission-checked read with no business logic of its
 * own, so wrapping it in another custom endpoint would just duplicate
 * what Frappe already provides. */
export async function searchCustomers(term: string): Promise<CustomerRef[]> {
	const rows = (await call("frappe.client.get_list", {
		doctype: "Customer",
		filters: term ? [["customer_name", "like", `%${term}%`]] : [],
		fields: ["name", "customer_name"],
		limit_page_length: 10,
	})) as CustomerRef[];
	return rows;
}
