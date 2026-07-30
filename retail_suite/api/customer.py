"""Whitelisted quick-create endpoint for the POS (spec Part 4: "Customer
Creation" - minimum fields: Customer Name, Mobile Number). Uses the standard
ERPNext Customer/Contact/Address doctypes - no parallel customer record is
ever created."""

from __future__ import annotations

import frappe

from retail_suite.api.utils import api_endpoint


@frappe.whitelist()
@api_endpoint
def quick_create_customer(
	customer_name: str, mobile_no: str, address: str | None = None, email: str | None = None
):
	if not customer_name or not mobile_no:
		frappe.throw(frappe._("Customer Name and Mobile Number are required."))

	customer = frappe.new_doc("Customer")
	customer.customer_name = customer_name
	customer.customer_type = "Individual"
	customer.insert()

	contact = frappe.new_doc("Contact")
	contact.first_name = customer_name
	contact.append("phone_nos", {"phone": mobile_no, "is_primary_mobile_no": 1})
	if email:
		contact.append("email_ids", {"email_id": email, "is_primary": 1})
	contact.append("links", {"link_doctype": "Customer", "link_name": customer.name})
	contact.insert()

	if address:
		addr = frappe.new_doc("Address")
		addr.address_title = customer_name
		addr.address_line1 = address
		addr.address_type = "Billing"
		addr.append("links", {"link_doctype": "Customer", "link_name": customer.name})
		addr.insert()

	return {"name": customer.name}
