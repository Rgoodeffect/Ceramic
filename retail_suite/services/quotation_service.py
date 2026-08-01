"""Quotation creation for the Ceramic Showroom sales flow (spec Part 5)."""

from __future__ import annotations

import frappe
from frappe import _

from retail_suite.retail_suite_ceramic import calculation_service
from retail_suite.retail_suite_core.doctype.retail_suite_settings.retail_suite_settings import (
	get_default_company,
)
from retail_suite.retail_suite_core.permissions import permission_service


def create_quotation(customer: str, showroom: str, items: list[dict], price_list: str):
	"""Create a draft Quotation from POS/API input.

	`items` is a list of {"item_code": str, "required_area_sqm": float}.
	Boxes, delivered area, and rate are computed here via CalculationService -
	the caller only ever supplies the required area, never a box count.
	"""
	permission_service.assert_showroom_access(showroom)
	if not items:
		frappe.throw(_("At least one item is required to create a quotation."))

	quotation = frappe.new_doc("Quotation")
	quotation.company = get_default_company()
	quotation.quotation_to = "Customer"
	quotation.party_name = customer
	quotation.custom_showroom = showroom
	quotation.selling_price_list = price_list

	for item in items:
		row = quotation.append("items", {})
		row.item_code = item["item_code"]
		row.custom_required_area_sqm = item["required_area_sqm"]
		calculation_service.apply_to_item_row(row, price_list)

	quotation.insert()
	return quotation
