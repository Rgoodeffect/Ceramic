# Administrator Manual

## Who does what (Roles)

| Role | Can do |
|---|---|
| Retail Salesperson | Create Customers, Quotations, Sales Invoices, Payment Entries, Supplier Availability Confirmations, Supplier Delivery Orders. View own showroom's data. Print documents. |
| Retail Showroom Manager | View all sales in their showroom, approve/submit/cancel Quotations and Supplier Delivery Orders. |
| Retail Warehouse User | View/process Delivery Notes. No visibility into prices, accounting, or other showrooms. |
| Retail Purchasing User | Manage Suppliers, view Supplier Delivery Orders, create Purchase Invoices. |
| Retail Accounts User | Sales Invoices, Purchase Invoices, Payment Entries, financial reports. |
| Retail Company Owner | Everything, every showroom, both dashboards. |
| System Manager | Full administrative access (standard Frappe role, unrestricted). |

Every non-owner role above is confined to **one showroom** - see
"Showroom Security" below. Full matrix:
`documentation/architecture/PLAN.md` §3.

## Onboarding a new user

1. Desk → User → New. Set email, name.
2. Add exactly one Retail Suite role (plus `System Manager` only for real
   administrators).
3. Set `custom_default_showroom` on the User (informational).
4. Desk → User Permission → New: `User` = this person, `Allow` = `Branch`,
   `For Value` = their showroom. **This step is what actually restricts
   their data** - it drives Frappe's own permission engine, which then
   auto-filters every list view, report, search box, and Link field that
   points to a Branch. Skipping it leaves the user unrestricted.
5. Leave the User Permission step out entirely for Company Owner/System
   Manager - no User Permission row means unrestricted access by design.

## Showroom security, in plain terms

- A "showroom" is an ERPNext `Branch` with a few extra fields - not a
  Company, not a Warehouse.
- Every Quotation, Sales Invoice, Delivery Note, Purchase Invoice, Payment
  Entry, Supplier Delivery Order, and Supplier Availability Confirmation
  carries a showroom field that's auto-filled from the creating user's
  showroom and **cannot be changed to a different one** by a restricted
  user (the system blocks it server-side, not just by hiding a dropdown).
- This is enforced twice: once by the standard Frappe `User Permission`
  mechanism, and again by this app's own `permission_service.py` as an
  explicit backstop used by every API endpoint - see PLAN.md §1.3-2 if
  you want the technical detail.

## Approvals

Discount and cancellation approvals are gated by role (Showroom Manager or
Company Owner) inside the service layer, not by a separate workflow
document. There is no separate "approval request" doctype to configure.

## Reports (Desk → Report, or the Retail Suite Workspace's Reports shortcut)

Sales Summary Report, Sales By Showroom Report (Company Owner only),
Salesperson Performance Report, Customer Sales History, Quotation
Analysis, Supplier Delivery Report, Top Selling Products, Product
Performance Report. All of them respect showroom permissions automatically
- a Salesperson never sees another showroom's rows, even by adjusting
filters.

## Dashboards

- **Showroom Dashboard**: today's sales/quotations/invoices/customers,
  pending deliveries/supplier orders, monthly sales, average invoice
  value, a daily sales trend chart.
- **Executive Dashboard**: the above plus yearly sales, total customers,
  pending payments, and a Sales By Showroom comparison chart. Note: the
  Dashboard doctype itself has no role-gating table, so technically any
  role that can read Sales Invoice can open this page - but every number
  on it is still computed through the showroom-permission system, so a
  Salesperson who navigates here just sees their own showroom's figures
  under executive labels, not a data leak. See PLAN.md Phase 9 notes.

## Print formats & Letter Heads

Each showroom (Branch) has one Letter Head, set via `custom_letter_head`.
It is selected automatically at print time based on the document's
showroom - nobody chooses a Letter Head manually. The 5 print formats
(Ceramic Quotation, Ceramic Sales Invoice, Ceramic Delivery Note, Ceramic
Supplier Delivery Order, Ceramic Payment Receipt) enforce the spec's
display rules directly: Delivery Note and Supplier Delivery Order never
show a price; Sales Invoice never shows the supplier or supply source.

## Retail Suite Settings (Desk → Retail Suite Settings)

Default Company, Default Currency, Default Language, POS Default Price
List, Discount Approval Limit, Enabled Verticals (Ceramic on by default;
Kitchen/Sanitary Ware/Marble & Granite/Furniture/Flooring/Building
Materials are placeholders for future verticals), and feature flags
(Supplier Delivery Workflow, Advanced Dashboard, Customer Portal).

## Backups

Standard Frappe/ERPNext backup applies unchanged - `bench backup` (or your
site's scheduled backup) covers this app's data along with everything
else, since no custom storage mechanism was introduced.
