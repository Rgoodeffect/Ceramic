"""Whitelisted read endpoint backing the POS product catalog
(spec Part 2/4: Product Search, Product Cards). Read-only, so it does not
route through a services/ module - it's a direct, permission-checked query
over the standard Item / Item Price doctypes."""

from __future__ import annotations

import frappe

from retail_suite.api.utils import api_endpoint

POS_ITEM_FIELDS = [
	"item_code",
	"item_name",
	"image",
	"brand",
	"custom_product_type",
	"custom_width",
	"custom_height",
	"custom_thickness",
	"custom_finish",
	"custom_color",
	"custom_collection",
	"custom_series",
	"custom_area_per_box",
	"custom_pieces_per_box",
	"custom_featured_product",
	"custom_display_sequence",
]


@frappe.whitelist()
@api_endpoint
def search_items(search_term: str = "", price_list: str | None = None, limit: int = 20):
	"""Search ceramic items for the POS grid by code, name, brand, collection,
	series, or color. Arabic and English both match: `like` is charset-agnostic.
	"""
	limit = min(int(limit), 100)
	filters = {"disabled": 0, "custom_show_in_pos": 1}
	or_filters = None
	if search_term:
		like = f"%{search_term}%"
		or_filters = [
			["item_code", "like", like],
			["item_name", "like", like],
			["brand", "like", like],
			["custom_collection", "like", like],
			["custom_series", "like", like],
			["custom_color", "like", like],
		]

	items = frappe.get_list(
		"Item",
		filters=filters,
		or_filters=or_filters,
		fields=POS_ITEM_FIELDS,
		order_by="custom_display_sequence asc, item_name asc",
		limit_page_length=limit,
	)

	if price_list:
		for item in items:
			item["price_per_sqm"] = frappe.db.get_value(
				"Item Price",
				{
					"item_code": item["item_code"],
					"price_list": price_list,
					"uom": "Sq Meter",
					"selling": 1,
				},
				"price_list_rate",
			)

	return items
