<template>
	<div class="rounded-lg border border-gray-200 bg-white p-4">
		<h2 class="mb-2 text-sm font-semibold text-gray-700">{{ t("Customer") }}</h2>

		<div v-if="cart.customer" class="flex items-center justify-between">
			<span class="text-sm font-medium">{{ cart.customer.customer_name }}</span>
			<button type="button" class="text-xs text-blue-600 hover:underline" @click="cart.setCustomer(null)">
				{{ t("Change") }}
			</button>
		</div>

		<div v-else class="space-y-2">
			<input
				v-model="term"
				type="text"
				:placeholder="t('Search customer by name...')"
				class="w-full rounded border border-gray-300 px-3 py-2 text-sm"
				@input="onSearchInput"
			/>
			<ul v-if="results.length" class="max-h-40 divide-y divide-gray-100 overflow-y-auto rounded border border-gray-100">
				<li
					v-for="customer in results"
					:key="customer.name"
					class="cursor-pointer px-3 py-2 text-sm hover:bg-gray-50"
					@click="select(customer)"
				>
					{{ customer.customer_name }}
				</li>
			</ul>
			<Button variant="outline" class="w-full" @click="showQuickCreate = true">{{ t("New Customer") }}</Button>
		</div>

		<QuickCreateCustomerDialog
			v-if="showQuickCreate"
			@close="showQuickCreate = false"
			@created="onCreated"
		/>
	</div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { Button, debounce } from "frappe-ui";
import { searchCustomers } from "@/api/customer";
import { t } from "@/utils/translate";
import { useCartStore } from "@/stores/cart";
import type { CustomerRef } from "@/types";
import QuickCreateCustomerDialog from "@/components/QuickCreateCustomerDialog.vue";

const cart = useCartStore();
const term = ref("");
const results = ref<CustomerRef[]>([]);
const showQuickCreate = ref(false);

const runSearch = debounce(async () => {
	if (!term.value) {
		results.value = [];
		return;
	}
	results.value = await searchCustomers(term.value);
}, 300);

function onSearchInput() {
	runSearch();
}

function select(customer: CustomerRef) {
	cart.setCustomer(customer);
	results.value = [];
	term.value = "";
}

function onCreated(customer: CustomerRef) {
	cart.setCustomer(customer);
}
</script>
