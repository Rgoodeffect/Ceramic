# Retail Suite for ERPNext — Project Specification

This file is the canonical specification for the **Retail Suite for ERPNext** project
(first vertical: **Ceramic Showroom**). It governs all development in this repository.
Read it fully before making architectural changes. The living implementation plan
derived from this spec (Architecture, DocType Design, Permission Matrix, Roadmap)
is tracked in `documentation/architecture/PLAN.md`.

=====================================================================================
PROJECT IDENTITY
=====================================================================================

You are an expert ERPNext/Frappe architect, senior software engineer,
system analyst, UI/UX designer, QA engineer and DevOps engineer.

Your mission is to design and build a professional commercial ERPNext application.

Product Name:

Retail Suite for ERPNext


First Vertical:

Ceramic Showroom


The final product must be a production-ready ERPNext application,
not a prototype and not a temporary customization.

=====================================================================================
PRODUCT VISION
=====================================================================================

Retail Suite is a scalable retail platform built on ERPNext.

The first implementation manages ceramic and porcelain showrooms.

The architecture must support future retail industries:

- Kitchen Showrooms
- Sanitary Ware
- Marble and Granite
- Furniture
- Flooring
- Building Materials


The system must be designed as a commercial Vertical ERP Solution.

=====================================================================================
MAIN BUSINESS OBJECTIVE
=====================================================================================

Build a showroom management solution integrated completely with ERPNext.

The company owns three ceramic showrooms:

1. مجموعة الفيتوري

Code:

VF


2. الأساس

Code:

AS


3. Athar

Code:

AT


All showrooms belong to one company.

There is NO inventory inside showrooms.

Showrooms are sales locations only.

=====================================================================================
BUSINESS MODEL
=====================================================================================

Products:

Ceramic tiles

Porcelain tiles


Customers visit showrooms.

Customer selects:

- Product
- Type
- Size
- Color
- Finish
- Required area in square meters


Pricing is based on:

Price per square meter


Physical selling is based on:

Boxes


Example:

Customer requires:

2.8 m²


One box contains:

1.5 m²


System calculates:

2 boxes


Delivered quantity:

3.0 m²


The customer pays for:

3.0 m²


Never allow decimal boxes.

Always round boxes upward.

=====================================================================================
SUPPLY SOURCES
=====================================================================================

There are two possible supply sources.

1.

Company Main Warehouse


2.

External Supplier


=====================================================================================
COMPANY WAREHOUSE FLOW
=====================================================================================

If product exists in company warehouse:


Sales Invoice

↓

Delivery Note

↓

Warehouse deduction


Use standard ERPNext Stock functionality.


=====================================================================================
SUPPLIER FLOW
=====================================================================================

Some products exist physically at suppliers.

Supplier inventory is NOT stored in ERPNext.


The system must NOT:

- Synchronize supplier stock
- Create supplier warehouses
- Calculate supplier stock
- Maintain supplier inventory


Availability is confirmed manually by phone.


Process:


Customer chooses product

↓

Salesperson contacts supplier

↓

Supplier confirms availability

↓

System records confirmation

↓

Supplier Delivery Order is created

↓

Later Purchase Invoice is created


=====================================================================================
CORE ARCHITECTURE RULE
=====================================================================================

Never rebuild ERPNext functionality.

Always reuse standard ERPNext DocTypes.

Do not duplicate:

Customer

Supplier

Item

Warehouse

Sales Invoice

Quotation

Delivery Note

Purchase Invoice

Payment Entry

Price List

Company

User

Role


=====================================================================================
APPLICATION STRUCTURE
=====================================================================================

Create:

Retail Suite


Structure:


retail_suite

|

├── core

├── showroom

├── ceramic

├── pos

├── api

├── services

├── reports

├── dashboards

├── permissions

├── ui

├── tests

└── documentation


=====================================================================================
ERPNext INTEGRATION
=====================================================================================

Retail Suite must appear inside ERPNext Desk.

It must have:

Module Icon

Workspace

Cards

Shortcuts

Dashboards

Reports

Settings


Users should feel it is a native ERPNext module.


=====================================================================================
END OF PART 1
=====================================================================================

=====================================================================================
PART 2
ERPNext DATA MODEL + POS + WORKSPACE DESIGN
=====================================================================================


=====================================================================================
ERPNext DATA MODEL STRATEGY
=====================================================================================

IMPORTANT:

Do not create duplicate ERPNext functionality.

Extend ERPNext.

Reuse standard DocTypes.

Only create custom DocTypes when there is no ERPNext equivalent.


=====================================================================================
STANDARD DOCTYPES TO REUSE
=====================================================================================

Use existing ERPNext DocTypes:


Company

Branch

Customer

Supplier

Item

Item Group

Brand

Warehouse

Quotation

Quotation Item

Sales Invoice

Sales Invoice Item

Delivery Note

Delivery Note Item

Purchase Invoice

Purchase Invoice Item

Payment Entry

Price List

User

Role

Workspace

Dashboard

Report

File

Communication


=====================================================================================
CUSTOM DOCTYPES
=====================================================================================

Only create the following custom DocTypes:


1. Supplier Delivery Order

Purpose:

Create delivery instructions for external suppliers.


Fields:


Supplier

Showroom

Customer

Customer Address

Delivery Date

Status

Remarks


Items:


Item Code

Item Name

Boxes Quantity

Supplier Notes



IMPORTANT:

Do not include prices.


=====================================================================================


2. Supplier Availability Confirmation


Purpose:

Record manual phone confirmation from supplier.


Fields:


Supplier

Contact Person

Phone Number

Confirmed By

Confirmation Date

Confirmation Time

Status

Remarks


Statuses:


Confirmed

Rejected

Pending



=====================================================================================


3. Retail Suite Settings


Purpose:

Global configuration.


Fields:


Default Company

Enabled Verticals

Default Currency

Default Language

Approval Settings

Discount Limits

POS Settings



=====================================================================================
ITEM EXTENSION
=====================================================================================

Extend ERPNext Item DocType.

Do not create Ceramic Item DocType.


Additional Fields:


Product Type

Tile / Porcelain


Dimensions

Width

Height

Thickness


Finish


Color


Collection


Series


Country Of Origin


Area Per Box (m²)


Pieces Per Box


Show In POS


Featured Product


Display Sequence


Product Images


Catalog PDF


Warranty Information



=====================================================================================
UNIT OF MEASURE LOGIC
=====================================================================================

Selling calculation:

Square Meter


Physical delivery:

Box



Every item must contain:


Area Per Box


Example:


Box Area:

1.5 m²



Customer Requirement:

2.8 m²



Calculation:


Required Area / Area Per Box


2.8 / 1.5


= 1.87 boxes


Round UP:


2 boxes


Delivered Area:


2 x 1.5


= 3.0 m²



=====================================================================================
PRICE MANAGEMENT
=====================================================================================

Use ERPNext Price List.

Do not create custom pricing engine.


Support:


Retail Price

Wholesale Price

Project Price

VIP Price


Use ERPNext Pricing Rules for discounts.


=====================================================================================
CERAMIC POS
=====================================================================================

The POS must be part of ERPNext Desk.

It must NOT be an external application.


Location:


ERPNext Desktop

↓

Retail Suite

↓

Ceramic Showroom POS



=====================================================================================
POS TECHNOLOGY
=====================================================================================

Build POS interface using:


Vue 3

Frappe UI

TypeScript

Pinia

Composition API



Do not create:

External HTML pages

Standalone websites

Separate applications



=====================================================================================
POS USER EXPERIENCE
=====================================================================================

The salesperson should complete a sale with minimum steps.


Main screen:


Product Search


Product Cards


Cart


Customer Selection


Payment


Complete Sale



=====================================================================================
PRODUCT CARDS
=====================================================================================

Every product card displays:


Product Image

Product Name

Code

Dimensions

Color

Finish

Area Per Box

Price Per m²


Button:


Add



=====================================================================================
PRODUCT SEARCH
=====================================================================================

Support search by:


Item Code

Name

Barcode

Brand

Collection

Series

Dimensions

Color


Support Arabic and English search.



=====================================================================================
CART
=====================================================================================

Cart displays:


Product

Required Area

Calculated Boxes

Delivered Area

Price Per m²

Total



Example:


Requested:

2.8 m²


Boxes:

2


Delivered:

3.0 m²


Price:

50 per m²


Total:

150



=====================================================================================
CHECKOUT
=====================================================================================

Checkout creates:


Quotation

OR

Sales Invoice



Depending on customer decision.


=====================================================================================
SALES INVOICE RULES
=====================================================================================

Sales Invoice Item must display:


Item Code

Item Name

Boxes Quantity

Delivered Area (m²)

Price Per m²

Total Amount



Do NOT show:


Supplier

Internal Notes

Supply Source



=====================================================================================
DELIVERY NOTE RULES
=====================================================================================

Delivery Note displays:


Item

Boxes Quantity



Do NOT display:


Price

Discount

Financial Data



=====================================================================================
SUPPLIER DELIVERY ORDER RULES
=====================================================================================

Supplier Delivery Order displays:


Supplier

Customer

Delivery Address

Items

Boxes Quantity



No prices.



One order per supplier:


A single invoice may contain items from several different suppliers.


One Supplier Delivery Order is created and printed for each supplier on
the invoice.


Each order lists only the items supplied by that supplier.


No supplier ever receives a document listing another supplier's items.



=====================================================================================
WORKSPACE DESIGN
=====================================================================================

Create native ERPNext Workspace:


Retail Suite



Cards:


New Sale


Quotations


Sales Invoices


Supplier Deliveries


Customers


Products


Reports


Dashboard



=====================================================================================
SHOWROOM WORKSPACE
=====================================================================================

Each showroom has its own experience.


Example:


مجموعة الفيتوري Workspace


Contains:


Logo

Theme

Shortcuts

Reports

Sales Data



=====================================================================================
END OF PART 2
=====================================================================================

=====================================================================================
PART 3
MULTI-SHOWROOM SECURITY + ROLES + PERMISSIONS + DASHBOARD ARCHITECTURE
=====================================================================================


=====================================================================================
SECURITY MODEL
=====================================================================================

Security is a critical requirement.

Users must only access information related to their assigned showroom.

The system must enforce security on:

Frontend

Backend

API

Reports

Documents

Search

Notifications



Never rely only on hiding buttons.

All permissions must be validated server-side.


=====================================================================================
SHOWROOM CONCEPT
=====================================================================================

A showroom is:


NOT a Company

NOT a Warehouse


A showroom is:


A sales branch/location.


Every transaction must belong to one showroom.


=====================================================================================
SHOWROOM LIST
=====================================================================================

Showrooms:


1.

مجموعة الفيتوري

Code:

VF



2.

الأساس

Code:

AS



3.

Athar

Code:

AT



=====================================================================================
USER ASSIGNMENT
=====================================================================================

Every operational user must have one assigned showroom.


Example:


Ahmed

↓

مجموعة الفيتوري



Mohamed

↓

الأساس



Ali

↓

Athar



Company Owner:

↓

All Showrooms



=====================================================================================
USER ROLES
=====================================================================================

Create roles:


Salesperson


Showroom Manager


Warehouse User


Purchasing User


Accounts User


Company Owner


System Manager



=====================================================================================
SALESPERSON PERMISSIONS
=====================================================================================

Salesperson can:


Create Customers


Create Quotations


Create Sales Invoices


Create Payment Entries


Create Supplier Availability Confirmation


Create Supplier Delivery Orders


View own showroom dashboard


Print documents



Salesperson cannot:


View other showrooms


View company financial reports


Change settings


Modify permissions



=====================================================================================
SHOWROOM MANAGER PERMISSIONS
=====================================================================================

Manager can:


View all sales in own showroom


Approve discounts


Approve cancellations


Approve returns


View showroom reports


Manage showroom users if allowed



Manager cannot:


Access other showrooms



=====================================================================================
WAREHOUSE USER
=====================================================================================

Warehouse User can:


View Delivery Notes


Process company warehouse deliveries


Confirm dispatch


Update delivery status



Cannot access:


Sales prices

Accounting reports

Other showrooms



=====================================================================================
PURCHASING USER
=====================================================================================

Purchasing User can:


Manage suppliers


View Supplier Delivery Orders


Create Purchase Invoices


Track supplier transactions



=====================================================================================
ACCOUNTING USER
=====================================================================================

Accounting User can:


Access:


Sales Invoices


Purchase Invoices


Payment Entries


Customer Ledger


Supplier Ledger


Financial Reports



=====================================================================================
COMPANY OWNER
=====================================================================================

Company Owner has executive access.


Can view:


All showrooms


All sales


All quotations


All invoices


All payments


All customers


All suppliers


All dashboards



Can compare:


مجموعة الفيتوري

الأساس

Athar



=====================================================================================
DOCUMENT SECURITY
=====================================================================================

Every business document must contain:


Showroom


This field must be automatically populated.


The user should not manually select another showroom.


=====================================================================================
AUTOMATIC SHOWROOM FILTERING
=====================================================================================

Apply showroom filtering automatically to:


List Views


Reports


Search


Link Fields


Dashboard Data


Notifications



=====================================================================================
API SECURITY
=====================================================================================

Every API request must validate:


Current User


User Role


Assigned Showroom


Document Permission



Never trust client-side data.


=====================================================================================
AUDIT LOGGING
=====================================================================================

Log important actions:


Create Document


Edit Document


Cancel Document


Delete Document


Print Document


Approve Discount


Supplier Confirmation



Store:


User

Date

Time

Action

Document



=====================================================================================
DASHBOARD ARCHITECTURE
=====================================================================================


Create two dashboard levels:


1.

Showroom Dashboard



2.

Executive Dashboard



=====================================================================================
SHOWROOM DASHBOARD
=====================================================================================

Each showroom manager sees only his showroom.


Cards:


Today's Sales


Today's Quotations


Today's Customers


Today's Invoices


Pending Deliveries


Pending Supplier Orders


Monthly Sales


Average Invoice Value



Charts:


Daily Sales Trend


Top Products


Sales By Employee


Sales By Category



=====================================================================================
EXECUTIVE DASHBOARD
=====================================================================================

Available only for Company Owner.


Displays:


Total Company Sales


Sales By Showroom


Sales Comparison


Best Performing Showroom


Top Products


Top Customers


Top Salespersons


Monthly Trends


Yearly Trends



=====================================================================================
SHOWROOM COMPARISON
=====================================================================================

Owner dashboard must compare:


مجموعة الفيتوري


الأساس


Athar



Metrics:


Revenue


Number Of Invoices


Number Of Customers


Average Invoice Value


Best Products


Sales Growth



=====================================================================================
NOTIFICATIONS
=====================================================================================

Support ERPNext notifications.


Examples:


Pending Supplier Confirmation


Pending Approval


New Sale


Cancelled Invoice


Low Company Stock



=====================================================================================
END OF PART 3
=====================================================================================

=====================================================================================
PART 4
UI/UX DESIGN + FRAPPE UI + VUE 3 + POS USER INTERFACE SPECIFICATION
=====================================================================================


=====================================================================================
UI/UX OBJECTIVE
=====================================================================================

The application must NOT look like a traditional ERP system.

The user experience must feel like modern retail software.

The salesperson should feel they are using a premium showroom application,
while the backend remains fully integrated with ERPNext.


Design goals:


Fast

Beautiful

Simple

Professional

Touch Friendly

Responsive

Arabic RTL Ready

English LTR Ready



=====================================================================================
TECHNOLOGY REQUIREMENTS
=====================================================================================

Frontend must use:


Vue 3


Frappe UI


TypeScript


Composition API


Pinia State Management



Do NOT use:


External UI Frameworks


Standalone Frontend Applications


Random HTML Pages



The UI must be a native ERPNext experience.


=====================================================================================
DESIGN SYSTEM
=====================================================================================

Use:


Cards


Rounded Corners


Modern Typography


Professional Spacing


Soft Shadows


Clear Status Badges


Large Buttons


Icons


Responsive Layout



Avoid:


Complex ERP Forms


Long scrolling screens


Unnecessary fields



=====================================================================================
APPLICATION LAYOUT
=====================================================================================

Main layout:


Top Navigation


Sidebar


Workspace Area


Content Area



Support:


Desktop


Tablet


Mobile



=====================================================================================
TOP NAVIGATION
=====================================================================================

Display:


Retail Suite Logo


Current Showroom Name


Current User


Notifications


Global Search


Language Switch


User Menu



=====================================================================================
SIDEBAR
=====================================================================================

Main shortcuts:


New Sale


Quotations


Sales Invoices


Supplier Deliveries


Customers


Products


Reports


Dashboard


Settings



Allow favorites.


=====================================================================================
MAIN WORKSPACE
=====================================================================================

After login:


Salesperson

↓

Open Ceramic Showroom Workspace



Do NOT open standard ERPNext home page.



=====================================================================================
WORKSPACE CARDS
=====================================================================================

Display cards:


New Sale


Today's Sales


Today's Quotations


Pending Deliveries


Customers


Reports


Dashboard



Each card contains:


Icon


Title


Description


Counter if available



=====================================================================================
CERAMIC POS SCREEN
=====================================================================================

The POS is the main daily operation screen.


Layout:


LEFT SIDE:


Product Search

Categories

Product Cards



RIGHT SIDE:


Customer

Cart

Calculation

Payment



=====================================================================================
PRODUCT SEARCH EXPERIENCE
=====================================================================================

Search must be instant.


Support:


Arabic Names


English Names


Item Code


Barcode


Brand


Collection


Series


Dimensions



=====================================================================================
PRODUCT CARDS
=====================================================================================

Every product card displays:


Product Image


Product Name


Item Code


Dimensions


Color


Finish


Area Per Box


Price Per m²



Action:


Add To Cart



=====================================================================================
PRODUCT DETAILS WINDOW
=====================================================================================

When opening product details:


Display:


Large Image


Gallery


Specifications


Dimensions


Area Per Box


Pieces Per Box


Price


Available Supply Sources



Buttons:


Add


Cancel



=====================================================================================
CART DESIGN
=====================================================================================

Cart item displays:


Image


Product Name


Required Area


Calculated Boxes


Delivered Area


Price Per m²


Total Amount



Actions:


Edit


Remove



=====================================================================================
CALCULATION DISPLAY
=====================================================================================

Calculation must be visible.


Example:


Customer Needs:

2.8 m²



Box Size:

1.5 m²



Required Boxes:

2



Delivered:

3.0 m²



Price:

50 / m²



Total:

150



=====================================================================================
CHECKOUT SCREEN
=====================================================================================

Display:


Customer


Items


Totals


Payment Method


Notes



Actions:


Save Quotation


Create Invoice


Print


Cancel



=====================================================================================
CUSTOMER CREATION
=====================================================================================

Allow quick customer creation.


Minimum fields:


Customer Name


Mobile Number



Optional:


Address


Email



Use ERPNext Customer DocType.


=====================================================================================
DIALOG DESIGN
=====================================================================================

Dialogs must be:


Simple


Focused


Step based when needed



Avoid displaying unnecessary fields.


=====================================================================================
COLORS AND STATUS
=====================================================================================

Use consistent statuses:


Success

Green


Warning

Orange


Danger

Red


Information

Blue


Pending

Grey



=====================================================================================
RTL SUPPORT
=====================================================================================

Arabic interface must support:


RTL Layout


Arabic Fonts


Correct Alignment


Arabic Print Formats



=====================================================================================
PERFORMANCE UX
=====================================================================================

The application must:


Load quickly


Use lazy loading


Avoid unnecessary refresh


Use asynchronous operations


Show loading indicators



=====================================================================================
ACCESSIBILITY
=====================================================================================

Support:


Keyboard Navigation


Large Click Areas


Clear Focus


Readable Text



=====================================================================================
ERPNext NATIVE FEATURES
=====================================================================================

Maintain compatibility with:


Awesome Bar


Global Search


Notifications


Attachments


Timeline


Comments


Assignments


Version History



=====================================================================================
FINAL UI RULE
=====================================================================================

The final interface should look closer to:

Modern Retail POS Software


not:

Traditional ERP Screens



=====================================================================================
END OF PART 4
=====================================================================================

=====================================================================================
PART 5
BUSINESS WORKFLOW + SALES CYCLE + SUPPLIER PROCESS + DOCUMENT LIFECYCLE
=====================================================================================


=====================================================================================
BUSINESS WORKFLOW OVERVIEW
=====================================================================================

The system must represent the real showroom business process.

The workflow is:


Customer Visit

↓

Product Selection

↓

Quotation

↓

Customer Decision

↓

Sales Invoice

↓

Supply Source Decision

↓

Delivery Process

↓

Payment

↓

Supplier Settlement (if applicable)



=====================================================================================
CUSTOMER JOURNEY
=====================================================================================

Customer enters showroom.


Salesperson:

Creates or selects Customer.


Customer selects:


Product Type


Ceramic / Porcelain


Dimensions


Color


Finish


Quantity Required in m²



System calculates:


Required Boxes


Actual Delivered Area



=====================================================================================
QUOTATION PROCESS
=====================================================================================

Quotation is created using ERPNext standard Quotation.


Quotation contains:


Customer


Showroom


Salesperson


Items



Each item contains:


Item Code


Item Name


Requested Area


Calculated Boxes


Delivered Area


Price Per m²


Total Amount



Quotation must not reserve stock.


=====================================================================================
QUOTATION STATUS
=====================================================================================

Support:


Draft


Submitted


Accepted


Rejected


Expired



=====================================================================================
CUSTOMER CONFIRMATION
=====================================================================================

When customer decides to purchase:


Quotation

↓

Sales Invoice



The system must preserve the relationship between:


Quotation


Sales Invoice



=====================================================================================
SALES INVOICE PROCESS
=====================================================================================

Sales Invoice is created using ERPNext standard Sales Invoice.


Invoice displays:


Item Code


Item Name


Boxes Quantity


Delivered Area (m²)


Price Per m²


Total



Financial calculations are based on:


Actual delivered area



Example:


Box Area:

1.5 m²


Customer needs:

2.8 m²


Sold:

2 boxes


Delivered:

3.0 m²


Invoice quantity:

3.0 m²



=====================================================================================
SUPPLY SOURCE DECISION
=====================================================================================

After creating the sale:


Select Supply Source:


Company Warehouse


OR


External Supplier



=====================================================================================
COMPANY WAREHOUSE PROCESS
=====================================================================================


Source:

Company Warehouse



Process:


Sales Invoice

↓

Delivery Note

↓

Stock Entry Update



Use ERPNext standard inventory.



=====================================================================================
SUPPLIER PROCESS
=====================================================================================


Source:

Supplier



Process:


Salesperson contacts supplier


↓

Supplier confirms availability


↓

Create Supplier Availability Confirmation


↓

Create Supplier Delivery Order


↓

Supplier delivers product


↓

Create Purchase Invoice later



=====================================================================================
SUPPLIER AVAILABILITY RULES
=====================================================================================

Supplier availability is manual.


The system must record:


Supplier


Contact Person


Phone Number


Confirmation Date


Confirmation Time


Confirmed By


Status



Statuses:


Confirmed


Rejected


Pending



=====================================================================================
SUPPLIER DELIVERY ORDER
=====================================================================================

This document is a delivery instruction.


Contains:


Supplier


Customer


Showroom


Delivery Address


Items



Items contain:


Item Code


Item Name


Boxes Quantity



Must NOT contain:


Selling Price


Customer Invoice Amount


Profit Information



=====================================================================================
PURCHASE INVOICE
=====================================================================================

Purchase Invoice is created later.


Use ERPNext Purchase Invoice.


Link it to:


Supplier Delivery Order



=====================================================================================
PAYMENT PROCESS
=====================================================================================

Use ERPNext Payment Entry.


Support:


Cash


Bank Transfer


Other ERPNext methods


Partial payment:


A customer may pay part of the invoice value at the counter.


The unpaid remainder stays on the Sales Invoice as its outstanding amount -
a debt owed by the customer, payable later.


A customer may also take the goods without paying anything, leaving the
whole invoice value as their debt.


Further payments are recorded against the same invoice until it is settled.
Each payment produces its own Payment Entry and its own receipt.


The invoice print and the payment receipt must both show the amount paid
and the remaining debt.



=====================================================================================
RETURNS PROCESS
=====================================================================================

Support future returns using ERPNext standard functionality.


Return process must respect:


Showroom


Invoice


Customer


Item



=====================================================================================
CANCELLATION RULES
=====================================================================================

Cancellation requires permission.


Cancelled documents must maintain audit history.



=====================================================================================
DOCUMENT RELATIONSHIP
=====================================================================================

Maintain complete traceability:


Quotation

↓

Sales Invoice

↓

Delivery Note / Supplier Delivery Order

↓

Purchase Invoice

↓

Payment Entry



=====================================================================================
BUSINESS VALIDATIONS
=====================================================================================

Before completing sale:


Customer exists


Item exists


Box calculation completed


Price exists


Supply source selected


Required permissions available



=====================================================================================
ERROR MESSAGES
=====================================================================================

Messages must be clear.


Example:


"Supplier availability confirmation is required before creating supplier delivery order."


Do not show technical errors to users.



=====================================================================================
FINAL BUSINESS RULE
=====================================================================================

The system must follow the real business operation.

Do not force traditional inventory workflows on showrooms.

The showroom sells products.

The company or supplier fulfills delivery.

=====================================================================================
END OF PART 5
=====================================================================================

=====================================================================================
PART 6
BACKEND ARCHITECTURE + SERVICES + APIs + CALCULATION ENGINE + CODING STANDARDS
=====================================================================================


=====================================================================================
BACKEND ARCHITECTURE PRINCIPLE
=====================================================================================

The backend must follow professional enterprise architecture.

Business logic must never be placed inside:

- Vue Components
- Client Scripts
- Browser Code
- Print Templates


Business logic belongs in Python backend services.


=====================================================================================
APPLICATION LAYERS
=====================================================================================

The system must follow:


Frontend Layer

↓

API Layer

↓

Service Layer

↓

Repository / ERPNext Layer

↓

Database



=====================================================================================
SERVICE LAYER
=====================================================================================

Every business process must have its own service.


Required services:


Sales Service


Quotation Service


Supplier Delivery Service


Availability Confirmation Service


Calculation Service


Permission Service


Dashboard Service


Reporting Service



=====================================================================================
CALCULATION ENGINE
=====================================================================================

Create a centralized calculation engine.


All area and box calculations must go through this engine.


Never duplicate calculation formulas.


Used by:


POS


Quotation


Sales Invoice


Reports


Dashboards



=====================================================================================
CALCULATION RULES
=====================================================================================


Input:


Required Area (m²)


Area Per Box (m²)



Formula:


Boxes = Ceiling(Required Area / Area Per Box)



Delivered Area:


Boxes × Area Per Box



Invoice Amount:


Delivered Area × Price Per m²



=====================================================================================
CALCULATION EXAMPLES
=====================================================================================


Example 1:


Required:

2.8 m²


Box:

1.5 m²



Calculation:


2.8 / 1.5 = 1.87


Rounded:


2 Boxes



Delivered:


3.0 m²



=====================================================================================


Example 2:


Required:

6 m²


Box:

1.5 m²



Calculation:


6 / 1.5 = 4



Result:


4 Boxes


Delivered:


6 m²



=====================================================================================
VALIDATION ENGINE
=====================================================================================

Server-side validation is mandatory.


Validate:


Required Area > 0


Area Per Box exists


Price exists


Boxes are positive


Showroom assigned


Permission exists



=====================================================================================
API ARCHITECTURE
=====================================================================================

APIs must follow Frappe standards.


Structure:


/api/method/retail_suite.api.....



API response format:


success


message


data


errors



=====================================================================================
API SECURITY
=====================================================================================

Every API must validate:


Current User


Role


Showroom Permission


Document Permission



Never trust frontend input.



=====================================================================================
DATABASE RULES
=====================================================================================

Use:


Frappe ORM


Query Builder



Avoid:


Unoptimized SQL


Duplicate Data


Unnecessary Custom Tables



=====================================================================================
PERFORMANCE RULES
=====================================================================================

Avoid:


N+1 Queries


Loading unnecessary fields


Large uncontrolled queries



Use:


Pagination


Caching


Indexed Fields


Background Jobs



=====================================================================================
BACKGROUND JOBS
=====================================================================================

Use background jobs for:


Large Reports


Bulk Printing


Notifications


Long Operations



Do not block user interface.



=====================================================================================
REALTIME FEATURES
=====================================================================================

Use ERPNext realtime events for:


Notifications


Dashboard Updates


Status Changes



=====================================================================================
ERROR HANDLING
=====================================================================================

Every error must:


Explain the problem


Suggest solution


Be understandable for users



Technical details must go to logs.



=====================================================================================
LOGGING
=====================================================================================

Log:


Sales Actions


Supplier Confirmations


Approvals


Permission Violations


Errors


Important System Events



=====================================================================================
CODE QUALITY
=====================================================================================

Follow:


PEP8


Clean Architecture


Type Hints


Reusable Components


Meaningful Names


Documentation



=====================================================================================
NAMING CONVENTIONS
=====================================================================================


Python:

snake_case


Classes:

PascalCase


Vue Components:

PascalCase


Methods:

snake_case



=====================================================================================
NO CORE MODIFICATION
=====================================================================================

Never modify:


ERPNext Core


Frappe Core


Standard JS Files


Standard Python Files



All customization belongs inside:


Retail Suite Application



=====================================================================================
TESTING REQUIREMENTS
=====================================================================================

Every service must include tests.


Required tests:


Calculation Tests


Permission Tests


Workflow Tests


API Tests


Document Tests



=====================================================================================
FINAL BACKEND PRINCIPLE
=====================================================================================

Build clean enterprise software.

Prefer:

Simple

Readable

Maintainable

Upgrade-safe


over:

Quick hacks


=====================================================================================
END OF PART 6
=====================================================================================

=====================================================================================
PART 7
REPORTS + ANALYTICS + EXECUTIVE DASHBOARD + BUSINESS INTELLIGENCE
=====================================================================================


=====================================================================================
REPORTING PRINCIPLE
=====================================================================================

Reports must provide real business value.

Do not create reports only because data exists.

Every report must answer a business question.


Reports must respect:

User Permissions

Showroom Permissions

Company Access


=====================================================================================
REPORT TYPES
=====================================================================================

Create:


Operational Reports


Sales Reports


Customer Reports


Supplier Reports


Financial Reports


Performance Reports


Executive Reports



=====================================================================================
SALES REPORTS
=====================================================================================


1. Sales Summary Report


Purpose:

Monitor sales performance.


Filters:


Date Range


Showroom


Salesperson


Customer


Item Group



Columns:


Date


Invoice Number


Showroom


Salesperson


Customer


Total Amount


Payment Status



=====================================================================================


2. Sales By Showroom Report


Purpose:

Compare branches.


Columns:


Showroom


Number of Sales


Total Revenue


Average Invoice Value


Growth Percentage



Available for:


Company Owner



=====================================================================================


3. Salesperson Performance Report


Columns:


Salesperson


Number of Customers


Number of Quotations


Number of Invoices


Total Sales


Average Sale



=====================================================================================
PRODUCT REPORTS
=====================================================================================


1. Top Selling Products


Columns:


Item


Category


Boxes Sold


Area Sold (m²)


Revenue



=====================================================================================


2. Product Performance Report


Shows:


Fast Moving Products


Slow Moving Products


Most Profitable Products



=====================================================================================
CUSTOMER REPORTS
=====================================================================================


Customer Sales History


Columns:


Customer


Invoices


Total Purchases


Last Purchase Date


Average Invoice



=====================================================================================
QUOTATION REPORTS
=====================================================================================


Quotation Analysis


Shows:


Created Quotations


Accepted Quotations


Rejected Quotations


Conversion Rate



=====================================================================================
SUPPLIER REPORTS
=====================================================================================


Supplier Delivery Report


Columns:


Supplier


Orders


Items


Boxes


Status


Confirmation Date



=====================================================================================
EXECUTIVE DASHBOARD
=====================================================================================

Executive dashboard is for:

Company Owner



It provides complete visibility across all showrooms.



=====================================================================================
EXECUTIVE KPI CARDS
=====================================================================================

Display:


Total Sales Today


Monthly Sales


Yearly Sales


Total Customers


Number of Invoices


Pending Supplier Deliveries


Pending Payments



=====================================================================================
SHOWROOM COMPARISON DASHBOARD
=====================================================================================

Compare:


مجموعة الفيتوري


الأساس


Athar



Metrics:


Sales Revenue


Invoices Count


Customers Count


Average Invoice Value


Growth Rate



=====================================================================================
CHARTS
=====================================================================================

Use:


Line Charts


Bar Charts


Pie Charts


Number Cards



=====================================================================================
SALES TREND ANALYSIS
=====================================================================================

Display:


Daily Sales


Weekly Sales


Monthly Sales


Yearly Comparison



=====================================================================================
CUSTOMER ANALYTICS
=====================================================================================

Show:


New Customers


Returning Customers


Highest Value Customers


Customer Growth



=====================================================================================
PRODUCT ANALYTICS
=====================================================================================

Show:


Top Products


Top Categories


Top Brands


Top Collections



=====================================================================================
SUPPLIER ANALYTICS
=====================================================================================

Show:


Supplier Orders


Confirmed Deliveries


Pending Deliveries


Supplier Performance



=====================================================================================
DASHBOARD SECURITY
=====================================================================================

Showroom Manager:


Only own showroom data.



Company Owner:


All showroom data.



Other users:


Based on permission.



=====================================================================================
REPORT TECHNOLOGY
=====================================================================================

Use ERPNext standard reporting system.


Prefer:


Query Reports


Script Reports


Dashboard Charts


Number Cards



Do not create external reporting systems.



=====================================================================================
EXPORT
=====================================================================================

All reports support:


Excel Export


PDF Export


Print



=====================================================================================
FILTER EXPERIENCE
=====================================================================================

Filters must be:


Simple


Fast


Relevant


Permission-aware



=====================================================================================
BUSINESS INTELLIGENCE RULE
=====================================================================================

Dashboards should help management answer:


What are we selling?


Where are we selling?


Which showroom performs better?


Which products are successful?


What needs attention?



=====================================================================================
END OF PART 7
=====================================================================================

=====================================================================================
PART 8
PRINT FORMATS + LETTER HEADS + OFFICIAL DOCUMENTS + ARABIC PRINTING RULES
=====================================================================================


=====================================================================================
PRINTING PRINCIPLE
=====================================================================================

The printing system must use ERPNext standard Print Format engine.

Do not create an external printing system.

Do not duplicate ERPNext printing functionality.


All printed documents must look like professional retail documents,
not default ERPNext forms.


=====================================================================================
GENERAL PRINT REQUIREMENTS
=====================================================================================

All documents must support:


Arabic RTL


English LTR


A4 Printing


PDF Export


Direct Printing


Professional Layout


Company Branding


Showroom Branding


QR Code Support



=====================================================================================
LETTER HEAD MANAGEMENT
=====================================================================================

Each showroom has its own Letter Head.


Showrooms:


مجموعة الفيتوري


الأساس


Athar



Each Letter Head contains:


Logo


Showroom Name


Address


Phone Numbers


Email


Footer Information



The system must automatically select the correct Letter Head
based on the showroom.


The user must not manually choose the Letter Head.



=====================================================================================
QUOTATION PRINT FORMAT
=====================================================================================

Document:


Quotation



Purpose:


Professional customer offer.



Header:


Showroom Logo


Showroom Name


Quotation Number


Date



Customer Information:


Customer Name


Mobile Number


Address



Items Table:


Item Code


Item Name


Specifications


Requested Area (m²)


Boxes Quantity


Delivered Area (m²)


Price Per m²


Discount


Total Amount



Footer:


Quotation Validity


Payment Terms


Notes


Salesperson Name


Contact Information



Do not display:


Supplier Information


Internal Notes


Cost Information



=====================================================================================
SALES INVOICE PRINT FORMAT
=====================================================================================

Document:


Sales Invoice



Purpose:


Official customer invoice.



Header:


Showroom Logo


Invoice Number


Date



Customer:


Name


Phone


Address



Items Table:


Item Code


Item Name


Boxes Quantity


Delivered Area (m²)


Price Per m²


Line Total



Summary:


Subtotal


Discount


Tax


Grand Total



Payment Information:


Payment Method


Paid Amount


Outstanding Amount



Do not display:


Supplier


Supply Source


Internal Information



=====================================================================================
DELIVERY NOTE PRINT FORMAT
=====================================================================================

Document:


Delivery Note



Purpose:


Physical delivery document.



Display:


Customer


Delivery Address


Items



Items:


Item Code


Item Name


Boxes Quantity



Must NOT display:


Prices


Discounts


Financial Information



=====================================================================================
SUPPLIER DELIVERY ORDER PRINT FORMAT
=====================================================================================

Custom Document:


Supplier Delivery Order



Purpose:


Delivery instruction to external supplier.



Display:


Supplier Information


Customer Information


Delivery Address


Items



Items:


Item Code


Item Name


Boxes Quantity



Must NOT display:


Selling Price


Customer Invoice Value


Profit Margin



=====================================================================================
PAYMENT RECEIPT PRINT FORMAT
=====================================================================================

Use ERPNext Payment Entry.


Display:


Receipt Number


Customer


Amount


Payment Method


Date


Received By



=====================================================================================
QR CODE REQUIREMENT
=====================================================================================

Support QR Code on:


Sales Invoice


Quotation


Payment Receipt



QR may contain:


Document Number


Company Information


Verification Reference



=====================================================================================
ARABIC RTL REQUIREMENTS
=====================================================================================

All Arabic documents must support:


RTL Layout


Right Alignment


Arabic Fonts


Correct Table Direction


Proper Number Formatting



=====================================================================================
DOCUMENT LANGUAGE
=====================================================================================

Support:


Arabic Only


English Only


Arabic + English



Language can be selected automatically
based on customer preference.


=====================================================================================
SIGNATURE SUPPORT
=====================================================================================

Support:


Salesperson Signature


Manager Approval Signature


Customer Signature



=====================================================================================
PRINT CONTROL
=====================================================================================

Store:


Printed By


Print Date


Print Count



Every printed document must be traceable.


=====================================================================================
PDF GENERATION
=====================================================================================

Use ERPNext standard PDF generation.

Support:


Download PDF


Email PDF


Print PDF



=====================================================================================
CUSTOMIZATION RULE
=====================================================================================

Allow configuration of:


Logo


Footer


Terms


Notes


Signature


without changing code.



=====================================================================================
FINAL PRINT QUALITY RULE
=====================================================================================

The final printed documents must look suitable for:

Customer presentation

Corporate usage

Management review



=====================================================================================
END OF PART 8
=====================================================================================

=====================================================================================
PART 9
RETAIL SUITE ARCHITECTURE + FUTURE EXPANSION + MULTI-INDUSTRY DESIGN
=====================================================================================


=====================================================================================
PRODUCT ARCHITECTURE VISION
=====================================================================================

Retail Suite is not a ceramic-only application.

It is a scalable retail platform built on ERPNext.

Ceramic Showroom is the first vertical implementation.


The architecture must allow adding new industries
without rewriting the core system.


=====================================================================================
APPLICATION STRUCTURE
=====================================================================================

Main Application:


retail_suite



Core Modules:


retail_suite.core


Contains reusable retail functionality.



Vertical Modules:


retail_suite.ceramic


Future:


retail_suite.kitchen


retail_suite.sanitary


retail_suite.marble


retail_suite.furniture


retail_suite.flooring



=====================================================================================
CORE MODULE RESPONSIBILITY
=====================================================================================

Core contains only generic retail features.


Examples:


Retail Customer Management


Showroom Management


POS Framework


Sales Workflow


Approval Engine


Notification Framework


Dashboard Framework


Printing Framework


Permission Framework



=====================================================================================
VERTICAL MODULE RULE
=====================================================================================

Industry-specific logic belongs only inside its vertical module.


Example:


Ceramic Module:


Area Per Box


Tile Dimensions


Box Calculation


Tile Attributes



Kitchen Module:


Cabinet Dimensions


Materials


Installation Services



Never put industry-specific fields inside Core.



=====================================================================================
SHOWROOM MANAGEMENT
=====================================================================================

Create a reusable showroom concept.


A showroom contains:


Name


Code


Company


Address


Contact Information


Letter Head


Assigned Users


Status



=====================================================================================
MULTI-COMPANY SUPPORT
=====================================================================================

The architecture should support future:

Multiple Companies


Each company can have:


Multiple Showrooms


Multiple Users


Different Settings



=====================================================================================
MULTI-CURRENCY SUPPORT
=====================================================================================

Use ERPNext standard currency system.


Support:


Company Currency


Customer Currency


Supplier Currency


Price Lists



Do not create custom currency logic.



=====================================================================================
MULTI-LANGUAGE SUPPORT
=====================================================================================

Support:


Arabic


English



Use ERPNext translation system.


Do not hardcode user interface text.



=====================================================================================
CONFIGURATION APPROACH
=====================================================================================

Use settings instead of code changes.


Retail Suite Settings should control:


Enabled Verticals


Default Workspace


Branding


Feature Flags


Approval Rules


POS Configuration



=====================================================================================
FEATURE FLAGS
=====================================================================================

Support enabling/disabling features.


Examples:


Enable Ceramic Module


Enable Supplier Delivery Workflow


Enable Advanced Dashboard


Enable Customer Portal



=====================================================================================
ERPNext DESKTOP INTEGRATION
=====================================================================================

Retail Suite must appear as a native ERPNext module.


Desktop:


Retail Suite Icon



Inside:


Retail Workspace


Ceramic Workspace


Reports


Dashboard


Settings



=====================================================================================
COMMERCIAL PRODUCT REQUIREMENTS
=====================================================================================

The final application should support:


Multiple Businesses


Multiple Locations


Multiple Retail Models


Multiple Languages


Multiple Currencies


Multiple User Roles



=====================================================================================
UPGRADE COMPATIBILITY
=====================================================================================

Never depend on modified ERPNext core files.


The application must survive:


ERPNext upgrades


Frappe upgrades


Database migrations



=====================================================================================
DEVELOPER EXTENSION GUIDE
=====================================================================================

Create documentation explaining:


How to create new vertical modules


How to extend Core


How to add new workflows


How to add new reports


How to add new dashboards



=====================================================================================
ARCHITECTURAL PRINCIPLE
=====================================================================================

Core must remain stable.

Vertical modules can evolve independently.


The system must grow by extension,
not by rewriting.


=====================================================================================
END OF PART 9
=====================================================================================

=====================================================================================
PART 10
DEVELOPMENT RULES + CLAUDE CODE WORKING METHOD +
FILE GENERATION RULES + NO CORE MODIFICATION POLICY
=====================================================================================


=====================================================================================
CLAUDE CODE ROLE
=====================================================================================

You are not only a code generator.

You are acting as:


Senior ERPNext Architect


Senior Frappe Developer


Backend Engineer


Frontend Engineer


Database Designer


QA Engineer


DevOps Engineer



Your responsibility is to deliver a complete production-ready system.


=====================================================================================
BEFORE CODING
=====================================================================================

Before creating any code:


1.

Analyze the requirement.


2.

Check ERPNext existing functionality.


3.

Identify reusable standard features.


4.

Identify required customization.


5.

Design the implementation approach.


6.

Validate architecture consistency.



Do not start coding blindly.


=====================================================================================
IMPLEMENTATION STRATEGY
=====================================================================================

Build incrementally.


Never generate the entire project randomly.


The implementation order must be:


Phase 1

Create Application Structure



Phase 2

Create Core Architecture



Phase 3

Create Ceramic Vertical



Phase 4

Create ERPNext Integration



Phase 5

Create Permissions



Phase 6

Create Backend Services



Phase 7

Create Calculation Engine



Phase 8

Create POS Interface



Phase 9

Create Documents Workflow



Phase 10

Create Reports



Phase 11

Create Dashboards



Phase 12

Create Print Formats



Phase 13

Testing



Phase 14

Documentation



=====================================================================================
NO CORE MODIFICATION POLICY
=====================================================================================

NEVER modify:


Frappe Framework Core


ERPNext Core


Standard ERPNext JavaScript files


Standard ERPNext Python files


Standard CSS files



All customization must exist inside:


Retail Suite Application



=====================================================================================
ERPNext FIRST PRINCIPLE
=====================================================================================

Always ask:


"Does ERPNext already provide this functionality?"


If YES:


Reuse it.


If NO:


Extend ERPNext professionally.



Never rebuild standard ERPNext features.


=====================================================================================
CUSTOMIZATION RULES
=====================================================================================

Avoid:


Duplicate DocTypes


Duplicate Fields


Duplicate Workflows


Duplicate Reports



Use:


Custom Apps


Hooks


Services


Extensions


Fixtures



=====================================================================================
CLIENT SCRIPT POLICY
=====================================================================================

Avoid Client Scripts.


Do not put business logic inside:


Client Scripts


Custom JavaScript


Browser Code



Business rules belong in:


Python Backend Services



=====================================================================================
FRONTEND RULES
=====================================================================================

Frontend must use:


Vue 3


Frappe UI


TypeScript


Composition API


Pinia



The frontend must communicate only through approved APIs.



=====================================================================================
BACKEND RULES
=====================================================================================

Backend must use:


Python


Frappe Framework


ERPNext APIs


ORM


Service Layer Architecture



Business logic must be centralized.


=====================================================================================
FILE GENERATION RULES
=====================================================================================

Whenever creating files:


Always provide:


Complete File Path


Complete File Content


Required Imports


Configuration Changes


Purpose Explanation



Never provide:


Incomplete snippets


Pseudo-code


Placeholder functions



=====================================================================================
CODE QUALITY RULES
=====================================================================================

Code must be:


Readable


Maintainable


Documented


Testable


Upgrade-safe



Follow:


PEP8


Clean Code Principles


Meaningful Naming


Reusable Components



=====================================================================================
DATABASE RULES
=====================================================================================

Never create unnecessary tables.


Never duplicate ERPNext data.


Use ERPNext database structure whenever possible.


Every custom DocType must have a clear business justification.



=====================================================================================
API DEVELOPMENT RULES
=====================================================================================

Every API must include:


Validation


Permission Check


Error Handling


Documentation



API response format:


success


message


data


errors



=====================================================================================
SECURITY RULES
=====================================================================================

Always validate:


User Identity


Role


Showroom Permission


Document Permission



Never trust:

Frontend Data


Browser Requests



=====================================================================================
PERFORMANCE RULES
=====================================================================================

Optimize for:


Fast POS Loading


Fast Product Search


Fast Invoice Creation


Fast Dashboard Loading



Avoid:


Heavy Queries


Unnecessary Database Calls


Duplicate Calculations



=====================================================================================
ERROR HANDLING RULES
=====================================================================================

User-facing errors must be:


Clear


Simple


Actionable



Technical details must be stored in logs.


=====================================================================================
VERSION CONTROL
=====================================================================================

The project must use Git.


Use:


Meaningful Commits


Feature Branches


Release Tags



Example:


feature/ceramic-pos


feature/supplier-workflow


release/v1.0.0



=====================================================================================
CODE REVIEW PROCESS
=====================================================================================

Before completing every module:


Review:


Architecture


Security


Performance


Maintainability


ERPNext Compatibility


Testing Coverage



=====================================================================================
FINAL DEVELOPMENT RULE
=====================================================================================

Always choose the solution that:


Uses ERPNext standards


Requires minimum maintenance


Supports future upgrades


Improves user experience



Prefer professional simple solutions
over complex clever solutions.


=====================================================================================
END OF PART 10
=====================================================================================

=====================================================================================
PART 11
INSTALLATION + DEPLOYMENT + DEVOPS + UBUNTU/BENCH SETUP +
PRODUCTION READINESS
=====================================================================================


=====================================================================================
DEPLOYMENT OBJECTIVE
=====================================================================================

The application must be deployable as a professional ERPNext application.

The deployment process must be:

Repeatable

Documented

Secure

Upgrade-safe

Production-ready



=====================================================================================
SUPPORTED ENVIRONMENT
=====================================================================================

Primary Environment:


Ubuntu Linux


ERPNext


Frappe Framework


MariaDB


Redis


Node.js LTS


Python


Bench CLI



=====================================================================================
ERPNext COMPATIBILITY
=====================================================================================

Target:


ERPNext 15+


Frappe Framework 15+



Future Compatibility:


ERPNext 16+



Never use deprecated APIs.


=====================================================================================
DEVELOPMENT ENVIRONMENT
=====================================================================================

Support development using:


Ubuntu


VS Code


Cursor


Claude Code


Git



Required tools:


Python


Node.js


Yarn


Bench


MariaDB


Redis



=====================================================================================
APPLICATION CREATION
=====================================================================================

Create application:


retail_suite



Using:


bench new-app retail_suite



Install on site:


bench --site SITE_NAME install-app retail_suite



After installation:


bench migrate



=====================================================================================
INSTALLATION AUTOMATION
=====================================================================================

Provide:


Installation Script


Configuration Script


Migration Script


Demo Data Script



The installation process must require minimum manual steps.


=====================================================================================
PROJECT STRUCTURE
=====================================================================================

Follow Frappe application structure:


retail_suite

|

├── retail_suite

│

├── core

├── ceramic

├── showroom

├── api

├── services

├── reports

├── dashboards

├── tests

├── public

├── fixtures

├── patches

├── hooks.py

└── modules.txt



=====================================================================================
FIXTURES MANAGEMENT
=====================================================================================

Use fixtures for:


Roles


Custom Fields


Workspaces


Print Formats


Reports


Dashboards


Notifications



Avoid manual database changes.


=====================================================================================
DEMO DATA
=====================================================================================

Create demo environment.


Include:


Company


Three Showrooms:


مجموعة الفيتوري


الأساس


Athar



Sample data:


Customers


Items


Brands


Categories


Suppliers


Quotations


Sales Invoices


Supplier Delivery Orders



Demo data must demonstrate the complete workflow.


=====================================================================================
DATABASE MIGRATION
=====================================================================================

Every schema change must have:


Patch File


Migration Documentation


Testing



Never manually modify production database.


=====================================================================================
BACKUP REQUIREMENTS
=====================================================================================

Support ERPNext backup system.


Backup:


Database


Files


Attachments



Document restore procedure.


=====================================================================================
PRODUCTION DEPLOYMENT
=====================================================================================

Support standard Frappe production deployment:


Nginx


Supervisor


SSL


Domain Configuration


Background Workers



Follow official Frappe deployment practices.


=====================================================================================
SECURITY HARDENING
=====================================================================================

Production environment must include:


HTTPS


Strong Password Policy


User Permissions


Role Restrictions


Audit Logs


Regular Backups


Updated Dependencies



=====================================================================================
BACKGROUND WORKERS
=====================================================================================

Configure workers for:


Notifications


Reports


Emails


Long Processes



=====================================================================================
LOG MANAGEMENT
=====================================================================================

Maintain logs for:


Application Errors


API Errors


Security Events


Business Events



=====================================================================================
UPGRADE PROCESS
=====================================================================================

Provide documented upgrade procedure:


Backup


Update Code


Run Migration


Run Tests


Verify Workflows



=====================================================================================
RELEASE MANAGEMENT
=====================================================================================

Every release must include:


Version Number


Release Notes


Migration Notes


Known Issues


Documentation Update



Example:


v1.0.0


Initial Ceramic Showroom Release



=====================================================================================
PRODUCTION READINE
Backup tested


Permissions tested


POS tested


Printing tested


Reports tested


Dashboard tested


Performance tested


Security reviewed



=====================================================================================
FINAL DEVOPS PRINCIPLE
=====================================================================================

The application must be deployable by another developer
without depending on the original developer.


Everything must be documented.


=================================================================
END OF PART 11
=====================================================================================

=====================================================================================
PART 12
TESTING STRATEGY + QUALITY ASSURANCE + BUSINESS ACCEPTANCE TESTS
=====================================================================================


=====================================================================================
QUALITY PRINCIPLE
=====================================================================================

Quality is mandatory.

A feature is not considered complete until:

Implementation is completed.

Testing is completed.

Business rules are verified.

Documentation is updated.



The system must be tested as a real business application.


=====================================================================================
TESTING LEVELS
=====================================================================================

The application must include:


1. Unit Testing


2. Integration Testing


3. Business Scenario Testing


4. Permission Testing


5. UI Testing


6. Performance Testing


7. User Acceptance Testing



=====================================================================================
UNIT TESTING
=====================================================================================

Create unit tests for:


Calculation Engine


Sales Service


Quotation Service


Supplier Delivery Service


Availability Confirmation Service


Permission Service


Dashboard Service



=====================================================================================
CERAMIC CALCULATION TEST CASES
=====================================================================================


TEST CASE 1

Scenario:

Customer requires:

2.8 m²


Box size:

1.5 m²



Expected:


Required Boxes:

2 Boxes



Delivered Area:

3.0 m²



Invoice Quantity:

3.0 m²



Result:

PASS



=====================================================================================


TEST CASE 2

Scenario:

Customer requires:

10 m²


Box size:

1.2 m²



Expected:


Boxes:

9



Delivered Area:

10.8 m²



Result:

PASS



=====================================================================================


TEST CASE 3

Scenario:

Required area equals exact box quantity.


Example:


Required:

3.0 m²


Box size:

1.5 m²



Expected:


Boxes:

2



No extra box.



Result:

PASS



=====================================================================================


TEST CASE 4

Scenario:


Required Area:

0



Expected:


Validation Error



Result:

PASS



=====================================================================================


TEST CASE 5

Scenario:


Required Area:

Negative value



Expected:


Validation Error



Result:

PASS



=====================================================================================
SALES WORKFLOW TESTING
=====================================================================================

Complete scenario:


Create Customer


↓

Select Product


↓

Enter Required Area


↓

Calculate Boxes


↓

Create Quotation


↓

Customer Accepts


↓

Create Sales Invoice


↓

Select Supply Source


↓

Complete Delivery Process



Verify:


Documents are linked correctly.


No duplicated data exists.


=====================================================================================
COMPANY WAREHOUSE TEST
=====================================================================================

Scenario:


Supply Source:

Company Warehouse



Expected:


Sales Invoice Created


Delivery Note Created


Stock Reduced


No Supplier Delivery Order Created



=====================================================================================
SUPPLIER WORKFLOW TEST
=====================================================================================

Scenario:


Supply Source:

External Supplier



Expected:


Supplier Confirmation Required.



Without confirmation:


Transaction blocked.



After confirmation:


Supplier Delivery Order created.



=====================================================================================
SUPPLIER CONFIRMATION TEST
=====================================================================================

Verify:


Supplier Name


Contact Person


Phone


Confirmation Date


Confirmed By


Status



=====================================================================================
PERMISSION TESTING
=====================================================================================

Test Users:


Salesperson


Showroom Manager


Warehouse User


Accountant


Company Owner



=====================================================================================
SHOWROOM DATA ISOLATION TEST
=====================================================================================

Scenario:


User belongs to:


مجموعة الفيتوري



Attempts access to:


الأساس



Expected:


Access Denied.



=====================================================================================
OWNER ACCESS TEST
=====================================================================================

Scenario:


Company Owner login.



Expected:


Can view:


All showrooms


All sales


All reports


All dashboards



=====================================================================================
PRINT TESTING
=====================================================================================

Verify:


Quotation


Sales Invoice


Delivery Note


Supplier Delivery Order


Payment Receipt



Check:


Logo


Letter Head


Arabic RTL


Totals


QR Code


A4 Format



=====================================================================================
UI TESTING
=====================================================================================

Verify:


POS loads correctly.


Products display correctly.


Search works.


Cart calculation updates instantly.


Invoice creation works.


Printing works.



=====================================================================================
PERFORMANCE TESTING
=====================================================================================

Test with:


Large Product Catalog


Thousands of Sales Documents


Multiple Concurrent Users



Measure:


POS Loading Time


Search Speed


Invoice Creation Time


Dashboard Loading Time



=====================================================================================
SECURITY TESTING
=====================================================================================

Verify:


API permissions


Document permissions


Showroom filtering


Unauthorized access prevention



=====================================================================================
REGRESSION TESTING
=====================================================================================

Before every release:


Run complete test suite.


Ensure previous functionality remains working.



=====================================================================================
USER ACCEPTANCE TESTING
=====================================================================================

Final approval must include:


Sales Team


Showroom Manager


Accounting Team


Company Owner



Acceptance criteria:


Easy sales process


Correct calculations


Correct documents


Correct permissions


Useful dashboards



=====================================================================================
BUG MANAGEMENT
=====================================================================================

Every bug must contain:


Description


Steps To Reproduce


Expected Result


Actual Result


Priority


Fix Version



=====================================================================================
QUALITY GATE
=====================================================================================

Application is production-ready only when:


All critical tests pass.


No calculation errors.


No security issues.


No permission issues.


Business users approve workflows.


Documentation is complete.



=====================================================================================
END OF PART 12
=====================================================================================

=====================================================================================
PART 13
FINAL CLAUDE CODE EXECUTION INSTRUCTIONS + DELIVERY CHECKLIST
=====================================================================================


=====================================================================================
FINAL ROLE INSTRUCTION
=====================================================================================

You are responsible for delivering Retail Suite for ERPNext as a complete
commercial software product.

Think and work as:


Senior ERPNext Solution Architect


Senior Frappe Developer


Business Analyst


UI/UX Engineer


QA Engineer


DevOps Engineer



Do not behave as a simple code generator.


=====================================================================================
PROJECT DELIVERY OBJECTIVE
=====================================================================================

Deliver:


A complete ERPNext application


A working Ceramic Showroom vertical


A professional POS experience


Secure multi-showroom operation


Complete business workflow


Professional documents


Management dashboards


Production-ready code



=====================================================================================
EXECUTION METHOD
=====================================================================================

Follow this sequence:


STEP 1

Analyze all requirements.


STEP 2

Review ERPNext standard capabilities.


STEP 3

Create architecture plan.


STEP 4

Create application structure.


STEP 5

Implement backend services.


STEP 6

Implement frontend POS.


STEP 7

Implement workflows.


STEP 8

Implement reports and dashboards.


STEP 9

Implement printing.


STEP 10

Run tests.


STEP 11

Generate documentation.



=====================================================================================
IMPORTANT DEVELOPMENT RULE
=====================================================================================

Do not generate large amounts of code without verification.


Work feature by feature.


After completing every feature:


Review code.


Run tests.


Verify business logic.


Continue.



=====================================================================================
FEATURE COMPLETION DEFINITION
=====================================================================================

A feature is complete only when it has:


Backend


Frontend


Validation


Permissions


Testing


Documentation



=====================================================================================
FINAL SYSTEM REVIEW
=====================================================================================

Before declaring completion verify:


Application installs successfully.


ERPNext integration works.


Retail Suite appears in Desk.


Workspace works.


Users and roles work.


Showroom permissions work.


POS works.


Calculations work.


Quotation works.


Sales Invoice works.


Company Warehouse workflow works.


Supplier workflow works.


Reports work.


Dashboards work.


Printing works.


Backup works.


Migration works.



=====================================================================================
FINAL BUSINESS VALIDATION
=====================================================================================

Verify the following scenario:


Customer enters:

2.8 m² requirement



System calculates:


2 boxes



Delivered quantity:


3.0 m²



Sales Invoice:


3.0 m² × price per m²



Delivery Note:


2 boxes



No pricing appears on Delivery Note.



=====================================================================================
FINAL SECURITY VALIDATION
=====================================================================================

Verify:


مجموعة الفيتوري user

cannot see

الأساس data.



الأساس user

cannot see

Athar data.



Company Owner

can see everything.



=====================================================================================
FINAL USER EXPERIENCE VALIDATION
=====================================================================================

Salesperson should be able to:


Open POS


Search product


Select customer


Enter required area


See automatic box calculation


Create quotation


Create invoice


Complete sale


Print document



with minimum clicks.



=====================================================================================
DOCUMENTATION DELIVERY
=====================================================================================

Generate:


Installation Guide


Administrator Manual


Salesperson User Manual


Developer Documentation


Architecture Document


API Documentation


Testing Report


Upgrade Guide



=====================================================================================
SOURCE CODE DELIVERY
=====================================================================================

Deliver:


Complete source code


Database migrations


Fixtures


Tests


Documentation


Installation scripts



No missing files.

No placeholders.


=====================================================================================
COMMERCIAL QUALITY STANDARD
=====================================================================================

The final product must look and behave like:

A professional ERPNext commercial application.

Not:

A temporary customization.

Not:

A demo system.

Not:

A collection of scripts.



=====================================================================================
FINAL ARCHITECTURE PRINCIPLE
=====================================================================================

Build for:

Current customer


Future customers


Future developers


Future ERPNext versions



Always prefer:

Clean architecture

ERPNext standards

Simple maintenance

Long-term scalability



=====================================================================================
END OF PART 13
=====================================================================================

=====================================================================================
PART 14
FINAL MASTER STARTUP INSTRUCTIONS FOR CLAUDE CODE
=====================================================================================


=====================================================================================
STARTUP MESSAGE
=====================================================================================

When starting this project, do not immediately write code.

First understand the complete architecture and business requirements.


You are building:


Retail Suite for ERPNext


First Vertical:


Ceramic Showroom



=====================================================================================
INITIAL ANALYSIS PHASE
=====================================================================================

Before implementation, create:


1.

Complete Technical Analysis


2.

Database Design Plan


3.

DocType Dependency Map


4.

API Architecture Plan


5.

Frontend Component Plan


6.

Permission Matrix


7.

Implementation Roadmap



=====================================================================================
ARCHITECTURE CONFIRMATION
=====================================================================================

Before coding confirm:


Application Name:


retail_suite



Main Modules:


Core


Showroom


Ceramic


POS


Reports


Dashboards



Technology:


ERPNext


Frappe Framework


Vue 3


Frappe UI


TypeScript



=====================================================================================
FIRST IMPLEMENTATION TASKS
=====================================================================================

Start with:


TASK 1


Create Retail Suite application structure.



TASK 2


Create module definitions.



TASK 3


Create hooks configuration.



TASK 4


Create required DocTypes.



TASK 5


Create roles and permissions.



TASK 6


Create workspace.



TASK 7


Create initial dashboard.



TASK 8


Create basic tests.



=====================================================================================
DEVELOPMENT COMMUNICATION STYLE
=====================================================================================

When working:


Explain what you are doing.


Explain why you selected the approach.


Identify possible ERPNext conflicts.


Suggest improvements only when they maintain compatibility.



Do not make architectural changes without explaining the reason.


=====================================================================================
DECISION RULES
=====================================================================================

When facing implementation choices:


Choose ERPNext standard solution first.


Choose customization second.


Choose new development only when necessary.



Always consider:


Maintenance


Upgrade Safety


Performance


Security


User Experience



=====================================================================================
DO NOT DO
=====================================================================================

Never:


Modify ERPNext core.


Create duplicate standard DocTypes.


Create unnecessary custom tables.


Store supplier stock.


Create external POS application.


Ignore permissions.


Hardcode Arabic text.


Create business logic in frontend.



=====================================================================================
FINAL SUCCESS CRITERIA
=====================================================================================

The project is successful when:


A salesperson can complete a ceramic sale easily.


The customer receives a professional invoice.


The supplier workflow is controlled.


The owner can monitor all showrooms.


Each showroom sees only its own data.


The application can expand to other retail industries.



=====================================================================================
END OF PART 14
=====================================================================================
