"""Integration test for the full business workflow (spec Part 5/12):
Quotation -> Sales Invoice -> Supplier Delivery Order, and the final
business/security validations from spec Part 13/14 stated as assertions.
"""

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, today

from retail_suite.services import (
	availability_confirmation_service,
	quotation_service,
	sales_service,
	supplier_delivery_service,
)
from retail_suite.tests import test_utils


class TestWorkflowIntegration(FrappeTestCase):
	def setUp(self):
		self.branch_vf = test_utils.ensure_branch("_Test Workflow Showroom VF")
		self.branch_as = test_utils.ensure_branch("_Test Workflow Showroom AS")
		self.salesperson = test_utils.ensure_user(
			"retail-suite-test-workflow-salesperson@example.com",
			role="Retail Salesperson",
			showroom=self.branch_vf,
		)
		self.other_salesperson = test_utils.ensure_user(
			"retail-suite-test-workflow-other@example.com",
			role="Retail Salesperson",
			showroom=self.branch_as,
		)
		self.owner = test_utils.ensure_user(
			"retail-suite-test-workflow-owner@example.com", role="Retail Company Owner"
		)
		self.item = test_utils.ensure_item("_Test Workflow Item", area_per_box=1.5)
		self.price_list = test_utils.ensure_price(self.item, "_Test Workflow Price List", rate=50)
		self.customer = test_utils.ensure_customer("_Test Workflow Customer")
		self.supplier = test_utils.ensure_supplier("_Test Workflow Supplier")

	def test_full_quotation_to_supplier_delivery_workflow(self):
		with self.set_user(self.salesperson):
			# Customer requires 2.8 m2 -> spec's own worked example (Part 6/13).
			quotation = quotation_service.create_quotation(
				customer=self.customer,
				showroom=self.branch_vf,
				items=[{"item_code": self.item, "required_area_sqm": 2.8}],
				price_list=self.price_list,
			)
			quotation.submit()

			availability_confirmation_service.record_confirmation(
				supplier=self.supplier,
				showroom=self.branch_vf,
				contact_person="Contact",
				phone_number="+10000000000",
				status="Confirmed",
				item=self.item,
			)

			invoice = sales_service.create_sales_invoice_from_quotation(
				quotation.name, {self.item: "Supplier"}
			)
			invoice.submit()

			confirmation = frappe.get_last_doc(
				"Supplier Availability Confirmation", filters={"item": self.item, "showroom": self.branch_vf}
			)
			delivery_order = supplier_delivery_service.create_from_sales_invoice(
				sales_invoice_name=invoice.name,
				supplier_availability_confirmation_name=confirmation.name,
				delivery_date=add_days(today(), 3),
			)

		# --- Final Business Validation (spec Part 13/14) ---
		row = invoice.items[0]
		self.assertEqual(row.qty, 2)  # 2 boxes
		self.assertAlmostEqual(row.custom_delivered_area_sqm, 3.0)  # delivered 3.0 m2
		self.assertAlmostEqual(invoice.grand_total, 150.0)  # 3.0 m2 x 50/m2
		self.assertEqual(delivery_order.items[0].boxes_qty, 2)

		# Documents stay linked (spec Part 5: "Document Relationship").
		self.assertEqual(delivery_order.sales_invoice, invoice.name)
		self.assertEqual(delivery_order.supplier_availability_confirmation, confirmation.name)

		# --- Final Security Validation (spec Part 13/14): showroom isolation ---
		with self.set_user(self.other_salesperson):
			self.assertFalse(frappe.has_permission("Sales Invoice", doc=invoice.name))
			self.assertFalse(frappe.has_permission("Supplier Delivery Order", doc=delivery_order.name))

		# Company Owner sees everything, regardless of showroom.
		with self.set_user(self.owner):
			self.assertTrue(frappe.has_permission("Sales Invoice", doc=invoice.name))
			self.assertTrue(frappe.has_permission("Supplier Delivery Order", doc=delivery_order.name))
