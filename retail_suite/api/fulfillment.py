"""Whitelisted endpoints for post-sale fulfillment: payment and delivery.
See services/fulfillment_service.py for the actual business logic."""

from __future__ import annotations

import frappe
from frappe.utils import flt

from retail_suite.api.utils import api_endpoint
from retail_suite.services import fulfillment_service


@frappe.whitelist()
@api_endpoint
def create_payment(sales_invoice: str, mode_of_payment: str | None = None, paid_amount=None):
	"""Record a payment against a submitted Sales Invoice.

	`paid_amount`: leave unset to settle the invoice in full. Pass a smaller
	amount to take a part payment - the rest stays on the invoice as the
	customer's debt, and calling this again later pays more of it off.

	Returns the resulting `payment_status` alongside the Payment Entry name
	so the POS can show the new balance without a second round-trip.
	"""
	doc = fulfillment_service.create_payment_entry(
		sales_invoice, mode_of_payment, paid_amount=_optional_amount(paid_amount)
	)
	return {
		"name": doc.name,
		"paid_amount": flt(doc.paid_amount),
		"payment_status": fulfillment_service.get_payment_status(sales_invoice),
	}


@frappe.whitelist()
@api_endpoint
def get_payment_status(sales_invoice: str):
	"""What the invoice is worth, what has been paid against it, and what the
	customer still owes (on this invoice and in total)."""
	return fulfillment_service.get_payment_status(sales_invoice)


@frappe.whitelist()
@api_endpoint
def create_delivery_note(sales_invoice: str):
	doc = fulfillment_service.create_delivery_note(sales_invoice)
	return {"name": doc.name}


@frappe.whitelist()
@api_endpoint
def create_supplier_deliveries(sales_invoice: str, delivery_date: str | None = None):
	"""One Supplier Delivery Order per supplier on the invoice - an invoice
	mixing items from several suppliers produces (and prints) one order each,
	covering only that supplier's own lines."""
	orders = fulfillment_service.create_supplier_deliveries(sales_invoice, delivery_date)
	return {
		"orders": [
			{
				"name": order.name,
				"supplier": order.supplier,
				"supplier_name": frappe.db.get_value("Supplier", order.supplier, "supplier_name")
				or order.supplier,
			}
			for order in orders
		]
	}


def _optional_amount(value):
	"""Whitelisted arguments arrive as strings ("450.5") or not at all, and an
	omitted amount must stay None - `flt("")` would turn "not given" into a
	0 payment, which is a different (and rejected) request."""
	if value is None or value == "":
		return None
	return flt(value)
