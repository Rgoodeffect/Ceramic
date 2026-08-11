"""Supplier Delivery Order creation (spec Part 5: Supplier Process).

The supplier is normally passed in directly (picked on the Sales Invoice
line at the point of sale - see `sales_service`), not derived from a
Supplier Availability Confirmation; that confirmation is now optional and
only enforced when Retail Suite Settings > Require Supplier Availability
Confirmation is on. Either way, the order never carries pricing
(spec: "Do not include prices").
"""

from __future__ import annotations

import frappe
from frappe import _

from retail_suite.retail_suite_core.permissions import permission_service

SUPPLIER_SOURCE = "Supplier"


def create_from_sales_invoice(
	sales_invoice_name: str,
	delivery_date: str,
	supplier: str | None = None,
	supplier_availability_confirmation_name: str | None = None,
	customer_address: str | None = None,
	remarks: str | None = None,
):
	from retail_suite.retail_suite_core.doctype.retail_suite_settings.retail_suite_settings import (
		is_supplier_confirmation_required,
	)

	invoice = frappe.get_doc("Sales Invoice", sales_invoice_name)
	permission_service.assert_showroom_access(invoice.custom_showroom)

	confirmation = None
	if supplier_availability_confirmation_name:
		confirmation = frappe.get_doc(
			"Supplier Availability Confirmation", supplier_availability_confirmation_name
		)
		if confirmation.status != "Confirmed" or confirmation.docstatus != 1:
			frappe.throw(
				_("Supplier availability confirmation is required before creating a supplier delivery order.")
			)
		supplier = supplier or confirmation.supplier
	elif is_supplier_confirmation_required():
		frappe.throw(
			_("Supplier availability confirmation is required before creating a supplier delivery order.")
		)

	if not supplier:
		frappe.throw(_("A supplier is required to create a supplier delivery order."))

	supplier_items = [row for row in invoice.items if row.custom_supply_source == SUPPLIER_SOURCE]
	if not supplier_items:
		frappe.throw(_("Sales Invoice {0} has no items sourced from a supplier.").format(sales_invoice_name))

	order = frappe.new_doc("Supplier Delivery Order")
	order.supplier = supplier
	order.showroom = invoice.custom_showroom
	order.customer = invoice.customer
	order.customer_address = customer_address or invoice.get("customer_address")
	order.delivery_date = delivery_date
	if confirmation:
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
