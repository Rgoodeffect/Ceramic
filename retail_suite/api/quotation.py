"""Whitelisted endpoints for Quotation creation. See services/quotation_service.py
for the actual business logic - this module only parses input and shapes output."""

from __future__ import annotations

import json

import frappe

from retail_suite.api.utils import api_endpoint
from retail_suite.services import quotation_service


@frappe.whitelist()
@api_endpoint
def create_quotation(customer: str, showroom: str, items, price_list: str):
	"""`items`: JSON list of {"item_code": str, "required_area_sqm": float}."""
	if isinstance(items, str):
		items = json.loads(items)
	doc = quotation_service.create_quotation(customer, showroom, items, price_list)
	return {"name": doc.name}
