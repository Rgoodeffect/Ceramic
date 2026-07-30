import frappe
from frappe.tests.utils import FrappeTestCase

from retail_suite.retail_suite_core.printing import print_service


class TestPrintService(FrappeTestCase):
	def setUp(self):
		self.letter_head = "_Test Print Service Letter Head"
		if not frappe.db.exists("Letter Head", self.letter_head):
			frappe.get_doc({"doctype": "Letter Head", "letter_head_name": self.letter_head}).insert(
				ignore_permissions=True
			)

		self.branch = "_Test Print Service Showroom"
		if not frappe.db.exists("Branch", self.branch):
			frappe.get_doc(
				{"doctype": "Branch", "branch": self.branch, "custom_letter_head": self.letter_head}
			).insert(ignore_permissions=True)
		else:
			frappe.db.set_value("Branch", self.branch, "custom_letter_head", self.letter_head)

	def test_letter_head_is_set_from_showroom(self):
		quotation = frappe.new_doc("Quotation")
		quotation.custom_showroom = self.branch
		print_service.apply_print_context(quotation)
		self.assertEqual(quotation.letter_head, self.letter_head)

	def test_qr_code_is_populated_for_supported_doctypes(self):
		"""custom_qr_code must be an actual scannable image, not the raw
		reference string - a Barcode field's get_formatted() has no
		server-side rendering, so a print format can only ever show a real
		QR code if this method builds one itself (see print_service.py's
		_apply_qr_code docstring; found by loading a real print view in a
		browser and seeing literal text where a QR code should be).

		PNG, not SVG: an SVG data URI renders fine in a live browser print
		preview but is silently dropped by wkhtmltopdf (the PDF export
		engine) - found by downloading and inspecting a real generated PDF,
		not just the in-browser preview."""
		quotation = frappe.get_doc({"doctype": "Quotation", "name": "QTN-TEST-0001"})
		print_service.apply_print_context(quotation)
		self.assertTrue(quotation.custom_qr_code.startswith("data:image/png;base64,"))
		import base64

		png_bytes = base64.b64decode(quotation.custom_qr_code.split(",", 1)[1])
		self.assertTrue(png_bytes.startswith(b"\x89PNG\r\n\x1a\n"))

	def test_qr_code_is_skipped_for_unsupported_doctypes(self):
		delivery_note = frappe.get_doc({"doctype": "Delivery Note", "name": "DN-TEST-0001"})
		print_service.apply_print_context(delivery_note)
		self.assertIsNone(delivery_note.get("custom_qr_code"))
