/** Thin wrapper around Frappe's global client-side translator.
 *
 * `window.__` is set by Frappe's own core bundle (`frappe/public/js/frappe/
 * translate.js: window.__ = frappe._`) before this Page's script ever runs -
 * see `retail_suite_core/page/ceramic_pos/ceramic_pos.js`. It looks up
 * `frappe.boot.__messages`, populated server-side from every installed
 * app's `translations/<lang>.csv` (this app's own `retail_suite/
 * translations/ar.csv` included) for the current user's language, and
 * falls back to the original English text when no translation exists -
 * exactly the spec's "Use ERPNext translation system. Do not hardcode
 * user interface text" (Part 9), applied to the POS SPA instead of just
 * Desk-rendered forms.
 */
declare global {
	interface Window {
		__?: (text: string, replace?: unknown[], context?: string) => string;
	}
}

export function t(text: string, replace?: unknown[], context?: string): string {
	return window.__ ? window.__(text, replace, context) : text;
}
