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
# Populated as Roles, Custom Fields, Workspaces, Print Formats, Letter Heads
# and Dashboards are added (Phases 2-3, 7, 9-10). See documentation/architecture/PLAN.md.
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
	}
]

# Doc Events
# ----------
# Populated in Phase 5 once CalculationService and the showroom-enforcement
# validators land (retail_suite/services, retail_suite/retail_suite_ceramic).
doc_events = {}

# Permission Query Conditions / has_permission
# ---------------------------------------------
# Wired up in Phase 3 (showroom permission enforcement) via
# retail_suite.retail_suite_core.permissions.permission_service
permission_query_conditions = {}
has_permission = {}
