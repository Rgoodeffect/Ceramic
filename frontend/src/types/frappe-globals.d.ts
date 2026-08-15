export {};

declare global {
	interface Window {
		// Provided by ERPNext Desk at runtime; not typed further here since
		// this app only ever reads the small subset of boot info it needs
		// (see stores/session.ts / api/session.ts), and the source of truth
		// for showroom/permission data is always the server API, never boot.
		frappe: Record<string, unknown>;
	}
}
