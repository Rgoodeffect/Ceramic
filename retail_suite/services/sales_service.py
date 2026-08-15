"""Sales Invoice creation and submission-time validation (spec Part 5)."""

from __future__ import annotations

import frappe
from frappe import _

from retail_suite.retail_suite_ceramic import calculation_service
from retail_suite.retail_suite_core.doctype.retail_suite_settings.retail_suite_settings import (
	get_default_company,
	is_supplier_confirmation_required,
)
from retail_suite.retail_suite_core.permissions import permission_service

SUPPLIER_SOURCE = "Supplier"
WAREHOUSE_SOURCE = "Company Warehouse"
VALID_SUPPLY_SOURCES = (SUPPLIER_SOURCE, WAREHOUSE_SOURCE)


def create_sales_invoice(customer: str, showroom: str, items: list[dict], price_list: str):
	"""Direct "New Sale" path (no prior quotation).

	`items`: list of {"item_code", "supply_source", "supplier", and either
	"required_area_sqm" (ceramic items) or "qty" (everything else - sold by
	the piece, bag, etc., not the square meter)}.
	`supplier` is required when `supply_source` is "Supplier" (spec Part 5 supply
	source decision) - see `_assert_valid_supply_source`.
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
		_assert_valid_supply_source(item.get("supply_source"), item["item_code"], supplier=item.get("supplier"))
		row = invoice.append("items", {})
		row.item_code = item["item_code"]
		row.custom_supply_source = item["supply_source"]
		if item["supply_source"] == SUPPLIER_SOURCE:
			row.custom_supplier = item.get("supplier")
		if item.get("required_area_sqm"):
			row.custom_required_area_sqm = item["required_area_sqm"]
			calculation_service.apply_to_item_row(row, price_list)
		else:
			calculation_service.apply_simple_row(row, item.get("qty"), price_list)

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


def create_sales_invoice_from_quotation(quotation_name: str, supply_source_by_item: dict[str, str | dict]):
	"""Convert an accepted Quotation into a Sales Invoice.

	Reuses ERPNext's own Quotation -> Sales Invoice mapping
	(`erpnext.selling.doctype.quotation.quotation.make_sales_invoice`)
	instead of re-implementing `get_mapped_doc`, then fills in the one thing
	that mapping does not know: the per-item supply source decision, which
	only happens after the sale (spec Part 5: "Supply Source Decision").

	Each value in `supply_source_by_item` is either the plain supply-source
	string ("Company Warehouse"/"Supplier" - Company Warehouse items need
	nothing else) or, for a Supplier-sourced item,
	`{"supply_source": "Supplier", "supplier": "<Supplier name>"}`.
	"""
	from erpnext.selling.doctype.quotation.quotation import make_sales_invoice

	quotation = frappe.get_doc("Quotation", quotation_name)
	permission_service.assert_showroom_access(quotation.custom_showroom)

	invoice = make_sales_invoice(quotation_name)
	invoice.custom_showroom = quotation.custom_showroom

	for row in invoice.items:
		entry = supply_source_by_item.get(row.item_code)
		if isinstance(entry, dict):
			supply_source, supplier = entry.get("supply_source"), entry.get("supplier")
		else:
			supply_source, supplier = entry, None
		_assert_valid_supply_source(supply_source, row.item_code, supplier=supplier)
		row.custom_supply_source = supply_source
		if supply_source == SUPPLIER_SOURCE:
			row.custom_supplier = supplier
		# Re-run the same engine manual Desk entry uses so a stale mapped
		# rate never silently diverges from the calculation. Only ceramic
		# rows carry a required area - everything else keeps the qty/rate
		# the mapping already carried over from the Quotation row.
		if row.custom_required_area_sqm:
			calculation_service.apply_to_item_row(row, invoice.selling_price_list)

	invoice.insert()
	return invoice


def validate_supply_sources(sales_invoice, method=None) -> None:
	"""`validate` doc_event body (wired in Phase 5): every item needs a supply
	source, and a Supplier-sourced item needs a supplier (`custom_supplier`)
	picked directly on the line - see module docstring on why this no longer
	goes through a Supplier Availability Confirmation by default."""
	for row in sales_invoice.items:
		_assert_valid_supply_source(
			row.custom_supply_source, row.item_code, row_idx=row.idx, supplier=row.get("custom_supplier")
		)


def validate_supplier_confirmation_before_submit(sales_invoice, method=None) -> None:
	"""`before_submit` doc_event body (wired in Phase 5).

	Only enforced when Retail Suite Settings > Require Supplier Availability
	Confirmation is on (off by default - see
	`retail_suite_settings.is_supplier_confirmation_required`). When off, a
	Supplier-sourced line only needs its `custom_supplier` set (already
	guaranteed by `validate_supply_sources`), so the invoice, its Supplier
	Delivery Order, and any payment against it can all proceed without a
	separate confirmation record.
	"""
	if not is_supplier_confirmation_required():
		return
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


def _assert_valid_supply_source(
	supply_source: str | None, item_code: str, row_idx: int | None = None, supplier: str | None = None
) -> None:
	prefix = _("Row #{0}: ").format(row_idx) if row_idx else ""
	if supply_source not in VALID_SUPPLY_SOURCES:
		frappe.throw(
			prefix
			+ _("Select a supply source ({0} or {1}) for item {2}.").format(
				WAREHOUSE_SOURCE, SUPPLIER_SOURCE, item_code
			)
		)
	if supply_source == SUPPLIER_SOURCE and not supplier:
		frappe.throw(prefix + _("Select a supplier for Supplier-sourced item {0}.").format(item_code))
