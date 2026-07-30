"""Supplier Delivery Order creation (spec Part 5: Supplier Process).

A Supplier Delivery Order can never be created without a *Confirmed*
Supplier Availability Confirmation - that hard link is the whole point of
the confirmation doctype - and it never carries pricing (spec: "Do not
include prices").
"""

from __future__ import annotations

import frappe
from frappe import _

from retail_suite.retail_suite_core.permissions import permission_service

SUPPLIER_SOURCE = "Supplier"


def create_from_sales_invoice(
	sales_invoice_name: str,
	supplier_availability_confirmation_name: str,
	delivery_date: str,
	customer_address: str | None = None,
	remarks: str | None = None,
):
	invoice = frappe.get_doc("Sales Invoice", sales_invoice_name)
	permission_service.assert_showroom_access(invoice.custom_showroom)

	confirmation = frappe.get_doc(
		"Supplier Availability Confirmation", supplier_availability_confirmation_name
	)
	if confirmation.status != "Confirmed" or confirmation.docstatus != 1:
		frappe.throw(
			_("Supplier availability confirmation is required before creating a supplier delivery order.")
		)

	supplier_items = [row for row in invoice.items if row.custom_supply_source == SUPPLIER_SOURCE]
	if not supplier_items:
		frappe.throw(_("Sales Invoice {0} has no items sourced from a supplier.").format(sales_invoice_name))

	order = frappe.new_doc("Supplier Delivery Order")
	order.supplier = confirmation.supplier
	order.showroom = invoice.custom_showroom
	order.customer = invoice.customer
	order.customer_address = customer_address or invoice.get("customer_address")
	order.delivery_date = delivery_date
	order.supplier_availability_confirmation = confirmation.name
	order.sales_invoice = invoice.name
	order.remarks = remarks

	for row in supplier_items:
		item_row = order.append("items", {})
		item_row.item_code = row.item_code
		item_row.item_name = row.item_name
		# qty is already expressed in Box UOM by CalculationService - see
		# retail_suite.retail_suite_ceramic.calculation_service.apply_to_item_row
		item_row.boxes_qty = row.qty

	order.insert()
	return order
