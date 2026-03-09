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
#   DATABASE_URL  PostgreSQL 접속 URL (예: postgresql://user:pass@host:5432/dbname)
#

set -e

# 기본값
DAYS=""
EMAIL=""
USER_ID=""
DATE_COL="created_at"
EXECUTE=false
DB_URL="${DATABASE_URL:-}"

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
    echo "  --database-url <URL>    PostgreSQL URL (미지정 시 DATABASE_URL 환경변수)"
    echo "  -y, --yes               확인 프롬프트 건너뛰기 (cron용)"
    echo "  -h, --help              도움말"
    exit 1
}

AUTO_YES=false

# 인자 없으면 도움말 출력
if [ $# -eq 0 ]; then
    usage
fi

# 인자 파싱
while [ $# -gt 0 ]; do
    case "$1" in
        --days)        DAYS="$2"; shift 2 ;;
        --email)       EMAIL="$2"; shift 2 ;;
        --user-id)     USER_ID="$2"; shift 2 ;;
        --by)          DATE_COL="$2"; shift 2 ;;
        --execute)     EXECUTE=true; shift ;;
        --database-url) DB_URL="$2"; shift 2 ;;
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

if [ -z "$DB_URL" ]; then
    echo "[ERROR] DATABASE_URL 환경변수를 설정하거나 --database-url 옵션을 사용하세요."
    exit 1
fi

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

echo "============================================================"
echo "Open WebUI 채팅 내역 정리"
echo "============================================================"
echo "  기준 컬럼 : ${DATE_COL}"
echo "  삭제 기준 : ${DAYS}일 이전 (${CUTOFF_DISPLAY} 이전)"

# 이메일로 user_id 조회
if [ -n "$EMAIL" ]; then
    USER_ID=$(run_sql "SELECT id FROM \"user\" WHERE email = '$(echo "$EMAIL" | sed "s/'/''/g")' LIMIT 1;")
    if [ -z "$USER_ID" ]; then
        echo "[ERROR] 이메일 '${EMAIL}'에 해당하는 사용자를 찾을 수 없습니다."
        exit 1
    fi
    USER_NAME=$(run_sql "SELECT name FROM \"user\" WHERE id = '${USER_ID}';")
    echo "  사용자 확인: id=${USER_ID}, name=${USER_NAME}, email=${EMAIL}"
fi

if [ -n "$USER_ID" ]; then
    echo "  대상 사용자: ${USER_ID}"
    USER_FILTER="AND user_id = '${USER_ID}'"
else
    echo "  대상 사용자: 전체"
    USER_FILTER=""
fi

# 대상 건수 확인
COUNT=$(run_sql "SELECT COUNT(*) FROM chat WHERE ${DATE_COL} < ${CUTOFF_EPOCH} AND user_id NOT LIKE 'shared-%%' ${USER_FILTER};")
echo "  대상 채팅 수: ${COUNT}건"

if [ "$COUNT" -eq 0 ] 2>/dev/null; then
    echo ""
    echo "삭제 대상이 없습니다."
    exit 0
fi

# 미리보기
echo ""
echo "--- 삭제 대상 미리보기 (최대 10건) ---"
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
done

# dry-run 모드
if [ "$EXECUTE" != true ]; then
    echo ""
    echo "[DRY-RUN] --execute 플래그 없이 실행되었습니다. 실제 삭제는 수행되지 않았습니다."
    exit 0
fi

# 최종 확인
if [ "$AUTO_YES" != true ]; then
    printf "\n정말로 %s건의 채팅을 삭제하시겠습니까? (yes/no): " "$COUNT"
    read -r CONFIRM
    if [ "$CONFIRM" != "yes" ]; then
        echo "취소되었습니다."
        exit 0
    fi
fi

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
echo "  shared 채팅 삭제 완료"

# 본 채팅 삭제
MAIN_DELETED=$(run_sql "
DELETE FROM chat
WHERE ${DATE_COL} < ${CUTOFF_EPOCH}
  AND user_id NOT LIKE 'shared-%%'
  ${USER_FILTER};
")
echo ""
echo "[완료] 채팅 삭제가 완료되었습니다."

# 삭제 후 잔여 확인
REMAINING=$(run_sql "SELECT COUNT(*) FROM chat WHERE user_id NOT LIKE 'shared-%%' ${USER_FILTER};")
echo "  남은 채팅 수: ${REMAINING}건"
