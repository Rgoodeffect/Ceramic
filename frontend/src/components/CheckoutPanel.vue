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

			<!-- Payment: the customer may pay all of it, part of it, or none of
			     it at all - whatever is left stays on the invoice as their debt. -->
			<div v-if="invoiceSubmitted && paymentStatus" class="rounded-md border border-gray-200 bg-white p-3">
				<p class="mb-2 text-xs font-medium uppercase text-gray-500">{{ t("Payment") }}</p>

				<div class="mb-3 text-sm">
					<div class="flex justify-between py-0.5">
						<span class="text-gray-500">{{ t("Invoice Total") }}</span>
						<span>{{ money(paymentStatus.grand_total) }}</span>
					</div>
					<div class="flex justify-between py-0.5">
						<span class="text-gray-500">{{ t("Paid Amount") }}</span>
						<span>{{ money(paymentStatus.paid_amount) }}</span>
					</div>
					<div
						class="flex justify-between border-t border-gray-200 pt-1 font-semibold"
						:class="hasDebt ? 'text-red-600' : 'text-green-700'"
					>
						<span>{{ hasDebt ? t("Remaining Debt") : t("Fully Paid") }}</span>
						<span>{{ money(paymentStatus.outstanding_amount) }}</span>
					</div>
					<p v-if="hasDebt && customerName" class="mt-1 text-xs text-gray-500">
						{{ t("This amount stays as a debt on {0}, payable later.", [customerName]) }}
					</p>
					<p v-if="paymentStatus.customer_outstanding > 0" class="mt-1 text-xs text-gray-500">
						{{ t("Total debt for this customer") }}:
						{{ money(paymentStatus.customer_outstanding) }}
					</p>
				</div>

				<div v-if="hasDebt" class="flex flex-wrap items-end gap-2">
					<div>
						<label class="mb-1 block text-xs font-medium text-gray-700">
							{{ t("Amount Paid Now") }}
						</label>
						<input
							v-model.number="paymentAmount"
							type="number"
							min="0"
							step="0.001"
							:max="paymentStatus.outstanding_amount"
							class="w-36 rounded border border-gray-300 px-3 py-2 text-sm"
						/>
					</div>
					<Button size="sm" variant="outline" @click="payFullRemaining">
						{{ t("Full Amount") }}
					</Button>
					<Button
						size="sm"
						variant="solid"
						theme="blue"
						:loading="recordingPayment"
						@click="recordPayment"
					>
						{{ t("Record Payment") }}
					</Button>
				</div>
			</div>

			<div>
				<p class="mb-1 text-xs font-medium uppercase text-gray-500">{{ t("Actions") }}</p>
				<div class="flex flex-wrap gap-2">
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
						v-if="invoiceSubmitted && hasSupplierItems && !supplierOrders.length"
						size="sm"
						variant="solid"
						theme="blue"
						:loading="creatingSupplierDelivery"
						@click="createSupplierDeliveryOrders"
					>
						{{ t("Create Supplier Delivery Orders") }}
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
						v-for="(payment, index) in paymentNames"
						:key="payment"
						size="sm"
						variant="outline"
						@click="printDoc('Payment Entry', payment)"
					>
						{{
							paymentNames.length > 1
								? t("Print Payment Receipt {0}", [index + 1])
								: t("Print Payment Receipt")
						}}
					</Button>
					<Button
						v-if="deliveryNoteName"
						size="sm"
						variant="outline"
						@click="printDoc('Delivery Note', deliveryNoteName!)"
					>
						{{ t("Print Delivery Note") }}
					</Button>
					<!-- One order, and one printout, per supplier on the invoice. -->
					<Button
						v-for="order in supplierOrders"
						:key="order.name"
						size="sm"
						variant="outline"
						@click="printDoc('Supplier Delivery Order', order.name)"
					>
						{{ t("Print Supplier Delivery Order") }} - {{ order.supplier_name }}
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
import { computed, ref } from "vue";
import { Button } from "frappe-ui";
import { createQuotation } from "@/api/quotation";
import { createSalesInvoice, submitSalesInvoice } from "@/api/sales";
import {
	createPayment,
	createDeliveryNote,
	createSupplierDeliveries,
	getPaymentStatus,
} from "@/api/fulfillment";
import { t } from "@/utils/translate";
import { formatMoney } from "@/utils/money";
import { useCartStore } from "@/stores/cart";
import { useSessionStore } from "@/stores/session";
import type { PaymentStatus, SupplierDeliveryOrderRef } from "@/types";

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
/** Kept because the cart (and its customer) is cleared once the invoice
 * exists, but the debt message still needs to name who owes it. */
const customerName = ref("");
const paymentStatus = ref<PaymentStatus | null>(null);
/** Every Payment Entry taken against this invoice - a part payment can be
 * followed by more, and each one gets its own receipt to print. */
const paymentNames = ref<string[]>([]);
const paymentAmount = ref<number | null>(null);
const deliveryNoteName = ref<string | null>(null);
const supplierOrders = ref<SupplierDeliveryOrderRef[]>([]);

const hasDebt = computed(() => (paymentStatus.value?.outstanding_amount ?? 0) > 0);

function money(amount: number): string {
	return formatMoney(amount, paymentStatus.value?.currency ?? session.currency);
}

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
	customerName.value = "";
	paymentStatus.value = null;
	paymentNames.value = [];
	paymentAmount.value = null;
	deliveryNoteName.value = null;
	supplierOrders.value = [];
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
				required_area_sqm: line.required_area_sqm ?? undefined,
				qty: line.qty ?? undefined,
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
	paymentStatus.value = null;
	paymentNames.value = [];
	paymentAmount.value = null;
	deliveryNoteName.value = null;
	supplierOrders.value = [];
	// Supply sources and the customer are only known while the cart still has
	// lines - capture them before the cart is cleared below.
	hasWarehouseItems.value = cart.lines.some((line) => line.supply_source === "Company Warehouse");
	hasSupplierItems.value = cart.lines.some((line) => line.supply_source === "Supplier");
	customerName.value = cart.customer.customer_name;
	try {
		const result = await createSalesInvoice(
			cart.customer.name,
			session.showroom,
			cart.lines.map((line) => ({
				item_code: line.item.item_code,
				required_area_sqm: line.required_area_sqm ?? undefined,
				qty: line.qty ?? undefined,
				supply_source: line.supply_source,
				supplier: line.supplier ?? undefined,
			})),
			session.priceList,
		);
		invoiceName.value = result.name;
		cart.clear();

		try {
			await submitSalesInvoice(result.name);
			invoiceSubmitted.value = true;
			successMessage.value = t("Sales Invoice {0} completed.", [result.name]);
			// Deliberately not inside the same try as the submit: a balance
			// that fails to load must not be reported as a failed submit.
			try {
				await refreshPaymentStatus();
			} catch (statusError) {
				error.value = statusError instanceof Error ? statusError.message : String(statusError);
			}
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

/** Loads the balance and pre-fills the amount box with everything still
 * owed - paying in full stays a single click, a part payment is typing a
 * smaller number over it. */
async function refreshPaymentStatus() {
	if (!invoiceName.value) return;
	paymentStatus.value = await getPaymentStatus(invoiceName.value);
	paymentAmount.value = paymentStatus.value.outstanding_amount || null;
}

function payFullRemaining() {
	paymentAmount.value = paymentStatus.value?.outstanding_amount ?? null;
}

async function recordPayment() {
	if (!invoiceName.value || !paymentStatus.value) return;
	const amount = paymentAmount.value;
	if (!amount || amount <= 0) {
		error.value = t("Enter the amount the customer is paying now.");
		return;
	}
	if (amount > paymentStatus.value.outstanding_amount) {
		error.value = t("Payment amount is more than the outstanding amount.");
		return;
	}
	recordingPayment.value = true;
	error.value = "";
	try {
		const result = await createPayment(invoiceName.value, undefined, amount);
		paymentNames.value.push(result.name);
		paymentStatus.value = result.payment_status;
		paymentAmount.value = result.payment_status.outstanding_amount || null;
		successMessage.value = result.payment_status.outstanding_amount
			? t("Payment of {0} recorded. {1} remains as debt.", [
					money(result.paid_amount),
					money(result.payment_status.outstanding_amount),
				])
			: t("Payment of {0} recorded. Invoice fully paid.", [money(result.paid_amount)]);
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

async function createSupplierDeliveryOrders() {
	if (!invoiceName.value) return;
	creatingSupplierDelivery.value = true;
	error.value = "";
	try {
		const result = await createSupplierDeliveries(invoiceName.value);
		supplierOrders.value = result.orders;
		successMessage.value =
			result.orders.length > 1
				? t("{0} supplier delivery orders created - one per supplier.", [result.orders.length])
				: t("Supplier delivery order {0} created.", [result.orders[0].name]);
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
