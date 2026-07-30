# Installation Guide

Target environment: Ubuntu Linux, Frappe Framework 15+, ERPNext 15+,
MariaDB, Redis, Node.js LTS, Bench CLI, Python 3.10+, `wkhtmltopdf` (for
PDF/print export - a standard Frappe dependency, but confirm it's on
`PATH`).

This app has since been installed and run against a real Frappe 15 +
ERPNext 15 bench, with `bench migrate`, the full test suite, the POS,
and print/PDF output all verified working end to end (see
`documentation/testing-report.md` and `documentation/final-review.md`).
The steps below reflect what that actually took, including two easy
things to get wrong that aren't obvious from the spec alone.

## 0. Start from a normal ERPNext site, not a bare one

The single biggest time-saver: create your site and install ERPNext the
**normal way**, going through the Setup Wizard (or at least letting
`bench new-site --install-app erpnext` run its full `after_install` flow
uninterrupted) rather than a bare `install-app` with the wizard skipped.
The Setup Wizard is what seeds a pile of baseline records ERPNext's own
controllers assume exist - default `Standard Selling`/`Standard Buying`
Price Lists, Warehouse Types, root Item/Customer/Supplier Groups and
Territories, and more. Skip it and you'll hit `Could not find Warehouse
Type: Transit`-style errors the first time you touch Sales/Purchase
documents - not a `retail_suite` bug, just missing bootstrap data that a
normal install always has.

Also install the **`payments`** app alongside `erpnext`:

```bash
bench get-app payments --branch version-15
bench --site <site-name> install-app payments
```

ERPNext's `Item Price` and party-account resolution logic reference a
`Payment Gateway` doctype that only exists once `payments` is installed;
without it, saving a Sales/Purchase Invoice fails outright. A standard
`bench setup` following Frappe's own production docs installs this
automatically - it only needs calling out here because it's easy to miss
if you're assembling a bench by hand.

## 1. Get the app onto your bench

```bash
cd ~/frappe-bench
bench get-app retail_suite <this-repo-url> --branch claude/retail-suite-erpnext-architecture-ykrlfr
```

## 2. Install it on a site

```bash
bench --site <site-name> install-app retail_suite
bench --site <site-name> migrate
```

`migrate` does the heavy lifting: creates the three custom doctypes
(Supplier Delivery Order, Supplier Availability Confirmation, Retail Suite
Settings), applies all custom fields, syncs the six Retail Suite roles and
their permissions (including a grant on the standard `Account` doctype -
without it, every custom role fails to save a Sales/Purchase Invoice the
moment ERPNext tries to resolve a default receivable/payable account),
the Retail Suite Workspace, the 8 reports, the Number Cards/Dashboard
Charts/Dashboards, and the 5 print formats.

**If you edit any print format / report / workspace / dashboard chart /
number card JSON after the site has already synced it once**, a plain
`bench migrate` will silently do nothing - Frappe only re-imports a
module-JSON record when its file's `modified` timestamp is newer than
what's already in the database. Either bump that timestamp in the JSON,
or force a reload directly:

```bash
bench --site <site-name> execute frappe.reload_doc --kwargs \
  '{"module": "Retail Suite Core", "dt": "Print Format", "dn": "Ceramic Sales Invoice", "force": True}'
```

## 3. Build the POS frontend

The Vue 3 + TypeScript + Pinia + Frappe UI POS is **not** built
automatically by `bench build`/`install-app` - build it explicitly:

```bash
cd apps/retail_suite/frontend
npm install
npm run build
cd ~/frappe-bench
bench build --app retail_suite
```

`npm run build` produces
`apps/retail_suite/retail_suite/public/frontend/ceramic_pos.js` (a single
IIFE bundle with CSS inlined); `bench build` is what actually links/copies
`public/` into the site's served `assets/` folder - skipping it means the
`ceramic-pos` Page's `frappe.require()` call 404s even though the bundle
built successfully. Re-run **both** commands after pulling any update
that touches `frontend/`.

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

- `custom_showroom_code` (e.g. VF, AS, AT) - a free-text field, not a fixed
  list, so a 4th+ showroom needs no schema change
- `custom_address`, `custom_phone`, `custom_email`
- `custom_letter_head` (create a Letter Head for the showroom first -
  Desk → Letter Head - it's auto-selected on print, never user-chosen;
  put the showroom's actual logo in the Letter Head's HTML content for it
  to appear on printed documents - see `retail_suite/setup/demo_data.py`'s
  `_create_showrooms_and_letter_heads` for a worked example)
- `custom_status` = Active

## 6. Set up items

For every ceramic/porcelain item you sell, set on the Item:

- `custom_area_per_box` (the whole system's box/area math depends on this
  being correct and greater than zero - `CalculationService` validates it
  at the point of use with a clear error if it's missing, rather than as a
  blanket mandatory field, so it doesn't affect non-ceramic items on a
  multi-vertical instance)
- `custom_product_type`, dimensions, `custom_color`, `custom_finish`,
  `custom_collection`, `custom_series`
- `custom_show_in_pos` = 1 to make it appear in the POS product grid
  (this defaults to **off** - every item is opt-in, so nothing shows up in
  the Ceramic Showroom POS by accident)
- Stock/Sales UOM = **Box**
- Register **Square Meter** as an alternate UOM on the Item (its `UOMs`
  table), with a conversion factor of `1 / area_per_box` back to Box -
  ERPNext's Item Price validation requires this before it will accept any
  Item Price in a UOM other than the stock UOM
- An Item Price on your selling Price List with **UOM = Square Meter** (not
  "Sq Meter" - use ERPNext's actual UOM name) - this is where the
  price-per-square-meter actually lives (spec: reuse ERPNext Price List,
  no custom pricing engine)

## 7. Configure Retail Suite Settings

Desk → Retail Suite Settings (single doctype): set Default Company,
Default Currency, POS Default Price List, and toggle which verticals/
feature flags are enabled (Ceramic is on by default).

## 8. Optional: load demo data

To see the whole system populated and working end to end (a demo company,
the three showrooms with the spec's own example names and real logos, demo
users per role, a small catalog, and one worked example of each
fulfillment path):

```bash
bench --site <site-name> execute retail_suite.setup.demo_data.create_demo_data
```

This is **not** run automatically on install - see
`documentation/architecture/PLAN.md` Phase 11 notes for why (fixtures sync
into every installing site; a made-up demo company should not). It's safe
to re-run against a site that already has the demo data - every step
checks for an existing record first (and Letter Head content specifically
gets refreshed in place, so re-running after updating a showroom's logo
picks up the change).

## 9. Open the POS

Desk → Retail Suite (Workspace) → New Sale, or navigate directly to
`/app/ceramic-pos`.

## Running the test suite

```bash
bench --site <site-name> run-tests --app retail_suite
```

All 52 tests across the 15 test files pass on a real Frappe 15 + ERPNext
15 site (confirmed - see `documentation/testing-report.md` for the full
account, including 14 real bugs this process found and fixed along the
way). Run this after install as your own first real signal on your exact
environment/versions.

## Company Warehouse path: a one-time setup step

The "Company Warehouse" supply-source path (Sales Invoice → Delivery Note
→ stock deduction) relies entirely on standard ERPNext stock functionality
by design (spec: "Use standard ERPNext Stock functionality") - this app
deliberately doesn't configure warehouses for you. Before that path will
work for a given company:

1. Give each item a default warehouse (Item → **Item Defaults** table, per
   Company) - or set one sitewide in Stock Settings.
2. Get opening stock into that warehouse (Stock Entry, type **Material
   Receipt**, or however you're bringing in existing inventory).

With that done, ERPNext's standard "Sales Invoice → Make → Delivery Note"
mapping picks up the warehouse and delivered quantity automatically and
deducts stock on submit - confirmed working with zero `retail_suite` code
changes needed.
