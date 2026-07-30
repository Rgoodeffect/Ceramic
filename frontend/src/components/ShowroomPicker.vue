<template>
	<div class="mt-3 text-left">
		<label class="mb-1 block text-sm font-medium text-gray-700">Select a showroom</label>
		<select
			class="w-full rounded border border-gray-300 px-3 py-2 text-sm"
			@change="onSelect(($event.target as HTMLSelectElement).value)"
		>
			<option value="" disabled selected>Choose a showroom</option>
			<option v-for="branch in branches" :key="branch.name" :value="branch.name">
				{{ branch.name }}
			</option>
		</select>
	</div>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { listBranches, type BranchRef } from "@/api/branch";
import { useSessionStore } from "@/stores/session";

const session = useSessionStore();
const branches = ref<BranchRef[]>([]);

onMounted(async () => {
	branches.value = await listBranches();
});

function onSelect(value: string) {
	if (value) session.setManualShowroom(value);
}
</script>
