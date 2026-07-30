<template>
	<div
		class="flex flex-col overflow-hidden rounded-lg border border-gray-200 shadow-sm transition hover:shadow-md"
	>
		<div class="flex aspect-square items-center justify-center bg-gray-100">
			<img
				v-if="item.image"
				:src="item.image"
				:alt="item.item_name"
				class="h-full w-full object-cover"
			/>
			<span v-else class="text-xs text-gray-400">No Image</span>
		</div>
		<div class="flex flex-1 flex-col gap-1 p-3">
			<p class="truncate text-sm font-semibold" :title="item.item_name">{{ item.item_name }}</p>
			<p class="text-xs text-gray-500">{{ item.item_code }}</p>
			<p v-if="specLine" class="text-xs text-gray-500">{{ specLine }}</p>
			<p class="text-xs text-gray-500">Box: {{ item.custom_area_per_box }} m²</p>
			<p class="text-sm font-medium text-gray-900">
				{{ item.price_per_sqm != null ? `${formatNumber(item.price_per_sqm)} / m²` : "No price set" }}
			</p>
			<Button variant="solid" theme="blue" class="mt-auto w-full" @click="$emit('add', item)">
				Add
			</Button>
		</div>
	</div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { Button } from "frappe-ui";
import type { PosItem } from "@/types";

const props = defineProps<{ item: PosItem }>();
defineEmits<{ add: [item: PosItem] }>();

const specLine = computed(() => {
	const { custom_width, custom_height, custom_thickness, custom_color, custom_finish } = props.item;
	const parts: string[] = [];
	if (custom_width && custom_height) {
		let dims = `${custom_width}x${custom_height}`;
		if (custom_thickness) dims += `x${custom_thickness}`;
		parts.push(`${dims} mm`);
	}
	if (custom_color) parts.push(custom_color);
	if (custom_finish) parts.push(custom_finish);
	return parts.join(" · ");
});

function formatNumber(value: number): string {
	return new Intl.NumberFormat(undefined, { maximumFractionDigits: 2 }).format(value);
}
</script>
