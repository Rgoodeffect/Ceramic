"""Whitelisted read endpoint exposing the current user's showroom context.

Spec Part 3: the showroom field "must be automatically populated. The user
should not manually select another showroom." The POS calls this once on
load to know which showroom (and default price list/currency) to submit
with every sale - it never lets an operational user type or pick a
different one.
"""

from __future__ import annotations

import frappe

from retail_suite.api.utils import api_endpoint
from retail_suite.retail_suite_core.permissions import permission_service


@frappe.whitelist()
@api_endpoint
def get_session_context():
	price_list = frappe.db.get_single_value("Retail Suite Settings", "pos_default_price_list")
	return {
		"showroom": permission_service.get_user_showroom(),
		"is_unrestricted": permission_service.is_unrestricted(),
		"price_list": price_list or "Standard Selling",
		"currency": frappe.defaults.get_global_default("currency"),
	}
