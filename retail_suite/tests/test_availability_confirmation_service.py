import frappe
from frappe.tests.utils import FrappeTestCase

from retail_suite.services import availability_confirmation_service
from retail_suite.tests import test_utils


class TestAvailabilityConfirmationService(FrappeTestCase):
	def setUp(self):
		self.branch = test_utils.ensure_branch("_Test ACS Showroom")
		self.user = test_utils.ensure_user(
			"retail-suite-test-acs-user@example.com", role="Retail Salesperson", showroom=self.branch
		)
		self.supplier = test_utils.ensure_supplier("_Test ACS Supplier")

	def test_record_confirmation_submits_by_default(self):
		with self.set_user(self.user):
			confirmation = availability_confirmation_service.record_confirmation(
				supplier=self.supplier,
				showroom=self.branch,
				contact_person="Contact",
				phone_number="+10000000000",
				status="Confirmed",
			)
		self.assertEqual(confirmation.docstatus, 1)
		self.assertEqual(confirmation.confirmed_by, self.user)

	def test_record_confirmation_rejects_invalid_status(self):
		with self.set_user(self.user), self.assertRaises(frappe.ValidationError):
			availability_confirmation_service.record_confirmation(
				supplier=self.supplier,
				showroom=self.branch,
				contact_person="Contact",
				phone_number="+10000000000",
				status="Maybe",
			)

	def test_record_confirmation_can_stay_draft(self):
		with self.set_user(self.user):
			confirmation = availability_confirmation_service.record_confirmation(
				supplier=self.supplier,
				showroom=self.branch,
				contact_person="Contact",
				phone_number="+10000000000",
				status="Pending",
				submit=False,
			)
		self.assertEqual(confirmation.docstatus, 0)
