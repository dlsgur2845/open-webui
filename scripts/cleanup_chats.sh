#!/bin/sh
#
# Open WebUI 채팅 내역 정리 스크립트 (PostgreSQL)
#
# 사용법:
#   # 30일 이상 된 전체 사용자 채팅 삭제 (dry-run)
#   ./cleanup_chats.sh --days 30
#
#   # 실제 삭제 실행
#   ./cleanup_chats.sh --days 30 --execute
#
#   # 특정 사용자 이메일로 지정
#   ./cleanup_chats.sh --days 30 --email user@example.com --execute
#
#   # 특정 사용자 ID로 지정
#   ./cleanup_chats.sh --days 30 --user-id abc-123 --execute
#
#   # updated_at 기준으로 삭제 (기본은 created_at)
#   ./cleanup_chats.sh --days 30 --by updated_at --execute
#
# 환경변수:
#   APP_USER      PostgreSQL 사용자
#   APP_PASSWORD  PostgreSQL 비밀번호
#   APP_DB        PostgreSQL 데이터베이스명
#

set -e

# 기본값
DAYS=""
EMAIL=""
USER_ID=""
DATE_COL="created_at"
EXECUTE=false
APP_USER="${APP_USER:-}"
APP_PASSWORD="${APP_PASSWORD:-}"
APP_DB="${APP_DB:-}"

usage() {
    echo "사용법: $0 --days <일수> [옵션]"
    echo ""
    echo "필수:"
    echo "  --days <N>              N일보다 오래된 채팅 삭제"
    echo ""
    echo "옵션:"
    echo "  --email <이메일>        특정 사용자 이메일 (미지정 시 전체)"
    echo "  --user-id <ID>          특정 사용자 ID (미지정 시 전체)"
    echo "  --by <created_at|updated_at>  기준 컬럼 (기본: created_at)"
    echo "  --execute               실제 삭제 실행 (미지정 시 dry-run)"
    echo "  --app-user <사용자>     DB 사용자 (미지정 시 APP_USER 환경변수)"
    echo "  --app-password <비밀번호> DB 비밀번호 (미지정 시 APP_PASSWORD 환경변수)"
    echo "  --app-db <DB명>         DB 이름 (미지정 시 APP_DB 환경변수)"
    echo "  -y, --yes               확인 프롬프트 건너뛰기 (cron용)"
    echo "  -h, --help              도움말"
    exit 1
}

AUTO_YES=false

# 인자 없으면 도움말 출력
if [ $# -eq 0 ]; then
    usage
fi

# 값이 필요한 옵션의 인자 존재 여부 확인 헬퍼
require_arg() {
    if [ $# -lt 2 ] || echo "$2" | grep -q '^--'; then
        echo "[ERROR] '$1' 옵션에는 값이 필요합니다."
        usage
    fi
}

# 인자 파싱
while [ $# -gt 0 ]; do
    case "$1" in
        --days)        require_arg "$1" "${2:-}"; DAYS="$2"; shift 2 ;;
        --email)       require_arg "$1" "${2:-}"; EMAIL="$2"; shift 2 ;;
        --user-id)     require_arg "$1" "${2:-}"; USER_ID="$2"; shift 2 ;;
        --by)          require_arg "$1" "${2:-}"; DATE_COL="$2"; shift 2 ;;
        --execute)     EXECUTE=true; shift ;;
        --app-user)     require_arg "$1" "${2:-}"; APP_USER="$2"; shift 2 ;;
        --app-password) require_arg "$1" "${2:-}"; APP_PASSWORD="$2"; shift 2 ;;
        --app-db)       require_arg "$1" "${2:-}"; APP_DB="$2"; shift 2 ;;
        -y|--yes)      AUTO_YES=true; shift ;;
        -h|--help)     usage ;;
        *)             echo "[ERROR] 알 수 없는 옵션: $1"; usage ;;
    esac
done

# 필수값 검증
if [ -z "$DAYS" ]; then
    echo "[ERROR] --days 옵션은 필수입니다."
    usage
fi

if [ -z "$APP_USER" ] || [ -z "$APP_PASSWORD" ] || [ -z "$APP_DB" ]; then
    echo "[ERROR] APP_USER, APP_PASSWORD, APP_DB 환경변수를 설정하거나 해당 옵션을 사용하세요."
    exit 1
fi

# 로그 파일 설정 (스크립트와 동일 디렉토리)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_FILE="${SCRIPT_DIR}/cleanup_chats.log"

# 로그 출력 헬퍼: 콘솔 + 파일 동시 출력
log() {
    echo "$@" | tee -a "$LOG_FILE"
}

# 로그 시작 구분선
{
    echo ""
    echo "================================================================"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 실행 시작"
    echo "  실행 인자: --days ${DAYS} --by ${DATE_COL} ${EMAIL:+--email $EMAIL} ${USER_ID:+--user-id $USER_ID} ${EXECUTE:+--execute}"
    echo "================================================================"
} >> "$LOG_FILE"

DB_URL="postgresql://${APP_USER}:${APP_PASSWORD}@localhost:5432/${APP_DB}"

if [ "$DATE_COL" != "created_at" ] && [ "$DATE_COL" != "updated_at" ]; then
    echo "[ERROR] --by 옵션은 created_at 또는 updated_at만 가능합니다."
    exit 1
fi

# psql 실행 헬퍼
run_sql() {
    psql "$DB_URL" -t -A -c "$1"
}

# cutoff epoch 계산
CUTOFF_EPOCH=$(( $(date +%s) - DAYS * 86400 ))
CUTOFF_DISPLAY=$(date -d "@${CUTOFF_EPOCH}" "+%Y-%m-%d %H:%M:%S" 2>/dev/null \
    || date -r "${CUTOFF_EPOCH}" "+%Y-%m-%d %H:%M:%S" 2>/dev/null \
    || echo "${CUTOFF_EPOCH}")

log "============================================================"
log "Open WebUI 채팅 내역 정리"
log "============================================================"
log "  기준 컬럼 : ${DATE_COL}"
log "  삭제 기준 : ${DAYS}일 이전 (${CUTOFF_DISPLAY} 이전)"

# 이메일로 user_id 조회
if [ -n "$EMAIL" ]; then
    USER_ID=$(run_sql "SELECT id FROM \"user\" WHERE email = '$(echo "$EMAIL" | sed "s/'/''/g")' LIMIT 1;")
    if [ -z "$USER_ID" ]; then
        log "[ERROR] 이메일 '${EMAIL}'에 해당하는 사용자를 찾을 수 없습니다."
        exit 1
    fi
    USER_NAME=$(run_sql "SELECT name FROM \"user\" WHERE id = '${USER_ID}';")
    log "  사용자 확인: id=${USER_ID}, name=${USER_NAME}, email=${EMAIL}"
fi

if [ -n "$USER_ID" ]; then
    log "  대상 사용자: ${USER_ID}"
    USER_FILTER="AND user_id = '${USER_ID}'"
else
    log "  대상 사용자: 전체"
    USER_FILTER=""
fi

# 대상 건수 확인
COUNT=$(run_sql "SELECT COUNT(*) FROM chat WHERE ${DATE_COL} < ${CUTOFF_EPOCH} AND user_id NOT LIKE 'shared-%%' ${USER_FILTER};")
log "  대상 채팅 수: ${COUNT}건"

if [ "$COUNT" -eq 0 ] 2>/dev/null; then
    log ""
    log "삭제 대상이 없습니다."
    exit 0
fi

# 미리보기
log ""
log "--- 삭제 대상 미리보기 (최대 10건) ---"
run_sql "
SELECT
    LEFT(id, 8) || '...' AS id,
    LEFT(user_id, 16) AS user_id,
    LEFT(COALESCE(title, '(제목없음)'), 40) AS title,
    to_timestamp(created_at)::date AS created,
    to_timestamp(updated_at)::date AS updated
FROM chat
WHERE ${DATE_COL} < ${CUTOFF_EPOCH}
  AND user_id NOT LIKE 'shared-%%'
  ${USER_FILTER}
ORDER BY ${DATE_COL} ASC
LIMIT 10;
" | while IFS='|' read -r cid cuser ctitle ccreated cupdated; do
    printf "  [%s] user=%-16s title=%-40s created=%s updated=%s\n" \
        "$cid" "$cuser" "$ctitle" "$ccreated" "$cupdated"
done | tee -a "$LOG_FILE"

# dry-run 모드
if [ "$EXECUTE" != true ]; then
    log ""
    log "[DRY-RUN] --execute 플래그 없이 실행되었습니다. 실제 삭제는 수행되지 않았습니다."
    exit 0
fi

# 최종 확인
if [ "$AUTO_YES" != true ]; then
    printf "\n정말로 %s건의 채팅을 삭제하시겠습니까? (yes/no): " "$COUNT"
    read -r CONFIRM
    if [ "$CONFIRM" != "yes" ]; then
        log "취소되었습니다."
        exit 0
    fi
fi

# 삭제 대상 전체 목록을 로그 파일에 기록 (콘솔에는 출력하지 않음)
echo "--- 삭제 대상 전체 목록 (${COUNT}건) ---" >> "$LOG_FILE"
run_sql "
SELECT
    id,
    user_id,
    LEFT(COALESCE(title, '(제목없음)'), 60) AS title,
    to_timestamp(created_at)::timestamp(0) AS created,
    to_timestamp(updated_at)::timestamp(0) AS updated
FROM chat
WHERE ${DATE_COL} < ${CUTOFF_EPOCH}
  AND user_id NOT LIKE 'shared-%%'
  ${USER_FILTER}
ORDER BY ${DATE_COL} ASC;
" >> "$LOG_FILE"
echo "--- 전체 목록 끝 ---" >> "$LOG_FILE"

# shared 채팅 삭제
SHARED_DELETED=$(run_sql "
DELETE FROM chat
WHERE user_id IN (
    SELECT 'shared-' || c.id
    FROM chat c
    WHERE c.${DATE_COL} < ${CUTOFF_EPOCH}
      AND c.user_id NOT LIKE 'shared-%%'
      ${USER_FILTER}
);
SELECT COUNT(*);
" 2>/dev/null || echo "0")
log "  shared 채팅 삭제 완료"

# 본 채팅 삭제
MAIN_DELETED=$(run_sql "
DELETE FROM chat
WHERE ${DATE_COL} < ${CUTOFF_EPOCH}
  AND user_id NOT LIKE 'shared-%%'
  ${USER_FILTER};
")
log ""
log "[완료] 채팅 삭제가 완료되었습니다."
log "  실행 시각   : $(date '+%Y-%m-%d %H:%M:%S')"
log "  삭제 대상   : ${COUNT}건"
log "  기준 컬럼   : ${DATE_COL}"
log "  기준 일수   : ${DAYS}일 이전 (${CUTOFF_DISPLAY} 이전)"
log "  대상 사용자 : ${USER_ID:-전체}"

# 삭제 후 잔여 확인
REMAINING=$(run_sql "SELECT COUNT(*) FROM chat WHERE user_id NOT LIKE 'shared-%%' ${USER_FILTER};")
log "  남은 채팅 수: ${REMAINING}건"
log "------------------------------------------------------------"
