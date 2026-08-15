from frappe.model.document import Document


class SupplierDeliveryOrder(Document):
	# Business rules (confirmation-required check, no-price enforcement) live in
	# retail_suite.services.supplier_delivery_service and are wired via hooks.py.
	pass
