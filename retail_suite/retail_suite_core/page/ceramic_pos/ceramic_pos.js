frappe.pages["ceramic-pos"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Ceramic Showroom POS"),
		single_column: true,
	});

	$("<div id=\"ceramic-pos-app\"></div>").appendTo(page.body);

	// frappe-ui's request helper (used by the bundle below for every API
	// call) only attaches the CSRF header when `window.csrf_token` is set -
	// a standalone frappe-ui app gets that from its own jinja-rendered
	// index.html, which this Page intentionally has none of (jinjaBootData
	// is disabled in frontend/vite.config.ts, since this mounts inside Desk
	// instead of as its own route). Desk itself only exposes the same token
	// as `frappe.csrf_token`, a different global, so without this line every
	// call the bundle makes fails with CSRFTokenError - caught by actually
	// loading this page in a browser, not by any static check.
	window.csrf_token = frappe.csrf_token;

	// The built Vue 3 + Pinia + Frappe UI SPA (see /frontend) mounts itself
	// into #ceramic-pos-app and talks to the server only through
	// retail_suite's whitelisted API endpoints - no business logic lives in
	// this Page controller, by design (spec Part 6/10: "Client Script
	// Policy"). CSS is embedded in the JS bundle by the build (see
	// frontend/vite.config.ts), so only one asset needs loading here.
	frappe.require("/assets/retail_suite/frontend/ceramic_pos.js");
};
