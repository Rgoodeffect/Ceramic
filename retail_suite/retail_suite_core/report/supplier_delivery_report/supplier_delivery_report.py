"""Supplier Delivery Report (spec Part 7): one row per Supplier Delivery
Order (rather than aggregated per supplier) so Status and Confirmation Date
- both per-document facts - stay meaningful columns."""

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
		{"label": "Delivery Order", "fieldname": "name", "fieldtype": "Link", "options": "Supplier Delivery Order", "width": 150},
		{"label": "Supplier", "fieldname": "supplier", "fieldtype": "Link", "options": "Supplier", "width": 150},
		{"label": "Showroom", "fieldname": "showroom", "fieldtype": "Link", "options": "Branch", "width": 110},
		{"label": "Customer", "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 150},
		{"label": "Delivery Date", "fieldname": "delivery_date", "fieldtype": "Date", "width": 110},
		{"label": "Items", "fieldname": "item_count", "fieldtype": "Int", "width": 70},
		{"label": "Boxes", "fieldname": "total_boxes", "fieldtype": "Int", "width": 80},
		{"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 100},
		{
			"label": "Confirmation Date",
			"fieldname": "confirmation_date",
			"fieldtype": "Date",
			"width": 130,
		},
	]


def get_data(filters: dict):
	conditions = ["sdo.docstatus < 2"]
	values: dict = {}
	if filters.get("from_date"):
		conditions.append("sdo.delivery_date >= %(from_date)s")
		values["from_date"] = filters["from_date"]
	if filters.get("to_date"):
		conditions.append("sdo.delivery_date <= %(to_date)s")
		values["to_date"] = filters["to_date"]
	if filters.get("supplier"):
		conditions.append("sdo.supplier = %(supplier)s")
		values["supplier"] = filters["supplier"]
	if filters.get("status"):
		conditions.append("sdo.status = %(status)s")
		values["status"] = filters["status"]

	showroom_condition = get_showroom_condition("sdo.showroom", filters.get("showroom"))
	if showroom_condition:
		conditions.append(showroom_condition)

	query = f"""
		select
			sdo.name, sdo.supplier, sdo.showroom, sdo.customer, sdo.delivery_date, sdo.status,
			sac.confirmation_date,
			(select count(*) from `tabSupplier Delivery Order Item` i where i.parent = sdo.name) as item_count,
			(select coalesce(sum(boxes_qty), 0) from `tabSupplier Delivery Order Item` i where i.parent = sdo.name) as total_boxes
		from `tabSupplier Delivery Order` sdo
		left join `tabSupplier Availability Confirmation` sac on sac.name = sdo.supplier_availability_confirmation
		where {" and ".join(conditions)}
		order by sdo.delivery_date desc
	"""
	return frappe.db.sql(query, values, as_dict=True)
