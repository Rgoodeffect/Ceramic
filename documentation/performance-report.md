# Performance Report

## Environment and method (read this first)

This was run against the same live Frappe 15 + ERPNext 15 bench used for
the rest of real-bench testing (see `testing-report.md`), inside a single
sandboxed container with no dedicated benchmarking tools available (no
`locust`, `ab`, `wrk`, or `k6`). Two kinds of real measurement were taken
instead:

1. **Server-side latency** for individual operations, called directly
   (`bench execute`), timed with `time.perf_counter()`.
2. **A concurrent HTTP load test** against the live running site, written
   with Python's stdlib `concurrent.futures.ThreadPoolExecutor` and
   `requests` (a real client hitting a real running `bench serve` process
   over HTTP, not a mocked call).

**This is not a production capacity benchmark, and the numbers below
should not be read as one.** `bench serve` runs Frappe's built-in
Werkzeug development server - threaded, but a single OS process with no
multi-worker fan-out - on a resource-constrained, shared sandbox VM. A
real deployment follows Frappe's standard production setup (`bench setup
production`: Nginx in front of `gunicorn` with multiple worker processes,
plus Redis/MariaDB tuned for the host), which this environment cannot
stand up. What these numbers *do* show, honestly: the app's own
queries/logic hold up correctly under a realistic data volume and don't
error or fall over under load, and roughly where a single dev-server
process's ceiling sits - useful signal, not a sizing guarantee.

## Data volume

Seeded on top of the existing demo data, using the app's own
`sales_service.create_sales_invoice` (i.e. every one of these documents
went through the real `validate`/`before_submit` hooks, not raw SQL
inserts):

| | Count |
|---|---|
| Items (`custom_show_in_pos = 1`) | 121 |
| Sales Invoices (submitted) | 498 |
| Sales Invoice Items | ~500+ |

450 invoices were created back-to-back through the real service layer at
**3.4-3.5 invoices/sec sustained** (130s for 450, zero errors) - each one
running full showroom-lock validation, the Calculation Engine, and supply
source validation. That rate held flat across the whole run (no slowdown
as row counts grew), which is a good sign against N+1-style degradation
in the write path specifically.

## Single-request server-side latency

5 repeated calls per operation (3 for the report), `frappe.clear_cache()`
between each to avoid the numbers being flattered by cross-call caching:

| Operation | avg | min | max |
|---|---|---|---|
| POS search - empty query (full grid, 121 items) | 153.8ms | 133.6ms | 210.0ms |
| POS search - `"Milano"` | 132.5ms | 127.4ms | 139.5ms |
| POS search - `"Perf"` (100+ matches) | 148.3ms | 138.9ms | 169.6ms |
| Dashboard Number Card - Today's Sales | 193.0ms | 166.2ms | 230.1ms |
| Dashboard Number Card - Pending Deliveries | 166.9ms | 160.6ms | 174.5ms |
| Sales Summary Report (Company Owner, all 498 invoices) | 5.6ms | 4.4ms | 7.8ms |
| `frappe.get_list` Sales Invoice, restricted Salesperson | 173.9ms | 161.8ms | 186.4ms |

All comfortably inside the spec's "Fast POS Loading, Fast Product
Search" intent for a single interactive request - these are `bench
execute` timings (Python process + ORM + DB round trip, no HTTP/network
layer), so real end-user latency adds HTTP/session overhead on top, but
not enough to change the picture. The showroom-restricted `get_list` call
correctly returned **166 of 498** invoices for a Salesperson scoped to
one showroom - confirms the `permission_query_conditions` filtering is
still doing its job under volume, not just in the 2-3-row test fixtures.

## Concurrent HTTP load test

Real HTTP requests against the live site's POS search endpoint
(`retail_suite.api.catalog.search_items`), authenticated sessions,
varying concurrency:

| Concurrent users | Requests | Wall time | Throughput | p50 | p95 | p99 | Errors |
|---|---|---|---|---|---|---|---|
| 5 | 50 | 1.21s | 41.2 req/s | 122ms | 196ms | 233ms | 0 |
| 20 | 200 | 5.45s | 36.7 req/s | 457ms | 1731ms | 1795ms | 0 |
| 40 | 400 | 9.54s | 41.9 req/s | 959ms | 1427ms | 1703ms | 0 |

**Zero HTTP errors at every concurrency level** - no 500s, no timeouts,
no dropped connections, across 650 total requests. Throughput plateaus at
roughly **37-42 req/s regardless of concurrency** (20 users isn't faster
than 5, and 40 isn't faster than 20) while p50/p95 latency climbs
sharply with concurrency - the textbook signature of a single-process
server's request queue saturating, not of a query getting slower or a
lock getting worse as data grows. That ceiling is a property of `bench
serve`'s single-process dev server on this sandbox's CPU allocation, not
of `retail_suite`'s code - a production `gunicorn` deployment with
several worker processes would raise it roughly in proportion to worker
count, since each worker gets its own DB connection and Python
interpreter.

**Practical read for this app's real usage pattern**: three showrooms
means realistically 3-6 concurrent salespeople hitting the POS at once,
not 40 - the 5-concurrent-user numbers (p50 122ms, p95 196ms) are the
relevant ones, and they're comfortably fast.

## What this does and doesn't establish

Established:
- No errors, crashes, or query blow-ups under 498 real invoices and 121
  items, created through the real validation/hook path.
- Individual operations (search, dashboard, report, permission-filtered
  list) all respond in well under a quarter-second server-side.
- The showroom permission filter is doing real work under volume, not
  just passing tiny test fixtures.
- No obvious N+1 query degradation as data grew during the 450-invoice
  seeding run (rate stayed flat throughout).

Not established (out of scope for this environment):
- Behavior at production data scale (thousands of items, tens of
  thousands of invoices, years of history).
- Real concurrent-user capacity under a production `gunicorn`/`nginx`
  deployment - only a single-process dev server ceiling was measured.
- Database performance under production hardware, connection pooling, or
  MariaDB tuning.
- Sustained/soak testing (this was single load bursts, not hours of
  continuous traffic).

A real pre-launch capacity test should repeat the same method described
above (a `ThreadPoolExecutor` + `requests` HTTP load test at a few
concurrency levels, plus `bench execute`-timed single-operation latency)
against an actual `bench setup production` deployment on the target
hardware - the scripts used here were session scratch files, not part of
this repo, but the approach is a few dozen lines of stdlib Python to
reproduce.
