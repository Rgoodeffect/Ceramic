import frappe
from frappe.tests.utils import FrappeTestCase

from retail_suite.api.session import get_session_context


class TestSessionApi(FrappeTestCase):
	def setUp(self):
		self.branch = "_Test Session Api Showroom"
		if not frappe.db.exists("Branch", self.branch):
			frappe.get_doc({"doctype": "Branch", "branch": self.branch}).insert(ignore_permissions=True)

		self.user = "retail-suite-test-session-api@example.com"
		if not frappe.db.exists("User", self.user):
			frappe.get_doc(
				{"doctype": "User", "email": self.user, "first_name": "Session Api Test", "send_welcome_email": 0}
			).insert(ignore_permissions=True)

		if not frappe.db.exists("User Permission", {"user": self.user, "allow": "Branch", "for_value": self.branch}):
			frappe.get_doc(
				{"doctype": "User Permission", "user": self.user, "allow": "Branch", "for_value": self.branch}
			).insert(ignore_permissions=True)

	def test_returns_assigned_showroom_for_restricted_user(self):
		with frappe.set_user(self.user):
			envelope = get_session_context()
		self.assertTrue(envelope["success"])
		self.assertEqual(envelope["data"]["showroom"], self.branch)
		self.assertFalse(envelope["data"]["is_unrestricted"])

	def test_unrestricted_for_administrator(self):
		with frappe.set_user("Administrator"):
			envelope = get_session_context()
		self.assertTrue(envelope["success"])
		self.assertTrue(envelope["data"]["is_unrestricted"])
