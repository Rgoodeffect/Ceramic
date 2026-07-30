import frappe
from frappe.tests.utils import FrappeTestCase


class TestSupplierAvailabilityConfirmation(FrappeTestCase):
	def test_default_status_is_pending(self):
		doc = frappe.new_doc("Supplier Availability Confirmation")
		self.assertEqual(doc.status, "Pending")

	def test_status_options_match_spec(self):
		meta = frappe.get_meta("Supplier Availability Confirmation")
		status_field = meta.get_field("status")
		self.assertEqual(status_field.options.split("\n"), ["Pending", "Confirmed", "Rejected"])
