"""Cross-cutting showroom defaulting/locking.

Wired via hooks.py `validate` doc_events onto every showroom-scoped doctype
(spec Part 3 "Document Security": "Every business document must contain
Showroom. This field must be automatically populated. The user should not
manually select another showroom.").
"""

from __future__ import annotations

from retail_suite.retail_suite_core.permissions import permission_service

SHOWROOM_FIELD_BY_DOCTYPE = permission_service.SHOWROOM_FIELD_BY_DOCTYPE


def apply_showroom_default_and_lock(doc) -> None:
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
