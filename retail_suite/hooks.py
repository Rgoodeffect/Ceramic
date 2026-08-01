from retail_suite import __version__ as app_version

app_name = "retail_suite"
app_title = "Retail Suite"
app_publisher = "Retail Suite for ERPNext"
app_description = (
    "Multi-vertical retail platform for ERPNext. First vertical: Ceramic Showroom."
)
app_email = "support@retailsuite.example"
app_license = "Proprietary"

# Includes in <head>
# ------------------
# app_include_css = "/assets/retail_suite/css/retail_suite.css"
# app_include_js = "/assets/retail_suite/js/retail_suite.js"

# Fixtures
# --------
# Populated as Print Formats, Letter Heads and Property Setters are added
# (Phases 9-10). See documentation/architecture/PLAN.md. Workspace, Report,
# and Dashboard Chart records are NOT fixtures - they live under their own
# module folders (retail_suite_core/workspace/, /report/, /dashboard_chart/)
# and sync automatically via the standard module-reload mechanism.
fixtures = [
	{
		"doctype": "Custom Field",
		"filters": [
			["fieldname", "like", "custom_%"],
			[
				"dt",
				"in",
				[
					"Branch",
					"Item",
					"Quotation",
					"Quotation Item",
					"Sales Invoice",
					"Sales Invoice Item",
					"Delivery Note",
					"Delivery Note Item",
					"Purchase Invoice",
					"Payment Entry",
					"User",
				],
			],
		],
	},
	{
		"doctype": "Role",
		"filters": [
			[
				"name",
				"in",
				[
					"Retail Salesperson",
					"Retail Showroom Manager",
					"Retail Warehouse User",
					"Retail Purchasing User",
					"Retail Accounts User",
					"Retail Company Owner",
				],
			]
		],
	},
	{
		# Filtered by doctype (parent), not by role, and that's deliberate:
		# the moment a site has *any* Custom DocPerm row for a doctype,
		# Frappe's permission resolution (frappe.permissions.get_valid_perms)
		# stops consulting that doctype's standard, built-in DocPerm rows
		# entirely - for every role, not just the ones a new row was added
		# for. Filtering this fixture by our own role names only exports our
		# 6 new rows per doctype, silently dropping the standard rows
		# (Stock User/Stock Manager/Sales User/Delivery User/Delivery
		# Manager on Delivery Note, etc.) that a fresh install still needs -
		# found by logging in as a user with only System Manager (no retail
		# role) and hitting "You need the 'create' permission on Delivery
		# Note" on a real site, then discovering every standard role had
		# silently lost all access to every doctype in this list the moment
		# our roles were added to it. Fixed by re-copying the original
		# DocPerm rows into Custom DocPerm (frappe.permissions.copy_perms,
		# the same thing "Customize Form" does under the hood) before
		# exporting, so this fixture is the *complete* permission set for
		# each doctype - standard roles plus ours - not just the diff.
		"doctype": "Custom DocPerm",
		"filters": [
			[
				"parent",
				"in",
				[
					"Account",
					"Branch",
					"Customer",
					"Delivery Note",
					"Item",
					"Payment Entry",
					"Price List",
					"Purchase Invoice",
					"Quotation",
					"Sales Invoice",
					"Supplier",
				],
			]
		],
	},
	{
		# Makes each Ceramic print format the one a plain "Print" click uses,
		# not just something reachable from the format picker - without this,
		# printing a Quotation/Sales Invoice/Delivery Note/Payment Entry falls
		# back to Frappe's own generic layout (raw QR data URI as text, no
		# letterhead, ERPNext's full field set including things like "Grant
		# Commission") - exactly the "default ERPNext forms" look spec Part 8
		# says these documents must not have. Found by printing a real invoice
		# without explicitly picking a format in the browser. This is the same
		# Property Setter `frappe.printing...print_format.make_default()`
		# creates when a user clicks "Set as Default" in the Desk UI - done as
		# a fixture here so it's already true on install, for every doctype
		# this app owns a Ceramic print format for except Supplier Delivery
		# Order (a custom doctype, so `default_print_format` is set directly
		# on its own DocType JSON instead - no foreign doctype to avoid
		# touching there).
		"doctype": "Property Setter",
		"filters": [
			["property", "=", "default_print_format"],
			[
				"doc_type",
				"in",
				["Quotation", "Sales Invoice", "Delivery Note", "Payment Entry"],
			],
		],
	},
]

# Doc Events
# ----------
# Showroom defaulting/locking (PLAN.md §1.4) applies to every showroom-scoped
# doctype; CalculationService recomputes ceramic item rows so manual Desk
# entry and the POS API (Phase 6) always agree; the Sales Invoice supplier
# workflow is enforced at validate (supply source required) and before_submit
# (a Confirmed Supplier Availability Confirmation must exist for any
# Supplier-sourced line).
_SHOWROOM_LOCK = "retail_suite.retail_suite_core.showroom.showroom_service.apply_showroom_default_and_lock"
_SHOWROOM_REQUIRE = "retail_suite.retail_suite_core.showroom.showroom_service.require_showroom_before_submit"
_CALC_MODULE = "retail_suite.retail_suite_ceramic.calculation_service"
_SALES_SERVICE = "retail_suite.services.sales_service"
_PRINT_SERVICE = "retail_suite.retail_suite_core.printing.print_service.apply_print_context"

doc_events = {
	"Quotation": {
		"validate": [_SHOWROOM_LOCK, f"{_CALC_MODULE}.validate_item_rows"],
		"before_submit": [_SHOWROOM_REQUIRE],
		"before_print": [_PRINT_SERVICE],
	},
	"Sales Invoice": {
		"validate": [
			_SHOWROOM_LOCK,
			f"{_CALC_MODULE}.validate_item_rows",
			f"{_SALES_SERVICE}.validate_supply_sources",
		],
		"before_submit": [_SHOWROOM_REQUIRE, f"{_SALES_SERVICE}.validate_supplier_confirmation_before_submit"],
		"before_print": [_PRINT_SERVICE],
	},
	"Delivery Note": {
		"validate": _SHOWROOM_LOCK,
		"before_submit": [_SHOWROOM_REQUIRE],
		"before_print": [_PRINT_SERVICE],
	},
	"Purchase Invoice": {
		"validate": _SHOWROOM_LOCK,
		"before_submit": [_SHOWROOM_REQUIRE],
		"before_print": [_PRINT_SERVICE],
	},
	"Payment Entry": {
		"validate": _SHOWROOM_LOCK,
		"before_submit": [_SHOWROOM_REQUIRE],
		"before_print": [_PRINT_SERVICE],
	},
	"Supplier Delivery Order": {"validate": _SHOWROOM_LOCK, "before_print": [_PRINT_SERVICE]},
	"Supplier Availability Confirmation": {"validate": _SHOWROOM_LOCK},
	"Branch": {
		"validate": ["retail_suite.retail_suite_core.showroom.showroom_service.validate_showroom_code"]
	},
}

# Permission Query Conditions / has_permission
# ---------------------------------------------
# Showroom-isolation backstop (defense-in-depth on top of the User
# Permission mechanism - see documentation/architecture/PLAN.md §1.3-2 and
# retail_suite_core/permissions/permission_service.py).
_PERM_MODULE = "retail_suite.retail_suite_core.permissions.permission_service"

permission_query_conditions = {
	"Quotation": f"{_PERM_MODULE}.get_permission_query_conditions_quotation",
	"Sales Invoice": f"{_PERM_MODULE}.get_permission_query_conditions_sales_invoice",
	"Delivery Note": f"{_PERM_MODULE}.get_permission_query_conditions_delivery_note",
	"Purchase Invoice": f"{_PERM_MODULE}.get_permission_query_conditions_purchase_invoice",
	"Payment Entry": f"{_PERM_MODULE}.get_permission_query_conditions_payment_entry",
	"Supplier Delivery Order": f"{_PERM_MODULE}.get_permission_query_conditions_supplier_delivery_order",
	"Supplier Availability Confirmation": (
		f"{_PERM_MODULE}.get_permission_query_conditions_supplier_availability_confirmation"
	),
}

has_permission = {
	"Quotation": f"{_PERM_MODULE}.has_permission",
	"Sales Invoice": f"{_PERM_MODULE}.has_permission",
	"Delivery Note": f"{_PERM_MODULE}.has_permission",
	"Purchase Invoice": f"{_PERM_MODULE}.has_permission",
	"Payment Entry": f"{_PERM_MODULE}.has_permission",
	"Supplier Delivery Order": f"{_PERM_MODULE}.has_permission",
	"Supplier Availability Confirmation": f"{_PERM_MODULE}.has_permission",
}
