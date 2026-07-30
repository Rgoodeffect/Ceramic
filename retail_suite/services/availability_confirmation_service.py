"""Supplier Availability Confirmation recording (spec Part 5: Supplier Process).

Supplier stock is never synchronized, warehoused, or calculated (spec Part
1/5) - this service only records what a human was told on a phone call.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import getdate, nowtime

from retail_suite.retail_suite_core.permissions import permission_service

VALID_STATUSES = ("Pending", "Confirmed", "Rejected")


def record_confirmation(
	supplier: str,
	showroom: str,
	contact_person: str,
	phone_number: str,
	status: str,
	item: str | None = None,
	confirmation_date: str | None = None,
	confirmation_time: str | None = None,
	remarks: str | None = None,
	submit: bool = True,
):
	permission_service.assert_showroom_access(showroom)
	if status not in VALID_STATUSES:
		frappe.throw(_("Status must be one of: {0}.").format(", ".join(VALID_STATUSES)))

	confirmation = frappe.new_doc("Supplier Availability Confirmation")
	confirmation.supplier = supplier
	confirmation.item = item
	confirmation.showroom = showroom
	confirmation.contact_person = contact_person
	confirmation.phone_number = phone_number
	confirmation.status = status
	confirmation.confirmation_date = confirmation_date or getdate()
	confirmation.confirmation_time = confirmation_time or nowtime()
	confirmation.confirmed_by = frappe.session.user
	confirmation.remarks = remarks
	confirmation.insert()
	if submit:
		confirmation.submit()
	return confirmation
