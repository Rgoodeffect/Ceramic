import frappe
from frappe.tests.utils import FrappeTestCase

from retail_suite.services import availability_confirmation_service, sales_service
from retail_suite.tests import test_utils


class TestSalesService(FrappeTestCase):
	def setUp(self):
		self.branch = test_utils.ensure_branch("_Test SS Showroom")
		self.user = test_utils.ensure_user(
			"retail-suite-test-ss-user@example.com", role="Retail Salesperson", showroom=self.branch
		)
		self.item = test_utils.ensure_item("_Test SS Item", area_per_box=1.5)
		self.price_list = test_utils.ensure_price(self.item, "_Test SS Price List", rate=50)
		self.customer = test_utils.ensure_customer("_Test SS Customer")
		self.supplier = test_utils.ensure_supplier("_Test SS Supplier")

	def test_create_sales_invoice_company_warehouse(self):
		with frappe.set_user(self.user):
			invoice = sales_service.create_sales_invoice(
				customer=self.customer,
				showroom=self.branch,
				items=[
					{
						"item_code": self.item,
						"required_area_sqm": 2.8,
						"supply_source": "Company Warehouse",
					}
				],
				price_list=self.price_list,
			)
		self.assertEqual(invoice.items[0].qty, 2)
		self.assertEqual(invoice.items[0].custom_supply_source, "Company Warehouse")

	def test_create_sales_invoice_rejects_invalid_supply_source(self):
		with frappe.set_user(self.user), self.assertRaises(frappe.ValidationError):
			sales_service.create_sales_invoice(
				customer=self.customer,
				showroom=self.branch,
				items=[{"item_code": self.item, "required_area_sqm": 2.8, "supply_source": "Warehouse Down The Street"}],
				price_list=self.price_list,
			)

	def test_submit_blocked_without_supplier_confirmation(self):
		with frappe.set_user(self.user):
			invoice = sales_service.create_sales_invoice(
				customer=self.customer,
				showroom=self.branch,
				items=[{"item_code": self.item, "required_area_sqm": 2.8, "supply_source": "Supplier"}],
				price_list=self.price_list,
			)
			with self.assertRaises(frappe.ValidationError):
				invoice.submit()

	def test_submit_allowed_after_confirmed_availability(self):
		with frappe.set_user(self.user):
			availability_confirmation_service.record_confirmation(
				supplier=self.supplier,
				showroom=self.branch,
				contact_person="Test Contact",
				phone_number="+10000000000",
				status="Confirmed",
				item=self.item,
			)
			invoice = sales_service.create_sales_invoice(
				customer=self.customer,
				showroom=self.branch,
				items=[{"item_code": self.item, "required_area_sqm": 2.8, "supply_source": "Supplier"}],
				price_list=self.price_list,
			)
			invoice.submit()
		self.assertEqual(invoice.docstatus, 1)
