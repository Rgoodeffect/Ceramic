import frappe
from frappe.tests.utils import FrappeTestCase


class TestSupplierDeliveryOrder(FrappeTestCase):
	def test_cannot_save_without_items(self):
		doc = frappe.get_doc(
			{
				"doctype": "Supplier Delivery Order",
				"supplier": "_Test Supplier",
				"showroom": "_Test Showroom VF",
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
