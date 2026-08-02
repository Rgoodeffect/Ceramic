"""Sales Invoice creation and submission-time validation (spec Part 5)."""

from __future__ import annotations

import frappe
from frappe import _

from retail_suite.retail_suite_ceramic import calculation_service
from retail_suite.retail_suite_core.doctype.retail_suite_settings.retail_suite_settings import (
	get_default_company,
)
from retail_suite.retail_suite_core.permissions import permission_service

SUPPLIER_SOURCE = "Supplier"
WAREHOUSE_SOURCE = "Company Warehouse"
VALID_SUPPLY_SOURCES = (SUPPLIER_SOURCE, WAREHOUSE_SOURCE)


def create_sales_invoice(customer: str, showroom: str, items: list[dict], price_list: str):
	"""Direct "New Sale" path (no prior quotation).

	`items`: list of {"item_code", "required_area_sqm", "supply_source"}.
	"""
	permission_service.assert_showroom_access(showroom)
	if not items:
		frappe.throw(_("At least one item is required to create a sales invoice."))

	invoice = frappe.new_doc("Sales Invoice")
	invoice.company = get_default_company()
	invoice.customer = customer
	invoice.custom_showroom = showroom
	invoice.selling_price_list = price_list

	for item in items:
		_assert_valid_supply_source(item.get("supply_source"), item["item_code"])
		row = invoice.append("items", {})
		row.item_code = item["item_code"]
		row.custom_required_area_sqm = item["required_area_sqm"]
		row.custom_supply_source = item["supply_source"]
		calculation_service.apply_to_item_row(row, price_list)

	invoice.insert()
	return invoice


def submit_sales_invoice(name: str):
	"""Finalize a draft Sales Invoice (spec Part 4: "Create Invoice" completes the sale).

	Kept as its own step, separate from `create_sales_invoice`, rather than
	submitting inline there: `before_submit`'s supplier-confirmation gate
	(`validate_supplier_confirmation_before_submit`) needs to be able to
	reject a submit while still leaving the invoice created as a draft the
	salesperson can come back to once availability is confirmed, not fail
	the whole checkout.
	"""
	invoice = frappe.get_doc("Sales Invoice", name)
	permission_service.assert_showroom_access(invoice.custom_showroom)
	invoice.submit()
	return invoice


def create_sales_invoice_from_quotation(quotation_name: str, supply_source_by_item: dict[str, str]):
	"""Convert an accepted Quotation into a Sales Invoice.

	Reuses ERPNext's own Quotation -> Sales Invoice mapping
	(`erpnext.selling.doctype.quotation.quotation.make_sales_invoice`)
	instead of re-implementing `get_mapped_doc`, then fills in the one thing
	that mapping does not know: the per-item supply source decision, which
	only happens after the sale (spec Part 5: "Supply Source Decision").
	"""
	from erpnext.selling.doctype.quotation.quotation import make_sales_invoice

	quotation = frappe.get_doc("Quotation", quotation_name)
	permission_service.assert_showroom_access(quotation.custom_showroom)

	invoice = make_sales_invoice(quotation_name)
	invoice.custom_showroom = quotation.custom_showroom

	for row in invoice.items:
		supply_source = supply_source_by_item.get(row.item_code)
		_assert_valid_supply_source(supply_source, row.item_code)
		row.custom_supply_source = supply_source
		# Re-run the same engine manual Desk entry uses so a stale mapped
		# rate never silently diverges from the calculation.
		calculation_service.apply_to_item_row(row, invoice.selling_price_list)

	invoice.insert()
	return invoice


def validate_supply_sources(sales_invoice, method=None) -> None:
	"""`validate` doc_event body (wired in Phase 5): every item needs a supply source."""
	for row in sales_invoice.items:
		_assert_valid_supply_source(row.custom_supply_source, row.item_code, row_idx=row.idx)


def validate_supplier_confirmation_before_submit(sales_invoice, method=None) -> None:
	"""`before_submit` doc_event body (wired in Phase 5).

	Spec Part 5/12: a Sales Invoice line sourced from a Supplier cannot be
	submitted until a *Confirmed* Supplier Availability Confirmation exists
	for that item and showroom. The exact supplier is pinned down later,
	when the Supplier Delivery Order is created against that confirmation.
	"""
	for row in sales_invoice.items:
		if row.custom_supply_source != SUPPLIER_SOURCE:
			continue
		confirmed = frappe.db.exists(
			"Supplier Availability Confirmation",
			{
				"item": row.item_code,
				"showroom": sales_invoice.custom_showroom,
				"status": "Confirmed",
				"docstatus": 1,
			},
		)
		if not confirmed:
			frappe.throw(
				_(
					"Supplier availability confirmation is required before creating a supplier "
					"delivery for item {0}."
				).format(row.item_code)
			)


def _assert_valid_supply_source(supply_source: str | None, item_code: str, row_idx: int | None = None) -> None:
	if supply_source in VALID_SUPPLY_SOURCES:
		return
	prefix = _("Row #{0}: ").format(row_idx) if row_idx else ""
	frappe.throw(
		prefix
		+ _("Select a supply source ({0} or {1}) for item {2}.").format(
			WAREHOUSE_SOURCE, SUPPLIER_SOURCE, item_code
		)
	)
