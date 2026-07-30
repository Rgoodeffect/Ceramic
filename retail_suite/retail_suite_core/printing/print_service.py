"""Print-time customization (spec Part 8): automatically select the Letter
Head for the document's showroom - the user never manually picks one - and
populate the QR code field. Wired via hooks.py `before_print`.
"""

from __future__ import annotations

import frappe

SHOWROOM_FIELD_BY_DOCTYPE = {
	"Quotation": "custom_showroom",
	"Sales Invoice": "custom_showroom",
	"Delivery Note": "custom_showroom",
	"Purchase Invoice": "custom_showroom",
	"Supplier Delivery Order": "showroom",
}

QR_FIELD_DOCTYPES = {"Quotation", "Sales Invoice", "Payment Entry"}


def apply_print_context(doc, method=None, print_settings=None) -> None:
	_apply_letter_head(doc)
	_apply_qr_code(doc)


def _apply_letter_head(doc) -> None:
	fieldname = SHOWROOM_FIELD_BY_DOCTYPE.get(doc.doctype)
	if not fieldname or not doc.meta.has_field("letter_head"):
		return
	showroom = doc.get(fieldname)
	if not showroom:
		return
	letter_head = frappe.db.get_value("Branch", showroom, "custom_letter_head")
	if letter_head:
		doc.letter_head = letter_head


def _apply_qr_code(doc) -> None:
	if doc.doctype not in QR_FIELD_DOCTYPES or not doc.meta.has_field("custom_qr_code"):
		return
	doc.custom_qr_code = f"{doc.doctype}:{doc.name}"
