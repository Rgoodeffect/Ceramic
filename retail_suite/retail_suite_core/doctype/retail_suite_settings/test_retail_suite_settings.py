import frappe
from frappe.tests.utils import FrappeTestCase


class TestRetailSuiteSettings(FrappeTestCase):
	def test_is_single(self):
		meta = frappe.get_meta("Retail Suite Settings")
		self.assertTrue(meta.issingle)

	def test_ceramic_enabled_by_default(self):
		settings = frappe.get_single("Retail Suite Settings")
		self.assertEqual(settings.enable_ceramic, 1)
