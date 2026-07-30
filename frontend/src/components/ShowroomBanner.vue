<template>
	<span
		v-if="session.showroom"
		class="rounded-full bg-green-100 px-3 py-1 text-sm font-medium text-green-800"
	>
		{{ session.showroom }}
	</span>
	<span v-else class="text-sm text-gray-400">No showroom assigned</span>
</template>

<script setup lang="ts">
import { useSessionStore } from "@/stores/session";

const session = useSessionStore();
</script>
