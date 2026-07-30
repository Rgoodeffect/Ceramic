# Developer Documentation

Read `CLAUDE.md` (the product spec) and `documentation/architecture/PLAN.md`
(the architecture decisions, DocType design, permission matrix, and
phase-by-phase implementation notes/caveats) before changing anything here -
this file assumes both.

## Layout

```
retail_suite/
├── hooks.py                    App metadata, fixtures, doc_events, permission hooks
├── retail_suite_core/          Generic retail engine (Module: "Retail Suite Core")
│   ├── doctype/                Supplier Delivery Order(+Item), Supplier Availability
│   │                           Confirmation, Retail Suite Settings
│   ├── showroom/                showroom_service.py - default/lock the showroom field
│   ├── permissions/             permission_service.py - the showroom isolation backstop
│   ├── printing/                print_service.py - letter head + QR at before_print
│   ├── report/, number_card/, dashboard_chart/, dashboard/, workspace/, page/
├── retail_suite_ceramic/       Ceramic vertical (Module: "Retail Suite Ceramic")
│   └── calculation_service.py  THE box/area engine - see below
├── services/                   SalesService, QuotationService, SupplierDeliveryService,
│                               AvailabilityConfirmationService - all business rules live here
├── api/                        Thin whitelisted wrappers around services/ - no logic here
├── reports/report_utils.py     Shared showroom-scoping helper for Script Reports
├── dashboards/number_cards.py  Number Card "Custom" type computations
├── fixtures/                   Custom Field, Role, Custom DocPerm (data records, not module-owned)
├── setup/demo_data.py          Explicit demo data script (NOT auto-applied - see PLAN.md Phase 11)
└── tests/                      Cross-cutting tests + test_utils.py helpers
frontend/                       Vue 3 + TS + Pinia + Frappe UI POS source (see frontend/README.md)
```

## The one rule that matters most

**Never rebuild what ERPNext already has.** Before adding anything, ask:
does Company/Customer/Supplier/Item/Warehouse/Quotation/Sales
Invoice/Delivery Note/Purchase Invoice/Payment Entry/Price List already
cover this? If yes, extend it with a Custom Field and a service function,
not a new doctype. The only 3 custom doctypes in this entire app
(Supplier Delivery Order, Supplier Availability Confirmation, Retail Suite
Settings) exist because there was genuinely no ERPNext equivalent - see
PLAN.md §2 for the reasoning behind each one.

## The Calculation Engine is the single source of truth

`retail_suite_ceramic/calculation_service.py` is the *only* place box/area
math happens:

```python
calculate_boxes(required_area_sqm, area_per_box) -> int         # ceil, validates > 0
calculate_delivered_area(boxes, area_per_box) -> float
calculate_row(item_code, required_area_sqm, price_list) -> dict  # boxes, delivered_area_sqm, rate_per_box, amount
apply_to_item_row(row, price_list)                               # mutates a Quotation/Sales Invoice Item row
```

It's called from three places, and must always be called from exactly
these three places - never duplicate the formula:

1. `api/calculation.py` (POS live preview, before a line is added to the cart)
2. `services/quotation_service.py` / `services/sales_service.py` (building rows via the API)
3. `calculation_service.validate_item_rows`, wired as a `validate` doc_event
   on Quotation/Sales Invoice, so **manual Desk entry recomputes the same
   numbers** the POS would have produced.

If you ever find yourself writing `math.ceil(area / area_per_box)`
anywhere outside this file, stop - call `calculate_row`/`apply_to_item_row`
instead.

## Adding a new vertical (e.g. Kitchen Showrooms)

1. Create `retail_suite_kitchen/` alongside `retail_suite_ceramic/`, with
   its own Module ("Retail Suite Kitchen") in `modules.txt`.
2. Put vertical-specific fields on `Item` via `fixtures/custom_field.json`
   (same pattern as `custom_area_per_box` etc.) - never in `retail_suite_core`.
3. Write a vertical-specific calculation engine if the pricing/quantity
   logic differs from ceramic's box math (it will).
4. Reuse `retail_suite_core`'s showroom/permission/printing services as-is
   - they're generic by design and don't know anything about ceramic.
5. Add a feature flag to `Retail Suite Settings` (`enable_kitchen` already
   exists as a placeholder) and gate any Workspace shortcuts/POS routing on it.

## Adding a Script Report

Follow the pattern in `retail_suite_core/report/sales_summary_report/`:
`.json` (Report doctype record, `report_type: "Script Report"`), `.py`
(`execute(filters) -> (columns, data)`), `.js` (`frappe.query_reports[...]`
filter definitions). **If your query uses `frappe.db.sql` directly**
(needed for aggregates/joins), you must call
`reports.report_utils.get_showroom_condition()` yourself and AND it into
your WHERE clause - raw SQL bypasses Frappe's automatic permission
filtering, unlike `frappe.get_list`. This is the one place in the app
where showroom scoping doesn't happen for free; every existing report
does this - copy the pattern, don't skip it.

## Adding an API endpoint

Endpoints in `api/` are wrappers, nothing else:

```python
@frappe.whitelist()
@api_endpoint          # from retail_suite.api.utils - uniform {success,message,data,errors}
def my_endpoint(...):
    return my_service.do_the_actual_thing(...)   # business logic lives in services/
```

Never trust a client-supplied showroom value - call
`permission_service.assert_showroom_access(showroom)` inside the service
function, not in the endpoint.

## Frontend

See `frontend/README.md` for the Vite/build details (IIFE bundle, why
`frappe-ui`'s own vite plugins are partially disabled, the known
`vue-tsc` noise from `frappe-ui`'s uncompiled source). In short: Pinia
stores hold state, `api/client.ts`'s `invoke()` is the only way components
talk to the server, and no business logic belongs in a `.vue` file.

## Tests

`bench --site <site> run-tests --app retail_suite`. Use
`retail_suite/tests/test_utils.py`'s `ensure_*` helpers for new test data
setup rather than hand-rolling Branch/User/Item/Price List creation again.

## What NOT to do (from the spec, still true)

- Never modify Frappe/ERPNext core files.
- Never create a duplicate of a standard doctype.
- Never store or calculate supplier stock - availability is a manual phone
  confirmation, recorded, not synchronized.
- Never put business logic in a Client Script or a Vue component.
- Never use `permlevel` to hide a field from *some* roles on a *standard*
  doctype - it's global and will hide it from every role site-wide (see
  PLAN.md §3 notes for exactly this mistake being caught and reverted).
