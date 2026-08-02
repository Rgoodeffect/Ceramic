"""Post-sale fulfillment on a submitted Sales Invoice (spec Part 5): recording
payment and, for Company Warehouse-sourced lines, creating the Delivery Note.
Supplier-sourced lines are never included here - those are fulfilled through
Supplier Delivery Order instead (see supplier_delivery_service.py).
"""

from __future__ import annotations

import frappe
from frappe import _

from retail_suite.retail_suite_core.permissions import permission_service
from retail_suite.services.sales_service import WAREHOUSE_SOURCE


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
