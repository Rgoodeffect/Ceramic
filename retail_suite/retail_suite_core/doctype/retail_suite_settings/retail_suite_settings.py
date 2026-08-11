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


def is_supplier_confirmation_required() -> bool:
	"""Whether a *Confirmed* Supplier Availability Confirmation is still a hard
	gate on submitting a Sales Invoice / creating its Supplier Delivery Order.

	Off by default: the salesperson picks the supplier directly on the
	Supplier-sourced Sales Invoice Item line (`custom_supplier`) instead of
	waiting on a separate phone-confirmation record. Turn this on (Retail
	Suite Settings) to restore the original spec Part 5 behaviour.
	"""
	return bool(frappe.db.get_single_value("Retail Suite Settings", "require_supplier_confirmation"))
