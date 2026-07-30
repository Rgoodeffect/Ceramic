import invoke from "./client";
import type { SessionContext } from "@/types";

export function getSessionContext(): Promise<SessionContext> {
	return invoke<SessionContext>("retail_suite.api.session.get_session_context");
}
