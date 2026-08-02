"""Whitelisted endpoints for post-sale fulfillment: payment and delivery.
See services/fulfillment_service.py for the actual business logic."""

from __future__ import annotations

import frappe

from retail_suite.api.utils import api_endpoint
from retail_suite.services import fulfillment_service


@frappe.whitelist()
@api_endpoint
def create_payment(sales_invoice: str, mode_of_payment: str | None = None):
	doc = fulfillment_service.create_payment_entry(sales_invoice, mode_of_payment)
	return {"name": doc.name}


@frappe.whitelist()
@api_endpoint
def create_delivery_note(sales_invoice: str):
	doc = fulfillment_service.create_delivery_note(sales_invoice)
	return {"name": doc.name}


@frappe.whitelist()
@api_endpoint
def create_supplier_delivery(sales_invoice: str, delivery_date: str | None = None):
	doc = fulfillment_service.create_supplier_delivery(sales_invoice, delivery_date)
	return {"name": doc.name}
