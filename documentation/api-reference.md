# API Documentation

All endpoints are Frappe whitelisted methods, called as
`POST /api/method/<dotted.path>` with a Frappe session cookie/CSRF token
(standard Frappe auth - nothing custom). Every response is wrapped in the
same envelope by `retail_suite.api.utils.api_endpoint`:

```json
{
  "success": true,
  "message": "",
  "data": { "...": "..." },
  "errors": []
}
```

On failure (`success: false`), `message` is a clear, user-facing
explanation - never a raw traceback. Unexpected server errors are logged
via `frappe.log_error` and reported generically to the client.

## `retail_suite.api.session`

### `get_session_context()`
No arguments. Returns the current user's showroom context - the POS calls
this once on load.
```json
{ "showroom": "مجموعة الفيتوري", "is_unrestricted": false, "price_list": "Standard Selling", "currency": "USD" }
```

## `retail_suite.api.catalog`

### `search_items(search_term="", price_list=None, limit=20)`
Returns a list of Item dicts (code, name, image, dimensions, color,
finish, area per box, `price_per_sqm` if `price_list` given) for items
with `custom_show_in_pos = 1`. Matches `search_term` against item code,
name, brand, collection, series, or color.

## `retail_suite.api.calculation`

### `preview_row(item_code, required_area_sqm, price_list)`
Runs the real Calculation Engine and returns the exact numbers a saved
document would have, without saving anything:
```json
{ "boxes": 2, "area_per_box": 1.5, "delivered_area_sqm": 3.0, "price_per_sqm": 50, "rate_per_box": 75, "amount": 150 }
```

## `retail_suite.api.customer`

### `quick_create_customer(customer_name, mobile_no, address=None, email=None)`
Creates a standard Customer + Contact (+ Address if given). Returns
`{"name": "<customer id>"}`.

## `retail_suite.api.quotation`

### `create_quotation(customer, showroom, items, price_list)`
`items` is a JSON string: `[{"item_code": "...", "required_area_sqm": 2.8}]`.
Creates a draft Quotation with boxes/rate/delivered area computed server-side.
Returns `{"name": "<quotation id>"}`. Raises a permission error if
`showroom` isn't one the calling user is allowed to act on.

## `retail_suite.api.sales`

### `create_sales_invoice(customer, showroom, items, price_list)`
`items`: `[{"item_code", "required_area_sqm", "supply_source": "Company Warehouse"|"Supplier"}]`.
Returns `{"name": "<sales invoice id>"}`.

### `create_sales_invoice_from_quotation(quotation, supply_source_by_item)`
`supply_source_by_item`: JSON dict `{"<item_code>": "Company Warehouse"|"Supplier"}`.
Converts a Quotation into a Sales Invoice via ERPNext's own mapping
function, then applies the per-item supply source. Returns
`{"name": "<sales invoice id>"}`.

## `retail_suite.api.fulfillment`

### `create_payment(sales_invoice, mode_of_payment=None, paid_amount=None)`
Records and submits a Payment Entry against a submitted Sales Invoice.
Leave `paid_amount` unset to settle the invoice in full. Pass a smaller
amount to take a **part payment**: the rest stays on the invoice as its
`outstanding_amount` - the customer's debt - and the invoice moves to
ERPNext's `Partly Paid` status. Call it again later, with the balance or
any part of it, to pay more of that debt off; each call produces its own
receipt. Returns
`{"name": "<payment entry id>", "paid_amount": <float>, "payment_status": {...}}`,
where `payment_status` is the same shape `get_payment_status` returns, so
the caller sees the new balance without a second round-trip.

### `get_payment_status(sales_invoice)`
Returns `{"sales_invoice", "currency", "status", "grand_total",
"paid_amount", "outstanding_amount", "customer_outstanding"}`.
`paid_amount` is derived from what is still outstanding, not from
`Sales Invoice.paid_amount` - that field only carries a figure on POS-mode
invoices and stays 0 on these however much has been received.
`customer_outstanding` is what the customer owes across every submitted
invoice, company-wide, not just this one.

### `create_delivery_note(sales_invoice)`
Creates and submits a Delivery Note covering only the invoice's
`Company Warehouse`-sourced lines. Returns `{"name": "<delivery note id>"}`.

### `create_supplier_deliveries(sales_invoice, delivery_date=None)`
Creates and submits **one Supplier Delivery Order per supplier** on the
invoice's Supplier-sourced lines, each carrying only that supplier's own
items - an invoice mixing three suppliers produces three orders, and three
printouts. Returns
`{"orders": [{"name", "supplier", "supplier_name"}, ...]}`, ordered by
where each supplier first appears on the invoice.

## `retail_suite.api.supplier_delivery`

### `record_availability_confirmation(supplier, showroom, contact_person, phone_number, status, item=None, confirmation_date=None, confirmation_time=None, remarks=None)`
`status` must be `Pending`, `Confirmed`, or `Rejected`. Returns
`{"name": "...", "status": "..."}`. Submits the confirmation immediately.

### `create_supplier_delivery_order(sales_invoice, supplier_availability_confirmation, delivery_date, customer_address=None, remarks=None)`
Requires the referenced confirmation to be submitted and `Confirmed`.
Returns `{"name": "<supplier delivery order id>"}`. Never includes
pricing.

## Errors you'll actually see

- `"Required area must be greater than zero."` - bad input to the
  calculation engine.
- `"You do not have access to showroom {0}."` - a restricted user tried to
  act on (or the client sent) a showroom they aren't assigned to.
- `"Select a supply source (Company Warehouse or Supplier) for item {0}."`
  - missing/invalid `supply_source` on a Sales Invoice line.
- `"Supplier availability confirmation is required before creating a
  supplier delivery for item {0}."` - tried to submit a Supplier-sourced
  Sales Invoice line with no Confirmed confirmation on record.
- `"Supplier availability confirmation is required before creating a
  supplier delivery order."` - the confirmation passed to
  `create_supplier_delivery_order` isn't submitted/Confirmed.
- `"Payment amount must be greater than zero."` - `create_payment` was
  given a `paid_amount` of 0 or less. Taking no payment at all isn't a
  payment: just don't call `create_payment`, and the whole invoice stands
  as the customer's debt.
- `"Payment amount {0} is more than the outstanding amount {1} on Sales
  Invoice {2}."` - `create_payment` was asked to take more than is still
  owed on the invoice.
- `"Sales Invoice {0} has no items sourced from supplier {1}."` - a
  Supplier Delivery Order was requested for a supplier that has no lines
  on that invoice.
