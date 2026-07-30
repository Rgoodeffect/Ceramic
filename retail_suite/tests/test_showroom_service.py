import frappe
from frappe.tests.utils import FrappeTestCase

from retail_suite.retail_suite_core.showroom import showroom_service


class TestShowroomService(FrappeTestCase):
	def setUp(self):
		self.branch_vf = self._ensure_branch("_Test Showroom Service VF")
		self.branch_as = self._ensure_branch("_Test Showroom Service AS")
		self.user = self._ensure_user("retail-suite-test-showroom-lock@example.com")
		# FrappeTestCase only rolls back once per test *class* (see
		# addClassCleanup(_rollback_db) in frappe.tests.utils), not per test
		# method, so setUp() runs against the same open transaction across
		# every test in this class - this insert must be idempotent like
		# `_ensure_user`/`_ensure_branch` above, or it raises
		# DuplicateEntryError from the second test method onward.
		if not frappe.db.exists(
			"User Permission", {"user": self.user, "allow": "Branch", "for_value": self.branch_vf}
		):
			frappe.get_doc(
				{
					"doctype": "User Permission",
					"user": self.user,
					"allow": "Branch",
					"for_value": self.branch_vf,
				}
			).insert(ignore_permissions=True)

	def _ensure_branch(self, name: str) -> str:
		if not frappe.db.exists("Branch", name):
			frappe.get_doc({"doctype": "Branch", "branch": name}).insert(ignore_permissions=True)
		return name

	def _ensure_user(self, email: str) -> str:
		if not frappe.db.exists("User", email):
			frappe.get_doc(
				{"doctype": "User", "email": email, "first_name": "Showroom Lock Test", "send_welcome_email": 0}
			).insert(ignore_permissions=True)
		return email

	def test_blank_showroom_is_defaulted_for_restricted_user(self):
		quotation = frappe.new_doc("Quotation")
		with self.set_user(self.user):
			showroom_service.apply_showroom_default_and_lock(quotation)
		self.assertEqual(quotation.custom_showroom, self.branch_vf)

	def test_matching_showroom_is_left_alone(self):
		quotation = frappe.new_doc("Quotation")
		quotation.custom_showroom = self.branch_vf
		with self.set_user(self.user):
			showroom_service.apply_showroom_default_and_lock(quotation)
		self.assertEqual(quotation.custom_showroom, self.branch_vf)

	def test_mismatched_showroom_is_blocked(self):
		quotation = frappe.new_doc("Quotation")
		quotation.custom_showroom = self.branch_as
		with self.set_user(self.user), self.assertRaises(frappe.PermissionError):
			showroom_service.apply_showroom_default_and_lock(quotation)

	def test_unrestricted_user_without_default_is_left_blank(self):
		quotation = frappe.new_doc("Quotation")
		with self.set_user("Administrator"):
			showroom_service.apply_showroom_default_and_lock(quotation)
		self.assertFalse(quotation.custom_showroom)
