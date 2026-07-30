import { fileURLToPath, URL } from "node:url";
import vue from "@vitejs/plugin-vue";
import frappeui from "frappe-ui/vite";
import { defineConfig } from "vite";

// The POS is embedded inside a Frappe Page (Desk), not served as a
// standalone website route, so frappeui's own buildConfig/jinjaBootData
// plugins (which assume a `www/<route>.html` target) are disabled and the
// output config is set explicitly below. Fixed (non-hashed) asset names let
// the Page controller (retail_suite_core/page/ceramic_pos/ceramic_pos.js)
// reference the bundle by a stable URL via frappe.require().
export default defineConfig({
	plugins: [
		frappeui({
			frappeProxy: true,
			lucideIcons: true,
			jinjaBootData: false,
			buildConfig: false,
		}),
		vue(),
	],
	resolve: {
		alias: {
			"@": fileURLToPath(new URL("./src", import.meta.url)),
		},
	},
	build: {
		outDir: "../retail_suite/public/frontend",
		emptyOutDir: true,
		sourcemap: true,
		rollupOptions: {
			// IIFE (not the Vite default of ES modules) because the Page
			// controller loads this file with frappe.require(), which injects
			// a plain <script src> tag - a module-format bundle's bare
			// import/export syntax would fail there. IIFE also can't code
			// split, which is fine: we want exactly one script for
			// frappe.require() to load.
			output: {
				format: "iife",
				entryFileNames: "ceramic_pos.js",
				assetFileNames: (assetInfo) =>
					assetInfo.name && assetInfo.name.endsWith(".css")
						? "ceramic_pos.css"
						: "ceramic_pos-[name][extname]",
			},
		},
	},
	base: "/assets/retail_suite/frontend/",
});
