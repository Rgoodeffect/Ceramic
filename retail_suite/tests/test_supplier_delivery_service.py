import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, today

from retail_suite.services import availability_confirmation_service, sales_service, supplier_delivery_service
from retail_suite.tests import test_utils


class TestSupplierDeliveryService(FrappeTestCase):
	def setUp(self):
		self.branch = test_utils.ensure_branch("_Test SDS Showroom")
		self.user = test_utils.ensure_user(
			"retail-suite-test-sds-user@example.com", role="Retail Salesperson", showroom=self.branch
		)
		self.item = test_utils.ensure_item("_Test SDS Item", area_per_box=1.5)
		self.price_list = test_utils.ensure_price(self.item, "_Test SDS Price List", rate=50)
		self.customer = test_utils.ensure_customer("_Test SDS Customer")
		self.supplier = test_utils.ensure_supplier("_Test SDS Supplier")

	def _submitted_invoice_and_confirmation(self):
		with self.set_user(self.user):
			confirmation = availability_confirmation_service.record_confirmation(
				supplier=self.supplier,
				showroom=self.branch,
				contact_person="Contact",
				phone_number="+10000000000",
				status="Confirmed",
				item=self.item,
			)
			invoice = sales_service.create_sales_invoice(
				customer=self.customer,
				showroom=self.branch,
				items=[
					{
						"item_code": self.item,
						"required_area_sqm": 2.8,
						"supply_source": "Supplier",
						"supplier": self.supplier,
					}
				],
				price_list=self.price_list,
			)
			invoice.submit()
		return invoice, confirmation

	def test_create_from_sales_invoice(self):
		invoice, confirmation = self._submitted_invoice_and_confirmation()
		with self.set_user(self.user):
			order = supplier_delivery_service.create_from_sales_invoice(
				sales_invoice_name=invoice.name,
				supplier_availability_confirmation_name=confirmation.name,
				delivery_date=add_days(today(), 2),
			)
		self.assertEqual(order.supplier, self.supplier)
		self.assertEqual(order.showroom, self.branch)
		self.assertEqual(order.items[0].boxes_qty, 2)

	def test_only_the_named_suppliers_items_go_on_its_order(self):
		"""An invoice can carry lines from several suppliers. Each order must
		list only the lines belonging to the supplier it is raised for -
		otherwise a supplier is handed a document telling it to deliver
		another supplier's goods."""
		other_item = test_utils.ensure_item("_Test SDS Other Item", area_per_box=2.0)
		test_utils.ensure_price(other_item, self.price_list, rate=60)
		other_supplier = test_utils.ensure_supplier("_Test SDS Other Supplier")

		with self.set_user(self.user):
			invoice = sales_service.create_sales_invoice(
				customer=self.customer,
				showroom=self.branch,
				items=[
					{
						"item_code": self.item,
						"required_area_sqm": 2.8,
						"supply_source": "Supplier",
						"supplier": self.supplier,
					},
					{
						"item_code": other_item,
						"required_area_sqm": 4.0,
						"supply_source": "Supplier",
						"supplier": other_supplier,
					},
				],
				price_list=self.price_list,
			)
			invoice.submit()
			order = supplier_delivery_service.create_from_sales_invoice(
				sales_invoice_name=invoice.name,
				supplier=other_supplier,
				delivery_date=add_days(today(), 2),
			)

		self.assertEqual(order.supplier, other_supplier)
		self.assertEqual([row.item_code for row in order.items], [other_item])

	def test_rejects_a_supplier_with_no_items_on_the_invoice(self):
		invoice, _confirmation = self._submitted_invoice_and_confirmation()
		unrelated = test_utils.ensure_supplier("_Test SDS Unrelated Supplier")
		with self.set_user(self.user), self.assertRaises(frappe.ValidationError):
			supplier_delivery_service.create_from_sales_invoice(
				sales_invoice_name=invoice.name,
				supplier=unrelated,
				delivery_date=add_days(today(), 2),
			)

	def test_order_item_never_carries_price_fields(self):
		meta = frappe.get_meta("Supplier Delivery Order Item")
		fieldnames = {df.fieldname for df in meta.fields}
		self.assertTrue(fieldnames.isdisjoint({"rate", "amount", "price_list_rate"}))

	def test_rejects_a_confirmation_that_is_not_confirmed(self):
		"""The Sales Invoice's own before_submit gate needs *a* Confirmed
		confirmation to exist for the item/showroom, but create_from_sales_invoice
		must independently validate whatever specific confirmation it is
		handed - a second, still-Pending confirmation for the same item must
		not be accepted just because submission itself succeeded."""
		invoice, _confirmed = self._submitted_invoice_and_confirmation()
		with self.set_user(self.user):
			pending = availability_confirmation_service.record_confirmation(
				supplier=self.supplier,
				showroom=self.branch,
				contact_person="Contact",
				phone_number="+10000000000",
				status="Pending",
				item=self.item,
			)
			with self.assertRaises(frappe.ValidationError):
				supplier_delivery_service.create_from_sales_invoice(
					sales_invoice_name=invoice.name,
					supplier_availability_confirmation_name=pending.name,
					delivery_date=add_days(today(), 2),
				)
