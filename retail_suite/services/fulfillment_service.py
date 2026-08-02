"""Post-sale fulfillment on a submitted Sales Invoice (spec Part 5): recording
payment, creating the Delivery Note for Company Warehouse-sourced lines, and
creating the Supplier Delivery Order for Supplier-sourced lines.
"""

from __future__ import annotations

import frappe
from frappe import _

from retail_suite.retail_suite_core.permissions import permission_service
from retail_suite.services.sales_service import SUPPLIER_SOURCE, WAREHOUSE_SOURCE


def create_payment_entry(sales_invoice: str, mode_of_payment: str | None = None):
	"""Record and finalize a payment against a submitted Sales Invoice.

	Uses ERPNext's own mapping (spec: "Use ERPNext Payment Entry", no custom
	payment logic) to resolve the party account, currency, and the full
	outstanding amount, then submits it directly - the salesperson at the
	counter is completing the sale, not staging a draft for someone else to
	confirm later.
	"""
	from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry

	invoice = frappe.get_doc("Sales Invoice", sales_invoice)
	permission_service.assert_showroom_access(invoice.custom_showroom)
	if invoice.docstatus != 1:
		frappe.throw(_("Sales Invoice must be submitted before recording a payment."))
	if invoice.outstanding_amount <= 0:
		frappe.throw(_("Sales Invoice {0} has no outstanding amount to pay.").format(sales_invoice))

	payment = get_payment_entry("Sales Invoice", sales_invoice)
	payment.custom_showroom = invoice.custom_showroom
	if mode_of_payment:
		payment.mode_of_payment = mode_of_payment
	payment.insert()
	payment.submit()
	return payment


def create_delivery_note(sales_invoice: str):
	"""Create and submit a Delivery Note for a submitted Sales Invoice's
	Company Warehouse-sourced lines only.

	`erpnext.accounts.doctype.sales_invoice.sales_invoice.make_delivery_note`
	maps every undelivered line by default - it knows nothing about
	`custom_supply_source`, so Supplier-sourced rows are stripped back out
	here before insert (spec Part 5: Supplier-sourced items are fulfilled
	through Supplier Delivery Order, never a Delivery Note).
	"""
	from erpnext.accounts.doctype.sales_invoice.sales_invoice import make_delivery_note

	invoice = frappe.get_doc("Sales Invoice", sales_invoice)
	permission_service.assert_showroom_access(invoice.custom_showroom)
	if invoice.docstatus != 1:
		frappe.throw(_("Sales Invoice must be submitted before creating a delivery note."))

	warehouse_row_names = {
		row.name for row in invoice.items if row.custom_supply_source == WAREHOUSE_SOURCE
	}
	if not warehouse_row_names:
		frappe.throw(_("This invoice has no Company Warehouse-sourced items to deliver."))

	delivery_note = make_delivery_note(sales_invoice)
	delivery_note.items = [row for row in delivery_note.items if row.si_detail in warehouse_row_names]
	delivery_note.custom_showroom = invoice.custom_showroom
	delivery_note.insert()
	delivery_note.submit()
	return delivery_note


def create_supplier_delivery(sales_invoice: str, delivery_date: str | None = None):
	"""Create a Supplier Delivery Order for a submitted Sales Invoice's
	Supplier-sourced lines.

	`before_submit` (`sales_service.validate_supplier_confirmation_before_submit`)
	already guarantees a *Confirmed* Supplier Availability Confirmation
	exists per Supplier-sourced item/showroom before the invoice could even
	reach docstatus 1 - this just looks that confirmation back up so the
	salesperson at the POS doesn't have to hunt for its name themselves.
	`supplier_delivery_service.create_from_sales_invoice` puts every
	Supplier-sourced row on one order under that one confirmation's
	supplier (a cart split across multiple different suppliers isn't
	something this app's model represents - one order per checkout).
	"""
	from retail_suite.services import supplier_delivery_service

	invoice = frappe.get_doc("Sales Invoice", sales_invoice)
	permission_service.assert_showroom_access(invoice.custom_showroom)
	if invoice.docstatus != 1:
		frappe.throw(_("Sales Invoice must be submitted before creating a supplier delivery order."))

	supplier_rows = [row for row in invoice.items if row.custom_supply_source == SUPPLIER_SOURCE]
	if not supplier_rows:
		frappe.throw(_("This invoice has no Supplier-sourced items to deliver."))

	confirmation_name = frappe.db.get_value(
		"Supplier Availability Confirmation",
		{
			"item": supplier_rows[0].item_code,
			"showroom": invoice.custom_showroom,
			"status": "Confirmed",
			"docstatus": 1,
		},
		"name",
		order_by="confirmation_date desc",
	)
	if not confirmation_name:
		# Guarded against by before_submit already, so this should be
		# unreachable in practice - kept as a clear error, not an assert,
		# in case a confirmation is cancelled between submit and this call.
		frappe.throw(
			_("No confirmed supplier availability found for item {0}.").format(supplier_rows[0].item_code)
		)

	order = supplier_delivery_service.create_from_sales_invoice(
		sales_invoice_name=sales_invoice,
		supplier_availability_confirmation_name=confirmation_name,
		delivery_date=delivery_date or frappe.utils.nowdate(),
	)
	# create_from_sales_invoice itself only inserts (it's also used from
	# Desk, where draft-then-review is the normal flow) - submitted here
	# instead, same as create_payment_entry/create_delivery_note above, so
	# a POS checkout actually finishes the job rather than leaving the
	# salesperson to go find and submit a draft in Desk afterward.
	order.submit()
	return order
