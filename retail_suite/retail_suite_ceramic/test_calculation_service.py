import frappe
from frappe.tests.utils import FrappeTestCase

from retail_suite.retail_suite_ceramic import calculation_service as calc


class TestCalculationService(FrappeTestCase):
	"""Spec Part 12 "Ceramic Calculation Test Cases", verbatim."""

	def test_case_1_partial_box_rounds_up(self):
		boxes = calc.calculate_boxes(2.8, 1.5)
		self.assertEqual(boxes, 2)
		self.assertAlmostEqual(calc.calculate_delivered_area(boxes, 1.5), 3.0)

	def test_case_2_non_exact_ratio_rounds_up(self):
		boxes = calc.calculate_boxes(10, 1.2)
		self.assertEqual(boxes, 9)
		self.assertAlmostEqual(calc.calculate_delivered_area(boxes, 1.2), 10.8)

	def test_case_3_exact_multiple_no_extra_box(self):
		boxes = calc.calculate_boxes(3.0, 1.5)
		self.assertEqual(boxes, 2)
		self.assertAlmostEqual(calc.calculate_delivered_area(boxes, 1.5), 3.0)

	def test_case_4_zero_area_is_rejected(self):
		with self.assertRaises(frappe.ValidationError):
			calc.calculate_boxes(0, 1.5)

	def test_case_5_negative_area_is_rejected(self):
		with self.assertRaises(frappe.ValidationError):
			calc.calculate_boxes(-1, 1.5)

	def test_zero_area_per_box_is_rejected(self):
		with self.assertRaises(frappe.ValidationError):
			calc.calculate_boxes(2.8, 0)

	def test_calculate_row_end_to_end(self):
		item_code = self._make_test_item(area_per_box=1.5)
		price_list = self._make_price_list_with_sqm_rate(item_code, rate=50)

		result = calc.calculate_row(item_code, 2.8, price_list)

		self.assertEqual(result["boxes"], 2)
		self.assertAlmostEqual(result["delivered_area_sqm"], 3.0)
		self.assertAlmostEqual(result["price_per_sqm"], 50)
		self.assertAlmostEqual(result["rate_per_box"], 75)  # 50 * 1.5
		self.assertAlmostEqual(result["amount"], 150)  # 2 boxes * 75

	def test_validate_item_rows_matches_direct_calculate_row(self):
		"""Manual Desk entry (validate_item_rows) and the POS API
		(calculate_row / apply_to_item_row) must produce identical numbers -
		this is the whole point of having a single Calculation Engine."""
		item_code = self._make_test_item(area_per_box=1.5)
		price_list = self._make_price_list_with_sqm_rate(item_code, rate=50)
		expected = calc.calculate_row(item_code, 2.8, price_list)

		quotation = frappe.new_doc("Quotation")
		quotation.selling_price_list = price_list
		row = quotation.append("items", {})
		row.item_code = item_code
		row.custom_required_area_sqm = 2.8

		calc.validate_item_rows(quotation)

		self.assertEqual(row.qty, expected["boxes"])
		self.assertEqual(row.uom, "Box")
		self.assertAlmostEqual(row.rate, expected["rate_per_box"])
		self.assertAlmostEqual(row.custom_delivered_area_sqm, expected["delivered_area_sqm"])

	def test_validate_item_rows_skips_non_ceramic_items(self):
		"""An item with no Area Per Box configured is left completely alone."""
		non_ceramic_item = "_Test Retail Suite Non Ceramic Item"
		if not frappe.db.exists("Item", non_ceramic_item):
			frappe.get_doc(
				{
					"doctype": "Item",
					"item_code": non_ceramic_item,
					"item_name": non_ceramic_item,
					"item_group": "All Item Groups",
					"stock_uom": "Nos",
				}
			).insert(ignore_permissions=True)

		quotation = frappe.new_doc("Quotation")
		row = quotation.append("items", {})
		row.item_code = non_ceramic_item
		row.qty = 5
		row.rate = 20

		calc.validate_item_rows(quotation)

		self.assertEqual(row.qty, 5)
		self.assertEqual(row.rate, 20)

	def _make_test_item(self, area_per_box: float) -> str:
		item_code = "_Test Retail Suite Ceramic Item"
		if not frappe.db.exists("Item", item_code):
			frappe.get_doc(
				{
					"doctype": "Item",
					"item_code": item_code,
					"item_name": item_code,
					"item_group": "All Item Groups",
					"stock_uom": "Box",
					"custom_area_per_box": area_per_box,
				}
			).insert(ignore_permissions=True)
		else:
			frappe.db.set_value("Item", item_code, "custom_area_per_box", area_per_box)
		return item_code

	def _make_price_list_with_sqm_rate(self, item_code: str, rate: float) -> str:
		price_list = "_Test Retail Suite Price List"
		if not frappe.db.exists("Price List", price_list):
			frappe.get_doc(
				{
					"doctype": "Price List",
					"price_list_name": price_list,
					"selling": 1,
					"currency": frappe.db.get_default("currency") or "USD",
				}
			).insert(ignore_permissions=True)
		existing = frappe.db.exists(
			"Item Price", {"item_code": item_code, "price_list": price_list, "uom": "Sq Meter"}
		)
		if existing:
			frappe.db.set_value("Item Price", existing, "price_list_rate", rate)
		else:
			frappe.get_doc(
				{
					"doctype": "Item Price",
					"item_code": item_code,
					"price_list": price_list,
					"uom": "Sq Meter",
					"selling": 1,
					"price_list_rate": rate,
				}
			).insert(ignore_permissions=True)
		return price_list
