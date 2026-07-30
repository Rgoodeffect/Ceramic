import frappe
from frappe.tests.utils import FrappeTestCase

from retail_suite.services import quotation_service
from retail_suite.tests import test_utils


class TestQuotationService(FrappeTestCase):
	def setUp(self):
		self.branch = test_utils.ensure_branch("_Test QS Showroom")
		self.other_branch = test_utils.ensure_branch("_Test QS Other Showroom")
		self.user = test_utils.ensure_user(
			"retail-suite-test-qs-user@example.com", role="Retail Salesperson", showroom=self.branch
		)
		self.item = test_utils.ensure_item("_Test QS Item", area_per_box=1.5)
		self.price_list = test_utils.ensure_price(self.item, "_Test QS Price List", rate=50)
		self.customer = test_utils.ensure_customer("_Test QS Customer")

	def test_create_quotation_computes_items_via_calculation_engine(self):
		with self.set_user(self.user):
			quotation = quotation_service.create_quotation(
				customer=self.customer,
				showroom=self.branch,
				items=[{"item_code": self.item, "required_area_sqm": 2.8}],
				price_list=self.price_list,
			)
		row = quotation.items[0]
		self.assertEqual(row.qty, 2)
		self.assertEqual(row.uom, "Box")
		self.assertAlmostEqual(row.custom_delivered_area_sqm, 3.0)
		self.assertAlmostEqual(row.rate, 75.0)
		self.assertEqual(quotation.custom_showroom, self.branch)

	def test_create_quotation_rejects_empty_items(self):
		with self.set_user(self.user), self.assertRaises(frappe.ValidationError):
			quotation_service.create_quotation(
				customer=self.customer, showroom=self.branch, items=[], price_list=self.price_list
			)

	def test_create_quotation_blocks_other_showroom(self):
		with self.set_user(self.user), self.assertRaises(frappe.PermissionError):
			quotation_service.create_quotation(
				customer=self.customer,
				showroom=self.other_branch,
				items=[{"item_code": self.item, "required_area_sqm": 2.8}],
				price_list=self.price_list,
			)
