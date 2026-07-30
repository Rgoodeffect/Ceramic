# Testing Report

## Environment constraint (read this first)

This app was built in an environment with **no live Frappe/bench
installation** - only Python, Node.js, and standard dev tooling. Every
test file listed below has been **written and reasoned through carefully,
syntax-checked (`python3 -m py_compile`), and in several cases traced
line-by-line against the exact service code it exercises**, but none of
them have actually been *executed* against a real Frappe site, because no
such site exists in this environment. Run
`bench --site <site> run-tests --app retail_suite` after installation to
get a first real pass/fail signal, and treat that as required before
calling this application production-ready - this report is not a
substitute for it.

Two things *were* independently verified in this environment despite the
constraint, because the tools for them (Node.js, `jinja2`) happened to be
available:
- The POS frontend actually builds (`cd frontend && npm run build`
  succeeds, verified more than once).
- All 5 print format Jinja templates were parsed *and rendered* against
  representative mock documents using the real `jinja2` package (not just
  checked for valid JSON).

## Test inventory (15 files)

| File | Covers |
|---|---|
| `retail_suite_core/doctype/supplier_delivery_order/test_supplier_delivery_order.py` | Mandatory items; no price fields on the child table |
| `retail_suite_core/doctype/supplier_availability_confirmation/test_supplier_availability_confirmation.py` | Default status; status options match spec |
| `retail_suite_core/doctype/retail_suite_settings/test_retail_suite_settings.py` | Single doctype; Ceramic enabled by default |
| `retail_suite_ceramic/test_calculation_service.py` | **Spec Part 12's 5 calculation test cases verbatim**, plus an end-to-end row test and a doc_events-vs-API parity test |
| `tests/test_permission_service.py` | Unrestricted vs restricted users, showroom query conditions, Company Owner bypass |
| `tests/test_showroom_service.py` | Auto-default, lock against a different showroom, unrestricted-user passthrough |
| `tests/test_api_utils.py` | Success/failure envelope shape, no internal error leakage |
| `tests/test_session_api.py` | Showroom resolution for restricted vs unrestricted users |
| `tests/test_number_cards.py` | Value shape; a restricted user's card never includes another showroom's data |
| `tests/test_print_service.py` | Letter head auto-selection; QR population only on supported doctypes |
| `tests/test_quotation_service.py` | Calculation wiring, empty-items rejection, cross-showroom rejection |
| `tests/test_sales_service.py` | Supply source validation, the before_submit supplier-confirmation gate (both blocked and allowed paths) |
| `tests/test_availability_confirmation_service.py` | Default submit behavior, status validation, draft option |
| `tests/test_supplier_delivery_service.py` | Happy path, no-price-fields invariant, rejecting a confirmation that isn't Confirmed |
| `tests/test_workflow_integration.py` | **Full Quotation → Sales Invoice → Supplier Delivery Order flow**, asserting the spec's own worked numbers (2.8→2 boxes→3.0 m²→150 total) and the Final Security Validation (cross-showroom denial, owner access) |

Not a test file, but load-bearing for all of the above:
`tests/test_utils.py` (shared Branch/User/Item/Price List/Customer/Supplier
fixture helpers, introduced in Phase 12).

## Coverage against the spec's Part 12 requirements

| Spec requirement | Status |
|---|---|
| Calculation Engine unit tests (5 named test cases) | ✅ verbatim, in `test_calculation_service.py` |
| Sales/Quotation/Supplier Delivery/Availability Confirmation service tests | ✅ one file each |
| Permission tests (showroom isolation, owner access) | ✅ `test_permission_service.py`, `test_showroom_service.py`, and asserted again in `test_workflow_integration.py` |
| Workflow/business scenario testing | ✅ `test_workflow_integration.py` |
| Company Warehouse workflow test | ⚠️ partial - demonstrated in `setup/demo_data.py` up through Sales Invoice submission; a Delivery Note / actual stock movement was intentionally not scripted, since it requires Warehouse/Stock Settings this app doesn't configure (see PLAN.md Phase 11 notes) |
| UI testing (POS loads, search, cart, printing) | ❌ not attempted - no live bench/browser-against-Desk available; `frontend/` was verified to build and its unit logic to type-check cleanly (`vue-tsc` reports zero errors under this project's own `src/`), but no interactive UI test was run |
| Performance testing | ❌ not attempted - requires a populated real site |
| Print testing (logo, letterhead, RTL, totals, QR, A4) | ⚠️ partial - all 5 templates render correctly against mock data (see above); visual/RTL/A4 layout was not checked in an actual browser or PDF renderer |
| Regression/User Acceptance Testing | ❌ not applicable yet - needs a real site and real users |

## What "done" means here

Every test file is complete, readable, and (as far as static analysis and
manual tracing can establish) internally consistent with the code it
tests. Several genuine bugs were caught this way during development and
fixed before being committed - notably during Phase 11's demo script
(`User.add_roles()` ordering, a non-existent `Sales Invoice.remarks`
field) and Phase 10's print formats (a test-harness bug that would have
masked a real `doc.items` check). That process is a substitute for careful
review, not for actually running the code - the first `bench run-tests`
against a real site remains the true acceptance gate for this application.
