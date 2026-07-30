"""Demo data script (spec Part 11: "Installation Automation ... Demo Data
Script"). Deliberately NOT a fixture: fixtures sync into every site that
installs this app (including real customer sites), which is exactly wrong
for made-up demo companies/showrooms/customers. Run explicitly instead:

    bench --site <site-name> execute retail_suite.setup.demo_data.create_demo_data

Everything here is idempotent (checks existence before creating) so it can
be run more than once safely. It builds one company, the three showrooms
from the spec, one demo user per role, a small ceramic catalog with Sq
Meter pricing, and a worked example of both fulfillment paths (Company
Warehouse and Supplier) so the whole business workflow is visible end to
end, not just isolated records.
"""

from __future__ import annotations

import frappe
from frappe.utils import add_days, today

from retail_suite.services import (
	availability_confirmation_service,
	quotation_service,
	sales_service,
	supplier_delivery_service,
)

COMPANY_NAME = "Ceramic Showrooms Co"
COMPANY_ABBR = "CSC"
DEMO_COUNTRY = "United Arab Emirates"  # placeholder - a real deployment uses the customer's actual country
CURRENCY = "USD"
PRICE_LIST = "Standard Selling"

SHOWROOMS = [
	# (branch name, code, letter head text)
	("مجموعة الفيتوري", "VF", "Al Fitouri Group - Ceramic Showroom"),
	("الأساس", "AS", "Al Asas - Ceramic Showroom"),
	("Athar", "AT", "Athar Ceramic Showroom"),
]

# (email, first_name, role, showroom_code or None for unrestricted)
DEMO_USERS = [
	("ahmed@retailsuite.demo", "Ahmed", "Retail Salesperson", "VF"),
	("mohamed@retailsuite.demo", "Mohamed", "Retail Salesperson", "AS"),
	("ali@retailsuite.demo", "Ali", "Retail Salesperson", "AT"),
	("manager.vf@retailsuite.demo", "Fatima", "Retail Showroom Manager", "VF"),
	("warehouse@retailsuite.demo", "Youssef", "Retail Warehouse User", "VF"),
	("purchasing@retailsuite.demo", "Sara", "Retail Purchasing User", "VF"),
	("accounts@retailsuite.demo", "Omar", "Retail Accounts User", "VF"),
	("owner@retailsuite.demo", "Layla", "Retail Company Owner", None),
]

ITEMS = [
	# (item_code, item_name, width, height, thickness, color, finish, area_per_box, pieces_per_box, price_per_sqm)
	("TILE-MILANO-WHITE-6060", "Milano White 60x60", 600, 600, 9, "White", "Matte", 1.44, 4, 45),
	("PORC-GRIGIO-3060", "Grigio Grey Porcelain 30x60", 300, 600, 10, "Grey", "Polished", 1.44, 8, 60),
	("TILE-BEIGE-2020", "Classic Beige 20x20", 200, 200, 8, "Beige", "Glossy", 1.00, 25, 25),
]


def create_demo_data():
	"""Entry point for `bench execute`. Safe to re-run."""
	company = _create_company()
	branches_by_code = _create_showrooms_and_letter_heads()
	_create_demo_users(branches_by_code)
	_create_catalog()
	customers = _create_customers()
	supplier = _create_supplier()
	_create_showroom_workspaces(branches_by_code)
	_create_sample_workflow(company, branches_by_code, customers, supplier)
	frappe.db.commit()
	print("Retail Suite demo data ready.")


def _create_company() -> str:
	if frappe.db.exists("Company", COMPANY_NAME):
		return COMPANY_NAME
	# NOTE: country/currency are demo placeholders - a real deployment should
	# use the customer's actual country and operating currency.
	frappe.get_doc(
		{
			"doctype": "Company",
			"company_name": COMPANY_NAME,
			"abbr": COMPANY_ABBR,
			"default_currency": CURRENCY,
			"country": DEMO_COUNTRY,
		}
	).insert(ignore_permissions=True)
	return COMPANY_NAME


def _create_showrooms_and_letter_heads() -> dict:
	branches_by_code = {}
	for branch_name, code, letter_head_text in SHOWROOMS:
		letter_head_name = f"{branch_name} Letter Head"
		if not frappe.db.exists("Letter Head", letter_head_name):
			frappe.get_doc(
				{
					"doctype": "Letter Head",
					"letter_head_name": letter_head_name,
					"source": "HTML",
					"content": f"<div style='text-align:center'><h2>{branch_name}</h2><p>{letter_head_text}</p></div>",
				}
			).insert(ignore_permissions=True)

		if not frappe.db.exists("Branch", branch_name):
			frappe.get_doc(
				{
					"doctype": "Branch",
					"branch": branch_name,
					"custom_showroom_code": code,
					"custom_letter_head": letter_head_name,
					"custom_status": "Active",
				}
			).insert(ignore_permissions=True)
		branches_by_code[code] = branch_name
	return branches_by_code


def _create_demo_users(branches_by_code: dict) -> None:
	for email, first_name, role, showroom_code in DEMO_USERS:
		if not frappe.db.exists("User", email):
			user = frappe.get_doc(
				{
					"doctype": "User",
					"email": email,
					"first_name": first_name,
					"send_welcome_email": 0,
					"custom_default_showroom": branches_by_code[showroom_code] if showroom_code else None,
				}
			)
			user.insert(ignore_permissions=True)
			# add_roles() reloads and saves the doc, so it must run after insert.
			user.add_roles(role)
		if showroom_code:
			showroom = branches_by_code[showroom_code]
			if not frappe.db.exists("User Permission", {"user": email, "allow": "Branch", "for_value": showroom}):
				frappe.get_doc(
					{"doctype": "User Permission", "user": email, "allow": "Branch", "for_value": showroom}
				).insert(ignore_permissions=True)


def _create_catalog() -> None:
	item_group = "Ceramic Tiles"
	if not frappe.db.exists("Item Group", item_group):
		frappe.get_doc(
			{"doctype": "Item Group", "item_group_name": item_group, "parent_item_group": "All Item Groups"}
		).insert(ignore_permissions=True)

	brand = "Retail Suite Ceramics"
	if not frappe.db.exists("Brand", brand):
		frappe.get_doc({"doctype": "Brand", "brand": brand}).insert(ignore_permissions=True)

	for item_code, item_name, width, height, thickness, color, finish, area_per_box, pieces, price in ITEMS:
		if not frappe.db.exists("Item", item_code):
			frappe.get_doc(
				{
					"doctype": "Item",
					"item_code": item_code,
					"item_name": item_name,
					"item_group": item_group,
					"brand": brand,
					"stock_uom": "Box",
					"custom_product_type": "Porcelain" if "PORC" in item_code else "Tile",
					"custom_width": width,
					"custom_height": height,
					"custom_thickness": thickness,
					"custom_color": color,
					"custom_finish": finish,
					"custom_area_per_box": area_per_box,
					"custom_pieces_per_box": pieces,
					"custom_show_in_pos": 1,
				}
			).insert(ignore_permissions=True)

		if not frappe.db.exists(
			"Item Price", {"item_code": item_code, "price_list": PRICE_LIST, "uom": "Sq Meter"}
		):
			frappe.get_doc(
				{
					"doctype": "Item Price",
					"item_code": item_code,
					"price_list": PRICE_LIST,
					"uom": "Sq Meter",
					"selling": 1,
					"price_list_rate": price,
				}
			).insert(ignore_permissions=True)


def _create_customers() -> list[str]:
	names = ["Demo Customer One", "Demo Customer Two"]
	for customer_name in names:
		if not frappe.db.exists("Customer", customer_name):
			frappe.get_doc(
				{"doctype": "Customer", "customer_name": customer_name, "customer_type": "Individual"}
			).insert(ignore_permissions=True)
	return names


def _create_supplier() -> str:
	supplier_name = "Demo Ceramic Supplier"
	if not frappe.db.exists("Supplier", supplier_name):
		frappe.get_doc(
			{"doctype": "Supplier", "supplier_name": supplier_name, "supplier_group": "All Supplier Groups"}
		).insert(ignore_permissions=True)
	return supplier_name


def _create_showroom_workspaces(branches_by_code: dict) -> None:
	"""Lightweight per-showroom Workspace variants (deferred from Phase 7 -
	see PLAN.md - since the literal showroom names/branding are this
	customer's business data, not generic app architecture)."""
	for code, branch_name in branches_by_code.items():
		workspace_name = f"{branch_name} Workspace"
		if frappe.db.exists("Workspace", workspace_name):
			continue
		content = [
			{
				"id": f"{code}-header",
				"type": "header",
				"data": {"text": f"<span class=\"h4\"><b>{branch_name}</b></span>", "level": 4, "col": 12},
			},
			{
				"id": f"{code}-shortcut-pos",
				"type": "shortcut",
				"data": {"shortcut_name": "New Sale", "col": 4},
			},
			{
				"id": f"{code}-shortcut-invoices",
				"type": "shortcut",
				"data": {"shortcut_name": "Sales Invoices", "col": 4},
			},
			{
				"id": f"{code}-shortcut-dashboard",
				"type": "shortcut",
				"data": {"shortcut_name": "Showroom Dashboard", "col": 4},
			},
		]
		frappe.get_doc(
			{
				"doctype": "Workspace",
				"name": workspace_name,
				"label": workspace_name,
				"title": workspace_name,
				"module": "Retail Suite Core",
				"public": 1,
				"icon": "retail",
				"content": frappe.as_json(content),
				"shortcuts": [
					{
						"doctype": "Workspace Shortcut",
						"label": "New Sale",
						"type": "Page",
						"link_to": "ceramic-pos",
						"color": "Green",
					},
					{
						"doctype": "Workspace Shortcut",
						"label": "Sales Invoices",
						"type": "DocType",
						"link_to": "Sales Invoice",
						"color": "Blue",
					},
					{
						"doctype": "Workspace Shortcut",
						"label": "Showroom Dashboard",
						"type": "Dashboard",
						"link_to": "Showroom Dashboard",
						"color": "Grey",
					},
				],
			}
		).insert(ignore_permissions=True)


def _create_sample_workflow(company: str, branches_by_code: dict, customers: list[str], supplier: str) -> None:
	"""One worked example of each fulfillment path, exercising the real
	CalculationService/services layer end to end - not just inserted rows."""
	vf = branches_by_code["VF"]
	az = branches_by_code["AS"]

	# --- Company Warehouse path: Quotation -> Sales Invoice ---
	# Marked via `po_no` (Customer's Purchase Order No - a standard Sales
	# Invoice field) purely as an idempotency check for this script; it has
	# no other significance here.
	if not frappe.db.exists("Sales Invoice", {"po_no": "DEMO-WAREHOUSE-PATH"}):
		with frappe.set_user("ahmed@retailsuite.demo"):
			quotation = quotation_service.create_quotation(
				customer=customers[0],
				showroom=vf,
				items=[{"item_code": ITEMS[0][0], "required_area_sqm": 10}],
				price_list=PRICE_LIST,
			)
			quotation.submit()
			invoice = sales_service.create_sales_invoice_from_quotation(
				quotation.name, {ITEMS[0][0]: "Company Warehouse"}
			)
			invoice.po_no = "DEMO-WAREHOUSE-PATH"
			invoice.save(ignore_permissions=True)
			invoice.submit()
			# Next step in a real showroom: create a Delivery Note from this
			# Sales Invoice via the standard "Make > Delivery Note" button
			# (requires Warehouse/Stock Settings configured for the company,
			# which this demo script intentionally does not attempt to set up).

	# --- Supplier path: Availability Confirmation -> Sales Invoice -> Supplier Delivery Order ---
	if not frappe.db.exists("Sales Invoice", {"po_no": "DEMO-SUPPLIER-PATH"}):
		with frappe.set_user("mohamed@retailsuite.demo"):
			confirmation = availability_confirmation_service.record_confirmation(
				supplier=supplier,
				showroom=az,
				contact_person="Supplier Contact",
				phone_number="+971500000000",
				status="Confirmed",
				item=ITEMS[1][0],
				remarks="Demo phone confirmation.",
			)
			invoice = sales_service.create_sales_invoice(
				customer=customers[1],
				showroom=az,
				items=[{"item_code": ITEMS[1][0], "required_area_sqm": 5, "supply_source": "Supplier"}],
				price_list=PRICE_LIST,
			)
			invoice.po_no = "DEMO-SUPPLIER-PATH"
			invoice.save(ignore_permissions=True)
			invoice.submit()
			supplier_delivery_service.create_from_sales_invoice(
				sales_invoice_name=invoice.name,
				supplier_availability_confirmation_name=confirmation.name,
				delivery_date=add_days(today(), 3),
			)
