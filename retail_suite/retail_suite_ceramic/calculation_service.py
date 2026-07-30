"""The single source of truth for area/box math (spec Part 6: Calculation Engine).

Every place that turns a customer's required area into boxes, a delivered
area, or an invoice amount must go through this module - the POS API, the
Quotation/Sales Invoice `validate` doc_events (Phase 5), and reports. Never
duplicate these formulas elsewhere.
"""

from __future__ import annotations

import math

import frappe
from frappe import _


def calculate_boxes(required_area_sqm: float, area_per_box: float) -> int:
	"""Round the required area up to a whole number of boxes. Never returns a fraction."""
	if required_area_sqm is None or required_area_sqm <= 0:
		frappe.throw(_("Required area must be greater than zero."), frappe.ValidationError)
	if area_per_box is None or area_per_box <= 0:
		frappe.throw(_("Area per box must be greater than zero."), frappe.ValidationError)
	return math.ceil(required_area_sqm / area_per_box)


def calculate_delivered_area(boxes: int, area_per_box: float) -> float:
	"""What the customer actually receives and pays for: boxes x area per box."""
	return round(boxes * area_per_box, 3)


def get_item_area_per_box(item_code: str) -> float:
	area_per_box = frappe.db.get_value("Item", item_code, "custom_area_per_box")
	if not area_per_box or area_per_box <= 0:
		frappe.throw(
			_("Item {0} does not have a valid Area Per Box configured.").format(item_code),
			frappe.ValidationError,
		)
	return area_per_box


def get_item_price_per_sqm(item_code: str, price_list: str) -> float:
	"""Look up the Sq Meter price from the standard Item Price / Price List - never a
	custom pricing engine (spec: "Use ERPNext Price List. Do not create custom pricing
	engine.")."""
	if not price_list:
		frappe.throw(_("A price list is required to price item {0}.").format(item_code))
	price_list_rate = frappe.db.get_value(
		"Item Price",
		{"item_code": item_code, "price_list": price_list, "uom": "Sq Meter", "selling": 1},
		"price_list_rate",
	)
	if price_list_rate is None:
		frappe.throw(
			_("No Sq Meter price found for item {0} in price list {1}.").format(item_code, price_list),
			frappe.ValidationError,
		)
	return price_list_rate


def calculate_row(item_code: str, required_area_sqm: float, price_list: str) -> dict:
	"""Full calculation for one Quotation/Sales Invoice item row.

	Returns boxes, the area actually delivered, the per-box rate translated
	from the Sq Meter price list, and the line amount - all derived from the
	single required-area input and the item's configured Area Per Box.
	"""
	area_per_box = get_item_area_per_box(item_code)
	boxes = calculate_boxes(required_area_sqm, area_per_box)
	delivered_area_sqm = calculate_delivered_area(boxes, area_per_box)
	price_per_sqm = get_item_price_per_sqm(item_code, price_list)
	rate_per_box = round(price_per_sqm * area_per_box, 2)
	amount = round(boxes * rate_per_box, 2)
	return {
		"boxes": boxes,
		"area_per_box": area_per_box,
		"delivered_area_sqm": delivered_area_sqm,
		"price_per_sqm": price_per_sqm,
		"rate_per_box": rate_per_box,
		"amount": amount,
	}


def apply_to_item_row(row, price_list: str) -> None:
	"""Mutate a Quotation Item / Sales Invoice Item child row from its required area.

	Called both when the POS API builds rows programmatically and from the
	`validate` doc_event on manually-entered Desk documents (Phase 5), so
	both paths produce identical numbers.
	"""
	result = calculate_row(row.item_code, row.custom_required_area_sqm, price_list)
	row.qty = result["boxes"]
	row.uom = "Box"
	row.rate = result["rate_per_box"]
	row.custom_delivered_area_sqm = result["delivered_area_sqm"]


def validate_item_rows(doc) -> None:
	"""`validate` doc_event body for Quotation and Sales Invoice (Phase 5).

	Recomputes every ceramic item row from its required area so manual Desk
	entry and the POS API always agree. Items without a configured Area Per
	Box (i.e. not part of the ceramic vertical) are left untouched, so this
	is safe on an instance where other, non-retail sales also happen.
	"""
	price_list = doc.get("selling_price_list")
	for row in doc.items:
		if not row.custom_required_area_sqm:
			continue
		if not frappe.db.get_value("Item", row.item_code, "custom_area_per_box"):
			continue
		apply_to_item_row(row, price_list)
