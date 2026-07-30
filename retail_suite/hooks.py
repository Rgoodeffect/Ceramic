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
# Populated as Workspaces, Print Formats, Letter Heads and Dashboards are
# added (Phases 7, 9-10). See documentation/architecture/PLAN.md.
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
		"doctype": "Custom DocPerm",
		"filters": [
			[
				"role",
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
]

# Doc Events
# ----------
# Populated in Phase 5 once CalculationService and the showroom-enforcement
# validators land (retail_suite/services, retail_suite/retail_suite_ceramic).
doc_events = {}

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
