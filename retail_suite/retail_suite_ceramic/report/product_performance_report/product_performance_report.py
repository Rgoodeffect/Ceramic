"""Product Performance Report (spec Part 7): "Fast Moving Products, Slow
Moving Products, Most Profitable Products".

This app has no landed-cost/valuation data for supplier-sourced items (the
spec explicitly forbids tracking supplier stock/cost - Part 1/5), so
"profitability" here is a deliberate proxy: revenue and boxes sold, ranked
both ways. A true margin figure would need Item valuation rate wired in for
company-warehouse items only, which is a natural but separate future
enhancement - not something to fake with invented numbers.
"""

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
		{"label": "Boxes Sold", "fieldname": "boxes_sold", "fieldtype": "Int", "width": 110},
		{"label": "Revenue", "fieldname": "revenue", "fieldtype": "Currency", "width": 130},
		{"label": "Movement", "fieldname": "movement", "fieldtype": "Data", "width": 110},
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

	showroom_condition = get_showroom_condition("si.custom_showroom", filters.get("showroom"))
	if showroom_condition:
		conditions.append(showroom_condition)

	rows = frappe.db.sql(
		f"""
			select sii.item_code, sum(sii.qty) as boxes_sold, sum(sii.amount) as revenue
			from `tabSales Invoice Item` sii
			join `tabSales Invoice` si on si.name = sii.parent
			where {" and ".join(conditions)}
			group by sii.item_code
			order by boxes_sold desc
		""",
		values,
		as_dict=True,
	)
	if not rows:
		return rows

	fast_cutoff = max(1, len(rows) // 3)
	slow_cutoff = max(1, len(rows) - fast_cutoff)
	for idx, row in enumerate(rows):
		if idx < fast_cutoff:
			row["movement"] = "Fast Moving"
		elif idx >= slow_cutoff:
			row["movement"] = "Slow Moving"
		else:
			row["movement"] = "Moderate"
	return rows
