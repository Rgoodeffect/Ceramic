import { defineStore } from "pinia";
import { previewRow, previewSimpleRow } from "@/api/calculation";
import { isAreaBasedItem } from "@/types";
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
		 * api/calculation.previewRow/previewSimpleRow) so the cart always shows
		 * the exact numbers the saved document will have - see spec Part 6:
		 * "Calculation Engine ... Used by POS". `supplier` is required by the
		 * backend when `supplySource` is "Supplier" (validated again at
		 * checkout - see sales_service.validate_supply_sources). `quantity`
		 * means required area (m²) for a ceramic item, or a plain quantity in
		 * the item's own UOM for everything else - see isAreaBasedItem. */
		async addItem(
			item: PosItem,
			quantity: number,
			supplySource: SupplySource,
			supplier: string | null = null,
		) {
			const session = useSessionStore();
			const isAreaBased = isAreaBasedItem(item);
			const calculation = isAreaBased
				? await previewRow(item.item_code, quantity, session.priceList)
				: await previewSimpleRow(item.item_code, quantity, session.priceList);
			this.lines.push({
				key: `line-${nextKey++}`,
				item,
				is_area_based: isAreaBased,
				required_area_sqm: isAreaBased ? quantity : null,
				qty: isAreaBased ? null : quantity,
				supply_source: supplySource,
				supplier: supplySource === "Supplier" ? supplier : null,
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
