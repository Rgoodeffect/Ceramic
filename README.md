# Retail Suite for ERPNext

A scalable, multi-vertical retail platform built on ERPNext/Frappe. The first
vertical implementation is **Ceramic Showroom** — a multi-branch ceramic and
porcelain tile showroom operation (three showrooms: VF, AS, AT) with a
native ERPNext POS, area/box sale-unit conversion, company-warehouse and
external-supplier fulfillment, and strict per-showroom data isolation.

Full product specification: [`CLAUDE.md`](./CLAUDE.md).
Full documentation index (architecture, install, admin, user, developer,
API, testing, upgrade): [`documentation/README.md`](./documentation/README.md).

## Status

Phases 1-13 of the roadmap are complete (app scaffold, core doctypes,
roles/permissions, calculation engine + services, validation hooks, API
layer, Workspace, the Ceramic POS, reports/dashboards, print formats,
demo data, tests, and documentation); Phase 14 (final review against the
spec's own checklists) is next. See `documentation/architecture/PLAN.md`
for the full phase-by-phase status, and `documentation/testing-report.md`
for exactly what has and hasn't been verified without a live bench in this
authoring environment.

To load demo data (a company, the three showrooms, demo users, a small
catalog, and one worked example of each fulfillment path) after install:

```
bench --site <site-name> execute retail_suite.setup.demo_data.create_demo_data
```

## Project layout

```
retail_suite/                  Frappe app package
├── hooks.py                   App metadata, fixtures, doc_events, permission hooks
├── modules.txt                Frappe Module Defs (Retail Suite Core, Retail Suite Ceramic)
├── retail_suite_core/         Generic retail engine: showroom, permissions, custom doctypes,
│                               the Retail Suite Workspace, and the ceramic-pos Page
├── retail_suite_ceramic/      Ceramic vertical: item extension, calculation engine
├── services/                  Business logic (Sales, Quotation, Supplier Delivery, ...)
├── api/                       Thin whitelisted endpoints calling services/
├── reports/                   Shared report query/helper logic
├── dashboards/                Shared dashboard helper logic
├── fixtures/                  Roles, Custom Fields, Custom DocPerm, Print Formats, ...
├── patches/                   Schema/data migrations
├── public/frontend/           Built POS assets (gitignored - see frontend/)
└── tests/
frontend/                      Vue 3 + TypeScript + Pinia + Frappe UI POS source (see frontend/README.md)
documentation/                 Install, Admin, User, Developer, API, and Architecture guides
```

## Requirements

- Frappe Framework 15+, ERPNext 15+
- Python 3.10+, Node.js LTS, MariaDB, Redis, Bench CLI

This repository is developed without a live bench in the authoring environment;
install it into a real bench with:

```
bench get-app retail_suite <this-repo-url>
bench --site <site-name> install-app retail_suite
bench migrate

# Build the POS frontend (not run automatically by bench build/install-app):
cd apps/retail_suite/frontend && npm install && npm run build
```

## License

See [`license.txt`](./license.txt).
