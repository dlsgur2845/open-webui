<script lang="ts">
	import { toast } from 'svelte-sonner';
	import { onMount, onDestroy, tick, getContext } from 'svelte';
	import { openDB, deleteDB } from 'idb';
	import fileSaver from 'file-saver';
	const { saveAs } = fileSaver;

	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { fade } from 'svelte/transition';

	import { getModels, getToolServersData, getVersionUpdates } from '$lib/apis';
	import { getTools } from '$lib/apis/tools';
	import { getBanners } from '$lib/apis/configs';
	import { getTerminalServers } from '$lib/apis/terminal';
	import { getUserSettings } from '$lib/apis/users';
	import { refreshSession, userSignOut } from '$lib/apis/auths';
	import { setTextScale } from '$lib/utils/text-scale';

	import { WEBUI_VERSION, WEBUI_API_BASE_URL } from '$lib/constants';
	import { compareVersion } from '$lib/utils';

	import {
		config,
		user,
		settings,
		models,
		knowledge,
		tools,
		functions,
		tags,
		banners,
		showSettings,
		showShortcuts,
		showChangelog,
		temporaryChatEnabled,
		toolServers,
		terminalServers,
		selectedTerminalId,
		showSearch,
		showSidebar,
		showControls,
		mobile
	} from '$lib/stores';

	import Sidebar from '$lib/components/layout/Sidebar.svelte';
	import SettingsModal from '$lib/components/chat/SettingsModal.svelte';
	// import ChangelogModal from '$lib/components/ChangelogModal.svelte';
	import AgreementModal from '$lib/components/AgreementModal.svelte';
	import AccountPending from '$lib/components/layout/Overlay/AccountPending.svelte';
	import SessionTimeoutModal from '$lib/components/layout/Overlay/SessionTimeoutModal.svelte';
	import UpdateInfoToast from '$lib/components/layout/UpdateInfoToast.svelte';
	import Spinner from '$lib/components/common/Spinner.svelte';
	import ArrowPath from '$lib/components/icons/ArrowPath.svelte';
	import { Shortcut, shortcuts } from '$lib/shortcuts';

	let showTimeoutModal = false;
	let showAgreement = false;

	// Token Refresh State
	let lastRefresh = Date.now();
	let clockSkew = 0;
	let tokenDuration = 60 * 60; // Default 1 hour

	// Auto refresh on user activity (sliding session): a user action while the
	// token is past half of its lifetime triggers a renewal — no activity
	// window is tracked, only the moment of actual use counts.
	const MIN_AUTO_REFRESH_INTERVAL = 10 * 1000; // ms - minimum gap between auto refresh attempts (spaces out retries on failure)
	let autoRefreshInFlight = false;
	let lastAutoRefreshAttempt = 0;
	let timerInterval: ReturnType<typeof setInterval> | null = null;
	// Tokens live in sessionStorage (per tab) while the backend enforces a single
	// JTI per user, so a refresh in one tab invalidates every other tab's token.
	// Broadcast refreshed tokens so all tabs stay on the current one.
	let sessionChannel: BroadcastChannel | null = null;

	const i18n = getContext('i18n');

	let loaded = false;
	let DB = null;
	let localDBChats = [];

	let version;

	const clearChatInputStorage = () => {
		const chatInputKeys = Object.keys(localStorage).filter((key) => key.startsWith('chat-input'));
		if (chatInputKeys.length > 0) {
			chatInputKeys.forEach((key) => {
				localStorage.removeItem(key);
			});
		}
	};

	const checkLocalDBChats = async () => {
		try {
			// Check if IndexedDB exists
			DB = await openDB('Chats', 1);

			if (!DB) {
				return;
			}

			const chats = await DB.getAllFromIndex('chats', 'timestamp');
			localDBChats = chats.map((item, idx) => chats[chats.length - 1 - idx]);

			if (localDBChats.length === 0) {
				await deleteDB('Chats');
			}
		} catch (error) {
			// IndexedDB Not Found
		}
	};

	const setUserSettings = async (cb?: () => Promise<void>) => {
		let userSettings = await getUserSettings(sessionStorage.token).catch((error) => {
			console.error(error);
			return null;
		});

		if (!userSettings) {
			try {
				userSettings = JSON.parse(localStorage.getItem('settings') ?? '{}');
			} catch (e: unknown) {
				console.error('Failed to parse settings from localStorage', e);
				userSettings = {};
			}
		}

		if (userSettings?.ui) {
			settings.set(userSettings.ui);
		}

		setTextScale($settings?.textScale ?? 1);

		if (cb) {
			await cb();
		}
	};

	const setModels = async () => {
		models.set(
			await getModels(
				sessionStorage.token,
				$config?.features?.enable_direct_connections ? ($settings?.directConnections ?? null) : null
			)
		);
	};

	const setToolServers = async () => {
		let toolServersData = await getToolServersData($settings?.toolServers ?? []);
		toolServersData = toolServersData.filter((data) => {
			if (!data || data.error) {
				toast.error(
					$i18n.t(`Failed to connect to {{URL}} OpenAPI tool server`, {
						URL: data?.url
					})
				);
				return false;
			}
			return true;
		});
		toolServers.set(toolServersData);

		// Inject enabled terminal servers as always-on tool servers
		const enabledTerminals = ($settings?.terminalServers ?? []).filter((s) => s.enabled);
		if (enabledTerminals.length > 0) {
			let terminalServersData = await getToolServersData(
				enabledTerminals.map((t) => ({
					url: t.url,
					auth_type: t.auth_type ?? 'bearer',
					key: t.key ?? '',
					path: t.path ?? '/openapi.json',
					config: { enable: true }
				}))
			);
			terminalServersData = terminalServersData
				.filter((data) => {
					if (!data || data.error) {
						toast.error(
							$i18n.t(`Failed to connect to {{URL}} terminal server`, {
								URL: data?.url
							})
						);
						return false;
					}
					return true;
				})
				.map((data, i) => ({
					...data,
					key: enabledTerminals[i]?.key ?? ''
				}));

			terminalServers.set(terminalServersData);
		} else {
			terminalServers.set([]);
		}

		// Fetch terminal servers the user has access to (for FileNav + terminal_id)
		const systemTerminals = await getTerminalServers(sessionStorage.token);
		if (systemTerminals.length > 0) {
			// Store with proxy URL and session key for FileNav file browsing
			const terminalEntries = systemTerminals.map((t) => ({
				id: t.id,
				url: `${WEBUI_API_BASE_URL}/terminals/${t.id}`,
				name: t.name,
				key: sessionStorage.token
			}));
			terminalServers.update((existing) => [...existing, ...terminalEntries]);
		}
	};

	const setBanners = async () => {
		const bannersData = await getBanners(sessionStorage.token);
		banners.set(bannersData);
	};

	const setTools = async () => {
		const toolsData = await getTools(sessionStorage.token);
		tools.set(toolsData);
	};

	// Helper functions defined at top-level
	// 사용자 조작(click, keydown, touchstart, scroll)마다 호출:
	// 실제 사용 시점에만, 토큰 수명의 절반이 지난 경우에만 세션을 갱신한다.
	// 마우스 포인터 이동(mousemove)은 수동적 동작이라 갱신 트리거에서 제외.
	// attemptAutoRefresh가 고빈도 이벤트를 스로틀링한다.
	const onUserActivity = () => {
		if (!$user?.expires_at) {
			return;
		}
		const diff = $user.expires_at - (Math.floor(Date.now() / 1000) - clockSkew);
		if (diff > 0 && diff <= Math.floor(tokenDuration / 2)) {
			attemptAutoRefresh();
		}
	};

	const calculateClockSkew = (serverTimestamp: number) => {
		if (serverTimestamp) {
			const now = Math.floor(Date.now() / 1000);
			clockSkew = now - serverTimestamp;
			console.log('Clock skew:', clockSkew);
		}
	};

	const adoptRefreshedToken = (res: any) => {
		sessionStorage.token = res.token;
		if (res.expires_at) {
			user.update((u: any) => ({ ...u, expires_at: res.expires_at }));

			if (res.server_timestamp) {
				tokenDuration = res.expires_at - res.server_timestamp;
			}
		}
		if (res.server_timestamp) {
			calculateClockSkew(res.server_timestamp);
		}
		lastRefresh = Date.now();
		showTimeoutModal = false;
	};

	// Coalesce concurrent callers (timer, manual button, modal extend) onto one
	// request: the backend rotates the JTI on every refresh, so parallel refreshes
	// can leave the stored token and the DB JTI out of sync.
	let refreshPromise: Promise<void> | null = null;
	const refreshSessionHelper = () => {
		if (refreshPromise) {
			return refreshPromise;
		}
		refreshPromise = (async () => {
			if (!sessionStorage.token) {
				return;
			}
			try {
				const res = await refreshSession(sessionStorage.token);
				if (res && res.token) {
					adoptRefreshedToken(res);
					sessionChannel?.postMessage({
						type: 'token-refreshed',
						token: res.token,
						expires_at: res.expires_at,
						server_timestamp: res.server_timestamp
					});
				}
			} catch (err: any) {
				console.error('Refresh failed:', err);
				if (err?.status === 401) {
					await localStorage.removeItem('token');
					await sessionStorage.removeItem('token');
					await user.set(null);
					window.location.href = '/auth';
				}
			}
		})().finally(() => {
			refreshPromise = null;
		});
		return refreshPromise;
	};

	onMount(async () => {
		if ($user === undefined || $user === null) {
			await goto('/auth');
			return;
		}
		if (!['user', 'admin'].includes($user?.role)) {
			return;
		}

		// 로그인/세션 응답의 server_timestamp로 시계 차이를 즉시 보정한다.
		// 첫 토큰 갱신 전까지 clockSkew=0이면, 서버 시계가 브라우저보다 느릴 때
		// 아래 1초 타이머가 만료로 오판해 로그인 직후 바로 로그아웃되는 문제가 있었다.
		if ($user?.server_timestamp) {
			calculateClockSkew($user.server_timestamp);
			if ($user?.expires_at) {
				tokenDuration = $user.expires_at - $user.server_timestamp;
			}
		}

		clearChatInputStorage();
		await Promise.all([
			checkLocalDBChats(),
			setBanners().catch((e) => console.error('Failed to load banners:', e)),
			setTools().catch((e) => console.error('Failed to load tools:', e)),
			setUserSettings(async () => {
				await setModels().catch((e) => console.error('Failed to load models:', e));
			}).catch((e) => console.error('Failed to load user settings:', e))
		]);

		// Tool servers can be slow or unreachable; they are not needed to initialize chat.
		setToolServers().catch((e) => console.error('Failed to load tool servers:', e));

		// Helper function to check if the pressed keys match the shortcut definition
		const isShortcutMatch = (event: KeyboardEvent, shortcut): boolean => {
			const keys = shortcut?.keys || [];

			const normalized = keys.map((k) => k.toLowerCase());
			const needCtrl = normalized.includes('ctrl') || normalized.includes('mod');
			const needShift = normalized.includes('shift');
			const needAlt = normalized.includes('alt');

			const mainKeys = normalized.filter((k) => !['ctrl', 'shift', 'alt', 'mod'].includes(k));

			// Get the main key pressed
			const keyPressed = event.key.toLowerCase();

			// Check modifiers
			if (needShift && !event.shiftKey) return false;

			if (needCtrl && !(event.ctrlKey || event.metaKey)) return false;
			if (!needCtrl && (event.ctrlKey || event.metaKey)) return false;
			if (needAlt && !event.altKey) return false;
			if (!needAlt && event.altKey) return false;

			if (mainKeys.length && !mainKeys.includes(keyPressed)) return false;

			return true;
		};

		const setupKeyboardShortcuts = () => {
			document.addEventListener('keydown', async (event) => {
				if (isShortcutMatch(event, shortcuts[Shortcut.SEARCH])) {
					console.log('Shortcut triggered: SEARCH');
					event.preventDefault();
					showSearch.set(!$showSearch);
				} else if (isShortcutMatch(event, shortcuts[Shortcut.NEW_CHAT])) {
					console.log('Shortcut triggered: NEW_CHAT');
					event.preventDefault();
					document.getElementById('sidebar-new-chat-button')?.click();
				} else if (isShortcutMatch(event, shortcuts[Shortcut.FOCUS_INPUT])) {
					console.log('Shortcut triggered: FOCUS_INPUT');
					event.preventDefault();
					document.getElementById('chat-input')?.focus();
				} else if (isShortcutMatch(event, shortcuts[Shortcut.COPY_LAST_CODE_BLOCK])) {
					console.log('Shortcut triggered: COPY_LAST_CODE_BLOCK');
					event.preventDefault();
					[...document.getElementsByClassName('copy-code-button')]?.at(-1)?.click();
				} else if (isShortcutMatch(event, shortcuts[Shortcut.COPY_LAST_RESPONSE])) {
					console.log('Shortcut triggered: COPY_LAST_RESPONSE');
					event.preventDefault();
					[...document.getElementsByClassName('copy-response-button')]?.at(-1)?.click();
				} else if (isShortcutMatch(event, shortcuts[Shortcut.TOGGLE_SIDEBAR])) {
					console.log('Shortcut triggered: TOGGLE_SIDEBAR');
					event.preventDefault();
					showSidebar.set(!$showSidebar);
				} else if (isShortcutMatch(event, shortcuts[Shortcut.DELETE_CHAT])) {
					console.log('Shortcut triggered: DELETE_CHAT');
					event.preventDefault();
					document.getElementById('delete-chat-button')?.click();
				} else if (isShortcutMatch(event, shortcuts[Shortcut.OPEN_SETTINGS])) {
					console.log('Shortcut triggered: OPEN_SETTINGS');
					event.preventDefault();
					showSettings.set(!$showSettings);
				} else if (isShortcutMatch(event, shortcuts[Shortcut.SHOW_SHORTCUTS])) {
					console.log('Shortcut triggered: SHOW_SHORTCUTS');
					event.preventDefault();
					showShortcuts.set(!$showShortcuts);
				} else if (isShortcutMatch(event, shortcuts[Shortcut.CLOSE_MODAL])) {
					console.log('Shortcut triggered: CLOSE_MODAL');
					event.preventDefault();
					showSettings.set(false);
					showShortcuts.set(false);
				} else if (isShortcutMatch(event, shortcuts[Shortcut.OPEN_MODEL_SELECTOR])) {
					console.log('Shortcut triggered: OPEN_MODEL_SELECTOR');
					event.preventDefault();
					document.getElementById('model-selector-0-button')?.click();
				} else if (isShortcutMatch(event, shortcuts[Shortcut.NEW_TEMPORARY_CHAT])) {
					console.log('Shortcut triggered: NEW_TEMPORARY_CHAT');
					event.preventDefault();
					if ($user?.role !== 'admin' && $user?.permissions?.chat?.temporary_enforced) {
						temporaryChatEnabled.set(true);
					} else {
						temporaryChatEnabled.set(!$temporaryChatEnabled);
					}
					await goto('/');
					setTimeout(() => {
						document.getElementById('new-chat-button')?.click();
					}, 0);
				} else if (isShortcutMatch(event, shortcuts[Shortcut.GENERATE_MESSAGE_PAIR])) {
					console.log('Shortcut triggered: GENERATE_MESSAGE_PAIR');
					event.preventDefault();
					document.getElementById('generate-message-pair-button')?.click();
				} else if (
					isShortcutMatch(event, shortcuts[Shortcut.REGENERATE_RESPONSE]) &&
					document.activeElement?.id === 'chat-input'
				) {
					console.log('Shortcut triggered: REGENERATE_RESPONSE');
					event.preventDefault();
					[...document.getElementsByClassName('regenerate-response-button')]?.at(-1)?.click();
				}
			});
		};
		setupKeyboardShortcuts();

		if ($user?.role === 'admin' || ($user?.permissions?.chat?.temporary ?? true)) {
			if ($page.url.searchParams.get('temporary-chat') === 'true') {
				temporaryChatEnabled.set(true);
			}

			if ($user?.role !== 'admin' && $user?.permissions?.chat?.temporary_enforced) {
				temporaryChatEnabled.set(true);
			}
		}

		// Check for version updates
		if ($user?.role === 'admin' && $config?.features?.enable_version_update_check) {
			// Check if the user has dismissed the update toast in the last 24 hours
			if (localStorage.dismissedUpdateToast) {
				const dismissedUpdateToast = new Date(Number(localStorage.dismissedUpdateToast));
				const now = new Date();

				if (now - dismissedUpdateToast > 24 * 60 * 60 * 1000) {
					checkForVersionUpdates();
				}
			} else {
				checkForVersionUpdates();
			}
		}
		// Persist showControls: track open/close state separately from saved size
		// chatControlsSize always retains the last width for openPane()
		await showControls.set(!$mobile ? localStorage.showControls === 'true' : false);
		showControls.subscribe((value) => {
			localStorage.showControls = value ? 'true' : 'false';
		});

		// Persist selectedTerminalId across page loads
		selectedTerminalId.set(localStorage.selectedTerminalId ?? null);
		selectedTerminalId.subscribe((value) => {
			if (value === null) {
				delete localStorage.selectedTerminalId;
			} else {
				localStorage.selectedTerminalId = value;
			}
		});

		// Runs once at mount (config is loaded by the root layout before this mounts);
		// refreshSessionHelper keeps tokenDuration up to date afterwards.
		if ($config?.features?.jwt_expires_in) {
			const configDuration = parseFloat($config.features.jwt_expires_in);
			if (!isNaN(configDuration) && configDuration > 0) {
				tokenDuration = configDuration;
			}
		}

		if (typeof BroadcastChannel !== 'undefined') {
			sessionChannel = new BroadcastChannel('session-token');
			sessionChannel.onmessage = (event: MessageEvent) => {
				const msg = event.data;
				if (msg?.type === 'token-refreshed' && msg.token) {
					adoptRefreshedToken(msg);
				}
			};
		}

		window.addEventListener('keydown', onUserActivity);
		window.addEventListener('click', onUserActivity);
		window.addEventListener('touchstart', onUserActivity);
		// capture: true so scrolling inside nested containers (chat list, sidebar) counts too
		window.addEventListener('scroll', onUserActivity, true);

		// Integrated Timer & Auto Refresh (check every second)
		timerInterval = setInterval(async () => {
			if ($user?.expires_at) {
				// Use server time for calculation: now - clockSkew
				const currentServerTime = Math.floor(Date.now() / 1000) - clockSkew;
				const diff = $user.expires_at - currentServerTime;

				const isVisible = document.visibilityState === 'visible';
				// warningThreshold: When to show the modal
				// If token duration > 60s, show at 60s remaining.
				// If token duration <= 60s, show at 10s remaining.
				const warningThreshold = tokenDuration > 60 ? 60 : 10;

				if (diff <= 0) {
					if (timerInterval) {
						clearInterval(timerInterval);
					}
					await logoutHandler();
					return;
				}

				// Auto refresh is event-driven (onUserActivity) — the timer only
				// handles expiry, the warning modal and the countdown badge.
				if (diff <= warningThreshold) {
					console.log(
						`[Timer] Show Modal: diff=${diff}, threshold=${warningThreshold}, isVisible=${isVisible}, showing=${showTimeoutModal}`
					);
					if (isVisible && !showTimeoutModal) {
						showTimeoutModal = true;
					}
				} else {
					if (showTimeoutModal) {
						showTimeoutModal = false;
					}
				}

				modalCountdown = Math.max(0, diff);

				if (diff > 0) {
					const m = Math.floor(diff / 60);
					const s = diff % 60;
					timeRemaining = `로그아웃 ${m}분 ${s}초 남음`;
					isExpiringSoon = diff < 60;
				} else {
					timeRemaining = '만료됨';
					isExpiringSoon = true;
				}
			} else {
				timeRemaining = '';
				isExpiringSoon = false;
			}
		}, 1000);

		await tick();

		if (!localStorage.getItem('agreedToTerms')) {
			showAgreement = true;
		}

		loaded = true;
	});

	// onMount is async, so a cleanup function returned from it would be ignored —
	// teardown must live in onDestroy.
	onDestroy(() => {
		window.removeEventListener('keydown', onUserActivity);
		window.removeEventListener('click', onUserActivity);
		window.removeEventListener('touchstart', onUserActivity);
		window.removeEventListener('scroll', onUserActivity, true);
		if (timerInterval) {
			clearInterval(timerInterval);
		}
		sessionChannel?.close();
	});

	const logoutHandler = async () => {
		let redirectUrl = '/auth';
		try {
			const res = await userSignOut();
			if (res?.redirect_url) {
				redirectUrl = res.redirect_url;
			}
		} catch (e) {
			console.error(e);
		}
		// Fallback clearing just in case
		await localStorage.removeItem('token');
		await sessionStorage.removeItem('token');
		await user.set(null);

		// Force reload to clear state and ensure clean logout
		window.location.href = redirectUrl;
	};

	const attemptAutoRefresh = async () => {
		if (autoRefreshInFlight) {
			return;
		}
		const now = Date.now();
		if (now - lastAutoRefreshAttempt < MIN_AUTO_REFRESH_INTERVAL) {
			return;
		}
		lastAutoRefreshAttempt = now;
		autoRefreshInFlight = true;
		try {
			await refreshSessionHelper();
		} finally {
			autoRefreshInFlight = false;
		}
	};

	let manualRefreshLoading = false;
	const onManualRefresh = async () => {
		if (manualRefreshLoading) return;
		manualRefreshLoading = true;
		await refreshSessionHelper();
		setTimeout(() => {
			manualRefreshLoading = false;
		}, 10000); // 10s cooldown
	};

	const checkForVersionUpdates = async () => {
		version = await getVersionUpdates(sessionStorage.token).catch((error) => {
			return {
				current: WEBUI_VERSION,
				latest: WEBUI_VERSION
			};
		});
	};

	let timeRemaining = '';
	let isExpiringSoon = false;
	let modalCountdown = 0;
</script>

<SettingsModal bind:show={$showSettings} />
<!-- <ChangelogModal bind:show={$showChangelog} /> -->
<AgreementModal bind:show={showAgreement} />

{#if version && compareVersion(version.latest, version.current) && ($settings?.showUpdateToast ?? true)}
	<div class=" absolute bottom-8 right-8 z-50" in:fade={{ duration: 100 }}>
		<UpdateInfoToast
			{version}
			on:close={() => {
				localStorage.setItem('dismissedUpdateToast', Date.now().toString());
				version = null;
			}}
		/>
	</div>
{/if}

{#if timeRemaining}
	<div
		class="fixed top-4 right-36 z-[999] flex items-center gap-2 px-3 py-1.5 rounded-full backdrop-blur-md shadow-sm border border-gray-100 dark:border-gray-800 bg-white/80 dark:bg-gray-900/80 transition-all duration-300"
	>
		<div
			class="text-xs font-mono font-medium tabular-nums transition-colors duration-300 {isExpiringSoon
				? 'text-red-500 animate-pulse'
				: 'text-gray-600 dark:text-gray-300'}"
		>
			{timeRemaining}
		</div>

		<button
			class="p-0.5 rounded-full hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors disabled:opacity-30 disabled:cursor-not-allowed group"
			on:click={onManualRefresh}
			disabled={manualRefreshLoading || timeRemaining === '만료됨'}
			title="세션 연장 (10초 대기)"
		>
			<div
				class={manualRefreshLoading
					? 'animate-spin'
					: 'group-hover:rotate-180 transition-transform duration-500'}
			>
				<ArrowPath className="size-3.5 text-gray-500 dark:text-gray-400" />
			</div>
		</button>
	</div>
{/if}

{#if $user}
	<div class="app relative">
		<div
			class=" text-gray-700 dark:text-gray-100 bg-white dark:bg-gray-900 h-screen max-h-[100dvh] overflow-auto flex flex-row justify-end"
		>
			{#if !['user', 'admin'].includes($user?.role)}
				<AccountPending />
			{:else}
				{#if localDBChats.length > 0}
					<div class="fixed w-full h-full flex z-50">
						<div
							class="absolute w-full h-full backdrop-blur-md bg-white/20 dark:bg-gray-900/50 flex justify-center"
						>
							<div class="m-auto pb-44 flex flex-col justify-center">
								<div class="max-w-md">
									<div class="text-center dark:text-white text-2xl font-medium z-50">
										{$i18n.t('Important Update')}<br />
										{$i18n.t('Action Required for Chat Log Storage')}
									</div>

									<div class=" mt-4 text-center text-sm dark:text-gray-200 w-full">
										{$i18n.t(
											"Saving chat logs directly to your browser's storage is no longer supported. Please take a moment to download and delete your chat logs by clicking the button below. Don't worry, you can easily re-import your chat logs to the backend through"
										)}
										<span class="font-medium dark:text-white"
											>{$i18n.t('Settings')} > {$i18n.t('Chats')} > {$i18n.t('Import Chats')}</span
										>. {$i18n.t(
											'This ensures that your valuable conversations are securely saved to your backend database. Thank you!'
										)}
									</div>

									<div class=" mt-6 mx-auto relative group w-fit">
										<button
											class="relative z-20 flex px-5 py-2 rounded-full bg-white border border-gray-100 dark:border-none hover:bg-gray-100 transition font-medium text-sm"
											on:click={async () => {
												let blob = new Blob([JSON.stringify(localDBChats)], {
													type: 'application/json'
												});
												saveAs(blob, `chat-export-${Date.now()}.json`);

												const tx = DB.transaction('chats', 'readwrite');
												await Promise.all([tx.store.clear(), tx.done]);
												await deleteDB('Chats');

												localDBChats = [];
											}}
										>
											{$i18n.t('Download & Delete')}
										</button>

										<button
											class="text-xs text-center w-full mt-2 text-gray-400 underline"
											on:click={async () => {
												localDBChats = [];
											}}>{$i18n.t('Close')}</button
										>
									</div>
								</div>
							</div>
						</div>
					</div>
				{/if}

				<Sidebar />

				{#if loaded}
					<slot />
				{:else}
					<div
						class="w-full flex-1 h-full flex items-center justify-center {$showSidebar
							? '  md:max-w-[calc(100%-var(--sidebar-width))]'
							: ' '}"
					>
						<Spinner className="size-5" />
					</div>
				{/if}
			{/if}
		</div>
	</div>
{/if}

<SessionTimeoutModal
	bind:show={showTimeoutModal}
	countdown={modalCountdown}
	on:extend={async () => {
		await refreshSessionHelper();
	}}
	on:logout={logoutHandler}
/>

<style>
	.loading {
		display: inline-block;
		clip-path: inset(0 1ch 0 0);
		animation: l 1s steps(3) infinite;
		letter-spacing: -0.5px;
	}

	@keyframes l {
		to {
			clip-path: inset(0 -1ch 0 0);
		}
	}

	pre[class*='language-'] {
		position: relative;
		overflow: auto;

		/* make space  */
		margin: 5px 0;
		padding: 1.75rem 0 1.75rem 1rem;
		border-radius: 10px;
	}

	pre[class*='language-'] button {
		position: absolute;
		top: 5px;
		right: 5px;

		font-size: 0.9rem;
		padding: 0.15rem;
		background-color: #828282;

		border: ridge 1px #7b7b7c;
		border-radius: 5px;
		text-shadow: #c4c4c4 0 0 2px;
	}

	pre[class*='language-'] button:hover {
		cursor: pointer;
		background-color: #bcbabb;
	}
</style>
