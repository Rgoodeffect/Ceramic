from frappe.model.document import Document


class SupplierAvailabilityConfirmation(Document):
	# Business rules (status transitions, linkage checks) live in
	# retail_suite.services.availability_confirmation_service and are wired via hooks.py.
	pass
