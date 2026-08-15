"""Shared helpers for the whitelisted API layer.

Every function in retail_suite.api.* is a thin wrapper: parse input shape,
call a services/ function, and return this uniform envelope (spec Part 6:
"API response format: success, message, data, errors"). All business rules
and permission checks live in the service layer itself - an endpoint must
never re-implement a check a service already does, and must never trust a
client-supplied value (showroom, user, etc.) without the service
re-validating it server-side.
"""

from __future__ import annotations

import functools

import frappe

EXPECTED_ERRORS = (frappe.ValidationError, frappe.PermissionError, frappe.MandatoryError)


def success(data=None, message: str = "") -> dict:
	return {"success": True, "message": message, "data": data, "errors": []}


def failure(message: str, errors: list | None = None) -> dict:
	return {"success": False, "message": message, "data": None, "errors": errors or [message]}


def api_endpoint(func):
	"""Wrap a whitelisted function so it always returns the uniform envelope.

	Expected validation/permission errors are converted into a clear
	failure() response instead of a raw traceback (spec Part 6: user-facing
	errors must be understandable, technical detail belongs in the logs).
	Anything unexpected is logged server-side and reported generically -
	never leak internals to the client.
	"""

	@functools.wraps(func)
	def wrapper(*args, **kwargs):
		try:
			data = func(*args, **kwargs)
			return success(data)
		except EXPECTED_ERRORS as e:
			frappe.clear_last_message()
			return failure(str(e))
		except Exception:
			frappe.log_error(title=f"Retail Suite API error in {func.__module__}.{func.__name__}")
			return failure(frappe._("Something went wrong. Please try again or contact support."))

	return wrapper
