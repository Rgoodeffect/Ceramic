import frappe
from frappe.tests.utils import FrappeTestCase

from retail_suite.retail_suite_core.permissions import permission_service as perm


class TestPermissionService(FrappeTestCase):
	def setUp(self):
		self.branch_vf = self._ensure_branch("_Test Showroom VF")
		self.branch_as = self._ensure_branch("_Test Showroom AS")
		self.user = self._ensure_user("retail-suite-test-salesperson@example.com")
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
				{
					"doctype": "User",
					"email": email,
					"first_name": "Retail Suite Test Salesperson",
					"send_welcome_email": 0,
				}
			).insert(ignore_permissions=True)
		return email

	def test_administrator_is_unrestricted(self):
		self.assertTrue(perm.is_unrestricted("Administrator"))

	def test_restricted_user_sees_only_assigned_showroom(self):
		self.assertFalse(perm.is_unrestricted(self.user))
		self.assertEqual(perm.get_user_showrooms(self.user), [self.branch_vf])

	def test_assert_showroom_access_allows_own_showroom(self):
		perm.assert_showroom_access(self.branch_vf, self.user)

	def test_assert_showroom_access_blocks_other_showroom(self):
		with self.assertRaises(frappe.PermissionError):
			perm.assert_showroom_access(self.branch_as, self.user)

	def test_company_owner_role_is_unrestricted_even_with_no_user_permission(self):
		owner = self._ensure_user("retail-suite-test-owner@example.com")
		frappe.get_doc(
			{"doctype": "Has Role", "parent": owner, "parenttype": "User", "parentfield": "roles", "role": "Retail Company Owner"}
		).insert(ignore_permissions=True)
		self.assertTrue(perm.is_unrestricted(owner))

	def test_query_condition_scopes_to_users_showroom(self):
		condition = perm._query_condition_for("Quotation", self.user)
		self.assertIn("tabQuotation", condition)
		self.assertIn(self.branch_vf, condition)
		self.assertNotIn(self.branch_as, condition)

	def test_query_condition_empty_for_unrestricted_user(self):
		self.assertEqual(perm._query_condition_for("Quotation", "Administrator"), "")
