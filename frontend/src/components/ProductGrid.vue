<template>
	<div class="flex-1 overflow-y-auto p-4">
		<div v-if="catalog.loading" class="flex justify-center py-10">
			<LoadingIndicator class="h-6 w-6 text-gray-400" />
		</div>
		<p v-else-if="catalog.error" class="text-sm text-red-600">{{ catalog.error }}</p>
		<p v-else-if="catalog.searched && catalog.items.length === 0" class="text-sm text-gray-500">
			{{ t("No products found.") }}
		</p>
		<div v-else class="grid grid-cols-3 gap-4">
			<ProductCard
				v-for="item in catalog.items"
				:key="item.item_code"
				:item="item"
				@add="(selected) => $emit('add', selected)"
			/>
		</div>
	</div>
</template>

<script setup lang="ts">
import { LoadingIndicator } from "frappe-ui";
import { t } from "@/utils/translate";
import { useCatalogStore } from "@/stores/catalog";
import type { PosItem } from "@/types";
import ProductCard from "@/components/ProductCard.vue";

defineEmits<{ add: [item: PosItem] }>();
const catalog = useCatalogStore();
</script>
