"""Post-sale fulfillment on a submitted Sales Invoice (spec Part 5): recording
payment, creating the Delivery Note for Company Warehouse-sourced lines, and
creating the Supplier Delivery Orders for Supplier-sourced lines.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import flt, fmt_money

from retail_suite.retail_suite_core.permissions import permission_service
from retail_suite.services.sales_service import SUPPLIER_SOURCE, WAREHOUSE_SOURCE


def create_payment_entry(
	sales_invoice: str, mode_of_payment: str | None = None, paid_amount: float | None = None
):
	"""Record and finalize a payment against a submitted Sales Invoice.

	`paid_amount` is what the customer actually hands over at the counter.
	Leave it None to settle the invoice in full (the original behaviour);
	pass a smaller figure to take a part payment, which leaves the rest
	sitting on the invoice as its `outstanding_amount` - the customer's debt
	- and moves the invoice to ERPNext's "Partly Paid" status. Nothing here
	is one-shot: calling this again later with the balance (or any part of
	it) settles more of that debt, so a customer can pay an invoice off over
	several visits.

	Uses ERPNext's own mapping (spec: "Use ERPNext Payment Entry", no custom
	payment logic) to resolve the party account, currency and amounts, then
	submits it directly - the salesperson at the counter is completing the
	sale, not staging a draft for someone else to confirm later. A part
	payment is expressed through `get_payment_entry`'s own `party_amount`
	argument rather than by editing the mapped document afterwards: that
	single argument is what drives the paid/received pair *and* the
	reference row's allocated amount consistently, including the
	multi-currency case where paid and received differ by the exchange rate.
	"""
	from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry

	invoice = frappe.get_doc("Sales Invoice", sales_invoice)
	permission_service.assert_showroom_access(invoice.custom_showroom)
	if invoice.docstatus != 1:
		frappe.throw(_("Sales Invoice must be submitted before recording a payment."))

	precision = invoice.precision("outstanding_amount")
	outstanding = flt(invoice.outstanding_amount, precision)
	if outstanding <= 0:
		frappe.throw(_("Sales Invoice {0} has no outstanding amount to pay.").format(sales_invoice))

	party_amount = None
	if paid_amount is not None:
		party_amount = flt(paid_amount, precision)
		if party_amount <= 0:
			frappe.throw(_("Payment amount must be greater than zero."))
		if party_amount > outstanding:
			frappe.throw(
				_("Payment amount {0} is more than the outstanding amount {1} on Sales Invoice {2}.").format(
					fmt_money(party_amount, currency=invoice.currency),
					fmt_money(outstanding, currency=invoice.currency),
					sales_invoice,
				)
			)
		if party_amount == outstanding:
			# Paying the balance off in full - hand that back to
			# get_payment_entry's default path rather than pinning the
			# amount ourselves, so settling an invoice behaves exactly as it
			# did before part payments existed.
			party_amount = None

	payment = get_payment_entry("Sales Invoice", sales_invoice, party_amount=party_amount)
	payment.custom_showroom = invoice.custom_showroom
	if mode_of_payment:
		payment.mode_of_payment = mode_of_payment
	payment.insert()
	payment.submit()
	return payment


def get_payment_status(sales_invoice: str) -> dict:
	"""Where an invoice stands: what it is worth, how much has actually been
	paid against it, and how much the customer still owes.

	This is what the POS shows after a part payment and what it defaults the
	next payment amount to, so it deliberately does not read
	`Sales Invoice.paid_amount`: that field only carries a figure on
	POS-mode invoices, and stays 0 on the ordinary invoices this app creates
	however many Payment Entries are submitted against them. The amount paid
	is derived from what is still outstanding instead, against
	`rounded_total` where there is one - `outstanding_amount` is itself
	computed from the rounded total, so subtracting from `grand_total`
	would report the rounding adjustment (LYD rounds to the whole dinar) as
	money received.
	"""
	invoice = frappe.get_doc("Sales Invoice", sales_invoice)
	permission_service.assert_showroom_access(invoice.custom_showroom)

	precision = invoice.precision("outstanding_amount")
	total = flt(invoice.rounded_total or invoice.grand_total, precision)
	if invoice.docstatus == 1:
		outstanding = flt(invoice.outstanding_amount, precision)
	elif invoice.docstatus == 0:
		# ERPNext only computes outstanding_amount on submit, so a draft
		# reports 0 - which would read here as "fully paid". Nothing has
		# been paid against a draft: it is all still owed.
		outstanding = total
	else:
		outstanding = 0.0

	return {
		"sales_invoice": invoice.name,
		"currency": invoice.currency,
		"status": invoice.status,
		"grand_total": total,
		"paid_amount": flt(total - outstanding, precision),
		"outstanding_amount": outstanding,
		"customer_outstanding": get_customer_outstanding(invoice.customer, invoice.company),
	}


def get_customer_outstanding(customer: str, company: str) -> float:
	"""Everything this customer still owes the company, across every
	submitted invoice - not just the one on screen. A part payment turns
	into debt that follows the customer, not the sale, so the counter needs
	to see the running total before agreeing to another one.

	`frappe.get_all` (not `get_list`) on purpose: a salesperson is
	restricted to their own showroom's documents, but a customer's debt is
	owed to the company as a whole and would otherwise be understated by
	whatever they bought at another showroom.
	"""
	total = frappe.get_all(
		"Sales Invoice",
		filters={"customer": customer, "company": company, "docstatus": 1},
		fields=["sum(outstanding_amount) as total"],
	)[0].total
	return flt(total)


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


def create_supplier_deliveries(sales_invoice: str, delivery_date: str | None = None) -> list:
	"""Create and submit one Supplier Delivery Order per supplier on a
	submitted Sales Invoice's Supplier-sourced lines.

	One invoice routinely mixes items from several different suppliers, and
	each supplier may only be handed the lines it is actually expected to
	deliver - so the Supplier-sourced rows are grouped by their own
	`custom_supplier` and every group becomes its own order, and therefore
	its own printout. This used to put every Supplier-sourced row on a
	single order filed under the *first* row's supplier, which both told
	that supplier to deliver another supplier's goods and left the other
	suppliers with no order at all.

	The supplier comes straight from the invoice line (`custom_supplier`,
	set at the point of sale - see `sales_service.validate_supply_sources`),
	not from a Supplier Availability Confirmation - that record is now only
	consulted when Retail Suite Settings > Require Supplier Availability
	Confirmation is on (spec Part 5's original behaviour), and even then only
	to attach it to the order for traceability, not to determine who the
	supplier is.

	Returns the orders in the order their suppliers first appear on the
	invoice, so the sequence of printouts matches the sequence of lines the
	salesperson entered.
	"""
	invoice = frappe.get_doc("Sales Invoice", sales_invoice)
	permission_service.assert_showroom_access(invoice.custom_showroom)
	if invoice.docstatus != 1:
		frappe.throw(_("Sales Invoice must be submitted before creating a supplier delivery order."))

	supplier_rows = [row for row in invoice.items if row.custom_supply_source == SUPPLIER_SOURCE]
	if not supplier_rows:
		frappe.throw(_("This invoice has no Supplier-sourced items to deliver."))

	first_row_by_supplier: dict[str, object] = {}
	for row in supplier_rows:
		if not row.custom_supplier:
			frappe.throw(_("No supplier set on item {0}.").format(row.item_code))
		first_row_by_supplier.setdefault(row.custom_supplier, row)

	return [
		_create_supplier_delivery_for(
			invoice=invoice,
			supplier=supplier,
			first_row=first_row,
			delivery_date=delivery_date or frappe.utils.nowdate(),
		)
		for supplier, first_row in first_row_by_supplier.items()
	]


def _create_supplier_delivery_for(invoice, supplier, first_row, delivery_date):
	"""One supplier's order: its own availability confirmation (when the
	setting demands one) and its own lines - see
	`supplier_delivery_service.create_from_sales_invoice`, which selects the
	rows belonging to this supplier."""
	from retail_suite.retail_suite_core.doctype.retail_suite_settings.retail_suite_settings import (
		is_supplier_confirmation_required,
	)
	from retail_suite.services import supplier_delivery_service

	confirmation_name = frappe.db.get_value(
		"Supplier Availability Confirmation",
		{
			"item": first_row.item_code,
			"showroom": invoice.custom_showroom,
			"supplier": supplier,
			"status": "Confirmed",
			"docstatus": 1,
		},
		"name",
		order_by="confirmation_date desc",
	)
	if is_supplier_confirmation_required() and not confirmation_name:
		# Guarded against by before_submit already, so this should be
		# unreachable in practice when the setting is on - kept as a clear
		# error, not an assert, in case a confirmation is cancelled between
		# submit and this call.
		frappe.throw(_("No confirmed supplier availability found for item {0}.").format(first_row.item_code))

	order = supplier_delivery_service.create_from_sales_invoice(
		sales_invoice_name=invoice.name,
		supplier=supplier,
		supplier_availability_confirmation_name=confirmation_name,
		delivery_date=delivery_date,
	)
	# create_from_sales_invoice itself only inserts (it's also used from
	# Desk, where draft-then-review is the normal flow) - submitted here
	# instead, same as create_payment_entry/create_delivery_note above, so
	# a POS checkout actually finishes the job rather than leaving the
	# salesperson to go find and submit a draft in Desk afterward.
	order.submit()
	return order
