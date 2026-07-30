<template>
	<div class="border-b border-gray-200 p-4">
		<input
			v-model="catalog.searchTerm"
			type="text"
			placeholder="Search by name, code, brand, collection, series, or color..."
			class="w-full rounded-lg border border-gray-300 px-4 py-2 text-sm focus:border-blue-500 focus:outline-none"
			@input="onInput"
		/>
	</div>
</template>

<script setup lang="ts">
import { onMounted } from "vue";
import { debounce } from "frappe-ui";
import { useCatalogStore } from "@/stores/catalog";

const catalog = useCatalogStore();
const debouncedSearch = debounce(() => catalog.search(), 300);

function onInput() {
	debouncedSearch();
}

onMounted(() => {
	catalog.search();
});
</script>
