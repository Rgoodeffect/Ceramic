import { defineStore } from "pinia";
import { previewRow } from "@/api/calculation";
import type { CartLine, CustomerRef, PosItem, SupplySource } from "@/types";
import { useSessionStore } from "./session";

let nextKey = 1;

export const useCartStore = defineStore("cart", {
	state: () => ({
		customer: null as CustomerRef | null,
		lines: [] as CartLine[],
	}),
	getters: {
		grandTotal: (state): number =>
			state.lines.reduce((sum, line) => sum + line.calculation.amount, 0),
		isEmpty: (state): boolean => state.lines.length === 0,
	},
	actions: {
		setCustomer(customer: CustomerRef | null) {
			this.customer = customer;
		},
		/** Runs the same CalculationService the backend uses (via
		 * api/calculation.previewRow) so the cart always shows the exact
		 * numbers the saved document will have - see spec Part 6:
		 * "Calculation Engine ... Used by POS". */
		async addItem(item: PosItem, requiredAreaSqm: number, supplySource: SupplySource) {
			const session = useSessionStore();
			const calculation = await previewRow(item.item_code, requiredAreaSqm, session.priceList);
			this.lines.push({
				key: `line-${nextKey++}`,
				item,
				required_area_sqm: requiredAreaSqm,
				supply_source: supplySource,
				calculation,
			});
		},
		async updateRequiredArea(key: string, requiredAreaSqm: number) {
			const line = this.lines.find((l) => l.key === key);
			if (!line) return;
			const session = useSessionStore();
			line.calculation = await previewRow(line.item.item_code, requiredAreaSqm, session.priceList);
			line.required_area_sqm = requiredAreaSqm;
		},
		removeLine(key: string) {
			this.lines = this.lines.filter((line) => line.key !== key);
		},
		clear() {
			this.customer = null;
			this.lines = [];
		},
	},
});
