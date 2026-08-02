<template>
	<div class="flex h-screen flex-col bg-gray-50 text-gray-900">
		<header class="flex items-center justify-between border-b border-gray-200 bg-white px-6 py-3 shadow-sm">
			<h1 class="text-lg font-semibold">{{ t("Ceramic Showroom POS") }}</h1>
			<ShowroomBanner />
		</header>

		<main v-if="session.loaded && session.canSell" class="flex flex-1 overflow-hidden">
			<section class="flex w-2/3 flex-col overflow-hidden border-r border-gray-200 bg-white">
				<ProductSearchBar />
				<ProductGrid @add="openAddDialog" />
			</section>
			<section class="flex w-1/3 flex-col gap-4 overflow-y-auto p-4">
				<CustomerPanel />
				<CartPanel />
				<CheckoutPanel />
			</section>
		</main>

		<main v-else-if="session.loaded" class="flex flex-1 items-center justify-center p-6">
			<div class="max-w-md rounded-lg border border-amber-300 bg-amber-50 p-6 text-center">
				<p class="text-amber-800">
					{{
						session.loadError ||
						t(
							"Your user does not have a showroom assigned. Ask your administrator to set a Default Showroom on your User record.",
						)
					}}
				</p>
				<ShowroomPicker v-if="session.isUnrestricted" />
			</div>
		</main>

		<main v-else class="flex flex-1 items-center justify-center">
			<LoadingIndicator class="h-6 w-6 text-gray-400" />
		</main>

		<AddToCartDialog v-if="activeItem" :item="activeItem" @close="activeItem = null" />
	</div>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { LoadingIndicator } from "frappe-ui";
import { t } from "@/utils/translate";
import { useSessionStore } from "@/stores/session";
import type { PosItem } from "@/types";
import ShowroomBanner from "@/components/ShowroomBanner.vue";
import ShowroomPicker from "@/components/ShowroomPicker.vue";
import ProductSearchBar from "@/components/ProductSearchBar.vue";
import ProductGrid from "@/components/ProductGrid.vue";
import CustomerPanel from "@/components/CustomerPanel.vue";
import CartPanel from "@/components/CartPanel.vue";
import CheckoutPanel from "@/components/CheckoutPanel.vue";
import AddToCartDialog from "@/components/AddToCartDialog.vue";

const session = useSessionStore();
const activeItem = ref<PosItem | null>(null);

function openAddDialog(item: PosItem) {
	activeItem.value = item;
}

onMounted(() => {
	session.load();
});
</script>
