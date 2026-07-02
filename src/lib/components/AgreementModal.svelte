<script lang="ts">
	import { onMount, getContext } from 'svelte';
	import { marked } from 'marked';
	import DOMPurify from 'dompurify';

	import Modal from './common/Modal.svelte';
	import { WEBUI_NAME } from '$lib/stores';

	const i18n = getContext('i18n');

	export let show = false;

	let agreementContent = '';

	const init = async () => {
		try {
			const res = await fetch('/agreement.md');
			if (res.ok) {
				const text = await res.text();
				agreementContent = DOMPurify.sanitize(marked.parse(text));
			} else {
				agreementContent = 'Failed to load agreement content.';
			}
		} catch (e) {
			console.error(e);
			agreementContent = 'Error loading agreement content.';
		}
	};

	$: if (show) {
		init();
	}

	const handleAgree = () => {
		localStorage.setItem('agreedToTerms', 'true');
		show = false;
	};
</script>

<Modal bind:show size="xl" dismissible={false}>
	<div class="px-6 pt-5 dark:text-white text-black">
		<div class="flex justify-between items-start">
			<div class="text-xl font-medium">
				{$i18n.t('Agreement')}
			</div>
		</div>
	</div>

	<div class="w-full p-4 px-5 text-gray-700 dark:text-gray-100">
		<div class="overflow-y-scroll max-h-[60vh] scrollbar-hidden prose dark:prose-invert max-w-none">
			{@html agreementContent}
		</div>
		<div class="flex justify-end pt-5 text-sm font-medium">
			<button
				on:click={handleAgree}
				class="px-5 py-2 text-sm font-medium bg-black hover:bg-gray-900 text-white dark:bg-white dark:text-black dark:hover:bg-gray-100 transition rounded-full"
			>
				동의하기
			</button>
		</div>
	</div>
</Modal>
