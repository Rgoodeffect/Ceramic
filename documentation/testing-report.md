# Testing Report

## Update: now executed against a real Frappe/ERPNext 15 bench

This app was originally built with no live Frappe/bench installation
available, so every test file was written and reasoned through carefully
but never actually *executed*. That gap has since been closed: a real
Frappe 15 + ERPNext 15 bench was stood up, `retail_suite` was installed
onto a live site with `bench install-app`, `bench migrate` was run to
completion, and `bench --site <site> run-tests --app retail_suite` was run
repeatedly against real code until it passed cleanly:

```
Ran 52 tests in 15.984s

OK
```

`bench --site <site> execute retail_suite.setup.demo_data.create_demo_data`
was also run end to end and verified in the database afterwards: 3
Branches, 8 Users, 3 Items, 2 Customers, 1 Supplier, 1 Quotation, 2 Sales
Invoices (one per fulfillment path), 1 Supplier Availability Confirmation,
and 1 Supplier Delivery Order were all created correctly.

Getting from "zero failures visible" to "52/52 passing" surfaced **eight
genuine, previously-undetected bugs** that no amount of manual code review
had caught - the kind of thing that only shows up when the code actually
runs. Each is described in detail, next to the design decision it
corrects, in `documentation/architecture/PLAN.md`. Summary:

1. Every `doc_event` hook (showroom lock/calculation/supply-source
   validation) only accepted `(doc)`, but Frappe always calls them as
   `f(doc, method)` - this crashed on every real document save.
2. `Branch.custom_showroom_code` was a required `Select` field with fixed
   options `VF/AS/AT`. Frappe auto-defaults a blank `Select` field to its
   first option on every new document, so any Branch created without
   explicitly choosing a code silently collided on `"VF"`. Changed to a
   plain, non-required `Data` field with uniqueness enforced in code.
3. `custom_showroom` on `Quotation`/`Sales Invoice`/`Delivery Note`/
   `Purchase Invoice`/`Payment Entry` was `reqd=1`, which broke Frappe's
   own generic test-fixture creation for those shared doctypes (same class
   of issue as `Item.custom_area_per_box`, found in the same way one layer
   earlier). Moved to a `before_submit` check instead.
4. The app referenced a UOM literally named `"Sq Meter"` everywhere, but
   Frappe's standard UOM is named `"Square Meter"`.
5. ERPNext's `Item Price` validation requires any priced UOM other than an
   Item's `stock_uom` to be registered on that Item's own `uoms` table
   first; our ceramic items never registered `"Square Meter"`, so every
   `Item Price` insert failed outright.
6. Our 5 custom Retail roles had **zero** permission on the standard
   `Account` doctype. A brand-new custom Role starts with no permissions
   on anything (unlike ERPNext's built-in `Sales User`/`Purchase User`/
   `Accounts User`, which ship with `Account` access already), so
   `Sales Invoice`/`Purchase Invoice` saves failed for every one of our
   roles the moment ERPNext tried to resolve a default receivable/payable
   account.
7. Frappe's `submit()`/`cancel()` always require `write` permission before
   any submit-specific check runs. Our `Sales Invoice` grants for
   Salesperson/Showroom Manager had `submit=1` with `write=0`, which no
   standard ERPNext role is ever defined with.
8. `frappe.set_user()` is a plain function in this Frappe version, not a
   context manager - every `with frappe.set_user(...):` in the test suite
   and in `setup/demo_data.py` raised `TypeError` immediately.

Plus a handful of test-isolation bugs in the test suite itself, once the
above unblocked real execution far enough to reach them: `FrappeTestCase`
only rolls back once per test *class*, not per test method, so a couple of
tests had non-idempotent `setUp()` inserts, and one test's data leaked into
another's assertion.

Two supporting facts about this bench, for anyone reproducing the run: it
was installed via `bench install-app` directly rather than the interactive
Setup Wizard, so a few pieces of standard ERPNext bootstrap data the wizard
normally seeds (Warehouse Types, root Item/Customer/Supplier Groups and
Territories, the `Standard Selling`/`Standard Buying` Price Lists, the
`payments` app providing the `Payment Gateway` doctype) had to be created
manually first - none of that is a `retail_suite` bug, it is exactly what
the Setup Wizard would have done on a real customer install.

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
| Calculation Engine unit tests (5 named test cases) | ✅ verbatim, in `test_calculation_service.py`, **executed and passing** |
| Sales/Quotation/Supplier Delivery/Availability Confirmation service tests | ✅ one file each, **executed and passing** |
| Permission tests (showroom isolation, owner access) | ✅ `test_permission_service.py`, `test_showroom_service.py`, and asserted again in `test_workflow_integration.py`, **executed and passing** |
| Workflow/business scenario testing | ✅ `test_workflow_integration.py`, **executed and passing**; `demo_data.py` additionally exercises both fulfillment paths against a live site |
| Company Warehouse workflow test | ⚠️ partial - demonstrated in `setup/demo_data.py` up through Sales Invoice submission (**verified live**); a Delivery Note / actual stock movement was intentionally not scripted, since it requires Warehouse/Stock Settings this app doesn't configure (see PLAN.md Phase 11 notes) |
| UI testing (POS loads, search, cart, printing) | ❌ still not attempted - no browser-against-Desk session run in this environment; `frontend/` was verified to build and its unit logic to type-check cleanly (`vue-tsc` reports zero errors), but no interactive UI test was run |
| Performance testing | ❌ not attempted - requires a populated real site under load, out of scope for this pass |
| Print testing (logo, letterhead, RTL, totals, QR, A4) | ⚠️ partial - all 5 templates render correctly against mock data via `jinja2`; visual/RTL/A4 layout still not checked in an actual browser or PDF renderer |
| Regression/User Acceptance Testing | ❌ not applicable yet - needs real users |

## What "done" means here

`bench run-tests --app retail_suite` passes 52/52 against a real Frappe 15
+ ERPNext 15 site, and `demo_data.py` completes end to end with verified
output. That was the actual acceptance gate this report used to call out
as missing - it is no longer missing. What remains open is UI/browser
testing of the POS page, print-format visual/RTL verification, and
performance testing, none of which this environment could exercise (no
browser-against-Desk session, no load-testing setup); those are called out
explicitly above rather than claimed as done.
