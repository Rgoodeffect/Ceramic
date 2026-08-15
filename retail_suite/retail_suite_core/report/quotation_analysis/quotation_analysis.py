"""Quotation Analysis (spec Part 7): Created/Accepted/Rejected quotations,
conversion rate, grouped by showroom. "Accepted" maps to ERPNext's
Quotation status "Ordered" (converted into a sale); "Rejected" maps to
"Lost" - the two closest standard statuses to the spec's business language.
"""

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
		{"label": "Showroom", "fieldname": "showroom", "fieldtype": "Link", "options": "Branch", "width": 140},
		{"label": "Created Quotations", "fieldname": "created", "fieldtype": "Int", "width": 140},
		{"label": "Accepted (Ordered)", "fieldname": "accepted", "fieldtype": "Int", "width": 140},
		{"label": "Rejected (Lost)", "fieldname": "rejected", "fieldtype": "Int", "width": 130},
		{"label": "Conversion Rate (%)", "fieldname": "conversion_rate", "fieldtype": "Percent", "width": 150},
	]


def get_data(filters: dict):
	conditions = ["docstatus < 2"]
	values: dict = {}
	if filters.get("from_date"):
		conditions.append("transaction_date >= %(from_date)s")
		values["from_date"] = filters["from_date"]
	if filters.get("to_date"):
		conditions.append("transaction_date <= %(to_date)s")
		values["to_date"] = filters["to_date"]

	showroom_condition = get_showroom_condition("custom_showroom", filters.get("showroom"))
	if showroom_condition:
		conditions.append(showroom_condition)

	rows = frappe.db.sql(
		f"""
			select custom_showroom as showroom, status, count(*) as count
			from `tabQuotation`
			where {" and ".join(conditions)}
			group by custom_showroom, status
		""",
		values,
		as_dict=True,
	)

	by_showroom: dict[str, dict[str, int]] = {}
	for row in rows:
		if not row.showroom:
			continue
		bucket = by_showroom.setdefault(row.showroom, {"created": 0, "accepted": 0, "rejected": 0})
		bucket["created"] += row.count
		if row.status == "Ordered":
			bucket["accepted"] += row.count
		elif row.status == "Lost":
			bucket["rejected"] += row.count

	data = []
	for showroom, bucket in by_showroom.items():
		conversion_rate = flt(bucket["accepted"] / bucket["created"] * 100, 2) if bucket["created"] else 0
		data.append({"showroom": showroom, "conversion_rate": conversion_rate, **bucket})
	data.sort(key=lambda r: r["created"], reverse=True)
	return data
