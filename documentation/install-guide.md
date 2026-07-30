# Installation Guide

Target environment: Ubuntu Linux, Frappe Framework 15+, ERPNext 15+,
MariaDB, Redis, Node.js LTS, Bench CLI, Python 3.10+.

## 1. Get the app onto your bench

```bash
cd ~/frappe-bench
bench get-app retail_suite <this-repo-url>
```

## 2. Install it on a site

```bash
bench --site <site-name> install-app retail_suite
bench --site <site-name> migrate
```

`migrate` does the heavy lifting: creates the three custom doctypes
(Supplier Delivery Order, Supplier Availability Confirmation, Retail Suite
Settings), applies all custom fields, syncs the six Retail Suite roles and
their permissions, the Retail Suite Workspace, the 8 reports, the Number
Cards/Dashboard Charts/Dashboards, and the 5 print formats.

**Verify the schema against your exact Frappe/ERPNext version before going
further.** This app was built without a live bench to migrate against (see
`documentation/architecture/PLAN.md` for exactly which fixtures carry a
"best-effort schema" caveat: primarily the Workspace `content` JSON, the
Number Card "Custom" type fields, and the Dashboard Chart fields). If
`bench migrate` reports an error on one of those, the fix is almost always
a field name or JSON shape mismatch for that specific Frappe version, not a
structural problem with the app.

## 3. Build the POS frontend

The Vue 3 + TypeScript + Pinia + Frappe UI POS is **not** built
automatically by `bench build`/`install-app` - build it explicitly:

```bash
cd apps/retail_suite/frontend
npm install
npm run build
```

This produces `apps/retail_suite/retail_suite/public/frontend/ceramic_pos.js`
(a single IIFE bundle with CSS inlined), which the `ceramic-pos` Frappe Page
loads via `frappe.require()`. Re-run this after pulling any update that
touches `frontend/`.

## 4. Assign showrooms to your operational users

Every Salesperson/Showroom Manager/Warehouse User/Purchasing User/Accounts
User needs:

1. The corresponding Retail Suite role (Desk → User → Roles).
2. `custom_default_showroom` set on their User record.
3. A `User Permission` row: `Allow` = Branch, `For Value` = their showroom.
   (Step 2 is informational/for reference; step 3 is what actually
   restricts their data access - see `documentation/architecture/PLAN.md`
   §1.3-2.)

Leave both blank for **Company Owner** and **System Manager** - they see
every showroom by design.

## 5. Configure the three showrooms

Retail Suite models a "showroom" as an extended `Branch` (see PLAN.md §1.3-1,
not a new doctype). For each showroom, create or edit a Branch and set:

- `custom_showroom_code` (e.g. VF, AS, AT)
- `custom_address`, `custom_phone`, `custom_email`
- `custom_letter_head` (create a Letter Head for the showroom first -
  Desk → Letter Head - it's auto-selected on print, never user-chosen)
- `custom_status` = Active

## 6. Set up items

For every ceramic/porcelain item you sell, set on the Item:

- `custom_area_per_box` (**required** - the whole system's box/area math
  depends on this being correct and greater than zero)
- `custom_product_type`, dimensions, `custom_color`, `custom_finish`,
  `custom_collection`, `custom_series`
- `custom_show_in_pos` = 1 to make it appear in the POS product grid
- Stock/Sales UOM = **Box**
- An Item Price on your selling Price List with **UOM = Square Meter** - this
  is where the price-per-square-meter actually lives (spec: reuse ERPNext
  Price List, no custom pricing engine)

## 7. Configure Retail Suite Settings

Desk → Retail Suite Settings (single doctype): set Default Company,
Default Currency, POS Default Price List, and toggle which verticals/
feature flags are enabled (Ceramic is on by default).

## 8. Optional: load demo data

To see the whole system populated and working end to end (a demo company,
the three showrooms with the spec's own example names, demo users per
role, a small catalog, and one worked example of each fulfillment path):

```bash
bench --site <site-name> execute retail_suite.setup.demo_data.create_demo_data
```

This is **not** run automatically on install - see
`documentation/architecture/PLAN.md` Phase 11 notes for why (fixtures sync
into every installing site; a made-up demo company should not).

## 9. Open the POS

Desk → Retail Suite (Workspace) → New Sale, or navigate directly to
`/app/ceramic-pos`.

## Running the test suite

```bash
bench --site <site-name> run-tests --app retail_suite
```

None of the 15 test files in this app have been executed in the authoring
environment (no live bench was available - see the repo README). Run this
after install to get a first real signal.
