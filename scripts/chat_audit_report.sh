#!/bin/sh
#
# Open WebUI 대화 감사 추적 리포트 스크립트 (PostgreSQL)
#
# 보안 감사 증빙용: 사용자 대화 이력 및 상세 내용 조회
# - 대화 목록: 누가, 언제, 어떤 대화를 했는지
# - 상세 내용: 대화 본문 (role, content) 샘플
#
# 사용법:
#   # 최근 7일 대화 이력 조회 (목록만)
#   ./chat_audit_report.sh
#
#   # 상세 대화 내용 포함 (최근 N건의 대화 본문 표시)
#   ./chat_audit_report.sh --detail 5
#
#   # 조회 기간 변경 (예: 30일)
#   ./chat_audit_report.sh --days 30
#
#   # 특정 사용자 이메일로 필터
#   ./chat_audit_report.sh --email hong@example.com
#
#   # DB 접속 정보 직접 지정
#   ./chat_audit_report.sh --app-user myuser --app-password mypass --app-db mydb
#
# 환경변수:
#   APP_USER      PostgreSQL 사용자
#   APP_PASSWORD  PostgreSQL 비밀번호
#   APP_DB        PostgreSQL 데이터베이스명
#

set -e

# 기본값
DAYS=7
DETAIL=0
LIMIT=20
EMAIL=""
APP_USER="${APP_USER:-}"
APP_PASSWORD="${APP_PASSWORD:-}"
APP_DB="${APP_DB:-}"

usage() {
    echo "사용법: $0 [옵션]"
    echo ""
    echo "옵션:"
    echo "  --days <N>                조회 기간 (기본: 7일)"
    echo "  --detail <N>              상세 대화 내용 표시 건수 (기본: 0=미표시)"
    echo "  --limit <N>               대화 목록 최대 표시 건수 (기본: 20)"
    echo "  --email <이메일>          특정 사용자 필터"
    echo "  --app-user <사용자>       DB 사용자 (미지정 시 APP_USER 환경변수)"
    echo "  --app-password <비밀번호> DB 비밀번호 (미지정 시 APP_PASSWORD 환경변수)"
    echo "  --app-db <DB명>           DB 이름 (미지정 시 APP_DB 환경변수)"
    echo "  -h, --help                도움말"
    exit 1
}

require_arg() {
    if [ $# -lt 2 ] || echo "$2" | grep -q '^--'; then
        echo "[ERROR] '$1' 옵션에는 값이 필요합니다."
        usage
    fi
}

# 인자 파싱
while [ $# -gt 0 ]; do
    case "$1" in
        --days)         require_arg "$1" "${2:-}"; DAYS="$2"; shift 2 ;;
        --detail)       require_arg "$1" "${2:-}"; DETAIL="$2"; shift 2 ;;
        --limit)        require_arg "$1" "${2:-}"; LIMIT="$2"; shift 2 ;;
        --email)        require_arg "$1" "${2:-}"; EMAIL="$2"; shift 2 ;;
        --app-user)     require_arg "$1" "${2:-}"; APP_USER="$2"; shift 2 ;;
        --app-password) require_arg "$1" "${2:-}"; APP_PASSWORD="$2"; shift 2 ;;
        --app-db)       require_arg "$1" "${2:-}"; APP_DB="$2"; shift 2 ;;
        -h|--help)      usage ;;
        *)              echo "[ERROR] 알 수 없는 옵션: $1"; usage ;;
    esac
done

# 필수값 검증
if [ -z "$APP_USER" ] || [ -z "$APP_PASSWORD" ] || [ -z "$APP_DB" ]; then
    echo "[ERROR] APP_USER, APP_PASSWORD, APP_DB 환경변수를 설정하거나 해당 옵션을 사용하세요."
    exit 1
fi

DB_URL="postgresql://${APP_USER}:${APP_PASSWORD}@localhost:5432/${APP_DB}"

run_sql() {
    psql "$DB_URL" -t -A -c "$1"
}

NOW_DISPLAY=$(date '+%Y-%m-%d %H:%M:%S')

# 이메일 필터 조건
if [ -n "$EMAIL" ]; then
    EMAIL_FILTER="AND u.email = '${EMAIL}'"
    EMAIL_DISPLAY="$EMAIL"
else
    EMAIL_FILTER=""
    EMAIL_DISPLAY="전체"
fi

# 전체 통계
TOTAL_CHATS=$(run_sql "
SELECT COUNT(*)
FROM chat c
JOIN \"user\" u ON c.user_id = u.id
WHERE c.user_id NOT LIKE 'shared-%%'
  AND c.created_at >= EXTRACT(EPOCH FROM (CURRENT_DATE - INTERVAL '1 day' * $(( DAYS - 1 ))))
  ${EMAIL_FILTER};
")

TOTAL_USERS_WITH_CHATS=$(run_sql "
SELECT COUNT(DISTINCT c.user_id)
FROM chat c
JOIN \"user\" u ON c.user_id = u.id
WHERE c.user_id NOT LIKE 'shared-%%'
  AND c.created_at >= EXTRACT(EPOCH FROM (CURRENT_DATE - INTERVAL '1 day' * $(( DAYS - 1 ))))
  ${EMAIL_FILTER};
")

echo "============================================================"
echo "Open WebUI 대화 감사 추적 리포트"
echo "============================================================"
echo "  조회 시각     : ${NOW_DISPLAY}"
echo "  조회 기간     : 최근 ${DAYS}일"
echo "  대상 사용자   : ${EMAIL_DISPLAY}"
echo "  기간 내 대화 수: ${TOTAL_CHATS}건"
echo "  대화 사용자 수 : ${TOTAL_USERS_WITH_CHATS}명"
echo "============================================================"
echo ""

# 1. 대화 목록
echo "--- 대화 목록 (최근 ${DAYS}일, 최대 ${LIMIT}건) ---"
echo ""
printf "  %-20s  %-28s  %-40s  %-19s  %-19s\n" "사용자" "이메일" "대화 제목" "생성일시" "최종수정일시"
printf "  %-20s  %-28s  %-40s  %-19s  %-19s\n" "--------------------" "----------------------------" "----------------------------------------" "-------------------" "-------------------"

run_sql "
SELECT
    LEFT(u.name, 20),
    LEFT(u.email, 28),
    LEFT(REPLACE(c.title, E'\n', ' '), 40),
    TO_CHAR(TO_TIMESTAMP(c.created_at), 'YYYY-MM-DD HH24:MI:SS'),
    TO_CHAR(TO_TIMESTAMP(c.updated_at), 'YYYY-MM-DD HH24:MI:SS')
FROM chat c
JOIN \"user\" u ON c.user_id = u.id
WHERE c.user_id NOT LIKE 'shared-%%'
  AND c.created_at >= EXTRACT(EPOCH FROM (CURRENT_DATE - INTERVAL '1 day' * $(( DAYS - 1 ))))
  ${EMAIL_FILTER}
ORDER BY c.updated_at DESC
LIMIT ${LIMIT};
" | while IFS='|' read -r name email title created updated; do
    printf "  %-20s  %-28s  %-40s  %-19s  %-19s\n" "$name" "$email" "$title" "$created" "$updated"
done

echo ""
echo "------------------------------------------------------------"

# 2. 일별 대화 건수 통계
echo ""
echo "--- 일별 대화 건수 (최근 ${DAYS}일) ---"
echo ""
printf "  %-12s  %-4s  %s\n" "날짜" "요일" "대화 건수"
printf "  %-12s  %-4s  %s\n" "------------" "----" "---------"

run_sql "
WITH date_range AS (
    SELECT generate_series(
        (CURRENT_DATE - INTERVAL '1 day' * $(( DAYS - 1 )))::date,
        CURRENT_DATE,
        '1 day'::interval
    )::date AS day
)
SELECT
    dr.day,
    CASE EXTRACT(DOW FROM dr.day)
        WHEN 0 THEN '일'
        WHEN 1 THEN '월'
        WHEN 2 THEN '화'
        WHEN 3 THEN '수'
        WHEN 4 THEN '목'
        WHEN 5 THEN '금'
        WHEN 6 THEN '토'
    END AS dow,
    COALESCE(COUNT(c.id), 0) AS chat_count
FROM date_range dr
LEFT JOIN chat c
    ON TO_TIMESTAMP(c.created_at)::date = dr.day
    AND c.user_id NOT LIKE 'shared-%%'
GROUP BY dr.day
ORDER BY dr.day ASC;
" | while IFS='|' read -r day dow count; do
    printf "  %-12s  %-4s  %s건\n" "$day" "$dow" "$count"
done

echo ""
echo "------------------------------------------------------------"

# 3. 상세 대화 내용 (옵션)
if [ "$DETAIL" -gt 0 ]; then
    echo ""
    echo "--- 상세 대화 내용 (최근 ${DETAIL}건 샘플) ---"

    run_sql "
    SELECT
        c.id,
        u.name,
        u.email,
        REPLACE(c.title, E'\n', ' '),
        TO_CHAR(TO_TIMESTAMP(c.created_at), 'YYYY-MM-DD HH24:MI:SS')
    FROM chat c
    JOIN \"user\" u ON c.user_id = u.id
    WHERE c.user_id NOT LIKE 'shared-%%'
      AND c.created_at >= EXTRACT(EPOCH FROM (CURRENT_DATE - INTERVAL '1 day' * $(( DAYS - 1 ))))
      ${EMAIL_FILTER}
    ORDER BY c.updated_at DESC
    LIMIT ${DETAIL};
    " | while IFS='|' read -r chat_id name email title created; do
        echo ""
        echo "  ============================================================"
        echo "  대화 ID  : ${chat_id}"
        echo "  사용자   : ${name} (${email})"
        echo "  제목     : ${title}"
        echo "  생성일시 : ${created}"
        echo "  ------------------------------------------------------------"

        run_sql "
        SELECT
            msg->>'role' AS role,
            LEFT(REPLACE(msg->>'content', E'\n', ' '), 100) AS content
        FROM chat,
             json_array_elements(chat.chat->'messages') AS msg
        WHERE chat.id = '${chat_id}'
          AND msg->>'role' IN ('user', 'assistant')
        LIMIT 6;
        " | while IFS='|' read -r role content; do
            if [ "$role" = "user" ]; then
                printf "  [사용자]  %s\n" "$content"
            else
                printf "  [AI응답]  %s\n" "$content"
            fi
        done
    done

    echo ""
    echo "  ============================================================"
fi

echo ""
echo "============================================================"
echo "  * 본 리포트는 Open WebUI DB(chat 테이블)에 저장된"
echo "    대화 이력을 기반으로 생성되었습니다."
echo "  * chat 컬럼(JSON)에 전체 대화 내용(role, content)이"
echo "    보존되어 감사 추적이 가능합니다."
echo "============================================================"
