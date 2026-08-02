import frappe
from frappe.tests.utils import FrappeTestCase

from retail_suite.services import fulfillment_service, sales_service
from retail_suite.tests import test_utils


class TestFulfillmentService(FrappeTestCase):
	def setUp(self):
		# Fulfillment needs a real, submittable Sales Invoice, which needs a
		# company - "_Test Company" (INR) is the standard ERPNext test
		# fixture with working default accounts already configured.
		# test_utils.ensure_price falls back to the site's default currency
		# when none is given, so it has to be switched to INR too, or Sales
		# Invoice's own party-account currency check rejects the invoice
		# ("Party Account ... currency (INR) and document currency (USD)
		# should be same") before this test ever reaches fulfillment_service.
		frappe.db.set_default("currency", "INR")
		frappe.db.set_single_value("Retail Suite Settings", "default_company", "_Test Company")
		self.branch = test_utils.ensure_branch("_Test FS Showroom")
		self.user = test_utils.ensure_user(
			"retail-suite-test-fs-user@example.com", role="Retail Salesperson", showroom=self.branch
		)
		self.item = test_utils.ensure_item("_Test FS Item", area_per_box=1.5)
		self.price_list = test_utils.ensure_price(self.item, "_Test FS Price List", rate=50)
		self.customer = test_utils.ensure_customer("_Test FS Customer")

	def _submitted_invoice(self, supply_source="Company Warehouse"):
		with self.set_user(self.user):
			invoice = sales_service.create_sales_invoice(
				customer=self.customer,
				showroom=self.branch,
				items=[{"item_code": self.item, "required_area_sqm": 2.8, "supply_source": supply_source}],
				price_list=self.price_list,
			)
			invoice = sales_service.submit_sales_invoice(invoice.name)
		return invoice

	def test_create_payment_entry_pays_off_outstanding(self):
		invoice = self._submitted_invoice()
		self.assertGreater(invoice.outstanding_amount, 0)
		with self.set_user(self.user):
			payment = fulfillment_service.create_payment_entry(invoice.name)
		self.assertEqual(payment.docstatus, 1)
		self.assertEqual(payment.custom_showroom, self.branch)
		invoice.reload()
		self.assertEqual(invoice.outstanding_amount, 0)

	def test_create_payment_entry_rejects_draft_invoice(self):
		with self.set_user(self.user):
			invoice = sales_service.create_sales_invoice(
				customer=self.customer,
				showroom=self.branch,
				items=[{"item_code": self.item, "required_area_sqm": 2.8, "supply_source": "Company Warehouse"}],
				price_list=self.price_list,
			)
			with self.assertRaises(frappe.ValidationError):
				fulfillment_service.create_payment_entry(invoice.name)

	def test_create_delivery_note_rejects_when_no_warehouse_items(self):
		item = test_utils.ensure_item("_Test FS Supplier Item", area_per_box=1.5)
		price_list = test_utils.ensure_price(item, "_Test FS Supplier Price List", rate=50)
		from retail_suite.services import availability_confirmation_service

		with self.set_user(self.user):
			availability_confirmation_service.record_confirmation(
				supplier=test_utils.ensure_supplier("_Test FS Supplier"),
				showroom=self.branch,
				contact_person="Test Contact",
				phone_number="+10000000000",
				status="Confirmed",
				item=item,
			)
			invoice = sales_service.create_sales_invoice(
				customer=self.customer,
				showroom=self.branch,
				items=[{"item_code": item, "required_area_sqm": 2.8, "supply_source": "Supplier"}],
				price_list=price_list,
			)
			invoice = sales_service.submit_sales_invoice(invoice.name)
			with self.assertRaises(frappe.ValidationError):
				fulfillment_service.create_delivery_note(invoice.name)

	def test_create_delivery_note_rejects_draft_invoice(self):
		with self.set_user(self.user):
			invoice = sales_service.create_sales_invoice(
				customer=self.customer,
				showroom=self.branch,
				items=[{"item_code": self.item, "required_area_sqm": 2.8, "supply_source": "Company Warehouse"}],
				price_list=self.price_list,
			)
			with self.assertRaises(frappe.ValidationError):
				fulfillment_service.create_delivery_note(invoice.name)
