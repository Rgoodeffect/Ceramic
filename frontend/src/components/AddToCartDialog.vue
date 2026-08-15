<template>
	<Dialog v-model="open" :options="{ title: item.item_name, size: 'md' }" @close="emit('close')">
		<template #body-content>
			<div class="space-y-4">
				<div>
					<label class="mb-1 block text-sm font-medium text-gray-700">
						{{ isAreaBased ? t("Required Area (m²)") : t("Quantity") + " (" + t(item.stock_uom) + ")" }}
					</label>
					<input
						v-model.number="quantity"
						type="number"
						min="0"
						:step="isAreaBased ? 0.01 : 1"
						class="w-full rounded border border-gray-300 px-3 py-2 text-sm"
						@input="onQuantityInput"
					/>
				</div>

				<div>
					<label class="mb-1 block text-sm font-medium text-gray-700">{{ t("Supply Source") }}</label>
					<select v-model="supplySource" class="w-full rounded border border-gray-300 px-3 py-2 text-sm">
						<option value="Company Warehouse">{{ t("Company Warehouse") }}</option>
						<option value="Supplier">{{ t("Supplier") }}</option>
					</select>
					<p class="mt-1 text-xs text-gray-400">
						{{ t("Only used if this line becomes part of a Sales Invoice.") }}
					</p>
				</div>

				<div v-if="supplySource === 'Supplier'">
					<label class="mb-1 block text-sm font-medium text-gray-700">{{ t("Supplier") }}</label>
					<div v-if="supplier" class="flex items-center justify-between rounded border border-gray-300 px-3 py-2 text-sm">
						<span>{{ supplier.supplier_name }}</span>
						<button type="button" class="text-xs text-blue-600 hover:underline" @click="supplier = null">
							{{ t("Change") }}
						</button>
					</div>
					<div v-else class="space-y-1">
						<input
							v-model="supplierTerm"
							type="text"
							:placeholder="t('Search supplier by name...')"
							class="w-full rounded border border-gray-300 px-3 py-2 text-sm"
							@input="onSupplierSearchInput"
						/>
						<ul
							v-if="supplierResults.length"
							class="max-h-32 divide-y divide-gray-100 overflow-y-auto rounded border border-gray-100"
						>
							<li
								v-for="s in supplierResults"
								:key="s.name"
								class="cursor-pointer px-3 py-2 text-sm hover:bg-gray-50"
								@click="selectSupplier(s)"
							>
								{{ s.supplier_name }}
							</li>
						</ul>
					</div>
					<p class="mt-1 text-xs text-gray-400">
						{{ t("No availability confirmation needed - the supplier is set directly on this line.") }}
					</p>
				</div>

				<div v-if="loading" class="flex justify-center py-4">
					<LoadingIndicator class="h-5 w-5 text-gray-400" />
				</div>
				<p v-else-if="error" class="text-sm text-red-600">{{ error }}</p>
				<div v-else-if="areaPreview" class="rounded-lg bg-gray-50 p-4 text-sm">
					<div class="flex justify-between py-0.5">
						<span class="text-gray-500">{{ t("Box Size") }}</span>
						<span>{{ areaPreview.area_per_box }} {{ t("m²") }}</span>
					</div>
					<div class="flex justify-between py-0.5">
						<span class="text-gray-500">{{ t("Required Boxes") }}</span>
						<span>{{ areaPreview.boxes }}</span>
					</div>
					<div class="flex justify-between py-0.5">
						<span class="text-gray-500">{{ t("Delivered Area") }}</span>
						<span>{{ areaPreview.delivered_area_sqm }} {{ t("m²") }}</span>
					</div>
					<div class="flex justify-between py-0.5">
						<span class="text-gray-500">{{ t("Price") }}</span>
						<span>{{ areaPreview.price_per_sqm }} / {{ t("m²") }}</span>
					</div>
					<div class="mt-2 flex justify-between border-t border-gray-200 pt-2 font-semibold">
						<span>{{ t("Total") }}</span>
						<span>{{ areaPreview.amount }}</span>
					</div>
				</div>
				<div v-else-if="simplePreview" class="rounded-lg bg-gray-50 p-4 text-sm">
					<div class="flex justify-between py-0.5">
						<span class="text-gray-500">{{ t("Quantity") }}</span>
						<span>{{ simplePreview.qty }} {{ t(simplePreview.uom) }}</span>
					</div>
					<div class="flex justify-between py-0.5">
						<span class="text-gray-500">{{ t("Price") }}</span>
						<span>{{ simplePreview.rate }} / {{ t(simplePreview.uom) }}</span>
					</div>
					<div class="mt-2 flex justify-between border-t border-gray-200 pt-2 font-semibold">
						<span>{{ t("Total") }}</span>
						<span>{{ simplePreview.amount }}</span>
					</div>
				</div>
			</div>
		</template>
		<template #actions>
			<Button
				variant="solid"
				theme="blue"
				class="w-full"
				:disabled="!preview || loading || (supplySource === 'Supplier' && !supplier)"
				@click="add"
			>
				{{ t("Add To Cart") }}
			</Button>
		</template>
	</Dialog>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { Button, Dialog, LoadingIndicator, debounce } from "frappe-ui";
import { previewRow, previewSimpleRow } from "@/api/calculation";
import { searchSuppliers } from "@/api/supplier";
import { t } from "@/utils/translate";
import { useCartStore } from "@/stores/cart";
import { useSessionStore } from "@/stores/session";
import { isAreaBasedItem } from "@/types";
import type { CalculationPreview, PosItem, SimpleCalculationPreview, SupplierRef, SupplySource } from "@/types";

const props = defineProps<{ item: PosItem }>();
const emit = defineEmits<{ close: [] }>();

const cart = useCartStore();
const session = useSessionStore();

const isAreaBased = isAreaBasedItem(props.item);

const open = ref(true);
const quantity = ref<number>(isAreaBased ? 0 : 1);
const supplySource = ref<SupplySource>("Company Warehouse");
const areaPreview = ref<CalculationPreview | null>(null);
const simplePreview = ref<SimpleCalculationPreview | null>(null);
const preview = computed(() => areaPreview.value ?? simplePreview.value);
const loading = ref(false);
const error = ref("");

const supplier = ref<SupplierRef | null>(null);
const supplierTerm = ref("");
const supplierResults = ref<SupplierRef[]>([]);

const runSupplierSearch = debounce(async () => {
	if (!supplierTerm.value) {
		supplierResults.value = [];
		return;
	}
	supplierResults.value = await searchSuppliers(supplierTerm.value);
}, 300);

function onSupplierSearchInput() {
	runSupplierSearch();
}

function selectSupplier(s: SupplierRef) {
	supplier.value = s;
	supplierResults.value = [];
	supplierTerm.value = "";
}

async function refreshPreview() {
	if (!quantity.value || quantity.value <= 0) {
		areaPreview.value = null;
		simplePreview.value = null;
		error.value = "";
		return;
	}
	loading.value = true;
	error.value = "";
	try {
		if (isAreaBased) {
			areaPreview.value = await previewRow(props.item.item_code, quantity.value, session.priceList);
		} else {
			simplePreview.value = await previewSimpleRow(props.item.item_code, quantity.value, session.priceList);
		}
	} catch (e) {
		error.value = e instanceof Error ? e.message : String(e);
		areaPreview.value = null;
		simplePreview.value = null;
	} finally {
		loading.value = false;
	}
}

const onQuantityInput = debounce(refreshPreview, 300);

async function add() {
	if (!quantity.value || !preview.value) return;
	if (supplySource.value === "Supplier" && !supplier.value) return;
	await cart.addItem(props.item, quantity.value, supplySource.value, supplier.value?.name ?? null);
	open.value = false;
	emit("close");
}

onMounted(refreshPreview);
</script>
