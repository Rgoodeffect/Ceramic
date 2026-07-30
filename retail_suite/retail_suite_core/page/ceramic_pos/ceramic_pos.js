frappe.pages["ceramic-pos"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: "Ceramic Showroom POS",
		single_column: true,
	});

	$("<div id=\"ceramic-pos-app\"></div>").appendTo(page.body);

	// The built Vue 3 + Pinia + Frappe UI SPA (see /frontend) mounts itself
	// into #ceramic-pos-app and talks to the server only through
	// retail_suite's whitelisted API endpoints - no business logic lives in
	// this Page controller, by design (spec Part 6/10: "Client Script
	// Policy"). CSS is embedded in the JS bundle by the build (see
	// frontend/vite.config.ts), so only one asset needs loading here.
	frappe.require("/assets/retail_suite/frontend/ceramic_pos.js");
};
