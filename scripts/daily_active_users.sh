#!/bin/sh
#
# Open WebUI 일별 접속 사용자 수 조회 스크립트 (PostgreSQL)
#
# 최근 7일간 일별 접속(활동)한 고유 사용자 수를 조회합니다.
# - chat 테이블의 created_at/updated_at 기준 활동 사용자 집계
# - user 테이블의 last_active_at 기준 활동 사용자 집계
# 두 가지 데이터를 종합하여 일별 DAU(Daily Active Users)를 산출합니다.
#
# 사용법:
#   # 최근 7일 일별 접속 사용자 수 조회
#   ./daily_active_users.sh
#
#   # 조회 기간 변경 (예: 14일)
#   ./daily_active_users.sh --days 14
#
#   # DB 접속 정보 직접 지정
#   ./daily_active_users.sh --app-user myuser --app-password mypass --app-db mydb
#
# 환경변수:
#   APP_USER      PostgreSQL 사용자
#   APP_PASSWORD  PostgreSQL 비밀번호
#   APP_DB        PostgreSQL 데이터베이스명
#

set -e

# 기본값
DAYS=7
APP_USER="${APP_USER:-}"
APP_PASSWORD="${APP_PASSWORD:-}"
APP_DB="${APP_DB:-}"

usage() {
    echo "사용법: $0 [옵션]"
    echo ""
    echo "옵션:"
    echo "  --days <N>                조회 기간 (기본: 7일)"
    echo "  --app-user <사용자>       DB 사용자 (미지정 시 APP_USER 환경변수)"
    echo "  --app-password <비밀번호> DB 비밀번호 (미지정 시 APP_PASSWORD 환경변수)"
    echo "  --app-db <DB명>           DB 이름 (미지정 시 APP_DB 환경변수)"
    echo "  -h, --help                도움말"
    exit 1
}

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
        --days)         require_arg "$1" "${2:-}"; DAYS="$2"; shift 2 ;;
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

# psql 실행 헬퍼
run_sql() {
    psql "$DB_URL" -t -A -c "$1"
}

# 현재 시각
NOW_DISPLAY=$(date '+%Y-%m-%d %H:%M:%S')

# 전체 등록 사용자 수
TOTAL_USERS=$(run_sql "SELECT COUNT(*) FROM \"user\";")

echo "============================================================"
echo "Open WebUI 일별 접속 사용자 수 (DAU) 리포트"
echo "============================================================"
echo "  조회 시각     : ${NOW_DISPLAY}"
echo "  조회 기간     : 최근 ${DAYS}일"
echo "  전체 등록 사용자: ${TOTAL_USERS}명"
echo "============================================================"
echo ""

# 일별 접속 사용자 수 조회
# chat 테이블의 created_at, updated_at과 user 테이블의 last_active_at를
# UNION하여 일별 고유 사용자 수를 집계합니다.
echo "--- 일별 접속 사용자 수 (최근 ${DAYS}일) ---"
echo ""
printf "  %-12s  %s\n" "날짜" "접속 사용자 수"
printf "  %-12s  %s\n" "------------" "--------------"

run_sql "
WITH date_range AS (
    SELECT generate_series(
        (CURRENT_DATE - INTERVAL '1 day' * $(( DAYS - 1 )))::date,
        CURRENT_DATE,
        '1 day'::interval
    )::date AS day
),
active_users AS (
    -- chat 생성 기준 활동 사용자
    SELECT DISTINCT
        to_timestamp(created_at)::date AS active_date,
        user_id
    FROM chat
    WHERE created_at >= EXTRACT(EPOCH FROM (CURRENT_DATE - INTERVAL '1 day' * $(( DAYS - 1 ))))
      AND user_id NOT LIKE 'shared-%%'

    UNION

    -- chat 업데이트 기준 활동 사용자
    SELECT DISTINCT
        to_timestamp(updated_at)::date AS active_date,
        user_id
    FROM chat
    WHERE updated_at >= EXTRACT(EPOCH FROM (CURRENT_DATE - INTERVAL '1 day' * $(( DAYS - 1 ))))
      AND user_id NOT LIKE 'shared-%%'
)
SELECT
    dr.day,
    COALESCE(COUNT(DISTINCT au.user_id), 0) AS dau
FROM date_range dr
LEFT JOIN active_users au ON dr.day = au.active_date
GROUP BY dr.day
ORDER BY dr.day ASC;
" | while IFS='|' read -r day count; do
    printf "  %-12s  %s명\n" "$day" "$count"
done

echo ""
echo "------------------------------------------------------------"

# 7일 평균 DAU
AVG_DAU=$(run_sql "
WITH active_users AS (
    SELECT DISTINCT
        to_timestamp(created_at)::date AS active_date,
        user_id
    FROM chat
    WHERE created_at >= EXTRACT(EPOCH FROM (CURRENT_DATE - INTERVAL '1 day' * $(( DAYS - 1 ))))
      AND user_id NOT LIKE 'shared-%%'

    UNION

    SELECT DISTINCT
        to_timestamp(updated_at)::date AS active_date,
        user_id
    FROM chat
    WHERE updated_at >= EXTRACT(EPOCH FROM (CURRENT_DATE - INTERVAL '1 day' * $(( DAYS - 1 ))))
      AND user_id NOT LIKE 'shared-%%'
),
daily_counts AS (
    SELECT
        active_date,
        COUNT(DISTINCT user_id) AS dau
    FROM active_users
    GROUP BY active_date
)
SELECT ROUND(AVG(dau), 1) FROM daily_counts;
")

echo ""
echo "  ${DAYS}일 평균 DAU: ${AVG_DAU}명"
echo ""

# 오늘 접속 사용자 목록
echo "--- 오늘 접속한 사용자 목록 ---"
echo ""
printf "  %-20s  %-30s  %s\n" "이름" "이메일" "마지막 활동"
printf "  %-20s  %-30s  %s\n" "--------------------" "------------------------------" "-------------------"

run_sql "
SELECT DISTINCT
    u.name,
    u.email,
    to_char(to_timestamp(u.last_active_at), 'YYYY-MM-DD HH24:MI:SS') AS last_active
FROM \"user\" u
WHERE EXISTS (
    SELECT 1 FROM chat c
    WHERE c.user_id = u.id
      AND (
          to_timestamp(c.created_at)::date = CURRENT_DATE
          OR to_timestamp(c.updated_at)::date = CURRENT_DATE
      )
      AND c.user_id NOT LIKE 'shared-%%'
)
ORDER BY u.name ASC;
" | while IFS='|' read -r name email last_active; do
    printf "  %-20s  %-30s  %s\n" "$name" "$email" "$last_active"
done

echo ""
echo "============================================================"
