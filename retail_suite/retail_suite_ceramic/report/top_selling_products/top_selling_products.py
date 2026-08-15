"""Top Selling Products (spec Part 7)."""

from __future__ import annotations

import frappe

from retail_suite.reports.report_utils import get_showroom_condition


def execute(filters: dict | None = None):
	filters = filters or {}
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{"label": "Item", "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 160},
		{"label": "Category", "fieldname": "item_group", "fieldtype": "Link", "options": "Item Group", "width": 140},
		{"label": "Boxes Sold", "fieldname": "boxes_sold", "fieldtype": "Int", "width": 110},
		{"label": "Area Sold (m²)", "fieldname": "area_sold", "fieldtype": "Float", "precision": 2, "width": 130},
		{"label": "Revenue", "fieldname": "revenue", "fieldtype": "Currency", "width": 130},
	]


def get_data(filters: dict):
	conditions = ["si.docstatus = 1"]
	values: dict = {}
	if filters.get("from_date"):
		conditions.append("si.posting_date >= %(from_date)s")
		values["from_date"] = filters["from_date"]
	if filters.get("to_date"):
		conditions.append("si.posting_date <= %(to_date)s")
		values["to_date"] = filters["to_date"]
	if filters.get("item_group"):
		conditions.append("it.item_group = %(item_group)s")
		values["item_group"] = filters["item_group"]

	showroom_condition = get_showroom_condition("si.custom_showroom", filters.get("showroom"))
	if showroom_condition:
		conditions.append(showroom_condition)

	query = f"""
		select
			sii.item_code, it.item_group,
			sum(sii.qty) as boxes_sold,
			sum(sii.custom_delivered_area_sqm) as area_sold,
			sum(sii.amount) as revenue
		from `tabSales Invoice Item` sii
		join `tabSales Invoice` si on si.name = sii.parent
		join `tabItem` it on it.item_code = sii.item_code
		where {" and ".join(conditions)}
		group by sii.item_code, it.item_group
		order by revenue desc
	"""
	return frappe.db.sql(query, values, as_dict=True)
