"""Number Card computations for the Showroom/Executive dashboards (spec
Part 3/7).

Implemented as whitelisted Python functions (Number Card type "Custom")
rather than static filter JSON, because several of these metrics ("today",
"this month", "this year") need a real dynamic date range evaluated on
every view, not a filter value frozen at fixture-authoring time.

Every query goes through `frappe.get_list` (not `get_all`), which applies
the viewer's normal permissions - including our showroom
permission_query_conditions - automatically. A restricted user's "Today's
Sales" card is already scoped to their own showroom for free; nothing
showroom-specific needs to happen in this file.
"""

from __future__ import annotations

import frappe
from frappe.utils import flt, get_first_day, getdate, today


def _count(doctype: str, filters: dict) -> dict:
	rows = frappe.get_list(doctype, filters=filters, fields=["count(name) as total"])
	return {"value": rows[0].total if rows and rows[0].total else 0}


def _sum(doctype: str, fieldname: str, filters: dict) -> dict:
	rows = frappe.get_list(doctype, filters=filters, fields=[f"sum({fieldname}) as total"])
	return {"value": flt(rows[0].total if rows and rows[0].total else 0, 2)}


def _avg(doctype: str, fieldname: str, filters: dict) -> dict:
	rows = frappe.get_list(doctype, filters=filters, fields=[f"avg({fieldname}) as average"])
	return {"value": flt(rows[0].average if rows and rows[0].average else 0, 2)}


@frappe.whitelist()
def todays_sales():
	return _sum("Sales Invoice", "grand_total", {"posting_date": today(), "docstatus": 1})


@frappe.whitelist()
def todays_quotations():
	return _count("Quotation", {"transaction_date": today(), "docstatus": ["<", 2]})


@frappe.whitelist()
def todays_invoices():
	return _count("Sales Invoice", {"posting_date": today(), "docstatus": 1})


@frappe.whitelist()
def todays_customers():
	return _count("Customer", {"creation": [">=", today()]})


@frappe.whitelist()
def monthly_sales():
	return _sum(
		"Sales Invoice",
		"grand_total",
		{"posting_date": [">=", get_first_day(today())], "docstatus": 1},
	)


@frappe.whitelist()
def yearly_sales():
	year_start = f"{getdate(today()).year}-01-01"
	return _sum("Sales Invoice", "grand_total", {"posting_date": [">=", year_start], "docstatus": 1})


@frappe.whitelist()
def average_invoice_value():
	return _avg("Sales Invoice", "grand_total", {"docstatus": 1})


@frappe.whitelist()
def total_customers():
	return _count("Customer", {"disabled": 0})


@frappe.whitelist()
def pending_deliveries():
	return _count("Delivery Note", {"docstatus": 0})


@frappe.whitelist()
def pending_supplier_orders():
	return _count("Supplier Delivery Order", {"status": ["in", ["Draft", "Confirmed"]], "docstatus": ["<", 2]})


@frappe.whitelist()
def pending_payments():
	return _sum("Sales Invoice", "outstanding_amount", {"docstatus": 1, "outstanding_amount": [">", 0]})
