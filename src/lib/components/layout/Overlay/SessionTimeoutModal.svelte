<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import Modal from '$lib/components/common/Modal.svelte';

	export let show = false;
	export let countdown = 60;

	const dispatch = createEventDispatcher();

	const onExtend = () => {
		dispatch('extend');
	};

	const onLogout = () => {
		dispatch('logout');
	};
</script>

<Modal size="sm" bind:show>
	<div class="p-6">
		<div class="flex justify-between items-center mb-4">
			<h3 class="text-lg font-semibold text-gray-900 dark:text-gray-100">세션 만료 경고</h3>
		</div>

		<div class="mb-6 text-gray-600 dark:text-gray-300">
			<p>보안을 위해 <strong>{countdown}초</strong> 후 자동 로그아웃됩니다.</p>
			<p>계속 사용하시려면 연장 버튼을 눌러주세요.</p>
		</div>

		<div class="flex justify-end gap-3">
			<button
				class="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 dark:text-gray-200 dark:bg-gray-800 dark:hover:bg-gray-700 transition-colors"
				on:click={onLogout}
			>
				로그아웃
			</button>
			<button
				class="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
				on:click={onExtend}
			>
				연장하기
			</button>
		</div>
	</div>
</Modal>
