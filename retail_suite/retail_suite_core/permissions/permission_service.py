"""Showroom-isolation permission backstop.

Design (see documentation/architecture/PLAN.md §1.3-2): showroom scoping is
primarily enforced by a standard ERPNext `User Permission` row
(allow="Branch", for_value=<user's showroom>) on every operational user,
which Frappe's core permission engine already uses to auto-filter list
views, reports, search, and Link fields for any field linking to `Branch`.

This module exists as the explicit, testable, server-side backstop the spec
requires ("never rely only on hiding buttons... validate server-side"):
it is registered as `permission_query_conditions` / `has_permission` in
hooks.py for defense-in-depth, and its `assert_showroom_access` /
`get_user_showroom` functions are the ones the service layer (Phase 4) and
API layer (Phase 6) must call to validate a showroom explicitly, rather than
trusting a showroom value supplied by the client.
"""

from __future__ import annotations

import frappe

UNRESTRICTED_ROLES = {"System Manager", "Retail Company Owner"}

# Doctype -> fieldname holding the Branch (showroom) link on that doctype.
SHOWROOM_FIELD_BY_DOCTYPE = {
	"Quotation": "custom_showroom",
	"Sales Invoice": "custom_showroom",
	"Delivery Note": "custom_showroom",
	"Purchase Invoice": "custom_showroom",
	"Payment Entry": "custom_showroom",
	"Supplier Delivery Order": "showroom",
	"Supplier Availability Confirmation": "showroom",
}


def is_unrestricted(user: str | None = None) -> bool:
	"""True if the user is not confined to a single showroom.

	This is the case for System Manager / Retail Company Owner, and for any
	user who has no `User Permission` row restricting them to a Branch
	(the onboarding convention for those two roles, per PLAN.md §1.3-2).
	"""
	user = user or frappe.session.user
	if user == "Administrator":
		return True
	user_roles = set(frappe.get_roles(user))
	if user_roles & UNRESTRICTED_ROLES:
		return True
	return not bool(get_user_showrooms(user))


def get_user_showrooms(user: str | None = None) -> list[str]:
	"""Branches this user is restricted to via User Permission (empty = unrestricted)."""
	user = user or frappe.session.user
	return frappe.get_all(
		"User Permission",
		filters={"user": user, "allow": "Branch"},
		pluck="for_value",
	)


def get_user_showroom(user: str | None = None) -> str | None:
	"""Convenience accessor for the common single-showroom-per-user case."""
	showrooms = get_user_showrooms(user)
	return showrooms[0] if showrooms else None


def assert_showroom_access(showroom: str, user: str | None = None) -> None:
	"""Raise frappe.PermissionError if `user` may not act on `showroom`.

	Call this explicitly in service/API methods before creating or acting on
	a document for a given showroom — never trust a showroom value supplied
	by the client without this check.
	"""
	user = user or frappe.session.user
	if is_unrestricted(user):
		return
	if showroom not in get_user_showrooms(user):
		frappe.throw(
			frappe._("You do not have access to showroom {0}.").format(showroom),
			frappe.PermissionError,
		)


def _query_condition_for(doctype: str, user: str) -> str:
	if is_unrestricted(user):
		return ""
	showrooms = get_user_showrooms(user)
	if not showrooms:
		# Unrestricted-but-no-role-match should not happen for onboarded
		# users; fail closed rather than leaking cross-showroom data.
		return "1=0"
	fieldname = SHOWROOM_FIELD_BY_DOCTYPE[doctype]
	quoted = ", ".join(frappe.db.escape(showroom) for showroom in showrooms)
	return f"`tab{doctype}`.`{fieldname}` in ({quoted})"


# hooks.py registers permission_query_conditions per doctype as a dotted
# path to a callable(user) -> str, so each showroom-scoped doctype needs its
# own module-level function (the hook is never told which doctype it's
# filtering, only the doc controller call site knows that).
def get_permission_query_conditions_quotation(user: str) -> str:
	return _query_condition_for("Quotation", user)


def get_permission_query_conditions_sales_invoice(user: str) -> str:
	return _query_condition_for("Sales Invoice", user)


def get_permission_query_conditions_delivery_note(user: str) -> str:
	return _query_condition_for("Delivery Note", user)


def get_permission_query_conditions_purchase_invoice(user: str) -> str:
	return _query_condition_for("Purchase Invoice", user)


def get_permission_query_conditions_payment_entry(user: str) -> str:
	return _query_condition_for("Payment Entry", user)


def get_permission_query_conditions_supplier_delivery_order(user: str) -> str:
	return _query_condition_for("Supplier Delivery Order", user)


def get_permission_query_conditions_supplier_availability_confirmation(user: str) -> str:
	return _query_condition_for("Supplier Availability Confirmation", user)


def has_permission(doc, ptype: str | None = None, user: str | None = None, **kwargs) -> bool:
	"""Shared hooks.py `has_permission` target for every showroom-scoped doctype.

	Unlike permission_query_conditions, has_permission receives the full
	document, so doctype is available on `doc` itself and one function can
	serve all of them.
	"""
	user = user or frappe.session.user
	if is_unrestricted(user):
		return True
	fieldname = SHOWROOM_FIELD_BY_DOCTYPE.get(doc.doctype)
	if not fieldname:
		return True
	return doc.get(fieldname) in get_user_showrooms(user)
