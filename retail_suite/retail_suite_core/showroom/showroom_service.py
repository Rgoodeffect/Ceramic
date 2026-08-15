"""Cross-cutting showroom defaulting/locking.

Wired via hooks.py `validate` doc_events onto every showroom-scoped doctype
(spec Part 3 "Document Security": "Every business document must contain
Showroom. This field must be automatically populated. The user should not
manually select another showroom.").
"""

from __future__ import annotations

import frappe
from frappe import _

from retail_suite.retail_suite_core.permissions import permission_service

SHOWROOM_FIELD_BY_DOCTYPE = permission_service.SHOWROOM_FIELD_BY_DOCTYPE


def apply_showroom_default_and_lock(doc, method=None) -> None:
	fieldname = SHOWROOM_FIELD_BY_DOCTYPE.get(doc.doctype)
	if not fieldname:
		return

	current = doc.get(fieldname)
	if not current:
		user_showroom = permission_service.get_user_showroom()
		if user_showroom:
			doc.set(fieldname, user_showroom)
		# else: an unrestricted user (Company Owner/System Manager) has no
		# single default showroom and must pick one manually - the field's
		# own `reqd=1` catches it if they forget.
		return

	# A showroom is already set: block a restricted user from picking (or
	# having defaulted, on an amended/duplicated doc) one that isn't theirs.
	permission_service.assert_showroom_access(current)


def require_showroom_before_submit(doc, method=None) -> None:
	"""`before_submit` doc_event body for every showroom-scoped standard doctype.

	custom_showroom is intentionally *not* `reqd=1` at the field level: that
	flag applies unconditionally to every insert of the host doctype
	site-wide, including Frappe/ERPNext's own generic test fixtures (e.g.
	`_T-Quotation-00001`), which know nothing about this app's fields and
	broke outright when the flag was set (found by actually running
	`bench run-tests` against a real site; see PLAN.md - same class of issue
	as `Item.custom_area_per_box`). The real business rule ("every document
	must contain Showroom") only has to hold by the time the document
	becomes a submitted, financially/operationally real record, so it is
	enforced here instead.
	"""
	fieldname = SHOWROOM_FIELD_BY_DOCTYPE.get(doc.doctype)
	if not fieldname:
		return
	if not doc.get(fieldname):
		frappe.throw(_("Showroom is required before submitting {0}.").format(_(doc.doctype)))


def validate_showroom_code(doc, method=None) -> None:
	"""`validate` doc_event body for Branch (the showroom itself).

	custom_showroom_code is a plain Data field (see PLAN.md §2.2 for why it
	is not Select or `reqd`), so uniqueness has no DB-level constraint to
	rely on and is enforced here instead.
	"""
	if not doc.custom_showroom_code:
		return
	duplicate = frappe.db.exists(
		"Branch", {"custom_showroom_code": doc.custom_showroom_code, "name": ["!=", doc.name]}
	)
	if duplicate:
		frappe.throw(
			_("Showroom Code {0} is already used by {1}.").format(doc.custom_showroom_code, duplicate)
		)
