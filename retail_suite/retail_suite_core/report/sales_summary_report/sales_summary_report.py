"""Sales Summary Report (spec Part 7): monitor sales performance.

"Salesperson" is the Sales Invoice's owner (the logged-in user who created
it via the POS/Desk) - this app has no separate Sales Team allocation step,
so the creating user is the most accurate available proxy.
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
		{"label": "Date", "fieldname": "posting_date", "fieldtype": "Date", "width": 100},
		{"label": "Invoice", "fieldname": "name", "fieldtype": "Link", "options": "Sales Invoice", "width": 140},
		{"label": "Showroom", "fieldname": "custom_showroom", "fieldtype": "Link", "options": "Branch", "width": 120},
		{"label": "Salesperson", "fieldname": "owner", "fieldtype": "Link", "options": "User", "width": 160},
		{"label": "Customer", "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 160},
		{"label": "Total Amount", "fieldname": "grand_total", "fieldtype": "Currency", "width": 120},
		{"label": "Payment Status", "fieldname": "status", "fieldtype": "Data", "width": 110},
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
	if filters.get("customer"):
		conditions.append("si.customer = %(customer)s")
		values["customer"] = filters["customer"]
	if filters.get("salesperson"):
		conditions.append("si.owner = %(salesperson)s")
		values["salesperson"] = filters["salesperson"]
	if filters.get("item_group"):
		conditions.append(
			"exists (select 1 from `tabSales Invoice Item` sii "
			"join `tabItem` it on it.item_code = sii.item_code "
			"where sii.parent = si.name and it.item_group = %(item_group)s)"
		)
		values["item_group"] = filters["item_group"]

	showroom_condition = get_showroom_condition("si.custom_showroom", filters.get("showroom"))
	if showroom_condition:
		conditions.append(showroom_condition)

	query = f"""
		select
			si.posting_date, si.name, si.custom_showroom, si.owner,
			si.customer, si.grand_total, si.status
		from `tabSales Invoice` si
		where {" and ".join(conditions)}
		order by si.posting_date desc, si.name desc
	"""
	return frappe.db.sql(query, values, as_dict=True)
