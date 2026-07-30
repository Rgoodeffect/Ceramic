import { call } from "frappe-ui";
import type { ApiEnvelope } from "@/types";

/** Raised when a retail_suite API call succeeds at the HTTP level but its
 * envelope reports success: false (an expected, user-facing validation or
 * permission error - see retail_suite/api/utils.py). */
export class ApiError extends Error {}

/** Call one of retail_suite's whitelisted endpoints and unwrap its uniform
 * {success, message, data, errors} envelope, throwing ApiError with the
 * server's clear message on failure. Never call frappe-ui's `call()`
 * directly against a retail_suite.api.* method outside of this helper. */
export default async function invoke<T>(
	method: string,
	args: Record<string, unknown> = {},
): Promise<T> {
	const envelope = (await call(method, args)) as ApiEnvelope<T>;
	if (!envelope.success) {
		throw new ApiError(envelope.message || "Request failed.");
	}
	return envelope.data as T;
}
