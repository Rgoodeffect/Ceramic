<template>
	<Dialog v-model="open" :options="{ title: t('New Customer'), size: 'sm' }" @close="emit('close')">
		<template #body-content>
			<div class="space-y-3">
				<div>
					<label class="mb-1 block text-sm font-medium text-gray-700">{{ t("Customer Name") }} *</label>
					<input v-model="customerName" type="text" class="w-full rounded border border-gray-300 px-3 py-2 text-sm" />
				</div>
				<div>
					<label class="mb-1 block text-sm font-medium text-gray-700">{{ t("Mobile Number") }} *</label>
					<input v-model="mobileNo" type="tel" class="w-full rounded border border-gray-300 px-3 py-2 text-sm" />
				</div>
				<div>
					<label class="mb-1 block text-sm font-medium text-gray-700">{{ t("Address") }}</label>
					<input v-model="address" type="text" class="w-full rounded border border-gray-300 px-3 py-2 text-sm" />
				</div>
				<div>
					<label class="mb-1 block text-sm font-medium text-gray-700">{{ t("Email") }}</label>
					<input v-model="email" type="email" class="w-full rounded border border-gray-300 px-3 py-2 text-sm" />
				</div>
				<p v-if="error" class="text-sm text-red-600">{{ error }}</p>
			</div>
		</template>
		<template #actions>
			<Button variant="solid" theme="blue" class="w-full" :loading="saving" @click="save">
				{{ t("Create Customer") }}
			</Button>
		</template>
	</Dialog>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { Button, Dialog } from "frappe-ui";
import { quickCreateCustomer } from "@/api/customer";
import { t } from "@/utils/translate";
import type { CustomerRef } from "@/types";

const emit = defineEmits<{ close: []; created: [customer: CustomerRef] }>();

const open = ref(true);
const customerName = ref("");
const mobileNo = ref("");
const address = ref("");
const email = ref("");
const saving = ref(false);
const error = ref("");

async function save() {
	if (!customerName.value || !mobileNo.value) {
		error.value = t("Customer Name and Mobile Number are required.");
		return;
	}
	saving.value = true;
	error.value = "";
	try {
		const result = await quickCreateCustomer(
			customerName.value,
			mobileNo.value,
			address.value || undefined,
			email.value || undefined,
		);
		emit("created", { name: result.name, customer_name: customerName.value });
		open.value = false;
		emit("close");
	} catch (e) {
		error.value = e instanceof Error ? e.message : String(e);
	} finally {
		saving.value = false;
	}
}
</script>
