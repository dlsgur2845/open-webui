# Open WebUI 커스텀 마이그레이션 가이드 (0.6.43-fix1 -> 0.7.2-fix1)

본 문서는 **Open WebUI 0.6.43-fix1** 버전에 적용된 커스텀 사항들을 **0.7.2-fix1** 버전으로 이관하기 위한 상세 작업 지침서입니다.

---

## 1. 개요 및 사전 준비

*   **목표**: 0.6.43-fix1의 보안 강화(세션, JTI, 관리자 차단) 및 데이터 정책(채팅 삭제, 약관 동의) 기능을 0.7.2 기반의 커스텀 버전(0.7.2-fix1)에 동일하게 적용.
*   **주의사항**: 0.7.2 버전의 베이스 코드가 변경되었을 수 있으므로, 라인 번호보다는 **코드의 문맥(Context)**을 보고 삽입 위치를 찾으십시오.

---

## 2. 백엔드 (Backend) 변경 사항

### 2.1. 의존성 추가 (`Dockerfile`)
문서 파싱 호환성을 위한 패키지를 추가합니다.

**파일**: `Dockerfile`
```dockerfile
# (기존) RUN pip3 install --no-cache-dir uv && ...
# 아래 내용을 pip3 install 라인에 추가하거나 별도의 RUN 명령어로 추가
RUN pip3 install --no-cache-dir msoffcrypto-tool chardet nltk pyhwp
```

### 2.2. 환경 설정 (`backend/open_webui/env.py`)
새로운 환경 변수를 로드합니다.

**파일**: `backend/open_webui/env.py`
```python
# ... 기존 환경변수 로드 부분 하단에 추가
DISABLE_ADMIN = os.environ.get("DISABLE_ADMIN", "False").lower() == "true"
```

### 2.3. 설정 관리 (`backend/open_webui/config.py`)
`AppConfig` 클래스나 관련 설정 로직에 새 변수를 매핑합니다.

**파일**: `backend/open_webui/config.py`
```python
# ... (상단 import 부분)
from open_webui.env import (
    # ... 기존 import
    DISABLE_ADMIN, # 추가
)

# ... (AppConfig 클래스 내부 혹은 전역 설정 변수)
class AppConfig:
    # ...
    CHAT_DELETE_ENABLED: bool = False
    CHAT_DELETE_DAYS: int = 365
    DISABLE_ADMIN: bool = DISABLE_ADMIN # 추가
    # ...
```

### 2.4. 메인 로직 및 주기적 작업 (`backend/open_webui/main.py`)
채팅 자동 삭제 스케줄러와 프론트엔드로 전달할 설정값을 추가합니다.

**파일**: `backend/open_webui/main.py`
```python
# [Import 추가]
from open_webui.config import (
    # ...
    CHAT_DELETE_ENABLED,
    CHAT_DELETE_DAYS,
)
from open_webui.env import (
    # ...
    DISABLE_ADMIN,
)

# [lifespan 함수 내부] (앱 시작 시 실행되는 로직)
async def lifespan(app: FastAPI):
    # ... (기존 코드)

    # --- [추가 시작] ---
    async def periodic_chat_deletion():
        while True:
            if app.state.config.CHAT_DELETE_ENABLED:
                try:
                    days = app.state.config.CHAT_DELETE_DAYS
                    # log.info(f"Running periodic chat deletion for chats older than {days} days")
                    count = await anyio.to_thread.run_sync(
                        Chats.delete_chats_older_than, days
                    )
                    if count > 0:
                        log.info(f"Deleted {count} old chats")
                except Exception as e:
                    log.error(f"Error in periodic chat deletion: {e}")
            
            # Check every hour
            await asyncio.sleep(60 * 60)

    asyncio.create_task(periodic_chat_deletion())
    # --- [추가 끝] ---
    
    # ...

# [get_app_config 함수 내부] (프론트엔드 config API)
async def get_app_config(request: Request):
    # ...
    return {
        # ...
        "disable_admin": DISABLE_ADMIN, # 추가
        # ...
    }
```

### 2.5. 인증 및 권한 로직 (`backend/open_webui/utils/auth.py`)
관리자 접근 차단 로직을 추가합니다.

**파일**: `backend/open_webui/utils/auth.py`
```python
# [Import 추가]
from open_webui.env import DISABLE_ADMIN

# [get_admin_user 함수 수정]
def get_admin_user(user=Depends(get_current_user)):
    # --- [추가 시작] ---
    if DISABLE_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ERROR_MESSAGES.ACCESS_PROHIBITED,
        )
    # --- [추가 끝] ---

    if user.role != "admin":
        raise HTTPException(...)
    return user
```

### 2.6. 인증 라우터 (`backend/open_webui/routers/auths.py`)
클라이언트와의 시간 동기화를 위해 서버 타임스탬프를 응답에 포함합니다.

**파일**: `backend/open_webui/routers/auths.py`
```python
# [SessionUserResponse 클래스 등 수정]
class SessionUserResponse(Token, UserProfileImageResponse):
    # ...
    server_timestamp: Optional[int] = None # 추가

# [get_session_user, signin 등의 함수 반환값 수정]
# return 문 내의 딕셔너리에 추가:
# "server_timestamp": int(time.time()),
```

### 2.7. 데이터베이스 모델 (`backend/open_webui/models/chats.py`)
오래된 채팅 삭제 메서드를 추가합니다.

**파일**: `backend/open_webui/models/chats.py`
```python
    # [ChatTable 클래스 내부 메서드 추가]
    def delete_chats_older_than(self, days: int) -> int:
        try:
            with get_db() as db:
                cutoff_time = int(time.time()) - (days * 24 * 60 * 60)
                result = (
                    db.query(Chat)
                    .filter(Chat.updated_at < cutoff_time)
                    .delete(synchronize_session=False)
                )
                db.commit()
                return result
        except Exception:
            return 0
```

---

## 3. 데이터베이스 마이그레이션 (DB)

### 3.1. JTI 컬럼 추가
`alembic` 마이그레이션 파일을 생성하거나 수동으로 DB를 업데이트해야 합니다.

**파일**: `backend/open_webui/migrations/versions/xxxx_add_token_jti_to_auth.py` (새로 생성)
```python
"""add token_jti to auth"""
from alembic import op
import sqlalchemy as sa

# revision identifiers... (자동 생성됨)

def upgrade():
    op.add_column('auth', sa.Column('token_jti', sa.String(), nullable=True))

def downgrade():
    op.drop_column('auth', 'token_jti')
```

---

## 4. 프론트엔드 (Frontend) 변경 사항

### 4.1. 스토리지 변경 (전역) **[중요]**
프로젝트 전체에서 `localStorage`에 저장되는 토큰 로직을 `sessionStorage`로 변경해야 합니다.
**대상 파일**: `src/lib/apis/index.ts`, `src/routes/+layout.svelte`, 인증 관련 파일들.

*   **검색**: `localStorage.token` 및 `localStorage.getItem('token')`
*   **변경**: `sessionStorage.token` 및 `sessionStorage.getItem('token')`
*   **주의**: `AccountPending.svelte` 파일에서도 변경이 필요합니다 (`src/lib/components/layout/Overlay/AccountPending.svelte`).

### 4.2. API 클라이언트 (`src/lib/apis/index.ts`)
토큰 참조 위치 변경. (위의 4.1 전체 변경에 포함됨)

### 4.3. 레이아웃 및 보안 로직 (`src/routes/+layout.svelte`)
세션 타임아웃 감지, 글로벌 401 인터셉터, 약관 동의 모달 연결.

**파일**: `src/routes/+layout.svelte` (또는 `src/routes/(app)/+layout.svelte`)

**1. Import 및 State 추가**
```javascript
// [script]
import AgreementModal from '$lib/components/AgreementModal.svelte'; // 추가
import SessionTimeoutModal from '$lib/components/layout/Overlay/SessionTimeoutModal.svelte'; // 추가

// ...
let showTimeoutModal = false; // 추가
let showAgreement = false; // 추가

// ...
```

**2. 세션 체크 타이머 로직 (onMount 내부에 추가)**
```javascript
// Integrated Timer & Auto Refresh (check every second)
const timerInterval = setInterval(async () => {
    if ($user?.expires_at) {
        // Use server time for calculation: now - clockSkew
        const currentServerTime = Math.floor(Date.now() / 1000) - clockSkew;
        const diff = $user.expires_at - currentServerTime;

        // Logic: No Auto-Refresh. Show Modal if expiring.
        const isVisible = document.visibilityState === 'visible';
        // warningThreshold: When to show the modal
        const warningThreshold = tokenDuration > 60 ? 60 : 10;

        if (diff <= 0) {
            clearInterval(timerInterval);
            await logoutHandler();
            return;
        }

        if (diff <= warningThreshold) {
            if (isVisible && !showTimeoutModal) {
                showTimeoutModal = true;
            }
        } else {
            if (showTimeoutModal) {
                showTimeoutModal = false;
            }
        }

        modalCountdown = Math.max(0, diff);
        // ... (timeRemaining UI 업데이트 로직 - 선택 사항)
    }
}, 1000);

// 약관 동의 체크 (onMount 내부, 하단)
if (!localStorage.getItem('agreedToTerms')) {
    showAgreement = true;
}

// cleanup
return () => {
    // ...
    clearInterval(timerInterval);
};
```

**3. HTML 추가 (파일 하단부)**
```svelte
<AgreementModal bind:show={showAgreement} /> <!-- 추가 -->
<SessionTimeoutModal
    bind:show={showTimeoutModal}
    countdown={modalCountdown}
    on:extend={async () => {
        await refreshSessionHelper();
    }}
    on:logout={logoutHandler}
/> <!-- 추가 -->
```

### 4.4. 인증 페이지 (`src/routes/auth/+page.svelte`)
로그인 완료 시 토큰 저장소를 `sessionStorage`로 설정하고, 이미 로그인된 유저 체크 로직 수정.

**파일**: `src/routes/auth/+page.svelte`
```javascript
// onMount 체크 로직
if ($user) { // $user가 존재하면 리다이렉트
    goto(redirectPath || '/');
}
```

### 4.5. 관리자 페이지 차단 (`src/routes/(app)/admin/+layout.svelte`)
프론트엔드 단에서도 관리자 페이지 접근을 막습니다.

**파일**: `src/routes/(app)/admin/+layout.svelte`
```javascript
import { config } from '$lib/stores'; // config 스토어 import

onMount(async () => {
    // disable_admin 체크 추가
    if ($user?.role !== 'admin' || $config?.features?.disable_admin) {
        await goto('/');
    }
    // ...
});
```

### 4.6. 신규 파일 생성

#### 4.6.1 `src/lib/components/layout/Overlay/SessionTimeoutModal.svelte`
아래 코드를 전체 복사하여 파일을 생성하십시오.
```svelte
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
```

#### 4.6.2 `src/lib/components/AgreementModal.svelte`
아래 코드를 전체 복사하여 파일을 생성하십시오.
```svelte
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
               {$i18n.t('Agree and Continue')}
           </button>
       </div>
   </div>
</Modal>
```

#### 4.6.3 `static/agreement.md`
아래 내용을 파일로 저장하십시오.
```
< 원내 중요정보 보호 및 정보주체 권리 보장을 위한 고지사항 >

1. **업무 관련 중요자료는 AI시스템에 업로드 금지**
  * ① 비밀 및 대외비 문서, ② 개인정보 및 신용정보 파일, ③ 그 밖의 업무별 비공개 자료

2. **불법, 부당한 목적의 AI시스템 이용 금지**
  * ① 시스템 또는 데이터 접근권한 획득, ② 허용된 열람범위를 벗어난 정보 탐색, ③ 필터 등 보호조치 우회 시도, ④ 그 밖의 각종 권한, 정보 탈취

3. **비윤리적 목적의 AI시스템 활용 금지**
  * ① 민감정보 입력을 유도하는 대화, ② 개인정보를 이용한 악의적 콘텐츠 생성, ③ 그 밖의 사생활 침해를 야기할 수 있는 각종 시도

※ AI시스템과 사용자 사이의 대화 내용은 책임추적성 확보를 위해 자동 저장되며, 1년 간 보관 후 자동 파기됩니다.
```

### 4.7. 모달 닫기 방지 수정 (`src/lib/components/common/Modal.svelte`)

**파일**: `src/lib/components/common/Modal.svelte`

`close()` 동작에 `dismissible` 조건을 추가합니다.

```svelte
// 기존 handleKeydown 혹은 onKeydown 함수를 찾아서 수정
const onKeydown = (e) => {
    // --- [수정] ---
    if (dismissible && e.key === 'Escape') { 
        close();
    }
};

// 기존 backdrop click 핸들러 수정
const onBackdropClick = (e) => {
    // --- [수정] ---
    if (dismissible && e.target === e.currentTarget) {
        close();
    }
};
```

---

## 5. 최종 확인

1.  [ ] `AgreementModal` 및 `agreement.md` 파일이 존재하고, 앱 최초 접속 시 약관이 뜨는가?
2.  [ ] 약관 모달 및 중요 모달의 배경을 클릭해도 닫히지 않는가? (`dismissible={false}` 동작)
3.  [ ] 세션 만료 임박 시 경고창이 뜨고 리프레시되는가?
4.  [ ] `sessionStorage` 사용으로 탭 종료 시 로그아웃되는가?

---
*Generated by Antigravity*
