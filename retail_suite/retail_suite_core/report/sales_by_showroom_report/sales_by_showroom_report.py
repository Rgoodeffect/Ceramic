"""Sales By Showroom Report (spec Part 7): compare branches. Company Owner only."""

from __future__ import annotations

import frappe
from frappe.utils import add_days, date_diff, flt, getdate

from retail_suite.reports.report_utils import require_company_owner


def execute(filters: dict | None = None):
	require_company_owner()
	filters = filters or {}
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{"label": "Showroom", "fieldname": "showroom", "fieldtype": "Link", "options": "Branch", "width": 140},
		{"label": "Number of Sales", "fieldname": "invoice_count", "fieldtype": "Int", "width": 120},
		{"label": "Total Revenue", "fieldname": "total_revenue", "fieldtype": "Currency", "width": 130},
		{"label": "Average Invoice Value", "fieldname": "average_invoice", "fieldtype": "Currency", "width": 150},
		{"label": "Growth vs Prior Period (%)", "fieldname": "growth_percentage", "fieldtype": "Percent", "width": 170},
	]


def get_data(filters: dict):
	from_date = filters.get("from_date")
	to_date = filters.get("to_date")
	current = _revenue_by_showroom(from_date, to_date)

	prior_from, prior_to = _prior_period(from_date, to_date)
	prior = _revenue_by_showroom(prior_from, prior_to) if prior_from else {}

	rows = []
	for showroom, stats in current.items():
		prior_revenue = prior.get(showroom, {}).get("total_revenue", 0)
		growth = _growth_percentage(stats["total_revenue"], prior_revenue)
		rows.append(
			{
				"showroom": showroom,
				"invoice_count": stats["invoice_count"],
				"total_revenue": stats["total_revenue"],
				"average_invoice": flt(stats["total_revenue"] / stats["invoice_count"], 2)
				if stats["invoice_count"]
				else 0,
				"growth_percentage": growth,
			}
		)
	rows.sort(key=lambda r: r["total_revenue"], reverse=True)
	return rows


def _revenue_by_showroom(from_date, to_date) -> dict:
	conditions = ["docstatus = 1"]
	values: dict = {}
	if from_date:
		conditions.append("posting_date >= %(from_date)s")
		values["from_date"] = from_date
	if to_date:
		conditions.append("posting_date <= %(to_date)s")
		values["to_date"] = to_date

	rows = frappe.db.sql(
		f"""
			select custom_showroom as showroom, count(*) as invoice_count, sum(grand_total) as total_revenue
			from `tabSales Invoice`
			where {" and ".join(conditions)}
			group by custom_showroom
		""",
		values,
		as_dict=True,
	)
	return {row.showroom: row for row in rows if row.showroom}


def _prior_period(from_date, to_date):
	if not from_date or not to_date:
		return None, None
	days = date_diff(to_date, from_date) + 1
	prior_to = add_days(getdate(from_date), -1)
	prior_from = add_days(prior_to, -days + 1)
	return prior_from, prior_to


def _growth_percentage(current_revenue, prior_revenue) -> float:
	if not prior_revenue:
		return 100.0 if current_revenue else 0.0
	return flt((current_revenue - prior_revenue) / prior_revenue * 100, 2)
