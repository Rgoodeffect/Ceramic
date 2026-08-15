# Salesperson User Manual

## Opening the POS

Desk → **Retail Suite** (in the left sidebar) → **New Sale**. Your
showroom is shown at the top - you never need to pick it.

If you see "Your user does not have a showroom assigned," ask your
administrator to set up your account (see the Administrator Manual).

## Making a sale

1. **Search for the product** at the top of the left panel - by name,
   item code, brand, collection, series, or color.
2. **Tap "Add"** on the product card you want.
3. **Enter the required area** in square meters - whatever the customer
   actually needs. The system immediately shows you:
   - Box size
   - How many boxes that rounds up to (always a whole number, never a
     fraction)
   - The actual delivered area (boxes × box size - always slightly more
     than or equal to what was required)
   - Price per m² and the line total
4. **Choose the supply source** for that line: Company Warehouse or
   Supplier. (This only matters if you go straight to an invoice - a
   Quotation doesn't need it yet.)
5. **Tap "Add To Cart."**

Repeat for every product the customer wants.

## Example

Customer needs **2.8 m²** of a tile whose box covers **1.5 m²**:

- Boxes: **2** (2.8 ÷ 1.5 = 1.87, rounded up)
- Delivered: **3.0 m²** (2 × 1.5)
- At 50/m²: customer pays for the full 3.0 m² → **150**

## Customer

- Search by name in the Customer panel, or
- Tap **"New Customer"** - just Name and Mobile Number are required
  (Address and Email are optional).

## Finishing the sale

- **Save Quotation** if the customer isn't ready to buy yet. You can turn
  it into an invoice later once they decide.
- **Create Invoice** to complete the sale now.
- **Print** appears once a document is created - opens the print view in
  a new tab.
- **Cancel** clears the cart without saving anything.

## Taking payment - in full, in part, or later

Once the invoice is created, the Checkout panel shows the invoice total,
what has been paid, and what is still owed.

- **Amount Paid Now** starts filled in with the full remaining balance, so
  a customer paying in full is one tap on **Record Payment**.
- If the customer is only paying part of it, type the smaller amount over
  it and tap **Record Payment**. The rest is shown in red as **Remaining
  Debt** - it stays on the invoice as money the customer owes, and the
  invoice is marked *Partly Paid*.
- If they're paying nothing today, just don't record a payment. The whole
  invoice stands as their debt.
- **Full Amount** puts the whole remaining balance back in the box if you
  typed over it.
- The panel also shows **Total debt for this customer** across all their
  invoices, at every showroom - check it before agreeing to another
  part payment.

The customer can come back and pay more at any time: open the invoice's
POS checkout again and record another payment against it. Each payment
prints its own receipt showing what was paid and what is still owed, and
the invoice printout shows the paid amount and the remaining debt.

## If a product needs to come from a supplier

Before you can invoice a line marked "Supplier," you (or whoever handles
supplier calls) must record that the supplier actually confirmed it's
available:

1. Call the supplier and ask.
2. Record the call: Retail Suite → Supplier Confirmations → New. Fill in
   the supplier, contact person, phone number, and mark it **Confirmed**
   (or Rejected/Pending if that's the outcome).
3. Only after a **Confirmed** record exists for that item and your
   showroom can the invoice for that line be submitted. If you try before
   that, you'll see a clear message telling you exactly what's missing.
4. Once the invoice is submitted, a **Supplier Delivery Order** can be
   created from it, linked to that confirmation. It never shows prices -
   it's a delivery instruction, not a bill.

### Several suppliers on one invoice

One invoice can carry items from more than one supplier. Tapping
**Create Supplier Delivery Orders** creates a separate order for each
supplier on the invoice, listing only that supplier's own items - three
suppliers on the invoice means three orders, and a **Print Supplier
Delivery Order** button for each, labelled with the supplier's name. No
supplier is ever handed a document listing another supplier's goods.

## What you can and can't see

You only see your own showroom's customers, quotations, invoices, and
deliveries. That's not a preference you can turn off - it's how the
system is built to work, and it applies everywhere (lists, search,
reports), not just the POS.
