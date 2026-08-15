"""Print-time customization (spec Part 8): automatically select the Letter
Head for the document's showroom - the user never manually picks one - and
populate the QR code field. Wired via hooks.py `before_print`.

`apply_letter_head_default` is *also* wired into `validate` (see hooks.py) -
not just `before_print` - so the correct value is actually saved on the
document, not only computed transiently for one print request. Found by
actually printing two invoices from different showrooms via Desk's "Print"
button (the embedded `/app/print/...` page, not the standalone `/printview`
route both of these were previously verified against): its sidebar Letter
Head dropdown pre-fills itself from `frm.doc.letter_head` - the value
*saved* on the document - and only falls back to whatever Letter Head has
`is_default=1` site-wide when that's empty (`frappe/printing/page/print/
print.js:set_default_letterhead`). Since `before_print` alone never touched
the saved value, every document's dropdown fell back to the same site-wide
default letterhead - happened to be مجموعة الفيتوري's here - regardless of
which showroom the document actually belonged to, and printing then sent
that wrong pre-filled value back to the server as an explicit `letterhead`
query param, which `frappe.www.printview.get_letter_head` prioritizes over
the document's own field. The standalone `/printview` route never showed
this bug because it has no such picker to pre-fill in the first place - it
was `before_print` that had actually been verified in a browser before, not
this second Desk-native entry point.
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
	apply_letter_head_default(doc)
	_apply_qr_code(doc)


def apply_letter_head_default(doc, method=None) -> None:
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
	print/PDF. Fixed by generating the image ourselves with `pyqrcode`
	(already a Frappe dependency, the same library `frappe.twofactor.
	get_qr_svg_code` uses for the two-factor-auth QR), base64-encoded into a
	`data:` URI so print formats can embed it directly with
	`<img src="{{ doc.custom_qr_code }}">`.

	PNG, not SVG: an SVG data URI is exactly what Frappe's own 2FA code
	uses, and it renders correctly in a live browser print preview - but
	`bench`'s PDF export goes through `wkhtmltopdf` (0.12.6, a considerably
	older QtWebKit build) via `frappe.utils.pdf`, which silently drops an
	`<img>` whose `src` is an SVG data URI - confirmed by downloading a real
	PDF (`download_pdf`) and finding zero embedded XObjects on the page,
	despite the exact same HTML rendering the QR code correctly in-browser.
	PNG (via `pyqrcode`'s own `pypng`-backed `.png()`, already installed
	alongside it) is a raster format every renderer here supports the same
	way, browser or PDF.
	"""
	if doc.doctype not in QR_FIELD_DOCTYPES or not doc.meta.has_field("custom_qr_code"):
		return

	from pyqrcode import create as qrcreate

	stream = BytesIO()
	try:
		qrcreate(f"{doc.doctype}:{doc.name}").png(stream, scale=4)
		png_b64 = b64encode(stream.getvalue()).decode()
	finally:
		stream.close()

	doc.custom_qr_code = f"data:image/png;base64,{png_b64}"
