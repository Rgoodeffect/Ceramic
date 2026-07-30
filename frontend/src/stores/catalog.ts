import { defineStore } from "pinia";
import { searchItems } from "@/api/catalog";
import type { PosItem } from "@/types";
import { useSessionStore } from "./session";

export const useCatalogStore = defineStore("catalog", {
	state: () => ({
		searchTerm: "",
		items: [] as PosItem[],
		loading: false,
		error: "" as string,
		searched: false,
	}),
	actions: {
		async search() {
			const session = useSessionStore();
			this.loading = true;
			this.error = "";
			try {
				this.items = await searchItems(this.searchTerm, session.priceList);
			} catch (e) {
				this.error = e instanceof Error ? e.message : String(e);
				this.items = [];
			} finally {
				this.loading = false;
				this.searched = true;
			}
		},
	},
});
