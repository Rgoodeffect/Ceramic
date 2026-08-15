import frappe
from frappe.tests.utils import FrappeTestCase

from retail_suite.dashboards import number_cards


class TestNumberCards(FrappeTestCase):
	def test_pending_deliveries_returns_value_dict(self):
		result = number_cards.pending_deliveries()
		self.assertIn("value", result)
		self.assertIsInstance(result["value"], (int, float))

	def test_todays_sales_returns_value_dict(self):
		result = number_cards.todays_sales()
		self.assertIn("value", result)

	def test_restricted_user_only_sees_own_showroom_sales(self):
		branch = "_Test Number Card Showroom"
		if not frappe.db.exists("Branch", branch):
			frappe.get_doc({"doctype": "Branch", "branch": branch}).insert(ignore_permissions=True)

		user = "retail-suite-test-number-card@example.com"
		if not frappe.db.exists("User", user):
			new_user = frappe.get_doc(
				{"doctype": "User", "email": user, "first_name": "Number Card Test", "send_welcome_email": 0}
			)
			new_user.insert(ignore_permissions=True)
			# Without a role, this user has no read permission on Sales
			# Invoice at all, so todays_sales() would fail with a plain
			# PermissionError before ever reaching the showroom-scoping logic
			# this test is actually meant to exercise.
			new_user.add_roles("Retail Salesperson")
		if not frappe.db.exists("User Permission", {"user": user, "allow": "Branch", "for_value": branch}):
			frappe.get_doc(
				{"doctype": "User Permission", "user": user, "allow": "Branch", "for_value": branch}
			).insert(ignore_permissions=True)

		# A restricted user with no invoices in their showroom should see 0,
		# never another showroom's totals, even if other showrooms have sales.
		with self.set_user(user):
			result = number_cards.todays_sales()
		self.assertEqual(result["value"], 0)
