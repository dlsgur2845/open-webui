# Open WebUI 0.10.2 커스터마이징 전체 명세 (브랜치 `0.10.2-fix1`)

> **문서 목적**: 순정 Open WebUI **0.10.2**(커밋 `ecd48e2f7`) 대비 이 저장소에 적용된 **모든 커스텀 사항**을, **차기 업스트림 버전(0.11.x 이후)** 위에 동일하게 재구현할 수 있는 수준으로 기술한다.
>
> - **비교 기준**: `ecd48e2f7`(업스트림 v0.10.2) ↔ 브랜치 `0.10.2-fix1` HEAD
> - **규모**: 변경 파일 204개 (+5,715 / −1,050 라인). 이 중 약 157개는 `localStorage.token → sessionStorage.token` 기계적 치환 단독 변경.
> - **작성일**: 2026-07-14 (모든 내용은 `git diff ecd48e2f7..HEAD` 및 현재 트리 실측 기반)
> - **이전 기준 문서**: `CUSTOMIZATIONS_0.6.43-fix2.1.md`는 0.6.43 기준의 역사적 기록으로 대체됨. **차기 이관은 본 문서만을 기준으로 할 것.**
> - **데이터/DB 이관**: 코드 이식과 별개로 운영 DB·볼륨 전환은 `MIGRATION_RUNBOOK_to_0.10.2.md`(0.6.43→0.10.2 완료 기록)를 템플릿 삼아 대상 버전용 런북을 새로 작성할 것.

---

## 커스텀 커밋 이력 (시간순)

```
3584a740c chore: 0.10.2-fix1 기반 준비 — 커스텀 문서/운영 스크립트/신규 컴포넌트/compose 이식
23203ac6f feat: 백엔드 커스텀 이식 (0.6.43-fix2.1 → 0.10.2)
673d247ed feat: 프런트엔드 커스텀 이식 (0.6.43-fix2.1 → 0.10.2)
bd56c2cda fix: JTI 검사 예외를 automation 내부 토큰으로만 한정 (fail-closed)
82782b0e3 fix: start.sh alembic 실행을 open_webui 디렉터리에서 수행
16b045260 refactor: 토큰 자동 갱신을 이벤트 구동 방식으로 변경
fafd8e9fa ci: fix 브랜치용 도커 멀티아치 빌드/릴리즈 워크플로우 추가   (이후 3807d93fa에서 제거)
d69a30d7e ci: GHCR 이미지 경로를 ax/open-webui로 변경                  (이후 30a6b5ddf에서 원복)
30a6b5ddf ci: GHCR 이미지 경로 원복 및 릴리즈 노트에 재태깅 안내 추가
3807d93fa ci: fix 브랜치 도커 빌드 워크플로우 제거 (로컬 빌드로 전환)
75d2a4ed7 fix: 0.6.43-fix2.1 DB의 잘못된 alembic stamp 자동 교정
92c87cf7e fix: 서버-클라이언트 시계 차이로 로그인 직후 로그아웃되는 문제 수정
5560559e1 build: USE_CUDA 기본값을 false로 변경 (서버에서 GPU 미사용)
9131cfe00 fix: 앱 진입 시 clockSkew를 세션 응답의 server_timestamp로 즉시 초기화
e335d4095 refac: 마우스 포인터 이동을 세션 갱신 트리거에서 제외
ce04f3f16 docs: CLAUDE.md 추가 — 빌드/배포/테스트 규칙 정리 (.gitignore 예외 처리)
e81eedfdd docs: 서버 시계 NTP 동기화 반영, 시간 검증은 서버에서만 수행 원칙 명시
```

---

## 문서 구성

| 파트 | 주제 | 핵심 내용 |
|---|---|---|
| 1 | 인증/세션/토큰 보안 | JWT 24h, JTI 단일 세션, /auths/refresh, sessionStorage, 세션 타임아웃 UI, 이벤트 구동 자동 갱신, 시계차 보정(2026-07-14 수정 3건), alembic |
| 2 | 백엔드 보안/기능/파싱/DB | 오류 마스킹, DISABLE_ADMIN, 한글화, 비밀번호 정책, 기능 토글 3종, 대화 자동 삭제, Tika, 인사·조직 일일 동기화, start.sh, stamp 교정, Dockerfile |
| 3 | 프런트 전반/정책/운영·배포 | 동의 모달·보존 정책, sessionStorage 전수, 토글 UI, 운영 스크립트 3종, compose/CI/런북 |

---

## 최신 버전 재적용 시 공통 주의사항

1. **라인 번호가 아니라 코드 문맥 기준으로 이식할 것.** 본 문서의 라인 번호는 0.10.2-fix1 시점 실측값이며, 업스트림 리팩터링으로 위치가 달라질 수 있다.
2. **각 파트 서두의 "업스트림에 이미 흡수된 것들" 목록을 먼저 확인할 것.** 0.6.43 시절 커스텀 중 일부(전역 401 인터셉터, Analytics 대시보드, 파일 예외 처리 등)는 업스트림에 편입되어 커스텀이 소멸했다. 차기 버전에서도 같은 일이 일어날 수 있으니, 이식 전 대상 버전 소스에서 기존재 여부를 grep으로 확인하고 **중복 적용을 금지**한다.
3. **설정값은 DB(`config` 테이블)가 env보다 우선한다 — `ENABLE_PERSISTENT_CONFIG`는 기본값 `true`로 운영한다 (2026-07-22 재확정).** 부팅 시 `Config.seed_defaults(DEFAULT_CONFIG)`가 **DB에 없는 키만** 심고, 이후 `Config.get()`/`get_many()`는 DB 행을 우선 읽는다. 즉 env는 **키가 DB에 없을 때의 초기값**일 뿐이라, 기존 설치본에서 env만 바꾸면 반영되지 않는다 — 실사례: `ENABLE_WEBPAGE_ATTACHMENT=false`·`ENABLE_USER_PERSONAL_INFO=false`가 무시됨(0.6.43-fix2.1 DB 이관본에 두 행이 `true`로 이미 존재). 배포 후 값이 안 먹으면 DB를 직접 갱신할 것 (`value`는 JSON 컬럼이므로 JSON 불리언이어야 한다):
   ```sql
   SELECT key, value FROM config WHERE key IN ('ui.enable_webpage_attachment', 'ui.enable_user_personal_info');
   UPDATE config SET value = 'false'::json, updated_at = EXTRACT(EPOCH FROM NOW())::bigint
   WHERE key IN ('ui.enable_webpage_attachment', 'ui.enable_user_personal_info');
   ```
   경위: 2026-07-15에 이 함정을 없애려 `ENABLE_PERSISTENT_CONFIG=false`를 도입했다가, 관리자 UI 설정이 재시작 시 소멸하는 트레이드오프가 수용 불가로 판정되어 **기본값(true)으로 원복**했다. 커스텀 토글 3종은 쓰기 API가 없으므로(`routers/`에 쓰기 경로 0건) 위 UPDATE는 UI로 되돌아가지 않는 영구 설정이다. 차기 버전 이식 시 `Config.seed_defaults()`가 여전히 "없는 키만 삽입"인지 확인할 것.
4. **Alembic**: 커스텀 마이그레이션 `f1a2b3c4d5e6_add_token_jti_to_auth.py`의 `down_revision`을 **대상 버전의 실제 최신 head로 갱신**해야 단일 head가 유지된다. 대상 head 확인: `ls backend/open_webui/migrations/versions/` 후 `alembic heads` 또는 파트 1의 검증 스크립트 사용. 구 포크 DB의 stamp 자동 교정 로직(`migrations/env.py`)은 0.6.43 DB를 직접 받는 경우에만 필요하다.
5. **sessionStorage 치환은 스크립트로 일괄 처리** 후 `grep -rn "localStorage.token" src/`로 잔존 0건을 검증할 것 (파트 3, 섹션 2의 스크립트·주의 파일 목록 참조). 로그아웃 경로의 `localStorage.removeItem('token')` 병기는 치환하면 안 된다.
6. **시간 검증은 서버에서만 한다.** 프론트엔드가 브라우저 시계로 만료를 직접 판정하는 코드를 새로 들이지 말 것. 표시·타이머는 `server_timestamp` 기반 clockSkew 보정, 최종 판정(로그아웃)은 서버 401 확인. (파트 1, 섹션 10~12·14)
7. **빌드/테스트/배포 규칙은 `CLAUDE.md`를 따른다**: 이미지 태그 `ax/` 프리픽스, linux/amd64, non-root(appusr:appgrp 1000), CUDA 미사용, 로컬 빌드 → tar.gz. 토큰/세션 수정 시 Playwright 브라우저 시계 시프트 테스트 필수.

---

## 차기 버전 업그레이드 절차 (요약 체크리스트)

1. **준비**: `git fetch upstream --tags`로 대상 버전 태그 확보. **리모트에 같은 이름 브랜치가 있는지 먼저 확인** 후 `git checkout -b <X.Y.Z>-fix1 v<X.Y.Z>` 생성. `package.json` version을 브랜치명과 동일하게.
2. **소멸 커스텀 선별**: 각 파트 서두의 "업스트림 흡수" 목록 + 본 문서의 각 섹션 접점 파일을 대상 버전에서 grep — 이미 반영된 항목은 이식 생략.
3. **기계적 치환 먼저**: sessionStorage 전환(파트 3, 섹션 2 스크립트) → grep 검증.
4. **백엔드 이식**: 파트 2의 권장 순서(섹션 13) → 파트 1의 인증 체인(JTI → refresh → server_timestamp → alembic down_revision 갱신).
5. **프런트 이식**: 파트 1의 세션 UI·자동 갱신·시계차 보정 → 파트 3의 동의 모달·토글 UI.
6. **빌드/검증**: CLAUDE.md 규칙대로 빌드 → 컨테이너 `JWT_EXPIRES_IN=3m` 기동 → API 테스트(발급 직후 200 / 만료 후 401) + **Playwright 시계 시프트(+180s) 테스트** (로그인 유지 + 만료 시 로그아웃).
7. **데이터 이관 런북 작성**: `MIGRATION_RUNBOOK_to_0.10.2.md`를 템플릿으로 대상 버전용 작성 (alembic head, config 테이블, 벡터 컬렉션 네이밍 대조).
8. **문서 갱신**: 본 문서를 새 기준 버전으로 재작성(`CUSTOMIZATIONS_<X.Y.Z>-fixN.md`), 구 문서에 대체 배너 추가, CLAUDE.md 참조 갱신.

---

# 파트 1. 인증/세션/토큰 보안

기준: 업스트림 `ecd48e2f7` (v0.10.2) 대비 브랜치 `0.10.2-fix1` HEAD. 아래 내용은 전부 `git diff ecd48e2f7..HEAD` 및 현재 HEAD 트리 실측 기준이다.

**0.10.2 업스트림에 이미 흡수된 것들 (재이식 시 중복 적용 금지)**
- 전역 401 fetch 인터셉터(`isAuthenticatedBackendFetch`, `isCurrentSessionUnauthorized`, `redirectToAuthAfterUnauthorized`)와 15초 주기 `checkTokenExpiry`는 **업스트림 0.10.2에 이미 존재**한다(`src/routes/+layout.svelte`). 0.6.43 시절의 "인터셉터 신규 도입" 커스텀은 더 이상 필요 없고, 아래 9~10번의 **정책 병합분만** 커스텀이다.
- `create_token()`은 업스트림이 이미 모든 JWT에 `jti`(uuid4)를 넣는다(`backend/open_webui/utils/auth.py`의 `create_token`, 미변경).
- automation 실행용 내부 토큰(`typ: 'automation'`)도 업스트림 0.10.2 기능이다(`backend/open_webui/utils/automations.py`).
- `expires_at`을 세션 응답에 포함하는 것, httpOnly 쿠키 `token` 발급도 업스트림 기본 동작.
- 비밀번호 정책 강화(`validate_password` 규칙 기반 검사, `PASSWORD_BLACKLIST`)와 `DISABLE_ADMIN` 게이트도 이 파일들의 diff에 포함돼 있으나 **다른 파트 담당이므로 여기서는 다루지 않는다.**

---

### 1. JWT 세션 수명 단축 (기본 4w → 24h)

**목적/배경**
- 취약점 점검 조치. 기본 토큰 수명 4주가 과도하게 길어 24시간으로 단축.

**동작 방식**
- 환경변수 `JWT_EXPIRES_IN`의 코드 기본값만 변경. 0.10.2 베이스에서는 이 값이 `DEFAULT_CONFIG`의 `'auth.jwt_expiry'` 키로 시드되어 DB `config` 저장소(`Config.get('auth.jwt_expiry')`)를 통해 읽힌다.

**변경 파일 및 핵심 내용**
- `backend/open_webui/config.py` — `API_KEYS_ALLOWED_ENDPOINTS` 정의 직후:
```python
JWT_EXPIRES_IN = os.getenv('JWT_EXPIRES_IN', '24h')
```
(업스트림 기본값은 `'4w'`. `DEFAULT_CONFIG`의 `'auth.jwt_expiry': JWT_EXPIRES_IN` 항목 자체는 업스트림 그대로.)
- `docker-compose.yaml` — 배포에서는 기본값에 의존하지 않고 명시: `- 'JWT_EXPIRES_IN=24h'`

**재적용 가이드**
- 한 줄 변경. 단 **기존 설치본은 DB config에 `auth.jwt_expiry` 값이 이미 저장돼 있으면 코드 기본값이 무시**될 수 있으므로, 기존 DB에는 Admin 설정 또는 DB 업데이트로 별도 반영 확인.
- compose에 `JWT_EXPIRES_IN`을 명시해 두는 편이 안전(현재 그렇게 함).
- 업스트림 변화 접점: `JWT_EXPIRES_IN` env 정의 위치와 `auth.jwt_expiry` config 키 이름.

**관련 커밋**
- `23203ac6f` (백엔드 이식), `3584a740c` (compose 명시)

---

### 2. JTI 기반 단일 세션 강제 (Single Session Enforcement)

**목적/배경**
- 사용자당 활성 세션(토큰)을 1개로 제한. 새 위치에서 로그인하면 이전 토큰이 즉시 무효화되고, 로그아웃 시 서버 측에서 토큰을 즉시 무효화(재사용 방지).
- 토큰의 `jti`를 DB(`auth.token_jti`)에 "현재 유효한 단 하나의 jti"로 저장하고 매 요청 시 대조한다.

**동작 방식**
1. 로그인(`signin`/`signup`/`ldap`/OAuth 완료) 시: 0.10.2에서는 네 경로가 모두 공통 헬퍼 `create_session_response()`를 거치므로 **한 곳에만** JTI 저장을 삽입하면 된다. OAuth 콜백 경로 중 `utils/oauth.py`의 `OAuthManager`가 직접 `create_token`하는 지점에도 별도 삽입(0.6.43 시절 OAuth 미대응 문제 해결).
2. 갱신(`POST /auths/refresh`) 시: 새 토큰의 jti로 DB 교체 → 이전 토큰 즉시 무효화(회전). (섹션 5 참조)
3. 매 인증 요청(`get_current_user`, JWT 경로): 토큰에 `jti`가 있으면 DB의 `token_jti`와 다를 경우 401 (`INVALID_TOKEN`). 예외는 `typ='automation'` 내부 토큰뿐(섹션 3).
4. 로그아웃(`signout`): DB의 `token_jti`를 `None`으로 초기화(+ 업스트림의 `invalidate_token`도 그대로 수행).
- API 키(`sk-`) 인증 경로는 JWT 분기 이전에 return되므로 JTI 검사 대상이 아님.

**변경 파일 및 핵심 내용**

- `backend/open_webui/models/auths.py` — 컬럼/필드 추가 (0.10.2는 모델 계층이 **async**로 바뀌었으므로 메서드도 async로 재작성됨):
```python
class Auth(Base):  # credential ↔ user linkage
    ...
    token_jti = Column(String, nullable=True)  # currently valid JWT ID (single session enforcement)

class AuthModel(BaseModel):
    ...
    token_jti: Optional[str] = None
```
```python
async def update_user_token_jti_by_id(
    self,
    user_id: str,
    token_jti: str | None,
    db: AsyncSession | None = None,
) -> bool:
    """Store the currently valid JWT ID for single-session enforcement."""
    try:
        async with get_async_db_context(db) as session:
            auth_row = await session.get(Auth, user_id)
            if auth_row is None:
                return False
            auth_row.token_jti = token_jti
            await session.commit()
            return True
    except Exception:
        return False

async def get_user_token_jti_by_id(
    self,
    user_id: str,
    db: AsyncSession | None = None,
) -> str | None:
    """Return the currently valid JWT ID stored for the user, if any."""
    try:
        async with get_async_db_context(db) as session:
            auth_row = await session.get(Auth, user_id)
            return auth_row.token_jti if auth_row else None
    except Exception:
        return None
```
(삽입 위치: `update_email_by_id` 다음, `delete_auth_by_id` 앞.)

- `backend/open_webui/utils/auth.py` — `get_current_user`의 JWT 분기, OTel span 속성 설정 블록 직후·last-active 갱신(`asyncio.create_task(Users.update_last_active_by_id(...))`) 직전에 삽입:
```python
# Single Session Enforcement: a session token's JTI must match the
# one stored in the DB (rotated on signin/signup/ldap/oauth/refresh,
# cleared on signout). The only exemption is the server-internal
# automation-run token (typ='automation', issued in
# utils/automations.py and never sent to a client); any other typ
# value stays subject to the JTI check (fail-closed).
token_jti = data.get('jti')
if token_jti and data.get('typ') != 'automation':
    user_jti = await Auths.get_user_token_jti_by_id(user.id)
    if user_jti != token_jti:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_MESSAGES.INVALID_TOKEN,
        )
```
(0.10.2에서는 `Auths`가 모듈 상단에서 이미 import되어 있어(`from open_webui.models.auths import Auths`) 0.6.43 시절의 지역 import가 불필요해짐.)

- `backend/open_webui/routers/auths.py` — 공통 헬퍼 `create_session_response()`에서 `create_token(...)` 직후 삽입:
```python
# Single Session Enforcement: store this token's JTI as the only valid one,
# invalidating any previously issued session token for this user.
decoded = decode_token(token)
if decoded and 'jti' in decoded:
    await Auths.update_user_token_jti_by_id(user.id, decoded['jti'], db=db)
```
이 헬퍼는 현재 트리에서 `ldap_auth`, `signin`, `signup`, OAuth 완료 엔드포인트(`source='oauth'`) 4곳에서 호출된다 — 개별 엔드포인트에 중복 삽입할 필요 없음.

- `backend/open_webui/routers/auths.py` — `signout`에서 `invalidate_token(request, token)` 호출 직후:
```python
# Single Session Enforcement: clear the stored JTI so the token
# cannot be reused after signout.
try:
    if data and data.get('id'):
        await Auths.update_user_token_jti_by_id(data['id'], None, db=db)
except Exception as e:
    log.error(f'Error clearing JTI on signout: {e}')
```

- `backend/open_webui/utils/oauth.py` — `OAuthManager` 내 `create_token`으로 `jwt_token` 발급 직후(`ENABLE_OAUTH_GROUP_MANAGEMENT` 분기 앞):
```python
# Single Session Enforcement: store this token's JTI as the only
# valid one, so OAuth logins pass the JTI check in get_current_user.
decoded = decode_token(jwt_token)
if decoded and 'jti' in decoded:
    await Auths.update_user_token_jti_by_id(user.id, decoded['jti'])
```
(같은 파일 import에 `decode_token` 추가: `from open_webui.utils.auth import create_token, decode_token, get_password_hash`)

**재적용 가이드**
1. 대상 버전에서 `create_token()`이 `jti`를 payload에 넣는지 확인(0.10.2는 넣음).
2. **토큰 발급 지점 전수 조사**: `grep -rn "create_token(" backend/`로 모든 발급 지점을 찾고, 클라이언트에 전달되는 세션 토큰 발급 지점마다 JTI 저장을 삽입할 것. 0.10.2 기준 지점: `create_session_response`(4개 로그인 경로 공통), `refresh_session`, `utils/oauth.py`. 업스트림이 로그인 경로를 다시 개별화하거나 새 경로(예: SCIM, 데스크톱 연동)를 추가하면 지점이 늘 수 있다.
3. 모델 계층 시그니처(async 여부, `db` 세션 주입 방식 `get_async_db_context`)는 업스트림 변화가 잦은 접점 — 대상 버전의 인접 메서드(`update_email_by_id` 등) 형태를 따라 작성할 것.
4. 트러스티드 헤더/API 키 인증 경로는 JTI 검사 미적용이 맞는지 재확인.
5. 마이그레이션은 섹션 4 참조(한 세트).

**관련 커밋**
- `23203ac6f` feat: 백엔드 커스텀 이식 (0.6.43-fix2.1 → 0.10.2)
- `bd56c2cda` fix: JTI 검사 예외를 automation 내부 토큰으로만 한정 (섹션 3)

---

### 3. JTI 검사 예외를 automation 내부 토큰으로만 한정 (fail-closed)

**목적/배경**
- 0.10.2의 자동화(automation) 실행은 서버 내부에서 `typ: 'automation'` 클레임이 붙은 1시간짜리 토큰을 자체 발급해 chat completion 파이프라인을 호출한다. 이 토큰은 로그인 세션이 아니므로 DB의 `token_jti`와 일치하지 않고, JTI 검사를 그대로 적용하면 자동화 실행이 전부 401로 죽는다.
- 최초 이식(`23203ac6f`)은 `if token_jti and not data.get('typ'):`로 **"typ 클레임이 있으면 전부 면제"**였는데, 이는 향후 업스트림이 다른 `typ` 값을 추가하면 자동으로 단일 세션 검사를 우회하게 되는 fail-open 구조였다. `bd56c2cda`에서 **정확히 `typ='automation'`일 때만** 면제하도록 강화(fail-closed).

**동작 방식**
- 검사 조건: `if token_jti and data.get('typ') != 'automation':` — automation 토큰 외의 모든 jti 보유 토큰은 DB 대조 대상.
- automation 토큰의 발급 근거(현재 트리 `backend/open_webui/utils/automations.py`):
```python
token = create_token(
    data={'id': user.id, 'typ': 'automation'},
    expires_delta=expires_delta or timedelta(hours=1),
)
```
이 토큰은 서버 내부 `_build_request()`에만 쓰이고 클라이언트로 전송되지 않는다.

**변경 파일 및 핵심 내용**
- `backend/open_webui/utils/auth.py` — 섹션 2에 인용한 JTI 검사 블록의 조건식과 주석이 이 커밋의 결과물이다.

**재적용 가이드**
- 재이식 시 처음부터 `!= 'automation'` 형태(fail-closed)로 넣을 것.
- 업스트림 변화 접점: 새 버전에서 `create_token(data={..., 'typ': ...})` 형태의 내부 토큰 발급이 늘었는지 `grep -rn "'typ'" backend/`로 확인하고, 정당한 서버 내부 토큰이 추가됐다면 화이트리스트(`data.get('typ') not in ('automation', ...)`) 방식으로 확장 — 기본은 검사 대상에 포함시키는 방향 유지.

**관련 커밋**
- `bd56c2cda` fix: JTI 검사 예외를 automation 내부 토큰으로만 한정 (fail-closed)

---

### 4. Alembic 마이그레이션 `f1a2b3c4d5e6` + 레거시 포크 stamp 자동 교정

**목적/배경**
- `auth.token_jti` 컬럼 추가 마이그레이션. 0.6.43-fix2.1 시절의 revision id `a1b2c3d4e5f6`는 **0.10.2 업스트림 체인에서 skill 테이블 마이그레이션이 같은 id를 쓰고 있어 재사용 불가** → 새 id `f1a2b3c4d5e6`로 재작성.
- 0.6.43-fix2.1에서 운영하던 DB는 `alembic_version`이 `a1b2c3d4e5f6`(구 체인의 head = token_jti)로 stamp돼 있는데, 0.10.2 체인에서는 같은 id가 체인 중간(skill 테이블)을 가리키므로 그대로 업그레이드하면 중간 마이그레이션들이 건너뛰어져 `UndefinedTable`로 붕괴한다. 이를 기동 시 자동 교정.

**동작 방식**
- 마이그레이션: `auth` 테이블에 `token_jti` 컬럼이 없을 때만 추가(멱등) — 구 포크 DB에는 컬럼이 이미 있으므로 replay돼도 안전.
- stamp 교정(`migrations/env.py`): `alembic_version == 'a1b2c3d4e5f6'`인데 `skill` 테이블이 **없으면** 레거시 포크 DB로 판정하고, 그 DB가 실제로 적용한 마지막 공통 revision인 `c440947495f3`(add_chat_file_table)로 되돌려 stamp → 이후 나머지 체인이 순서대로 replay된다.

**변경 파일 및 핵심 내용**
- `backend/open_webui/migrations/versions/f1a2b3c4d5e6_add_token_jti_to_auth.py` (신규, 37줄 전체):
```python
revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, None] = '42e2978c7933'

def upgrade() -> None:
    # Older custom deployments may already have the column — keep this idempotent
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [column['name'] for column in inspector.get_columns('auth')]

    if 'token_jti' not in columns:
        op.add_column('auth', sa.Column('token_jti', sa.String(), nullable=True))
```
  - `down_revision = '42e2978c7933'`(add_memory_path_and_meta)은 **업스트림 0.10.2의 단일 head를 실측**해 지정한 값이다. 현재 트리에서도 `f1a2b3c4d5e6`가 유일한 head임(자식 revision 없음, 스크립트로 확인).
- `backend/open_webui/migrations/env.py` — `run_migrations_online()`에서 `enable_iam_token_auth(...)` 직후에 `_fix_legacy_fork_stamp(live_connectable)` 호출 추가:
```python
LEGACY_FORK_STAMP = 'a1b2c3d4e5f6'
LEGACY_FORK_RESTAMP = 'c440947495f3'


def _fix_legacy_fork_stamp(connectable) -> None:
    """Restamp databases carried over from the 0.6.43-fix2.1 fork.

    A database legitimately stamped at 'a1b2c3d4e5f6' by the current chain has
    the skill table (that revision creates it); a legacy-fork database does not,
    which makes the two cases distinguishable.
    """
    from sqlalchemy import inspect, text

    with connectable.connect() as connection:
        try:
            stamped = connection.execute(text('SELECT version_num FROM alembic_version')).scalar()
        except Exception:
            return  # fresh database — no alembic_version table yet
        if stamped != LEGACY_FORK_STAMP:
            return
        if inspect(connection).has_table('skill'):
            return
        ...
        connection.execute(
            text('UPDATE alembic_version SET version_num = :revision'),
            {'revision': LEGACY_FORK_RESTAMP},
        )
        connection.commit()
```

**재적용 가이드**
1. **`down_revision`은 대상 버전의 실제 최신 head로 반드시 재실측**할 것: versions 디렉터리에서 "어떤 파일의 down_revision으로도 참조되지 않는 revision"이 head다. 0.6.43 시절처럼 head가 2개로 갈라지는 실수를 반복하지 말 것.
2. revision id는 대상 버전 체인과 충돌하지 않는 값인지 `grep -rn "<id>" backend/open_webui/migrations/versions/`로 확인 후 사용.
3. `_fix_legacy_fork_stamp`는 **0.6.43-fix2.1 DB에서 직접 올라오는 경우에만** 필요한 일회성 안전장치다. 이미 0.10.2-fix1을 거친 DB는 stamp가 정상이므로, 미래 버전(0.11.x) 이식 시에는 이 함수 자체를 이식할 필요가 없을 수 있다 — 단, 0.6.43에서 곧바로 0.11.x로 뛰는 DB가 남아 있다면 유지.
4. 업스트림 변화 접점: `env.py`의 `run_migrations_online()` 구조(커넥션 획득 방식)가 버전마다 달라질 수 있음. "마이그레이션 실행 직전, 커넥터블 확보 직후"라는 위치만 지키면 된다.

**관련 커밋**
- `23203ac6f` (f1a2b3c4d5e6 마이그레이션), `75d2a4ed7` fix: 0.6.43-fix2.1 DB의 잘못된 alembic stamp 자동 교정

---

### 5. 세션 갱신 엔드포인트 `POST /api/v1/auths/refresh` + `server_timestamp` + `features.jwt_expires_in`

**목적/배경**
- 짧아진 토큰 수명을 보완해, 로그아웃 없이 세션을 연장(새 토큰 발급 + JTI 회전)하는 API. 클라이언트-서버 시계 오차 보정을 위해 모든 세션 응답에 `server_timestamp`(서버 현재 시각, epoch 초)를 포함하고, 프론트 타이머가 쓸 토큰 수명(초)을 `/api/config`의 `features.jwt_expires_in`으로 노출.

**동작 방식**
- 인증된 사용자(`Depends(get_current_user)` — 기존 토큰이 JTI 검사를 통과해야 함)가 호출하면: 새 토큰 발급 → 새 jti로 DB 교체(이전 토큰 즉시 무효화) → httpOnly 쿠키 `token` 재설정 → `SessionUserResponse`(+`server_timestamp`) 반환.
- `server_timestamp`는 `create_session_response()`(로그인 4경로 공통)와 `get_session_user`, `refresh_session` 응답에 모두 포함.

**변경 파일 및 핵심 내용**
- `backend/open_webui/routers/auths.py`:
```python
class SessionUserResponse(Token, UserProfileImageResponse):
    expires_at: int | None = None
    permissions: dict | None = None
    server_timestamp: int | None = None
```
  - `create_session_response()`와 `get_session_user`의 반환 dict 끝에 `'server_timestamp': int(time.time()),` 추가.
  - 신규 엔드포인트(`get_session_user` 뒤, "Update Profile" 섹션 앞에 삽입):
```python
@router.post('/refresh', response_model=SessionUserResponse)
async def refresh_session(
    request: Request,
    response: Response,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Issue a fresh token for an already-authenticated session (sliding session).
    Rotates the stored JTI, so the previous token is invalidated immediately.
    """
    expires_delta = parse_duration(await Config.get('auth.jwt_expiry'))
    expires_at = None
    if expires_delta:
        expires_at = int(time.time()) + int(expires_delta.total_seconds())

    token = create_token(
        data={'id': user.id},
        expires_delta=expires_delta,
    )

    # Single Session Enforcement: rotate the stored JTI to the new token
    decoded = decode_token(token)
    if decoded and 'jti' in decoded:
        await Auths.update_user_token_jti_by_id(user.id, decoded['jti'], db=db)

    datetime_expires_at = datetime.datetime.fromtimestamp(expires_at, datetime.timezone.utc) if expires_at else None
    max_age = int(expires_delta.total_seconds()) if expires_delta else None
    response.set_cookie(
        key='token',
        value=token,
        expires=datetime_expires_at,
        httponly=True,
        samesite=WEBUI_AUTH_COOKIE_SAME_SITE,
        secure=WEBUI_AUTH_COOKIE_SECURE,
        **({'max_age': max_age} if max_age is not None else {}),
    )

    user_permissions = await get_permissions(user.id, await Config.get('user.permissions'), db=db)

    return {
        'token': token,
        'token_type': 'Bearer',
        'expires_at': expires_at,
        'id': user.id,
        'email': user.email,
        'name': user.name,
        'role': user.role,
        'profile_image_url': user.profile_image_url,
        'permissions': user_permissions,
        'server_timestamp': int(time.time()),
    }
```
- `backend/open_webui/main.py` — `get_app_config`:
  - config 일괄 조회 키 목록에 `'auth.jwt_expiry',` 추가 (`'notes.enable'` 뒤).
  - `features`의 **로그인 사용자 전용 블록**(`# --- Authenticated: only consumed by logged-in frontend ---` 아래) 안에 추가:
```python
'jwt_expires_in': (
    f'{parse_duration(config.get("auth.jwt_expiry")).total_seconds()}'
    if parse_duration(config.get('auth.jwt_expiry'))
    else '0'
),
```
  - import 추가: `from open_webui.utils.misc import parse_duration`
- `src/lib/apis/auths/index.ts` — `getSessionUser` 뒤에 추가. **다른 API 헬퍼와 달리 `{ status, detail }` 객체를 throw**해 호출부가 401(토큰 무효)과 일시 장애를 구분할 수 있게 함:
```ts
export const refreshSession = async (token: string) => {
	const res = await fetch(`${WEBUI_API_BASE_URL}/auths/refresh`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		},
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
- `src/lib/stores/index.ts` — 타입 확장:
```ts
type Config = {
	features: {
		...
		jwt_expires_in?: string;
		...
	};
};

export type SessionUser = {
	id: string;
	email: string;
	name: string;
	role: string;
	profile_image_url: string;
	expires_at?: number;
	server_timestamp?: number; // 응답 생성 시점의 서버 시간 (시계 차이 보정용)
};
```

**재적용 가이드**
- 섹션 2(JTI)와 한 세트. refresh가 JTI를 회전시키므로 다중 탭 환경은 섹션 8의 BroadcastChannel 동기화와도 세트다.
- `refreshSession`의 `{ status, detail }` throw는 의도된 차이 — 공통 패턴(`err.detail` 문자열 throw)으로 되돌리면 401 감지 분기가 죽는다. 유지할 것.
- 업스트림 변화 접점: (1) 로그인 응답 조립이 `create_session_response` 공통 헬퍼에서 다시 개별화될 수 있음 — 그 경우 `server_timestamp`를 각 응답에 넣어야 함. (2) 쿠키 설정 옵션(`max_age` 처리 등)은 대상 버전의 `create_session_response` 쪽 코드를 복사해 맞출 것. (3) `get_app_config`의 features 구성(공개/인증 블록 구분)이 버전마다 바뀜 — `jwt_expires_in`은 인증 블록에 넣는다. (4) 권한 조회 시그니처(`get_permissions(user.id, await Config.get('user.permissions'), db=db)`)도 대상 버전에 맞출 것.

**관련 커밋**
- `23203ac6f` (백엔드), `673d247ed` (프론트 API/타입), `9131cfe00` (SessionUser.server_timestamp 타입 추가)

---

### 6. 토큰 저장 방식: `localStorage` → `sessionStorage` (프론트 전면 치환)

**목적/배경**
- 탭/브라우저 종료 시 토큰이 자동 소멸되도록 저장소를 `sessionStorage`로 이전(장기 토큰 탈취 표면 축소, 단일 세션 정책과 부합).

**동작 방식**
- 프론트 전반의 `localStorage.token` / `localStorage.getItem('token')` 참조를 `sessionStorage.*`로 치환. **현재 트리 실측: `src/` 내 `localStorage.token` 잔존 참조 0건, `sessionStorage.token` 계열 사용 파일 165개.**
- 소켓 인증(`src/routes/+layout.svelte`): `auth: { token: sessionStorage.token }`, `user-join` emit도 동일.
- 로그인 저장(`src/routes/auth/+page.svelte`): `setSessionUser`에서 `sessionStorage.token = sessionUser.token`, 토큰 쿼리파라미터 유입 경로에서 `sessionStorage.token = token`. (`redirectPath`는 여전히 localStorage — 의도된 유지.)
- 로그아웃/세션 무효 시에는 두 저장소 모두 정리: `localStorage.removeItem('token'); sessionStorage.removeItem('token');` (과거 잔존 토큰 정리 목적).

**변경 파일 및 핵심 내용**
- diff 기준 `-G "sessionStorage"` 검출 파일 176개(마이그레이션 문서 포함), 실제 코드 치환 165개 파일. 대표: `src/routes/+layout.svelte`, `src/routes/(app)/+layout.svelte`, `src/routes/auth/+page.svelte`, `src/lib/apis/**` 및 각 컴포넌트.

**재적용 가이드**
- 스크립트 일괄 치환 후 검증: `grep -rn "localStorage.token" src/` → 0건이어야 함(단, `localStorage.removeItem('token')`은 잔존 정리용으로 유지).
- OAuth 자동 리다이렉트 조건(`auth/+page.svelte`의 `!sessionStorage.token &&`)과 소켓 `user-join`, electron `token:update` relay 지점을 누락하지 말 것.
- 백엔드 httpOnly 쿠키 `token`은 별개로 계속 발급되므로 프론트 저장소 변경과 무관하게 동작.
- 부작용: 새 탭에서는 재로그인 필요(의도된 동작). 다중 탭 + JTI 단일 세션 경합은 섹션 8의 BroadcastChannel로 완화.

**관련 커밋**
- `3584a740c` (165개 파일 전면 치환), `673d247ed` (레이아웃/auth 페이지 마무리)

---

### 7. 세션 타임아웃 UI — 남은시간 배지, 수동 연장 버튼, SessionTimeoutModal

**목적/배경**
- 짧은 토큰 수명 하에서 사용자가 세션 만료를 인지하고 직접 연장할 수 있게 하는 UI. 만료 임박 시 경고 모달, 만료 시 자동 로그아웃.

**동작 방식** (`src/routes/(app)/+layout.svelte`)
- 상태: `lastRefresh`, `clockSkew`(클라-서버 시계 오차), `tokenDuration`(기본 3600초), `timeRemaining`, `isExpiringSoon`, `modalCountdown`, `showTimeoutModal`.
- `tokenDuration`은 onMount에서 `$config.features.jwt_expires_in`으로 1회 초기화(주석: "Runs once at mount (config is loaded by the root layout before this mounts)"), 이후 `$user.server_timestamp`(섹션 10)와 refresh 응답이 계속 갱신.
- 1초 주기 타이머(onMount에서 `timerInterval = setInterval(...)` 등록):
```js
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
if (diff <= warningThreshold) { ... showTimeoutModal = true; ... }
```
  배지 문구: `` timeRemaining = `로그아웃 ${m}분 ${s}초 남음` ``, `diff < 60`이면 `isExpiringSoon = true`(빨간색+pulse), 만료 시 `'만료됨'`.
- 배지 UI: 우상단 고정(`fixed top-4 right-36 z-[999]`), 수동 새로고침 버튼(ArrowPath, `on:click={onManualRefresh}`, **10초 쿨다운**, `만료됨`이면 비활성, `title="세션 연장 (10초 대기)"`).
- `logoutHandler()`: `userSignOut()`(서버 Redis 무효화 + JTI 제거) → 양쪽 저장소 토큰 삭제 → `user.set(null)` → `window.location.href = redirectUrl`(전체 리로드).
- `SessionTimeoutModal`(신규 45줄, `src/lib/components/layout/Overlay/SessionTimeoutModal.svelte`): props `show`/`countdown`, 이벤트 `extend`(→ `refreshSessionHelper`) / `logout`(→ `logoutHandler`). 문구 "보안을 위해 {countdown}초 후 자동 로그아웃됩니다." — 파일 전체를 그대로 복사하면 됨.
- 같은 파일에서 `ChangelogModal`은 import/렌더 모두 주석 처리, `showChangelog` 설정 블록 삭제(로그인 후 변경로그 팝업 제거). (`AgreementModal` 연결은 다른 파트 담당.)

**변경 파일 및 핵심 내용**
- `src/lib/components/layout/Overlay/SessionTimeoutModal.svelte` (신규)
- `src/routes/(app)/+layout.svelte` — import 추가(`refreshSession, userSignOut`, `onDestroy`, `SessionTimeoutModal`, `ArrowPath`), 상태/타이머/배지/모달/`logoutHandler`.

**재적용 가이드**
1. 섹션 5(refresh API + `server_timestamp` + `features.jwt_expires_in`)가 선행돼야 함.
2. 타이머 로직은 markup이 아니라 script 최상위 함수 + onMount 등록 구조 — 삽입 위치는 "onMount에서 keyboard shortcut 설정과 `await tick()` 사이" 및 script 상단 헬퍼 영역.
3. 배지 위치(`right-36`)는 업스트림 네브바 버튼과의 간섭을 피한 값 — 대상 버전 레이아웃에서 재확인.
4. 문구가 한국어 하드코딩(i18n 미사용). 다국어 필요 시 i18n 키로 교체.
5. 정리(teardown)는 `onDestroy` 사용(섹션 8 코드 참조) — async onMount의 반환 cleanup은 Svelte가 무시하므로 onMount return으로 옮기지 말 것.

**관련 커밋**
- `3584a740c` (SessionTimeoutModal 파일), `673d247ed` (레이아웃 통합)

---

### 8. 이벤트 구동 자동 갱신(슬라이딩 세션) + BroadcastChannel 탭 동기화

**목적/배경**
- 사용 중인 사용자는 타임아웃 모달을 보기 전에 토큰이 자동 연장되도록 함(모달은 갱신 실패 시 fallback).
- 0.6.43-fix2.1 말기의 "최근 60초 활동 윈도우 + 1초 타이머에서 `max(수명/2, 경고+20s)` 임계" 방식은 `16b045260`에서 **이벤트 구동 방식으로 단순화**됐다: 사용자 액션이 발생한 그 순간 잔여시간이 수명의 절반 이하면 갱신. 타이머는 만료 로그아웃/모달/배지만 담당.

**동작 방식** (`src/routes/(app)/+layout.svelte`)
- 활동 트리거 (현재 HEAD, **mousemove 없음** — 섹션 12):
```js
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
```
- 리스너 등록(onMount, BroadcastChannel 설정 직후):
```js
window.addEventListener('keydown', onUserActivity);
window.addEventListener('click', onUserActivity);
window.addEventListener('touchstart', onUserActivity);
// capture: true so scrolling inside nested containers (chat list, sidebar) counts too
window.addEventListener('scroll', onUserActivity, true);
```
- 스로틀(10초 간격, 폭주 방지 + 실패 시 재시도 간격):
```js
const MIN_AUTO_REFRESH_INTERVAL = 10 * 1000; // ms - minimum gap between auto refresh attempts (spaces out retries on failure)

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
```
- **동시 호출 합류(coalescing)**: 백엔드 refresh는 호출마다 JTI를 회전시키므로 병렬 refresh는 저장 토큰과 DB JTI를 어긋나게 할 수 있다. 공유 프로미스로 합류:
```js
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
```
- 토큰 채택(모든 갱신 경로 공용):
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
```
- **탭 간 토큰 동기화**: sessionStorage는 탭별 저장인데 JTI는 사용자당 1개 → 한 탭의 갱신이 다른 탭 토큰을 무효화한다. 갱신 성공 시 `session-token` 채널로 방송, 모든 탭이 채택(onMount):
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
- 정리(teardown):
```js
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
```

**변경 파일 및 핵심 내용**
- `src/routes/(app)/+layout.svelte` — 위 코드 전부 + 상단 상태 선언(`autoRefreshInFlight`, `lastAutoRefreshAttempt`, `timerInterval`, `sessionChannel`)
- `src/lib/apis/auths/index.ts` — 상태코드 보존형 `refreshSession`(섹션 5)이 401 분기의 전제조건

**재적용 가이드**
1. 섹션 7 위에 얹는 변경(7 → 8 순서). refresh API의 `{ status, detail }` throw(섹션 5)도 세트.
2. 갱신 임계가 `tokenDuration / 2`이므로 24h 토큰이면 잔여 12h 시점부터 사용자 액션 시 1회 갱신 — 서버 부하는 갱신당 JTI 업데이트 1회 수준.
3. **자동 갱신과 BroadcastChannel 탭 동기화는 반드시 세트로 이식**: 동기화가 없으면 "한 탭의 갱신 → 다른 탭 401 → 그 탭의 만료 로그아웃이 쿠키(최신 토큰)로 signout을 호출해 활성 탭까지 로그아웃"되는 연쇄가 일상적으로 발생한다.
4. 리스너를 새로 추가/삭제할 때 `onDestroy`의 해제 목록을 반드시 같은 시그니처(특히 scroll의 `true`)로 맞출 것.

**관련 커밋**
- `673d247ed` (활동 윈도우 방식 1차 이식) → `16b045260` refactor: 토큰 자동 갱신을 이벤트 구동 방식으로 변경 → `e335d4095` (mousemove 제외, 섹션 12)

---

### 9. 전역 401 인터셉터·만료 로그아웃 — 업스트림 병합 + 커스텀 정책

**목적/배경**
- 0.10.2 업스트림이 자체적으로 401 fetch 인터셉터와 15초 주기 `checkTokenExpiry`를 도입했다. 커스텀은 이를 **대체하지 않고 그 위에 정책만 병합**한다: sessionStorage 정리, 전체 리로드 리다이렉트, `TOKEN_EXPIRY_BUFFER=0`.

**동작 방식** (`src/routes/+layout.svelte`)
- 업스트림 유지: `window.fetch` 래핑(백엔드 origin + `authorization` 헤더가 있는 요청의 401만, `isCurrentSessionUnauthorized`로 `GET /auths/` 재확인 후 발동), `redirectToAuthAfterUnauthorized`, 15초 `tokenTimer = setInterval(checkTokenExpiry, 15000)`.
- 커스텀 변경점:
  - `const TOKEN_EXPIRY_BUFFER = 0; // seconds` (업스트림 `60`) — 만료 60초 전 선제 로그아웃 대신 정확히 만료 시점 처리. 선제 갱신/경고는 (app) 레이아웃(섹션 7~8)이 담당.
  - `redirectToAuthAfterUnauthorized`에 `sessionStorage.removeItem('token');` 추가, `goto(...)` → 전체 리로드:
```js
isAuthRedirectInProgress = true;
user.set(null);
localStorage.removeItem('token');
sessionStorage.removeItem('token');
toast.error($i18n.t('Session expired. Please sign in again.'));

// Force clean redirect (full reload) to clear all in-memory state
const currentPath = `${window.location.pathname}${window.location.search}`;
window.location.href = `/auth?redirect=${encodeURIComponent(currentPath)}`;
```
  - `checkTokenExpiry`의 로그아웃 분기에도 `sessionStorage.removeItem('token');` 추가.
  - onMount의 무효 세션 리다이렉트도 `goto` → `window.location.href = \`/auth?redirect=${encodedUrl}\``로 변경 + sessionStorage 정리.
  - `isCurrentSessionUnauthorized`의 Authorization 헤더가 `sessionStorage.token` 사용(섹션 6).

**변경 파일 및 핵심 내용**
- `src/routes/+layout.svelte` (위 전부; `unwrappedFetch`와 서버 401 확인은 섹션 10)

**재적용 가이드**
- **업스트림 인터셉터가 이미 있으므로 0.6.43식 인터셉터를 새로 넣지 말 것** — diff를 떠서 위 변경점만 병합.
- `TOKEN_EXPIRY_BUFFER=0`은 (app) 레이아웃 타이머와 세트 — 버퍼 60초를 유지하면 경고 모달이 뜨기 전에 루트 타이머가 먼저 로그아웃시킨다.
- 업스트림 변화 접점: 인터셉터 구현(헤더 판별 함수, 재확인 호출)이 버전마다 다듬어지고 있으므로, "401 확정 시 정리·리다이렉트 정책" 부분만 우리 정책으로 유지하면 된다.

**관련 커밋**
- `673d247ed` (병합 + BUFFER 60→0), `3584a740c` (sessionStorage 치환)

---

### 10. [신규 2026-07-14] checkTokenExpiry: 로그아웃 전 서버 401 확인 (시계차 수정 1/3)

**목적/배경**
- `expires_at`은 **서버 시계** 기준인데, 루트 레이아웃의 `checkTokenExpiry`는 브라우저 시계(`Date.now()`)와 직접 비교한다. 서버 시계가 브라우저보다 느리면(운영 서버에서 약 3분 실측) 아직 유효한 세션을 만료로 오판해 **로그인 직후 로그아웃**되는 문제가 있었다.
- 수정: 로컬 판정은 "의심"으로만 취급하고, 로그아웃 전에 서버에 실제 만료 여부(401)를 확인한다.

**동작 방식** (`src/routes/+layout.svelte`)
- 원본 fetch 보관: 401 인터셉터(래퍼)를 거치면 확인 요청 자체가 리다이렉트를 유발할 수 있으므로, 래핑 전 원본을 `unwrappedFetch`에 보관해 확인용으로 사용.
```js
const TOKEN_EXPIRY_BUFFER = 0; // seconds
let unwrappedFetch = null; // onMount에서 씌우는 401 리다이렉트 래퍼를 거치지 않는 원본 fetch
```
```js
onMount(async () => {
	const originalFetch = window.fetch.bind(window);
	unwrappedFetch = originalFetch;
	window.fetch = async (input, init) => { ... };
```
- `checkTokenExpiry` 내부, 만료 판정 직후:
```js
if (now >= exp - TOKEN_EXPIRY_BUFFER) {
	// expires_at은 서버 시계 기준이므로, 서버-클라이언트 시계 차이 때문에
	// 유효한 세션이 끊기지 않도록 로그아웃 전에 서버에 실제 만료 여부를 확인한다.
	if (!(await isCurrentSessionUnauthorized(unwrappedFetch ?? window.fetch))) {
		return;
	}

	const res = await userSignOut();
	user.set(null);
	localStorage.removeItem('token');
	sessionStorage.removeItem('token');

	location.href = res?.redirect_url ?? '/auth';
}
```
- `isCurrentSessionUnauthorized`는 업스트림 함수 재사용(`GET /auths/`가 401일 때만 true; 네트워크 오류는 false → 로그아웃 안 함).

**변경 파일 및 핵심 내용**
- `src/routes/+layout.svelte` — `unwrappedFetch` 선언, onMount 대입, `checkTokenExpiry` 가드 3줄.

**재적용 가이드**
- 삽입 위치: (1) `TOKEN_EXPIRY_BUFFER` 상수 바로 아래에 `unwrappedFetch` 선언, (2) onMount에서 `window.fetch`를 래핑하기 **직전** `unwrappedFetch = originalFetch;`, (3) `checkTokenExpiry`의 만료 분기 첫 줄에 서버 확인 가드.
- 업스트림 변화 접점: `isCurrentSessionUnauthorized` 시그니처(originalFetch 인자)가 바뀌면 가드 호출부만 맞추면 된다. 업스트림이 자체적으로 서버 재확인을 넣으면 이 커스텀은 불필요해질 수 있음 — 먼저 확인할 것.

**관련 커밋**
- `92c87cf7e` fix: 서버-클라이언트 시계 차이로 로그인 직후 로그아웃되는 문제 수정 (package.json 버전 0.10.2-fix1 포함)

---

### 11. [신규 2026-07-14] 앱 진입 시 clockSkew/tokenDuration 즉시 초기화 (시계차 수정 2/3)

**목적/배경**
- (app) 레이아웃의 1초 만료 타이머는 `clockSkew`로 서버 시간을 재구성해 판정하는데, `clockSkew`가 **첫 토큰 갱신 전까지 0**이었다. 서버 시계가 브라우저보다 느리면(예: 3분) 타이머가 만료로 오판해 로그인 직후 즉시 로그아웃되는 버그.
- 로그인/세션 응답(`create_session_response`/`get_session_user`)에 이미 포함된 `server_timestamp`(섹션 5)로 onMount에서 skew와 tokenDuration을 바로 보정한다.

**동작 방식** (`src/routes/(app)/+layout.svelte`)
- onMount 최상단, `$user` 가드(`if ($user === undefined || $user === null) { await goto('/auth'); ... }`) 직후에 삽입:
```js
// 로그인/세션 응답의 server_timestamp로 시계 차이를 즉시 보정한다.
// 첫 토큰 갱신 전까지 clockSkew=0이면, 서버 시계가 브라우저보다 느릴 때
// 아래 1초 타이머가 만료로 오판해 로그인 직후 바로 로그아웃되는 문제가 있었다.
if ($user?.server_timestamp) {
	calculateClockSkew($user.server_timestamp);
	if ($user?.expires_at) {
		tokenDuration = $user.expires_at - $user.server_timestamp;
	}
}
```
- `calculateClockSkew`(공용 헬퍼):
```js
const calculateClockSkew = (serverTimestamp: number) => {
	if (serverTimestamp) {
		const now = Math.floor(Date.now() / 1000);
		clockSkew = now - serverTimestamp;
		console.log('Clock skew:', clockSkew);
	}
};
```
- `$user`에 `server_timestamp`가 실리는 경로: 루트 레이아웃이 `getSessionUser()` 응답을 `user.set(...)`하고, 로그인 페이지가 `signin` 응답을 `user.set(sessionUser)`한다 — 백엔드가 두 응답 모두에 `server_timestamp`를 포함(섹션 5)하므로 별도 프론트 배선은 불필요.
- 타입: `src/lib/stores/index.ts`의 `SessionUser`에 `server_timestamp?: number;` 추가(섹션 5 인용 참조).

**재적용 가이드**
- 삽입 위치는 "onMount에서 `$user` null 가드 직후, `clearChatInputStorage()` 등 초기화 작업 이전".
- 전제: 백엔드 세션 응답의 `server_timestamp`(섹션 5). 이것이 빠지면 이 코드는 조용히 no-op이 되어 버그가 재현된다 — 이식 후 콘솔의 `Clock skew:` 로그로 실제 보정되는지 확인할 것.
- 업스트림 변화 접점: (app) 레이아웃 onMount의 초기화 순서. `$user` 스토어에 세션 응답 원본이 그대로 들어가는 구조가 바뀌면(별도 매핑 도입 등) `server_timestamp` 필드가 유실되지 않는지 확인.

**관련 커밋**
- `9131cfe00` fix: 앱 진입 시 clockSkew를 세션 응답의 server_timestamp로 즉시 초기화

---

### 12. [신규 2026-07-14] mousemove를 세션 갱신 트리거에서 제외 (시계차 수정 3/3)

**목적/배경**
- 마우스 포인터 이동은 수동적 동작(모니터 앞에 있지 않아도 발생 가능, 고빈도)이라 "실제 사용"의 근거로 약하다. 의도적인 조작(keydown, click, touchstart, scroll)만 자동 갱신 트리거로 사용하도록 정리.

**동작 방식** (`src/routes/(app)/+layout.svelte`)
- `window.addEventListener('mousemove', onUserActivity)` 등록·해제 라인 삭제. 현재 HEAD의 등록/해제 목록은 섹션 8 인용과 같이 `keydown/click/touchstart/scroll(capture)` 4종.
- `onUserActivity` 상단 주석에 정책 명문화(섹션 8 인용 참조): "마우스 포인터 이동(mousemove)은 수동적 동작이라 갱신 트리거에서 제외."

**재적용 가이드**
- 재이식 시 처음부터 mousemove 없이 4종만 등록할 것. 등록과 `onDestroy` 해제 목록을 짝맞출 것.

**관련 커밋**
- `e335d4095` refac: 마우스 포인터 이동을 세션 갱신 트리거에서 제외

---

### 13. 로그인 페이지 흐름 정리

**목적/배경**
- sessionStorage 이전·JTI 정책에 맞춘 로그인 경로 정리 + 잘못된 리다이렉트 수정.

**동작 방식 / 변경 파일** (`src/routes/auth/+page.svelte`)
- `setSessionUser`: `sessionStorage.token = sessionUser.token` 저장(업스트림은 localStorage).
- 토큰 쿼리파라미터 유입 경로: `sessionStorage.token = token;` 후 `setSessionUser(...)`.
- onMount 리다이렉트 조건 수정:
```js
const redirectPath = $page.url.searchParams.get('redirect');
if ($user) {
	goto(redirectPath || '/');
}
```
(업스트림은 `if ($user !== undefined)` — user가 `null`인 미로그인 상태에서도 리다이렉트되는 문제 수정.)
- OAuth 단일 프로바이더 자동 리다이렉트 조건도 `!sessionStorage.token &&`로 치환.
- 참고: `redirectPath` 저장은 여전히 `localStorage`(토큰이 아니므로 의도된 유지).

**재적용 가이드**
- 로그아웃 지점이 4곳(UserMenu / (app) 레이아웃 `logoutHandler` / 401 인터셉터 `redirectToAuthAfterUnauthorized` / `checkTokenExpiry`)이므로, 전부 "양쪽 저장소 삭제 + 전체 리로드 리다이렉트" 패턴으로 일관되게 맞출 것.

**관련 커밋**
- `3584a740c`, `673d247ed`

---

### 14. [설계 원칙] 시간 검증은 서버에서만 — 프론트는 보정·표시 전용

**원칙** (CLAUDE.md에 명문화, `e81eedfdd`)
- **토큰/세션 등 시간 검증은 서버에서만 한다.** 프론트엔드에서 브라우저 시계로 만료를 직접 판정하는 코드를 넣지 말 것.
- 프론트의 시간 표시/타이머는 세션 응답의 `server_timestamp`로 `clockSkew`를 보정해 **서버 시간 기준으로 계산**한다 (섹션 7·8·11).
- 로그아웃 같은 **최종 판정은 서버 응답(401)을 확인한 뒤** 수행한다 (섹션 9·10: 인터셉터의 `isCurrentSessionUnauthorized` 재확인, `checkTokenExpiry`의 서버 확인 가드).
- 서버 시계는 NTP 동기화됐지만(2026-07-14 적용), **동기화 여부와 무관하게 시계 차이를 전제로 코드를 작성할 것** — 클라이언트(브라우저) 시계는 언제든 어긋날 수 있다.

**재적용 가이드**
- 미래 버전 이식 시 새로 생긴 프론트 코드 중 `Date.now()`/`new Date()`와 `expires_at`을 직접 비교해 로그아웃·차단을 결정하는 지점이 있는지 검색(`grep -rn "expires_at" src/`)하고, 발견되면 (a) clockSkew 보정 또는 (b) 서버 401 확인 가드 중 하나를 적용할 것.

**관련 커밋**
- `92c87cf7e`, `9131cfe00`, `e335d4095`, `e81eedfdd` (CLAUDE.md 원칙 명문화)

---

# 파트: 백엔드 보안 / 기능 토글 / 문서 파싱 / DB (브랜치 `0.10.2-fix1`)

기준: 업스트림 v0.10.2(커밋 `ecd48e2f7`) 대비 `git diff ecd48e2f7..HEAD`. 모든 코드 인용과 삽입 위치(줄 번호)는 **현재 HEAD 트리에서 실측**한 것이다. 이 파트의 백엔드 변경 대부분은 이식 커밋 `23203ac6f`(feat: 백엔드 커스텀 이식 0.6.43-fix2.1 → 0.10.2) 하나에 들어 있고, 그 외에 `75d2a4ed7`(alembic stamp 교정), `82782b0e3`(start.sh CWD 수정), `5560559e1`(USE_CUDA 원복)이 있다.

담당 범위: `constants.py`, `env.py`, `config.py`(JWT 이외), `main.py`(인증 features 이외), `routers/ollama.py·openai.py·users.py·files.py`, `models/chats.py`, `retrieval/loaders/main.py`, `backend/start.sh`, `migrations/env.py`, `Dockerfile`, 비밀번호 정책(`utils/auth.py`의 `validate_password`). JTI 단일 세션·refresh·`server_timestamp`·`JWT_EXPIRES_IN`은 인증 파트 문서 담당이며 여기서는 경계만 표시한다.

**0.10.2 이식에서 달라진 큰 전제 (0.6.43 문서 대비)**
- 0.10.2는 `PersistentConfig` 클래스가 없다. 설정은 `config.py`의 평범한 env 읽기 + `DEFAULT_CONFIG` 딕셔너리(키 → 기본값) + 런타임 `await Config.get("키")` 비동기 조회 구조다. 0.6.43 문서의 "PersistentConfig 추가" 지침은 전부 이 구조로 번역해서 적용됐다.
- DB 계층이 비동기(AsyncSession)로 바뀌어 `models/chats.py`의 커스텀 메서드도 async로 재작성됐다.
- `requirements.txt` / `pyproject.toml` 변경은 **없다**. 파싱 의존성(pyhwp 등)은 Dockerfile RUN 레이어로만 추가된다(§11).

---

### 1. 외부 API(Ollama/OpenAI) 오류 응답 마스킹 및 연결검증 400 통일

**목적/배경**
- 외부 LLM 서버(Ollama/OpenAI 호환/Anthropic)의 원본 오류 본문(내부 URL, 키 관련 힌트, 업스트림 상세 오류)이 클라이언트에 그대로 전달되는 정보 노출을 차단. 상세 내용은 서버 로그에만 남기고 클라이언트에는 고정 문구 `"An error occurred. Please contact the administrator."`만 반환한다.
- 연결 검증(verify) 엔드포인트의 실패 응답은 원본 상태코드 대신 400으로 통일해 내부 구성 유추를 어렵게 한다.

**동작 방식**
- 오류 시 `log.error(...)` / `log.exception(...)`으로 원본 기록 → 응답 본문은 `{"detail": "An error occurred. Please contact the administrator."}` (상태코드는 채팅/임베딩/프록시 경로에서는 원본 `r.status` 유지, verify 경로에서는 400 고정).
- 0.10.2 업스트림은 오류 시 `publish_model_provider_request_failed(..., upstream_error=...)` 이벤트를 먼저 발행하는데, 이 호출은 그대로 두고 **클라이언트로 나가는 응답만** 교체했다.

**변경 파일 및 핵심 내용 (현재 트리 실측)**

`backend/open_webui/routers/ollama.py`
- `send_request()` (0.6.43의 `send_post_request`가 0.10.2에서 개명됨) 내 3곳:
  - 145행 부근: `if 'error' in res:` → `log.error(f'Ollama Error: {res["error"]}')` 후 `HTTPException(status_code=r.status, detail='An error occurred. Please contact the administrator.')`
  - 파싱 실패 분기: `detail=ERROR_MESSAGES.SERVER_CONNECTION_ERROR` → 고정 문구로 교체
  - 함수 말미 `except Exception`: `log.error(f'Ollama: {e}')` 추가 후 `detail='An error occurred. ...'` (기존은 `f'Ollama: {e}'`를 그대로 노출)
- `verify_connection()` (278행 부근):
  - `raise Exception(detail)` → `raise HTTPException(status_code=400, detail=detail)` (detail은 `f'External Error: {res["error"]}'` 유지, 상태코드만 400)
  - `except HTTPException: raise` 추가 (위 400이 아래 except에 삼켜지지 않도록)
  - `aiohttp.ClientError` → 500에서 **400** + `ERROR_MESSAGES.SERVER_CONNECTION_ERROR`(한글화됨, §4)
  - 최종 `except Exception` → 500 + `f'Unexpected error: {exc}'`에서 **400 + 고정 문구**로 교체

`backend/open_webui/routers/openai.py`
- `speech()` (~408행): 외부 응답에서 detail을 추출하던 블록 전체 삭제 → `HTTPException(status_code=r.status if r else 500, detail='An error occurred. ...')`
- `verify_connection()` (~753행, ~780행): OpenAI 호환 2개 분기 모두 `JSONResponse/PlainTextResponse(status_code=r.status → 400, content=response_data)` — **본문은 그대로 전달하고 상태코드만 400 고정**(0.6.43과 동일한 트레이드오프). Anthropic 분기(0.10.2 신규)는 `HTTPException(500 → 400)` 2곳. try 블록 뒤에 `except HTTPException: raise` 추가.
- `generate_chat_completion()` (~1285행): 비스트리밍 오류 2곳(`error_json` 반환, `json.JSONDecodeError` 분기) 모두 `content={'detail': 'An error occurred. ...'}` 로 교체. SSE 아닌 응답의 `r.status >= 400` 분기(~1330행)는 `log.error(f'OpenAI Error ({r.status}): {response}')` 후 detail 고정 문구. 함수 말미 `HTTPException`의 `ERROR_MESSAGES.SERVER_CONNECTION_ERROR` → 고정 문구.
- `embeddings()` (~1443행), `responses()` (~1571행, **0.10.2 신규 엔드포인트 — 이번 이식에서 새로 적용된 지점**), `proxy()` (~1694행): 동일 패턴 — 오류 본문을 `log.error` 후 `{'detail': 'An error occurred. ...'}` 로 교체, 말미 `except Exception`의 detail도 고정 문구.

**재적용 가이드**
1. 원칙은 "클라이언트로 나가는 detail/본문 지점을 전수 조사해 로그+고정 문구로 교체". 미래 버전에서 함수 이름/구조가 또 바뀔 수 있으므로(0.6.43→0.10.2에서 이미 `send_post_request`→`send_request`, `responses()` 신설) diff 라인이 아니라 `JSONResponse(status_code=r.status, content=...)`·`PlainTextResponse`·`detail=` 패턴을 grep해서 찾을 것: `grep -n "upstream_error\|status_code=r.status" routers/openai.py routers/ollama.py`.
2. 새 엔드포인트가 추가되면(0.10.2의 `responses()`처럼) 같은 원칙을 신규 적용해야 한다.
3. verify 400 통일 시 openai 쪽은 본문 미마스킹(관리자용 연결 테스트 편의)이라는 기존 정책을 유지할지 함께 결정.
4. 고정 문구는 영어 하드코딩(한글화 대상 아님) — 프런트 `Error.svelte` 축약 표시(프런트 파트 문서)와 세트.

**관련 커밋**: `23203ac6f`

---

### 2. 파일 업로드 확장자 오류 메시지 은닉 (files.py)

**목적/배경**
- 허용 확장자 외 파일 업로드 시 `File type {ext} is not allowed`처럼 서버 설정을 유추할 수 있는 메시지가 노출되던 것을 고정 한글 문구로 교체.

**동작 방식**
- 확장자 불허 시 400 + `ERROR_MESSAGES.FILE_NOT_SUPPORTED`("지원하지 않는 파일 형식입니다.", §4의 한글화 상수).

**변경 파일 및 핵심 내용**
- `backend/open_webui/routers/files.py` `upload_file_handler()` 318~324행:
```python
if file_extension not in allowed_file_extensions:
    # Do not echo the extension/allowlist back to the client
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=ERROR_MESSAGES.FILE_NOT_SUPPORTED,
    )
```

**0.6.43 대비 소멸 항목**: 0.6.43 커스텀이던 `except HTTPException: raise`(내부 400이 바깥 except에 뭉개지는 문제)는 **업스트림 0.10.2에 이미 반영**되어(현재 429행 `except HTTPException as e:`) 별도 이식이 불필요해졌다. 이번 diff는 detail 한 줄 교체가 전부다.

**재적용 가이드**
1. `constants.py`의 `FILE_NOT_SUPPORTED` 한글화(§4)가 선행돼야 함.
2. 미래 버전에서 확장자 검사 지점(`allowed_extensions` grep)만 찾아 detail을 교체.

**관련 커밋**: `23203ac6f`

---

### 3. DISABLE_ADMIN — 관리자 기능 전면 차단 게이트

**목적/배경**
- role=admin 계정이 있어도 서버 수준에서 관리자 API 전체를 403으로 차단하는 배포 스위치.

**동작 방식**
- env `DISABLE_ADMIN`(기본 `False`, 재시작 필요·DB config 아님) → `get_admin_user` 의존성 최상단에서 403 → `Depends(get_admin_user)`를 쓰는 모든 관리자 API 차단.
- `/api/config` 응답 `features.disable_admin`으로 프런트 노출 → admin 레이아웃 진입 차단(프런트 파트 문서).

**변경 파일 및 핵심 내용 (현재 트리 실측)**
- `backend/open_webui/env.py` 732행 (`CUSTOM_API_KEY_HEADER` 선언 직후, `ENABLE_PASSWORD_VALIDATION` 직전):
```python
# Block every admin API (get_admin_user dependency) at the server level
DISABLE_ADMIN = os.getenv('DISABLE_ADMIN', 'False').lower() == 'true'
```
- `backend/open_webui/utils/auth.py` 558~562행 (env import 목록에 `DISABLE_ADMIN` 추가):
```python
def get_admin_user(user=Depends(get_current_user)):
    if DISABLE_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ERROR_MESSAGES.ACCESS_PROHIBITED,
        )
```
- `backend/open_webui/main.py` 82행(env import), 1943행 — `get_app_config()`의 features 중 **비인증 사용자에게도 내려가는 공통 블록**(`'enable_websocket'` 다음, 인증 사용자 전용 `**({...})` 블록 직전):
```python
'disable_admin': DISABLE_ADMIN,
```

**0.6.43 대비 소멸 항목**: 0.6.43 커스텀에 있던 "`enable_admin_export`를 공통 블록에 중복 노출"은 **이식되지 않았다**. 0.10.2 현재 `enable_admin_export`는 업스트림 그대로 인증 사용자 블록(main.py 1979행)에만 존재한다. 프런트가 비로그인 상태에서 이 값을 참조하지 않는 한 문제 없음.

**재적용 가이드**
1. env.py → utils/auth.py → main.py 순. `disable_admin`은 반드시 비인증 공통 블록에 넣어야 로그인 화면부터 프런트 분기가 동작한다.
2. 프런트 차단은 우회 가능하므로 `get_admin_user` 게이트가 본체. `get_admin_user`를 거치지 않는 관리자성 엔드포인트가 새 버전에 생겼는지 확인할 것.
3. `DISABLE_ADMIN=true`는 최초 관리자 온보딩까지 막으므로 초기 설정 완료 후에만 켤 것.

**관련 커밋**: `23203ac6f`

---

### 4. 백엔드 시스템/오류 메시지 한글화 (constants.py)

**목적/배경**
- 백엔드가 직접 내려주는 오류 메시지(프런트 토스트로 그대로 노출)를 한글화. 원문 영어를 각 항목 **바로 위 주석**으로 보존해 업스트림 diff 대조가 가능하게 하는 컨벤션 유지.

**동작 방식 / 변경 파일 및 핵심 내용**
- `backend/open_webui/constants.py` — `_ERRNO_MESSAGES` 딕셔너리(0.10.2 신규 구조), `_error_message()` 헬퍼, `MESSAGES`, `WEBHOOK_MESSAGES`, `ERROR_MESSAGES` Enum의 사용자 노출 문자열 전체를 한국어로 교체(+257줄 규모). 0.10.2에서 새로 생긴 메시지(AUTOMATION_*, FEATURE_DISABLED, INPUT_TOO_LONG, REQUIRED_FIELD_EMPTY, OAUTH_NOT_CONFIGURED, USERNAME_TAKEN, INCORRECT_PASSWORD 등)도 모두 번역됐다. 대표 예:
```python
# The email or password provided is incorrect. Please check for typos and try logging in again.
INVALID_CRED = '이메일 또는 비밀번호가 올바르지 않습니다. 확인 후 다시 시도해주세요.'
# Oops! It seems like the file format you're trying to upload is not supported. ...
FILE_NOT_SUPPORTED = '지원하지 않는 파일 형식입니다.'   # 정보 노출 축소 겸함
# Open WebUI: Server Connection Error
SERVER_CONNECTION_ERROR = '서버 연결 오류가 발생했습니다. 관리자에게 문의하세요.'
```
- 비밀번호 정책 신규 상수 6종(업스트림에 없음, 현재 163~169행) — §5에서 사용:
```python
# Password validation errors
PASSWORD_TOO_SHORT = '비밀번호는 최소 8자 이상이어야 합니다.'
PASSWORD_MISSING_CHARS = '비밀번호는 영문자, 숫자, 특수문자를 각각 1개 이상 포함해야 합니다.'
PASSWORD_SEQUENTIAL = '비밀번호에 4자 이상의 연속된 문자나 숫자를 사용할 수 없습니다 (예: 1234, abcd).'
PASSWORD_REPETITIVE = '비밀번호에 4자 이상의 반복된 문자나 숫자를 사용할 수 없습니다 (예: 1111, aaaa).'
PASSWORD_CONTAINS_ACCOUNT_INFO = '비밀번호에 이메일 아이디나 이름을 포함할 수 없습니다.'
PASSWORD_COMMON = '비밀번호로 사용할 수 없는 쉬운 문자열이 포함되어 있습니다.'
```
- `TASKS` Enum 등 내부 식별자는 건드리지 않는다.

**재적용 가이드**
1. 미래 버전에서 메시지 항목이 늘었을 가능성이 매우 높다. **기계적 3-way merge 대신, 새 업스트림 constants.py를 기준으로 항목별 재번역**하고 원문 주석 컨벤션을 유지하라. 현재 파일의 주석이 업스트림 원문 그대로이므로 `git diff` 시 어떤 항목이 신규인지 바로 식별 가능하다.
2. PASSWORD_* 6종은 §5와 반드시 세트로 적용.
3. 메시지 값을 문자열 매칭에 쓰는 코드가 새로 생겼는지 확인(현재까지 문제 없음).

**관련 커밋**: `23203ac6f`

---

### 5. 비밀번호 정책 강화 (규칙 기반 검증 + 블랙리스트 + 계정정보 검사)

**목적/배경**
- 업스트림의 단일 정규식 검사(`PASSWORD_VALIDATION_REGEX_PATTERN`)를 규칙 기반 다단계 검사로 교체. 길이/복잡도/연속·반복 문자 금지/블랙리스트/계정정보 포함 금지를 규칙별 한글 메시지(§4)와 함께 적용.

**동작 방식**
- 게이트: `ENABLE_PASSWORD_VALIDATION`(업스트림 기존 env, 기본 False)이 켜져 있을 때만 규칙 검사. bcrypt 72바이트 상한 검사는 항상 수행(업스트림 유지 — 0.10.2에서는 `PASSWORD_HASH_ALGORITHM == 'bcrypt'` 조건부).
- 신규 env `PASSWORD_BLACKLIST`(콤마 구분, 기본 `password,123456,admin,test`).
- 검사 순서: ① 최소 8자 ② 영문+숫자+특수문자 각 1개 ③ 4자 이상 정/역방향 연속(alnum만, ord() 비교) ④ 동일문자 4연속 ⑤ 블랙리스트 부분문자열(대소문자 무시) ⑥ `user_data`의 email 로컬파트·name 포함 금지.
- `PASSWORD_VALIDATION_REGEX_PATTERN`/`PASSWORD_VALIDATION_HINT`는 env.py와 import에 잔존하지만 **validate_password에서 더 이상 사용되지 않음**.

**변경 파일 및 핵심 내용 (현재 트리 실측)**
- `backend/open_webui/env.py` 751~756행 (`PASSWORD_VALIDATION_HINT` 뒤):
```python
# Comma-separated list of strings that may not appear in passwords
PASSWORD_BLACKLIST = [
    item.strip()
    for item in os.getenv('PASSWORD_BLACKLIST', 'password,123456,admin,test').split(',')
    if item.strip()
]
```
- `backend/open_webui/utils/auth.py` 179행 `validate_password(password: str, user_data: Optional[Dict[str, str]] = None) -> bool` — 본문 전체 교체(약 179~241행). 상단에 `import re`, `from typing import Dict` 추가, env import에 `PASSWORD_BLACKLIST` 추가. 규칙 ③은 `ord(password[i+1]) == ord(password[i]) + 1 ...` 4연속 비교 후 `password[i:i+4].isalnum()`일 때만 거부, ⑥은 `email.split('@')[0] in password.lower()` / `name in password.lower()`.
- `backend/open_webui/constants.py` — PASSWORD_* 6종(§4).
- 호출부 4곳 — 전부 `user_data` 전달:
  - `routers/auths.py` 449행 `update_password`: `validate_password(form_data.new_password, {'email': session_user.email, 'name': session_user.name})` (0.10.2 업스트림은 이미 `new_password`를 검증하므로 0.6.43의 "검증 대상 버그 수정"은 소멸)
  - `routers/auths.py` 920행 `signup`: `{'email': form_data.email, 'name': form_data.name}`
  - `routers/auths.py` 1115행 `add_user`: `{'email': form_data.email, 'name': form_data.name}` — **0.6.43의 알려진 버그(관리자 본인 정보와 대조)가 이번 이식에서 form_data 기준으로 수정됨**
  - `routers/users.py` 642행 `update_user_by_id`: `{'email': user.email, 'name': user.name}` — 여기의 `user`는 `Users.get_user_by_id(user_id)`로 조회한 **대상 사용자**(요청자 아님). 이 호출부는 0.10.2에서 새로 생긴 것으로, 이번 이식에서 user_data 전달을 신규 적용했다.

**재적용 가이드**
1. 순서: constants.py → env.py → utils/auth.py → 호출부. 호출부는 `grep -rn "validate_password(" backend/`로 전수 확인 후 각각 대상 사용자의 email/name을 전달(LDAP/OAuth 경로에 새 호출부가 생겼는지 확인).
2. 배포 env: `ENABLE_PASSWORD_VALIDATION=true`, `PASSWORD_BLACKLIST=...` (compose 파트 문서 참조).
3. 1~2자 이름 사용자는 규칙 ⑥에서 오탐 가능 — 정책 검토 포인트(0.6.43 문서와 동일).
4. `utils/auth.py`는 JTI 검증(같은 파일 462행)과 겹치므로 인증 파트와 병합 순서 조율.

**관련 커밋**: `23203ac6f`

---

### 6. 기능 토글 3종 (ENABLE_IMAGE_CAPTURE / ENABLE_WEBPAGE_ATTACHMENT / ENABLE_USER_PERSONAL_INFO)

**목적/배경**
- 화면 캡처 첨부·외부 웹페이지 첨부·계정 개인정보(성별/생년월일) UI를 서버 설정으로 끄는 토글. 세 플래그 모두 **UI(진입점) 숨김 전용**이며 백엔드 API 차단은 없다(0.6.43과 동일).

**동작 방식**
- env(기본 전부 `True`) → `DEFAULT_CONFIG`의 `ui.enable_image_capture` / `ui.enable_webpage_attachment` / `ui.enable_user_personal_info` 키 → `/api/config`의 **인증 사용자 전용** features로 노출 → 프런트 `$config.features.*` 조건부 렌더링(프런트 파트 문서).
- 0.10.2의 config 시스템 특성상 DB `config`에 해당 키가 저장돼 있으면 DB 값이 env보다 우선한다(0.6.43 PersistentConfig와 동일한 주의점). **실운영 DB(0.6.43-fix2.1 이관본)에는 세 행이 이미 존재하므로 env 변경은 무시된다 — 값 변경은 `UPDATE config SET value = 'false'::json WHERE key = '<키>'`로 한다.** 서두 "이식 시 반드시 지킬 것" 3번 항목 참조.

**변경 파일 및 핵심 내용 (현재 트리 실측)**
- `backend/open_webui/config.py` 1998~2002행 (`ENABLE_NOTES` 직후):
```python
ENABLE_IMAGE_CAPTURE = os.getenv('ENABLE_IMAGE_CAPTURE', 'True').lower() == 'true'
ENABLE_WEBPAGE_ATTACHMENT = os.getenv('ENABLE_WEBPAGE_ATTACHMENT', 'True').lower() == 'true'
ENABLE_USER_PERSONAL_INFO = os.getenv('ENABLE_USER_PERSONAL_INFO', 'True').lower() == 'true'
```
- `backend/open_webui/config.py` 3034~3036행 — `DEFAULT_CONFIG`에 (`'notes.enable'` 다음):
```python
'ui.enable_image_capture': ENABLE_IMAGE_CAPTURE,
'ui.enable_webpage_attachment': ENABLE_WEBPAGE_ATTACHMENT,
'ui.enable_user_personal_info': ENABLE_USER_PERSONAL_INFO,
```
- `backend/open_webui/main.py`:
  - 1887~1889행: `get_app_config()`가 일괄 조회하는 config 키 리스트에 `'ui.enable_image_capture'`, `'ui.enable_webpage_attachment'`, `'ui.enable_user_personal_info'` 추가 (`'notes.enable'` 다음; 같은 자리에 인증 파트 소관 `'auth.jwt_expiry'`도 추가돼 있음).
  - 1960~1962행: features의 인증 사용자 블록(`'enable_notes'` 다음):
```python
'enable_image_capture': config.get('ui.enable_image_capture'),
'enable_webpage_attachment': config.get('ui.enable_webpage_attachment'),
'enable_user_personal_info': config.get('ui.enable_user_personal_info'),
```

**재적용 가이드**
1. config.py(env 읽기 + DEFAULT_CONFIG) → main.py(키 리스트 + features) → 프런트 순.
2. 미인증 `/api/config` 응답에는 키가 없고 프런트는 `?? true` 폴백이므로 "플래그 부재 = 기능 노출". 끄려면 반드시 `false`가 내려가야 한다.
3. 백엔드 web-loader/업로드/프로필 API는 차단하지 않는다 — 보안 목적이면 백엔드 차단 추가를 검토(현재 미구현, 0.6.43과 동일).
4. DB 마이그레이션 불필요.

**관련 커밋**: `23203ac6f`

---

### 7. 대화 자동 삭제 (데이터 보존 정책, CHAT_DELETE_ENABLED / CHAT_DELETE_DAYS)

**목적/배경**
- "대화 내용은 보존 기간 경과 후 자동 파기" 정책의 서버 측 구현. 1시간마다 보존 기간을 초과한 채팅을 일괄 삭제한다.

**동작 방식**
- env `CHAT_DELETE_ENABLED`(기본 False) / `CHAT_DELETE_DAYS`(기본 365) → `DEFAULT_CONFIG`의 `chat.delete.enable` / `chat.delete.days` → lifespan 백그라운드 태스크가 매 시간 `await Config.get('chat.delete.enable')` 확인 후 `Chats.delete_chats_older_than(days)` 실행.
- 삭제 기준은 `Chat.updated_at < (now - days*86400)` — **updated_at 기준**(created_at 아님).
- **0.6.43 대비 개선**: 벌크 delete 전에 연관 데이터를 함께 정리한다 — `AutomationRun.chat_id`를 NULL로(FK 보호), `ChatMessage` 행 삭제, `SharedChat`(공유 사본) 삭제. 0.6.43 문서에서 한계로 지적됐던 "공유 사본 잔존" 문제가 해소됐다. 첨부 파일(file 테이블/스토리지)은 여전히 삭제하지 않는다.

**변경 파일 및 핵심 내용 (현재 트리 실측)**
- `backend/open_webui/config.py` 2229~2231행 (`ENABLE_FOLLOW_UP_GENERATION` 직후):
```python
# Automatic chat deletion (data retention policy)
CHAT_DELETE_ENABLED = os.getenv('CHAT_DELETE_ENABLED', 'False').lower() == 'true'
CHAT_DELETE_DAYS = int(os.getenv('CHAT_DELETE_DAYS', '365'))
```
및 3049~3050행 `DEFAULT_CONFIG`: `'chat.delete.enable'`, `'chat.delete.days'`.
- `backend/open_webui/models/chats.py` 1921~1944행 — `ChatTable`에 async 메서드 추가:
```python
async def delete_chats_older_than(self, days: int, db: AsyncSession | None = None) -> int:
    from open_webui.models.shared_chats import SharedChat
    try:
        async with get_async_db_context(db) as session:
            cutoff_time = int(time.time()) - (days * 24 * 60 * 60)
            chat_ids_stmt = select(Chat.id).filter(Chat.updated_at < cutoff_time)
            await session.execute(update(AutomationRun).filter(AutomationRun.chat_id.in_(chat_ids_stmt)).values(chat_id=None))
            await session.execute(delete(ChatMessage).filter(ChatMessage.chat_id.in_(chat_ids_stmt)))
            await session.execute(delete(SharedChat).filter(SharedChat.chat_id.in_(chat_ids_stmt)))
            result = await session.execute(delete(Chat).filter(Chat.updated_at < cutoff_time))
            await session.commit()
            return result.rowcount or 0
    except Exception:
        log.exception('Failed to delete chats older than %s days', days)
        return 0
```
- `backend/open_webui/main.py` 353~368행 — `lifespan` 내부, `asyncio.create_task(periodic_session_pool_cleanup())` 직후 / `scheduler_worker_loop` 기동 직전:
```python
# Automatic chat deletion (data retention policy)
async def periodic_chat_deletion():
    while True:
        if await Config.get('chat.delete.enable'):
            try:
                days = int(await Config.get('chat.delete.days'))
                count = await Chats.delete_chats_older_than(days)
                if count > 0:
                    log.info(f'Deleted {count} old chats')
            except Exception as e:
                log.error(f'Error in periodic chat deletion: {e}')
        # Check every hour
        await asyncio.sleep(60 * 60)

asyncio.create_task(periodic_chat_deletion())
```
(0.6.43의 `anyio.to_thread.run_sync` 스레드풀 호출은 async DB 계층 덕에 불필요해져 직접 await로 단순화됨. `app.state.config` 등록도 불필요 — Config.get 직접 조회.)

**재적용 가이드**
1. config.py → models/chats.py → main.py 순. DB 스키마 변경 없음(마이그레이션 불필요).
2. 미래 버전에서 `ChatMessage`/`SharedChat`/`AutomationRun` 등 채팅 연관 테이블이 늘면 삭제 목록에 추가해야 한다. `delete_chat_by_id`가 정리하는 연관 대상을 기준으로 대조할 것.
3. 멀티 워커 환경에서는 워커마다 태스크가 뜨지만 삭제는 멱등.
4. 운영 스크립트(`scripts/cleanup_chats.sh`, `scripts/chat_audit_report.sh`)가 이 정책을 보조한다(운영 파트 문서).

**관련 커밋**: `23203ac6f`

---

### 8. Tika 로더 — 로깅/에러 처리 강화 (tika/text 유지 — rmeta 전환 금지)

**목적/배경**
- Tika 연동 실패 원인 파악용 로깅 강화(기존 예외는 `r.reason`만 포함), 연결 실패/HTTP 오류 구분, 응답 본문 포함 상세 예외.
- **커스텀은 로깅/에러 처리뿐이다. 엔드포인트는 업스트림 0.10.2 그대로 `tika/text`, MIME 전달 없음.**
- **사고 이력 (0.10.2-fix1.1에서 교정, 2026-07-22):** 최초 이식 커밋 `23203ac6f`가 0.6.43 시절 **당일 롤백됐던** 실험 커밋 `a8841c5a5`(rmeta/text 전환 + 배열 `[0]` 선택 + `mime_type` 전달)를 재적용했다. 그 결과 **HWP/HWPX 추출이 깨졌다**: (a) `rmeta/text`는 응답을 구성요소별 배열로 쪼개는데 `[0]`(컨테이너 레코드)만 취해 본문이 유실되고, (b) 브라우저가 붙인 부정확한 MIME(octet-stream 등)이 `Content-Type` 힌트로 강제되어 Tika의 파서 자동 감지를 방해했다. Tika가 200 OK를 반환하므로 에러 로그 없이 EMPTY_CONTENT로만 나타난다. 구 문서의 경고("`a8841c5a5`를 그대로 적용하면 안 됨")를 어긴 이식 실수였고, fix1.1에서 0.6.43 최종 상태(= 업스트림 0.10.2와 동일)로 원복했다. **재발 방지: rmeta 전환·MIME 전달을 다시 시도하지 말 것.**

**동작 방식**
- 엔드포인트 `{TIKA_SERVER_URL}/tika/text` (PUT, Content-Type 헤더 없음 → Tika가 바이트 스니핑으로 파서 선택). 응답은 단일 JSON 객체, `X-TIKA:content` 사용.
- 추출 시작 `log.info`, 엔드포인트 `log.debug`, 연결 실패 별도 `log.error` 후 re-raise, HTTP 실패 시 `status_code reason - body` 포함 로깅/예외.

**변경 파일 및 핵심 내용 (0.10.2-fix1.1 트리 실측)**
- `backend/open_webui/retrieval/loaders/main.py` — `TikaLoader.load()`:
```python
def load(self) -> list[Document]:
    log.info(f'Starting Tika extraction for file: {self.file_path}')
    ...
    endpoint += 'tika/text'   # rmeta/text 금지 — 위 사고 이력 참조 (소스에 한글 경고 주석 있음)
    log.debug(f'Tika endpoint: {endpoint}')
    try:
        r = requests.put(endpoint, data=data, headers=headers, verify=REQUESTS_VERIFY)
    except Exception as e:
        log.error(f'Failed to connect to Tika at {endpoint}: {e}')
        raise e
    if r.ok:
        raw_metadata = r.json()
        text = raw_metadata.get('X-TIKA:content', '<No text content found>').strip()
        ...
    else:
        log.error(f'Error calling Tika: {r.status_code} {r.reason} - {r.text}')
        raise Exception(f'Error calling Tika: {r.status_code} {r.reason} - {r.text}')
```
(`verify=REQUESTS_VERIFY`는 업스트림 0.10.2 기존 코드 — 유지할 것.)
- 같은 파일 `Loader`의 tika 분기 — `mime_type`을 **넘기지 않는다** (업스트림과 동일). 커스텀은 `log.debug` 한 줄과 호출부 위 한글 경고 주석뿐:
```python
elif self.engine == 'tika' and self.kwargs.get('TIKA_SERVER_URL'):
    if self._is_text_file(file_ext, file_content_type):
        log.debug('Falling back to TextLoader for text file (Tika configured)')
        loader = TextLoader(file_path, encoding=self._detect_text_encoding(file_path))
    else:
        loader = TikaLoader(
            url=self.kwargs.get('TIKA_SERVER_URL'),
            file_path=file_path,
            extract_images=self.kwargs.get('PDF_EXTRACT_IMAGES'),
        )
```

**재적용 가이드**
1. `TikaLoader.load()`에 로깅/try-except/상세 예외만 얹는다. 엔드포인트(`tika/text`)와 호출부 시그니처는 업스트림 그대로 두고, rmeta/MIME 관련 변경이 업스트림에 새로 생겼는지 확인 후 **HWP 업로드 실테스트**로 검증할 것.
2. Dockerfile의 파싱 의존성(§11의 pyhwp/msoffcrypto-tool 등)과 세트 — Tika 서버 측 HWP 처리 파이프라인 보조용.
3. DB/설정 변경 없음. `TIKA_SERVER_URL` 등 기존 설정 그대로.
4. 검증 방법: HWP/HWPX 파일 업로드 → 지식베이스 또는 채팅 첨부에서 내용 질의가 되는지 확인. 실패 시 증상은 "에러 로그 없이(INFO만) 추출 실패" — Tika는 200을 주므로 서버 로그만 봐서는 안 보인다.

**관련 커밋**: `23203ac6f`(최초 이식, rmeta 사고 포함) → 0.10.2-fix1.1에서 교정

---

### 9. backend/start.sh — 기동 시 alembic 마이그레이션 명시 실행

**목적/배경**
- 커스텀 마이그레이션(`f1a2b3c4d5e6_add_token_jti_to_auth.py`, 인증 파트 문서)과 §10의 stamp 자동 교정이 uvicorn 기동 **전에** 확실히 적용되도록 alembic을 명시 실행.

**동작 방식 / 변경 파일 및 핵심 내용 (현재 트리 실측)**
- `backend/start.sh` 97~102행 — "Launch uvicorn" 섹션 직전:
```bash
# ── Database migrations ──────────────────────────────────────────────────────

# Run migrations explicitly before serving traffic. The app also runs them at
# startup, but this guarantees the custom token_jti migration is applied first.
# alembic.ini's script_location is relative to the CWD, so run from open_webui/.
(cd open_webui && WEBUI_SECRET_KEY="${WEBUI_SECRET_KEY:-}" alembic upgrade head)
```
- 이력: 최초 이식(`23203ac6f`)은 `alembic -c open_webui/alembic.ini upgrade head`였으나, alembic.ini의 `script_location`(migrations)이 **CWD 기준 상대경로**라 `/app/backend`에서 실행하면 스크립트를 못 찾는 문제가 있어 `82782b0e3`에서 서브셸 `cd open_webui` 방식으로 수정됐다. 재이식 시 반드시 최종형(cd 방식)을 쓸 것.

**재적용 가이드**
1. uvicorn exec 직전에 위 블록 삽입. 서브셸이므로 이후 CWD에 영향 없음.
2. `WEBUI_SECRET_KEY`를 넘기는 이유: migrations/env.py가 open_webui 패키지를 import하며 env 검증을 타기 때문. `:-`로 미설정 시 빈 값 허용.
3. 멀티 레플리카 배포에서는 기동 경합 가능(단일 컨테이너 전제).

**관련 커밋**: `23203ac6f`, `82782b0e3`

---

### 10. migrations/env.py — 구 포크 DB의 잘못된 alembic stamp 자동 교정

**목적/배경**
- 0.6.43-fix2.1 포크는 커스텀 JTI 마이그레이션에 리비전 ID `a1b2c3d4e5f6`을 썼는데, **업스트림 0.10.2 체인에는 동일 ID가 skill 테이블 생성 마이그레이션으로 존재한다**(`versions/a1b2c3d4e5f6_add_skill_table.py` — 우연한 충돌). 구 포크 DB(`alembic_version = a1b2c3d4e5f6`)를 0.10.2-fix1 이미지에 물리면 alembic이 "skill 마이그레이션까지 적용됨"으로 오인해 중간 마이그레이션(prompt_history/chat_message/access_grant 등)을 건너뛰고, 이후 UndefinedTable로 죽는다. 이를 기동 시 자동 감지·교정한다.
- (이식판 JTI 마이그레이션은 충돌을 피해 `f1a2b3c4d5e6_add_token_jti_to_auth.py`로 재작성됨 — 인증 파트 문서.)

**동작 방식**
- `alembic upgrade head` 실행 시(§9의 start.sh, 그리고 앱 내부 마이그레이션 모두 `run_migrations_online()` 경유) 마이그레이션 전에 검사:
  1. `alembic_version.version_num`이 `a1b2c3d4e5f6`인가? (아니면 통과)
  2. `skill` 테이블이 실제로 존재하는가? — 존재하면 현 체인에서 정상적으로 그 지점에 도달한 DB이므로 통과. **없으면 구 포크 DB로 판정**(구 포크에는 skill 테이블이 없음 — 판별 근거).
  3. 판정 시 `version_num`을 `c440947495f3`(add_chat_file_table — 구 포크 DB가 실제로 적용한 마지막 공통 리비전)으로 UPDATE → 이후 upgrade가 나머지 체인을 재생. 재생되는 커스텀 마이그레이션들은 guard/멱등 처리돼 있어 이중 적용에 안전.

**변경 파일 및 핵심 내용 (현재 트리 실측)**
- `backend/open_webui/migrations/env.py` 68~106행 — `LEGACY_FORK_STAMP = 'a1b2c3d4e5f6'`, `LEGACY_FORK_RESTAMP = 'c440947495f3'` 상수와 `_fix_legacy_fork_stamp(connectable)` 함수(사유를 설명하는 긴 주석 포함). `alembic_version` 테이블이 없으면(신규 DB) 조용히 return.
- 113행 — `run_migrations_online()`에서 `enable_iam_token_auth(live_connectable)` 직후 호출:
```python
live_connectable = _get_engine_connectable()
enable_iam_token_auth(live_connectable)
_fix_legacy_fork_stamp(live_connectable)
```
(offline 모드 `run_migrations_offline()`에는 미적용 — 운영 경로는 online만 사용.)

**재적용 가이드**
1. **이 항목은 0.6.43-fix2.1 DB에서 이미 전환을 마친 뒤에는 불필요해진다.** 모든 운영 DB가 0.10.2-fix1 이상으로 마이그레이션 완료됐음이 확인되면 미래 버전 이식에서 생략 가능. 확신이 없으면 유지해도 무해(조건이 매우 특정적이라 오탐 여지 없음).
2. 유지할 경우: 미래 버전에서 `run_migrations_online()` 구조가 바뀌면 "connect 전, engine 확보 직후" 지점에 호출을 배치. `LEGACY_FORK_RESTAMP` 값은 절대 바꾸지 말 것(구 포크가 실제 적용한 마지막 리비전이라는 사실에 기반).
3. 상세 전환 절차는 저장소 루트 `MIGRATION_RUNBOOK_to_0.10.2.md` 참조.

**관련 커밋**: `75d2a4ed7`

---

### 11. Dockerfile — 비루트 기본화, NODE_OPTIONS, 문서 파싱 의존성 (업스트림과의 전체 차이)

**목적/배경**
- 컨테이너 기본 실행 계정을 root(UID 0)에서 UID/GID 1000의 일반 사용자(`appusr:appgrp`)로 변경, HOME을 `/home/appusr`로 이동. 프런트 빌드 OOM 방지용 NODE_OPTIONS 활성화. HWP 등 사내 문서 파싱 호환용 파이썬 패키지 및 nltk 데이터 빌드 타임 설치.

**변경 파일 및 핵심 내용 — 업스트림 0.10.2 Dockerfile과의 차이 전량 (현재 트리 실측)**

(a) 비루트 기본값 (22~24행):
```dockerfile
# Run as a non-root user by default (security hardening)     ← 주석도 교체(업스트림: "Override at your own risk - non-root configurations are untested")
ARG UID=1000     # 업스트림 0
ARG GID=1000     # 업스트림 0
```
말미의 `USER $UID:$GID`(206행)는 업스트림 기존 라인 — UID 기본값이 1000이 되면서 실제 비루트 실행이 된다.

(b) NODE_OPTIONS 활성화 (31행, 프런트 빌드 스테이지):
```dockerfile
ENV NODE_OPTIONS="--max-old-space-size=4096"     # 업스트림은 주석 처리 상태
```

(c) HOME 및 사용자 생성 (111~118행):
```dockerfile
ENV HOME=/home/appusr     # 업스트림 /root
# Create user and group if not root
RUN if [ $UID -ne 0 ]; then \
    if [ $GID -ne 0 ]; then \
    addgroup --gid $GID appgrp; \                # 업스트림 그룹명 app
    fi; \
    adduser --uid $UID --gid $GID --home $HOME --disabled-password --gecos "" appusr; \
    fi                                            # 업스트림: --no-create-home app / 커스텀: 홈 생성 + --gecos ""
```
직후의 `RUN mkdir -p $HOME/.cache/chroma` 등 `$HOME` 참조 라인들은 업스트림 그대로이나 새 HOME 값 기준으로 동작한다.

(d) 문서 파싱 의존성 (167~169행, requirements 설치 RUN 직후 / "Install Ollama if requested" 직전의 독립 레이어):
```dockerfile
# Install additional dependencies for documented parsing compatibility
RUN pip3 install --no-cache-dir msoffcrypto-tool chardet nltk pyhwp && \
    python3 -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab')"
```
nltk 데이터는 빌드 시점 `$HOME/nltk_data`(= `/home/appusr/nltk_data`)에 저장 — (c)의 HOME 변경과 세트여야 런타임 사용자가 읽을 수 있다. `backend/requirements.txt`/`pyproject.toml`은 건드리지 않는다.

(e) 권한 강화 블록(`USE_PERMISSION_HARDENING`, 195~204행)의 `/root` → `$HOME` 치환 (주석 포함 4곳):
```dockerfile
    chgrp -R 0 /app $HOME || true; \
    chmod -R g+rwX /app $HOME || true; \
    find /app -type d -exec chmod g+s {} + || true; \
    find $HOME -type d -exec chmod g+s {} + || true; \
```

(f) `USE_CUDA` — **업스트림과 차이 없음(기본 false)**. 이식 커밋 `23203ac6f`가 0.6.43 커스텀을 따라 `true`로 올렸다가 `5560559e1`에서 다시 `false`로 원복해 순 diff가 0이 됐다(서버 GPU 미사용, 이미지 용량 절감). 0.6.43 문서의 "USE_CUDA=true 기본화" 항목은 **폐기됨** — 미래 이식 시 건드리지 말 것.

**재적용 가이드**
1. 적용 지점 4곳을 문맥으로 찾는다: ① `ARG UID/GID` ② 프런트 스테이지 `NODE_OPTIONS` 주석 ③ `ENV HOME` + adduser 블록 + hardening 블록 ④ requirements 설치 직후의 파싱 의존성 레이어. 미래 버전에서 스테이지 구조가 바뀌어도 이 4지점 치환 방식이면 안전하다.
2. `/app/backend/data`는 업스트림 RUN에서 이미 `chown -R $UID:$GID` 되지만, **기존 볼륨(root 소유)이 있는 환경에 비루트 이미지를 올리면 권한 오류**가 난다. 볼륨 데이터 소유권을 1000:1000으로 맞추는 운영 절차 필요(`MIGRATION_RUNBOOK_to_0.10.2.md` 참조).
3. 새 업스트림이 파싱 패키지 일부를 requirements에 포함했는지 확인 후 중복 설치 정리. nltk 데이터 경로가 애매하면 `NLTK_DATA` env로 고정하는 방법도 있다.
4. 파싱 의존성은 §8(Tika/HWP)과 세트로 검토.

**관련 커밋**: `23203ac6f`, `5560559e1`

---

### 12. [신규 2026-08-13] 인사·조직 마스터 데이터 일일 동기화 (`HR_SYNC_*`)

**목적/배경**
- 사내 인사 REST API에서 **직원·부서·공휴일** 스냅샷을 매일 **같은 시각에 한 번** 받아 파일로 저장하고, 직원+부서를 합쳐 **조직도(`org.json`)를 파생 생성**한다. 소비자는 OpenWebUI Functions 필터와 외부 조회 도구이며, 이들은 파일을 **읽기만** 한다.
- 종전에는 같은 수집 로직이 Functions 필터 안에 있어 **그날 첫 채팅 요청이 트리거**했다. 첫 사용자가 수집 지연을 떠안고, 수집 시각이 매일 달라지며, 필터를 끄면 수집도 멈추는 구조였다. 이를 **정시 배치**로 분리한 것이 본 기능이다.

**접점 파일**
| 파일 | 변경 |
|---|---|
| `backend/open_webui/utils/hr_sync.py` | **신규**(562행). 수집·저장·조직도 생성·스케줄러 전부 |
| `backend/open_webui/main.py` | `lifespan` 내 2줄 — `scheduler_worker_loop` 등록 직후 `asyncio.create_task(hr_sync_loop())` |

```python
    # 인사·조직 마스터 데이터 일일 동기화 (HR_SYNC_* 환경변수, 기본 비활성)
    from open_webui.utils.hr_sync import hr_sync_loop

    asyncio.create_task(hr_sync_loop())
```

**설정 — 전부 환경변수 (DB `config` 테이블을 쓰지 않는다)**
- 이유 두 가지: ① 공통 주의사항 3의 함정(=DB 행이 env보다 우선해 env 수정이 먹지 않음)을 아예 피한다. ② **이 저장소는 공개**라 API 주소·헤더 이름/값·기관 코드 같은 사내 식별자를 코드·문서·compose 어디에도 남기지 않고 배포 서버 compose 에만 둔다.
- 값이 바뀌면 **재기동 필요**(모듈 로드 시점 1회 읽기).

| 환경변수 | 기본값 | 설명 |
|---|---|---|
| `HR_SYNC_ENABLED` | `false` | 꺼져 있으면 백그라운드 태스크 자체가 뜨지 않는다 |
| `HR_SYNC_TIME` | `08:00` | 매일 실행 시각 `HH:MM`. 기본값은 롤오버 시각과 같게 두어, 종전 "롤오버 후 첫 요청이 수집"과 같은 타이밍을 유지한다 |
| `HR_SYNC_TZ` | `Asia/Seoul` | 실행 시각·날짜 라벨 기준 타임존 |
| `HR_SYNC_DIR` | `<DATA_DIR>/hr` | 스냅샷 저장 디렉터리(조회 도구와 공유) |
| `HR_SYNC_EMP_API_URL` / `_DEPT_API_URL` / `_HOLIDAY_API_URL` | — | 비운 항목은 미수집. 셋 다 비면 루프 미기동 |
| `HR_SYNC_API_HEADER_NAME` / `_VALUE` | — | 시스템 식별용 추가 요청 헤더(비우면 미전송) |
| `HR_SYNC_API_TIMEOUT` | `10` | 호출 타임아웃(초) |
| `HR_SYNC_ROLLOVER_HOUR` | `8` | 날짜 라벨 기준 시각. 이 시각 전이면 전날로 본다 |
| `HR_SYNC_RETENTION_DAYS` | `7` | 일자 보관본 유지 일수 |
| `HR_SYNC_HOLIDAY_YEARS_BACK` / `_AHEAD` | `1` / `1` | 공휴일 수집 범위(작년 1/1 ~ 내년 12/31) |
| `HR_SYNC_ROOT_DEPT_CODE` / `_NAME` | — | 조직도 최상위 노드. 비우면 삽입하지 않는다 |
| `HR_SYNC_RUN_ON_START` | `true` | 기동 시 오늘자 스냅샷이 없으면 즉시 1회 보충 |

**동작**
- **스케줄 판정**: 1분마다 현재 시각을 다시 읽어 `달력 날짜가 바뀌었고 && 현재 시각 ≥ HR_SYNC_TIME`이면 실행. 긴 `sleep` 대신 짧은 폴링이라 컨테이너 일시정지·시계 조정으로 시간이 튀어도 예정 시각을 지나치지 않는다. 실행 후에는 그날 다시 돌지 않는다(실패해도 재시도하지 않고 다음 날).
- **기동 시**: 이미 예정 시각을 지난 상태로 떠도 그날 몫을 다시 돌리지 않는다(재기동마다 재수집 방지). 대신 `RUN_ON_START`가 오늘자 파일 부재를 확인해 보충한다.
- **산출물**: `emp.json` / `dept.json` / `holiday.json` / `org.json` + 일자 보관본 `<이름>.<YYYY-MM-DD>.json`(기본 7일, 초과분 삭제).
- **원자적 저장**: 임시파일 → `os.replace`. 읽는 쪽이 쓰다 만 JSON을 보지 않는다.
- **`useYn` 규칙**: 명시적 `N`만 제외(필드 없음/빈 값은 유지) — API가 필드를 빼는 변경에도 전원 누락으로 번지지 않게. 저장 시점과 읽는 시점 양쪽에서 적용.
- **실패 격리**: 항목별로 독립 처리한다. 한 API가 죽어도 나머지는 갱신되고, 실패한 항목은 **직전 파일이 그대로 남아** 읽는 쪽이 보관본으로 계속 동작한다.
- **빈 응답 가드**: 레코드 0건이면 저장하지 않고 실패로 처리한다(기존 파일 보존). 판정은 **루트 노드 삽입 전**에 한다 — 삽입분 때문에 빈 응답이 1건으로 보이지 않도록.
- **공휴일**: 전 범위(작년~내년)를 한 번에 요청하고, 응답이 비면 **연 단위로 나눠 받아 합친다**(범위 조회를 지원하지 않는 API 대비).
- **조직도**: 저장된 `emp`+`dept` 파일 기준으로 매번 다시 만든다. 부모는 `dept2Code`→`dept3Code` 중 자기 코드와 처음으로 다른 코드, 상위가 없는 노드는 최상위 노드 아래로 모아 루트를 하나로 유지한다. 부서 목록에 없는 부서코드의 직원은 **`미분류(<코드>)` 노드로 보존**(누락 금지). 조직은 `deptOrder`, 인원은 `positionOrder` 오름차순 정렬 후 **정렬용 값은 출력에서 제외**(배열 순서로 대신). 인원 레코드에 **사번·이메일은 싣지 않는다**.

**주의사항**
1. **`HR_SYNC_TIME`은 `HR_SYNC_ROLLOVER_HOUR` 이후여야 한다.** 그 전에 저장하면 전날 라벨이 붙어, 같은 롤오버 규칙으로 "오늘자가 있는가"를 판정하는 소비자가 계속 낡았다고 본다. 어긋나면 기동 시 경고 로그를 남긴다.
2. **`UVICORN_WORKERS=1` 전제**(기본값). 여러 워커로 띄우면 워커 수만큼 같은 시각에 호출이 나간다 — 저장은 원자적이라 파일이 깨지진 않지만 API 호출이 중복된다.
3. **파일명·JSON 형태·정렬 규칙은 소비자와의 계약**이다. 바꾸면 조회 도구가 함께 깨진다.
4. 디렉터리는 컨테이너 사용자(uid 1000)가 쓸 수 있어야 한다. 기본값(`<DATA_DIR>/hr`)은 기존 데이터 볼륨 안이라 문제없고, 다른 컨테이너와 공유하려면 별도 볼륨을 양쪽에 마운트한다.
5. 기존 Functions 필터에도 같은 수집 로직이 남아 있다면 **같은 디렉터리를 가리키는 한 충돌하지 않는다** — 필터는 "오늘자 파일 있음"을 확인하고 건너뛰므로 사실상 폴백으로만 동작한다.

**재이식 방법 (차기 버전)**
1. `backend/open_webui/utils/hr_sync.py`를 그대로 복사한다(업스트림 의존은 `open_webui.env`의 `DATA_DIR`·`REQUESTS_VERIFY` 두 개뿐).
2. `main.py`의 `lifespan`에서 `scheduler_worker_loop` 등록 직후에 위 2줄을 추가한다.
3. 검증: 가짜 인사 API(로컬 HTTP 서버)를 띄우고 `sync_snapshots(day)` 호출 → 4종 파일·정렬·`useYn` 필터·보관 7일·실패 격리 확인. 스케줄 판정은 모듈의 `datetime`을 가짜 시계로 대체해 "예정 시각 통과 시 1회, 같은 날 재실행 없음, 다음 날 재실행"을 확인한다. (2026-08-13 기준 linux/amd64 컨테이너·uid 1000에서 34개 항목 통과)

---

### 13. 경계 항목·이식되지 않은 항목·변경 없음 확인

**같은 파일에 있으나 다른 파트 소관 (충돌 주의)**
- `config.py` 2402행 `JWT_EXPIRES_IN = os.getenv('JWT_EXPIRES_IN', '24h')`(업스트림 '4w'), `main.py` 1890행 `'auth.jwt_expiry'` 키 추가 및 1963~1967행 features `'jwt_expires_in'` 노출 — **인증/세션 파트 문서 담당**.
- `utils/auth.py` 462~468행 JTI 단일 세션 검증(automation 토큰 예외 fail-closed 포함), `routers/auths.py`의 refresh/`server_timestamp`/JTI 회전, `models/auths.py`, `migrations/versions/f1a2b3c4d5e6_add_token_jti_to_auth.py` — 인증 파트 담당. 본 파트는 `validate_password` 호출부만 다룸.
- `docker-compose.yaml`의 배포 env 값(`DISABLE_ADMIN`, `ENABLE_PASSWORD_VALIDATION`, `PASSWORD_BLACKLIST`, `CHAT_DELETE_*`, 토글 3종 등) — 운영/배포 파트 문서 담당.

**0.6.43 문서에 있었으나 0.10.2 이식에서 소멸/불필요해진 항목**
- `files.py`의 `except HTTPException: raise` — 업스트림 0.10.2에 이미 반영(§2).
- `auths.py` `update_password`의 검증 대상 버그(password→new_password) — 업스트림에서 이미 수정(§5).
- `add_user`의 user_data 오전달(관리자 본인 정보 대조) 버그 — 이번 이식에서 `form_data` 기준으로 수정(§5).
- `enable_admin_export` 공통 블록 중복 노출 — **이식되지 않음**(§3). 필요성 재확인 후 필요 시 별도 적용.
- ~~Tika `tika/text` 유지(0.6.43 최종) — 0.10.2에서는 반대로 `rmeta/text`가 채택됨~~ → **2026-07-23 정정**: `rmeta/text` 채택은 이식 실수였고 HWP/HWPX 본문 유실을 일으켜 `tika/text`로 원복했다(§8). 차기 이식에서도 `tika/text`를 유지할 것.
- Dockerfile `USE_CUDA=true` 기본화 — 폐기(§11 (f)).

**변경 없음 확인**
- `main.py`의 보안 응답 헤더(SecurityHeadersMiddleware 등) 관련 커스텀 변경은 이번 diff에 **없다**.
- `backend/requirements.txt`, `pyproject.toml` 변경 없음.

**본 파트 재적용 권장 순서**
1. `constants.py` 한글화 + PASSWORD_* (다른 변경의 의존 대상)
2. `env.py`: `DISABLE_ADMIN`, `PASSWORD_BLACKLIST`
3. `utils/auth.py`: `get_admin_user` 게이트, `validate_password` 교체 (인증 파트의 JTI 블록과 병합)
4. 호출부: `routers/auths.py` 3곳 + `routers/users.py` 1곳
5. `routers/files.py`: FILE_NOT_SUPPORTED
6. `routers/ollama.py` / `openai.py`: 오류 마스킹 + verify 400 통일 (신규 엔드포인트 포함 전수 조사)
7. `config.py`: 토글 3종 + CHAT_DELETE_* (env 읽기 + DEFAULT_CONFIG 키)
8. `main.py`: disable_admin(공통 블록)·토글 features·config 키 리스트·periodic_chat_deletion
9. `models/chats.py`: `delete_chats_older_than` (연관 테이블 목록 최신화)
10. `retrieval/loaders/main.py`: Tika 로깅/에러 처리 (**`tika/text` 유지 — `rmeta/text` 전환 금지**, §8)
11. `utils/hr_sync.py` 신규 복사 + `main.py` lifespan 2줄 (§12)
12. `Dockerfile` 4지점 + `backend/start.sh` alembic 블록
13. `migrations/env.py` stamp 교정 — 구 포크 DB 전환이 남아 있는 경우에만

---

# 파트: 프런트엔드 전반 / 동의·데이터정책 / 운영 스크립트·배포

> 비교 기준: `git diff ecd48e2f7..HEAD` (업스트림 v0.10.2 = `ecd48e2f7` → 브랜치 `0.10.2-fix1`).
> 코드 위치·인용은 현재 HEAD 트리에서 실측한 값이다.
> src/ 하위 변경 파일은 총 176개이며, 그중 약 157개는 `localStorage.token → sessionStorage.token` 일괄 치환만 포함(섹션 2), 나머지는 아래 각 섹션에 배정했다. 배정 대조표는 문서 말미 "기타" 참조.

---

### 1. 이용 동의(고지사항) 모달 및 데이터 보존 정책

**목적/배경**
- 사내 AI 시스템 이용 시 중요정보 업로드 금지, 부당 이용 금지 등 보안 고지사항에 대한 사용자 동의를 최초 접속 시 강제한다.
- 고지문에 명시된 "대화 내용 1년 보관 후 자동 파기" 정책을 백엔드의 대화 자동 삭제 스케줄러가 실제로 집행한다. 정책 기본값은 **365일**(코드 기본값·compose 모두 365, 2026-07-14 확정). 주의: `chat.delete.days`는 DB `config` 테이블에 시드되므로, 테스트 값(예: 1)으로 부팅한 적 있는 DB는 env 수정만으로 바뀌지 않는다 — `UPDATE config SET value='365' WHERE key='chat.delete.days';`로 교정할 것.
- 업스트림의 ChangelogModal(관리자 로그인 시 버전 변경 안내)은 사내 운영에 불필요하여 비활성화하고, 그 자리에 동의 모달을 넣었다.

**동작 방식**
- `src/routes/(app)/+layout.svelte`의 `onMount` 말미에서 `localStorage.getItem('agreedToTerms')`가 없으면 `showAgreement = true`로 동의 모달을 띄운다. 동의 여부만 localStorage에 남고(브라우저·기기 단위 1회), 토큰과 달리 세션스토리지가 아니다.
- `AgreementModal`은 열릴 때 `fetch('/agreement.md')`로 정적 파일 `static/agreement.md`를 가져와 `marked.parse` + `DOMPurify.sanitize` 후 렌더링한다. "동의하기" 버튼을 눌러야만 닫힌다.
- 모달 강제성은 공통 `Modal.svelte`에 추가한 `dismissible` prop으로 구현: `dismissible={false}`이면 ESC 키와 배경 클릭으로 닫히지 않는다.
- ChangelogModal은 컴포넌트 자체는 남겨두고(sessionStorage 치환만 적용) 사용처에서 import와 렌더링, `showChangelog.set(...)` 트리거를 모두 주석/삭제 처리했다.
- 대화 자동 삭제(백엔드, 정책 관점 요약): `backend/open_webui/main.py:354` `periodic_chat_deletion()`이 1시간 간격으로 `Config.get('chat.delete.enable')`을 확인하고, 활성 시 `Chats.delete_chats_older_than(days)`를 호출. `backend/open_webui/models/chats.py:1921` `delete_chats_older_than()`은 `chat.updated_at < (now - days*86400)` 기준으로 AutomationRun 참조 해제 → ChatMessage·SharedChat 삭제 → Chat 삭제까지 일괄 수행한다. 설정 키는 `chat.delete.enable` / `chat.delete.days`(env `CHAT_DELETE_ENABLED`, `CHAT_DELETE_DAYS`, 기본 False/365 — `backend/open_webui/config.py:2229` 부근). 상세 구현 명세는 백엔드 파트 문서 참조.

**변경 파일 및 핵심 내용**
- `src/lib/components/AgreementModal.svelte` (신규, 62줄): agreement.md 로드·렌더, `handleAgree()`에서 `localStorage.setItem('agreedToTerms', 'true')`. `<Modal bind:show size="xl" dismissible={false}>` 사용. "동의하기" 버튼 문구는 하드코딩(한글).
- `static/agreement.md` (신규, 12줄): 고지문 본문. **문구 수정은 이 파일만 바꾸면 되고 코드 수정 불필요.**
- `src/lib/components/common/Modal.svelte`: `export let dismissible = true;` 추가. `handleKeyDown`의 Escape 처리와 배경 `on:mousedown` 닫기 양쪽에 `dismissible` 조건 추가 (총 +8줄 수준의 작은 diff).
- `src/routes/(app)/+layout.svelte`:
  - `import ChangelogModal ...` 주석 처리, `<ChangelogModal bind:show={$showChangelog} />` 주석 처리.
  - `if ($user?.role === 'admin' && ($settings?.showChangelog ?? true)) { showChangelog.set(...) }` 블록 삭제.
  - `import AgreementModal`, `let showAgreement = false;`, onMount 말미 `agreedToTerms` 체크, `<AgreementModal bind:show={showAgreement} />` 추가.
- `src/lib/components/ChangelogModal.svelte`: sessionStorage 치환만(기능 변경 없음).

**재적용 가이드**
1. `AgreementModal.svelte`, `static/agreement.md`는 신규 파일이므로 그대로 복사 — 업스트림 충돌 없음.
2. `Modal.svelte`의 `dismissible` prop 3개 지점(선언, Escape, 배경 클릭)을 수동 재적용. 업스트림에서 Modal이 리팩터링되면(예: 자체 dismissible 도입 여부 확인) 닫기 경로가 늘었는지 점검하고 모든 닫기 경로에 조건을 걸 것.
3. `(app)/+layout.svelte`는 업스트림 변동이 잦은 파일이다. "ChangelogModal 제거 + AgreementModal 추가 + agreedToTerms 체크" 3가지 포인트만 이식하면 되며, 이 파일의 세션 타이머 부분(세션/인증 파트 소유)과 섞이지 않게 주의.
4. 검증: 시크릿 창 접속 → 로그인 직후 동의 모달이 뜨고 ESC/배경클릭으로 닫히지 않는지, 동의 후 새로고침 시 다시 뜨지 않는지, 관리자 로그인 시 Changelog 모달이 뜨지 않는지 확인.

**관련 커밋**
- `3584a740c` (AgreementModal·agreement.md·SessionTimeoutModal 파일 추가, ChangelogModal sessionStorage 치환)
- `673d247ed` (Modal dismissible, (app)/+layout에 모달 배선·Changelog 비활성화)
- 백엔드 스케줄러: `23203ac6f`

---

### 2. 인증 토큰 저장소 전환: localStorage → sessionStorage (프런트 전면)

**목적/배경**
- JWT를 localStorage에 두면 브라우저를 닫아도 토큰이 남는다. 탭/브라우저 종료 시 토큰이 소멸되도록 sessionStorage로 전환(보안 요구사항). 백엔드의 JTI 단일 세션 강제와 세트로 동작하며, 탭 간 토큰 동기화는 BroadcastChannel(`session-token`)로 해결(세션/인증 파트 참조).

**동작 방식**
- 코드 전반의 `localStorage.token` 읽기/쓰기와 `localStorage.getItem('token')`을 sessionStorage로 치환. 로그아웃·세션만료 정리 시에는 잔존물 제거를 위해 `localStorage.removeItem('token')`과 `sessionStorage.removeItem('token')`을 **둘 다** 호출한다(구버전에서 남은 localStorage 토큰 청소 목적 — 현재 7곳).
- `agreedToTerms`(섹션 1), `localStorage.version`(Changelog), `redirectPath` 등 토큰이 아닌 키는 의도적으로 localStorage에 남아 있다.

**현황 실측 (HEAD 기준)**
- `grep -rn "localStorage.token" src/ | wc -l` → **0**
- `grep -rln "sessionStorage.token" src/ | wc -l` → **164** (파일 수)
- `localStorage.getItem('token')` 잔존 → 0 (`XTerminal.svelte`까지 치환 완료)
- `git diff ecd48e2f7..HEAD --stat -- src/` → 176개 파일. 이 중 약 157개는 이 치환만 포함(Analytics 4개 파일 포함 — 섹션 4). 대표 파일: `src/routes/+layout.svelte`(소켓 auth), `src/lib/components/chat/Chat.svelte`, `src/lib/components/chat/Settings/Account.svelte`(JWT 표시/복사), `src/lib/apis/index.ts`(tool server session 인증), `src/lib/components/chat/XTerminal.svelte`.

**재적용 가이드 (업그레이드 시 재실행 절차)**
1. 업스트림 새 버전 체크아웃 후 일괄 치환:
   ```bash
   grep -rl "localStorage.token" src/ | xargs sed -i 's/localStorage\.token/sessionStorage.token/g'
   grep -rl "localStorage.getItem('token')" src/ | xargs sed -i "s/localStorage.getItem('token')/sessionStorage.getItem('token')/g"
   grep -rl "localStorage.setItem('token'" src/ | xargs sed -i "s/localStorage.setItem('token'/sessionStorage.setItem('token'/g"
   ```
2. `localStorage.removeItem('token')`은 치환하지 말 것 — 대신 각 위치(로그아웃 핸들러, 401 리다이렉트, AccountPending, UserMenu 등)에 `sessionStorage.removeItem('token')`이 **병기**되어 있는지 확인하고 없으면 추가.
3. 검증:
   ```bash
   grep -rn "localStorage.token" src/ | wc -l          # 0이어야 함
   grep -rn "localStorage.getItem('token')" src/        # 결과 없어야 함
   grep -rn "sessionStorage.removeItem('token')" src/ | wc -l   # 로그아웃 경로 수와 일치(현재 7)
   npm run build                                        # 빌드 통과 확인
   ```
4. 기능 검증: 로그인 → 새 탭에서 세션 공유가 안 되는 것이 정상(탭별 sessionStorage). 탭 간 토큰 갱신 전파는 BroadcastChannel이 담당하므로 두 탭을 열고 한쪽에서 세션 연장 시 다른 쪽이 로그아웃되지 않는지 확인(세션/인증 파트 시나리오).
5. 주의: 업스트림이 새로 추가한 컴포넌트도 `localStorage.token`을 쓰므로 버전을 올릴 때마다 1번 치환을 반드시 재실행해야 한다. 쿠키(`token=`) 경로는 백엔드가 별도 설정하므로 이 치환과 무관.

**관련 커밋**
- `3584a740c` (전면 일괄 치환 — src 170여 파일)
- `673d247ed`, `16b045260`, `92c87cf7e` (이후 추가된 세션 코드에서의 후속 정리)

---

### 3. 서버 설정 기반 기능 토글 UI (이미지 캡처 / 웹페이지 첨부 / 개인정보 입력 / 관리자 페이지)

**목적/배경**
- 보안 정책상 불필요·위험한 기능(화면 캡처 업로드, 임의 웹페이지 첨부, 성별·생년월일 등 개인정보 입력)을 환경변수로 서버에서 끄고, 프런트 UI도 함께 숨긴다.

**동작 방식**
- 백엔드가 env → config 키(`ui.enable_image_capture` 등, `backend/open_webui/config.py:1998~2002`, 기본값 모두 True)로 저장하고, `/api/config`의 `features`로 노출한다(`backend/open_webui/main.py:1960~1962`, `disable_admin`은 `main.py:1943`).
- 프런트는 `$config?.features?.enable_* ?? true` 패턴으로 해당 UI 블록을 `{#if}`로 감싼다. 기본값 true 폴백이므로 백엔드가 키를 안 내려줘도(업스트림 백엔드) UI는 그대로 보인다.

**변경 파일 및 핵심 내용**
- `src/lib/stores/index.ts`: `Config.features` 타입에 `enable_image_capture?`, `enable_webpage_attachment?`, `enable_user_personal_info?`, `disable_admin?`, `jwt_expires_in?` 필드 추가.
- `src/lib/components/chat/MessageInput/InputMenu.svelte`: 입력창 "+" 메뉴의 **Capture(화면/카메라 캡처)** 버튼을 `{#if $config?.features?.enable_image_capture ?? true}`로, **Attach Webpage** 버튼을 `{#if $config?.features?.enable_webpage_attachment ?? true}`로 래핑(버튼 자체는 업스트림 코드 그대로, 들여쓰기만 변경 — diff가 커 보이는 이유).
- `src/lib/components/workspace/Knowledge/KnowledgeBase/AddContentMenu.svelte`: 지식 컬렉션의 "Add webpage" 버튼을 `{#if $config?.features?.enable_webpage_attachment ?? true}`로 래핑. `import { config } from '$lib/stores';` 추가.
- `src/lib/components/chat/Settings/Account.svelte`: 성별(Gender)·생년월일(Birth Date) 입력 블록 전체를 `{#if $config?.features?.enable_user_personal_info ?? true}`로 래핑.
- `src/routes/(app)/admin/+layout.svelte`: `if ($user?.role !== 'admin' || $config?.features?.disable_admin) { await goto('/'); }` — DISABLE_ADMIN 시 관리자 페이지 접근을 프런트에서도 차단(서버 측 차단은 백엔드 파트).
- 배포 값: `docker-compose.yaml`에서 `ENABLE_IMAGE_CAPTURE=true`, `ENABLE_WEBPAGE_ATTACHMENT=false`, `ENABLE_USER_PERSONAL_INFO=false`, `DISABLE_ADMIN=false`.

**재적용 가이드**
1. stores 타입 필드 추가는 기계적 — 업스트림 `Config` 타입에 병합.
2. 각 컴포넌트에서 해당 버튼/블록을 찾아 `{#if ...}` 래핑 재적용. 업그레이드 시 버튼의 마크업이 바뀌어 있을 수 있으므로 diff를 그대로 적용하기보다 **버튼을 찾아 새로 감싸는** 방식을 권장. 검색 명령:
   ```bash
   grep -rn "enable_image_capture\|enable_webpage_attachment\|enable_user_personal_info" src/
   grep -rn "screenCaptureHandler\|Attach Webpage\|Add webpage" src/   # 업스트림 쪽 앵커
   ```
3. 웹페이지 첨부는 InputMenu와 AddContentMenu **두 곳** 모두 막아야 하며, 업스트림이 웹 첨부 진입점을 추가했는지(`showAttachWebpageModal`, `type: 'web'` 검색) 확인할 것. 참고: 실제 크롤링 차단은 백엔드에서도 이뤄져야 안전하다(프런트 숨김은 UX 차원).
4. 검증: compose에서 각 env를 false로 놓고 재기동 → 해당 메뉴가 사라지는지, `/api/config` 응답 `features`에 값이 내려오는지 확인.

**관련 커밋**
- `673d247ed` (프런트 토글 전체), `23203ac6f` (백엔드 config/features 노출), `3584a740c` (compose env)

---

### 4. Analytics 컴포넌트 — 커스텀 아님 (업스트림 0.10.2 기능) 판별

**목적/배경**
- `git diff`에 `src/lib/components/admin/Analytics/` 하위 4개 파일이 나타나 커스텀 신규로 오인할 수 있어 실측 판별했다.

**판별 결과**
- `git ls-tree ecd48e2f7 --name-only src/lib/components/admin/Analytics/` → `AnalyticsModelModal.svelte`, `ChartLine.svelte`, `Dashboard.svelte`, `ModelUsage.svelte`, `UserUsage.svelte` 5개 파일이 **업스트림 0.10.2에 이미 존재**한다. 관리자 Analytics 대시보드는 업스트림 기능이다.
- diff에 잡힌 4개 파일(`AnalyticsModelModal`, `Dashboard`, `ModelUsage`, `UserUsage`)의 변경 내용은 전부 `localStorage.token → sessionStorage.token` 치환뿐이다(섹션 2의 일괄 치환 대상). `ChartLine.svelte`는 토큰을 다루지 않아 변경 없음.
- 참고: 0.6.43 시절 문서에서 Analytics가 커스텀 신규 컴포넌트였다면, 0.10.2에서는 업스트림에 동등 기능이 편입된 상태이므로 **별도 이식 불필요**.

**재적용 가이드**
- 없음. 섹션 2의 일괄 치환에 자동 포함된다. 차기 업그레이드 시에도 이 디렉터리에 개별 커스텀을 이식하지 말 것.

**관련 커밋**
- `3584a740c` (sessionStorage 치환만)

---

### 5. 운영 스크립트 (scripts/*.sh — PostgreSQL 직결 유지보수 도구)

**목적/배경**
- 앱을 거치지 않고 DB에서 직접 수행하는 정기 운영 작업 3종: 보존정책 백스톱 삭제, 이용 현황 집계, 보안 감사 증빙.

**동작 방식 (공통)**
- 3개 스크립트 모두 POSIX sh, `psql` CLI로 `postgresql://${APP_USER}:${APP_PASSWORD}@localhost:5432/${APP_DB}` 에 직접 접속한다(호스트/포트 `localhost:5432` 하드코딩 — DB 서버 로컬 또는 포트포워딩 환경에서 실행 전제). 접속 정보는 환경변수 `APP_USER` / `APP_PASSWORD` / `APP_DB` 또는 `--app-user`/`--app-password`/`--app-db` 옵션으로 주입.

**파일별 요약**
- `scripts/cleanup_chats.sh` (259줄): N일 이상 지난 chat 행 삭제. 기본 **dry-run**이며 `--execute`를 붙여야 실제 삭제. `--days <N>`(필수), `--email`/`--user-id`(특정 사용자 한정), `--by created_at|updated_at`(기준 컬럼, 기본 created_at), `-y`(cron용 확인 생략). 실행 로그를 스크립트 디렉터리에 `cleanup_chats_YYYYmmdd_HHMMSS.log`로 남긴다. 애플리케이션 내 자동 삭제 스케줄러(섹션 1)와 별개의 수동/백스톱 수단.
- `scripts/daily_active_users.sh` (222줄): 최근 N일(기본 7일) 일별 활동 고유 사용자 수 집계. chat 테이블의 created_at/updated_at 기준, 일별 목록은 주말 포함하되 평균 DAU 계산에서는 토/일 제외. `--days <N>`.
- `scripts/chat_audit_report.sh` (255줄): 보안 감사 증빙용 대화 이력 리포트. 대화 목록(누가/언제/무슨 제목)과 `--detail <N>` 지정 시 대화 본문(role, content) 샘플까지 출력. `--days`(기본 7), `--limit`(기본 20), `--email` 필터.

**재적용 가이드**
- 신규 파일 3개 그대로 복사(업스트림 충돌 없음 — 업스트림 scripts/에는 `generate-sbom.sh`, `prepare-pyodide.js`만 존재). 단, **chat 테이블 스키마가 업그레이드에서 바뀌면 SQL을 점검**해야 한다(특히 cleanup은 chat 행만 지우므로, 0.10.2에서 추가된 `chat_message`, `shared_chat`, `automation_run.chat_id` 참조는 앱 스케줄러 쪽이 처리 — 스크립트로만 지울 경우 고아 행 여부 확인 필요).
- 검증: `--execute` 없이 dry-run 출력이 앱 화면의 대화 수와 부합하는지 확인 후 실행.

**관련 커밋**
- `3584a740c`

---

### 6. 배포 구성 (docker-compose / Dockerfile / CI 워크플로우 / 이관 런북)

**목적/배경**
- 사내 단독 배포(외부 Ollama 미사용, 로컬 이미지 빌드) 기준으로 compose를 재구성하고, 커스텀 env를 한곳에 명시한다. CI 도커 빌드는 시도 후 로컬 빌드로 회귀했다.

**동작 방식 / 변경 내용**
- `docker-compose.yaml`:
  - `ollama` 서비스·볼륨·`depends_on`·`OLLAMA_BASE_URL` 전부 제거(단일 open-webui 서비스).
  - `image: ax/open-webui:0.10.2-fix1-AppleSilicon` — 로컬 빌드 태그(빌드 머신에 따라 태그 조정 필요), `build:` 블록 유지.
  - environment에 커스텀 env 집약: `JWT_EXPIRES_IN=24h`, `WEBUI_SECRET_KEY=`, `DISABLE_ADMIN=false`, `CHAT_DELETE_ENABLED=true`, `CHAT_DELETE_DAYS=365`, `ENABLE_PASSWORD_VALIDATION=true`, `PASSWORD_BLACKLIST=kftc,admin`, `ENABLE_IMAGE_CAPTURE=true`, `ENABLE_WEBPAGE_ATTACHMENT=false`, `ENABLE_USER_PERSONAL_INFO=false`. (실운영에서는 PostgreSQL/Qdrant 등 추가 env가 별도 존재 — 이 파일은 참조용 기본형.)
- `Dockerfile` (소유는 백엔드/보안 파트와 걸침, 배포 관점 요약):
  - 비루트 기본화 `UID/GID 1000`, `HOME=/home/appusr`, 사용자명 `appusr`/`appgrp`.
  - `NODE_OPTIONS=--max-old-space-size=4096` 활성화(프런트 빌드 OOM 방지).
  - 문서 파싱 의존성 추가: `msoffcrypto-tool chardet nltk pyhwp` + nltk `punkt`,`punkt_tab` 다운로드.
  - `USE_CUDA` 기본값 false(커밋 `5560559e1`) — GPU 미사용 서버에서 이미지 용량 절감.
- `.github` 워크플로우: **최종 트리 기준 업스트림과 차이 없음**(`git diff ecd48e2f7..HEAD -- .github` 공백). 경위: `fafd8e9fa`에서 fix 브랜치용 멀티아치 도커 빌드/릴리즈 워크플로우(`docker-fix.yaml`, 202줄) 추가 → `d69a30d7e` GHCR 경로를 ax/open-webui로 변경 → `30a6b5ddf` 경로 원복+재태깅 안내 → `3807d93fa`에서 **워크플로우 삭제, 로컬 빌드로 확정**. 차기 버전에서 이식할 것 없음. 이미지 빌드는 `docker compose build` 또는 `docker build` 로컬 수행이 공식 절차.
- `MIGRATION_RUNBOOK_to_0.10.2.md` (신규, 237줄): 0.6.43-fix2.1 → 0.10.2 **DB/데이터 이관 런북**. 코드 이식이 아니라 alembic 다중 head 정리(`a1b2c3d4e5f6` 커스텀 리비전 처리), `token_jti` 컬럼 멱등 마이그레이션, config 테이블·Qdrant 컬렉션 호환성(재인덱싱 불필요 판정) 등 **이미 완료된 이관의 기록**이다. 다음 업그레이드 시 절차의 템플릿으로 참고하되 그대로 재사용하지는 말 것.
- `package.json`: `"version": "0.10.2-fix1"` — 버전 문자열에 fix 접미사(About 화면 등에 노출).
- `.gitignore`: 업스트림이 무시하던 `CLAUDE.md` 라인 제거(리포에 CLAUDE.md 커밋하기 위함, 커밋 `ce04f3f16`).

**재적용 가이드**
1. compose는 업스트림 파일을 베이스로 쓰지 말고 **우리 파일을 유지**한 채 업스트림 diff(새 서비스/헬스체크 등)만 선별 반영. env 목록이 커스텀 기능 전체의 스위치 판이므로, 백엔드 파트의 env 신설·개명 여부와 대조.
2. 이미지 태그의 버전 접미사(`0.10.2-fix1`)와 `package.json` version을 새 버전에 맞게 갱신.
3. Dockerfile은 업스트림 변경이 잦으므로 4개 포인트(UID/GID·HOME, NODE_OPTIONS, pip 파싱 의존성 RUN 블록, USE_CUDA 기본값)를 앵커 검색으로 재적용: `grep -n "max-old-space-size\|msoffcrypto\|USE_CUDA\|appusr" Dockerfile`.
4. 새 버전 이관 시 `MIGRATION_RUNBOOK_to_0.10.2.md`의 0단계(사전 조사 SQL)를 복제해 새 런북을 작성하는 방식을 권장.

**관련 커밋**
- `3584a740c` (compose·런북), `fafd8e9fa`→`d69a30d7e`→`30a6b5ddf`→`3807d93fa` (CI 도입과 철회), `5560559e1` (USE_CUDA), `ce04f3f16` (.gitignore/CLAUDE.md), `23203ac6f` (Dockerfile 대부분)

---

### 7. 오류 메시지 일반화·한글화 및 ko-KR 번역 변경

**목적/배경**
- 백엔드 원문 오류(스택·내부 URL·모델명 등)가 사용자 화면에 그대로 노출되는 것을 막고(정보 노출 방지), 사용자에게는 일반화된 한글 안내만 보여준다. 원문은 콘솔로만 남겨 디버깅 경로를 유지한다.

**동작 방식 / 변경 파일**
- `src/lib/components/chat/Messages/Error.svelte`: 응답 메시지 오류 박스가 content의 원문(문자열/객체 detail 등)을 렌더링하던 분기 전체를 삭제하고, 항상 `{$i18n.t('An error occurred. Please contact the administrator.')}` 한 줄만 표시. 원문은 `console.error('Chat Error:', content)`로 출력.
- `src/lib/apis/files/index.ts` `uploadFile()`: 비-JSON 오류 응답(HTML 등) 파싱 실패 시 `{ detail: '서버 오류가 발생했습니다. 관리자에게 문의하세요.' }`로 대체, 최종 폴백 `'파일 업로드 중 오류가 발생했습니다.'`(하드코딩 한글).
- `src/lib/components/chat/MessageInput.svelte`: 업로드 실패 토스트를 `toast.error(\`${e}\`)` → `console.error(...)` + `toast.error($i18n.t(e))`로 변경(백엔드가 i18n 키를 detail로 주는 경우 번역 노출).
- `src/lib/components/chat/Settings/Account.svelte`: 프로필 갱신·세션 조회 실패 토스트를 원문 대신 `$i18n.t('Something went wrong. Please contact administrator.')`로 통일.
- `src/lib/i18n/locales/ko-KR/translation.json` (diff 4줄):
  - 신규 키 `"An error occurred. Please contact the administrator."` → "문제가 발생했습니다. 관리자에게 문의하세요."
  - 신규 키 `"Something went wrong. Please contact administrator."` → "문제가 발생했습니다. 관리자에게 문의하세요."
  - 기존 키 `"Something went wrong :/"` 번역을 "무언가 잘못 되었습니다 :/" → "문제가 발생했습니다 :/"로 수정.
  - (그 외 대량 한글화는 없음 — 0.6.43 문서의 constants.py 백엔드 메시지 한글화는 백엔드 파트 참조.)

**재적용 가이드**
1. i18n 키 2개 추가는 ko-KR json에 병합(업스트림 json과 충돌 시 키 단위 병합, 정렬 유지).
2. Error.svelte는 업스트림에서 오류 렌더링 분기가 확장될 수 있으므로 "본문 렌더 부분을 통째로 고정 문구로 교체"라는 의도로 재적용.
3. 검증: 존재하지 않는 모델로 채팅을 시도해 오류 박스에 내부 정보가 안 보이고 고정 문구만 보이는지, 콘솔에 원문이 찍히는지 확인. 40MB 초과/차단 확장자 파일 업로드 시 토스트 문구 확인.

**관련 커밋**
- `673d247ed`

---

### 기타 — 위 1~7에 속하지 않는 src/ 변경 (파트 경계 명시)

`git diff --name-only ecd48e2f7..HEAD`의 src/ 파일 전수를 대조한 결과, 위 섹션에 배정되지 않은 변경은 전부 **세션/인증 파트(다른 담당) 소유**다. 본 파트 재적용 순서에 넣지 말 것. 목록:

- `src/routes/(app)/+layout.svelte`: 세션 타이머(1초 인터벌), 남은시간 배지·수동 연장 버튼, 활동 이벤트(click/keydown/touchstart/scroll — mousemove 제외) 기반 슬라이딩 갱신, clockSkew 보정, BroadcastChannel 토큰 전파, `logoutHandler`. (본 파트 소유분은 섹션 1의 모달 배선뿐.)
- `src/lib/components/layout/Overlay/SessionTimeoutModal.svelte` (신규, 45줄): 만료 임박 경고 모달(연장/로그아웃) — 세션 파트.
- `src/routes/+layout.svelte`: 전역 fetch 401 인터셉터, `TOKEN_EXPIRY_BUFFER 60→0`, 만료 전 서버 재확인(`isCurrentSessionUnauthorized`), 강제 새로고침 리다이렉트 — 세션 파트.
- `src/lib/apis/auths/index.ts`: `refreshSession()` API(+status 보존 throw) — 세션 파트.
- `src/lib/stores/index.ts`의 `SessionUser.expires_at`/`server_timestamp` 필드 — 세션 파트(같은 파일의 features 필드는 섹션 3).
- `src/routes/auth/+page.svelte`: 토큰 저장 sessionStorage화(섹션 2) 외에 `$user !== undefined` → `$user` 조건 수정 — 세션 파트.
- `src/lib/components/layout/Sidebar/UserMenu.svelte`, `src/lib/components/layout/Overlay/AccountPending.svelte`: 로그아웃 시 `sessionStorage.removeItem('token')` 병기(섹션 2 일부로 취급).
- 루트 문서류: `CLAUDE.md`(빌드/배포/테스트 규칙, 44줄), `CUSTOMIZATIONS_0.6.43-fix2.1.md`(구버전 명세 보존본) — 문서 파일이므로 그대로 복사.

이 외의 src/ 변경 파일(약 157개)은 전부 섹션 2의 sessionStorage 치환 단독 변경임을 실측으로 확인했다.
