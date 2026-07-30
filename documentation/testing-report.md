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
| Company Warehouse workflow test | ✅ full loop verified live - `demo_data.py`'s Quotation → Sales Invoice, then (by hand, at the deployment level, same as a real customer would) Item Defaults + opening stock + ERPNext's standard "Make → Delivery Note" mapping, submitted, with the Stock Ledger Entry confirming the deduction. Zero app code changes needed. |
| UI testing (POS loads, search, cart, printing) | ✅ done - drove the POS with a real Chromium browser (Playwright) as a logged-in Retail Salesperson: search, add-to-cart with live box/area calculation, customer selection, and checkout into a real submitted Sales Invoice, then its print view. Found and fixed 5 more real bugs this surfaced (CSRF token plumbing, POS product filter defaulting the wrong way, QR code rendering as literal text, Letter Head computed but never shown, Payment Entry missing from the print showroom-field map) - see PLAN.md. |
| Performance testing | ❌ not attempted - requires a populated real site under load, out of scope for this pass |
| Print testing (logo, letterhead, RTL, totals, QR, A4) | ✅ mostly done - all formats verified rendering correctly in a real browser via `/printview` (not just mock-data `jinja2` rendering): Arabic RTL letterhead, real scannable QR code, correct field content per doctype. Not done: downloading and opening an actual exported PDF file. |
| Regression/User Acceptance Testing | ❌ not applicable yet - needs real users |

## What "done" means here

`bench run-tests --app retail_suite` passes 52/52 against a real Frappe 15
+ ERPNext 15 site, `demo_data.py` completes end to end with verified
output, the POS was driven start-to-finish in a real browser as a
salesperson, the Company Warehouse path was completed through an actual
Delivery Note and confirmed stock deduction, and print output was visually
verified in-browser (RTL letterhead, QR code, correct fields per doctype).
Those were the acceptance gates this report used to call out as missing -
none of them are missing anymore, and thirteen real, previously-invisible
bugs were found and fixed getting there (see PLAN.md for each one, next to
the design decision it corrects). What remains open: performance testing
under real load, and opening an actually-exported PDF file rather than the
equivalent in-browser print preview - both out of scope for what this
environment could reasonably exercise in this pass.
