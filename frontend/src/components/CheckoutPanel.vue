<template>
	<div class="rounded-lg border border-gray-200 bg-white p-4">
		<h2 class="mb-2 text-sm font-semibold text-gray-700">Checkout</h2>

		<p v-if="error" class="mb-2 text-sm text-red-600">{{ error }}</p>
		<p v-if="successMessage" class="mb-2 text-sm text-green-700">{{ successMessage }}</p>

		<div v-if="invoiceName" class="mb-3 flex flex-col gap-2 rounded-md bg-gray-50 p-3">
			<p class="text-xs font-medium uppercase text-gray-500">
				Sales Invoice {{ invoiceName }} - {{ invoiceSubmitted ? "Finalized" : "Draft" }}
			</p>
			<div class="flex flex-wrap gap-2">
				<Button size="sm" variant="outline" @click="printDoc('Sales Invoice', invoiceName)">
					Print Invoice
				</Button>
				<Button
					v-if="invoiceSubmitted"
					size="sm"
					variant="outline"
					:loading="recordingPayment"
					@click="recordPayment"
				>
					Record Payment
				</Button>
				<Button
					v-if="invoiceSubmitted && hasWarehouseItems && !deliveryNoteName"
					size="sm"
					variant="outline"
					:loading="creatingDeliveryNote"
					@click="createDelivery"
				>
					Create Delivery Note
				</Button>
			</div>
			<p v-if="paymentName" class="text-xs text-green-700">
				Payment {{ paymentName }} recorded.
				<button type="button" class="ml-1 font-medium underline" @click="printDoc('Payment Entry', paymentName)">
					Print Receipt
				</button>
			</p>
			<p v-if="deliveryNoteName" class="text-xs text-green-700">
				Delivery Note {{ deliveryNoteName }} created.
				<button
					type="button"
					class="ml-1 font-medium underline"
					@click="printDoc('Delivery Note', deliveryNoteName)"
				>
					Print Delivery Note
				</button>
			</p>
		</div>

		<p v-if="quotationSuccessMessage" class="mb-2 text-sm text-green-700">
			{{ quotationSuccessMessage }}
			<button type="button" class="ml-1 font-medium underline" @click="printDoc('Quotation', quotationName!)">
				Print
			</button>
		</p>

		<div class="flex flex-col gap-2">
			<Button variant="outline" :loading="savingQuotation" @click="saveQuotation">Save Quotation</Button>
			<Button variant="solid" theme="blue" :loading="creatingInvoice" @click="createInvoice">Create Invoice</Button>
			<Button variant="ghost" theme="red" @click="resetAll">Cancel</Button>
		</div>
	</div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { Button } from "frappe-ui";
import { createQuotation } from "@/api/quotation";
import { createSalesInvoice, submitSalesInvoice } from "@/api/sales";
import { createPayment, createDeliveryNote } from "@/api/fulfillment";
import { useCartStore } from "@/stores/cart";
import { useSessionStore } from "@/stores/session";

const cart = useCartStore();
const session = useSessionStore();

const savingQuotation = ref(false);
const creatingInvoice = ref(false);
const recordingPayment = ref(false);
const creatingDeliveryNote = ref(false);
const error = ref("");
const successMessage = ref("");
const quotationSuccessMessage = ref("");
const quotationName = ref<string | null>(null);

const invoiceName = ref<string | null>(null);
const invoiceSubmitted = ref(false);
const hasWarehouseItems = ref(false);
const paymentName = ref<string | null>(null);
const deliveryNoteName = ref<string | null>(null);

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

function resetAll() {
	cart.clear();
	error.value = "";
	successMessage.value = "";
	quotationSuccessMessage.value = "";
	quotationName.value = null;
	invoiceName.value = null;
	invoiceSubmitted.value = false;
	hasWarehouseItems.value = false;
	paymentName.value = null;
	deliveryNoteName.value = null;
}

async function saveQuotation() {
	if (!validate() || !cart.customer || !session.showroom) return;
	savingQuotation.value = true;
	quotationSuccessMessage.value = "";
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
		quotationName.value = result.name;
		quotationSuccessMessage.value = `Quotation ${result.name} created.`;
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
	error.value = "";
	invoiceName.value = null;
	invoiceSubmitted.value = false;
	paymentName.value = null;
	deliveryNoteName.value = null;
	// Supply sources are only known while the cart still has lines - capture
	// them before the cart is cleared below.
	hasWarehouseItems.value = cart.lines.some((line) => line.supply_source === "Company Warehouse");
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
		invoiceName.value = result.name;
		cart.clear();

		try {
			await submitSalesInvoice(result.name);
			invoiceSubmitted.value = true;
			successMessage.value = `Sales Invoice ${result.name} completed.`;
		} catch (submitError) {
			// Created successfully as a draft, but couldn't finalize yet (e.g.
			// a Supplier-sourced line is still waiting on availability
			// confirmation - spec Part 5). Keep the draft, surface why.
			successMessage.value = "";
			error.value =
				`Sales Invoice ${result.name} was saved as a draft but could not be finalized: ` +
				(submitError instanceof Error ? submitError.message : String(submitError));
		}
	} catch (e) {
		error.value = e instanceof Error ? e.message : String(e);
	} finally {
		creatingInvoice.value = false;
	}
}

async function recordPayment() {
	if (!invoiceName.value) return;
	recordingPayment.value = true;
	error.value = "";
	try {
		const result = await createPayment(invoiceName.value);
		paymentName.value = result.name;
	} catch (e) {
		error.value = e instanceof Error ? e.message : String(e);
	} finally {
		recordingPayment.value = false;
	}
}

async function createDelivery() {
	if (!invoiceName.value) return;
	creatingDeliveryNote.value = true;
	error.value = "";
	try {
		const result = await createDeliveryNote(invoiceName.value);
		deliveryNoteName.value = result.name;
	} catch (e) {
		error.value = e instanceof Error ? e.message : String(e);
	} finally {
		creatingDeliveryNote.value = false;
	}
}

function printDoc(doctype: string, name: string) {
	const url = `/printview?doctype=${encodeURIComponent(doctype)}&name=${encodeURIComponent(name)}`;
	window.open(url, "_blank");
}
</script>
