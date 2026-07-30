<template>
	<div class="rounded-lg border border-gray-200 bg-white p-4">
		<h2 class="mb-2 text-sm font-semibold text-gray-700">Checkout</h2>

		<p v-if="error" class="mb-2 text-sm text-red-600">{{ error }}</p>
		<p v-if="successMessage" class="mb-2 text-sm text-green-700">
			{{ successMessage }}
			<button type="button" class="ml-1 font-medium underline" @click="print">Print</button>
		</p>

		<div class="flex flex-col gap-2">
			<Button variant="outline" :loading="savingQuotation" @click="saveQuotation">Save Quotation</Button>
			<Button variant="solid" theme="blue" :loading="creatingInvoice" @click="createInvoice">Create Invoice</Button>
			<Button variant="ghost" theme="red" @click="cart.clear()">Cancel</Button>
		</div>
	</div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { Button } from "frappe-ui";
import { createQuotation } from "@/api/quotation";
import { createSalesInvoice } from "@/api/sales";
import { useCartStore } from "@/stores/cart";
import { useSessionStore } from "@/stores/session";

const cart = useCartStore();
const session = useSessionStore();

const savingQuotation = ref(false);
const creatingInvoice = ref(false);
const error = ref("");
const successMessage = ref("");
const lastDoctype = ref<"Quotation" | "Sales Invoice" | null>(null);
const lastName = ref<string | null>(null);

function validate(): boolean {
	error.value = "";
	if (!session.showroom) {
		error.value = "No showroom available for this sale.";
		return false;
	}
	if (!cart.customer) {
		error.value = "Select or create a customer first.";
		return false;
	}
	if (cart.isEmpty) {
		error.value = "Add at least one item to the cart.";
		return false;
	}
	return true;
}

async function saveQuotation() {
	if (!validate() || !cart.customer || !session.showroom) return;
	savingQuotation.value = true;
	successMessage.value = "";
	try {
		const result = await createQuotation(
			cart.customer.name,
			session.showroom,
			cart.lines.map((line) => ({
				item_code: line.item.item_code,
				required_area_sqm: line.required_area_sqm,
			})),
			session.priceList,
		);
		lastDoctype.value = "Quotation";
		lastName.value = result.name;
		successMessage.value = `Quotation ${result.name} created.`;
		cart.clear();
	} catch (e) {
		error.value = e instanceof Error ? e.message : String(e);
	} finally {
		savingQuotation.value = false;
	}
}

async function createInvoice() {
	if (!validate() || !cart.customer || !session.showroom) return;
	creatingInvoice.value = true;
	successMessage.value = "";
	try {
		const result = await createSalesInvoice(
			cart.customer.name,
			session.showroom,
			cart.lines.map((line) => ({
				item_code: line.item.item_code,
				required_area_sqm: line.required_area_sqm,
				supply_source: line.supply_source,
			})),
			session.priceList,
		);
		lastDoctype.value = "Sales Invoice";
		lastName.value = result.name;
		successMessage.value = `Sales Invoice ${result.name} created.`;
		cart.clear();
	} catch (e) {
		error.value = e instanceof Error ? e.message : String(e);
	} finally {
		creatingInvoice.value = false;
	}
}

function print() {
	if (!lastDoctype.value || !lastName.value) return;
	const url = `/printview?doctype=${encodeURIComponent(lastDoctype.value)}&name=${encodeURIComponent(lastName.value)}`;
	window.open(url, "_blank");
}
</script>
