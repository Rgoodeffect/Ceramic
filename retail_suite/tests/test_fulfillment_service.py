import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import flt

from retail_suite.services import availability_confirmation_service, fulfillment_service, sales_service
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

	def test_partial_payment_leaves_the_rest_outstanding(self):
		"""The customer pays part of the invoice at the counter and owes the
		rest - the invoice stays open for exactly the unpaid remainder."""
		invoice = self._submitted_invoice()
		total = flt(invoice.rounded_total or invoice.grand_total, invoice.precision("outstanding_amount"))
		with self.set_user(self.user):
			payment = fulfillment_service.create_payment_entry(invoice.name, paid_amount=total / 4)
		self.assertEqual(payment.docstatus, 1)
		self.assertEqual(flt(payment.paid_amount), flt(total / 4))
		invoice.reload()
		self.assertEqual(flt(invoice.outstanding_amount), flt(total - total / 4))
		self.assertEqual(invoice.status, "Partly Paid")

	def test_a_later_payment_settles_the_remaining_debt(self):
		"""Debt is paid off on a later visit, against the same invoice."""
		invoice = self._submitted_invoice()
		total = flt(invoice.rounded_total or invoice.grand_total, invoice.precision("outstanding_amount"))
		with self.set_user(self.user):
			fulfillment_service.create_payment_entry(invoice.name, paid_amount=total / 4)
			invoice.reload()
			fulfillment_service.create_payment_entry(invoice.name, paid_amount=invoice.outstanding_amount)
		invoice.reload()
		self.assertEqual(flt(invoice.outstanding_amount), 0)

	def test_rejects_a_payment_larger_than_the_outstanding_amount(self):
		invoice = self._submitted_invoice()
		with self.set_user(self.user), self.assertRaises(frappe.ValidationError):
			fulfillment_service.create_payment_entry(
				invoice.name, paid_amount=flt(invoice.outstanding_amount) + 1
			)

	def test_rejects_a_zero_or_negative_payment(self):
		"""Paying nothing is not a payment - the sale is simply left unpaid,
		with the whole invoice standing as the customer's debt."""
		invoice = self._submitted_invoice()
		with self.set_user(self.user):
			for amount in (0, -5):
				with self.assertRaises(frappe.ValidationError):
					fulfillment_service.create_payment_entry(invoice.name, paid_amount=amount)

	def test_get_payment_status_reports_what_was_paid_and_what_is_owed(self):
		"""Sales Invoice.paid_amount stays 0 on a non-POS invoice however much
		is received against it, so the status is derived from what is still
		outstanding - see fulfillment_service.get_payment_status."""
		invoice = self._submitted_invoice()
		with self.set_user(self.user):
			before = fulfillment_service.get_payment_status(invoice.name)
			self.assertEqual(before["paid_amount"], 0)
			self.assertEqual(before["outstanding_amount"], before["grand_total"])

			fulfillment_service.create_payment_entry(invoice.name, paid_amount=before["grand_total"] / 4)
			after = fulfillment_service.get_payment_status(invoice.name)

		self.assertEqual(after["paid_amount"], flt(before["grand_total"] / 4, 2))
		self.assertEqual(
			flt(after["paid_amount"] + after["outstanding_amount"], 2), flt(after["grand_total"], 2)
		)
		self.assertGreaterEqual(after["customer_outstanding"], after["outstanding_amount"])

	def _submitted_supplier_invoice(self):
		"""A submitted invoice with one Supplier-sourced line, confirmed
		availability already recorded - shared by the delivery-note and
		supplier-delivery tests below."""
		item = test_utils.ensure_item("_Test FS Supplier Item", area_per_box=1.5)
		price_list = test_utils.ensure_price(item, "_Test FS Supplier Price List", rate=50)
		supplier = test_utils.ensure_supplier("_Test FS Supplier")
		with self.set_user(self.user):
			availability_confirmation_service.record_confirmation(
				supplier=supplier,
				showroom=self.branch,
				contact_person="Test Contact",
				phone_number="+10000000000",
				status="Confirmed",
				item=item,
			)
			invoice = sales_service.create_sales_invoice(
				customer=self.customer,
				showroom=self.branch,
				items=[
					{
						"item_code": item,
						"required_area_sqm": 2.8,
						"supply_source": "Supplier",
						"supplier": supplier,
					}
				],
				price_list=price_list,
			)
			invoice = sales_service.submit_sales_invoice(invoice.name)
		return invoice

	def test_create_delivery_note_rejects_when_no_warehouse_items(self):
		invoice = self._submitted_supplier_invoice()
		with self.set_user(self.user), self.assertRaises(frappe.ValidationError):
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

	def test_create_supplier_delivery_submits_order_against_confirmation(self):
		invoice = self._submitted_supplier_invoice()
		with self.set_user(self.user):
			orders = fulfillment_service.create_supplier_deliveries(invoice.name)
		self.assertEqual(len(orders), 1)
		order = orders[0]
		self.assertEqual(order.docstatus, 1)
		self.assertEqual(order.sales_invoice, invoice.name)
		self.assertEqual(order.showroom, self.branch)
		self.assertTrue(
			frappe.db.get_value(
				"Supplier Availability Confirmation", order.supplier_availability_confirmation, "status"
			)
			== "Confirmed"
		)

	def test_creates_one_order_per_supplier_carrying_only_that_suppliers_items(self):
		"""One invoice, items from two different suppliers: each supplier gets
		its own order listing only its own goods, so neither is handed a
		printout telling it to deliver the other's items."""
		item_a = test_utils.ensure_item("_Test FS Multi Item A", area_per_box=1.5)
		item_b = test_utils.ensure_item("_Test FS Multi Item B", area_per_box=2.0)
		price_list = test_utils.ensure_price(item_a, "_Test FS Multi Price List", rate=50)
		test_utils.ensure_price(item_b, price_list, rate=60)
		supplier_a = test_utils.ensure_supplier("_Test FS Multi Supplier A")
		supplier_b = test_utils.ensure_supplier("_Test FS Multi Supplier B")

		with self.set_user(self.user):
			invoice = sales_service.create_sales_invoice(
				customer=self.customer,
				showroom=self.branch,
				items=[
					{
						"item_code": item_a,
						"required_area_sqm": 3.0,
						"supply_source": "Supplier",
						"supplier": supplier_a,
					},
					{
						"item_code": item_b,
						"required_area_sqm": 4.0,
						"supply_source": "Supplier",
						"supplier": supplier_b,
					},
				],
				price_list=price_list,
			)
			invoice = sales_service.submit_sales_invoice(invoice.name)
			orders = fulfillment_service.create_supplier_deliveries(invoice.name)

		self.assertEqual(len(orders), 2)
		# Ordered by where each supplier first appears on the invoice, so the
		# printouts come out in the order the lines were entered.
		self.assertEqual([order.supplier for order in orders], [supplier_a, supplier_b])
		self.assertEqual([row.item_code for row in orders[0].items], [item_a])
		self.assertEqual([row.item_code for row in orders[1].items], [item_b])
		for order in orders:
			self.assertEqual(order.docstatus, 1)
			self.assertEqual(order.sales_invoice, invoice.name)

	def test_groups_several_items_from_the_same_supplier_onto_one_order(self):
		"""Two lines, one supplier - one order carrying both, not two orders."""
		item_a = test_utils.ensure_item("_Test FS Same Item A", area_per_box=1.5)
		item_b = test_utils.ensure_item("_Test FS Same Item B", area_per_box=2.0)
		price_list = test_utils.ensure_price(item_a, "_Test FS Same Price List", rate=50)
		test_utils.ensure_price(item_b, price_list, rate=60)
		supplier = test_utils.ensure_supplier("_Test FS Same Supplier")

		with self.set_user(self.user):
			invoice = sales_service.create_sales_invoice(
				customer=self.customer,
				showroom=self.branch,
				items=[
					{
						"item_code": item_a,
						"required_area_sqm": 3.0,
						"supply_source": "Supplier",
						"supplier": supplier,
					},
					{
						"item_code": item_b,
						"required_area_sqm": 4.0,
						"supply_source": "Supplier",
						"supplier": supplier,
					},
				],
				price_list=price_list,
			)
			invoice = sales_service.submit_sales_invoice(invoice.name)
			orders = fulfillment_service.create_supplier_deliveries(invoice.name)

		self.assertEqual(len(orders), 1)
		self.assertEqual(sorted(row.item_code for row in orders[0].items), sorted([item_a, item_b]))

	def test_create_supplier_delivery_rejects_when_no_supplier_items(self):
		invoice = self._submitted_invoice()
		with self.set_user(self.user), self.assertRaises(frappe.ValidationError):
			fulfillment_service.create_supplier_deliveries(invoice.name)

	def test_create_supplier_delivery_rejects_draft_invoice(self):
		with self.set_user(self.user):
			invoice = sales_service.create_sales_invoice(
				customer=self.customer,
				showroom=self.branch,
				items=[{"item_code": self.item, "required_area_sqm": 2.8, "supply_source": "Company Warehouse"}],
				price_list=self.price_list,
			)
			with self.assertRaises(frappe.ValidationError):
				fulfillment_service.create_supplier_deliveries(invoice.name)
