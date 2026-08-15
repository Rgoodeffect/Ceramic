import { call } from "frappe-ui";
import type { SupplierRef } from "@/types";

/** Supplier search uses the standard Frappe list API directly
 * (frappe.client.get_list), same as customer search in api/customer.ts - a
 * plain, already-permission-checked read with no business logic of its own. */
export async function searchSuppliers(term: string): Promise<SupplierRef[]> {
	const rows = (await call("frappe.client.get_list", {
		doctype: "Supplier",
		filters: term ? [["supplier_name", "like", `%${term}%`]] : [],
		fields: ["name", "supplier_name"],
		limit_page_length: 10,
	})) as SupplierRef[];
	return rows;
}
