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
		quotation = frappe.get_doc({"doctype": "Quotation", "name": "QTN-TEST-0001"})
		print_service.apply_print_context(quotation)
		self.assertEqual(quotation.custom_qr_code, "Quotation:QTN-TEST-0001")

	def test_qr_code_is_skipped_for_unsupported_doctypes(self):
		delivery_note = frappe.get_doc({"doctype": "Delivery Note", "name": "DN-TEST-0001"})
		print_service.apply_print_context(delivery_note)
		self.assertIsNone(delivery_note.get("custom_qr_code"))
