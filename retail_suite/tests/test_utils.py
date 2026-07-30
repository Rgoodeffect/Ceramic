"""Shared test-data helpers. Not a test module itself (no Test* classes) -
factored out because nearly every retail_suite test needs a Branch, a
showroom-restricted User, a ceramic Item with an Sq Meter price, a
Customer, or a Supplier, and repeating that setup in every test file would
drift out of sync over time.
"""

from __future__ import annotations

import frappe


def ensure_branch(name: str) -> str:
	if not frappe.db.exists("Branch", name):
		frappe.get_doc({"doctype": "Branch", "branch": name}).insert(ignore_permissions=True)
	return name


def ensure_user(email: str, role: str | None = None, showroom: str | None = None) -> str:
	if not frappe.db.exists("User", email):
		user = frappe.get_doc(
			{"doctype": "User", "email": email, "first_name": email.split("@")[0], "send_welcome_email": 0}
		)
		user.insert(ignore_permissions=True)
		if role:
			user.add_roles(role)
	if showroom and not frappe.db.exists("User Permission", {"user": email, "allow": "Branch", "for_value": showroom}):
		frappe.get_doc(
			{"doctype": "User Permission", "user": email, "allow": "Branch", "for_value": showroom}
		).insert(ignore_permissions=True)
	return email


def ensure_item(item_code: str, area_per_box: float = 1.5) -> str:
	if not frappe.db.exists("Item", item_code):
		frappe.get_doc(
			{
				"doctype": "Item",
				"item_code": item_code,
				"item_name": item_code,
				"item_group": "All Item Groups",
				"stock_uom": "Box",
				"custom_area_per_box": area_per_box,
			}
		).insert(ignore_permissions=True)
	else:
		frappe.db.set_value("Item", item_code, "custom_area_per_box", area_per_box)
	return item_code


def ensure_price(item_code: str, price_list: str, rate: float) -> str:
	if not frappe.db.exists("Price List", price_list):
		frappe.get_doc(
			{
				"doctype": "Price List",
				"price_list_name": price_list,
				"selling": 1,
				"currency": frappe.db.get_default("currency") or "USD",
			}
		).insert(ignore_permissions=True)

	existing = frappe.db.exists("Item Price", {"item_code": item_code, "price_list": price_list, "uom": "Sq Meter"})
	if existing:
		frappe.db.set_value("Item Price", existing, "price_list_rate", rate)
	else:
		frappe.get_doc(
			{
				"doctype": "Item Price",
				"item_code": item_code,
				"price_list": price_list,
				"uom": "Sq Meter",
				"selling": 1,
				"price_list_rate": rate,
			}
		).insert(ignore_permissions=True)
	return price_list


def ensure_customer(name: str) -> str:
	if not frappe.db.exists("Customer", name):
		frappe.get_doc({"doctype": "Customer", "customer_name": name, "customer_type": "Individual"}).insert(
			ignore_permissions=True
		)
	return name


def ensure_supplier(name: str) -> str:
	if not frappe.db.exists("Supplier", name):
		frappe.get_doc(
			{"doctype": "Supplier", "supplier_name": name, "supplier_group": "All Supplier Groups"}
		).insert(ignore_permissions=True)
	return name
