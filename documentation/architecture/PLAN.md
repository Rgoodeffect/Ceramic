# Retail Suite for ERPNext — Architecture, DocType Design, Permission Matrix & Roadmap

> This is the approved architecture plan for the project (see `CLAUDE.md` for the
> full product specification it implements). It is the source of truth for
> module boundaries, DocType design, and the permission model; update it if any
> of those decisions change.

## Context

The specification in `CLAUDE.md` defines "Retail Suite for ERPNext" (first
vertical: Ceramic Showroom) and instructs: analyze first, produce an
Architecture Plan / DocType Design / Permission Matrix / Implementation
Roadmap, and only then start building, feature by feature. This document is
that deliverable, refined slightly during Phase 1 execution (see the
naming-correction note at the end of §1.1).

Two environment facts shape the plan:
- **No live Frappe/bench runtime exists in the authoring environment.** The
  app is **hand-authored as a standard Frappe app source tree** (the same
  layout `bench new-app` produces), ready to be installed with
  `bench --site SITE install-app retail_suite` in a real environment. Unit
  tests are written as part of each phase but can only be *executed* once
  installed into a real bench+site.
- This is a greenfield build governed entirely by the spec's "ERPNext-first"
  rule: reuse standard doctypes, extend only where there's no standard
  equivalent, never duplicate.

---

## 1. Architecture Plan

### 1.1 App identity

- App name: `retail_suite` (Frappe app, `bench new-app` layout)
- Two Frappe **Modules** (Module Def records, drive the Desk module list and
  doctype ownership): **`Retail Suite Core`** and **`Retail Suite Ceramic`**.
  Everything else (`services/`, `api/`, `reports/`, `dashboards/`, `public/`,
  `fixtures/`, `patches/`, `tests/`) is plain code organization, not a
  separate Frappe Module.

```
retail_suite/                          (repo root)
├── pyproject.toml, license.txt, MANIFEST.in, README.md
├── retail_suite/                      (Python package / app)
│   ├── hooks.py
│   ├── modules.txt                    # "Retail Suite Core", "Retail Suite Ceramic"
│   ├── retail_suite_core/             # Module: Retail Suite Core
│   │   ├── doctype/                   # Supplier Delivery Order, Supplier
│   │   │                              # Availability Confirmation, Retail Suite Settings
│   │   ├── showroom/                  # Branch extension helpers
│   │   ├── permissions/               # permission_service (query conditions, has_permission)
│   │   ├── report/                    # Query/Script Report doctype exports
│   │   ├── dashboard_chart/, number_card/, workspace/, page/
│   ├── retail_suite_ceramic/          # Module: Retail Suite Ceramic
│   │   ├── doctype/                   # (none yet — Item is extended via Custom Field, not a doctype)
│   │   ├── item_extension/            # Item custom field fixture definitions
│   │   └── report/
│   ├── services/                      # SalesService, QuotationService, CalculationService,
│   │                                   # SupplierDeliveryService, AvailabilityConfirmationService,
│   │                                   # DashboardService, ReportingService
│   ├── api/                           # whitelisted endpoints only — thin, call services
│   ├── reports/                       # shared report query/helper logic (not Report doctypes)
│   ├── dashboards/                    # shared dashboard helper logic
│   ├── public/
│   │   └── pos/                       # Vue 3 + TS + Pinia POS SPA, mounted as a Frappe Page
│   ├── fixtures/                      # Roles, Custom Fields, Workspaces, Print Formats,
│   │                                   # Letter Heads, DocPerms, Notifications
│   ├── patches/                       # schema/data migrations
│   ├── config/, templates/, www/      # standard Frappe app folders
│   └── tests/
└── documentation/                     # install / admin / user / dev / API / upgrade guides
```

> **Naming correction made during Phase 1:** the folders for the two Modules
> are `retail_suite_core` and `retail_suite_ceramic` (matching
> `frappe.scrub("Retail Suite Core")`), not bare `core`/`ceramic` as an
> earlier illustrative sketch of this tree showed. A Module Def literally
> named `Core` would collide with Frappe framework's own built-in `Core`
> module (Module Def names are global), so the modules are namespaced.

### 1.2 Layering

```
Vue 3 POS (public/pos)
   │  fetch/call via frappe-ui resource
   ▼
api/  (whitelisted methods — validate input shape only)
   ▼
services/  (ALL business rules live here: SalesService, QuotationService,
            CalculationService, SupplierDeliveryService,
            AvailabilityConfirmationService, PermissionService,
            DashboardService, ReportingService)
   ▼
Frappe ORM / ERPNext standard doctypes (frappe.get_doc, Query Builder)
   ▼
MariaDB
```

No business logic in Client Scripts or Vue components — components call
`api/` endpoints, which are thin wrappers that call a `services/` class
method and return `{success, message, data, errors}`.

### 1.3 Key architecture decisions

These four decisions translate the spec's prose into concrete ERPNext
mechanisms, favoring "reuse ERPNext" over literal doctype names in the spec.
Flagging them explicitly since they're the highest-leverage calls in the
whole design:

1. **"Showroom" = extended ERPNext `Branch`, not a new custom doctype.**
   The spec's own reuse list (Part 2) already names `Branch` as standard;
   Part 9's "showroom concept" (name, code, company, address, contact,
   letter head, assigned users, status) is exactly what `Branch` plus a
   handful of custom fields covers. Creating a parallel "Showroom" doctype
   would duplicate `Branch` and violate the "no duplicate doctypes" rule.
   `Branch` gets custom fields: `custom_showroom_code` (VF/AS/AT),
   `custom_address` (Link Address), `custom_phone`, `custom_email`,
   `custom_letter_head` (Link Letter Head), `custom_status` (Active/Inactive).

2. **Showroom data isolation = native ERPNext `User Permission` against
   `Branch`, not a bespoke permission engine.**
   Every transactional doctype (Quotation, Sales Invoice, Delivery Note,
   Payment Entry, Supplier Delivery Order, Supplier Availability
   Confirmation) gets a mandatory `custom_showroom` Link field (options:
   `Branch`). A `User Permission` row (`allow=Branch`,
   `for_value=<their showroom>`) is created per operational user during
   onboarding. This is the standard ERPNext mechanism that *already*
   auto-filters List Views, Reports, Search, and Link fields — satisfying
   Part 3's "Automatic Showroom Filtering" requirement natively instead of
   hand-rolling query filters everywhere. Company Owner / System Manager
   simply get **no** User Permission row (unrestricted). A thin
   `permission_service.py` still registers `permission_query_conditions` +
   `has_permission` hooks per doctype as defense-in-depth (Part 3: "never
   rely only on hiding buttons... validate server-side") and as the single
   place vertical modules extend later.

3. **Box/area math lives in custom fields + `CalculationService`, not in
   UOM conversion factors, and pricing stays 100% in ERPNext Price
   List/Item Price (no custom pricing engine).**
   - Item: stock UOM = sales UOM = **"Box"** (integer, matches physical
     delivery and real warehouse counts).
   - Item Price records are created in Price Lists with UOM = **"Sq
     Meter"** — this is where "Retail / Wholesale / Project / VIP"
     price-per-m² lives, using ERPNext's existing per-UOM pricing,
     untouched.
   - Quotation Item / Sales Invoice Item / Delivery Note Item get two
     custom fields: `custom_required_area_sqm` (input) and
     `custom_delivered_area_sqm` (read-only, computed).
   - `CalculationService.calculate_row(item_code, required_area, price_list)`:
     `boxes = ceil(required_area / area_per_box)`;
     `delivered_area = boxes * area_per_box`;
     `rate = item_price_per_sqm(price_list) * area_per_box` (this becomes
     the row's standard `rate` — a translation, not a second pricing
     engine); `amount = boxes * rate = delivered_area * price_per_sqm`.
   - This keeps `qty`/`uom`/`rate`/`amount` as plain standard fields (no
     duplicated totals), while `custom_required_area_sqm`/
     `custom_delivered_area_sqm` are the only new numbers, purely for
     transparency/print/report. One engine
     (`retail_suite_ceramic/calculation_service.py`) is called from the POS
     API, from a `validate` hook on Quotation/Sales Invoice (so manual Desk
     entry gets the same math), and from reports — never duplicated.

4. **Product gallery = standard Frappe `File` attachments, not a new child
   doctype.** Primary image uses Item's standard `image` field; the rest of
   the gallery is just multiple attached `File` records against the Item
   (`frappe.client.get_list("File", filters={"attached_to_doctype": "Item",
   "attached_to_name": ...})`). No new "Item Image" child table needed.

### 1.4 `hooks.py` responsibilities

- `doc_events`: `Quotation`, `Sales Invoice` → `validate` (run
  CalculationService, enforce showroom set, enforce non-negative/positive
  area); `Sales Invoice` → `before_submit` (block if supply source =
  Supplier and no *Confirmed* Supplier Availability Confirmation exists);
  `Delivery Note`/`Purchase Invoice` → `validate` (showroom default/lock).
- `permission_query_conditions` / `has_permission`: registered per
  transactional doctype → `retail_suite_core/permissions/permission_service.py`.
- `fixtures`: Custom Field, Custom DocPerm/Role, Workspace, Print Format,
  Letter Head, Dashboard Chart, Number Card, Notification.
- `after_install`: seed default Roles + Retail Suite Settings singleton.

### 1.5 Calculation Engine contract (stable API, everything else calls this)

```
CalculationService.calculate_boxes(required_area_sqm, area_per_box) -> int   # ceil, validates > 0
CalculationService.calculate_delivered_area(boxes, area_per_box) -> float
CalculationService.calculate_row(item_code, required_area_sqm, price_list) -> {
    boxes, delivered_area_sqm, rate_per_box, amount
}
```

---

## 2. DocType Design

### 2.1 Reused standard doctypes (unmodified behavior, just used as-is)

Company, Customer, Supplier, Item, Item Group, Brand, Warehouse, Quotation,
Sales Invoice, Delivery Note, Purchase Invoice, Payment Entry, Price List,
Item Price, Pricing Rule, User, Role, Workspace, Dashboard, Dashboard
Chart, Number Card, Report, Print Format, Letter Head, File, Communication,
Address, Contact, User Permission.

### 2.2 Extended standard doctypes (custom fields, via `fixtures/custom_field.json`)

| DocType | Field (fieldname) | Type | Notes |
|---|---|---|---|
| Branch (= "Showroom") | `custom_showroom_code` | Select (VF/AS/AT, extensible) | unique |
| Branch | `custom_address` | Link → Address | |
| Branch | `custom_phone`, `custom_email` | Data | |
| Branch | `custom_letter_head` | Link → Letter Head | auto-selected on print, never user-chosen |
| Branch | `custom_status` | Select (Active/Inactive) | |
| Item | `custom_product_type` | Select (Tile/Porcelain) | |
| Item | `custom_width`, `custom_height`, `custom_thickness` | Float (mm) | |
| Item | `custom_finish`, `custom_color`, `custom_collection`, `custom_series` | Data/Select | |
| Item | `custom_country_of_origin` | Link → Country | reuse standard Country doctype |
| Item | `custom_area_per_box` | Float | **required**, drives all calculation |
| Item | `custom_pieces_per_box` | Int | |
| Item | `custom_show_in_pos`, `custom_featured_product` | Check | |
| Item | `custom_display_sequence` | Int | |
| Item | `custom_catalog_pdf` | Attach | |
| Item | `custom_warranty_information` | Small Text | |
| Quotation, Sales Invoice, Delivery Note, Purchase Invoice, Payment Entry | `custom_showroom` | Link → Branch | mandatory, set server-side from user's User Permission / default, read-only in UI |
| Quotation Item, Sales Invoice Item, Delivery Note Item | `custom_required_area_sqm` | Float | salesperson input |
| Quotation Item, Sales Invoice Item, Delivery Note Item | `custom_delivered_area_sqm` | Float, read-only | `boxes × area_per_box` |
| Sales Invoice Item | `custom_supply_source` | Select (Company Warehouse/Supplier) | **added in Phase 4** — internal routing only, `print_hide`, never shown on customer-facing documents; tells `SupplierDeliveryService` which lines need a Supplier Delivery Order vs a Delivery Note |
| User | `custom_default_showroom` | Link → Branch | source for the User Permission row; blank ⇒ Company Owner/System Manager (unrestricted) |

### 2.3 New custom doctypes (exactly the 3 the spec calls for, plus Item stays standard)

**Supplier Delivery Order** (submittable)
Parent: `supplier` (Link Supplier), `showroom` (Link Branch), `customer`
(Link Customer), `customer_address` (Link Address), `delivery_date`
(Date), `status` (Select: Draft/Confirmed/Delivered/Cancelled),
`remarks` (Small Text), `supplier_availability_confirmation`
(Link → Supplier Availability Confirmation, mandatory before submit),
`sales_invoice` (Link Sales Invoice, for traceability).
Child table `Supplier Delivery Order Item`: `item_code`, `item_name`,
`boxes_qty` (Int), `supplier_notes`. **No price fields anywhere on this
doctype** (enforced by field list, not just hidden in UI).

**Supplier Availability Confirmation** (submittable)
`supplier` (Link Supplier), `contact_person`, `phone_number`,
`confirmed_by` (Link User), `confirmation_date` (Date),
`confirmation_time` (Time), `status` (Select: Confirmed/Rejected/Pending),
`remarks`, `showroom` (Link Branch), `item` (Link Item, optional — which
product was confirmed).

**Retail Suite Settings** (single doctype)
`default_company` (Link Company), `enabled_verticals` (Table MultiSelect
or JSON — Ceramic checked by default), `default_currency`,
`default_language`, `discount_approval_limit` (Percent),
`pos_default_price_list` (Link Price List), feature-flag checks
(`enable_supplier_delivery_workflow`, `enable_advanced_dashboard`, etc.).

### 2.4 Dependency map

```
Branch(Showroom) ──< User Permission >── User
Company ──< Branch(Showroom)
Item ──< Item Price >── Price List
Customer ──< Quotation ──< Sales Invoice
                                │
                 ┌──────────────┴───────────────┐
                 ▼                               ▼
        Company Warehouse path            Supplier path
        Delivery Note (stock)      Supplier Availability Confirmation
                                          │
                                          ▼
                                 Supplier Delivery Order
                                          │
                                          ▼
                                  Purchase Invoice (later)
                 │
                 ▼
           Payment Entry
```
All nodes carry `custom_showroom`; every arrow is a standard ERPNext
link/`get_mapped_doc` relationship except Supplier Availability
Confirmation → Supplier Delivery Order, which is a hard validation in
`SupplierDeliveryService` (cannot create the order without a *Confirmed*
status confirmation).

---

## 3. Permission Matrix

Roles created (fixtures): `Retail Salesperson`, `Retail Showroom Manager`,
`Retail Warehouse User`, `Retail Purchasing User`, `Retail Accounts User`,
`Retail Company Owner`. `System Manager` is reused as-is (unrestricted,
standard).

All rows below are **additionally** scoped by the showroom `User
Permission` mechanism (§1.3‑2) except where marked "All showrooms".

| DocType | Salesperson | Showroom Manager | Warehouse User | Purchasing User | Accounts User | Company Owner |
|---|---|---|---|---|---|---|
| Customer | C,R,W | R,W | – | – | R | R (All) |
| Quotation | C,R,W,Submit | R,W,Submit,Cancel | – | – | R | R (All) |
| Sales Invoice | C,R,Submit | R,Submit,Cancel(approve) | – | – | R,W | R (All) |
| Delivery Note | R (own) | R | R,W,Submit | – | – | R (All) |
| Supplier Availability Confirmation | C,R,W | R | – | R,W | R | R (All) |
| Supplier Delivery Order | C,R,W,Submit | R,Submit,Cancel(approve) | – | R,W | R | R (All) |
| Purchase Invoice | – | – | – | C,R,W | R,W,Submit | R (All) |
| Payment Entry | C,R | R | – | – | R,W,Submit | R (All) |
| Item / Price List | R | R | R | R | R | R (All) |
| Supplier | R | R | – | C,R,W | R | R (All) |
| Branch (Showroom) | R (own) | R (own) | R (own) | R (own) | R (own) | C,R,W (All) |
| Retail Suite Settings | – | – | – | – | – | R,W (System Manager: full) |
| Showroom Dashboard/Reports | R (own) | R (own) | – | – | R (own) | R (All) + Executive Dashboard |
| Executive Dashboard / Cross-showroom comparison | – | – | – | – | – | R |

Notes:
- "Approve" actions (discount approval, cancellation, return approval) are
  gated inside `services/` via a role check (`Showroom Manager`/`Company
  Owner`) rather than raw DocType permission, matching Part 3's approval
  rules.
- Price/discount/financial data on Delivery Note and Supplier Delivery
  Order is kept away from Warehouse/Purchasing users **without** touching
  `permlevel` on the underlying standard fields: Warehouse User and
  Purchasing User simply never get a Sales Invoice / pricing-doctype
  permission at all (see table), and the Delivery Note / Supplier Delivery
  Order print formats (Phase 10) omit price fields entirely regardless of
  who prints them. Setting `permlevel` on `Sales Invoice Item`/`Delivery
  Note Item` fields was considered and rejected — it is a **global**
  change that would hide those fields from every role on the site
  (including ERPNext's own Sales/Accounts roles), not just our two
  restricted roles, so it's the wrong tool here.
- `permission_query_conditions`/`has_permission` in `permission_service.py`
  is the backstop that re-validates showroom scope on every API call,
  independent of the Desk UI.
- Custom DocPerm fixtures (`fixtures/custom_docperm.json`) add these role
  rows to standard ERPNext doctypes (Customer, Quotation, Sales Invoice,
  Delivery Note, Supplier, Purchase Invoice, Payment Entry, Item, Price
  List, Branch) without editing ERPNext's own doctype JSON — this is the
  standard, upgrade-safe ERPNext mechanism for exactly this purpose. The
  three app-owned custom doctypes carry their permissions directly in
  their own DocType JSON instead (see §2.3), since there's no foreign
  JSON to avoid touching.

---

## 4. Implementation Roadmap

| Phase | Deliverable | Exit criteria | Status |
|---|---|---|---|
| 1. App scaffold | Hand-author `retail_suite` app tree (§1.1), `hooks.py`, `modules.txt` | Structure matches §1.1; importable as a Frappe app once placed in a real bench | ✅ done |
| 2. Core doctypes & fixtures | `Supplier Delivery Order`, `Supplier Availability Confirmation`, `Retail Suite Settings`; Custom Fields from §2.2 as fixtures | JSON doctype defs + fixture files complete, self-consistent | ✅ done |
| 3. Roles & permissions | 6 custom Roles, DocPerm fixtures per §3, `permission_service.py` (query conditions + has_permission) | Permission matrix fully expressed in fixtures/code | ✅ done |
| 4. Calculation Engine & services | `CalculationService`, `SalesService`, `QuotationService`, `SupplierDeliveryService`, `AvailabilityConfirmationService` | Unit tests written for all 5 calculation test cases from spec Part 12 (ready to run once bench-installed) | ✅ done |
| 5. doc_events / validation hooks | Wire CalculationService + showroom enforcement into Quotation/Sales Invoice/Delivery Note/Purchase Invoice `validate` | Manual Desk entry and API entry produce identical results | ✅ done |
| 6. API layer | Whitelisted endpoints in `api/` wrapping the services, uniform `{success,message,data,errors}` response | Each service method has a thin corresponding endpoint | ✅ done |
| 7. Workspace & Desk integration | `Retail Suite` Workspace with cards/shortcuts; per-showroom workspace variant | Appears natively in Desk per Part 2/9 | ✅ done (per-showroom variants deferred to Phase 11, see note below) |
| 8. Ceramic POS (Vue 3 + Frappe UI + TS + Pinia) | Product search/cards, cart with live box/area calc, checkout → Quotation/Sales Invoice | POS mounted as a Frappe Page under Retail Suite, no standalone app | ✅ done - `npm run build` verified passing |
| 9. Reports & Dashboards | Query/Script Reports from Part 7; Showroom + Executive dashboards, Number Cards, Charts | Each report answers a named business question, permission-scoped | ✅ done (see notes) |
| 10. Print Formats & Letter Heads | Quotation, Sales Invoice, Delivery Note, Supplier Delivery Order, Payment Receipt; per-showroom Letter Head auto-select; QR code | Matches Part 8's "must/must-not display" rules per document | ✅ done - all 5 Jinja templates verified to actually render |
| 11. Demo data fixtures | Company, 3 Branches (VF/AS/AT), sample customers/items/suppliers/transactions | Demonstrates full workflow end to end | pending |
| 12. Tests | Unit (calculation, permission, service), integration (workflow), documented as pending real-bench execution | Test files complete and readable; execution deferred to real bench per environment note | pending |
| 13. Documentation | Install, Admin, Salesperson, Developer, Architecture, API, Upgrade guides | One doc per audience, no placeholders | pending |
| 14. Final review against spec's "Final System Review" / "Final Business Validation" / "Final Security Validation" checklists | Walk each checklist item in Parts 13/14 | All checked off or explicitly noted as deferred-to-real-bench | pending |

Each phase is built, self-reviewed, and reported before moving to the next
(per the spec's "work feature by feature" rule) rather than generated all
at once.

Phase 6 also added three read-only endpoints the services layer has no
natural home for, since Phase 8's POS cannot function without them:
`api/catalog.search_items` (product search/cards), `api/calculation.preview_row`
(live cart calculation before a line is committed to a document), and
`api/customer.quick_create_customer` (minimum-fields customer creation using
the standard Customer/Contact/Address doctypes).

Phase 8 notes:
- **`get_session_context` API added** (`retail_suite/api/session.py`): the
  POS needs to know the current user's showroom (to submit with every sale)
  without ever letting them type or pick a different one (spec Part 3). It
  wraps `permission_service.get_user_showroom()`/`is_unrestricted()`.
- **Frappe Page, not a website route.** The spec requires the POS live
  inside Desk, not as a standalone app. The Vue SPA (`frontend/`) is built
  by Vite and mounted by a minimal Page controller
  (`retail_suite_core/page/ceramic_pos/ceramic_pos.js`) via
  `frappe.require()`, rather than served through a `www/*.html` website
  route (which frappe-ui's own `buildConfig`/`jinjaBootData` vite plugins
  assume by default - both are disabled in `frontend/vite.config.ts`).
- **Build output format is IIFE, not Vite's default ES modules.**
  `frappe.require()` injects a classic `<script src>` tag, which can't
  execute bare `import`/`export` syntax; IIFE bundles everything (CSS
  included, self-injected at runtime) into one `ceramic_pos.js` with a
  fixed filename the Page controller references directly.
- **`npm run build` is the real correctness gate, not `vue-tsc`.**
  `frappe-ui` (pre-1.0) ships its own uncompiled source, so a plain
  `vue-tsc --noEmit` walks into its internals (icon components resolved via
  a Vite-only virtual module) and reports ~150 errors that are entirely
  inside `node_modules/frappe-ui` - verified zero errors under this
  project's own `src/`. The build was run in this environment and passes.
- The bundle is a build artifact (`retail_suite/public/frontend/`, gitignored)
  regenerated via `cd frontend && npm install && npm run build` - not
  something `bench build`/`install-app` can be assumed to trigger
  automatically, so this is called out explicitly in the install guide
  (Phase 13).

Phase 10 notes:
- **Letter Head auto-selection and QR population happen at `before_print`**
  (`retail_suite_core/printing/print_service.py`), not at save time:
  `_apply_letter_head` sets `doc.letter_head` from `Branch.custom_letter_head`
  for the doctype's showroom field, and `_apply_qr_code` sets a new
  `custom_qr_code` field (Barcode fieldtype, `fixtures/custom_field.json`)
  on Quotation/Sales Invoice/Payment Entry to `"{doctype}:{name}"`. Neither
  ever lets the user pick a Letter Head manually (spec Part 8).
- **Supplier Delivery Order gained a `letter_head` field** (amending its
  own DocType JSON from Phase 2 - it's our own doctype, so this is a plain
  field addition, not a foreign-doctype customization).
- **All 5 Jinja print format templates were actually rendered** (not just
  JSON-validated) against representative mock documents using the real
  `jinja2` package available in this sandbox, catching real template bugs
  (an early draft's `doc.items` collided with a `dict.items()` stand-in in
  the *test* harness, not real Frappe - fixed by using a plain-attribute
  stand-in matching how `frappe.model.document.Document` actually stores
  field values). Each format's "must/must-not display" list from spec
  Part 8 is enforced directly in the template (e.g. Delivery Note and
  Supplier Delivery Order never reference a price/amount field at all).
- Barcode/"Custom" Number Card-style caveat applies here too: the exact
  Print Format/Custom Field("Barcode") schema is best-effort without a live
  bench; verify QR rendering on first real `bench migrate`.

Phase 9 notes:
- **8 Script Reports** (`retail_suite_core/report/` for generic ones,
  `retail_suite_ceramic/report/` for box/area-specific ones): Sales Summary,
  Sales By Showroom (Company Owner only, via `report_utils.require_company_owner`),
  Salesperson Performance, Customer Sales History, Quotation Analysis,
  Supplier Delivery Report, Top Selling Products, Product Performance.
  "Salesperson" is the document's `owner` (the POS always creates
  documents as the logged-in user; there's no separate Sales Team
  allocation step in this design). "Most Profitable" in Product Performance
  is a documented proxy (revenue/volume ranking) - there is no landed-cost
  data for supplier-sourced items to compute a true margin, and the spec
  explicitly forbids tracking supplier stock/cost.
- **Script Reports use raw parameterized SQL, not the permission-checked
  ORM** (`frappe.db.sql`, needed for the aggregate joins/group-bys), so
  every one of them explicitly applies `report_utils.get_showroom_condition()`
  - this is the one place in the app where showroom scoping has to be
  hand-added rather than inherited automatically, and it's called out here
  so a future report author doesn't skip it.
- **Number Cards are "Custom" type, backed by real Python**
  (`retail_suite/dashboards/number_cards.py`) rather than static filter
  JSON, because several metrics ("Today's Sales", "Monthly Sales", "Yearly
  Sales") need a real dynamic date range evaluated on every view. These
  *do* go through `frappe.get_list` (not `get_all`), so showroom scoping
  is automatic and correct there without special-casing.
- **Two Dashboard Charts** (Daily Sales Trend - line/time-series; Sales By
  Showroom - bar/group-by) feed both the Showroom Dashboard and the
  Executive Dashboard.
- **Dashboard-level access is not role-gated** the way Reports/Pages are
  (the `Dashboard` doctype has no `roles` table): any role that can read
  Sales Invoice can open the Executive Dashboard page. This is not a data
  leak - every card/chart on it still queries through the showroom-scoped
  permission system, so a Salesperson who navigates there just sees their
  own showroom's numbers under executive labels - but it's a real UX gap
  worth tightening later (e.g. a Property Setter hiding the sidebar link
  for non-owner roles).
- **Best-effort JSON schema, same caveat as the Phase 7 Workspace:**
  Number Card ("Custom" type + `method`) and Dashboard Chart field names
  are written from best available knowledge of the Frappe 15 schema without
  a live bench to verify against; check them on first real `bench migrate`.

Phase 7 note - per-showroom workspaces deferred to Phase 11: the spec's
"مجموعة الفيتوري Workspace" example is *this customer's* branding/business
data (their three showrooms' actual names), not generic Retail Suite
architecture - a different commercial customer installing this app would
have entirely different showroom names. The single `Retail Suite` Workspace
built in this phase is the native Desk entry point for every role; each
user only ever sees their own showroom's data on it regardless, because
that's enforced by the permission system (§1.3-2), not by which workspace
page they're looking at. The three literally-named showroom workspaces
(with this customer's logos/branding) are added in Phase 11 alongside the
Branch/Company demo records they reference, as customer-specific fixtures
rather than app architecture.

---

## 5. Decisions confirmed with the product owner

1. **Showroom = extended `Branch`**, not a new "Showroom" doctype (§1.3‑1).
   Biggest literal deviation from the spec's prose, done specifically to
   satisfy the spec's own "never duplicate ERPNext DocTypes" rule.
2. **Showroom isolation via native `User Permission`** rather than a
   custom permission engine (§1.3‑2).
3. **Box/area math via custom fields on child tables + a rate
   translation, not UOM-conversion tricks**, keeping Price List/Item
   Price as the sole pricing source (§1.3‑3).
4. **No live bench/Frappe in the authoring environment** — the app source
   tree is hand-authored to be install-ready; `bench install-app`,
   `bench migrate`, and actual test execution happen once this is placed
   in a real Frappe environment.
