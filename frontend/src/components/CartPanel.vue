<template>
	<div class="rounded-lg border border-gray-200 bg-white p-4">
		<h2 class="mb-2 text-sm font-semibold text-gray-700">Cart</h2>
		<p v-if="cart.isEmpty" class="py-6 text-center text-sm text-gray-400">No items yet.</p>
		<div v-else>
			<CartLineItem
				v-for="line in cart.lines"
				:key="line.key"
				:line="line"
				@remove="cart.removeLine"
			/>
			<div class="mt-2 flex justify-between border-t border-gray-200 pt-2 text-base font-semibold">
				<span>Total</span>
				<span>{{ cart.grandTotal }}</span>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import { useCartStore } from "@/stores/cart";
import CartLineItem from "@/components/CartLineItem.vue";

const cart = useCartStore();
</script>
