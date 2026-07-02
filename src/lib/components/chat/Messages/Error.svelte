<script lang="ts">
	import Info from '$lib/components/icons/Info.svelte';
	import { getContext } from 'svelte';

	const i18n = getContext('i18n');

	export let content = '';

	$: {
		if (content) {
			console.error('Chat Error:', content);
		}
	}
</script>

<div class="flex my-2 gap-2.5 border px-4 py-3 border-red-600/10 bg-red-600/10 rounded-lg">
	<div class=" self-start mt-0.5">
		<Info className="size-5 text-red-700 dark:text-red-400" />
	</div>

	<div class=" self-center text-sm">
		{$i18n.t('An error occurred. Please contact the administrator.')}
	</div>
</div>
