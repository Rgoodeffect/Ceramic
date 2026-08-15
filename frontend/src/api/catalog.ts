import invoke from "./client";
import type { PosItem } from "@/types";

export function searchItems(
	searchTerm: string,
	priceList: string,
	limit = 20,
): Promise<PosItem[]> {
	return invoke<PosItem[]>("retail_suite.api.catalog.search_items", {
		search_term: searchTerm,
		price_list: priceList,
		limit,
	});
}
