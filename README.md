# Retail Suite for ERPNext

A scalable, multi-vertical retail platform built on ERPNext/Frappe. The first
vertical implementation is **Ceramic Showroom** — a multi-branch ceramic and
porcelain tile showroom operation (three showrooms: VF, AS, AT) with a
native ERPNext POS, area/box sale-unit conversion, company-warehouse and
external-supplier fulfillment, and strict per-showroom data isolation.

Full product specification: [`CLAUDE.md`](./CLAUDE.md).
Architecture, DocType design, permission matrix, and implementation roadmap:
[`documentation/architecture/PLAN.md`](./documentation/architecture/PLAN.md).

## Status

Phase 1 (application structure) is scaffolded. See the roadmap in
`documentation/architecture/PLAN.md` for what's implemented vs. planned.

## Project layout

```
retail_suite/                  Frappe app package
├── hooks.py                   App metadata, fixtures, doc_events, permission hooks
├── modules.txt                Frappe Module Defs (Retail Suite Core, Retail Suite Ceramic)
├── retail_suite_core/         Generic retail engine: showroom, permissions, custom doctypes
├── retail_suite_ceramic/      Ceramic vertical: item extension, calculation engine
├── services/                  Business logic (Sales, Quotation, Supplier Delivery, ...)
├── api/                       Thin whitelisted endpoints calling services/
├── reports/                   Shared report query/helper logic
├── dashboards/                Shared dashboard helper logic
├── fixtures/                  Exported Roles, Custom Fields, Workspaces, Print Formats, ...
├── patches/                   Schema/data migrations
├── public/pos/                Vue 3 + TypeScript + Pinia POS SPA (Frappe Page, not standalone)
└── tests/
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
```

## License

See [`license.txt`](./license.txt).
