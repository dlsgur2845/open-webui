# Open WebUI 0.6.43-fix2.1 → 0.10.2 DB/데이터 마이그레이션 런북

> **전제**
> - 운영 구성: **PostgreSQL**(메인 DB) + **Qdrant**(벡터 DB) + 데이터 볼륨(`/app/backend/data` — uploads, `.webui_secret_key` 등)
> - **코드 커스텀 재적용은 `CUSTOMIZATIONS_0.6.43-fix2.1.md` 기준으로 완료된 0.10.2 커스텀 이미지가 준비된 상태**를 전제로 한다. 본 런북은 **데이터·스키마·운영 전환**만 다룬다.
> - 실측 근거(2026-07-02, 업스트림 `v0.10.2` = `ecd48e2f7` 직접 대조):
>   - 0.10.2 Alembic head = `42e2978c7933` (`add_memory_path_and_meta`)
>   - 앱은 부팅 시 자동으로 `alembic upgrade head` 실행 (`config.py:run_migrations()` + 커스텀 `start.sh`)
>   - Qdrant 컬렉션 네이밍·설정 키·기본값(`ENABLE_QDRANT_MULTITENANCY_MODE=true`, `QDRANT_COLLECTION_PREFIX=open-webui`, `{prefix}_knowledge`/`_files`/`_memories`/`_web-search`/`_hash-based`)은 **0.6.43과 0.10.2가 완전히 동일** → 같은 env를 유지하면 **벡터 데이터 재인덱싱 불필요**
>   - `config` 테이블 구조(id, data JSON, version, created_at, updated_at) 동일 → 영속 설정 그대로 이전됨

---

## 0단계 — 사전 조사 (읽기 전용, 운영 영향 없음)

### 0-1. Alembic 상태 확인 — 가장 중요

```sql
SELECT version_num FROM alembic_version;
```

| 결과 | 판정 | 2단계 조치 |
|---|---|---|
| `018012973d35` 1행 | 업스트림 head만 기록 (커스텀 마이그레이션 미기록) | 정리 불필요 |
| `018012973d35` + `a1b2c3d4e5f6` 2행 | multi-head 기록 상태 | `a1b2c3d4e5f6` 행 삭제 필요 |
| `a1b2c3d4e5f6` 1행 | 커스텀 체인만 기록 (비정상) | `018012973d35`로 stamp 후 `a1b2c3d4e5f6` 삭제 |
| 그 외 리비전 | 중간 버전에서 멈춘 상태 | 개별 분석 필요 — 진행 중단하고 상태 공유 |

### 0-2. `token_jti` 컬럼 실존 여부 (alembic 기록과 별개로 확인)

```sql
SELECT column_name FROM information_schema.columns
WHERE table_name = 'auth' AND column_name = 'token_jti';
```

컬럼 유무와 무관하게 2단계의 **멱등 마이그레이션**이 안전하게 처리하지만, 리허설 결과 해석을 위해 기록해 둔다.

### 0-3. 영속 설정(config 테이블) 스냅샷

```sql
-- 토큰 수명 (코드 기본값 24h를 덮어쓰는 값이 있는지)
SELECT data->'auth'->>'jwt_expiry' AS jwt_expiry FROM config ORDER BY id DESC LIMIT 1;
-- 전체 설정 백업 (JSON 그대로 보관)
SELECT id, version, data FROM config ORDER BY id DESC LIMIT 1;
```

임베딩 모델 설정도 이 테이블에 있으므로 그대로 이전된다. **임베딩 모델을 바꾸지 않는 한 Qdrant 재인덱싱은 불필요**하다.

### 0-4. 검증 기준값 스냅샷 (전환 후 대조용)

```sql
SELECT 'user' t, count(*) FROM "user"
UNION ALL SELECT 'chat', count(*) FROM chat
UNION ALL SELECT 'file', count(*) FROM file
UNION ALL SELECT 'knowledge', count(*) FROM knowledge
UNION ALL SELECT 'auth', count(*) FROM auth;
```

### 0-5. Qdrant 상태 스냅샷

```bash
curl -s ${QDRANT_URI}/collections | jq '.result.collections[].name'
# 각 컬렉션 포인트 수 기록
curl -s ${QDRANT_URI}/collections/open-webui_knowledge | jq '.result.points_count'
curl -s ${QDRANT_URI}/collections/open-webui_files | jq '.result.points_count'
```

### 0-6. 데이터 볼륨 확인

```bash
docker exec open-webui sh -c 'ls -la /app/backend/data/ && du -sh /app/backend/data/uploads 2>/dev/null'
```

- **`.webui_secret_key` 파일 존재 확인 필수.** 현재 compose가 `WEBUI_SECRET_KEY=`(빈 값)이므로 JWT 서명키는 이 파일이다. 유실하면 전 사용자 토큰이 무효화된다(치명적이진 않으나 전원 재로그인).

---

## 1단계 — 백업 (필수, 서비스 정지 후)

```bash
# 1) 쓰기 중단
docker compose stop open-webui

# 2) PostgreSQL 전체 백업 (custom 포맷 — 선택 복원 가능)
PGPASSWORD="$APP_PASSWORD" pg_dump -h <DB_HOST> -U "$APP_USER" -d "$APP_DB" \
  -Fc -f openwebui_$(date +%Y%m%d_%H%M).dump

# 3) Qdrant 스냅샷 (컬렉션별)
for c in open-webui_knowledge open-webui_files open-webui_memories open-webui_web-search open-webui_hash-based; do
  curl -s -X POST "${QDRANT_URI}/collections/$c/snapshots"
done
# (또는 Qdrant 스토리지 볼륨/디렉터리 자체를 통째로 백업)

# 4) 데이터 볼륨 백업 (uploads + .webui_secret_key 포함)
docker run --rm -v open-webui:/data -v "$PWD":/backup alpine \
  tar czf /backup/openwebui_data_$(date +%Y%m%d_%H%M).tar.gz -C /data .

# 5) 시크릿 키 별도 사본
docker run --rm -v open-webui:/data alpine cat /data/.webui_secret_key > webui_secret_key.bak
```

---

## 2단계 — 커스텀 마이그레이션 재작성 + alembic 기록 정리

### 2-1. 0.10.2 커스텀 코드의 `token_jti` 마이그레이션은 아래처럼 작성한다

기존 파일(`a1b2c3d4e5f6_...py`)을 그대로 복사하지 말 것. **새 리비전 ID + 0.10.2 head 기반 + 멱등(idempotent) 구현**:

```python
"""add token_jti to auth (0.10.2 rebase)

Revision ID: f1a2b3c4d5e6
Revises: 42e2978c7933
"""
import sqlalchemy as sa
from alembic import op

revision = "f1a2b3c4d5e6"
down_revision = "42e2978c7933"   # 0.10.2 실제 head (실측 확인값)
branch_labels = None
depends_on = None


def upgrade():
    # 구버전 DB에는 컬럼이 이미 존재할 수 있으므로 멱등 처리
    conn = op.get_bind()
    insp = sa.inspect(conn)
    cols = [c["name"] for c in insp.get_columns("auth")]
    if "token_jti" not in cols:
        op.add_column("auth", sa.Column("token_jti", sa.String(), nullable=True))


def downgrade():
    op.drop_column("auth", "token_jti")
```

이렇게 하면 0단계에서 확인한 **컬럼 유무와 무관하게 어떤 케이스에서도 안전**하다.

### 2-2. 운영 DB의 낡은 리비전 기록 제거 (0-1 판정에 따라)

```sql
-- 케이스 B (두 행): 커스텀 리비전 행만 제거해 단일 체인으로
DELETE FROM alembic_version WHERE version_num = 'a1b2c3d4e5f6';

-- 케이스 C (a1b2c3d4e5f6 1행만): 업스트림 head로 교체
UPDATE alembic_version SET version_num = '018012973d35' WHERE version_num = 'a1b2c3d4e5f6';
```

정리 후 상태는 반드시 `018012973d35` **1행**이어야 한다. 그러면 0.10.2 첫 부팅 시
`018012973d35 → … → 42e2978c7933 → f1a2b3c4d5e6` 순서로 선형 적용된다.

---

## 3단계 — 리허설 (스테이징, 운영 전 필수)

1. 스테이징 PostgreSQL에 1단계 덤프 복원:
   ```bash
   PGPASSWORD=... pg_restore -h <STAGING_HOST> -U <USER> -d <STAGING_DB> --clean --if-exists openwebui_*.dump
   ```
2. 스테이징 DB에 2-2 정리 SQL 적용.
3. **0.10.2 커스텀 이미지**를 스테이징 DB에 연결해 기동(가능하면 Qdrant도 스냅샷 복원본으로).
4. 기동 로그에서 확인할 것:
   - alembic 리비전들이 순서대로 적용되고 마지막이 `f1a2b3c4d5e6`인지
   - 에러/트레이스백 없이 서버가 리슨 상태에 도달하는지
5. 아래 **5단계 검증 체크리스트**를 스테이징에서 전부 통과시킨 뒤에만 운영 전환 진행.
6. 리허설에서 `alembic upgrade` 소요 시간을 재서 운영 다운타임 창을 산정한다 (대략: pg_dump/restore 시간이 지배적, 마이그레이션 자체는 통상 수 분).

---

## 4단계 — 운영 전환

```text
공지 → 컨테이너 정지 → 최종 백업(1단계 반복) → alembic 정리 SQL(2-2)
→ 0.10.2 커스텀 이미지 기동 → 기동 로그 확인 → 5단계 검증 → 서비스 오픈
```

**env 유지 필수 목록** (같은 값 유지 — 바꾸면 데이터가 "사라진 것처럼" 보임):

| 변수 | 이유 |
|---|---|
| `DATABASE_URL` | 동일 PostgreSQL 지정 |
| `VECTOR_DB=qdrant`, `QDRANT_URI`, `QDRANT_API_KEY` | 동일 Qdrant 지정 |
| `ENABLE_QDRANT_MULTITENANCY_MODE` (현재 값 그대로) | 모드가 바뀌면 다른 컬렉션 구조를 조회해 기존 임베딩이 안 보임 |
| `QDRANT_COLLECTION_PREFIX` (기본 `open-webui` 그대로) | 컬렉션 이름 접두사 |
| `WEBUI_SECRET_KEY` 빈 값 + 데이터 볼륨 유지 (또는 키 값을 env로 명시) | JWT 서명키 보존 — 기존 로그인 유지 |
| 커스텀 env 일체 (`DISABLE_ADMIN`, `CHAT_DELETE_*`, `ENABLE_PASSWORD_VALIDATION`, `PASSWORD_BLACKLIST`, `ENABLE_IMAGE_CAPTURE`, `ENABLE_WEBPAGE_ATTACHMENT`, `ENABLE_USER_PERSONAL_INFO`, `JWT_EXPIRES_IN=24h`) | 커스텀 동작 유지. 0.10.2는 `JWT_EXPIRES_IN` 코드 기본값이 `4w`이므로 **env로 24h를 명시**하는 것이 안전 |

**⚠️ 전환 직후 자동 삭제 스케줄러 주의**: 현재 compose에는 `CHAT_DELETE_ENABLED=true`, `CHAT_DELETE_DAYS=1`로 되어 있다. 운영 env가 이대로라면 **첫 기동 직후 스케줄러가 1일 이상 된 채팅을 삭제**한다. 마이그레이션 검증이 끝날 때까지 `CHAT_DELETE_ENABLED=false`로 기동했다가, 검증 후 원래 정책(운영값)으로 되돌리는 것을 권장한다.

---

## 5단계 — 검증 체크리스트

| # | 항목 | 방법 / 기대 결과 |
|---|---|---|
| 1 | Alembic 상태 | `SELECT version_num FROM alembic_version;` → `f1a2b3c4d5e6` 1행 |
| 2 | 데이터 수치 | 0-4 스냅샷과 count 일치 (user/chat/file/knowledge/auth) |
| 3 | 로그인 + JTI 단일 세션 | 브라우저 A 로그인 → 브라우저 B 로그인 → A가 401/재로그인 유도되는지 |
| 4 | 세션 자동 갱신 | 로그인 후 활동(타이핑/클릭) 유지 시 만료 배지가 절반 이하로 내려가지 않고 갱신되는지 |
| 5 | 지식베이스 검색 | **기존**(전환 전 업로드) 문서가 검색되는지 → Qdrant 이전 확인 |
| 6 | 파일 업로드/다운로드 | 신규 업로드 + 기존 파일 열람 (uploads 볼륨 확인) |
| 7 | 채팅 히스토리 | 기존 대화 열람/이어쓰기 |
| 8 | 약관 모달 | 신규 브라우저(시크릿)에서 동의 모달 표시, 동의 없이는 닫기 불가 |
| 9 | 자동 삭제 스케줄러 | (재활성화 후) 로그에 주기 실행 기록, 의도한 일수 기준으로만 삭제 |
| 10 | 운영 스크립트 3종 | `cleanup_chats.sh --days N`(dry-run), `daily_active_users.sh`, `chat_audit_report.sh` — 0.10.2에서 `chat`/`user` 테이블 컬럼 변경 여부에 따라 SQL 수정 필요할 수 있음. dry-run 결과가 0-4 수치와 정합적인지 확인 |

---

## 6단계 — 롤백 절차

**스키마가 전진한 뒤에는 구버전 이미지를 그 DB에 다시 붙이지 말 것** (다운그레이드 마이그레이션은 미검증). 롤백은 백업 복원 방식으로만:

```bash
docker compose stop open-webui
# DB 복원
PGPASSWORD=... pg_restore -h <DB_HOST> -U "$APP_USER" -d "$APP_DB" --clean --if-exists openwebui_<시각>.dump
# 데이터 볼륨 복원
docker run --rm -v open-webui:/data -v "$PWD":/backup alpine \
  sh -c 'rm -rf /data/* && tar xzf /backup/openwebui_data_<시각>.tar.gz -C /data'
# Qdrant: 마이그레이션 과정에서 벡터 데이터는 변경되지 않으므로 통상 복원 불필요.
#         (임베딩 모델을 바꿨거나 이상 징후가 있으면 스냅샷 복원)
# 구버전(0.6.43-fix2.1) 이미지 기동
```

---

## 부록 — 자주 나올 실패와 원인

| 증상 | 원인 | 조치 |
|---|---|---|
| 부팅 시 `Multiple head revisions` | alembic_version 정리(2-2) 누락 또는 커스텀 마이그레이션을 옛 down_revision으로 복사 | 2단계 재수행 |
| 부팅 시 `column "token_jti" ... already exists` | 멱등 가드 없는 옛 마이그레이션 파일 사용 | 2-1의 멱등 버전으로 교체 |
| 지식베이스 검색 결과 0건 | Qdrant env 변경(prefix/멀티테넌시/URI) 또는 임베딩 모델 변경 | env 원복, 모델 변경 시 재인덱싱 |
| 전 사용자 강제 로그아웃 | `.webui_secret_key` 유실 또는 `WEBUI_SECRET_KEY` 변경 | 키 사본 복원 |
| 기동 직후 채팅 대량 삭제 | `CHAT_DELETE_ENABLED=true` + 낮은 `CHAT_DELETE_DAYS`로 스케줄러 즉시 동작 | 4단계 주의사항 참조 (검증 완료까지 비활성화) |
| 토큰이 4주짜리로 발급됨 | 0.10.2 기본값 `4w` + env/config 미지정 | `JWT_EXPIRES_IN=24h` env 명시 또는 관리자 UI 설정 |
