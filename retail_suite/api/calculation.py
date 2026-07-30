"""Whitelisted preview endpoint for the POS cart (spec Part 4: "Calculation
Display"). This calls the exact same engine used when a document is actually
saved (retail_suite.retail_suite_ceramic.calculation_service) - the POS uses
it purely to show the customer live numbers before committing a cart line."""

from __future__ import annotations

import frappe

from retail_suite.api.utils import api_endpoint
from retail_suite.retail_suite_ceramic import calculation_service


@frappe.whitelist()
@api_endpoint
def preview_row(item_code: str, required_area_sqm: float, price_list: str):
	return calculation_service.calculate_row(item_code, float(required_area_sqm), price_list)
