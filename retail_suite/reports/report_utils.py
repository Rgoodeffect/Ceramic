"""Shared helpers for retail_suite Script Reports.

Every report must respect showroom permissions (spec Part 7: "Reports must
respect ... Showroom Permissions") - never trust a showroom value from the
report's own filters alone, always intersect it with what the user is
actually allowed to see.
"""

from __future__ import annotations

import frappe

from retail_suite.retail_suite_core.permissions import permission_service


def get_showroom_condition(fieldname: str = "custom_showroom", requested_showroom: str | None = None) -> str:
	"""SQL condition restricting a report query to the current user's
	showroom(s), further narrowed by `requested_showroom` if the user picked
	one in the report filters and is allowed to see it. Returns "" (no
	restriction) only for an unrestricted user who did not request one.
	"""
	if permission_service.is_unrestricted():
		if requested_showroom:
			return f"{fieldname} = {frappe.db.escape(requested_showroom)}"
		return ""

	showrooms = permission_service.get_user_showrooms()
	if not showrooms:
		return "1=0"
	if requested_showroom and requested_showroom not in showrooms:
		return "1=0"
	if requested_showroom:
		return f"{fieldname} = {frappe.db.escape(requested_showroom)}"
	quoted = ", ".join(frappe.db.escape(showroom) for showroom in showrooms)
	return f"{fieldname} in ({quoted})"


def require_company_owner() -> None:
	"""Executive-only reports (Sales By Showroom, Showroom Comparison) call
	this first - spec Part 7: "Available for: Company Owner"."""
	if not permission_service.is_unrestricted():
		frappe.throw(
			frappe._("This report is only available to the Company Owner."), frappe.PermissionError
		)
