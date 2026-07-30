<template>
	<div class="flex items-start gap-3 border-b border-gray-100 py-3 last:border-0">
		<div class="h-12 w-12 flex-shrink-0 overflow-hidden rounded bg-gray-100">
			<img
				v-if="line.item.image"
				:src="line.item.image"
				:alt="line.item.item_name"
				class="h-full w-full object-cover"
			/>
		</div>
		<div class="min-w-0 flex-1">
			<p class="truncate text-sm font-medium">{{ line.item.item_name }}</p>
			<p class="text-xs text-gray-500">
				Required {{ line.required_area_sqm }} m² · {{ line.calculation.boxes }} boxes · Delivered
				{{ line.calculation.delivered_area_sqm }} m²
			</p>
			<p class="text-xs text-gray-500">{{ line.supply_source }}</p>
		</div>
		<div class="flex flex-shrink-0 flex-col items-end gap-1">
			<span class="text-sm font-semibold">{{ line.calculation.amount }}</span>
			<button type="button" class="text-xs text-red-500 hover:underline" @click="$emit('remove', line.key)">
				Remove
			</button>
		</div>
	</div>
</template>

<script setup lang="ts">
import type { CartLine } from "@/types";

defineProps<{ line: CartLine }>();
defineEmits<{ remove: [key: string] }>();
</script>
