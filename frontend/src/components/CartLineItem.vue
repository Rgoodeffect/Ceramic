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
			<p v-if="line.is_area_based" class="text-xs text-gray-500">
				{{ t("Required") }} {{ line.required_area_sqm }} {{ t("m²") }} ·
				{{ areaCalculation.boxes }} {{ t("boxes") }} · {{ t("Delivered") }}
				{{ areaCalculation.delivered_area_sqm }} {{ t("m²") }}
			</p>
			<p v-else class="text-xs text-gray-500">
				{{ line.qty }} {{ t(simpleCalculation.uom) }}
			</p>
			<p class="text-xs text-gray-500">
				{{ t(line.supply_source) }}<span v-if="line.supplier"> · {{ line.supplier }}</span>
			</p>
		</div>
		<div class="flex flex-shrink-0 flex-col items-end gap-1">
			<span class="text-sm font-semibold">{{ line.calculation.amount }}</span>
			<button type="button" class="text-xs text-red-500 hover:underline" @click="$emit('remove', line.key)">
				{{ t("Remove") }}
			</button>
		</div>
	</div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { t } from "@/utils/translate";
import type { CalculationPreview, CartLine, SimpleCalculationPreview } from "@/types";

const props = defineProps<{ line: CartLine }>();
defineEmits<{ remove: [key: string] }>();

// line.calculation's shape depends on line.is_area_based (see stores/cart.ts) -
// these narrow it for the template above, which branches on the same flag.
const areaCalculation = computed(() => props.line.calculation as CalculationPreview);
const simpleCalculation = computed(() => props.line.calculation as SimpleCalculationPreview);
</script>
