import { defineStore } from "pinia";
import { getSessionContext } from "@/api/session";

export const useSessionStore = defineStore("session", {
	state: () => ({
		showroom: null as string | null,
		priceList: "Standard Selling",
		currency: "USD",
		isUnrestricted: false,
		loaded: false,
		loadError: "" as string,
	}),
	getters: {
		/** The POS can only take a sale once a showroom is known - either
		 * auto-resolved for an operational user, or manually picked by an
		 * unrestricted user (Company Owner/System Manager). */
		canSell: (state) => Boolean(state.showroom),
	},
	actions: {
		async load() {
			this.loadError = "";
			try {
				const context = await getSessionContext();
				this.showroom = context.showroom;
				this.priceList = context.price_list || this.priceList;
				this.currency = context.currency || this.currency;
				this.isUnrestricted = context.is_unrestricted;
			} catch (e) {
				this.loadError = e instanceof Error ? e.message : String(e);
			} finally {
				this.loaded = true;
			}
		},
		/** Only reachable for an unrestricted user - see canSell/ShowroomBanner. */
		setManualShowroom(showroom: string) {
			this.showroom = showroom;
		},
	},
});
