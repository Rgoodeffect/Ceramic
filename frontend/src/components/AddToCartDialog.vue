<template>
	<Dialog v-model="open" :options="{ title: item.item_name, size: 'md' }" @close="emit('close')">
		<template #body-content>
			<div class="space-y-4">
				<div>
					<label class="mb-1 block text-sm font-medium text-gray-700">Required Area (m²)</label>
					<input
						v-model.number="requiredArea"
						type="number"
						min="0"
						step="0.01"
						class="w-full rounded border border-gray-300 px-3 py-2 text-sm"
						@input="onAreaInput"
					/>
				</div>

				<div>
					<label class="mb-1 block text-sm font-medium text-gray-700">Supply Source</label>
					<select v-model="supplySource" class="w-full rounded border border-gray-300 px-3 py-2 text-sm">
						<option value="Company Warehouse">Company Warehouse</option>
						<option value="Supplier">Supplier</option>
					</select>
					<p class="mt-1 text-xs text-gray-400">Only used if this line becomes part of a Sales Invoice.</p>
				</div>

				<div v-if="loading" class="flex justify-center py-4">
					<LoadingIndicator class="h-5 w-5 text-gray-400" />
				</div>
				<p v-else-if="error" class="text-sm text-red-600">{{ error }}</p>
				<div v-else-if="preview" class="rounded-lg bg-gray-50 p-4 text-sm">
					<div class="flex justify-between py-0.5">
						<span class="text-gray-500">Box Size</span>
						<span>{{ preview.area_per_box }} m²</span>
					</div>
					<div class="flex justify-between py-0.5">
						<span class="text-gray-500">Required Boxes</span>
						<span>{{ preview.boxes }}</span>
					</div>
					<div class="flex justify-between py-0.5">
						<span class="text-gray-500">Delivered Area</span>
						<span>{{ preview.delivered_area_sqm }} m²</span>
					</div>
					<div class="flex justify-between py-0.5">
						<span class="text-gray-500">Price</span>
						<span>{{ preview.price_per_sqm }} / m²</span>
					</div>
					<div class="mt-2 flex justify-between border-t border-gray-200 pt-2 font-semibold">
						<span>Total</span>
						<span>{{ preview.amount }}</span>
					</div>
				</div>
			</div>
		</template>
		<template #actions>
			<Button variant="solid" theme="blue" class="w-full" :disabled="!preview || loading" @click="add">
				Add To Cart
			</Button>
		</template>
	</Dialog>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { Button, Dialog, LoadingIndicator, debounce } from "frappe-ui";
import { previewRow } from "@/api/calculation";
import { useCartStore } from "@/stores/cart";
import { useSessionStore } from "@/stores/session";
import type { CalculationPreview, PosItem, SupplySource } from "@/types";

const props = defineProps<{ item: PosItem }>();
const emit = defineEmits<{ close: [] }>();

const cart = useCartStore();
const session = useSessionStore();

const open = ref(true);
const requiredArea = ref<number>(0);
const supplySource = ref<SupplySource>("Company Warehouse");
const preview = ref<CalculationPreview | null>(null);
const loading = ref(false);
const error = ref("");

async function refreshPreview() {
	if (!requiredArea.value || requiredArea.value <= 0) {
		preview.value = null;
		error.value = "";
		return;
	}
	loading.value = true;
	error.value = "";
	try {
		preview.value = await previewRow(props.item.item_code, requiredArea.value, session.priceList);
	} catch (e) {
		error.value = e instanceof Error ? e.message : String(e);
		preview.value = null;
	} finally {
		loading.value = false;
	}
}

const onAreaInput = debounce(refreshPreview, 300);

async function add() {
	if (!requiredArea.value || !preview.value) return;
	await cart.addItem(props.item, requiredArea.value, supplySource.value);
	open.value = false;
	emit("close");
}

onMounted(refreshPreview);
</script>
