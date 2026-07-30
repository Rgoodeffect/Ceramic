# Upgrade Guide

## Before any upgrade

1. **Back up.** `bench --site <site> backup --with-files`. Verify the
   backup file exists and is non-trivial in size before proceeding.
2. Note the current app version (`retail_suite/__init__.py`'s
   `__version__`) and read this file's changelog section below for
   anything between your version and the target.

## Standard upgrade procedure

```bash
cd ~/frappe-bench
bench get-app retail_suite <repo-url> --branch <target-branch>   # or git pull inside apps/retail_suite
bench --site <site-name> migrate
cd apps/retail_suite/frontend && npm install && npm run build     # rebuild the POS - see install-guide.md
bench --site <site-name> run-tests --app retail_suite
bench restart
```

Then manually verify the checklist in
`documentation/architecture/PLAN.md` §"Final review" (Phase 14) still
holds: POS loads, a sale can be completed, showroom isolation still works,
reports/dashboards still load, printing still works.

## Upgrade-safety guarantees this app relies on

- **No ERPNext/Frappe core files are ever modified.** Every customization
  lives inside this app (Custom Fields, Custom DocPerm, hooks.py doc_events,
  three genuinely new doctypes). An ERPNext core upgrade should never
  conflict with this app's own files.
- **Showroom = extended `Branch`, not a fork of any core doctype.** If a
  future ERPNext version changes Branch's own schema, only the
  `custom_*` fields added by this app's fixtures are at risk of a naming
  collision - check `fixtures/custom_field.json` against the new version's
  Branch fields if `bench migrate` complains.
- **The three custom doctypes are versioned Frappe doctypes like any
  other** - schema changes to them go through a Frappe **patch**
  (`retail_suite/patches/`), never a manual `ALTER TABLE`. There are no
  patches yet as of this writing; the first one should be added the first
  time a field needs to change shape (not just be added) on Supplier
  Delivery Order, Supplier Availability Confirmation, or Retail Suite
  Settings.

## Known schema risk areas (see PLAN.md for detail)

A few fixtures were authored without a live bench to validate their exact
JSON shape against a specific Frappe version - these are the first places
to check if an upgrade (or even the first install) surfaces a schema
error:

- `retail_suite_core/workspace/retail_suite/retail_suite.json` (Workspace
  `content` block format)
- `retail_suite_core/number_card/*/*.json` (Number Card "Custom" type +
  `method` field)
- `retail_suite_core/dashboard_chart/*/*.json` (Dashboard Chart field names)

None of these affect data integrity if wrong - worst case, a Workspace/
Number Card/Chart fails to render and needs its JSON corrected to match
the installed Frappe version's actual schema.

## Frappe/ERPNext version compatibility

Built against Frappe Framework 15+ / ERPNext 15+ conventions throughout
(Script Reports, Custom DocPerm, `frappe.get_list`, standard `Branch`/
`Item`/`Quotation`/`Sales Invoice` schemas as of that version line). No
deprecated APIs were knowingly used. Compatibility with Frappe/ERPNext 16+
has not been verified - re-run the full checklist above after any major
version bump.

## Changelog

### v0.0.1 (current)
Initial implementation: application scaffold, core doctypes and
permissions, calculation engine and business services, validation hooks,
API layer, Workspace, Ceramic POS, reports and dashboards, print formats,
demo data, and tests. See `documentation/architecture/PLAN.md` for the
full phase-by-phase history and every design decision behind it.
