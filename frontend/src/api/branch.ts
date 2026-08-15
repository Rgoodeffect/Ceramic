import { call } from "frappe-ui";

export interface BranchRef {
	name: string;
}

/** Only used for the rare unrestricted-user (Company Owner/System Manager)
 * manual showroom picker - operational users always get their showroom
 * auto-resolved server-side (see api/session.ts) and never see this. */
export async function listBranches(): Promise<BranchRef[]> {
	const rows = (await call("frappe.client.get_list", {
		doctype: "Branch",
		filters: [["custom_status", "=", "Active"]],
		fields: ["name"],
		limit_page_length: 50,
	})) as BranchRef[];
	return rows;
}
