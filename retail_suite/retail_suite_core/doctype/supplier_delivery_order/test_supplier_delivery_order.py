import frappe
from frappe.tests.utils import FrappeTestCase


class TestSupplierDeliveryOrder(FrappeTestCase):
	def test_cannot_save_without_items(self):
		# Not relying on another test file's setUp to have created this Branch
		# first - Frappe's test runner order across files isn't something to
		# depend on, and a bare `frappe.get_doc(...).insert()` validates Links
		# (this Branch existing) before it ever gets to the Mandatory check
		# this test actually wants to exercise.
		branch = "_Test SDO Showroom VF"
		if not frappe.db.exists("Branch", branch):
			frappe.get_doc({"doctype": "Branch", "branch": branch}).insert(ignore_permissions=True)

		doc = frappe.get_doc(
			{
				"doctype": "Supplier Delivery Order",
				"supplier": "_Test Supplier",
				"showroom": branch,
				"customer": "_Test Customer",
				"delivery_date": frappe.utils.today(),
				"items": [],
			}
		)
		with self.assertRaises(frappe.MandatoryError):
			doc.insert()

	def test_no_price_fields_on_item_row(self):
		meta = frappe.get_meta("Supplier Delivery Order Item")
		price_fieldnames = {"rate", "amount", "price_list_rate", "base_rate", "base_amount"}
		actual_fieldnames = {df.fieldname for df in meta.fields}
		self.assertTrue(
			price_fieldnames.isdisjoint(actual_fieldnames),
			"Supplier Delivery Order Item must never carry pricing fields (spec: no prices to suppliers).",
		)
