"""Whitelisted endpoints for the supplier workflow. See
services/availability_confirmation_service.py and
services/supplier_delivery_service.py for the actual business logic."""

from __future__ import annotations

import frappe

from retail_suite.api.utils import api_endpoint
from retail_suite.services import availability_confirmation_service, supplier_delivery_service


@frappe.whitelist()
@api_endpoint
def record_availability_confirmation(
	supplier: str,
	showroom: str,
	contact_person: str,
	phone_number: str,
	status: str,
	item: str | None = None,
	confirmation_date: str | None = None,
	confirmation_time: str | None = None,
	remarks: str | None = None,
):
	doc = availability_confirmation_service.record_confirmation(
		supplier=supplier,
		showroom=showroom,
		contact_person=contact_person,
		phone_number=phone_number,
		status=status,
		item=item,
		confirmation_date=confirmation_date,
		confirmation_time=confirmation_time,
		remarks=remarks,
	)
	return {"name": doc.name, "status": doc.status}


@frappe.whitelist()
@api_endpoint
def create_supplier_delivery_order(
	sales_invoice: str,
	delivery_date: str,
	supplier: str | None = None,
	supplier_availability_confirmation: str | None = None,
	customer_address: str | None = None,
	remarks: str | None = None,
):
	"""`supplier` is required unless `supplier_availability_confirmation` is
	given instead (its supplier is then used) - see
	`supplier_delivery_service.create_from_sales_invoice`. A confirmation is
	only mandatory when Retail Suite Settings > Require Supplier Availability
	Confirmation is on."""
	doc = supplier_delivery_service.create_from_sales_invoice(
		sales_invoice_name=sales_invoice,
		supplier=supplier,
		supplier_availability_confirmation_name=supplier_availability_confirmation,
		delivery_date=delivery_date,
		customer_address=customer_address,
		remarks=remarks,
	)
	return {"name": doc.name}
