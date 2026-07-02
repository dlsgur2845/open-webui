# Open WebUI 0.6.43 커스터마이징 전체 명세 (브랜치 `0.6.43-fix2.1`)

> **문서 목적**: 순정 Open WebUI **0.6.43**(포크 지점 커밋 `a7271532f`) 대비 이 저장소에 적용된 **모든 커스텀 사항**을, **마이그레이션 대상 버전인 순정 0.10.2** 위에 동일하게 재구현할 수 있는 수준으로 기술한다. (0.10.2 실측 점검 결과는 아래 전용 섹션 참조)
>
> - **비교 기준**: `a7271532f`(업스트림 0.6.43) ↔ 브랜치 `0.6.43-fix2.1` HEAD(`0f6d3c4aa`) **+ 미커밋 작업트리 변경**
> - **규모**: 변경 파일 165개 (커밋 기준 +2,827 / -781 라인, 작업트리 변경 별도)
> - **작성일**: 2026-07-02 (모든 내용은 실제 `git diff` / 소스 검증 기반이며, 검증하지 못한 부분은 본문에 "미확인"으로 표기)
> - **커버리지**: 전체 변경 파일 165개 전부가 본 문서의 파트 1~8 중 하나 이상에서 다뤄짐을 교차 검증함

---

## 커스텀 커밋 이력 (시간순, 31개)

```
2c8c04c2c 취약점 점검#1
6123e56c5 취약점 점검#2
a5955a4f0 취약점 점검#3
5759a7eb4 취약점 점검#4
453924007 취약점 점검#5
1da45db0e 취약점 점검#6
4be37956d 취약점 점검#7
7948a63ae 사용자 동의 모달 추가 및 대화 자동 삭제 기능 추가
b3b8f6476 변경사항 정리
d7fbc8924 변경사항 정리#2
528e54d48 빌드 이미지명 변경
ad66fabcc .
fa6d77876 fix(agreement): 동의 없는 모달 닫기 방지 및 버튼 한글화
702db1ef5 취약점 점검8
0fa60ef24 nltk 관련 라이브러리 추가
e2a1396a1 에러 메시지 한글화 및 파일 업로드 예외 처리 개선
98d3bdae5 feat: 비밀번호 유효성 검사 로직 강화(블랙리스트/사용자 정보 기반)
a8841c5a5 feat: Tika 엔드포인트 rmeta/text 전환, 배열 응답 처리, MIME 타입 전달
0a0f67f4c feat: Dockerfile USE_CUDA 기본값 true, docker-compose 이미지 태그 변경
1a4b2492f refactor: Dockerfile 비루트 사용자/권한 강화, Tika 로더 개선
3f76a2eb9 fix: OpenAI/Ollama 라우터 오류 응답 400 통일(HTTPException)
8497673dc feat: 이미지 캡처/웹페이지 첨부 구성 옵션 추가 및 UI 업데이트
0cb6d2410 feat: 개인정보 설정 여부에 따라 계정 UI 조건부 표시
9742cdbdf Add PostgreSQL chat cleanup script
175d21682 fix: 채팅 정리 스크립트 DB 접속을 APP_USER/APP_PASSWORD/APP_DB 로 변경
889997ef9 fix: 채팅 정리 스크립트 인자 검증 + 삭제 로그 기록
4a28f2eb5 Update cleanup_chats.sh
d816ed099 feat: 최근 7일 일별 접속자 수(DAU) 조회 스크립트 추가
380983eb0 fix: DAU 리포트 요일 표시 + 평균 DAU 주말 제외
2b4840c31 feat: 대화 감사 추적 리포트 스크립트 + 고지사항 문구 수정
0f6d3c4aa fix: docker-compose 이미지 버전 업데이트 + 웹페이지 첨부 비활성화
```

**미커밋 작업트리 변경 (2026-07-02 기준, 문서에 포함됨)**
- `src/routes/(app)/+layout.svelte`, `src/lib/apis/auths/index.ts` — 사용자 활동 감지 기반 토큰 자동 갱신(슬라이딩 세션) + 탭 간 토큰 동기화 (파트 1, 섹션 6)
- `src/lib/components/workspace/Knowledge/KnowledgeBase/AddContentMenu.svelte` — 지식베이스 "웹페이지 추가" 메뉴를 `enable_webpage_attachment` 플래그로 조건부 표시 (파트 4)

---

## 문서 구성

| 파트 | 주제 | 핵심 내용 |
|---|---|---|
| 1 | 인증/세션/토큰 보안 | JWT 수명 24h, JTI 단일 세션, `/auths/refresh`, sessionStorage 전환, 세션 타임아웃 UI, 활동 기반 자동 갱신, 비밀번호 정책, DISABLE_ADMIN |
| 2 | 백엔드 보안 강화 | 취약점 점검#1~8: 오류 응답 통일, 보안 헤더, Dockerfile 비루트, start.sh 등 |
| 3 | 이용 동의 모달·데이터 보존 정책 | AgreementModal, agreement.md 고지, 대화 1년 자동 삭제 스케줄러, ChangelogModal 비활성화 |
| 4 | 기능 토글 | ENABLE_IMAGE_CAPTURE / ENABLE_WEBPAGE_ATTACHMENT / ENABLE_USER_PERSONAL_INFO |
| 5 | 문서 파싱(Tika)·파일 업로드 | rmeta/text 전환, MIME 전달, 업로드 예외 처리·한글 에러, 파싱 의존성 |
| 6 | 프런트엔드 광범위 변경 | 대량 변경(119개 파일)의 실체 = 토큰 저장소 치환 패턴, ko-KR 번역, 기타 UI |
| 7 | 운영 스크립트·배포 구성 | cleanup_chats.sh, daily_active_users.sh, chat_audit_report.sh, docker-compose/Dockerfile |
| 8 | 커버리지 점검 | 전체 165개 파일 대조 결과 및 잔여 항목(migration_guide 문서) |

---

## 최신 버전 재적용 시 공통 주의사항

1. **라인 번호가 아니라 코드 문맥 기준으로 이식할 것.** 업스트림 리팩터링으로 파일 구조가 달라졌을 수 있다.
2. **`PersistentConfig` 값은 DB(`config` 테이블)에 영속화된다.** 코드 기본값 변경(예: `JWT_EXPIRES_IN = "24h"`)만으로는 기존 설치본에 반영되지 않으므로, 기존 DB는 관리자 UI 또는 DB에서 별도 갱신 필요.
3. **Alembic 마이그레이션 head 분기 주의.** 커스텀 마이그레이션(`token_jti`)의 `down_revision`을 대상 버전의 실제 최신 head로 지정해야 한다. 현재 저장소는 head가 2개로 갈라져 있어 자동 적용이 보장되지 않는 상태다 (파트 1, 섹션 2 참조).
4. **대량 파일 변경의 대부분은 기계적 치환이다.** `localStorage.token → sessionStorage.token` 패턴(119개 파일)은 스크립트로 일괄 치환 후 grep 검증하는 것이 안전하다 (파트 6 참조).
5. **미커밋 작업트리 변경 2건**(위 표 참조)도 이식 대상에 포함할 것. 재적용 전에 커밋해 두는 것을 권장.
6. 과거 저장소 루트에 있던 `migration_guide_0.6.43_fix1_to_0.7.2_fix1.md`(fix1 시점 요약, 0.7.2 대상)는 fix2.x 커스텀이 누락돼 **본 문서로 대체된 뒤 삭제**됐다(git 히스토리에서 열람 가능). 본문에 남아 있는 해당 가이드 언급은 분석 시점의 기록이다. **이관 작업은 본 문서만을 기준으로 할 것.**

---

## 대상 버전 0.10.2 실측 점검 결과

업스트림 `v0.10.2`(커밋 `ecd48e2f7`, 2026-07-01 릴리스) 태그를 직접 받아 커스텀 접점을 실측 대조한 결과다 (2026-07-02 확인). 아래 항목은 추정이 아니라 0.10.2 소스에서 grep/열람으로 확인한 사실이다.

### 전반 (모든 파트 공통)

- **프론트엔드는 Svelte 5.53 기반**이지만, 커스텀 이식 대상 핵심 파일(`src/routes/(app)/+layout.svelte`, `src/lib/components/common/Modal.svelte` 등)은 여전히 **레거시 문법(`export let`/`onMount`)을 사용** 중이다. 즉 커스텀 코드를 문법 변환 없이 이식할 수 있다. 단 신규 컴포넌트는 runes(`$state` 등)를 쓸 수 있으므로 파일 단위로 확인할 것.
- **백엔드 DB 모델 계층이 async로 전환됨.** `AuthsTable`의 메서드가 전부 `async def`이고 호출부는 `await Users.get_user_by_id(...)` 형태다. 커스텀 메서드 `update_user_token_jti_by_id` / `get_user_token_jti_by_id`도 **async로 작성하고 모든 호출부에서 await** 해야 한다 (파트 1, 섹션 2 코드 그대로 복사 금지).
- 신규 서브시스템 다수 추가(terminal servers, automations, calendar, memories, folders 등) — UI 커스텀 삽입 위치(메뉴, 설정 화면)가 이동했을 수 있으니 파일 단위 재확인 필요.

### 파트 1 (인증/세션) 관련

- `/api/v1/auths/refresh` 엔드포인트는 0.10.2에도 **없다** → 커스텀 그대로 필요. `SessionUserResponse` 클래스는 `routers/auths.py:214`에 존재하므로 필드 추가 방식은 동일하게 적용 가능.
- `create_token`은 여전히 `jti`를 발급하며, **`iat`(발급 시각)이 추가**됐다. 업스트림에 Redis 기반 토큰 폐기 2종이 신설됨: ① jti별 revoke(로그아웃), ② 사용자별 `revoked_at`(OIDC back-channel logout, `iat <= revoked_at`이면 거부). **DB JTI 단일 세션 커스텀과 역할이 달라 공존 가능**하며 충돌 없음. 단 `is_valid_token(decoded, redis)`로 시그니처가 바뀌었으니, JTI 대조 삽입 위치는 0.10.2 기준 `utils/auth.py`의 `get_current_user`(:315) 내 `is_valid_token` 호출(:368)과 사용자 조회 사이 문맥으로 잡을 것.
- `JWT_EXPIRES_IN` 기본값은 여전히 `'4w'`(`config.py:2391`). 다만 **PersistentConfig 클래스가 아니라 `os.getenv` + `ADMIN_CONFIG_KEYS`(`'auth.jwt_expiry'`) 매핑 방식으로 변경**됐다. 24h 정책은 env(`JWT_EXPIRES_IN=24h`) 또는 관리자 UI로 반영하는 편이 코드 수정보다 안전하다. `'-1'`(무기한) 설정 시 보안 경고를 출력하는 로직도 신설됨.
- `/api/config`의 `features`에 `jwt_expires_in` 노출이 **없다** → 프론트 세션 타이머의 전제조건이므로 main.py 커스텀(파트 1, 섹션 3)을 재적용해야 한다.
- **Alembic head = `42e2978c7933`** (`add_memory_path_and_meta`). `token_jti` 마이그레이션의 `down_revision`을 이 값으로 지정하면 head 분기 없이 깔끔하게 적용된다.
- 업스트림에 **signin rate limiter**(Redis 기반, 3분당 15회)가 추가됨 — 로그인 보안 커스텀과 중복/충돌 여부만 확인하면 됨.

### 파트 3·6 (모달/UI) 관련

- 0.10.2의 `Modal.svelte`에는 `dismissible` prop이 **없다** → 동의 모달 닫기 방지 커스텀(ESC/백드롭 조건부) 재적용 필요. Modal은 레거시 문법을 유지하고 있어 기존 패치 방식 그대로 적용 가능.
- `localStorage.token` 사용 파일이 **164개로 증가**(0.6.43 시점 119개) → sessionStorage 치환은 반드시 스크립트 일괄 처리 후 `grep -rn "localStorage.token" src/`로 검증할 것.

### 파트 5 (Tika) 관련

- Tika 로더는 여전히 `tika/text` 엔드포인트를 사용(`retrieval/loaders/main.py:163`) → `rmeta/text` 전환 + 배열 응답 처리 + MIME 전달 커스텀 재적용 필요.


---

# 파트 1. 인증/세션/토큰 보안


기준: 업스트림 `a7271532f` (v0.6.43) 대비 브랜치 `0.6.43-fix2.1` (커밋 + 미커밋 작업트리 포함). 아래 내용은 전부 실제 diff/파일 확인 기준이며, 확인하지 못한 부분은 "미확인"으로 표기했다.

---

### 1. JWT 세션 수명 단축 (기본 4주 → 24시간)

**목적/배경**
- 취약점 점검 조치. 기본 토큰 수명이 4주(`4w`)로 과도하게 길어 24시간으로 단축.

**동작 방식**
- 환경변수 `JWT_EXPIRES_IN`의 코드 기본값만 변경. `PersistentConfig`이므로 DB `config` 테이블의 `auth.jwt_expiry` 키에 영속화되고, Admin 설정 UI에서도 변경 가능.

**변경 파일 및 핵심 내용**
- `backend/open_webui/config.py`:
```python
JWT_EXPIRES_IN = PersistentConfig(
    "JWT_EXPIRES_IN", "auth.jwt_expiry", os.environ.get("JWT_EXPIRES_IN", "24h")
)
```
(업스트림은 기본값 `"4w"`)

**재적용 가이드**
- 한 줄 변경이지만 **기존 설치본은 DB config에 이미 `auth.jwt_expiry` 값이 저장돼 있으면 코드 기본값이 무시**된다. 기존 DB에는 admin 설정 UI 또는 DB 업데이트로 별도 반영 필요.
- 배포 `docker-compose.yaml`에는 `JWT_EXPIRES_IN`이 명시돼 있지 않아 이 기본값에 의존한다.

**관련 커밋**
- `453924007` 취약점 점검#5

---

### 2. JTI 기반 단일 세션 강제 (Single Session Enforcement)

**목적/배경**
- 사용자당 활성 세션(토큰)을 1개로 제한. 새 위치에서 로그인하면 이전 토큰이 즉시 무효화되고, 로그아웃 시 서버 측에서 토큰을 즉시 무효화(재사용 방지).
- 업스트림 0.6.43의 `create_token()`은 이미 모든 JWT에 `jti`(uuid4)를 넣는다(Redis 기반 revocation용). 이 커스텀은 그 `jti`를 **DB(`auth.token_jti`)에 "현재 유효한 단 하나의 jti"로 저장**하고 매 요청 시 대조하는 방식.

**동작 방식**
1. 로그인(`signin`/`signup`/`ldap`)·갱신(`refresh`) 시: 토큰 발급 → `decode_token`으로 `jti` 추출 → `Auths.update_user_token_jti_by_id(user.id, jti)`로 DB에 저장.
2. 매 인증 요청(`get_current_user`, JWT 경로): 토큰에 `jti`가 있으면 DB의 `token_jti`와 다를 경우 401 (`INVALID_TOKEN`).
3. 로그아웃(`signout`): DB의 `token_jti`를 `None`으로 초기화(+ 업스트림의 Redis `invalidate_token`도 그대로 수행).
- API 키(`sk-`) 인증 경로는 JTI 검사 대상이 아님(JWT 분기 이전에 return).

**변경 파일 및 핵심 내용**

- `backend/open_webui/models/auths.py` — 컬럼/메서드 추가:
```python
class Auth(Base):
    ...
    token_jti = Column(String, nullable=True)

class AuthModel(BaseModel):
    ...
    token_jti: Optional[str] = None
```
```python
def update_user_token_jti_by_id(self, id: str, token_jti: str) -> bool:
    try:
        with get_db() as db:
            result = db.query(Auth).filter_by(id=id).update({"token_jti": token_jti})
            db.commit()
            return True if result == 1 else False
    except Exception:
        return False

def get_user_token_jti_by_id(self, id: str) -> Optional[str]:
    try:
        with get_db() as db:
            auth = db.query(Auth).filter_by(id=id).first()
            return auth.token_jti if auth else None
    except Exception:
        return None
```
  - 부수 수정: `authenticate_user_by_api_key`의 예외 시 반환값 `False` → `None` (타입 정합성).

- `backend/open_webui/migrations/versions/a1b2c3d4e5f6_add_token_jti_to_auth.py` — 신규 Alembic 마이그레이션:
```python
revision = 'a1b2c3d4e5f6'
down_revision = 'c440947495f3'

def upgrade():
    op.add_column('auth', sa.Column('token_jti', sa.String(), nullable=True))

def downgrade():
    op.drop_column('auth', 'token_jti')
```

- `backend/open_webui/utils/auth.py` — `get_current_user`의 JWT 경로(span 설정 직후, last-active 갱신 직전)에 삽입:
```python
# Single Session Enforcement
from open_webui.models.auths import Auths

user_jti = Auths.get_user_token_jti_by_id(user.id)
token_jti = data.get("jti")

if token_jti:
    # If the token has a JTI, it must match the one in the DB
    if user_jti != token_jti:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_MESSAGES.INVALID_TOKEN,
        )
```
  - 최초 구현(`2c8c04c2c`)은 `if user_jti and data.get("jti") != user_jti:`(DB에 jti가 있을 때만 검사)였으나 `702db1ef5`에서 "토큰에 jti가 있으면 무조건 DB와 일치" 방식으로 강화됨.

- `backend/open_webui/routers/auths.py` — `signin`, `signup`, `ldap_auth`에서 토큰 발급 직후 공통 삽입:
```python
# Update JTI
decoded = decode_token(token)
if decoded and "jti" in decoded:
    Auths.update_user_token_jti_by_id(user.id, decoded["jti"])
```
  `signout`에서:
```python
if token:
    await invalidate_token(request, token)

    # Clear JTI from DB
    try:
        data = decode_token(token)
        if data and "id" in data:
            Auths.update_user_token_jti_by_id(data["id"], None)
    except Exception as e:
        log.error(f"Error clearing JTI on signout: {e}")
```

**재적용 가이드**
1. 대상 버전에서 `create_token()`이 `jti`를 payload에 넣는지 먼저 확인(0.6.43 이후 업스트림은 넣음). 없으면 jti 생성 로직부터 추가해야 함.
2. **마이그레이션 주의(중요)**: 현재 트리의 `down_revision = 'c440947495f3'`(add_chat_file_table)인데, 업스트림 0.6.43의 최신 head는 `018012973d35`(add_indexes, down: `d31026856c01`)다. 즉 **현재 저장소는 Alembic head가 2개(`018012973d35`, `a1b2c3d4e5f6`)로 갈라져 있고**, `config.py`의 `run_migrations()`는 `command.upgrade(cfg, "head")` 단일 head 업그레이드라 다중 head에서 예외가 나며(try/except로 로그만 남기고 지나감) 자동 적용이 보장되지 않는다. 실제 운영 DB에 어떻게 적용됐는지는 미확인. **재이식 시에는 down_revision을 대상 버전의 실제 최신 head로 지정**할 것. 파일 docstring의 "Revises: d31026856c01" 표기도 코드와 불일치(코드가 우선).
3. **OAuth 주의**: `utils/oauth.py`(미변경, create_token 호출 존재)는 JTI를 DB에 기록하지 않는다. 강화된 검사(토큰 jti 필수 대조) 하에서는 OAuth 로그인 토큰이 401이 될 것으로 보인다(코드 근거 추정, 실동작 미확인). OAuth를 쓰는 환경이라면 OAuth 콜백에도 JTI 갱신을 추가해야 함.
4. API 키 인증, 트러스티드 헤더 환경은 검사 우회/미적용 여부를 재확인할 것.
5. `get_current_user` 안의 지역 import(`from open_webui.models.auths import Auths`)는 순환 import 회피 목적이므로 유지 권장.

**관련 커밋**
- `2c8c04c2c` 취약점 점검#1 (모델/라우터/검증 최초 도입)
- `5759a7eb4` 취약점 점검#4 (Alembic 마이그레이션 추가)
- `702db1ef5` 취약점 점검8 (검증 강화)

---

### 3. 세션 갱신 엔드포인트 `POST /api/v1/auths/refresh` + `server_timestamp`

**목적/배경**
- 짧아진 토큰 수명(24h)을 보완해, 로그아웃 없이 세션을 연장(새 토큰 발급)할 수 있는 API. 클라이언트-서버 시계 오차 보정을 위해 `server_timestamp`도 함께 반환.

**동작 방식**
- 인증된 사용자(`Depends(get_current_user)` — 즉 기존 토큰이 JTI 검사를 통과해야 함)가 호출하면:
  - `JWT_EXPIRES_IN` 기준 새 토큰 발급, `expires_at` 계산
  - 새 토큰의 jti로 DB `token_jti` 교체 → **이전 토큰 즉시 무효화(회전)**
  - httpOnly 쿠키 `token` 재설정
  - `SessionUserResponse`(+`server_timestamp`) 반환
- `GET /api/v1/auths/`(get_session_user)와 `signin`/`ldap_auth` 응답에도 `server_timestamp: int(time.time())` 추가.

**변경 파일 및 핵심 내용**
- `backend/open_webui/routers/auths.py`:
```python
class SessionUserResponse(Token, UserProfileImageResponse):
    expires_at: Optional[int] = None
    permissions: Optional[dict] = None
    server_timestamp: Optional[int] = None
```
```python
@router.post("/refresh", response_model=SessionUserResponse)
async def refresh_session(request: Request, response: Response, user=Depends(get_current_user)):
    expires_delta = parse_duration(request.app.state.config.JWT_EXPIRES_IN)
    expires_at = None
    if expires_delta:
        expires_at = int(time.time()) + int(expires_delta.total_seconds())

    token = create_token(data={"id": user.id}, expires_delta=expires_delta)

    # Update JTI
    decoded = decode_token(token)
    if decoded and "jti" in decoded:
        Auths.update_user_token_jti_by_id(user.id, decoded["jti"])
    ...
    response.set_cookie(key="token", value=token, expires=datetime_expires_at,
        httponly=True, samesite=WEBUI_AUTH_COOKIE_SAME_SITE, secure=WEBUI_AUTH_COOKIE_SECURE)

    user_permissions = get_permissions(user.id, request.app.state.config.USER_PERMISSIONS)
    return { "token": token, "token_type": "Bearer", "expires_at": expires_at,
        "id": user.id, "email": user.email, "name": user.name, "role": user.role,
        "profile_image_url": user.profile_image_url, "permissions": user_permissions,
        "server_timestamp": int(time.time()) }
```
  - 참고: 현재 코드의 `get_session_user`/`signin`/`ldap_auth`/`refresh` 응답 dict에는 `"status_expires_at"`, `"profile_image_url"`, `"role"` 등이 **중복 기재**된 곳이 있음(파이썬 dict 리터럴이라 마지막 값이 이겨서 무해하나, 재이식 시 정리 권장).
- `backend/open_webui/main.py` — `/api/config`의 `features`에 토큰 수명(초)을 노출(프론트 타이머가 사용):
```python
from open_webui.utils.misc import parse_duration
...
"jwt_expires_in": f"{parse_duration(app.state.config.JWT_EXPIRES_IN).total_seconds()}" if parse_duration(app.state.config.JWT_EXPIRES_IN) else "0",
```
- `src/lib/apis/auths/index.ts` — 클라이언트 함수 추가 (작업트리 최종본 기준. 401 등 HTTP 오류 시 상태코드를 보존한 객체를 throw하여, 호출부가 "토큰 무효(401) → /auth 리다이렉트"와 "일시 장애 → 재시도"를 구분할 수 있게 함):
```ts
export const refreshSession = async (token: string) => {
	const res = await fetch(`${WEBUI_API_BASE_URL}/auths/refresh`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
		credentials: 'include'
	});

	// Preserve the HTTP status so callers can tell a revoked token (401)
	// apart from a transient failure and redirect to /auth accordingly.
	if (!res.ok) {
		const body = await res.json().catch(() => ({}));
		throw { status: res.status, detail: body?.detail ?? res.statusText };
	}

	return res.json();
};
```

**재적용 가이드**
- 섹션 2(JTI)와 한 세트로 적용해야 한다. refresh가 JTI를 회전시키므로, 다중 탭 환경에서는 sessionStorage(탭별 저장)와 결합 시 한 탭이 refresh하면 다른 탭 토큰이 무효화됨 — 이 문제는 섹션 6의 BroadcastChannel 탭 간 토큰 동기화로 완화한다.
- `refreshSession`은 다른 API 헬퍼들과 달리 `{ status, detail }` 형태로 throw한다(의도된 차이). 코드베이스 공통 패턴(`err.detail` 문자열 throw)으로 되돌리면 401 감지 분기가 죽으므로 유지할 것.
- `SessionUserInfoResponse`가 `SessionUserResponse`를 상속하므로 필드 추가만으로 두 응답 모두에 반영됨.
- 업스트림 버전에 따라 `get_session_user` 시그니처/응답 구성이 바뀌었을 수 있으니 `server_timestamp` 추가 위치만 맞추면 됨.

**관련 커밋**
- `2c8c04c2c` 취약점 점검#1 (refresh 엔드포인트·API 함수)
- `4be37956d` 취약점 점검#7 (`server_timestamp`, `jwt_expires_in` config 노출)

---

### 4. 토큰 저장 방식 변경: `localStorage` → `sessionStorage` (프론트 전면)

**목적/배경**
- 탭/브라우저 종료 시 토큰이 자동 소멸되도록 저장소를 `sessionStorage`로 이전(XSS 등으로 인한 장기 토큰 탈취 표면 축소, 단일 세션 정책과도 부합).

**동작 방식**
- 프론트엔드 전반의 `localStorage.token` / `localStorage.getItem('token')` 참조를 `sessionStorage.token` / `sessionStorage.getItem('token')`으로 치환. **확인 결과 현재 트리에 `localStorage.token` 잔존 참조 없음** (제거 코드 `localStorage.removeItem('token')`은 과거 잔존 토큰 정리용으로 곳곳에 유지).
- 소켓 연결 인증도 동일: `auth: { token: sessionStorage.token }` (`src/routes/+layout.svelte`).
- 로그인 성공 시 저장: `src/routes/auth/+page.svelte`에서 `localStorage.token = ...` → `sessionStorage.token = sessionUser.token` (토큰 쿼리파라미터 유입 경로 포함 2곳). 단 `redirectPath`는 여전히 localStorage 사용.
- 로그아웃/세션 무효 시에는 두 저장소 모두 정리: `localStorage.removeItem('token'); sessionStorage.removeItem('token');`

**변경 파일 및 핵심 내용**
- diff 기준 `-G "sessionStorage"`로 검출된 프론트 파일 **126개** 전부가 치환 대상 (전체 목록은 covered_files 참조). 대표:
  - `src/routes/+layout.svelte`, `src/routes/(app)/+layout.svelte`, `src/routes/auth/+page.svelte`, `src/lib/apis/index.ts`(툴서버 session 인증 토큰), `src/lib/components/layout/Sidebar/UserMenu.svelte` 및 admin/chat/channel/workspace/notes/playground 하위 컴포넌트 대부분.
  - 이 126개 파일 중 다수는 이 영역에서는 "토큰 치환"만 해당하며, 그 외 변경(채팅, 지식베이스 등)은 각 담당 영역 문서 참조.

**재적용 가이드**
- 사실상 프로젝트 전역 치환 작업: `localStorage.token` → `sessionStorage.token`, `localStorage.getItem('token')` → `sessionStorage.getItem('token')`. 치환 후 `grep -rn "localStorage.token" src/`로 잔존 여부 검증.
- 로그인 저장 지점(`auth/+page.svelte`)과 소켓 `user-join` 재접속 emit 지점을 반드시 포함할 것.
- 백엔드 httpOnly 쿠키 `token`은 별개로 계속 발급되므로(쿠키 기반 인증 경로 유지), 프론트 저장소 변경과 무관하게 동작.
- 부작용: 새 탭에서는 재로그인 필요(의도된 동작), 다중 탭 + JTI 단일 세션과 결합 시 탭 간 세션 경합 발생 — 갱신에 의한 경합은 섹션 6의 BroadcastChannel 동기화로 완화됨.

**관련 커밋**
- `453924007` 취약점 점검#5 (전면 치환), `2c8c04c2c` 취약점 점검#1 (핵심 파일 선치환), `4be37956d` 취약점 점검#7 (로그 문구 등 마무리)

---

### 5. 세션 타임아웃 UI — 남은시간 배지, 수동 연장 버튼, SessionTimeoutModal

**목적/배경**
- 24시간(또는 설정값) 토큰 수명 하에서 사용자가 세션 만료를 인지하고 직접 연장할 수 있게 하는 UI. 만료 임박 시 경고 모달, 만료 시 자동 로그아웃.

**동작 방식** (`src/routes/(app)/+layout.svelte`)
- 상태: `lastActive`, `lastRefresh`, `clockSkew`(클라-서버 시계 오차), `tokenDuration`(기본 3600초).
- `tokenDuration`은 `$config.features.jwt_expires_in`(초 문자열)에서 로드. ※ 이 로드는 `onMount` 내부에 `$:` 라벨로 작성돼 있어 실제로는 마운트 시 1회 실행되는 일반 라벨문임(Svelte 반응문 아님) — 재구현 시 참고.
- `refreshSessionHelper()`: `refreshSession(sessionStorage.token)` 호출 → 새 토큰을 `sessionStorage.token`에 저장, `user.expires_at` 갱신, `tokenDuration = expires_at - server_timestamp`, `clockSkew = now - server_timestamp` 재계산, `showTimeoutModal = false`. 실패 시 `err?.status === 401`이면 저장소 정리 후 `/auth`로 이동(실제 401은 전역 fetch 인터셉터가 먼저 처리하는 구조).
- 1초 주기 `setInterval` 타이머:
  - `currentServerTime = Math.floor(Date.now()/1000) - clockSkew`, `diff = expires_at - currentServerTime`
  - `warningThreshold = tokenDuration > 60 ? 60 : 10`
  - `diff <= 0` → `clearInterval` 후 `logoutHandler()`
  - `diff <= warningThreshold` && 탭 visible → `showTimeoutModal = true` (벗어나면 자동 닫힘)
  - 배지 문구: `로그아웃 ${m}분 ${s}초 남음`, `diff < 60`이면 `isExpiringSoon = true`(빨간색+pulse), 만료 시 `'만료됨'`
- 배지 UI: 화면 우상단 고정(`fixed top-4 right-36 z-[999]`), 남은시간 + 수동 새로고침 버튼(ArrowPath 아이콘, 클릭 시 `refreshSessionHelper`, **10초 쿨다운**, `만료됨`이면 비활성):
```svelte
<button ... on:click={onManualRefresh}
    disabled={manualRefreshLoading || timeRemaining === '만료됨'}
    title="세션 연장 (10초 대기)">
```
- `logoutHandler()`: `userSignOut()` API 호출(서버에서 Redis 무효화+JTI 제거) → 양쪽 저장소 토큰 삭제 → `user.set(null)` → `window.location.href = redirectUrl`(전체 리로드).
- `SessionTimeoutModal`(신규 컴포넌트, `src/lib/components/layout/Overlay/SessionTimeoutModal.svelte`): props `show`, `countdown`; 이벤트 `extend`(→ refreshSessionHelper) / `logout`(→ logoutHandler). 문구: "보안을 위해 {countdown}초 후 자동 로그아웃됩니다." / 버튼 "로그아웃", "연장하기". 45줄 전체 신규 파일이므로 그대로 복사 가능.
- 같은 파일에서 `ChangelogModal`은 주석 처리로 비활성화(로그인 후 변경로그 팝업 제거)되고 `showChangelog` 설정 블록 삭제됨.

**변경 파일 및 핵심 내용**
- `src/lib/components/layout/Overlay/SessionTimeoutModal.svelte` (신규)
- `src/routes/(app)/+layout.svelte` (타이머/배지/모달/logoutHandler — 위 요약 참조; `import { refreshSession, userSignOut } from '$lib/apis/auths';`, `import ArrowPath ...`, `import SessionTimeoutModal ...` 추가)

**재적용 가이드**
1. 섹션 3(refresh API + `server_timestamp` + `features.jwt_expires_in`)이 선행돼야 함.
2. `ArrowPath` 아이콘(`src/lib/components/icons/ArrowPath.svelte`)은 업스트림에 존재 — 추가 불필요.
3. 배지 위치(`right-36`)는 업스트림 네브바 버튼과 겹치지 않게 잡은 값이므로 대상 버전 레이아웃에 맞춰 조정.
4. 문구가 한국어 하드코딩(i18n 미사용)이므로 다국어 필요 시 i18n 키로 교체 권장.
5. `onMount`가 cleanup 함수를 반환하므로 async `onMount`에서는 cleanup이 무시될 수 있는 점 주의 — 현 코드는 `onMount(async () => { ... return () => {...} })` 형태로, Svelte에서 async 함수의 반환 cleanup은 호출되지 않음(현 코드 그대로의 동작 특성, 실동작 미확인). 재구현 시 `onDestroy` 사용 권장.

**관련 커밋**
- `2c8c04c2c` 취약점 점검#1 (카운트다운 1차)
- `6123e56c5` 취약점 점검#2 (ChangelogModal 비활성화)
- `4be37956d` 취약점 점검#7 (모달/배지/수동갱신/clockSkew 등 현재 형태로 전면 개편)

---

### 6. 활동 감지 기반 자동 갱신(슬라이딩 세션) — ★미커밋 작업트리 변경★

**목적/배경**
- 커밋된 HEAD 상태는 "자동 갱신 없음(No Auto-Refresh), 만료 임박 시 모달로 수동 연장" 정책이었다(주석 `// Logic: No Auto-Refresh. Show Modal if expiring.`). 작업트리에서 이 주석을 제거하고, **사용 중인 사용자는 모달을 보기 전에 토큰이 자동 연장**되도록 슬라이딩 세션을 재도입했다(모달은 갱신 실패 시 fallback). 최초 커밋(#1)에도 1분 주기 활동 갱신이 있었으나 #7에서 제거됐던 것을 개선된 형태로 되살린 것.

**동작 방식** (`src/routes/(app)/+layout.svelte` + `src/lib/apis/auths/index.ts`, 작업트리 미커밋)
- 신규 상수/상태:
```js
// Auto refresh on user activity (sliding session)
const ACTIVITY_REFRESH_WINDOW = 60 * 1000; // ms - user counts as "active" if an action happened within this window
const MIN_AUTO_REFRESH_INTERVAL = 10 * 1000; // ms - minimum gap between auto refresh attempts (spaces out retries on failure)
let autoRefreshInFlight = false;
let lastAutoRefreshAttempt = 0;
let timerInterval: ReturnType<typeof setInterval> | null = null;
// Tokens live in sessionStorage (per tab) while the backend enforces a single
// JTI per user, so a refresh in one tab invalidates every other tab's token.
// Broadcast refreshed tokens so all tabs stay on the current one.
let sessionChannel: BroadcastChannel | null = null;
```
- 활동 리스너 확장: 기존 `mousemove/keydown/click/scroll`에 **`touchstart` 추가**, `scroll`은 **capture: true**로 변경(중첩 컨테이너 내부 스크롤도 감지). 해제부도 동일 시그니처로 수정.
```js
window.addEventListener('touchstart', updateLastActive);
// capture: true so scrolling inside nested containers (chat list, sidebar) counts too
window.addEventListener('scroll', updateLastActive, true);
```
- 1초 타이머 내 삽입(만료 즉시 로그아웃 체크 이후, 모달 표시 판단 이전):
```js
// Sliding session: while the user is active, renew the token automatically
// once it drops below half its lifetime, so only idle sessions ever reach
// the timeout modal. The modal stays as a fallback if refresh keeps failing.
const isActive = Date.now() - lastActive <= ACTIVITY_REFRESH_WINDOW;
const refreshThreshold = Math.max(
    Math.floor(tokenDuration / 2),
    warningThreshold + 20
);
if (isVisible && isActive && diff <= refreshThreshold) {
    attemptAutoRefresh();
}
```
- 갱신 시도 가드(폭주 방지 + 실패 시 10초 간격 재시도):
```js
const attemptAutoRefresh = async () => {
    if (autoRefreshInFlight) return;
    const now = Date.now();
    if (now - lastAutoRefreshAttempt < MIN_AUTO_REFRESH_INTERVAL) return;
    lastAutoRefreshAttempt = now;
    autoRefreshInFlight = true;
    try {
        await refreshSessionHelper();
    } finally {
        autoRefreshInFlight = false;
    }
};
```
- **동시 호출 합류(coalescing)**: 백엔드 refresh는 호출마다 JTI를 회전시키므로, 타이머·수동 버튼·모달 연장이 병렬로 refresh를 쏘면(특히 멀티워커 배포에서) 저장된 토큰과 DB JTI가 어긋나 세션이 깨질 수 있다. `refreshSessionHelper`를 공유 프로미스로 만들어 모든 호출자가 진행 중인 요청 하나에 합류하게 했다. 토큰 채택 로직은 `adoptRefreshedToken(res)`로 분리(아래 탭 동기화에서 재사용):
```js
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
        if (!sessionStorage.token) return;
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
```
- **탭 간 토큰 동기화(BroadcastChannel)**: sessionStorage는 탭별 저장인데 JTI는 사용자당 1개라, 한 탭이 자동 갱신하면 다른 탭 토큰이 즉시 무효화되는 문제가 있다. 갱신 성공 시 `session-token` 채널로 새 토큰을 방송하고, 모든 탭이 이를 받아 채택하도록 했다(onMount에서 등록):
```js
if (typeof BroadcastChannel !== 'undefined') {
    sessionChannel = new BroadcastChannel('session-token');
    sessionChannel.onmessage = (event: MessageEvent) => {
        const msg = event.data;
        if (msg?.type === 'token-refreshed' && msg.token) {
            adoptRefreshedToken(msg);
        }
    };
}
```
- **정리(teardown) 위치 수정**: 기존에는 async `onMount`의 반환값으로 cleanup을 등록했는데, **async onMount가 반환하는 함수는 Svelte가 무시**하므로 리스너/타이머가 레이아웃 이탈 시 누수됐다. `onDestroy`로 이동(전역 `ssr = false`라 서버 실행 걱정 없음):
```js
// onMount is async, so a cleanup function returned from it would be ignored —
// teardown must live in onDestroy.
onDestroy(() => {
    window.removeEventListener('mousemove', updateLastActive);
    window.removeEventListener('keydown', updateLastActive);
    window.removeEventListener('click', updateLastActive);
    window.removeEventListener('touchstart', updateLastActive);
    window.removeEventListener('scroll', updateLastActive, true);
    if (timerInterval) {
        clearInterval(timerInterval);
    }
    sessionChannel?.close();
});
```
  (이에 맞춰 `timerInterval`을 컴포넌트 스코프 변수로 승격, onMount 내부의 오해 소지가 있던 `$:` 라벨(라벨문이라 반응형이 아님)도 일반 `if`로 정리.)
- `src/lib/apis/auths/index.ts`의 `refreshSession`도 상태코드 보존형 throw로 재작성(섹션 3의 최종본 참조) — 401 시 즉시 `/auth` 리다이렉트 분기가 실제로 동작하기 위한 전제조건.
- 정리하면: 탭이 보이는 상태 + 최근 60초 내 활동 + 남은시간이 `max(수명/2, 경고임계+20초)` 이하 → 자동 refresh(성공 시 만료시각 갱신 + 전 탭 동기화, 실패 시 10초 간격 재시도, 401이면 즉시 재로그인 유도). 유휴 사용자만 경고 모달/자동 로그아웃에 도달.

**변경 파일 및 핵심 내용**
- `src/routes/(app)/+layout.svelte` — 위 코드 전부 (상수/상태, 리스너, 타이머 삽입, coalescing, BroadcastChannel, onDestroy)
- `src/lib/apis/auths/index.ts` — `refreshSession` 오류 형태 변경(`{ status, detail }` throw)
- **둘 다 커밋되지 않은 작업트리 상태이므로, 이식 시 반드시 작업트리 버전을 기준으로 할 것.**

**재적용 가이드**
1. 섹션 5의 타이머 구조 위에 얹는 변경이므로 5 → 6 순서로 적용. `refreshSession` API 변경(섹션 3)도 같이 적용해야 401 처리가 산다.
2. `refreshThreshold`가 `tokenDuration / 2`이므로 수명이 24h면 남은시간 12시간 시점부터 활동 시 갱신이 시작됨(활성 사용자는 반감점마다 1회 회전). 서버 부하는 갱신 1회당 JTI 업데이트 1회 수준.
3. `warningThreshold + 20`은 짧은 토큰(테스트용 수십 초)에서도 모달 직전에 갱신 기회를 보장하기 위한 하한. 단 수명 100초 이하 토큰에서는 임계값이 수명 이상이 되어 활동 중 10초마다 계속 갱신되고, 61~100초 토큰에서는 재시도 간격 사이에 모달이 잠깐 깜빡일 수 있다 — 테스트 설정에서만 발생하는 알려진 한계(운영 24h 기준 무영향).
4. 다중 탭: BroadcastChannel 동기화로 모든 탭이 최신 토큰을 공유한다. 이 동기화가 없으면 자동 갱신 도입 시 "한 탭의 갱신 → 다른 탭 401 → 그 탭의 만료 로그아웃이 쿠키(최신 토큰)로 signout을 호출해 활성 탭까지 로그아웃"되는 연쇄가 일상적으로 발생하므로, **자동 갱신과 탭 동기화는 반드시 세트로 이식할 것.**

**관련 커밋**
- 커밋 없음 (작업트리 미커밋 변경). 전신: `2c8c04c2c`(1분 주기 활동 갱신 도입) → `4be37956d`(자동 갱신 제거) → 작업트리(개선 재도입).

---

### 7. 전역 401 인터셉터 및 만료 즉시 로그아웃 (루트 레이아웃)

**목적/배경**
- 무효화된 토큰(다른 곳 로그인으로 JTI 불일치, 만료 등)으로 API 호출 시 컴포넌트별 에러 처리에 기대지 않고 전역에서 일괄적으로 토큰 정리 + `/auth` 리다이렉트.

**동작 방식** (`src/routes/+layout.svelte`)
- `onMount` 최상단에서 `window.fetch`를 래핑. 응답이 401이고 요청에 `Authorization` 헤더가 있었던 경우에만(=인증된 API 호출) 발동:
```js
const originalFetch = window.fetch;
window.fetch = async (...args) => {
    const response = await originalFetch(...args);
    if (response.status === 401) {
        const [url, options] = args;
        const hasAuthHeader =
            (options?.headers &&
                (options.headers['Authorization'] || options.headers['authorization'])) ||
            (args[0] instanceof Request && args[0].headers.has('Authorization'));
        if (hasAuthHeader) {
            if (localStorage.getItem('token')) localStorage.removeItem('token');
            if (sessionStorage.getItem('token')) sessionStorage.removeItem('token');
            if (window.location.pathname !== '/auth') {
                window.location.href = '/auth';
            }
            return new Response(null, { status: 401 });
        }
    }
    return response;
};
```
  (`/auth` 중복 리다이렉트 방지 조건은 `702db1ef5`에서 추가)
- 업스트림의 15초 주기 `checkTokenExpiry`는 유지하되 `TOKEN_EXPIRY_BUFFER`를 `60` → `0`으로 변경(만료 60초 전 선제 로그아웃 → 정확히 만료 시점에 로그아웃; 선제 갱신/경고는 (app) 레이아웃의 1초 타이머가 담당).
- 세션 무효 시 리다이렉트를 `goto()` → `window.location.href = '/auth?redirect=...'`(전체 리로드)로 변경하고 sessionStorage도 함께 정리.
- `getUserSettings`는 `role`이 `user`/`admin`인 경우에만 호출하도록 가드(+catch) 추가 — pending 계정이 401 인터셉터 루프에 빠지는 것을 방지하는 성격의 변경(`98d3bdae5`에 포함).

**변경 파일 및 핵심 내용**
- `src/routes/+layout.svelte` (위 내용 전부 + sessionStorage 치환, 소켓 auth 토큰)

**재적용 가이드**
- fetch 래핑은 앱 전역에 영향을 주므로, 대상 버전에서 이미 유사한 인터셉터/에러 핸들러가 생겼는지 확인 후 중복 적용 금지.
- `headers`가 `Headers` 인스턴스인 일반 fetch 호출은 `options.headers['Authorization']` 인덱싱으로 감지되지 않는 한계가 있음(현 코드 그대로의 특성). Open WebUI API 헬퍼들은 평범한 객체 리터럴 헤더를 쓰므로 실용상 동작.
- `TOKEN_EXPIRY_BUFFER` 변경은 (app) 레이아웃 타이머와 세트로 봐야 함 — 버퍼 60초를 유지하면 경고 모달이 뜨기 전에 루트 타이머가 먼저 로그아웃시켜 버림.

**관련 커밋**
- `4be37956d` 취약점 점검#7, `702db1ef5` 취약점 점검8, `98d3bdae5`(getUserSettings 가드)

---

### 8. 로그인/로그아웃 흐름 변경

**목적/배경**
- sessionStorage 이전·JTI 정책에 맞춘 로그인/로그아웃 경로 정리.

**동작 방식 / 변경 파일**
- `src/routes/auth/+page.svelte`:
  - `setSessionUser`에서 `sessionStorage.token = sessionUser.token` 저장(토큰 쿼리파라미터 유입 경로도 `sessionStorage.token = token`).
  - onMount 리다이렉트 조건 `if ($user !== undefined)` → `if ($user)` (user가 null인 상태에서 잘못 리다이렉트되는 문제 수정).
- `src/lib/components/layout/Sidebar/UserMenu.svelte` — 로그아웃 버튼:
```js
const res = await userSignOut();
user.set(null);
localStorage.removeItem('token');
sessionStorage.removeItem('token');   // 추가
location.href = res?.redirect_url ?? '/auth';
```
- `src/routes/(app)/+layout.svelte` — `logoutHandler`(섹션 5 참조): 타임아웃/모달 로그아웃 공용 경로.
- 백엔드 `signout`(섹션 2): Redis 무효화 + DB JTI 제거.

**재적용 가이드**
- 로그아웃 지점이 UserMenu / logoutHandler / 401 인터셉터 / checkTokenExpiry 4곳이므로, 모두 "양쪽 저장소 삭제 + 전체 리로드 리다이렉트" 패턴으로 일관되게 맞출 것.

**관련 커밋**
- `2c8c04c2c` 취약점 점검#1, `453924007` 취약점 점검#5, `4be37956d` 취약점 점검#7

---

### 9. 비밀번호 유효성 강화 (규칙 기반 + 블랙리스트 + 계정정보 검사)

**목적/배경**
- 업스트림의 단일 정규식 검사(`PASSWORD_VALIDATION_REGEX_PATTERN`)를 규칙 기반 다단계 검사로 교체하고, 흔한 문자열 블랙리스트·계정정보 포함 여부 검사를 추가. 오류 메시지를 규칙별 한국어 메시지로 세분화.

**동작 방식**
- 게이트: 기존 env `ENABLE_PASSWORD_VALIDATION`(기본 False, 배포 compose에서는 `true`)가 켜져 있을 때만 규칙 검사 수행. 72바이트(bcrypt) 상한 검사는 항상 수행.
- 신규 env `PASSWORD_BLACKLIST` (콤마 구분, 기본 `password,123456,admin,test`; 배포 compose에서는 `kftc,admin`).
- 검사 규칙 (`backend/open_webui/utils/auth.py`의 `validate_password(password, user_data=None)`):
  1. 최소 8자
  2. 영문자+숫자+특수문자 각 1개 이상 (`[a-zA-Z]`, `\d`, `[^\w\s]`)
  3. 4자 이상 연속 문자/숫자 금지(전진·후진, `1234`/`dcba` 등; alnum에 한함)
  4. 4자 이상 동일문자 반복 금지(`1111` 등)
  5. 블랙리스트 부분문자열 금지(대소문자 무시)
  6. `user_data`의 email 로컬파트·name이 비밀번호에 포함되면 거부
- 기존 `PASSWORD_VALIDATION_REGEX_PATTERN` env는 남아 있으나 **validate_password에서 더 이상 사용되지 않음**.
- 호출부 (`backend/open_webui/routers/auths.py`):
  - `signup`: `validate_password(form_data.password, {"email": form_data.email, "name": form_data.name})` — try 구조도 정리(검증 실패를 바깥 try 이전에 400으로 반환).
  - `update_password`: 업스트림이 `form_data.password`(현재 비밀번호)를 검증하던 것을 **`form_data.new_password` 검증으로 수정**하고 세션 사용자의 email/name 전달.
  - `add_user`(관리자 사용자 추가): `{"email": user.email, "name": user.name}` 전달 — **주의: 여기의 `user`는 `get_admin_user`로 주입된 "관리자 본인"이라 신규 사용자(form_data)가 아닌 관리자의 계정정보와 대조됨.** 재이식 시 `form_data.email/name`으로 바꾸는 것을 검토(현 코드 그대로 옮기려면 이 동작도 그대로임).
- 오류 메시지 (`backend/open_webui/constants.py`에 신규 추가):
```python
PASSWORD_TOO_SHORT = "비밀번호는 최소 8자 이상이어야 합니다."
PASSWORD_MISSING_CHARS = "비밀번호는 영문자, 숫자, 특수문자를 각각 1개 이상 포함해야 합니다."
PASSWORD_SEQUENTIAL = "비밀번호에 4자 이상의 연속된 문자나 숫자를 사용할 수 없습니다 (예: 1234, abcd)."
PASSWORD_REPETITIVE = "비밀번호에 4자 이상의 반복된 문자나 숫자를 사용할 수 없습니다 (예: 1111, aaaa)."
PASSWORD_CONTAINS_ACCOUNT_INFO = "비밀번호에 이메일 아이디나 이름을 포함할 수 없습니다."
PASSWORD_COMMON = "비밀번호로 사용할 수 없는 쉬운 문자열이 포함되어 있습니다."
```
  (참고: `constants.py`는 이 외에도 다수 오류 메시지가 한국어화됨 — `e2a1396a1` 커밋, 별도 영역과 겹치는 전면 한글화이므로 여기서는 비밀번호 관련 항목만 명세)
- env (`backend/open_webui/env.py`):
```python
PASSWORD_BLACKLIST = [
    item.strip()
    for item in os.environ.get("PASSWORD_BLACKLIST", "password,123456,admin,test").split(",")
    if item.strip()
]
```

**재적용 가이드**
1. `utils/auth.py`의 `validate_password` 본문을 통째로 교체(시그니처에 `user_data: Optional[Dict[str, str]] = None` 추가, `import re` 필요).
2. 대상 버전의 `validate_password` 호출부(signup/update_password/add_user/LDAP 등)를 모두 찾아 `user_data` 전달 여부 결정. 업스트림에서 호출부가 늘었을 수 있음.
3. `ERROR_MESSAGES`에 6개 상수 추가, `env.py`에 `PASSWORD_BLACKLIST` 추가, 배포 env(`ENABLE_PASSWORD_VALIDATION=true`, `PASSWORD_BLACKLIST=...`) 설정.
4. 프론트엔드 별도 검증 로직 추가는 미확인(서버 400 detail 메시지를 그대로 표시하는 구조).

**관련 커밋**
- `98d3bdae5` feat: 비밀번호 유효성 검사 로직을 강화하고 블랙리스트 및 사용자 정보 기반 검사를 추가했습니다.
- `e2a1396a1` 에러 메시지 한글화 및 파일 업로드 예외 처리 개선 (constants.py 한글화)

---

### 10. DISABLE_ADMIN — 관리자 기능 전면 차단 게이트

**목적/배경**
- 운영 환경에서 관리자 API/화면 접근 자체를 환경변수로 차단할 수 있는 스위치(인증 게이트 레벨의 변경이므로 본 영역에 포함; 관리자 UI 상세는 해당 영역 문서 참조).

**동작 방식**
- env `DISABLE_ADMIN` (기본 `False`; compose에서는 `false`로 명시).
- 백엔드: `get_admin_user` 의존성 최상단에서 차단 → `Depends(get_admin_user)`를 쓰는 모든 관리자 API가 403.
- 프론트: `/api/config` `features.disable_admin`으로 노출, admin 레이아웃에서 진입 차단.

**변경 파일 및 핵심 내용**
- `backend/open_webui/env.py`:
```python
DISABLE_ADMIN = os.environ.get("DISABLE_ADMIN", "False").lower() == "true"
```
- `backend/open_webui/utils/auth.py`:
```python
def get_admin_user(user=Depends(get_current_user)):
    if DISABLE_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ERROR_MESSAGES.ACCESS_PROHIBITED,
        )
    ...
```
- `backend/open_webui/main.py` — `/api/config`: `"disable_admin": DISABLE_ADMIN` (같은 위치에 `"enable_admin_export"`도 추가돼 있으나 admin 영역 문서 참조).
- `src/routes/(app)/admin/+layout.svelte`:
```js
if ($user?.role !== 'admin' || $config?.features?.disable_admin) {
    await goto('/');
}
```

**재적용 가이드**
- env → utils/auth.py → main.py(config 노출) → admin 레이아웃 순으로 적용. UI 차단은 우회 가능하므로 백엔드 `get_admin_user` 게이트가 본체.

**관련 커밋**
- `1da45db0e` 취약점 점검#6

---

### 부록: 영역 전체 커밋 매핑

| 커밋 | 제목 | 본 영역 관련 내용 |
|---|---|---|
| `2c8c04c2c` | 취약점 점검#1 | JTI 단일 세션(모델/라우터/검증), `/auths/refresh`, refreshSession API, 활동 갱신 1차, sessionStorage 일부 |
| `6123e56c5` | 취약점 점검#2 | ChangelogModal 비활성화, CHANGELOG_SECURITY.md |
| `5759a7eb4` | 취약점 점검#4 | `a1b2c3d4e5f6` Alembic 마이그레이션 |
| `453924007` | 취약점 점검#5 | localStorage→sessionStorage 전면 치환, JWT_EXPIRES_IN 24h |
| `1da45db0e` | 취약점 점검#6 | DISABLE_ADMIN |
| `4be37956d` | 취약점 점검#7 | SessionTimeoutModal/배지/수동갱신/clockSkew, `server_timestamp`, `features.jwt_expires_in`, 전역 401 인터셉터, TOKEN_EXPIRY_BUFFER 0 |
| `702db1ef5` | 취약점 점검8 | JTI 검증 강화, 401 인터셉터 `/auth` 중복 리다이렉트 방지 |
| `98d3bdae5` | 비밀번호 유효성 강화 | validate_password 규칙 기반 교체, PASSWORD_BLACKLIST, getUserSettings 역할 가드 |
| `e2a1396a1` | 에러 메시지 한글화 | constants.py 한글화(비밀번호 메시지 포함 영역) |
| (미커밋) | — | 활동 감지 기반 슬라이딩 세션 자동 갱신 재도입 (`src/routes/(app)/+layout.svelte`) |

### 권장 재적용 순서 (요약)
1. 백엔드: `auth.token_jti` 컬럼 + 마이그레이션(down_revision을 대상 head로 수정) → 2. `get_current_user` JTI 검증 → 3. signin/signup/ldap JTI 기록, signout JTI 제거 → 4. `/auths/refresh` + `server_timestamp` + `features.jwt_expires_in` → 5. `JWT_EXPIRES_IN=24h`(기존 DB config 수동 반영) → 6. 프론트 sessionStorage 전면 치환 → 7. 루트 레이아웃(401 인터셉터, BUFFER 0) → 8. (app) 레이아웃 타이머/배지/SessionTimeoutModal → 9. 작업트리의 슬라이딩 세션 자동 갱신 → 10. 비밀번호 검증 강화 → 11. DISABLE_ADMIN. OAuth 사용 환경이면 JTI 미기록 문제(섹션 2)를 반드시 함께 해결할 것.


---

# 파트 2. 백엔드 보안 강화 (취약점 점검#1~8)


이 문서는 업스트림 0.6.43 (`a7271532f`) 대비 브랜치 `0.6.43-fix2.1`의 **백엔드 보안 관련 커스텀**을 다룬다. 인증 토큰(JTI 단일 세션, refresh, 마이그레이션 파일 자체)은 별도 에이전트 담당이므로 여기서는 경계에 걸치는 부분(start.sh의 alembic 실행, JWT 만료 기본값 등)만 짧게 다룬다. 모든 내용은 `git diff a7271532f` 로 실제 확인한 것이다.

### 1. 외부 API(Ollama/OpenAI) 오류 응답 마스킹 및 상태코드 400 통일

**목적/배경**
- 취약점 점검 결과, 외부 LLM 서버(Ollama/OpenAI 호환 서버)의 원본 오류 메시지(내부 URL, 스택 정보, 외부 서비스의 상세 오류)가 그대로 클라이언트에 전달되어 정보 노출 위험이 있었다. 상세 오류는 서버 로그에만 남기고, 클라이언트에는 고정 문구를 반환하도록 변경.
- 또한 외부 서버의 원본 HTTP 상태코드(예: 401, 502 등)를 그대로 프록시하면 내부 구성 정보를 유추할 수 있어, 연결 검증(verify) 엔드포인트의 실패 응답을 400으로 통일했다.

**동작 방식**
- 오류 발생 시 서버는 `log.error(...)` / `log.exception(...)` 으로 원본 오류를 기록하고, 클라이언트에는 항상 `"An error occurred. Please contact the administrator."` 문구만 반환한다.
- `POST /ollama/verify`, `POST /openai/verify` 류의 연결 검증 실패는 원본 상태 대신 400을 반환한다 (ollama는 `HTTPException(400)`, openai는 `JSONResponse/PlainTextResponse(status_code=400)`).
- 채팅 완료/임베딩/프록시 경로의 4xx/5xx 응답은 상태코드는 원본(`r.status`)을 유지하되 본문을 `{"detail": "An error occurred. Please contact the administrator."}` 로 교체한다.

**변경 파일 및 핵심 내용**

`backend/open_webui/routers/ollama.py`
- `send_post_request()` 내 오류 처리 3곳 — 원본 detail 제거, 고정 문구로 교체:
```python
if "error" in res:
    log.error(f"Ollama Error: {res['error']}")
    raise HTTPException(status_code=r.status, detail="An error occurred. Please contact the administrator.")
...
except Exception as e:
    log.error(f"Failed to parse error response: {e}")
    raise HTTPException(
        status_code=r.status,
        detail="An error occurred. Please contact the administrator.",
    )
...
except Exception as e:
    detail = f"Ollama: {e}"
    log.error(detail)
    raise HTTPException(
        status_code=r.status if r else 500,
        detail="An error occurred. Please contact the administrator.",
    )
```
- `verify_connection()` — `raise Exception(detail)` 을 `raise HTTPException(status_code=400, detail=detail)` 로 교체 (detail 은 `f"External Error: {res['error']}"` 유지, 상태코드만 400 고정):
```python
if r.status != 200:
    detail = f"HTTP Error: {r.status}"
    res = await r.json()
    if "error" in res:
        detail = f"External Error: {res['error']}"
    raise HTTPException(status_code=400, detail=detail)
```

`backend/open_webui/routers/openai.py`
- `speech()` — 외부 응답에서 detail을 추출하던 블록을 통째로 삭제하고 고정 문구 반환:
```python
raise HTTPException(
    status_code=r.status_code if r else 500,
    detail="An error occurred. Please contact the administrator.",
)
```
- `verify_connection()` — 2곳(모델 목록 조회 분기 포함)에서 `status_code=r.status` → `status_code=400` (응답 본문은 그대로 전달, 상태코드만 400 고정).
- `generate_chat_completion()`, `embeddings()`, `proxy()` — `r.status >= 400` 인 경우 원본 본문 대신:
```python
if r.status >= 400:
    log.error(f"OpenAI Error ({r.status}): {response}")
    return JSONResponse(status_code=r.status, content={"detail": "An error occurred. Please contact the administrator."})
```
- 위 3개 함수의 마지막 `except Exception` 블록의 detail도 `"Open WebUI: Server Connection Error"` → `"An error occurred. Please contact the administrator."` 로 교체.

**재적용 가이드**
1. 최신 업스트림에서 `send_post_request`(ollama), `speech`/`verify_connection`/`generate_chat_completion`/`embeddings`/`proxy`(openai)의 오류 처리 구조가 리팩터링됐을 수 있으므로, "클라이언트로 나가는 detail/본문" 지점을 찾아 동일 원칙(로그에는 원본, 응답에는 고정 문구)을 적용한다.
2. 프론트엔드 `src/lib/components/chat/Messages/Error.svelte` 도 취약점 점검#1 커밋에서 같이 수정됐다(오류 내용 표시 축소). 백엔드만 이식하면 UI가 기존 원본 오류를 기대할 수 있으니 프론트 담당 문서와 함께 적용할 것.
3. 고정 문구가 영어 하드코딩이라는 점(한글화 대상 아님)에 유의 — 재적용 시 문구를 그대로 유지하거나 정책에 맞게 통일.
4. `verify_connection`의 400 통일은 관리자용 연결 테스트 UX에 영향(프론트가 상태코드로 분기하면 확인 필요).

**관련 커밋**
- `2c8c04c2c` 취약점 점검#1 (오류 마스킹 본체)
- `3f76a2eb9` fix: OpenAI 및 Ollama 라우터의 오류 응답 상태 코드를 400으로 통일하고 HTTPException을 사용합니다.

### 2. 파일 업로드 오류 처리 강화 (files.py)

**목적/배경**
- 허용되지 않은 확장자 업로드 시 `File type {ext} is not allowed` 처럼 서버 설정을 유추할 수 있는 메시지가 노출되었고, 내부에서 발생한 `HTTPException` 이 바깥 `except Exception` 에 잡혀 원래 상태코드/메시지가 뭉개지는 문제가 있었다.

**동작 방식**
- 확장자 불허 시 400 + 고정 메시지 `ERROR_MESSAGES.FILE_NOT_SUPPORTED`("지원하지 않는 파일 형식입니다.") 반환.
- `upload_file_handler()` 의 최상위 예외 처리에 `except HTTPException: raise` 를 추가해, 내부에서 의도적으로 던진 HTTPException(400 등)이 500 계열 일반 오류로 덮어써지지 않게 함.

**변경 파일 및 핵심 내용**

`backend/open_webui/routers/files.py` — `upload_file_handler()`:
```python
if file_extension not in request.app.state.config.ALLOWED_FILE_EXTENSIONS:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=ERROR_MESSAGES.FILE_NOT_SUPPORTED,
    )
```
```python
    except HTTPException:
        raise
    except Exception as e:
        log.exception(e)
        raise HTTPException(
            ...
```
(`except HTTPException: raise` 는 기존 `except Exception as e:` 바로 위에 추가)

**재적용 가이드**
1. `FILE_NOT_SUPPORTED` 상수는 constants.py 한글화(아래 4절)에 의존한다. 순서상 constants.py 먼저 적용.
2. 최신 업스트림에서 upload_file_handler 구조가 바뀌었을 수 있으니 "확장자 검사 지점"과 "최상위 except" 두 지점만 찾아 동일 패턴 적용.
3. 프론트 `src/lib/apis/files/index.ts` 도 같은 커밋(e2a1396a1)에서 오류 표시 방식이 수정됨 — 프론트 담당 문서 참조.

**관련 커밋**
- `702db1ef5` 취약점 점검8 (확장자 메시지 은닉)
- `e2a1396a1` 에러 메시지 한글화 및 파일 업로드 예외 처리 개선 (`except HTTPException: raise` 추가)

### 3. DISABLE_ADMIN — 관리자 기능 전면 차단 환경변수

**목적/배경**
- 운영 환경에서 관리자 패널 접근 자체를 봉쇄하는 배포 옵션. 계정 권한(role=admin)이 있어도 서버 수준에서 관리자 API를 403으로 차단한다.

**동작 방식**
- 환경변수 `DISABLE_ADMIN=true` 설정 시:
  - 백엔드: `get_admin_user` 의존성을 쓰는 모든 관리자 API가 403 (`ERROR_MESSAGES.ACCESS_PROHIBITED`) 반환.
  - `GET /api/config` 응답 `features.disable_admin` 으로 프론트에 노출 → `src/routes/(app)/admin/+layout.svelte` 에서 `$user?.role !== 'admin' || $config?.features?.disable_admin` 이면 `/` 로 리다이렉트.
- 기본값 `False`. 최종 docker-compose.yaml 에는 `DISABLE_ADMIN=false` 로 배포 중 (점검#6 시점엔 true였다가 이후 false로 완화됨).

**변경 파일 및 핵심 내용**

`backend/open_webui/env.py`:
```python
DISABLE_ADMIN = os.environ.get("DISABLE_ADMIN", "False").lower() == "true"
```
(`WEBUI_AUTH_TRUSTED_GROUPS_HEADER` 선언 직후, `ENABLE_PASSWORD_VALIDATION` 직전에 위치)

`backend/open_webui/utils/auth.py` — `get_admin_user()` 맨 앞에 추가 (env import 목록에 `DISABLE_ADMIN` 추가):
```python
def get_admin_user(user=Depends(get_current_user)):
    if DISABLE_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ERROR_MESSAGES.ACCESS_PROHIBITED,
        )
    if user.role != "admin":
        ...
```

`backend/open_webui/main.py` — env import 에 `DISABLE_ADMIN` 추가, `get_app_config()` 의 `features` 딕셔너리(비인증 사용자에게도 내려가는 공통 블록)에 추가:
```python
"enable_public_active_users_count": ENABLE_PUBLIC_ACTIVE_USERS_COUNT,
"enable_admin_export": ENABLE_ADMIN_EXPORT,
"disable_admin": DISABLE_ADMIN,
```
주의: `enable_admin_export` 는 업스트림 0.6.43에서는 인증 사용자 블록(`**({...} if user is not None else {})` 내부)에만 있었는데, 이 커스텀이 공통 블록에도 중복 노출하도록 추가했다. 현재 코드에는 두 군데 모두 존재한다.

`docker-compose.yaml`:
```yaml
environment:
  - 'DISABLE_ADMIN=false'
```

**재적용 가이드**
1. env.py → utils/auth.py → main.py → 프론트(admin/+layout.svelte) 순으로 적용.
2. `get_admin_user` 차단은 최초 관리자 온보딩(첫 계정 생성 후 관리자 설정)까지 막을 수 있으므로, `DISABLE_ADMIN=true` 는 초기 설정 완료 후에만 켤 것.
3. 최신 업스트림에서 `get_app_config` 의 features 구조가 변할 수 있음 — `disable_admin` 은 반드시 **비인증 상태에서도 내려가는 블록**에 넣어야 로그인 화면 단계부터 프론트 분기가 동작한다.
4. 프론트 차단은 우회 가능(단순 리다이렉트)하므로 백엔드 `get_admin_user` 수정이 본질이다. `get_admin_user` 를 거치지 않는 관리자성 엔드포인트가 최신 버전에 새로 생겼는지 확인 필요 (미확인).

**관련 커밋**
- `1da45db0e` 취약점 점검#6

### 4. 백엔드 시스템/오류 메시지 한글화 (constants.py)

**목적/배경**
- 사용자 대상 서비스가 한국어 환경이므로 백엔드가 직접 내려주는 오류 메시지(토스트로 그대로 노출됨)를 한글화. 원문은 각 항목 위에 주석으로 보존해 업스트림과의 대조가 가능하게 했다.

**동작 방식**
- `MESSAGES`, `WEBHOOK_MESSAGES`, `ERROR_MESSAGES` Enum 의 모든 문자열 값을 한국어로 교체. 각 값 바로 위에 `# <원문 영어 메시지>` 주석 추가.
- 일부 메시지는 단순 번역을 넘어 정보 노출 축소를 겸함: 예) `FILE_NOT_SUPPORTED` 는 장문 안내 → `"지원하지 않는 파일 형식입니다."` 로 축약.
- 비밀번호 정책용 신규 상수 6종 추가 (5절에서 사용).

**변경 파일 및 핵심 내용**

`backend/open_webui/constants.py` — 전체 메시지 교체. 대표 예:
```python
DEFAULT = (
    lambda err="": f'{"문제가 발생했습니다." if err == "" else "[오류: " + str(err) + "]"}'
)
INVALID_CRED = "이메일 또는 비밀번호가 올바르지 않습니다. 확인 후 다시 시도해주세요."
UNAUTHORIZED = "401 인증되지 않음"
FILE_NOT_SUPPORTED = "지원하지 않는 파일 형식입니다."
FILE_TOO_LARGE = (
    lambda size="": f"파일이 너무 큽니다. {size} 미만의 파일을 업로드해주세요."
)
```
신규 추가 (업스트림에 없음):
```python
# Password validation errors
PASSWORD_TOO_SHORT = "비밀번호는 최소 8자 이상이어야 합니다."
PASSWORD_MISSING_CHARS = "비밀번호는 영문자, 숫자, 특수문자를 각각 1개 이상 포함해야 합니다."
PASSWORD_SEQUENTIAL = "비밀번호에 4자 이상의 연속된 문자나 숫자를 사용할 수 없습니다 (예: 1234, abcd)."
PASSWORD_REPETITIVE = "비밀번호에 4자 이상의 반복된 문자나 숫자를 사용할 수 없습니다 (예: 1111, aaaa)."
PASSWORD_CONTAINS_ACCOUNT_INFO = "비밀번호에 이메일 아이디나 이름을 포함할 수 없습니다."
PASSWORD_COMMON = "비밀번호로 사용할 수 없는 쉬운 문자열이 포함되어 있습니다."
```

**재적용 가이드**
1. 최신 업스트림 constants.py 에 메시지가 추가/변경되었을 가능성이 높다. 기계적 3-way merge 보다는, 현재 파일(원문 주석이 붙어 있음)을 기준으로 최신 파일의 각 항목을 한글로 다시 치환하는 방식을 권장.
2. `MESSAGES.MODEL_ADDED` 등 값 비교(문자열 매칭)에 쓰는 코드가 있는지 확인 (미확인 — 현재 포크에서는 문제 없이 동작 중).
3. 비밀번호 상수 6종은 5절(비밀번호 정책)과 반드시 함께 적용.

**관련 커밋**
- `e2a1396a1` 에러 메시지 한글화 및 파일 업로드 예외 처리 개선
- `98d3bdae5` feat: 비밀번호 유효성 검사 로직 강화 (PASSWORD_* 상수 추가)

### 5. 비밀번호 정책 강화 (규칙 기반 검증 + 블랙리스트 + 계정정보 검사)

**목적/배경**
- 업스트림의 `ENABLE_PASSWORD_VALIDATION` 은 단일 정규식(`PASSWORD_VALIDATION_REGEX_PATTERN`) 검사만 수행했다. 취약점 점검 요구사항(길이/복잡도/연속·반복 문자 금지/사전 단어 금지/계정정보 포함 금지)을 만족하도록 규칙 기반 검증으로 교체하고, 규칙별로 한글 오류 메시지를 반환하게 했다.

**동작 방식**
- `ENABLE_PASSWORD_VALIDATION=true` 일 때 `validate_password(password, user_data)` 가 순서대로 검사:
  1. 최소 8자 (`PASSWORD_TOO_SHORT`)
  2. 영문자+숫자+특수문자 각 1개 이상 (`PASSWORD_MISSING_CHARS`)
  3. 4자 이상 정방향/역방향 연속 문자열(abcd, 4321 등, 영숫자만 해당) 금지 (`PASSWORD_SEQUENTIAL`)
  4. 동일 문자 4회 이상 반복 금지 (`PASSWORD_REPETITIVE`)
  5. `PASSWORD_BLACKLIST` 환경변수(쉼표 구분, 기본 `password,123456,admin,test`)에 있는 문자열 포함 금지, 대소문자 무시 (`PASSWORD_COMMON`)
  6. `user_data` 의 이메일 로컬파트/이름 포함 금지 (`PASSWORD_CONTAINS_ACCOUNT_INFO`)
- 72바이트 초과 검사(bcrypt 제한)는 `ENABLE_PASSWORD_VALIDATION` 와 무관하게 항상 수행 (업스트림 동일).
- 기존 `PASSWORD_VALIDATION_REGEX_PATTERN` 은 env.py 에 남아 있지만 **더 이상 validate_password 에서 사용되지 않는다** (import 는 잔존).
- 배포 설정: docker-compose 에 `ENABLE_PASSWORD_VALIDATION=true`, `PASSWORD_BLACKLIST=kftc,admin`.

**변경 파일 및 핵심 내용**

`backend/open_webui/env.py` — `PASSWORD_VALIDATION_REGEX_PATTERN` 선언 뒤에 추가:
```python
PASSWORD_BLACKLIST = [
    item.strip()
    for item in os.environ.get(
        "PASSWORD_BLACKLIST", "password,123456,admin,test"
    ).split(",")
    if item.strip()
]
```

`backend/open_webui/utils/auth.py` — 시그니처 변경 및 본문 교체 (파일 상단 `import re`, env import 에 `PASSWORD_BLACKLIST` 추가):
```python
def validate_password(password: str, user_data: Optional[Dict[str, str]] = None) -> bool:
    if len(password.encode("utf-8")) > 72:
        raise Exception(ERROR_MESSAGES.PASSWORD_TOO_LONG)

    if not ENABLE_PASSWORD_VALIDATION:
        return True

    # 1. Length check
    if len(password) < 8:
        raise Exception(ERROR_MESSAGES.PASSWORD_TOO_SHORT)

    # 2. Complexity check (Letter, Number, Special)
    has_letter = re.search(r"[a-zA-Z]", password)
    has_number = re.search(r"\d", password)
    has_special = re.search(r"[^\w\s]", password)
    if not (has_letter and has_number and has_special):
        raise Exception(ERROR_MESSAGES.PASSWORD_MISSING_CHARS)

    # 3. Sequence check (4+ length, 정방향/역방향, isalnum 인 경우만)
    # 4. Repetition check (4연속 동일 문자)
    # 5. Common strings check: PASSWORD_BLACKLIST 대소문자 무시 부분일치
    # 6. Account info check: email 로컬파트 / name 포함 여부
    ...
    return True
```
(3~6번의 전체 구현은 현재 `backend/open_webui/utils/auth.py` 의 `validate_password` 참조 — ord() 비교 기반 연속성 검사, `password[i] == password[i+1] == password[i+2] == password[i+3]` 반복 검사, `blacklisted.lower() in password.lower()`, `email.split("@")[0] in password.lower()` / `name in password.lower()`)

`backend/open_webui/routers/auths.py` — 호출부 3곳에 `user_data` 전달:
- `update_password`: 검증 대상이 업스트림의 `form_data.password`(기존 비밀번호)에서 `form_data.new_password`(새 비밀번호)로 수정됨 — 업스트림 버그 수정 성격:
```python
validate_password(
    form_data.new_password,
    {"email": session_user.email, "name": session_user.name},
)
```
- `signup`: `validate_password(form_data.password, {"email": form_data.email, "name": form_data.name})` — 기존 중첩 try 에서 분리되어 signup 본문 try 앞으로 이동.
- `add_user`(관리자 사용자 추가): `validate_password(form_data.password, {"email": user.email, "name": user.name})` — **주의: 여기의 `user` 는 `Depends(get_admin_user)` 인 요청자(관리자)여서, 새로 만드는 사용자(form_data)가 아니라 관리자의 이메일/이름과 대조된다.** 재적용 시 `form_data.email/name` 으로 바로잡을지 결정 필요 (현재 포크는 관리자 정보 기준 그대로임).

`backend/open_webui/constants.py` — PASSWORD_* 상수 6종 (4절 참조).

`docker-compose.yaml`:
```yaml
  - 'ENABLE_PASSWORD_VALIDATION=true'
  - 'PASSWORD_BLACKLIST=kftc,admin'
```

**재적용 가이드**
1. 적용 순서: constants.py(상수) → env.py(PASSWORD_BLACKLIST) → utils/auth.py(validate_password) → routers/auths.py(호출부 3곳) → docker-compose.
2. 최신 업스트림에서 validate_password 호출부가 늘었을 수 있다(예: LDAP/OAuth 경로, 비밀번호 재설정). `grep validate_password` 로 전수 확인 후 user_data 전달 여부 결정.
3. `PASSWORD_VALIDATION_REGEX_PATTERN` 관련 코드는 삭제하지 않고 방치된 상태 — 이식 시 정리해도 무방.
4. name 이 매우 짧은 사용자(1~2자 한글 이름 등)는 6번 검사에서 오탐 가능성 있음 — 정책 검토 포인트.
5. 인증 라우터(auths.py)는 JTI/refresh 담당 에이전트와 파일이 겹치므로 충돌 주의.

**관련 커밋**
- `98d3bdae5` feat: 비밀번호 유효성 검사 로직을 강화하고 블랙리스트 및 사용자 정보 기반 검사를 추가했습니다.

### 6. Dockerfile 비루트 사용자 기본화 및 권한 강화 + 파싱 라이브러리/빌드 설정

**목적/배경**
- 컨테이너가 root(UID 0)로 실행되는 문제를 해소하기 위해 기본 UID/GID 를 1000으로 변경하고, HOME 을 `/root` 에서 일반 사용자 홈으로 이동. `USE_PERMISSION_HARDENING` 블록도 새 HOME 기준으로 수정.
- 별도로 사내 문서(HWP 등) 파싱 호환성을 위한 파이썬 패키지 설치와 빌드 편의 설정(NODE_OPTIONS, USE_CUDA)이 같은 파일에 누적되어 있다.

**동작 방식 / 변경 파일 및 핵심 내용** (`Dockerfile`)

(a) 비루트 사용자 기본화:
```dockerfile
ARG UID=1000
ARG GID=1000
...
ENV HOME=/home/appusr
# Create user and group if not root
RUN if [ $UID -ne 0 ]; then \
    if [ $GID -ne 0 ]; then \
    addgroup --gid $GID appgrp; \
    fi; \
    adduser --uid $UID --gid $GID --home $HOME --disabled-password --gecos "" appusr; \
    fi
```
업스트림은 `UID=0/GID=0`, `HOME=/root`, 사용자명 `app`, `--no-create-home` 이었다. 커스텀은 사용자/그룹명을 `appusr`/`appgrp` 로 바꾸고 `--no-create-home` 을 제거(홈 디렉터리 생성), `--gecos ""` 추가. 마지막 `USER $UID:$GID` 는 업스트림에 이미 존재 — UID 기본값이 1000이 되면서 실제로 비루트로 실행된다.

(b) 권한 강화 블록(`USE_PERMISSION_HARDENING`, 업스트림 기존 블록)의 `/root` 를 `$HOME` 으로 치환:
```dockerfile
RUN if [ "$USE_PERMISSION_HARDENING" = "true" ]; then \
    set -eux; \
    chgrp -R 0 /app $HOME || true; \
    chmod -R g+rwX /app $HOME || true; \
    find /app -type d -exec chmod g+s {} + || true; \
    find $HOME -type d -exec chmod g+s {} + || true; \
    fi
```

(c) 문서 파싱 라이브러리 추가 (기존 `pip3 install --no-cache-dir uv && ...` RUN 직후):
```dockerfile
# Install additional dependencies for documented parsing compatibility
RUN pip3 install --no-cache-dir msoffcrypto-tool chardet nltk pyhwp && \
    python3 -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab')"
```
처음(#3)에는 pip 설치만, 이후 nltk 데이터 다운로드가 `python3 -m nltk.downloader` 로 추가됐다가(0fa60ef24), 비루트 전환 커밋(1a4b2492f)에서 `python3 -c "import nltk; ..."` 형태로 변경됨. nltk 데이터는 빌드 시점 HOME 기준 경로에 저장되므로 (b)의 HOME 변경과 세트로 적용해야 런타임에서 읽을 수 있다.

(d) 빌드 설정 (보안 아님, 같은 파일 변경):
```dockerfile
ARG USE_CUDA=true            # 업스트림 false
ENV NODE_OPTIONS="--max-old-space-size=4096"   # 업스트림은 주석 처리 상태
```

**재적용 가이드**
1. `/app/backend/data` 는 업스트림 RUN 에서 이미 `chown -R $UID:$GID` 되므로 그대로 두면 된다. 다만 기존 볼륨(root 소유 파일)이 있는 환경에 비루트 이미지를 올리면 권한 오류가 나므로, 볼륨 데이터의 소유권을 1000:1000 으로 맞추는 운영 절차가 필요하다 (마이그레이션 가이드에도 명시된 사항인지 미확인 — 운영 시 직접 확인 필요).
2. 최신 업스트림 Dockerfile 은 베이스 이미지/스테이지 구조가 바뀌었을 수 있으니, (a)(b)는 "UID/GID 기본값, HOME, adduser 라인, permission hardening 블록" 4지점을 찾아 치환하는 식으로 적용.
3. `pyhwp`/`msoffcrypto-tool` 등은 retrieval 로더(Tika/HWP 처리) 커스텀과 연동되는 의존성이다 — 문서 파싱 담당 문서와 함께 검토.
4. `USE_CUDA=true` 기본값은 이미지 크기를 크게 늘린다. 이 포크는 Apple Silicon 용 자체 이미지 태그(`ax/open-webui:0.6.43-fix2.1-AppleSilicon`)를 쓰므로, 재적용 환경에 맞게 결정.

**관련 커밋**
- `a5955a4f0` 취약점 점검#3 (NODE_OPTIONS 활성화, 파싱 라이브러리 pip 설치)
- `0fa60ef24` nltk 관련 라이브러리 추가 (punkt/punkt_tab 다운로드)
- `0a0f67f4c` feat: USE_CUDA 기본값 true (빌드 설정)
- `1a4b2492f` refactor: 기본 비루트 사용자 설정 및 권한 강화 적용 (UID/GID 1000, HOME, appusr/appgrp, hardening 블록)

### 7. backend/start.sh — 기동 시 alembic 마이그레이션 자동 실행

**목적/배경**
- 단일 세션 강제(JTI) 기능을 위해 `auth` 테이블에 `token_jti` 컬럼을 추가하는 커스텀 alembic 마이그레이션(`a1b2c3d4e5f6_add_token_jti_to_auth.py`, 인증 담당 에이전트 문서 참조)이 추가되었는데, 컨테이너 기동 시 확실히 적용되도록 uvicorn 실행 직전에 alembic 을 명시 실행한다.

**동작 방식 / 변경 파일 및 핵심 내용**

`backend/start.sh` — uvicorn 실행 직전에 3줄 추가:
```bash
# Run migrations
alembic -c open_webui/alembic.ini upgrade head

# Run uvicorn
WEBUI_SECRET_KEY="$WEBUI_SECRET_KEY" exec "$PYTHON_CMD" -m uvicorn open_webui.main:app \
```

**재적용 가이드**
1. Open WebUI 는 앱 기동 시 내부적으로도 마이그레이션을 수행하지만, 이 커스텀은 이를 기동 전에 강제한다. 최신 버전에서 내부 마이그레이션 타이밍이 바뀌지 않았다면 그대로 이식 가능.
2. alembic CLI 가 PATH 에 있어야 한다(공식 이미지에는 포함). 작업 디렉터리가 `/app/backend` 이라는 전제(`open_webui/alembic.ini` 상대경로)에 주의.
3. 멀티 레플리카 배포에서는 기동 경합이 있을 수 있음 (현재 포크는 단일 컨테이너 전제) — 미확인.
4. 커스텀 마이그레이션 파일 자체(`backend/open_webui/migrations/versions/a1b2c3d4e5f6_add_token_jti_to_auth.py`)는 인증(JTI) 담당 문서에서 다룬다. start.sh 만 단독 적용해도 무해하다.

**관련 커밋**
- `5759a7eb4` 취약점 점검#4

### 8. 세션(JWT) 만료 기본값 단축 및 만료시간 프론트 노출 (인증 영역과 경계)

**목적/배경**
- 세션 탈취 위험 축소를 위해 JWT 만료 기본값을 4주에서 24시간으로 단축. 또 프론트의 세션 타임아웃 카운트다운/자동 갱신 UI(SessionTimeoutModal, 취약점 점검#7의 프론트 부분 — 다른 에이전트 담당)가 만료 시간을 알 수 있도록 `/api/config` 에 초 단위 만료값을 노출.

**동작 방식 / 변경 파일 및 핵심 내용**

`backend/open_webui/config.py`:
```python
JWT_EXPIRES_IN = PersistentConfig(
    "JWT_EXPIRES_IN", "auth.jwt_expiry", os.environ.get("JWT_EXPIRES_IN", "24h")
)
```
(업스트림 기본값 `"4w"` → `"24h"`. PersistentConfig 이므로 **기존 DB의 config 에 `auth.jwt_expiry` 값이 이미 저장돼 있으면 코드 기본값 변경만으로는 반영되지 않는다** — 재적용 시 DB 값 또는 관리자 설정에서 함께 변경 필요.)

`backend/open_webui/main.py` — 상단에 `from open_webui.utils.misc import parse_duration` 추가, `get_app_config()` 의 인증 사용자 블록에 추가:
```python
"enable_web_search": app.state.config.ENABLE_WEB_SEARCH,
"jwt_expires_in": f"{parse_duration(app.state.config.JWT_EXPIRES_IN).total_seconds()}" if parse_duration(app.state.config.JWT_EXPIRES_IN) else "0",
```
(`-1`(무제한) 등 parse_duration 이 None 을 반환하는 경우 `"0"` 반환. 값은 문자열화된 초 단위 float)

**재적용 가이드**
1. 이 항목은 세션 타임아웃 모달/토큰 자동 갱신(프론트, refresh API — 인증 담당 에이전트) 커스텀의 백엔드 지원부다. 함께 적용해야 의미가 있다.
2. 최신 업스트림에 유사한 만료 노출 필드가 생겼는지 먼저 확인 (미확인).
3. `jwt_expires_in` 은 인증된 사용자 블록에 있음 — 비로그인 상태에서는 내려가지 않는다.

**관련 커밋**
- `453924007` 취약점 점검#5 (JWT_EXPIRES_IN 24h)
- `4be37956d` 취약점 점검#7 (jwt_expires_in 노출)

### 9. docker-compose.yaml — 보안 관련 배포 환경변수 정리 (참고)

**목적/배경 및 동작 방식**
- 위 커스텀들의 실제 배포값 모음. ollama 서비스/의존성 제거, 자체 빌드 이미지 태그 사용(인프라 변경)과 함께 보안 환경변수가 명시돼 있다.

**변경 파일 및 핵심 내용** — 최종 상태:
```yaml
    image: ax/open-webui:0.6.43-fix2.1-AppleSilicon
    environment:
      - 'WEBUI_SECRET_KEY='
      - 'DISABLE_ADMIN=false'
      - 'CHAT_DELETE_ENABLED=true'      # 대화 자동 삭제 — 다른 에이전트 담당
      - 'CHAT_DELETE_DAYS=1'
      - 'ENABLE_PASSWORD_VALIDATION=true'
      - 'PASSWORD_BLACKLIST=kftc,admin'
      - 'ENABLE_IMAGE_CAPTURE=true'     # 기능 토글 — 다른 에이전트 담당
      - 'ENABLE_WEBPAGE_ATTACHMENT=false'
      - 'ENABLE_USER_PERSONAL_INFO=false'
```
(ollama 서비스 블록, `OLLAMA_BASE_URL`, `depends_on`, `ollama` 볼륨은 삭제됨)

**재적용 가이드**
- 본 문서 범위는 `DISABLE_ADMIN`, `ENABLE_PASSWORD_VALIDATION`, `PASSWORD_BLACKLIST` 세 개. 나머지 토글(CHAT_DELETE_*, ENABLE_IMAGE_CAPTURE 등)은 각각 대화 자동삭제/기능 토글 담당 문서를 참조.

**관련 커밋**
- `1da45db0e` 취약점 점검#6 (DISABLE_ADMIN 추가, 당시 true)
- `7948a63ae` 사용자 동의 모달 추가 및 대화 자동 삭제 기능 추가 (CHAT_DELETE_*)
- `98d3bdae5` 비밀번호 유효성 검사 강화 (ENABLE_PASSWORD_VALIDATION, PASSWORD_BLACKLIST, ollama 블록 제거 시점)
- `0f6d3c4aa` fix: docker-compose 이미지 버전 업데이트 및 웹페이지 첨부 비활성화

### 범위 밖(다른 에이전트 담당)이지만 같은 파일을 건드리는 변경 — 충돌 주의

- `backend/open_webui/main.py`: `periodic_chat_deletion` 백그라운드 태스크(CHAT_DELETE_ENABLED/DAYS), `ENABLE_IMAGE_CAPTURE`/`ENABLE_WEBPAGE_ATTACHMENT`/`ENABLE_USER_PERSONAL_INFO` config 및 features 노출 — 대화 자동삭제/기능 토글 담당.
- `backend/open_webui/utils/auth.py`: `get_current_user` 내 JTI 단일 세션 강제 블록 — 인증 담당. (점검#1에서 도입, 점검#8에서 "토큰에 jti 가 있는 경우에만 DB 값과 비교"하도록 완화된 이력만 여기 기록해 둔다.)
- `backend/open_webui/routers/auths.py`: refresh/서버 타임스탬프 등 — 인증 담당 (본 문서는 validate_password 호출부만 다룸).
- `backend/open_webui/retrieval/loaders/main.py`: Tika `rmeta/text` 엔드포인트 전환 등 문서 파싱 — 별도 영역 (Dockerfile 의 pyhwp/nltk 설치가 이와 연관).
- `backend/open_webui/models/auths.py`, `backend/open_webui/migrations/versions/a1b2c3d4e5f6_add_token_jti_to_auth.py`: JTI 컬럼 — 인증 담당.

### 재적용 권장 순서 (본 영역 전체)

1. `constants.py` 한글화 + PASSWORD_* 상수 (다른 변경들의 의존 대상)
2. `env.py`: `DISABLE_ADMIN`, `PASSWORD_BLACKLIST`
3. `utils/auth.py`: `get_admin_user` 차단, `validate_password` 교체 (+ 인증 담당의 JTI 블록과 병합)
4. `routers/auths.py`: validate_password 호출부 3곳
5. `routers/files.py`: FILE_NOT_SUPPORTED + `except HTTPException: raise`
6. `routers/ollama.py` / `routers/openai.py`: 오류 마스킹 + verify 400 통일
7. `config.py`: JWT_EXPIRES_IN 기본 24h (기존 DB persistent config 값 확인)
8. `main.py`: DISABLE_ADMIN/enable_admin_export/jwt_expires_in 노출
9. `Dockerfile`: 파싱 라이브러리 → 비루트 사용자/HOME/hardening (이미지 재빌드 및 기존 볼륨 소유권 조치)
10. `backend/start.sh`: alembic upgrade head
11. `docker-compose.yaml`: 환경변수 반영



---

# 파트 3. 이용 동의 모달 및 데이터 보존 정책


기준: 업스트림 포크 지점 `a7271532f`("0.6.43") 대비 현재 작업트리(브랜치 `0.6.43-fix2.1`) diff 를 직접 확인하여 작성함. 이 영역은 크게 (1) 사용자 동의(고지사항) 모달, (2) ChangelogModal 비활성화, (3) 대화 자동 삭제 스케줄러, (4) 공유 페이지 토큰 저장소 변경으로 구성된다.

### 1. 사용자 동의(고지사항) 모달 — AgreementModal

**목적/배경**
- 원내(기관 내부) AI 시스템 사용 시 중요정보 업로드 금지, 불법/비윤리적 이용 금지, 대화 내용 자동 저장·1년 보관 후 파기 등의 고지사항을 사용자가 최초 접속 시 반드시 확인·동의하도록 강제하기 위한 커스텀. 동의하기 전에는 ESC 키나 배경 클릭으로 모달을 닫을 수 없다.

**동작 방식**
- 앱 레이아웃(`src/routes/(app)/+layout.svelte`)의 `onMount` 마지막에서 `localStorage.getItem('agreedToTerms')` 가 없으면 `showAgreement = true` 로 모달을 띄운다.
- 모달은 `static/agreement.md` 를 `fetch('/agreement.md')` 로 읽어 `marked.parse` + `DOMPurify.sanitize` 를 거쳐 렌더링한다 (정적 파일이므로 백엔드 API/설정 키 없음).
- "동의하기" 버튼 클릭 시 `localStorage.setItem('agreedToTerms', 'true')` 후 모달을 닫는다. 즉 동의 여부는 **브라우저(localStorage) 단위**로만 저장되며, 서버/DB에는 기록되지 않는다. 브라우저를 바꾸거나 localStorage 를 지우면 다시 표시된다.
- `dismissible={false}` 로 렌더링되어 ESC/배경 클릭 닫기가 차단된다(공용 `Modal.svelte` 에 `dismissible` prop 신규 추가).

**변경 파일 및 핵심 내용**

1) `src/lib/components/AgreementModal.svelte` — **신규 파일** (전체 62라인, 아래가 최종 코드 전문의 핵심):

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
				동의하기
			</button>
		</div>
	</div>
</Modal>
```

- 버튼 텍스트는 원래 `{$i18n.t('Agree and Continue')}` 였다가 커밋 `fa6d77876` 에서 하드코딩 한글 `동의하기` 로 변경됨.
- 제목의 `$i18n.t('Agreement')` 키는 `ko-KR/translation.json` / `en-US/translation.json` 어디에도 추가되어 있지 않아 화면에는 키 문자열 그대로 "Agreement" 가 표시된다 (확인됨 — 재적용 시 번역 키 추가 여부 결정 필요).
- `WEBUI_NAME` import 는 실제로 사용되지 않음(불필요 import).

2) `static/agreement.md` — **신규 파일** (최종 전문):

```markdown
< 원내 중요정보 보호 및 정보주체 권리 보장을 위한 고지사항 >

1. **업무 관련 중요자료는 AI시스템에 업로드 금지**
  * ① 비밀 및 대외비 문서, ② 개인정보 및 신용정보 파일, ③ 그 밖의 업무별 비공개 자료

2. **불법, 부당한 목적의 AI시스템 이용 금지**
  * ① 시스템 또는 데이터 접근권한 획득, ② 허용된 열람범위를 벗어난 정보 탐색, ③ 필터 등 보호조치 우회 시도, ④ 그 밖의 각종 권한, 정보 탈취

3. **비윤리적 목적의 AI시스템 활용* 금지**
  * ① 민감정보 입력을 유도하는 대화, ② 개인정보를 이용한 악의적 콘텐츠 생성, ③ 그 밖의 사생활 침해를 야기할 수 있는 각종 시도

※ AI시스템과 사용자 사이의 대화 내용은 책임추적성 확보를 위해 자동 저장되며, 1년 간 보관 후 자동 파기됩니다.
```

- **고지사항 문구 수정**: 커밋 `2b4840c31` 에서 제목이 `...고지사항(예시) >` → `...고지사항 >` 으로 변경됨(`(예시)` 제거). 그 외 본문 변경 없음.

3) `src/lib/components/common/Modal.svelte` — `dismissible` prop 추가 (커밋 `fa6d77876`):

```diff
 	export let containerClassName = 'p-3';
 	export let className = 'bg-white/95 dark:bg-gray-900/95 backdrop-blur-sm rounded-4xl';
 
+	export let dismissible = true;
```

```diff
 	const handleKeyDown = (event: KeyboardEvent) => {
-		if (event.key === 'Escape' && isTopModal()) {
+		if (event.key === 'Escape' && isTopModal() && dismissible) {
 			console.log('Escape');
 			show = false;
 		}
```

```diff
 		on:mousedown={() => {
-			show = false;
+			if (dismissible) {
+				show = false;
+			}
 		}}
```

4) `src/routes/(app)/+layout.svelte` — 모달 연결 (커밋 `7948a63ae`). 이 파일은 세션 타임아웃 등 다른 영역의 변경이 대량 섞여 있으며, 이 영역에 해당하는 부분만 발췌:

```diff
+	import AgreementModal from '$lib/components/AgreementModal.svelte';
...
 	let showTimeoutModal = false;
+	let showAgreement = false;
```

`onMount` 내부, `await tick();` 직후 / `loaded = true;` 직전:

```diff
 		await tick();
 
+		if (!localStorage.getItem('agreedToTerms')) {
+			showAgreement = true;
+		}
+
 		loaded = true;
```

템플릿:

```diff
 <SettingsModal bind:show={$showSettings} />
-<ChangelogModal bind:show={$showChangelog} />
+<!-- <ChangelogModal bind:show={$showChangelog} /> -->
+<AgreementModal bind:show={showAgreement} />
```

**재적용 가이드**
1. `static/agreement.md` 를 그대로 복사(정적 파일이라 버전 충돌 없음).
2. `AgreementModal.svelte` 를 그대로 복사. 최신 업스트림에서 `marked`/`DOMPurify` 사용 패턴이 바뀌었는지(예: 공용 마크다운 렌더 컴포넌트 존재 여부)만 확인.
3. 공용 `Modal.svelte` 에 `dismissible` prop 이 이미 있는지 최신 업스트림에서 먼저 확인할 것 — 없으면 위 3개 지점(prop 선언, ESC 핸들러, 배경 mousedown)에 동일 패치. 최신 버전에서 Modal 구현이 크게 리팩터링되었을 수 있으므로 "ESC + 배경클릭 차단" 이라는 의도 기준으로 이식.
4. `(app)/+layout.svelte` 에 import / `showAgreement` 상태 / onMount 체크 / 템플릿 배치 4곳을 추가. `agreedToTerms` 는 localStorage 키이므로 마이그레이션 불필요.
5. 선택: `Agreement` i18n 키를 ko-KR 에 추가하면 제목도 한글화 가능(현재 포크에는 없음).

**관련 커밋**
- `7948a63ae` 사용자 동의 모달 추가 및 대화 자동 삭제 기능 추가 (모달·agreement.md 최초 도입)
- `fa6d77876` fix(agreement): 동의 없는 모달 닫기 방지 및 버튼 한글화 (`dismissible` prop, 동의하기 버튼)
- `2b4840c31` feat: 대화 감사 추적 리포트 스크립트 추가 및 고지사항 문구 수정 (제목의 `(예시)` 제거)

### 2. ChangelogModal 비활성화

**목적/배경**
- 커스텀 포크에서는 버전 업데이트 시 관리자에게 뜨는 "What's New(변경사항)" 모달이 불필요하여 비활성화. 대신 최초 접속 시 AgreementModal 이 그 자리를 차지한다.

**동작 방식**
- 삭제가 아니라 **주석 처리** 방식. `ChangelogModal` 컴포넌트 파일 자체는 남아 있으나 레이아웃에서 import/렌더링이 주석 처리되고, 표시 트리거 로직(`showChangelog.set(...)`)은 제거되었다.

**변경 파일 및 핵심 내용**

1) `src/routes/(app)/+layout.svelte` (최초 비활성화는 커밋 `6123e56c5` "취약점 점검#2"):

```diff
-	import ChangelogModal from '$lib/components/ChangelogModal.svelte';
+	// import ChangelogModal from '$lib/components/ChangelogModal.svelte';
```

`onMount` 내 트리거 로직 — 포크 지점 대비 최종 diff 에서는 아래 블록이 **완전히 제거**된 상태(중간 커밋에서는 주석 처리였다가 이후 정리됨):

```diff
-		if ($user?.role === 'admin' && ($settings?.showChangelog ?? true)) {
-			showChangelog.set($settings?.version !== $config.version);
-		}
```

템플릿:

```diff
-<ChangelogModal bind:show={$showChangelog} />
+<!-- <ChangelogModal bind:show={$showChangelog} /> -->
```

- `showChangelog` store import(`$lib/stores`)는 레이아웃에 여전히 남아 있음(미사용 상태).

2) `src/lib/components/ChangelogModal.svelte` — 기능 변경 아님. 전역 "토큰 저장소를 localStorage → sessionStorage 로 이전" 커스텀(커밋 `453924007` "취약점 점검#5", 세션 보안 영역)의 일부로 1줄만 변경:

```diff
-					await updateUserSettings(localStorage.token, { ui: $settings });
+					await updateUserSettings(sessionStorage.token, { ui: $settings });
```

**재적용 가이드**
1. 최신 업스트림 `(app)/+layout.svelte` 에서 `ChangelogModal` import·렌더링·`showChangelog.set` 트리거 3곳을 찾아 제거/주석 처리 (업스트림에서 위치나 조건이 바뀌었을 수 있으니 `showChangelog` 로 grep).
2. `ChangelogModal.svelte` 의 sessionStorage 변경은 이 모달이 비활성화된 상태에선 실질 효과가 없다. 다만 포크 전체가 sessionStorage 토큰 정책을 쓰므로, 일괄 치환 시 함께 처리하면 됨(세션/토큰 보안 영역 문서 참조).

**관련 커밋**
- `6123e56c5` 취약점 점검#2 (레이아웃에서 ChangelogModal 비활성화)
- `453924007` 취약점 점검#5 (ChangelogModal.svelte 내 sessionStorage 전환)

### 3. 대화 자동 삭제 (데이터 보존 정책, CHAT_DELETE_ENABLED / CHAT_DELETE_DAYS)

**목적/배경**
- 고지사항의 "대화 내용은 1년 간 보관 후 자동 파기" 정책을 실제로 이행하기 위한 서버 측 자동 삭제 기능. 백엔드가 1시간마다 보존 기간을 초과한 채팅을 일괄 삭제한다.

**동작 방식**
- 설정 키 2개가 `PersistentConfig` 로 추가됨 (환경변수 → DB config 저장):
  - `CHAT_DELETE_ENABLED` (config path `chat.delete.enable`, 기본 `False`)
  - `CHAT_DELETE_DAYS` (config path `chat.delete.days`, 기본 `365`)
- FastAPI `lifespan` 에서 백그라운드 태스크 `periodic_chat_deletion()` 을 기동. 1시간(`60 * 60` 초)마다 `CHAT_DELETE_ENABLED` 를 확인하고, 활성화 시 `Chats.delete_chats_older_than(days)` 를 스레드풀에서 실행.
- 삭제 기준은 `Chat.updated_at < (now - days*86400)` — **updated_at(마지막 수정 시각) 기준**이지 created_at 기준이 아님.
- 관리 UI는 없음. 환경변수/DB config 로만 제어. 별도 API 엔드포인트 없음.

**변경 파일 및 핵심 내용**

1) `backend/open_webui/config.py` — `ENABLE_FOLLOW_UP_GENERATION` 정의 바로 뒤에 추가:

```python
CHAT_DELETE_ENABLED = PersistentConfig(
    "CHAT_DELETE_ENABLED",
    "chat.delete.enable",
    os.environ.get("CHAT_DELETE_ENABLED", "False").lower() == "true",
)

CHAT_DELETE_DAYS = PersistentConfig(
    "CHAT_DELETE_DAYS",
    "chat.delete.days",
    int(os.environ.get("CHAT_DELETE_DAYS", "365")),
)
```

2) `backend/open_webui/models/chats.py` — `ChatTable` 클래스에 메서드 추가 (`update_shared_chat_by_id`/공유 관련 메서드 근처, `get_shared_chats_by_file_id` 바로 앞). `import time` 은 파일 상단에 이미 존재:

```python
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

3) `backend/open_webui/main.py` — 세 군데:

- config import 블록에 추가:

```python
from open_webui.config import (
    ...
    AppConfig,
    reset_config,
    CHAT_DELETE_ENABLED,
    CHAT_DELETE_DAYS,
)
```

- `lifespan` 내부, `asyncio.create_task(periodic_usage_pool_cleanup())` 직후:

```python
    async def periodic_chat_deletion():
        while True:
            if app.state.config.CHAT_DELETE_ENABLED:
                try:
                    days = app.state.config.CHAT_DELETE_DAYS
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
```

- app.state 등록 (`ENABLE_COMMUNITY_SHARING` 등록 근처):

```python
app.state.config.CHAT_DELETE_ENABLED = CHAT_DELETE_ENABLED
app.state.config.CHAT_DELETE_DAYS = CHAT_DELETE_DAYS
```

- 의존성: `anyio.to_thread`(상단에 `import anyio.to_thread` 기존 존재), `from open_webui.models.chats import Chats`(기존 존재) — 최신 버전 이식 시 두 import 존재 여부 확인.

4) `docker-compose.yaml` — 배포 환경변수 (커밋 `7948a63ae` 에서 추가):

```yaml
    environment:
      - 'CHAT_DELETE_ENABLED=true'
      - 'CHAT_DELETE_DAYS=1'
```

**주의**: 현재 compose 에는 테스트용으로 보이는 `CHAT_DELETE_DAYS=1`(1일)이 들어 있어, 고지사항의 "1년 보관" 문구와 불일치한다. 운영 배포 시 `365` 로 맞춰야 정책과 일치한다. (docker-compose.yaml 의 이미지 태그·다른 env 항목들은 별도 영역의 변경임.)

**재적용 가이드**
1. config.py → models/chats.py → main.py 순으로 적용. DB 스키마 변경이 없으므로 Alembic 마이그레이션 불필요.
2. **PersistentConfig 주의**: 최초 기동 시 env 값이 DB config(`chat.delete.enable`, `chat.delete.days`)에 저장된다. 이후 env 만 바꿔도 DB 값이 우선될 수 있으므로(`ENABLE_PERSISTENT_CONFIG` 정책에 따름), 운영 중 값 변경 시 admin config API 또는 DB config 갱신 필요.
3. **일괄 삭제의 한계**: 업스트림의 `delete_chat_by_id` 는 삭제 시 `delete_shared_chat_by_chat_id` 로 공유 사본까지 정리하지만, `delete_chats_older_than` 은 `Chat.updated_at` 조건의 벌크 delete 만 수행한다. 공유 채팅도 같은 `chat` 테이블 행이므로 자신의 `updated_at` 이 기준을 넘으면 함께 삭제되지만, 원본만 먼저 지워지고 공유 사본이 잠시 남는 시차가 있을 수 있다. 또한 채팅에 첨부된 파일(file 테이블/스토리지)은 삭제하지 않는다 — 완전한 보존정책이 필요하면 최신 버전 이식 시 보강 검토.
4. 멀티 워커/멀티 레플리카 환경에서는 워커마다 태스크가 떠서 시간당 여러 번 실행될 수 있으나 삭제 자체는 멱등이라 치명적이지 않음(로그 중복 정도).
5. 최신 업스트림에서 `lifespan` 구조나 `periodic_usage_pool_cleanup` 위치가 바뀌었을 수 있으니, "lifespan 에서 backgound task 하나 추가" 라는 의도 기준으로 배치.
6. 참고(이 영역 밖, 별도 영역에서 문서화): DB 레벨 수동 정리 스크립트 `scripts/cleanup_chats.sh`(PostgreSQL, dry-run/`--execute`, `APP_USER`/`APP_PASSWORD`/`APP_DB` 환경변수)와 감사 추적용 `scripts/chat_audit_report.sh` 가 이 보존 정책을 운영 측면에서 보조한다.

**관련 커밋**
- `7948a63ae` 사용자 동의 모달 추가 및 대화 자동 삭제 기능 추가 (config.py, main.py, models/chats.py, docker-compose 전부 이 커밋)

### 4. 공유 페이지(`src/routes/s/[id]/+page.svelte`) 변경

**목적/배경**
- 이 파일의 변경은 공유 기능 자체의 수정이 아니라, 포크 전역의 **인증 토큰 저장소 localStorage → sessionStorage 이전**(XSS 시 토큰 탈취 완화, 브라우저 종료 시 세션 소멸 목적의 보안 커스텀)의 일부다.

**동작 방식 / 변경 내용**
- 파일 내 5곳에서 `localStorage.token` → `sessionStorage.token` 단순 치환. 기능 로직 변경 없음:

```diff
-		const userSettings = await getUserSettings(localStorage.token).catch((error) => {
+		const userSettings = await getUserSettings(sessionStorage.token).catch((error) => {
```

동일 패턴으로 `getModels(...)`, `getChatByShareId(...)`, `getUserById(...)`, `cloneSharedChatById(...)` 호출부의 토큰 인자가 모두 `sessionStorage.token` 으로 변경됨.

**재적용 가이드**
1. 세션/토큰 보안 영역의 전역 치환 작업과 함께 처리하면 됨. 단독으로는 의미가 없고, 로그인 시 토큰을 sessionStorage 에 쓰는 커스텀(다른 영역)이 전제되어야 한다.
2. 최신 업스트림에서 이 페이지의 API 호출부가 바뀌었을 수 있으므로 파일 내 `localStorage.token` 을 grep 하여 일괄 치환.

**관련 커밋**
- `453924007` 취약점 점검#5

### 부록: 이 영역과 겹치는 파일에 대한 스코프 메모
- `src/routes/(app)/+layout.svelte` 에는 세션 타임아웃 모달/자동 갱신(슬라이딩 세션), sessionStorage 치환 등 **다른 영역의 대규모 변경**이 함께 들어 있다. 본 문서는 AgreementModal 연결부와 ChangelogModal 비활성화 부분만 다뤘다. 현재 작업트리에는 이 파일의 커밋 안 된 변경도 있으나(슬라이딩 세션 자동 갱신 관련), 이는 이 영역과 무관함을 확인했다.
- `docker-compose.yaml` 도 이미지 태그, `DISABLE_ADMIN`, 비밀번호 정책, 이미지 캡처/웹페이지 첨부 토글 등 다른 영역 env 가 섞여 있으며, 본 문서 소관은 `CHAT_DELETE_ENABLED`/`CHAT_DELETE_DAYS` 두 줄이다.
- 동의 여부의 서버 측 저장(사용자별 DB 기록)은 구현되어 있지 않음 — 미확인이 아니라 "미구현"으로 확인됨.
- `migration_guide_0.6.43_fix1_to_0.7.2_fix1.md` 의 이 영역 서술은 실제 diff 와 대체로 일치하나, 가이드에는 CHAT_DELETE 설정이 단순 상수처럼 적혀 있는 반면 실제 구현은 `PersistentConfig` 임(본 문서가 실제 코드 기준).


---

# 파트 4. 기능 토글 (이미지 캡처 / 웹페이지 첨부 / 계정 개인정보 UI)

### 개요: 3개 기능 토글 커스텀 (ENABLE_IMAGE_CAPTURE / ENABLE_WEBPAGE_ATTACHMENT / ENABLE_USER_PERSONAL_INFO)

이 영역은 환경변수 → 백엔드 `PersistentConfig` → `/api/config` 응답의 `features` 플래그 → 프론트엔드 `$config.features.*` 조건부 렌더링으로 이어지는 동일한 패턴의 기능 토글 3종이다. 세 플래그 모두 **UI(진입점) 숨김 전용**이며, 백엔드 API 차단은 없다(아래 각 섹션의 주의점 참조). 저장소의 `migration_guide_0.6.43_fix1_to_0.7.2_fix1.md`에는 이 3개 플래그가 전혀 언급되어 있지 않다(grep 확인). 해당 커밋들이 fix1 이후(2026-02~03)에 추가된 fix2 기능이기 때문이므로, 0.7.x 이식 시 이 문서를 기준으로 새로 반영해야 한다.

공통 백엔드 구조 (`backend/open_webui/config.py`, `ENABLE_NOTES` 정의 바로 뒤에 위치):

```python
ENABLE_IMAGE_CAPTURE = PersistentConfig(
    "ENABLE_IMAGE_CAPTURE",
    "ui.enable_image_capture",
    os.environ.get("ENABLE_IMAGE_CAPTURE", "True").lower() == "true",
)

ENABLE_WEBPAGE_ATTACHMENT = PersistentConfig(
    "ENABLE_WEBPAGE_ATTACHMENT",
    "ui.enable_webpage_attachment",
    os.environ.get("ENABLE_WEBPAGE_ATTACHMENT", "True").lower() == "true",
)

ENABLE_USER_PERSONAL_INFO = PersistentConfig(
    "ENABLE_USER_PERSONAL_INFO",
    "ui.enable_user_personal_info",
    os.environ.get("ENABLE_USER_PERSONAL_INFO", "True").lower() == "true",
)
```

공통 백엔드 배선 (`backend/open_webui/main.py`):

1) config import 블록(`ENABLE_NOTES` 다음)에 3개 심볼 import 추가:
```python
    ENABLE_NOTES,
    ENABLE_IMAGE_CAPTURE,
    ENABLE_WEBPAGE_ATTACHMENT,
    ENABLE_USER_PERSONAL_INFO,
```

2) `app.state.config` 할당(`app.state.config.ENABLE_NOTES = ENABLE_NOTES` 다음):
```python
app.state.config.ENABLE_IMAGE_CAPTURE = ENABLE_IMAGE_CAPTURE
app.state.config.ENABLE_WEBPAGE_ATTACHMENT = ENABLE_WEBPAGE_ATTACHMENT
app.state.config.ENABLE_USER_PERSONAL_INFO = ENABLE_USER_PERSONAL_INFO
```

3) `GET /api/config`(`get_app_config`)의 `features` 딕셔너리 중 **`if user is not None` 인 경우에만 펼쳐지는 내부 블록**에 추가(`"enable_notes"` 다음, `"enable_web_search"` 앞):
```python
"enable_image_capture": app.state.config.ENABLE_IMAGE_CAPTURE,
"enable_webpage_attachment": app.state.config.ENABLE_WEBPAGE_ATTACHMENT,
"enable_user_personal_info": app.state.config.ENABLE_USER_PERSONAL_INFO,
```

공통 주의점:
- **인증된 사용자에게만 플래그가 내려간다.** 미인증 상태의 `/api/config` 응답에는 이 키들이 없고, 프론트는 전부 `?? true` 폴백을 쓰므로 "플래그 부재 = 기능 노출"이다. 기능을 끄려면 반드시 값이 `false`로 내려가야 한다.
- **PersistentConfig 특성**: 초기값은 환경변수에서 읽지만, DB `config` 테이블에 `ui.enable_image_capture` 등의 키가 이미 저장돼 있으면(예: config export/import 경유) `ENABLE_PERSISTENT_CONFIG=true`(기본값)일 때 DB 값이 환경변수보다 우선한다. 이 3개 플래그를 바꾸는 관리자 설정 UI는 이 포크에 없으므로 평상시엔 환경변수가 실질적 소스다.
- 세 플래그 모두 **프론트 렌더링만 막는다**. 웹페이지 로딩/파일 업로드/프로필 갱신 API 자체는 백엔드에서 플래그로 차단하지 않는다(grep으로 백엔드 사용처가 `config.py`, `main.py` 뿐임을 확인). 보안 목적이라면 이식 시 백엔드 차단 추가를 검토할 것.

---

### 1. 채팅 입력 메뉴: 이미지 캡처(Capture) / 웹페이지 첨부(Attach Webpage) 토글

**목적/배경**: 사내 보안 정책상 화면 캡처 첨부와 외부 웹페이지 첨부 기능을 서버 설정으로 끌 수 있어야 한다. 순정 0.6.43은 두 메뉴가 무조건 노출된다. 실제 운영 배포(`docker-compose.yaml`)에서는 웹페이지 첨부를 `false`로 꺼서 사용 중이다.

**동작 방식**:
- 환경변수 `ENABLE_IMAGE_CAPTURE`(기본 `True`), `ENABLE_WEBPAGE_ATTACHMENT`(기본 `True`).
- `/api/config` → `$config.features.enable_image_capture`, `$config.features.enable_webpage_attachment`.
- 채팅 입력창의 "+" 드롭다운(`InputMenu.svelte`)에서 각 메뉴 항목을 `{#if}`로 감싸 숨긴다.

**변경 파일 및 핵심 내용**:
- `backend/open_webui/config.py`, `backend/open_webui/main.py`: 위 공통 구조 참조.
- `src/lib/components/chat/MessageInput/InputMenu.svelte`: 기존 "Capture" 항목(모바일이면 `camera-input` 클릭, 아니면 `screenCaptureHandler()` 호출하는 `<Tooltip>` + `DropdownMenu.Item` 블록 전체)을 다음으로 감쌈:

```svelte
{#if $config?.features?.enable_image_capture ?? true}
    <Tooltip ...>
        <DropdownMenu.Item ... on:click={() => { if (fileUploadEnabled) { if (!detectMobile()) { screenCaptureHandler(); } else { ... camera-input ... } } }}>
            <Camera />
            <div class=" line-clamp-1">{$i18n.t('Capture')}</div>
        </DropdownMenu.Item>
    </Tooltip>
{/if}
```

바로 이어지는 "Attach Webpage" 항목(`showAttachWebpageModal = true` 하는 블록)도 동일 패턴:

```svelte
{#if $config?.features?.enable_webpage_attachment ?? true}
    <Tooltip ...>
        <DropdownMenu.Item ... on:click={() => { if (fileUploadEnabled) { showAttachWebpageModal = true; } }}>
            <GlobeAlt />
            <div class="line-clamp-1">{$i18n.t('Attach Webpage')}</div>
        </DropdownMenu.Item>
    </Tooltip>
{/if}
```

변경은 이 두 `{#if}` 래핑(및 그에 따른 들여쓰기 재조정)이 전부다. 같은 파일 상단의 `<AttachWebpageModal bind:show={showAttachWebpageModal} ...>` 컴포넌트와 숨겨진 `<input id="camera-input">`는 **조건 없이 그대로 렌더링**된다(진입 버튼만 숨김).

**재적용 가이드**:
1. `config.py`에 두 `PersistentConfig` 추가 → `main.py` import/`app.state.config` 할당/`features` 응답 추가 → `InputMenu.svelte`의 두 메뉴 항목을 `{#if}`로 래핑, 순서로 적용.
2. 업스트림 0.7.x에서 `InputMenu.svelte` 구조(메뉴 항목 구성, 파일명)가 바뀌었을 수 있다(미확인). "Capture"와 "Attach Webpage"에 해당하는 항목을 찾아 같은 조건으로 감싸면 된다.
3. 붙여넣기/드래그앤드롭 등 다른 첨부 경로나 백엔드 web-loader 엔드포인트는 차단되지 않음을 인지할 것.
4. DB 마이그레이션 불필요.

**관련 커밋**: `8497673dc` "feat: 이미지 캡처 및 웹페이지 첨부 기능에 대한 구성 옵션을 추가하고 UI를 업데이트합니다." (config.py, main.py, docker-compose.yaml, InputMenu.svelte)

---

### 2. 지식(Knowledge) 컬렉션 "웹페이지 추가" 버튼 토글 — **커밋 안 된 작업트리 변경**

**목적/배경**: 섹션 1에서 채팅 입력의 웹페이지 첨부는 숨겼지만, 워크스페이스 > 지식 베이스의 "+" 메뉴에 있는 "Add webpage" 항목은 여전히 노출되어 있었다. 동일한 `ENABLE_WEBPAGE_ATTACHMENT` 플래그로 이 진입점도 함께 숨기는 후속 패치다. **이 변경은 현재 커밋되지 않은 작업트리 상태로만 존재한다.**

**동작 방식**: 섹션 1과 동일한 `$config.features.enable_webpage_attachment` 플래그를 재사용. 새 백엔드 설정은 없다.

**변경 파일 및 핵심 내용**:
- `src/lib/components/workspace/Knowledge/KnowledgeBase/AddContentMenu.svelte` (작업트리):

script 블록에 store import 추가:
```svelte
import { config } from '$lib/stores';
const i18n = getContext('i18n');
```

"Add webpage" 항목(`onAddWebpage()` 호출, `GlobeAlt` 아이콘)을 래핑 — 원 작성자가 내부 들여쓰기를 조정하지 않고 `{#if}`/`{/if}`만 삽입한 형태:
```svelte
{#if $config?.features?.enable_webpage_attachment ?? true}
<DropdownMenu.Item
    class="flex gap-2 items-center px-3 py-1.5 text-sm  cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800  rounded-xl"
    on:click={() => {
        onAddWebpage();
    }}
>
    <GlobeAlt strokeWidth="2" />
    <div class="flex items-center">{$i18n.t('Add webpage')}</div>
</DropdownMenu.Item>
{/if}
```

**재적용 가이드**:
1. 섹션 1(플래그 배선)이 선행되어야 한다.
2. **커밋되지 않은 변경이므로 브랜치 체크아웃만으로는 따라오지 않는다.** 이식 시 이 문서(또는 작업트리 diff)를 기준으로 직접 적용할 것.
3. 지식 문서의 "웹 검색/디렉터리 동기화" 등 다른 항목은 건드리지 않는다. 백엔드의 웹 URL 처리 엔드포인트는 여전히 열려 있다.

**관련 커밋**: 없음(작업트리 미커밋 상태, 2026-07-02 기준).

---

### 3. 계정 설정 개인정보(성별/생년월일) UI 토글 (ENABLE_USER_PERSONAL_INFO)

**목적/배경**: 사내 환경에서 사용자 성별·생년월일 같은 개인정보 수집 UI를 노출하지 않기 위함. 운영 배포에서는 `false`로 꺼져 있다.

**동작 방식**:
- 환경변수 `ENABLE_USER_PERSONAL_INFO`(기본 `True`) → `/api/config` → `$config.features.enable_user_personal_info`.
- 설정 모달 > 계정(`Account.svelte`)에서 **Gender 선택(select + custom 입력)과 Birth Date 입력 필드 블록만** `{#if}`로 감싼다. Name, Bio, 프로필 이미지는 그대로 노출된다.

**변경 파일 및 핵심 내용**:
- `backend/open_webui/config.py`, `backend/open_webui/main.py`: 공통 구조 참조.
- `src/lib/components/chat/Settings/Account.svelte`: Bio 필드 블록 바로 다음부터,

```svelte
{#if $config?.features?.enable_user_personal_info ?? true}
    <div class="flex flex-col w-full mt-2">
        <div class=" mb-1 text-xs font-medium">{$i18n.t('Gender')}</div>
        ... (select: Prefer not to say / Male / Female / Custom, custom 시 텍스트 입력) ...
    </div>

    <div class="flex flex-col w-full mt-2">
        <div class=" mb-1 text-xs font-medium">{$i18n.t('Birth Date')}</div>
        <div class="flex-1">
            <input ... type="date" bind:value={dateOfBirth} required />
        </div>
    </div>
{/if}
```

내부 마크업 자체는 순정 0.6.43과 동일하고 들여쓰기 한 단계 증가 + `{#if}` 래핑만 추가된 것이다.

**주의(같은 파일의 타 영역 변경)**: `Account.svelte`의 diff에는 이 토글 외에 (a) `localStorage.token` → `sessionStorage.token` 전면 교체, (b) 에러 토스트를 상세 에러 대신 `$i18n.t('Something went wrong. Please contact administrator.')` 고정 문구로 바꾸는 변경이 섞여 있다. 이는 각각 커밋 `453924007`(취약점 점검#5, 토큰 저장소 변경)과 `702db1ef5`(취약점 점검8, 에러 메시지 마스킹) 소속으로, **세션/보안 커스텀 영역**에 해당한다. 마찬가지로 `src/lib/components/chat/Settings/Account/UpdatePassword.svelte`, `src/lib/components/chat/Settings/Account/UserProfileImage.svelte`의 diff는 `localStorage`→`sessionStorage` 교체가 전부이며 이 토글 기능과 무관하므로 본 영역에서는 다루지 않는다(해당 영역 문서 참조).

**재적용 가이드**:
1. 백엔드 플래그 배선 후 `Account.svelte`의 Gender/Birth Date 블록을 래핑.
2. **UI 숨김일 뿐, 저장 로직은 그대로다.** `updateProfileHandler`는 플래그와 무관하게 `gender: gender ? gender : null, date_of_birth: dateOfBirth ? dateOfBirth : null`을 항상 전송하고, 백엔드 `updateUserProfile` API도 해당 필드를 계속 받는다. 데이터 수집을 완전히 막으려면 백엔드 검증 추가가 필요하다(이 포크에는 없음 — 확인 완료).
3. 업스트림 0.7.x에서 Account 설정 화면 구조가 바뀌었을 수 있다(미확인). Gender/Birth Date에 해당하는 블록을 찾아 동일 조건으로 감싸면 된다.
4. DB 마이그레이션 불필요.

**관련 커밋**: `0cb6d2410` "feat: 사용자 개인 정보 설정 활성화 여부에 따라 계정 UI를 조건부로 표시하도록 변경" (config.py, main.py, docker-compose.yaml, Account.svelte)

---

### 4. docker-compose.yaml 배포 설정 (본 영역 관련 env)

**목적/배경**: 실제 운영 배포에서 각 토글의 값을 지정한다.

**변경 파일 및 핵심 내용**: `docker-compose.yaml`의 `open-webui` 서비스 `environment`에 추가된 본 영역 관련 항목(최종 작업트리 기준):

```yaml
environment:
  - 'ENABLE_IMAGE_CAPTURE=true'
  - 'ENABLE_WEBPAGE_ATTACHMENT=false'
  - 'ENABLE_USER_PERSONAL_INFO=false'
```

이력: `8497673dc`에서 `ENABLE_IMAGE_CAPTURE=true`, `ENABLE_WEBPAGE_ATTACHMENT=true` 추가 → `0cb6d2410`에서 `ENABLE_USER_PERSONAL_INFO=false` 추가 → `0f6d3c4aa`에서 `ENABLE_WEBPAGE_ATTACHMENT`를 `false`로 변경(운영 정책 확정) 및 이미지 태그를 `ax/open-webui:0.6.43-fix2.1-AppleSilicon`으로 변경.

같은 파일에는 다른 영역 소속 변경(ollama 서비스 제거, `DISABLE_ADMIN`, `CHAT_DELETE_ENABLED/DAYS`, `ENABLE_PASSWORD_VALIDATION`, `PASSWORD_BLACKLIST`, 커스텀 이미지명)이 섞여 있다 — 본 문서는 위 3개 env만 담당.

**재적용 가이드**: 새 버전 compose 파일에 위 3개 env를 그대로 추가. 운영 정책값은 `이미지 캡처 켬 / 웹페이지 첨부 끔 / 개인정보 UI 끔`이다. `?? true` 폴백 때문에 env를 생략하면 기능이 켜진 것과 같으므로, 끄려는 항목은 반드시 `false`를 명시해야 한다.

**관련 커밋**: `8497673dc`, `0cb6d2410`, `0f6d3c4aa` "fix: docker-compose 이미지 버전 업데이트 및 웹페이지 첨부 비활성화"

---

### 검증 메모

- 세 플래그의 전체 사용처를 저장소 전역 grep으로 확인: 백엔드는 `config.py`(정의)와 `main.py`(배선/응답) 뿐, 프론트는 `InputMenu.svelte`(2곳), `AddContentMenu.svelte`(1곳, 작업트리), `Account.svelte`(1곳) 뿐이다. 그 외 signup 화면 등 다른 UI에는 영향 없음.
- `main.py` diff에는 본 영역 외 변경(`periodic_chat_deletion`, `jwt_expires_in` features 노출, `DISABLE_ADMIN`, `enable_admin_export` 등)이 섞여 있으나 이는 각각 다른 영역(대화 자동삭제/세션/관리자 제한) 소속이다.
- i18n: 커스텀 문자열 추가 없음 — 기존 키(`Capture`, `Attach Webpage`, `Add webpage`, `Gender`, `Birth Date`)만 재사용하므로 번역 파일 수정 불필요(본 영역 한정).


---

# 파트 5. 문서 파싱(Tika) 및 파일 업로드 처리


기준: 업스트림 0.6.43(`a7271532f`) 대비 `0.6.43-fix2.1` 브랜치의 누적 diff. 아래 내용은 전부 실제 `git diff` / `git show` 로 확인한 것이다.

> **중요 선행 공지 — rmeta/text 변경은 최종적으로 롤백됨**
> 커밋 `a8841c5a5` 에서 Tika 엔드포인트를 `tika/text` → `rmeta/text` 로 바꾸고, 배열 응답 처리 및 MIME 타입 전달을 추가했으나, **같은 날 커밋 `1a4b2492f` 에서 세 가지 모두 원복되었다.** 따라서 fork 지점 대비 최종(누적) diff 에는 rmeta 관련 코드가 존재하지 않으며, 최종 상태는 "`tika/text` 엔드포인트 + 로깅/에러 처리 강화"다. 재이식 시 `a8841c5a5` 를 그대로 적용하면 안 되고 최종 상태(아래 §1)를 기준으로 해야 한다.

---

### 1. Tika 로더 로깅 및 에러 처리 강화 (최종 상태)

**목적/배경**
- Tika 서버 연동 실패 시 원인 파악이 어려웠음(기존 예외 메시지는 `r.reason` 만 포함). 연결 실패와 HTTP 오류를 구분해 로그에 남기고, 응답 본문까지 포함한 상세 에러를 올리기 위한 변경.

**동작 방식**
- 파일 추출 시작 시 `log.info`, 호출 엔드포인트를 `log.debug` 로 기록.
- `requests.put` 호출을 try/except 로 감싸 **연결 자체가 실패**한 경우(`Failed to connect to Tika at {endpoint}`)를 별도로 로깅 후 re-raise.
- HTTP 응답이 실패(`not r.ok`)인 경우 상태코드·reason·응답 본문(`r.text`)까지 포함해 로깅/예외 발생.
- 텍스트 파일이 Tika 대신 `TextLoader` 로 폴백될 때 debug 로그 추가.
- 환경변수/설정 키 변경 없음. `TIKA_SERVER_URL` 등 기존 설정 그대로 사용.

**변경 파일 및 핵심 내용**

`backend/open_webui/retrieval/loaders/main.py` — `TikaLoader.load()` 최종 코드:

```python
def load(self) -> list[Document]:
    log.info(f"Starting Tika extraction for file: {self.file_path}")
    with open(self.file_path, "rb") as f:
        data = f.read()
    ...
    endpoint = self.url
    if not endpoint.endswith("/"):
        endpoint += "/"
    endpoint += "tika/text"          # rmeta/text 아님 — 원복된 최종 상태

    log.debug(f"Tika endpoint: {endpoint}")
    try:
        r = requests.put(endpoint, data=data, headers=headers)
    except Exception as e:
        log.error(f"Failed to connect to Tika at {endpoint}: {e}")
        raise e

    if r.ok:
        raw_metadata = r.json()
        text = raw_metadata.get("X-TIKA:content", "<No text content found>").strip()
        ...
    else:
        log.error(f"Error calling Tika: {r.status_code} {r.reason} - {r.text}")
        raise Exception(f"Error calling Tika: {r.status_code} {r.reason} - {r.text}")
```

`Loader` 클래스의 tika 분기 최종 코드 (`mime_type` 전달 없음에 주의):

```python
elif self.engine == "tika" and self.kwargs.get("TIKA_SERVER_URL"):
    if self._is_text_file(file_ext, file_content_type):
        log.debug("Falling back to TextLoader for text file (Tika configured)")
        loader = TextLoader(file_path, autodetect_encoding=True)
    else:
        loader = TikaLoader(
            url=self.kwargs.get("TIKA_SERVER_URL"),
            file_path=file_path,
            extract_images=self.kwargs.get("PDF_EXTRACT_IMAGES"),
        )
```

**중간에 시도됐다가 롤백된 내용 (참고용, 최종 코드에는 없음)** — 커밋 `a8841c5a5`:

```python
endpoint += "rmeta/text"
...
raw_metadata = r.json()
# rmeta/text returns an array, take the first element
if isinstance(raw_metadata, list) and len(raw_metadata) > 0:
    raw_metadata = raw_metadata[0]
...
loader = TikaLoader(
    url=self.kwargs.get("TIKA_SERVER_URL"),
    file_path=file_path,
    mime_type=file_content_type,      # 이후 1a4b2492f 에서 제거됨
    extract_images=self.kwargs.get("PDF_EXTRACT_IMAGES"),
)
```
롤백 사유는 커밋 메시지에 명시돼 있지 않음(미확인). 참고로 업스트림 0.6.43 의 `TikaLoader.__init__` 은 이미 `mime_type=None` 파라미터를 갖고 있으므로(호출부에서 안 넘길 뿐), rmeta 실험을 되살리려면 호출부에 `mime_type=file_content_type` 만 추가하면 된다.

**재적용 가이드**
1. 최신 업스트림의 `TikaLoader.load()` 를 열어 위 최종 코드 기준으로 로깅/try-except/에러 메시지 3곳만 얹는다. 엔드포인트는 업스트림 기본(`tika/text`)을 유지한다.
2. 최신 버전에서 `TikaLoader` 구조가 바뀌었을 수 있으므로(0.7.x 에서의 변경 여부 미확인) 라인이 아닌 "`requests.put` 호출 지점"과 "`r.ok` 분기" 문맥으로 위치를 찾는다.
3. 마이그레이션(DB) 불필요. 런타임 설정 변경 없음.

**관련 커밋**
- `a8841c5a5` feat: Tika 엔드포인트를 `tika/text`에서 `rmeta/text`로 변경하고, 배열 응답을 처리하며, Tika 로더에 MIME 타입을 전달하도록 수정했습니다. (→ 이후 롤백됨)
- `1a4b2492f` refactor: Dockerfile에서 기본 비루트 사용자 설정 및 권한 강화를 적용하고, Tika 로더의 엔드포인트와 오류 처리를 개선했습니다. (rmeta 원복 + 로깅/에러 처리 최종본)

---

### 2. 파일 업로드 예외 처리 개선 및 에러 메시지 한글화

**목적/배경**
- 업로드 실패 시 사용자에게 영어 원문 에러나 무의미한 `[object Object]` 류 메시지가 노출되는 문제 개선. 특히 허용되지 않은 확장자 업로드 시 구체적 HTTP 400 detail 이 바깥의 포괄 `except Exception` 에 삼켜져 "Error uploading file" 로 뭉개지는 버그 수정.
- 백엔드 서버측 에러 메시지 전반을 한국어로 통일 (사내/한국어 사용자 대상 배포 목적).

**동작 방식**
- 백엔드: `upload_file_handler` 에서 `HTTPException` 은 그대로 재전파(re-raise)하고, 그 외 예외만 포괄 처리. 확장자 불허 시 `ERROR_MESSAGES.FILE_NOT_SUPPORTED`(한글 "지원하지 않는 파일 형식입니다.") 를 detail 로 반환.
- 프론트: `uploadFile()` 이 비-JSON 응답(프록시 HTML 에러 페이지 등)을 받아도 죽지 않고 한글 폴백 메시지를 던짐. 채팅 입력창의 업로드 catch 블록은 에러를 콘솔에 남기고 `$i18n.t(e)` 로 토스트 표시(서버가 이미 한글 detail 을 주므로 대부분 그대로 노출됨).

**변경 파일 및 핵심 내용**

`backend/open_webui/routers/files.py` — `upload_file_handler` 내 두 곳:

```python
# (1) 확장자 불허 detail 교체 (커밋 702db1ef5)
if file_extension not in request.app.state.config.ALLOWED_FILE_EXTENSIONS:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=ERROR_MESSAGES.FILE_NOT_SUPPORTED,   # 기존: ERROR_MESSAGES.DEFAULT(f"File type {file_extension} is not allowed")
    )

# (2) 함수 말미 예외 처리 (커밋 e2a1396a1) — 기존 except Exception 앞에 추가
    except HTTPException:
        raise
    except Exception as e:
        log.exception(e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.DEFAULT("Error uploading file"),
        )
```

`src/lib/apis/files/index.ts` — `uploadFile` 응답 처리:

```typescript
.then(async (res) => {
    if (!res.ok) {
        let errorData;
        try {
            errorData = await res.json();
        } catch {
            // JSON 파싱 실패 시 (HTML 응답 등)
            throw { detail: '서버 오류가 발생했습니다. 관리자에게 문의하세요.' };
        }
        throw errorData;
    }
    return res.json();
})
.catch((err) => {
    error = err.detail || err.message || '파일 업로드 중 오류가 발생했습니다.';
    console.error(err);
    return null;
});
```

`src/lib/components/chat/MessageInput.svelte` — 업로드 catch 블록 (이 파일의 다른 변경들 — `localStorage.token` → `sessionStorage.token` — 은 토큰 저장소 영역 소관이며 본 영역 아님):

```javascript
} catch (e) {
    console.error('File upload error:', e);
    toast.error($i18n.t(e));            // 기존: toast.error(`${e}`);
    files = files.filter((item) => item?.itemId !== tempItemId);
}
```

`backend/open_webui/constants.py` — `MESSAGES` / `WEBHOOK_MESSAGES` / `ERROR_MESSAGES` 전체가 한국어로 교체됨(원문 영어는 각 항목 위 주석으로 보존). 파일 업로드 관련 항목 발췌:

```python
# FILE_NOT_SENT
FILE_NOT_SENT = "파일이 전송되지 않았습니다."
# Unsupported file format.
FILE_NOT_SUPPORTED = "지원하지 않는 파일 형식입니다."
# Uh-oh! This file is already registered. Please choose another file.
FILE_EXISTS = "이미 등록된 파일입니다. 다른 파일을 선택해주세요."
# Oops! The file you're trying to upload is too large. ...
FILE_TOO_LARGE = (
    lambda size="": f"파일이 너무 큽니다. {size} 미만의 파일을 업로드해주세요."
)
DUPLICATE_CONTENT = "중복된 내용이 감지되었습니다. 고유한 내용을 제공해주세요."
FILE_NOT_PROCESSED = "이 파일에서 추출된 내용을 사용할 수 없습니다. 파일이 처리되었는지 확인해주세요."
EMPTY_CONTENT = "내용이 비어있습니다. 텍스트나 데이터를 입력해주세요."
DEFAULT = (
    lambda err="": f'{"문제가 발생했습니다." if err == "" else "[오류: " + str(err) + "]"}'
)
```
(참고: 같은 파일 하단의 `PASSWORD_TOO_SHORT` 등 비밀번호 검증 상수 6종은 커밋 `98d3bdae5` 의 인증 영역 소관이므로 본 문서에서는 다루지 않음.)

`src/lib/i18n/locales/ko-KR/translation.json` — 이 커밋에서 추가/수정된 키 2개 (파일 전체의 나머지 변경은 타 영역):

```json
"Something went wrong :/": "문제가 발생했습니다 :/",
"Something went wrong. Please contact administrator.": "문제가 발생했습니다. 관리자에게 문의하세요.",
```

**재적용 가이드**
1. `constants.py` 는 최신 업스트림에서 메시지 항목이 추가/변경되었을 가능성이 높으므로 diff 를 그대로 붙이지 말고, **최신 파일 기준으로 항목별 번역을 다시 수행**하라. 원문을 주석으로 남기는 컨벤션(위 예시 참고)을 유지하면 이후 업스트림 diff 비교가 쉬워진다.
2. `files.py` 의 `except HTTPException: raise` 는 최신 업스트림에 이미 반영됐는지 먼저 확인하라(0.7.x 반영 여부 미확인). 없으면 포괄 `except Exception` 바로 앞에 추가.
3. `FILE_NOT_SUPPORTED` 교체는 detail 에서 확장자 정보가 사라지는 트레이드오프가 있음(보안 점검 커밋 `702db1ef5` 의 의도로 보이나 사유는 커밋 메시지에 명시 안 됨 — 미확인). 동일 정책 유지 여부를 결정하고 적용.
4. 프론트 `uploadFile` 수정은 다른 업로드 경로(지식베이스 등)가 같은 함수를 쓰는지 최신 코드에서 확인 후 적용. `toast.error($i18n.t(e))` 는 `e` 가 문자열일 때를 전제로 함 — 객체가 오면 i18n 키 조회가 실패할 수 있으므로 최신 버전에선 `e?.detail ?? e` 방어를 고려(현 포크 코드는 위 그대로임).
5. DB 마이그레이션 불필요.

**관련 커밋**
- `702db1ef5` 취약점 점검8 (files.py — FILE_NOT_SUPPORTED 교체)
- `e2a1396a1` 에러 메시지 한글화 및 파일 업로드 예외 처리 개선 (constants.py 전면 한글화, files.py HTTPException re-raise, files API/MessageInput/i18n)

---

### 3. Dockerfile 문서 파싱 의존성 추가 (msoffcrypto-tool, chardet, nltk, pyhwp)

**목적/배경**
- 문서 파싱 호환성 확보 목적(Dockerfile 주석 원문: "Install additional dependencies for documented parsing compatibility"). 패키지 이름으로 미루어 암호화된 MS Office 파일(msoffcrypto-tool), 인코딩 자동 감지(chardet), 문장 토크나이저를 요구하는 파싱 라이브러리 지원(nltk + punkt), HWP 한글 문서(pyhwp) 지원을 위한 것으로 보인다 — 단, 커밋 메시지에 구체적 사유는 없으므로 용도 추정임(미확인).
- nltk 데이터(punkt, punkt_tab)를 **빌드 타임에 미리 다운로드**하여, 오프라인/폐쇄망 런타임 환경에서 최초 파싱 시 다운로드 시도로 실패하는 문제를 방지.

**동작 방식**
- 백엔드 베이스 스테이지에서 requirements 설치 RUN 블록 직후, "Install Ollama if requested" RUN 블록 직전에 별도 RUN 레이어로 추가. 환경변수/설정 키 없음. 빌드 시 자동 포함.

**변경 파일 및 핵심 내용**

`Dockerfile` — 최종 상태:

```dockerfile
# (기존) RUN pip3 install --no-cache-dir uv && ... rm -rf /var/lib/apt/lists/*;  블록 바로 아래

# Install additional dependencies for documented parsing compatibility
RUN pip3 install --no-cache-dir msoffcrypto-tool chardet nltk pyhwp && \
    python3 -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab')"

# Install Ollama if requested
```

변경 이력(3단계로 진화):
1. `a5955a4f0`: `RUN pip3 install --no-cache-dir msoffcrypto-tool chardet nltk pyhwp` 만 추가.
2. `0fa60ef24`: `python3 -m nltk.downloader punkt punkt_tab` 체이닝 추가.
3. `1a4b2492f`: 다운로더 호출 방식을 `python3 -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab')"` 로 변경(모듈 실행 방식에서 API 호출 방식으로).

**재적용 가이드**
1. 최신 업스트림 Dockerfile 에서 백엔드 pip 설치 블록(현재는 `uv pip install -r requirements.txt` 계열) 바로 뒤에 위 RUN 블록을 그대로 추가하면 된다. requirements.txt 를 건드리지 않는 독립 레이어라 충돌 위험이 낮다.
2. `nltk.download()` 는 기본적으로 `$HOME/nltk_data` 에 저장된다. 이 포크는 같은 커밋(`1a4b2492f`)에서 `ENV HOME=/home/appusr` + 비루트 기본 사용자(UID/GID 1000)로 바꿨으므로, nltk 데이터 경로와 런타임 사용자 HOME 이 일치한다. **비루트 커스텀 없이 이 블록만 이식할 경우** 데이터가 `/root/nltk_data` 에 설치되므로 런타임 사용자가 읽을 수 있는지 확인 필요(실제 데이터 저장 경로는 빌드해 보지 않아 미확인). 필요하면 `NLTK_DATA` 환경변수로 경로를 고정하는 것도 방법.
3. 최신 Open WebUI 가 이 패키지들 일부를 이미 requirements 에 포함했는지 확인 후 중복 설치를 정리하라(0.7.x 포함 여부 미확인).
4. 같은 Dockerfile 의 나머지 변경(USE_CUDA=true 기본화, NODE_OPTIONS 활성화, UID/GID 1000 비루트 기본화, HOME=/home/appusr, appusr/appgrp 사용자 생성, 권한 강화 대상 `/root`→`$HOME`)은 빌드/보안 강화 영역 소관이므로 본 영역 문서에서는 존재만 언급한다 (관련 커밋: `a5955a4f0`, `0a0f67f4c`, `1a4b2492f`).

**관련 커밋**
- `a5955a4f0` 취약점 점검#3 (파싱 패키지 4종 추가, NODE_OPTIONS 활성화)
- `0fa60ef24` nltk 관련 라이브러리 추가 (punkt/punkt_tab 빌드 타임 다운로드)
- `1a4b2492f` refactor: Dockerfile에서 기본 비루트 사용자 설정 및 권한 강화... (nltk 다운로드 호출 방식 변경)

---

### 부록: 파일별 소유권 정리

| 파일 | 본 영역 해당 범위 |
|---|---|
| `backend/open_webui/retrieval/loaders/main.py` | 전체 (Tika 로더) |
| `backend/open_webui/routers/files.py` | 전체 (변경분 2곳 모두 업로드 처리) |
| `src/lib/apis/files/index.ts` | 전체 (변경분은 uploadFile 에러 처리뿐) |
| `backend/open_webui/constants.py` | 한글화 전반 + 파일 관련 메시지. 단 PASSWORD_* 상수 6종은 인증 영역 |
| `Dockerfile` | 문서 파싱 의존성 RUN 블록만. 비루트/CUDA/권한 강화는 타 영역 |
| `src/lib/components/chat/MessageInput.svelte` | 업로드 catch 블록 1곳만. sessionStorage 전환은 타 영역 |
| `src/lib/i18n/locales/ko-KR/translation.json` | 커밋 e2a1396a1 의 키 2개만. 나머지는 타 영역 |


---

# 파트 6. 프런트엔드 광범위 변경 (토큰 치환 패턴 / 한글화 / 기타 UI)


조사 기준: `git diff a7271532f`(작업트리 포함). src/ 하위 변경 파일은 총 136개(+`static/agreement.md`)이며, 이 중 **119개 .svelte/.ts 파일은 단 하나의 기계적 패턴(토큰 저장소 치환)만 포함**하고, 나머지 16개 파일 + `translation.json` + `static/agreement.md`에 기능적 변경이 있다. 참고: 과제 힌트에 있던 "Modal prop 추가가 모든 사용처에 전파" 가설은 사실이 아님 — Modal의 `dismissible` prop은 기본값 `true`라 기존 사용처는 전혀 수정되지 않았고, 대량 변경의 실제 원인은 아래 1번 패턴이다.

### 1. [전역 패턴] 인증 토큰 저장소 localStorage → sessionStorage 전환

**목적/배경**: 보안 취약점 점검("취약점 점검#5" 등)의 일환. JWT를 `localStorage`에 영구 보관하지 않고 `sessionStorage`로 옮겨 탭/브라우저 종료 시 토큰이 소멸되도록 함(세션 지속성 축소).

**동작 방식**:
- 로그인 성공 시 `src/routes/auth/+page.svelte`에서 `sessionStorage.token = sessionUser.token` 으로 저장 (기존 `localStorage.token = ...`).
- 이후 모든 API 호출부의 첫 인자 `localStorage.token`이 `sessionStorage.token`으로 치환됨.
- 로그아웃/세션 무효 시에는 방어적으로 `localStorage.removeItem('token')`과 `sessionStorage.removeItem('token')`을 **둘 다** 호출 (과거 localStorage에 남은 토큰 정리 목적).
- 토큰 이외의 localStorage 키(`redirectPath`, `agreedToTerms`, `locale` 등)는 그대로 localStorage 사용.

**변경 파일 및 핵심 내용**:
- 대상: src/ 하위 .svelte/.ts 변경 135개 중 119개 파일은 diff 전체가 이 치환뿐이다 (Chat.svelte 64라인, Sidebar.svelte 38라인, workspace/*, admin/*, channel/*, notes/*, playground/*, layout/* 등 — 전부 기능 변경 없음). `grep -rn "localStorage.token" src/` 결과 0건으로 치환 완료 확인.
- 대표 diff (`src/lib/components/layout/Sidebar/ChatItem.svelte`):
```diff
-			chat = await getChatById(localStorage.token, id);
+			chat = await getChatById(sessionStorage.token, id);
```
- 소켓 인증 (`src/routes/+layout.svelte`):
```diff
-			auth: { token: localStorage.token }
+			auth: { token: sessionStorage.token }
...
-			if (localStorage.getItem('token')) {
-				_socket.emit('user-join', { auth: { token: localStorage.token } });
+			if (sessionStorage.getItem('token')) {
+				_socket.emit('user-join', { auth: { token: sessionStorage.token } });
```
- 로그아웃 계열 (`src/lib/components/layout/Sidebar/UserMenu.svelte`, `src/lib/components/layout/Overlay/AccountPending.svelte`):
```diff
 					localStorage.removeItem('token');
+					sessionStorage.removeItem('token');
```
- `src/lib/components/chat/Settings/Account.svelte`의 "JWT Token 보기/복사" UI도 `sessionStorage.token` 참조로 변경.
- `src/lib/apis/index.ts`는 이 치환 1건만 포함 (`auth_type === 'session'`일 때 `toolServerToken = sessionStorage.token`).

**전파 규칙(재적용 시)**: "src/ 전체에서 `localStorage.token` → `sessionStorage.token`, `localStorage.getItem('token')` → `sessionStorage.getItem('token')`(user-join 분기 및 경고 문구 포함) 일괄 치환. 단 `removeItem('token')` 위치에서는 두 storage 모두 제거하도록 sessionStorage 제거 라인을 추가." — 이 규칙 하나로 119개 파일이 전부 설명된다.

**재적용 가이드**:
1. 업스트림 최신 버전에서 `grep -rn "localStorage.token" src/`로 대상 나열 후 일괄 치환 (신규 버전에는 사용처가 추가/이동되었을 수 있으므로 파일 목록을 고정하지 말 것).
2. 치환 후 잔여 0건 확인. `localStorage`의 비토큰 키는 건드리지 말 것.
3. 아래 4번(세션 타임아웃)과 세트로 적용해야 함 — sessionStorage 전환만 하면 탭 간 세션 공유가 끊기는 부작용이 있으니 운영 정책 확인 필요(본 포크는 의도된 동작).

**관련 커밋**: 453924007 "취약점 점검#5" (대량 치환), 4be37956d "취약점 점검#7" (로그아웃 시 양쪽 storage 제거 보강)

### 2. 공통 Modal 컴포넌트에 dismissible prop 추가

**목적/배경**: 사용자 동의 모달(3번)을 ESC 키나 배경 클릭으로 닫을 수 없게 하기 위한 공통 인프라.

**동작 방식**: `Modal.svelte`에 `export let dismissible = true;` prop 추가. `dismissible={false}`이면 ESC와 배경 mousedown으로 닫히지 않음. 기본값이 `true`이므로 기존 모든 Modal 사용처는 무수정.

**변경 파일 및 핵심 내용** (`src/lib/components/common/Modal.svelte`):
```diff
 	export let className = 'bg-white/95 dark:bg-gray-900/95 backdrop-blur-sm rounded-4xl';
+	export let dismissible = true;
...
-		if (event.key === 'Escape' && isTopModal()) {
+		if (event.key === 'Escape' && isTopModal() && dismissible) {
...
 		on:mousedown={() => {
-			show = false;
+			if (dismissible) {
+				show = false;
+			}
 		}}
```
`dismissible={false}` 사용처는 현재 `AgreementModal.svelte` 단 1곳 (grep으로 확인).

**재적용 가이드**: 업스트림 Modal.svelte에 동일 prop을 추가. 업스트림 최신 버전에 이미 유사 기능(`preventClose` 등)이 추가되었는지 먼저 확인할 것 — 미확인.

**관련 커밋**: fa6d77876 "fix(agreement): 동의 없는 모달 닫기 방지 및 버튼 한글화"

### 3. 사용자 동의(고지사항) 모달 — AgreementModal

**목적/배경**: 사내(원내) 중요정보 보호 고지사항에 대한 사용자 동의를 최초 접속 시 강제. 기존 ChangelogModal 자리를 대체.

**동작 방식**:
- 앱 레이아웃 마운트 시 `localStorage.getItem('agreedToTerms')`가 없으면 모달 표시.
- 모달 내용은 정적 파일 `static/agreement.md`를 fetch → `marked.parse` → `DOMPurify.sanitize`로 렌더.
- "동의하기" 클릭 시 `localStorage.setItem('agreedToTerms', 'true')` 후 닫힘. `dismissible={false}`라 동의 없이는 닫을 수 없음.
- ChangelogModal은 import/렌더 모두 주석 처리로 비활성화(파일 자체는 유지, 해당 파일 diff는 토큰 치환뿐).

**변경 파일 및 핵심 내용**:
- `src/lib/components/AgreementModal.svelte` (신규, 62라인): 핵심 부분:
```svelte
<Modal bind:show size="xl" dismissible={false}>
...
	const handleAgree = () => {
		localStorage.setItem('agreedToTerms', 'true');
		show = false;
	};
```
- `static/agreement.md` (신규): "원내 중요정보 보호 및 정보주체 권리 보장을 위한 고지사항" — 업로드 금지 자료, 이용 금지 행위, "대화 내용은 책임추적성 확보를 위해 자동 저장되며 1년 간 보관 후 자동 파기" 문구 포함.
- `src/routes/(app)/+layout.svelte`:
```diff
-	import ChangelogModal from '$lib/components/ChangelogModal.svelte';
+	// import ChangelogModal from '$lib/components/ChangelogModal.svelte';
+	import AgreementModal from '$lib/components/AgreementModal.svelte';
...
-		if ($user?.role === 'admin' && ($settings?.showChangelog ?? true)) {
-			showChangelog.set($settings?.version !== $config.version);
-		}
...(onMount 끝부분)
+		if (!localStorage.getItem('agreedToTerms')) {
+			showAgreement = true;
+		}
...
-<ChangelogModal bind:show={$showChangelog} />
+<!-- <ChangelogModal bind:show={$showChangelog} /> -->
+<AgreementModal bind:show={showAgreement} />
```

**재적용 가이드**: 2번(dismissible) 선행 필요. 동의 플래그가 클라이언트 localStorage에만 저장되므로 브라우저/기기 변경 시 재동의 요구됨(의도 여부 미확인). 서버측 동의 기록은 없음. 백엔드의 대화 자동 삭제(1년 보관)는 별도 영역(backend cleanup/스크립트) 참조.

**관련 커밋**: 7948a63ae "사용자 동의 모달 추가 및 대화 자동 삭제 기능 추가", fa6d77876 "동의 없는 모달 닫기 방지 및 버튼 한글화", 2b4840c31 (agreement.md 고지사항 문구 수정)

### 4. 세션 타임아웃 UI: 남은시간 표시, 만료 경고 모달, 세션 연장(refresh), 전역 401 처리

**목적/배경**: JWT 만료 기반 강제 로그아웃 정책(취약점 점검)의 프런트엔드 구현. 사용자는 만료 전 경고를 받고 세션을 연장할 수 있으며, 만료·401 시 확실히 로그아웃된다.

**동작 방식**:
- 백엔드 `/api/v1/auths/refresh` (POST, Bearer 토큰)가 새 토큰과 `expires_at`, `server_timestamp`를 반환한다고 가정 (백엔드 구현은 `backend/open_webui/routers/auths.py` — 별도 영역 문서 참조).
- `$user.expires_at`(unix ts)과 서버-클라이언트 clock skew를 보정해 1초 간격 타이머로 남은 시간을 계산.
- 화면 우상단 고정 pill에 `로그아웃 N분 N초 남음` 표시(만료 1분 미만이면 빨간색+pulse), 옆의 새로고침 버튼으로 수동 연장(성공/실패와 무관하게 10초 쿨다운).
- 남은 시간이 임계값(토큰 수명 >60초면 60초, 아니면 10초) 이하이고 탭이 visible이면 `SessionTimeoutModal` 표시 → "연장하기"(refresh) 또는 "로그아웃".
- (작업트리 미커밋 변경) 슬라이딩 세션: mousemove/keydown/click/touchstart/scroll(capture)로 활동 감지, 최근 60초 내 활동 + 탭 visible + 남은시간이 `max(수명/2, 경고임계+20초)` 이하이면 자동 refresh (동시 실행 방지 + 실패 시 10초 재시도 스로틀).
- 남은 시간 0 이하 → `logoutHandler()`: `userSignOut()` 호출 후 양쪽 storage 토큰 제거, `window.location.href`로 강제 이동.
- 토큰 수명은 `$config?.features?.jwt_expires_in`(초 단위 문자열, `backend/open_webui/main.py`가 `JWT_EXPIRES_IN` parse 결과를 내려줌)으로 초기화. 주의: 이 코드는 `onMount` 내부에 `$:` 라벨로 작성되어 있어 Svelte 반응성이 아니라 1회 실행되는 라벨문이다(동작상 마운트 시 1회 설정).
- 전역 fetch 인터셉터(`src/routes/+layout.svelte` onMount): 모든 응답 중 Authorization 헤더가 있던 요청이 401이면 양쪽 storage 토큰 제거 후 `/auth`로 강제 리다이렉트, 더미 401 Response 반환.
- `TOKEN_EXPIRY_BUFFER`를 60 → 0으로 변경(만료 60초 전 선제 로그아웃하던 기존 로직 제거 — 경고 모달이 대체).
- `getUserSettings`는 `['user','admin']` role일 때만 호출하고 실패를 catch하도록 변경. 세션 무효 시 `goto` 대신 `window.location.href = '/auth?redirect=...'`로 하드 리다이렉트.

**변경 파일 및 핵심 내용**:
- `src/lib/components/layout/Overlay/SessionTimeoutModal.svelte` (신규, 45라인): `show`, `countdown` prop; `extend`/`logout` 이벤트 dispatch; 문구는 한국어 하드코딩("세션 만료 경고", "보안을 위해 {countdown}초 후 자동 로그아웃됩니다.", 버튼 "로그아웃"/"연장하기").
- `src/lib/apis/auths/index.ts`: `refreshSession(token)` 신규 —
```ts
export const refreshSession = async (token: string) => {
	...
	const res = await fetch(`${WEBUI_API_BASE_URL}/auths/refresh`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
		credentials: 'include'
	})...
```
- `src/routes/(app)/+layout.svelte` (+259라인, 이 중 슬라이딩 세션 부분은 **미커밋 작업트리 변경**): 위 동작 대부분이 이 파일에 구현. 핵심 조각:
```ts
const refreshSessionHelper = async () => {
	if (sessionStorage.token) {
		const res = await refreshSession(sessionStorage.token);
		if (res && res.token) {
			sessionStorage.token = res.token;
			if (res.expires_at) { user.update((u) => ({ ...u, expires_at: res.expires_at })); ... }
			if (res.server_timestamp) { calculateClockSkew(res.server_timestamp); }
			showTimeoutModal = false;
		}
	} // 401이면 storage 정리 후 /auth 이동
};
```
```svelte
<SessionTimeoutModal bind:show={showTimeoutModal} countdown={modalCountdown}
	on:extend={async () => { await refreshSessionHelper(); }} on:logout={logoutHandler} />
```
- `src/routes/+layout.svelte`: 전역 401 인터셉터 + `TOKEN_EXPIRY_BUFFER = 0`:
```ts
const originalFetch = window.fetch;
window.fetch = async (...args) => {
	const response = await originalFetch(...args);
	if (response.status === 401) {
		const hasAuthHeader = (options?.headers && (options.headers['Authorization'] || ...));
		if (hasAuthHeader) {
			if (localStorage.getItem('token')) localStorage.removeItem('token');
			if (sessionStorage.getItem('token')) sessionStorage.removeItem('token');
			if (window.location.pathname !== '/auth') { window.location.href = '/auth'; }
			return new Response(null, { status: 401 });
		}
	}
	return response;
};
```

**재적용 가이드**:
1. 백엔드 `/auths/refresh` 엔드포인트(+ `expires_at`/`server_timestamp` 응답, JWT jti 관련 마이그레이션 `a1b2c3d4e5f6_add_token_jti_to_auth.py`)가 선행되어야 함 — 백엔드 영역 문서 참조.
2. `main.py`의 `/api/config` features에 `jwt_expires_in` 노출이 필요.
3. 슬라이딩 세션(자동 연장) 부분은 아직 커밋되지 않은 작업트리 상태이므로 이식 시 포함 여부를 명시적으로 결정할 것.
4. UI 문구(남은시간 pill, SessionTimeoutModal)가 i18n 없이 한국어 하드코딩임 — 다국어 필요 시 i18n 키로 전환 권장.
5. 업스트림 최신 버전은 `TOKEN_EXPIRY_BUFFER`/onMount 구조가 변했을 수 있으므로 diff를 라인이 아닌 함수 단위로 이식.

**관련 커밋**: 2c8c04c2c "취약점 점검#1" (refresh API/타이머 최초 도입), 6123e56c5 "취약점 점검#2", 4be37956d "취약점 점검#7" (SessionTimeoutModal 신규, 401 인터셉터, 하드 리다이렉트), 98d3bdae5·702db1ef5 (+layout 후속 수정), 미커밋 작업트리 (슬라이딩 자동 연장, touchstart/scroll capture 리스너)

### 5. 서버 설정 기반 기능 토글 (이미지 캡처 / 웹페이지 첨부 / 개인정보 입력 / 관리자 페이지)

**목적/배경**: 보안·운영 정책상 특정 기능을 서버 환경변수로 끌 수 있게 함. 백엔드는 `/api/config`의 `features`로 플래그를 노출하고, 프런트는 `$config?.features?.*`로 조건부 렌더.

**동작 방식** (환경변수 → config 키 → UI):
- `ENABLE_IMAGE_CAPTURE` (PersistentConfig `ui.enable_image_capture`, 기본 true) → `features.enable_image_capture` → 채팅 입력 "+" 메뉴의 "Capture"(화면/카메라 캡처) 항목 표시 여부.
- `ENABLE_WEBPAGE_ATTACHMENT` (PersistentConfig `ui.enable_webpage_attachment`, 기본 true) → `features.enable_webpage_attachment` → 채팅 입력 메뉴 "Attach Webpage" 및 지식베이스 "Add webpage" 항목 표시 여부. docker-compose.yaml에서 `false`로 운영.
- `ENABLE_USER_PERSONAL_INFO` (PersistentConfig `ui.enable_user_personal_info`, 기본 true) → `features.enable_user_personal_info` → 설정>계정의 성별(Gender)/생년월일(Birth Date) 입력 UI 표시 여부. docker-compose에서 `false`.
- `DISABLE_ADMIN` (env.py, 기본 false) → `features.disable_admin` → true면 admin이어도 `/admin` 레이아웃 진입 시 `/`로 리다이렉트.

**변경 파일 및 핵심 내용**:
- `src/lib/components/chat/MessageInput/InputMenu.svelte`: 기존 Capture/Attach Webpage 블록을 각각 다음으로 감쌈(내용 무변경, 들여쓰기만 증가):
```svelte
{#if $config?.features?.enable_image_capture ?? true}
	...Capture DropdownMenu.Item...
{/if}
{#if $config?.features?.enable_webpage_attachment ?? true}
	...Attach Webpage DropdownMenu.Item...
{/if}
```
- `src/lib/components/workspace/Knowledge/KnowledgeBase/AddContentMenu.svelte` (**미커밋 작업트리 변경**): `import { config } from '$lib/stores';` 추가 후 "Add webpage" 항목을 `{#if $config?.features?.enable_webpage_attachment ?? true}`로 감쌈.
- `src/lib/components/chat/Settings/Account.svelte`: Gender/Birth Date 블록 전체를 `{#if $config?.features?.enable_user_personal_info ?? true}`로 감쌈. (참고: 저장 시 `updateUserProfile` 호출 자체는 여전히 gender/date_of_birth를 전송 — UI만 숨김.)
- `src/routes/(app)/admin/+layout.svelte`:
```diff
-		if ($user?.role !== 'admin') {
+		if ($user?.role !== 'admin' || $config?.features?.disable_admin) {
 			await goto('/');
 		}
```

**재적용 가이드**: 백엔드 측 config.py/env.py/main.py 변경(별도 영역 문서)과 세트로 적용. 프런트는 `?? true` 기본값 덕에 백엔드가 플래그를 안 내려줘도 기존 동작 유지되므로 프런트를 먼저 이식해도 무해. AddContentMenu 변경은 미커밋 상태임을 유의. `disable_admin`은 클라이언트 리다이렉트일 뿐이므로 서버측 차단은 별도 확인 필요(미확인).

**관련 커밋**: 8497673dc "이미지 캡처 및 웹페이지 첨부 기능에 대한 구성 옵션 추가", 0cb6d2410 "사용자 개인 정보 설정 활성화 여부에 따라 계정 UI 조건부 표시", 1da45db0e "취약점 점검#6" (disable_admin), 0f6d3c4aa (docker-compose에서 webpage 첨부 off), AddContentMenu는 커밋 이력 없음(작업트리)

### 6. 에러 메시지 일반화·한글화

**목적/배경**: 서버 원본 에러(스택/내부 정보 포함 가능)를 사용자에게 그대로 노출하지 않고(정보 노출 취약점 대응), 일반화된 한국어 안내 문구로 대체. 원본 에러는 console로만 기록.

**변경 파일 및 핵심 내용**:
- `src/lib/components/chat/Messages/Error.svelte`: content의 타입별 상세 출력 로직(문자열/`error.message`/`detail`/`message`/JSON.stringify) 전체를 제거하고 고정 문구로 대체 + 콘솔 로깅 추가:
```svelte
$: { if (content) { console.error('Chat Error:', content); } }
...
<div class=" self-center text-sm">
	{$i18n.t('An error occurred. Please contact the administrator.')}
</div>
```
  주의: 키 `An error occurred. Please contact the administrator.`는 ko-KR translation.json에 **추가되지 않았음**(grep 확인) — 현재 영어 원문이 그대로 표시됨. 이식 시 번역 추가 권장.
- `src/lib/apis/files/index.ts` `uploadFile`: 비-JSON 에러 응답(HTML 등) 대비 + 기본 한국어 메시지:
```ts
if (!res.ok) {
	let errorData;
	try { errorData = await res.json(); }
	catch { throw { detail: '서버 오류가 발생했습니다. 관리자에게 문의하세요.' }; }
	throw errorData;
}
...
error = err.detail || err.message || '파일 업로드 중 오류가 발생했습니다.';
```
- `src/lib/components/chat/MessageInput.svelte` 업로드 catch:
```diff
-				toast.error(`${e}`);
+				console.error('File upload error:', e);
+				toast.error($i18n.t(e));
```
  (참고: `e`가 객체일 경우 `$i18n.t(e)` 인자 타입이 문자열이 아님 — 동작은 미확인, 이식 시 문자열 보장 권장.)
- `src/lib/components/chat/Settings/Account.svelte`: 프로필 저장/세션 조회 실패 시 `toast.error($i18n.t('Something went wrong. Please contact administrator.'))`로 교체.
- `src/lib/i18n/locales/ko-KR/translation.json` (변경 2건 + 파일 끝 개행 제거):
```diff
-	"Something went wrong :/": "무언가 잘못 되었습니다 :/",
+	"Something went wrong :/": "문제가 발생했습니다 :/",
+	"Something went wrong. Please contact administrator.": "문제가 발생했습니다. 관리자에게 문의하세요.",
```

**재적용 가이드**: Error.svelte는 업스트림에서 자주 바뀌는 파일이므로 "본문 렌더를 고정 i18n 문구로 대체" 규칙으로 이식. 최신 버전 en-US translation.json에 두 키를 추가하고 ko-KR 번역을 넣을 것(현 포크는 en-US 미수정, `An error occurred...` ko-KR 번역 누락 상태).

**관련 커밋**: e2a1396a1 "에러 메시지 한글화 및 파일 업로드 예외 처리 개선", 2c8c04c2c "취약점 점검#1" (Error.svelte 최초 변경), 702db1ef5 "취약점 점검8" (Account.svelte 문구)

### 7. 기타 개별 소규모 변경

- `src/routes/auth/+page.svelte`: 토큰 저장 위치 변경(1번 패턴) 외에, 마운트 시 리다이렉트 조건을 `if ($user !== undefined)` → `if ($user)`로 변경 — user가 `null`(비로그인)일 때 auth 페이지에 머물도록 엄격화.
- `src/lib/components/layout/Overlay/AccountPending.svelte`, `src/lib/components/layout/Sidebar/UserMenu.svelte`: Sign Out 시 `sessionStorage.removeItem('token')` 추가(1번 패턴의 보강 규칙).
- `src/routes/(app)/+layout.svelte`: 관리자 대상 ChangelogModal 자동 표시 로직 삭제(3번 참조), 우상단 세션 남은시간 pill UI 추가(4번 참조).
- `src/lib/components/layout/Sidebar.svelte`, `src/lib/components/chat/Chat.svelte`: **기능 변경 없음** — 각각 38/64라인 전부 토큰 치환(1번 패턴)으로 확인됨.
- `migration_guide_0.6.43_fix1_to_0.7.2_fix1.md`: fix1 시점의 이식 가이드 문서(참고용). 이 문서 작성 시 diff로 직접 재검증했으며, fix1 이후 변경(슬라이딩 세션 자동연장, AddContentMenu 토글, agreement.md 문구 수정 등)은 해당 가이드에 없음.

### 재적용 전체 순서 요약

1. 백엔드(별도 영역): `/auths/refresh` + jti 마이그레이션 + config features(`jwt_expires_in`, `enable_image_capture`, `enable_webpage_attachment`, `enable_user_personal_info`, `disable_admin`) 노출.
2. 1번 토큰 저장소 일괄 치환(+로그아웃 보강) → 빌드/grep 검증.
3. 2번 Modal `dismissible` → 3번 AgreementModal + `static/agreement.md`.
4. 4번 세션 타임아웃 세트(`refreshSession` API, SessionTimeoutModal, (app)/+layout 타이머, 루트 +layout 401 인터셉터·`TOKEN_EXPIRY_BUFFER=0`). 슬라이딩 자동연장(미커밋분) 포함 여부 결정.
5. 5번 기능 토글 4종(프런트는 독립 적용 가능).
6. 6번 에러 문구 교체 + ko-KR/en-US 번역 키 정비.


---

# 파트 7. 운영 스크립트 및 배포 구성


기준: 업스트림 포크 지점 `a7271532f` ("0.6.43") 대비 브랜치 `0.6.43-fix2.1`의 실제 diff 검증 결과. 이 영역 파일들에는 커밋되지 않은 작업트리 변경이 없음(작업트리 변경 2건은 모두 Svelte 파일로 타 영역 소속).

### 1. PostgreSQL 채팅 정리 스크립트 (scripts/cleanup_chats.sh) — 신규 추가

**목적/배경**
- 보안 정책상 대화 내역을 일정 기간 이후 DB에서 물리 삭제하기 위한 운영용 스크립트. 앱 내 자동 삭제 기능(`CHAT_DELETE_ENABLED`, 타 영역)과 별개로, DBA/운영자가 수동 또는 cron으로 일괄 정리할 때 사용.
- postgres 컨테이너 내부에서 `psql`로 직접 실행하는 방식을 전제로 설계됨(커밋 175d21682에서 `DATABASE_URL` 방식에서 전환).

**동작 방식**
- POSIX sh(`#!/bin/sh`) 스크립트, `set -e`.
- DB 접속: `APP_USER` / `APP_PASSWORD` / `APP_DB` 환경변수 또는 `--app-user` / `--app-password` / `--app-db` 옵션. 접속 URL은 하드코딩된 호스트/포트를 사용:
  ```sh
  DB_URL="postgresql://${APP_USER}:${APP_PASSWORD}@localhost:5432/${APP_DB}"
  run_sql() { psql "$DB_URL" -t -A -c "$1"; }
  ```
- 옵션:
  - `--days <N>` (필수): N일보다 오래된 채팅 삭제. cutoff는 셸 산술로 계산: `CUTOFF_EPOCH=$(( $(date +%s) - DAYS * 86400 ))` (chat 테이블의 `created_at`/`updated_at`이 epoch 정수라는 전제).
  - `--email <이메일>` / `--user-id <ID>`: 특정 사용자만 대상. 이메일 지정 시 `"user"` 테이블에서 id 조회(작은따옴표는 `sed "s/'/''/g"`로 이스케이프).
  - `--by <created_at|updated_at>`: 기준 컬럼 선택(기본 `created_at`, 두 값 외에는 에러).
  - `--execute`: 미지정 시 dry-run(미리보기만). 지정 시 실제 DELETE.
  - `-y`/`--yes`: `yes` 입력 확인 프롬프트 생략(cron용).
- 인자 검증(커밋 889997ef9): 값이 필요한 옵션에 값 누락 또는 다음 인자가 `--`로 시작하면 에러 후 usage 출력하는 `require_arg` 헬퍼. 인자 0개면 usage.
  ```sh
  require_arg() {
      if [ $# -lt 2 ] || echo "$2" | grep -q '^--'; then
          echo "[ERROR] '$1' 옵션에는 값이 필요합니다."
          usage
      fi
  }
  ```
- 삭제 로그(커밋 889997ef9 + 4a28f2eb5): 스크립트와 동일 디렉토리에 실행 시각 타임스탬프 파일명으로 로그 생성. 콘솔+파일 동시 출력 `log()` 헬퍼(tee) 사용. `--execute` 시 삭제 대상 전체 목록(id, user_id, title, created, updated)을 로그 파일에만 기록.
  ```sh
  SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
  LOG_FILE="${SCRIPT_DIR}/cleanup_chats_$(date '+%Y%m%d_%H%M%S').log"
  ```
- 삭제 순서: (1) 공유 채팅 삭제 — 원본 chat id 앞에 `shared-` 접두어가 붙은 행을 서브쿼리로 삭제, (2) 본 채팅 삭제. 모든 조회/삭제 쿼리에 `user_id NOT LIKE 'shared-%%'` 필터로 공유 사본이 "본 채팅"으로 집계되지 않게 함(SQL LIKE에서 `'shared-%%'`는 `'shared-%'`와 동일하게 매칭됨).
  ```sql
  DELETE FROM chat
  WHERE user_id IN (
      SELECT 'shared-' || c.id FROM chat c
      WHERE c.${DATE_COL} < ${CUTOFF_EPOCH}
        AND c.user_id NOT LIKE 'shared-%%' ${USER_FILTER}
  );
  ```
- 삭제 후 잔여 건수 확인 및 요약 로그 출력.
- 알려진 사소한 quirk: `SHARED_DELETED` / `MAIN_DELETED` 변수에 psql 결과를 담지만 실제 리포트에는 사용하지 않음(shared 삭제 쿼리 뒤에 붙은 `SELECT COUNT(*);`는 삭제 건수를 반환하지 않음). 재구현 시 그대로 두거나 정리해도 무방.

**변경 파일 및 핵심 내용**
- `scripts/cleanup_chats.sh` (신규, 259라인). 위 코드 조각 참고.

**재적용 가이드**
- 애플리케이션 코드와 독립적인 순수 셸 스크립트이므로 최신 버전에 그대로 복사 가능. 단, 최신 Open WebUI에서 chat 테이블 스키마(`created_at`/`updated_at`이 epoch 정수, 공유 채팅의 `user_id = 'shared-<chat_id>'` 규약)가 유지되는지 확인 필요.
- PostgreSQL 전용(`to_timestamp`, `generate_series` 등). SQLite 환경에서는 동작하지 않음.
- `localhost:5432` 하드코딩 — postgres 컨테이너 내부 실행 전제. 다른 배포 형태면 DB_URL 수정 필요.

**관련 커밋**
- `9742cdbdf` Add PostgreSQL chat cleanup script
- `175d21682` fix: 채팅 정리 스크립트의 DB 접속을 DATABASE_URL 대신 APP_USER/APP_PASSWORD/APP_DB 환경변수로 변경
- `889997ef9` fix: 채팅 정리 스크립트의 인자 검증 추가 및 삭제 로그 기록 기능 추가
- `4a28f2eb5` Update cleanup_chats.sh (로그 파일명을 고정 `cleanup_chats.log`에서 타임스탬프 포함 파일명으로 변경)

### 2. 일별 접속 사용자 수(DAU) 리포트 스크립트 (scripts/daily_active_users.sh) — 신규 추가

**목적/배경**
- 운영 지표 보고용. 최근 N일(기본 7일)간 일별 활동 사용자 수를 chat 테이블 기반으로 집계.

**동작 방식**
- DB 접속 방식/인자 검증(`require_arg`)/`run_sql` 헬퍼는 cleanup_chats.sh와 동일 패턴 (`APP_USER`/`APP_PASSWORD`/`APP_DB`, `postgresql://...@localhost:5432/...`).
- 옵션: `--days <N>`(기본 7), `--app-user`, `--app-password`, `--app-db`, `-h`.
- "활동 사용자" 정의: chat 테이블에서 `to_timestamp(created_at)::date` 또는 `to_timestamp(updated_at)::date`가 해당 날짜인 고유 `user_id` (두 기준의 UNION, `user_id NOT LIKE 'shared-%%'` 제외). 로그인 기록이 아니라 **채팅 생성/수정 활동** 기준임에 유의.
- 출력 구성:
  1. 헤더: 조회 시각, 조회 기간, 전체 등록 사용자 수(`SELECT COUNT(*) FROM "user"`).
  2. 일별 DAU 표(주말 포함): `generate_series`로 날짜 범위 생성 후 LEFT JOIN, 요일 컬럼은 `EXTRACT(DOW ...)`을 CASE로 한글 요일(일~토) 변환 (커밋 380983eb0에서 추가).
  3. 평균 DAU(평일만): 날짜 범위에서 `EXTRACT(DOW FROM day) NOT IN (0, 6)`으로 토/일 제외 후 `ROUND(AVG(dau), 1)` (커밋 380983eb0에서 주말 제외로 변경).
  4. 오늘 접속한 사용자 목록: 오늘 chat 활동이 있는 사용자의 이름/이메일/`last_active_at`(user 테이블) 출력.
- 날짜 범위 시작점은 셸 산술 `$(( DAYS - 1 ))`을 SQL에 삽입: `CURRENT_DATE - INTERVAL '1 day' * (DAYS-1)`.

**변경 파일 및 핵심 내용**
- `scripts/daily_active_users.sh` (신규, 222라인). 평균 DAU 핵심 SQL:
  ```sql
  weekdays AS (
      SELECT day FROM date_range
      WHERE EXTRACT(DOW FROM day) NOT IN (0, 6)
  ), ...
  SELECT ROUND(AVG(dau), 1) FROM daily_counts;
  ```

**재적용 가이드**
- 애플리케이션 독립 스크립트로 그대로 복사 가능. PostgreSQL 전용.
- 최신 버전에서 chat 테이블의 epoch 정수 타임스탬프와 `user` 테이블의 `last_active_at` 컬럼 존재 여부만 확인.

**관련 커밋**
- `d816ed099` feat: 최근 7일간 일별 접속 사용자 수(DAU) 조회 스크립트 추가
- `380983eb0` fix: DAU 리포트에 요일 표시 추가 및 평균 DAU에서 주말 제외

### 3. 대화 감사 추적 리포트 스크립트 (scripts/chat_audit_report.sh) — 신규 추가

**목적/배경**
- 보안 감사 증빙용: "누가, 언제, 어떤 대화를 했는지"와 대화 본문 샘플을 DB에서 직접 조회해 리포트로 출력. chat 컬럼(JSON)에 전체 대화(role, content)가 보존되어 감사 추적이 가능함을 증빙하는 용도(리포트 하단 고지 문구 포함).

**동작 방식**
- DB 접속/인자 검증 패턴은 위 두 스크립트와 동일 (`APP_USER`/`APP_PASSWORD`/`APP_DB`, `localhost:5432`).
- 옵션: `--days <N>`(기본 7), `--detail <N>`(대화 본문 샘플 표시 건수, 기본 0=미표시), `--limit <N>`(목록 최대 건수, 기본 20), `--email <이메일>`(특정 사용자 필터 — `u.email = '...'` 조건으로 추가되며 cleanup 스크립트와 달리 따옴표 이스케이프 없음), DB 접속 옵션들.
- 출력 구성:
  1. 헤더: 기간 내 대화 수, 대화 사용자 수 통계.
  2. 대화 목록: 사용자명/이메일/제목(개행 제거, 40자 절단)/생성일시/최종수정일시, `updated_at DESC` 정렬.
  3. 일별 대화 건수: `generate_series` + 한글 요일 표시(DAU 스크립트와 동일 패턴).
  4. `--detail N` 지정 시 최근 N건 대화의 본문 샘플: `json_array_elements(chat.chat->'messages')`로 messages 배열을 풀어 `role IN ('user','assistant')`인 메시지를 최대 6건, content는 100자 절단 후 `[사용자]`/`[AI응답]` 라벨로 출력.
  ```sql
  SELECT msg->>'role' AS role,
         LEFT(REPLACE(msg->>'content', E'\n', ' '), 100) AS content
  FROM chat, json_array_elements(chat.chat->'messages') AS msg
  WHERE chat.id = '${chat_id}' AND msg->>'role' IN ('user', 'assistant')
  LIMIT 6;
  ```

**변경 파일 및 핵심 내용**
- `scripts/chat_audit_report.sh` (신규, 255라인).
- 같은 커밋(2b4840c31)에서 `static/agreement.md`와 `migration_guide_...md`의 고지사항 제목에서 "(예시)" 문구 제거 — 해당 파일들은 타 영역 소속이므로 여기서는 언급만 함.

**재적용 가이드**
- 애플리케이션 독립 스크립트로 그대로 복사 가능. PostgreSQL 전용.
- `chat.chat` 컬럼이 JSON 타입이고 `messages` 배열 구조(`role`/`content`)를 유지하는지 최신 버전에서 확인 필요. 컬럼이 JSONB로 바뀌면 `json_array_elements` → `jsonb_array_elements`로 교체.

**관련 커밋**
- `2b4840c31` feat: 대화 감사 추적 리포트 스크립트 추가 및 고지사항 문구 수정

### 4. docker-compose.yaml — 배포 구성 커스텀

**목적/배경**
- 사내 배포 환경에 맞춰 (1) 번들 ollama 서비스 제거, (2) 자체 빌드 이미지 태그 사용, (3) 이 포크의 커스텀 백엔드 기능들을 켜는 환경변수 명시.

**동작 방식 / 최종 상태**
- ollama 서비스, `depends_on: ollama`, `OLLAMA_BASE_URL`, `ollama` 볼륨 전부 삭제 (커밋 98d3bdae5).
- 이미지: `ghcr.io/open-webui/open-webui:${WEBUI_DOCKER_TAG-main}` → `ax/open-webui:0.6.43-fix2.1-AppleSilicon`. 태그 변천: `0.6.43-fix1-MacSilicon`(528e54d48) → `0.6.43-fix2-MacSilicon`(98d3bdae5) → `0.6.43-fix2-AppleSilicon`(0a0f67f4c) → `0.6.43-fix2.1-AppleSilicon`(0f6d3c4aa). 릴리스마다 태그를 수동 갱신하는 운영 관행.
- 최종 environment 블록:
  ```yaml
  environment:
    - 'WEBUI_SECRET_KEY='
    - 'DISABLE_ADMIN=false'
    - 'CHAT_DELETE_ENABLED=true'
    - 'CHAT_DELETE_DAYS=1'
    - 'ENABLE_PASSWORD_VALIDATION=true'
    - 'PASSWORD_BLACKLIST=kftc,admin'
    - 'ENABLE_IMAGE_CAPTURE=true'
    - 'ENABLE_WEBPAGE_ATTACHMENT=false'
    - 'ENABLE_USER_PERSONAL_INFO=false'
  ```
- 각 환경변수의 백엔드 구현은 타 영역(backend/open_webui/env.py, config.py 등) 문서 참조. 이 파일 기준 현재 운영값: 관리자 패널 차단 해제(`DISABLE_ADMIN=false` — 이력상 true/false를 수차례 오간 운영 스위치), 채팅 1일 후 자동 삭제, 비밀번호 검증 활성(블랙리스트 `kftc,admin`), 이미지 캡처 허용, 웹페이지 첨부 비활성(0f6d3c4aa에서 true → false), 사용자 개인정보 UI 비활성.

**재적용 가이드**
- 최신 업스트림 docker-compose.yaml을 베이스로, ollama 제거 + 이미지 태그 교체 + environment 블록 이식. 환경변수 자체는 백엔드 커스텀(타 영역)이 먼저 이식되어야 의미가 있음.
- 이미지 태그의 버전 문자열은 릴리스 시점에 맞춰 갱신 필요.

**관련 커밋**
- `1da45db0e` 취약점 점검#6 (DISABLE_ADMIN 추가)
- `4be37956d` 취약점 점검#7 (DISABLE_ADMIN=false)
- `7948a63ae` 사용자 동의 모달 추가 및 대화 자동 삭제 기능 추가 (CHAT_DELETE_ENABLED/DAYS)
- `b3b8f6476` 변경사항 정리 / `ad66fabcc` "." (DISABLE_ADMIN 토글)
- `528e54d48` 빌드 이미지명 변경
- `98d3bdae5` feat: 비밀번호 유효성 검사... (ollama 제거, ENABLE_PASSWORD_VALIDATION/PASSWORD_BLACKLIST, fix2 태그)
- `0a0f67f4c` feat: USE_CUDA 기본값 true 및 이미지 태그 AppleSilicon으로 변경
- `8497673dc` feat: 이미지 캡처 및 웹페이지 첨부 구성 옵션 추가 (ENABLE_IMAGE_CAPTURE/ENABLE_WEBPAGE_ATTACHMENT)
- `0cb6d2410` feat: 사용자 개인 정보 설정... (ENABLE_USER_PERSONAL_INFO)
- `0f6d3c4aa` fix: docker-compose 이미지 버전 업데이트 및 웹페이지 첨부 비활성화

### 5. Dockerfile — 빌드/이미지 커스텀

**목적/배경**
- (a) 빌드 환경 기본값 변경(CUDA, Node 힙), (b) 문서 파싱 호환성 패키지 추가(암호화 Office 문서, 한글 인코딩, HWP, NLTK 토크나이저), (c) 보안 점검 대응으로 기본 비루트 사용자 실행.

**변경 파일 및 핵심 내용** (`Dockerfile`, 4개 항목)

1. **USE_CUDA 기본값 true** (0a0f67f4c):
   ```dockerfile
   ARG USE_CUDA=true   # 업스트림: false
   ```
2. **Node 빌드 힙 제한 해제** (a5955a4f0) — 프론트엔드 빌드 스테이지에서 주석 처리돼 있던 라인 활성화:
   ```dockerfile
   ENV NODE_OPTIONS="--max-old-space-size=4096"
   ```
3. **문서 파싱 의존성 추가** (a5955a4f0 → 0fa60ef24 → 1a4b2492f 순으로 진화, 최종형):
   ```dockerfile
   # Install additional dependencies for documented parsing compatibility
   RUN pip3 install --no-cache-dir msoffcrypto-tool chardet nltk pyhwp && \
       python3 -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab')"
   ```
   위치: 메인 `pip3 install uv && ...` RUN 블록 직후, Ollama 설치 블록 이전. NLTK 데이터를 빌드 타임에 다운로드해 런타임 외부 네트워크 의존 제거.
4. **기본 비루트 사용자 실행** (1a4b2492f):
   ```dockerfile
   ARG UID=1000        # 업스트림: 0
   ARG GID=1000        # 업스트림: 0
   ...
   ENV HOME=/home/appusr   # 업스트림: /root
   RUN if [ $UID -ne 0 ]; then \
       if [ $GID -ne 0 ]; then \
       addgroup --gid $GID appgrp; \
       fi; \
       adduser --uid $UID --gid $GID --home $HOME --disabled-password --gecos "" appusr; \
       fi
   ```
   - 사용자/그룹명 `app` → `appusr`/`appgrp`, `--no-create-home` 제거(홈 디렉토리 생성), `--gecos ""` 추가(비대화 생성).
   - `USE_PERMISSION_HARDENING` 블록의 `/root` 하드코딩을 `$HOME`으로 치환:
   ```dockerfile
   chgrp -R 0 /app $HOME || true; \
   chmod -R g+rwX /app $HOME || true; \
   find /app -type d -exec chmod g+s {} + || true; \
   find $HOME -type d -exec chmod g+s {} + || true; \
   ```
   - 파일 말미 `USER $UID:$GID`는 업스트림 그대로이나, 기본 ARG가 1000/1000이 되면서 기본 빌드가 비루트로 실행됨.

**재적용 가이드**
- 업스트림 Dockerfile은 버전마다 구조가 자주 바뀌므로 diff 통째 적용보다 위 4개 항목을 문맥 기준으로 개별 이식할 것.
- 비루트(UID 1000) 전환 시 볼륨 `/app/backend/data`의 파일 소유권 문제에 주의 — 기존 root 소유 볼륨을 재사용하면 쓰기 실패 가능(기존 배포 볼륨은 chown 필요). 업스트림 주석에도 "non-root configurations are untested"라고 명시돼 있음.
- `USE_CUDA=true` 기본값은 이미지 크기와 빌드 시간을 크게 늘림. Apple Silicon 태그와 함께 쓰는 점을 볼 때 배포 환경별 의도 확인 후 적용할 것(빌드 시 `--build-arg USE_CUDA=false`로 오버라이드 가능).
- `pyhwp`, `msoffcrypto-tool` 등은 백엔드 파일 파싱 커스텀(타 영역: `backend/open_webui/retrieval/loaders/main.py`, `routers/files.py`)과 세트로 필요.

**관련 커밋**
- `a5955a4f0` 취약점 점검#3 (NODE_OPTIONS, 파싱 패키지 최초 추가)
- `0fa60ef24` nltk 관련 라이브러리 추가 (punkt/punkt_tab 다운로드)
- `0a0f67f4c` feat: USE_CUDA 기본값을 true로 설정...
- `1a4b2492f` refactor: 기본 비루트 사용자 설정 및 권한 강화 (nltk 다운로드 방식도 `python3 -c` 형태로 변경)

### 6. backend/start.sh — 기동 시 Alembic 마이그레이션 명시 실행

**목적/배경**
- 커스텀 DB 마이그레이션(`a1b2c3d4e5f6_add_token_jti_to_auth.py`, auth 테이블에 `token_jti` 컬럼 추가 — 단일 세션 강제 기능용, 타 영역 소속)이 확실히 적용되도록 컨테이너 기동 시 alembic을 명시적으로 실행. 업스트림은 `backend/open_webui/config.py`의 `run_migrations()`가 앱 임포트 시 마이그레이션을 실행하지만 예외를 삼키고 계속 진행하는 구조라(try/except 후 log만 남김), 기동 스크립트에서 한 번 더 명시 실행하는 방어적 조치로 판단됨(정확한 도입 의도는 커밋 메시지 "취약점 점검#4" 외 미확인).

**동작 방식 / 변경 내용**
- `backend/start.sh`에서 uvicorn 실행 직전에 3줄 추가 (Dockerfile의 `CMD [ "bash", "start.sh"]` 경로로 컨테이너 기동 시 항상 실행됨):
  ```bash
  # Run migrations
  alembic -c open_webui/alembic.ini upgrade head

  # Run uvicorn
  WEBUI_SECRET_KEY="$WEBUI_SECRET_KEY" exec "$PYTHON_CMD" -m uvicorn open_webui.main:app \
  ```
- start.sh에는 `set -e`가 없으므로 alembic 실패 시에도 uvicorn 기동은 계속됨.

**재적용 가이드**
- token_jti 마이그레이션 파일(타 영역)과 함께 이식해야 의미가 있음. 마이그레이션 파일의 `down_revision`은 최신 버전의 head revision으로 갱신 필요(현재 파일은 docstring의 Revises와 실제 `down_revision = 'c440947495f3'`이 불일치하는 상태이므로 이식 시 정리 권장 — 이 상세는 auth 영역 문서 참조).
- 최신 업스트림 start.sh에서 uvicorn 실행 라인 직전에 동일하게 삽입하면 됨. working directory가 `backend/`인 상태에서 실행되므로 상대 경로 `open_webui/alembic.ini`가 유효한지 확인.

**관련 커밋**
- `5759a7eb4` 취약점 점검#4 (start.sh 3줄 + 마이그레이션 파일 추가)

### 7. CHANGELOG.md — 0.6.43-fix1 릴리스 노트 추가

**목적/배경**
- 포크의 커스텀 릴리스(0.6.43-fix1) 변경 내역을 한국어로 기록. 코드 동작에는 영향 없음.

**변경 내용**
- 파일 상단(0.6.43 항목 위)에 `## [0.6.43-fix1] - 2026-01-08` 섹션 추가. 내용: 토큰 만료 카운트다운, 활동 시 토큰 갱신, 문서 파싱 라이브러리 추가, 단일 세션 강제, `DISABLE_ADMIN` 관리자 패널 제한, Global 401 인터셉터, sessionStorage 전환, 변경 로그 팝업 비활성화, LLM 에러 마스킹, 로그아웃 시 JTI 무효화 + 백엔드/프론트엔드 기술적 세부 사항 목록.
- 주의: fix2 / fix2.1에서 추가된 기능(채팅 자동 삭제, 비밀번호 검증, 이미지 캡처/웹페이지 첨부 옵션, 개인정보 UI, 운영 스크립트 등)은 CHANGELOG에 **기록되어 있지 않음** — fix1 항목만 존재.

**재적용 가이드**
- 문서 파일이므로 새 베이스 버전으로 이식 시 그대로 복사하지 말고, 새 버전 기준의 릴리스 노트(예: `[0.7.x-fix1]`)로 재작성 권장. 이식 자체는 충돌 위험 낮음(파일 상단 삽입).

**관련 커밋**
- `4be37956d` 취약점 점검#7

### 부록: 이 영역에서 확인했으나 변경 없음 / 미확인 사항

- `scripts/prepare-pyodide.js`: 포크 지점 대비 변경 없음(diff 목록에 없음).
- 세 운영 스크립트 모두 커밋 상태와 작업트리가 동일(커밋 안 된 변경 없음).
- Dockerfile의 `USE_CUDA=true`와 AppleSilicon 태그 조합의 실제 빌드 검증 여부는 미확인(커밋 메시지 기준으로만 확인).
- `migration_guide_0.6.43_fix1_to_0.7.2_fix1.md`는 fix1 시점 기준 가이드로, 이 영역에서는 Dockerfile 파싱 패키지와 alembic 마이그레이션 항목만 다루며 fix2/fix2.1의 운영 스크립트·compose 환경변수 변경은 누락돼 있음(본 문서가 최신 diff 기준으로 보완).


---

# 파트 8. 커버리지 점검 (전체 165개 파일 대조)

### 커버리지 점검 결과 요약

`git diff a7271532f --name-only` (작업트리 포함) 기준 전체 변경 파일은 165개이며, 제공된 "문서화 완료" 목록과 대조한 결과 **누락된 파일은 단 1개**였다.

- 누락 파일: `migration_guide_0.6.43_fix1_to_0.7.2_fix1.md` (저장소 루트, 신규 추가 파일)

그 외 164개 파일은 모두 문서화 완료 목록에 포함되어 있음을 `comm` 기반 정렬 대조로 확인했다.

---

### migration_guide_0.6.43_fix1_to_0.7.2_fix1.md

- **절대 경로**: `/Users/inhyuk/Documents/openProjects/open-webui/migration_guide_0.6.43_fix1_to_0.7.2_fix1.md`
- **변경 유형**: 신규 파일 추가 (479줄 전체 추가, 코드 변경 없음 — 순수 마크다운 문서)
- **최초 도입 커밋**: `d7fbc8924` ("변경사항 정리#2") 계열, 이후 `26b57d8ed`, `4be037003`, `2b4840c31` 에서 수정 이력 존재
- **성격**: 실행 코드가 아닌 **내부 운영 문서**이다. 다만 내용 자체가 이 저장소의 커스텀 사항 전체를 요약한 "메타 문서"이므로 아래에 상세히 기록한다.

#### 목적

**Open WebUI 0.6.43-fix1** 에 적용된 사내 커스텀(보안 강화 + 데이터 정책)을 향후 **0.7.2 기반 커스텀 버전(0.7.2-fix1)** 으로 이관할 때 사용할 작업 지침서. 문서 서두에 "라인 번호보다 코드 문맥(Context)을 보고 삽입 위치를 찾으라"는 주의사항이 명시되어 있다. 문서 말미에 `*Generated by Antigravity*` 표기가 있다.

#### 문서가 다루는 커스텀 항목 (목차 요약)

문서는 다음 커스텀들을 재적용 가능한 코드 스니펫과 함께 정리하고 있다 (각 항목의 실제 구현 상세는 이미 개별 파일 문서에서 다뤄진 내용과 동일 주제):

1. **백엔드**
   - `Dockerfile`: 문서 파싱 호환용 패키지 추가 — `RUN pip3 install --no-cache-dir msoffcrypto-tool chardet nltk pyhwp`
   - `backend/open_webui/env.py`: `DISABLE_ADMIN` 환경변수 로드 (`os.environ.get("DISABLE_ADMIN", "False").lower() == "true"`)
   - `backend/open_webui/config.py`: `DISABLE_ADMIN` import 및 매핑, `CHAT_DELETE_ENABLED: bool = False` / `CHAT_DELETE_DAYS: int = 365` 설정 추가
   - `backend/open_webui/main.py`: `lifespan` 내 `periodic_chat_deletion()` 비동기 태스크 (1시간 간격으로 `Chats.delete_chats_older_than(days)` 실행), `get_app_config` 응답에 `"disable_admin": DISABLE_ADMIN` 추가
   - `backend/open_webui/utils/auth.py`: `get_admin_user`에서 `DISABLE_ADMIN`이면 `HTTP_403_FORBIDDEN` (`ERROR_MESSAGES.ACCESS_PROHIBITED`) 발생
   - `backend/open_webui/routers/auths.py`: `SessionUserResponse`에 `server_timestamp: Optional[int]` 필드 추가, 각 응답에 `"server_timestamp": int(time.time())` 포함 (클라이언트-서버 시간 동기화용)
   - `backend/open_webui/models/chats.py`: `ChatTable.delete_chats_older_than(self, days: int) -> int` 메서드 (`Chat.updated_at < cutoff_time` 조건 일괄 삭제)
2. **DB 마이그레이션**
   - `auth` 테이블에 `token_jti` (String, nullable) 컬럼을 추가하는 alembic 마이그레이션 (`op.add_column('auth', sa.Column('token_jti', sa.String(), nullable=True))`)
3. **프론트엔드**
   - 전역 토큰 저장소 `localStorage` → `sessionStorage` 전환 (검색어: `localStorage.token`, `localStorage.getItem('token')`; `AccountPending.svelte` 포함 주의)
   - `src/routes/+layout.svelte`: 1초 간격 세션 체크 타이머(서버시간 기반 `clockSkew` 보정, `warningThreshold = tokenDuration > 60 ? 60 : 10`, 만료 시 `logoutHandler()`), `AgreementModal`/`SessionTimeoutModal` 연결, `localStorage.getItem('agreedToTerms')` 미존재 시 약관 모달 표시
   - `src/routes/auth/+page.svelte`: 로그인 상태(`$user` 존재) 시 리다이렉트
   - `src/routes/(app)/admin/+layout.svelte`: `$config?.features?.disable_admin` 이면 관리자 페이지 접근 차단(`goto('/')`)
   - 신규 파일 3종의 전체 소스 수록: `SessionTimeoutModal.svelte` (세션 만료 경고/연장/로그아웃 모달), `AgreementModal.svelte` (marked + DOMPurify 로 `/agreement.md` 렌더링, `dismissible={false}`, 동의 시 `localStorage.agreedToTerms='true'`), `static/agreement.md` (원내 중요정보 보호 고지사항: 중요자료 업로드 금지 / 불법·부당 이용 금지 / 비윤리적 활용 금지, 대화 내용 1년 보관 후 자동 파기 고지)
   - `src/lib/components/common/Modal.svelte`: ESC 키 및 백드롭 클릭 닫기에 `dismissible` 조건 추가
4. **최종 확인 체크리스트**: 약관 모달 표시, `dismissible={false}` 동작, 세션 만료 경고, `sessionStorage` 사용으로 탭 종료 시 로그아웃 — 4개 항목

#### 핵심 코드

파일 전체가 마크다운 문서이므로 "핵심 코드"는 없다. 문서 내부의 코드 블록은 이미 문서화 완료된 각 소스 파일의 실제 변경 사항을 요약·인용한 것이며, 일부는 실제 구현과 세부 표현이 다를 수 있는 참고용 스니펫이다 (예: 마이그레이션 파일명은 실제로는 `a1b2c3d4e5f6_add_token_jti_to_auth.py`인데 문서에는 `xxxx_add_token_jti_to_auth.py`로 표기됨). **재적용 시에는 이 문서보다 실제 diff / 개별 파일 문서를 우선 기준으로 삼아야 한다.**

#### 순정 최신 버전 재적용 방법

**재적용 대상 아님.** 이 가이드 파일은 본 문서(`CUSTOMIZATIONS_0.6.43-fix2.1.md`)로 대체되어 이후 저장소에서 삭제됐다. 필요 시 git 히스토리에서 열람할 수 있다:
```bash
git show ab0073ddf^:migration_guide_0.6.43_fix1_to_0.7.2_fix1.md
```

#### 사소성 판단

빌드/런타임에 전혀 영향이 없는 순수 문서였으므로 **기능적으로는 자명하게 사소한(non-functional) 변경**이다. 위 분석 내용은 커버리지 전수 대조 당시의 기록으로 남겨 둔다.

---

### 결론

문서화 완료 목록 대비 누락 파일은 `migration_guide_0.6.43_fix1_to_0.7.2_fix1.md` 1건뿐이며, 위와 같이 문서화를 완료했다. 그 외 추가 누락은 없다.
