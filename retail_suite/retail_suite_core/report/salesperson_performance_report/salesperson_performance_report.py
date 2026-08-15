"""Salesperson Performance Report (spec Part 7). "Salesperson" is the
document owner - see sales_summary_report.py for why."""

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
		{"label": "Salesperson", "fieldname": "salesperson", "fieldtype": "Link", "options": "User", "width": 180},
		{"label": "Number of Customers", "fieldname": "customer_count", "fieldtype": "Int", "width": 140},
		{"label": "Number of Quotations", "fieldname": "quotation_count", "fieldtype": "Int", "width": 140},
		{"label": "Number of Invoices", "fieldname": "invoice_count", "fieldtype": "Int", "width": 130},
		{"label": "Total Sales", "fieldname": "total_sales", "fieldtype": "Currency", "width": 130},
		{"label": "Average Sale", "fieldname": "average_sale", "fieldtype": "Currency", "width": 130},
	]


def get_data(filters: dict):
	date_conditions = []
	values: dict = {}
	if filters.get("from_date"):
		date_conditions.append("posting_date >= %(from_date)s")
		values["from_date"] = filters["from_date"]
	if filters.get("to_date"):
		date_conditions.append("posting_date <= %(to_date)s")
		values["to_date"] = filters["to_date"]

	showroom_condition = get_showroom_condition("custom_showroom", filters.get("showroom"))

	invoice_conditions = ["docstatus = 1", *date_conditions]
	if showroom_condition:
		invoice_conditions.append(showroom_condition)

	invoice_rows = frappe.db.sql(
		f"""
			select owner as salesperson, count(distinct customer) as customer_count,
				count(*) as invoice_count, sum(grand_total) as total_sales
			from `tabSales Invoice`
			where {" and ".join(invoice_conditions)}
			group by owner
		""",
		values,
		as_dict=True,
	)

	quotation_conditions = ["docstatus = 1", *date_conditions]
	if showroom_condition:
		quotation_conditions.append(showroom_condition)

	quotation_rows = frappe.db.sql(
		f"""
			select owner as salesperson, count(*) as quotation_count
			from `tabQuotation`
			where {" and ".join(quotation_conditions)}
			group by owner
		""",
		values,
		as_dict=True,
	)
	quotation_counts = {row.salesperson: row.quotation_count for row in quotation_rows}

	data = []
	for row in invoice_rows:
		data.append(
			{
				"salesperson": row.salesperson,
				"customer_count": row.customer_count,
				"quotation_count": quotation_counts.get(row.salesperson, 0),
				"invoice_count": row.invoice_count,
				"total_sales": row.total_sales,
				"average_sale": flt(row.total_sales / row.invoice_count, 2) if row.invoice_count else 0,
			}
		)
	data.sort(key=lambda r: r["total_sales"], reverse=True)
	return data
