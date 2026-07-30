declare module "frappe-ui/vite" {
	import type { PluginOption } from "vite";

	interface FrappeUIViteOptions {
		frappeProxy?: boolean | Record<string, unknown>;
		lucideIcons?: boolean;
		jinjaBootData?: boolean;
		buildConfig?: boolean | Record<string, unknown>;
		frontendRoute?: string;
	}

	export default function frappeui(options?: FrappeUIViteOptions): PluginOption[];
}
