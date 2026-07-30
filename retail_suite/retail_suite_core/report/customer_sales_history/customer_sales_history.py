"""Customer Sales History (spec Part 7)."""

from __future__ import annotations

import frappe
from frappe.utils import flt

from retail_suite.reports.report_utils import get_showroom_condition


def execute(filters: dict | None = None):
	filters = filters or {}
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{"label": "Customer", "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 180},
		{"label": "Invoices", "fieldname": "invoice_count", "fieldtype": "Int", "width": 90},
		{"label": "Total Purchases", "fieldname": "total_purchases", "fieldtype": "Currency", "width": 130},
		{"label": "Last Purchase Date", "fieldname": "last_purchase_date", "fieldtype": "Date", "width": 140},
		{"label": "Average Invoice", "fieldname": "average_invoice", "fieldtype": "Currency", "width": 130},
	]


def get_data(filters: dict):
	conditions = ["docstatus = 1"]
	values: dict = {}
	if filters.get("from_date"):
		conditions.append("posting_date >= %(from_date)s")
		values["from_date"] = filters["from_date"]
	if filters.get("to_date"):
		conditions.append("posting_date <= %(to_date)s")
		values["to_date"] = filters["to_date"]
	if filters.get("customer"):
		conditions.append("customer = %(customer)s")
		values["customer"] = filters["customer"]

	showroom_condition = get_showroom_condition("custom_showroom", filters.get("showroom"))
	if showroom_condition:
		conditions.append(showroom_condition)

	rows = frappe.db.sql(
		f"""
			select customer, count(*) as invoice_count, sum(grand_total) as total_purchases,
				max(posting_date) as last_purchase_date
			from `tabSales Invoice`
			where {" and ".join(conditions)}
			group by customer
			order by total_purchases desc
		""",
		values,
		as_dict=True,
	)
	for row in rows:
		row["average_invoice"] = flt(row.total_purchases / row.invoice_count, 2) if row.invoice_count else 0
	return rows
