"""Print-time customization (spec Part 8): automatically select the Letter
Head for the document's showroom - the user never manually picks one - and
populate the QR code field. Wired via hooks.py `before_print`.
"""

from __future__ import annotations

from base64 import b64encode
from io import BytesIO

import frappe

SHOWROOM_FIELD_BY_DOCTYPE = {
	"Quotation": "custom_showroom",
	"Sales Invoice": "custom_showroom",
	"Delivery Note": "custom_showroom",
	"Purchase Invoice": "custom_showroom",
	"Payment Entry": "custom_showroom",
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
	"""Populate custom_qr_code with an actual scannable QR code, not the raw
	reference string.

	`custom_qr_code` is a Barcode field (maps to a `longtext` DB column - see
	`frappe.database.mariadb.database.type_map` - so it can hold this) purely
	because Frappe has no dedicated "QR code image" fieldtype. A Barcode
	field's `get_formatted()` (what a naive `{{ doc.get_formatted(...) }}` in
	a print format calls) just returns the plain string value unchanged - the
	scannable graphic only ever gets drawn client-side, by the Desk form
	control's JS barcode library, which isn't loaded during a server-rendered
	print/PDF. Print formats got a real QR code by hand-tracing a document
	through the browser and noticing the field printed as literal text (see
	PLAN.md) - fixed by generating the image ourselves, the same way Frappe's
	own two-factor-auth QR (`frappe.twofactor.get_qr_svg_code`) does: an SVG
	built with `pyqrcode` (already a Frappe dependency), base64-encoded into
	a `data:` URI so print formats can embed it directly with
	`<img src="{{ doc.custom_qr_code }}">` - no extra network request, and it
	survives PDF export the same way any other embedded image does.
	"""
	if doc.doctype not in QR_FIELD_DOCTYPES or not doc.meta.has_field("custom_qr_code"):
		return

	from pyqrcode import create as qrcreate

	stream = BytesIO()
	try:
		qrcreate(f"{doc.doctype}:{doc.name}").svg(stream, scale=4, background="#ffffff", module_color="#111111")
		svg_b64 = b64encode(stream.getvalue()).decode()
	finally:
		stream.close()

	doc.custom_qr_code = f"data:image/svg+xml;base64,{svg_b64}"
