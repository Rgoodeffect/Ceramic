import frappe
from frappe.model.document import Document


class RetailSuiteSettings(Document):
	pass


def get_default_company() -> str | None:
	"""Company to stamp on every Quotation/Sales Invoice the service layer creates.

	ERPNext's own controllers (`get_item_details`, party-account resolution)
	require `company` before `validate()` even reaches our showroom hooks -
	on a normal Desk form this is filled in client-side from
	`frappe.defaults.get_user_default("company")`, which never runs when a
	document is created server-side through the service layer (spec Part 6:
	business logic belongs in Python services, not client scripts). Found by
	actually creating a Quotation through `quotation_service` on a real site:
	every one failed validate() with "Please specify Company" because
	nothing had ever set it.
	"""
	return frappe.db.get_single_value("Retail Suite Settings", "default_company")
