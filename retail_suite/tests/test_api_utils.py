import frappe
from frappe.tests.utils import FrappeTestCase

from retail_suite.api.utils import api_endpoint


class TestApiUtils(FrappeTestCase):
	def test_successful_call_is_wrapped(self):
		@api_endpoint
		def ok():
			return {"answer": 42}

		result = ok()
		self.assertEqual(
			result, {"success": True, "message": "", "data": {"answer": 42}, "errors": []}
		)

	def test_validation_error_becomes_failure_envelope(self):
		@api_endpoint
		def bad():
			frappe.throw("Required area must be greater than zero.")

		result = bad()
		self.assertFalse(result["success"])
		self.assertIn("Required area must be greater than zero.", result["message"])
		self.assertIsNone(result["data"])

	def test_permission_error_becomes_failure_envelope(self):
		@api_endpoint
		def forbidden():
			frappe.throw("You do not have access to showroom AS.", frappe.PermissionError)

		result = forbidden()
		self.assertFalse(result["success"])
		self.assertIn("You do not have access to showroom AS.", result["message"])

	def test_unexpected_exception_does_not_leak_internals(self):
		@api_endpoint
		def boom():
			raise KeyError("some_internal_dict_key")

		result = boom()
		self.assertFalse(result["success"])
		self.assertNotIn("some_internal_dict_key", result["message"])
