"""Whitelisted endpoints for Sales Invoice creation. See services/sales_service.py
for the actual business logic - this module only parses input and shapes output."""

from __future__ import annotations

import json

import frappe

from retail_suite.api.utils import api_endpoint
from retail_suite.services import sales_service


@frappe.whitelist()
@api_endpoint
def create_sales_invoice(customer: str, showroom: str, items, price_list: str):
	"""`items`: JSON list of {"item_code", "required_area_sqm", "supply_source"}."""
	if isinstance(items, str):
		items = json.loads(items)
	doc = sales_service.create_sales_invoice(customer, showroom, items, price_list)
	return {"name": doc.name}


@frappe.whitelist()
@api_endpoint
def submit_sales_invoice(sales_invoice: str):
	doc = sales_service.submit_sales_invoice(sales_invoice)
	return {"name": doc.name, "docstatus": doc.docstatus}


@frappe.whitelist()
@api_endpoint
def create_sales_invoice_from_quotation(quotation: str, supply_source_by_item):
	"""`supply_source_by_item`: JSON dict of {item_code: "Company Warehouse"|"Supplier"}."""
	if isinstance(supply_source_by_item, str):
		supply_source_by_item = json.loads(supply_source_by_item)
	doc = sales_service.create_sales_invoice_from_quotation(quotation, supply_source_by_item)
	return {"name": doc.name}
