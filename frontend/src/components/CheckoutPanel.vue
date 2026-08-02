<template>
	<div class="rounded-lg border border-gray-200 bg-white p-4">
		<h2 class="mb-2 text-sm font-semibold text-gray-700">{{ t("Checkout") }}</h2>

		<p v-if="error" class="mb-2 text-sm text-red-600">{{ error }}</p>
		<p v-if="successMessage" class="mb-2 text-sm text-green-700">{{ successMessage }}</p>

		<div v-if="invoiceName" class="mb-3 flex flex-col gap-3 rounded-md bg-gray-50 p-3">
			<p class="text-xs font-medium uppercase text-gray-500">
				{{ t("Sales Invoice") }} {{ invoiceName }} -
				{{ invoiceSubmitted ? t("Finalized") : t("Draft") }}
			</p>

			<div>
				<p class="mb-1 text-xs font-medium uppercase text-gray-500">{{ t("Actions") }}</p>
				<div class="flex flex-wrap gap-2">
					<Button
						v-if="invoiceSubmitted && !paymentName"
						size="sm"
						variant="solid"
						theme="blue"
						:loading="recordingPayment"
						@click="recordPayment"
					>
						{{ t("Record Payment") }}
					</Button>
					<Button
						v-if="invoiceSubmitted && hasWarehouseItems && !deliveryNoteName"
						size="sm"
						variant="solid"
						theme="blue"
						:loading="creatingDeliveryNote"
						@click="createDelivery"
					>
						{{ t("Create Delivery Note") }}
					</Button>
					<Button
						v-if="invoiceSubmitted && hasSupplierItems && !supplierDeliveryName"
						size="sm"
						variant="solid"
						theme="blue"
						:loading="creatingSupplierDelivery"
						@click="createSupplierDeliveryOrder"
					>
						{{ t("Create Supplier Delivery Order") }}
					</Button>
				</div>
			</div>

			<div>
				<p class="mb-1 text-xs font-medium uppercase text-gray-500">{{ t("Print") }}</p>
				<div class="flex flex-wrap gap-2">
					<Button size="sm" variant="outline" @click="printDoc('Sales Invoice', invoiceName)">
						{{ t("Print Invoice") }}
					</Button>
					<Button
						v-if="paymentName"
						size="sm"
						variant="outline"
						@click="printDoc('Payment Entry', paymentName!)"
					>
						{{ t("Print Payment Receipt") }}
					</Button>
					<Button
						v-if="deliveryNoteName"
						size="sm"
						variant="outline"
						@click="printDoc('Delivery Note', deliveryNoteName!)"
					>
						{{ t("Print Delivery Note") }}
					</Button>
					<Button
						v-if="supplierDeliveryName"
						size="sm"
						variant="outline"
						@click="printDoc('Supplier Delivery Order', supplierDeliveryName!)"
					>
						{{ t("Print Supplier Delivery Order") }}
					</Button>
				</div>
			</div>
		</div>

		<div v-if="quotationName" class="mb-3 flex flex-col gap-2 rounded-md bg-gray-50 p-3">
			<p class="text-xs font-medium uppercase text-gray-500">{{ t("Quotation") }} {{ quotationName }}</p>
			<Button size="sm" variant="outline" @click="printDoc('Quotation', quotationName!)">
				{{ t("Print Quotation") }}
			</Button>
		</div>

		<div class="flex flex-col gap-2">
			<Button variant="outline" :loading="savingQuotation" @click="saveQuotation">{{ t("Save Quotation") }}</Button>
			<Button variant="solid" theme="blue" :loading="creatingInvoice" @click="createInvoice">
				{{ t("Create Invoice") }}
			</Button>
			<Button variant="ghost" theme="red" @click="resetAll">{{ t("Cancel") }}</Button>
		</div>
	</div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { Button } from "frappe-ui";
import { createQuotation } from "@/api/quotation";
import { createSalesInvoice, submitSalesInvoice } from "@/api/sales";
import { createPayment, createDeliveryNote, createSupplierDelivery } from "@/api/fulfillment";
import { t } from "@/utils/translate";
import { useCartStore } from "@/stores/cart";
import { useSessionStore } from "@/stores/session";

const cart = useCartStore();
const session = useSessionStore();

const savingQuotation = ref(false);
const creatingInvoice = ref(false);
const recordingPayment = ref(false);
const creatingDeliveryNote = ref(false);
const creatingSupplierDelivery = ref(false);
const error = ref("");
const successMessage = ref("");
const quotationName = ref<string | null>(null);

const invoiceName = ref<string | null>(null);
const invoiceSubmitted = ref(false);
const hasWarehouseItems = ref(false);
const hasSupplierItems = ref(false);
const paymentName = ref<string | null>(null);
const deliveryNoteName = ref<string | null>(null);
const supplierDeliveryName = ref<string | null>(null);

function validate(): boolean {
	error.value = "";
	if (!session.showroom) {
		error.value = t("No showroom available for this sale.");
		return false;
	}
	if (!cart.customer) {
		error.value = t("Select or create a customer first.");
		return false;
	}
	if (cart.isEmpty) {
		error.value = t("Add at least one item to the cart.");
		return false;
	}
	return true;
}

function resetAll() {
	cart.clear();
	error.value = "";
	successMessage.value = "";
	quotationName.value = null;
	invoiceName.value = null;
	invoiceSubmitted.value = false;
	hasWarehouseItems.value = false;
	hasSupplierItems.value = false;
	paymentName.value = null;
	deliveryNoteName.value = null;
	supplierDeliveryName.value = null;
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
		quotationName.value = result.name;
		successMessage.value = t("Quotation {0} created.", [result.name]);
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
	supplierDeliveryName.value = null;
	// Supply sources are only known while the cart still has lines - capture
	// them before the cart is cleared below.
	hasWarehouseItems.value = cart.lines.some((line) => line.supply_source === "Company Warehouse");
	hasSupplierItems.value = cart.lines.some((line) => line.supply_source === "Supplier");
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
			successMessage.value = t("Sales Invoice {0} completed.", [result.name]);
		} catch (submitError) {
			// Created successfully as a draft, but couldn't finalize yet (e.g.
			// a Supplier-sourced line is still waiting on availability
			// confirmation - spec Part 5). Keep the draft, surface why.
			successMessage.value = "";
			error.value = t("Sales Invoice {0} was saved as a draft but could not be finalized: {1}", [
				result.name,
				submitError instanceof Error ? submitError.message : String(submitError),
			]);
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

async function createSupplierDeliveryOrder() {
	if (!invoiceName.value) return;
	creatingSupplierDelivery.value = true;
	error.value = "";
	try {
		const result = await createSupplierDelivery(invoiceName.value);
		supplierDeliveryName.value = result.name;
	} catch (e) {
		error.value = e instanceof Error ? e.message : String(e);
	} finally {
		creatingSupplierDelivery.value = false;
	}
}

function printDoc(doctype: string, name: string) {
	const url = `/printview?doctype=${encodeURIComponent(doctype)}&name=${encodeURIComponent(name)}`;
	window.open(url, "_blank");
}
</script>
