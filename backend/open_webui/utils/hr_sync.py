"""
인사·조직 마스터 데이터 일일 동기화.

사내 인사 REST API 에서 직원·부서·공휴일 스냅샷을 매일 같은 시각에 한 번 받아 파일로
저장하고, 직원+부서를 합쳐 조직도(org.json)를 파생 생성한다. 생성 파일 4종:

    emp.json / dept.json / holiday.json / org.json
    (+ 일자 보관본 <이름>.<YYYY-MM-DD>.json — 기본 7일 보관)

읽는 쪽(Functions 필터, 외부 도구 등)은 이 파일들을 **읽기만** 한다. 저장은 임시파일 +
os.replace 라 원자적이어서, 쓰는 도중에 읽어도 깨진 JSON 을 보지 않는다.

설정은 전부 환경변수다 — 관리자 UI·DB config 를 거치지 않는다. API 주소·헤더 등 사내
정보를 저장소가 아니라 배포 compose 에만 두기 위한 선택이며, 그래서 값이 바뀌면 재기동이
필요하다. HR_SYNC_ENABLED 가 꺼져 있으면(기본) 백그라운드 태스크 자체가 뜨지 않는다.

날짜 라벨(파일명·generated)은 HR_SYNC_ROLLOVER_HOUR 기준이다. 읽는 쪽이 "오늘자 파일이
있는가"를 같은 기준으로 판정하므로, 실행 시각(HR_SYNC_TIME)은 롤오버 시각 이후여야 한다
(그 전이면 전날 라벨로 저장돼 읽는 쪽이 계속 낡았다고 본다 — 기동 시 경고를 남긴다).

Environment:
    HR_SYNC_ENABLED               – 기능 사용 여부 (기본 false)
    HR_SYNC_TIME                  – 매일 실행 시각 HH:MM (기본 08:00 = 롤오버와 동일 시각,
                                    HR_SYNC_TZ 기준. 종전 요청 트리거 수집과 같은 타이밍)
    HR_SYNC_TZ                    – 실행 시각·날짜 라벨 기준 타임존 (기본 Asia/Seoul)
    HR_SYNC_DIR                   – 스냅샷 저장 디렉터리 (기본 <DATA_DIR>/hr)
    HR_SYNC_EMP_API_URL           – 직원 스냅샷 API (비우면 미수집)
    HR_SYNC_DEPT_API_URL          – 부서 스냅샷 API (비우면 미수집)
    HR_SYNC_HOLIDAY_API_URL       – 공휴일 API (fromDate·toDate 파라미터. 비우면 미수집)
    HR_SYNC_API_HEADER_NAME       – 시스템 식별용 추가 요청 헤더 이름 (비우면 미전송)
    HR_SYNC_API_HEADER_VALUE      – 위 헤더 값
    HR_SYNC_API_TIMEOUT           – 호출 타임아웃 초 (기본 10)
    HR_SYNC_ROLLOVER_HOUR         – 날짜 라벨 기준 시각 0~23 (기본 8). 이 시각 전이면 전날
    HR_SYNC_RETENTION_DAYS        – 일자 보관본 유지 일수 (기본 7)
    HR_SYNC_HOLIDAY_YEARS_BACK    – 공휴일 수집 범위: 올해 기준 과거 N년 (기본 1)
    HR_SYNC_HOLIDAY_YEARS_AHEAD   – 공휴일 수집 범위: 올해 기준 미래 N년 (기본 1)
    HR_SYNC_ROOT_DEPT_CODE        – 조직도 최상위 노드 부서코드 (비우면 삽입 안 함)
    HR_SYNC_ROOT_DEPT_NAME        – 조직도 최상위 노드 이름
    HR_SYNC_RUN_ON_START          – 기동 시 오늘자 스냅샷이 없으면 즉시 1회 수집 (기본 true)
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from datetime import date, datetime, timedelta, timezone
from datetime import time as dtime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests
from open_webui.env import DATA_DIR, REQUESTS_VERIFY

log = logging.getLogger(__name__)


def _env_bool(key: str, default: bool) -> bool:
    return os.environ.get(key, str(default)).strip().lower() == 'true'


def _env_int(key: str, default: int) -> int:
    try:
        return int(os.environ.get(key, '').strip() or default)
    except ValueError:
        log.warning(f'HR sync: invalid {key}, using default {default}')
        return default


HR_SYNC_ENABLED = _env_bool('HR_SYNC_ENABLED', False)
HR_SYNC_TIME = os.environ.get('HR_SYNC_TIME', '08:00').strip()
HR_SYNC_TZ = os.environ.get('HR_SYNC_TZ', 'Asia/Seoul').strip() or 'Asia/Seoul'
HR_SYNC_DIR = os.environ.get('HR_SYNC_DIR', '').strip() or str(Path(DATA_DIR) / 'hr')

HR_SYNC_EMP_API_URL = os.environ.get('HR_SYNC_EMP_API_URL', '').strip()
HR_SYNC_DEPT_API_URL = os.environ.get('HR_SYNC_DEPT_API_URL', '').strip()
HR_SYNC_HOLIDAY_API_URL = os.environ.get('HR_SYNC_HOLIDAY_API_URL', '').strip()

HR_SYNC_API_HEADER_NAME = os.environ.get('HR_SYNC_API_HEADER_NAME', '').strip()
HR_SYNC_API_HEADER_VALUE = os.environ.get('HR_SYNC_API_HEADER_VALUE', '').strip()
HR_SYNC_API_TIMEOUT = float(_env_int('HR_SYNC_API_TIMEOUT', 10))

HR_SYNC_ROLLOVER_HOUR = max(0, min(23, _env_int('HR_SYNC_ROLLOVER_HOUR', 8)))
HR_SYNC_RETENTION_DAYS = max(1, _env_int('HR_SYNC_RETENTION_DAYS', 7))
HR_SYNC_HOLIDAY_YEARS_BACK = max(0, _env_int('HR_SYNC_HOLIDAY_YEARS_BACK', 1))
HR_SYNC_HOLIDAY_YEARS_AHEAD = max(0, _env_int('HR_SYNC_HOLIDAY_YEARS_AHEAD', 1))

HR_SYNC_ROOT_DEPT_CODE = os.environ.get('HR_SYNC_ROOT_DEPT_CODE', '').strip()
HR_SYNC_ROOT_DEPT_NAME = os.environ.get('HR_SYNC_ROOT_DEPT_NAME', '').strip()
HR_SYNC_RUN_ON_START = _env_bool('HR_SYNC_RUN_ON_START', True)

# 스냅샷 파일 4종. 읽는 쪽과 약속된 이름이라 환경변수로 열지 않는다(디렉터리만 설정 가능).
EMP_FILENAME = 'emp.json'  # 직원 — 수집
DEPT_FILENAME = 'dept.json'  # 부서 — 수집(최상위 노드 보강)
HOLIDAY_FILENAME = 'holiday.json'  # 공휴일 — 수집(연 단위 범위)
ORG_FILENAME = 'org.json'  # 조직도 — emp+dept 파생 생성

# 스냅샷 레코드 필드명(외부 API 스키마 — 읽는 쪽과 공유하는 고정 계약).
_F_DEPT_CODE = 'deptCode'
_F_EMP_NAME = 'name'
_F_EMP_TITLE = 'positionTitle'  # 직위
_F_EMP_GRADE = 'position'  # 직급

_POLL_SECONDS = 60  # 실행 시각 도래 확인 주기(정시 오차 최대 1분)


# ============================ 파일 입출력 ============================


def _tz():
    """실행 시각·날짜 라벨의 기준 타임존. 이름을 못 찾으면 고정 오프셋(+09:00)으로 내려간다
    (tzdata 가 없는 최소 이미지에서도 스케줄러가 죽지 않도록)."""
    for name in (HR_SYNC_TZ, 'Asia/Seoul'):
        try:
            return ZoneInfo(name)
        except Exception:
            log.warning(f'HR sync: timezone {name!r} unavailable')
    return timezone(timedelta(hours=9))


def _read_json(path: str):
    try:
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None


def _archive_name(filename: str, day: str) -> str:
    """emp.json → emp.<day>.json (일자별 보관 파일명)."""
    stem, ext = os.path.splitext(filename)
    return f'{stem}.{day}{ext}'


def _archive_files(filename: str) -> list:
    """보관된 일자별 스냅샷 파일명 목록(최신 날짜 먼저). 현재 파일 제외."""
    stem, ext = os.path.splitext(filename)
    try:
        files = [
            fn for fn in os.listdir(HR_SYNC_DIR) if fn.startswith(stem + '.') and fn.endswith(ext) and fn != filename
        ]
    except OSError:
        return []
    files.sort(reverse=True)  # 파일명이 ISO 날짜라 사전식 정렬 = 날짜 정렬
    return files


def snapshot_day(now: datetime | None = None) -> str:
    """날짜 라벨(ISO). 롤오버 시각(기본 8시) 전이면 전날로 본다 — 읽는 쪽과 같은 규칙."""
    now = now or datetime.now(_tz())
    return (now - timedelta(hours=HR_SYNC_ROLLOVER_HOUR)).date().isoformat()


def _save_snapshot(filename: str, data, day: str) -> None:
    """스냅샷을 <filename> + <filename>.<day> 로 저장하고 오래된 보관분을 정리한다.

    쓰기는 임시파일 + os.replace 로 원자적으로 한다 — 읽는 쪽이 같은 파일을 동시에 열기
    때문에, 직접 덮어쓰면 쓰다 만 JSON 을 읽어 파싱에 실패하는 일이 생긴다.
    """
    os.makedirs(HR_SYNC_DIR, exist_ok=True)
    raw = json.dumps(data, ensure_ascii=False, indent=2)
    for name in (filename, _archive_name(filename, day)):
        path = os.path.join(HR_SYNC_DIR, name)
        tmp = path + '.tmp'
        with open(tmp, 'w', encoding='utf-8') as f:
            f.write(raw)
        os.replace(tmp, path)  # 원자적 교체(같은 디렉터리라 rename 보장)
    for fn in _archive_files(filename)[HR_SYNC_RETENTION_DAYS:]:
        try:
            os.remove(os.path.join(HR_SYNC_DIR, fn))
        except OSError:
            pass


def _is_fresh(filename: str, day: str) -> bool:
    """해당 날짜의 스냅샷(현재본+일자 보관본)이 모두 있으면 신선한 것으로 본다."""
    return os.path.exists(os.path.join(HR_SYNC_DIR, filename)) and os.path.exists(
        os.path.join(HR_SYNC_DIR, _archive_name(filename, day))
    )


# ============================ API 호출 ============================


def _fetch(url: str, params: dict | None = None):
    """인사 API 호출(GET). 실패하면 예외를 그대로 올린다.

    헤더는 Content-Type 과 환경변수로 지정한 식별 헤더(설정된 경우) 두 개만 보낸다.
    params 는 기간이 필요한 API(공휴일 fromDate/toDate)에만 쓴다.
    """
    headers = {'Content-Type': 'application/json'}
    if HR_SYNC_API_HEADER_NAME:
        headers[HR_SYNC_API_HEADER_NAME] = HR_SYNC_API_HEADER_VALUE
    resp = requests.get(
        url,
        params=params or {},
        headers=headers,
        timeout=HR_SYNC_API_TIMEOUT,
        verify=REQUESTS_VERIFY,
    )
    resp.raise_for_status()
    return resp.json()


def _use_yn_ok(rec) -> bool:
    """useYn 이 명시적으로 N 인 레코드만 제외한다.

    필드가 없거나 비면 유지 — API 가 필드를 빼는 변경이 생겨도 전원 누락으로 번지지 않게.
    """
    v = str(rec.get('useYn') or '').strip().upper() if isinstance(rec, dict) else ''
    return not v or v == 'Y'


def _drop_unused(snapshot):
    """저장 전 useYn≠Y 레코드 제거(파일에도 사용분만 담는다). 응답의 형태는 보존."""
    if isinstance(snapshot, list):
        return [r for r in snapshot if _use_yn_ok(r)]
    if isinstance(snapshot, dict):
        out: dict = {}
        for k, v in snapshot.items():
            if isinstance(v, list):
                out[k] = [r for r in v if _use_yn_ok(r)]
            elif not (isinstance(v, dict) and not _use_yn_ok(v)):
                out[k] = v
        return out
    return snapshot


def _records_of(snapshot) -> list:
    """스냅샷에서 레코드(dict) 목록을 꺼낸다({"empList":[...]} 래핑/리스트/dict-by-key 대응).

    useYn≠Y 레코드는 제외한다 — 옛 보관본을 읽는 경우에 대한 이중 방어.
    """
    if isinstance(snapshot, list):
        return [r for r in snapshot if isinstance(r, dict) and _use_yn_ok(r)]
    out: list = []
    if isinstance(snapshot, dict):
        for v in snapshot.values():
            if isinstance(v, list):
                out.extend(r for r in v if isinstance(r, dict) and _use_yn_ok(r))
            elif isinstance(v, dict) and _use_yn_ok(v):
                out.append(v)
    return out


def _with_root_dept(snapshot):
    """부서 스냅샷 맨 위에 최상위 노드를 추가한다(환경변수로 코드·이름을 준 경우에만).

    부서 목록에는 없지만 임원 등이 소속된 최상위 코드가 있어, 그 인원이 조직도에서 빠지지
    않도록 루트 노드를 만들어 준다. 이미 있으면 그대로 둔다.
    """
    if not HR_SYNC_ROOT_DEPT_CODE:
        return snapshot
    root = {
        'deptCode': HR_SYNC_ROOT_DEPT_CODE,
        'deptName': HR_SYNC_ROOT_DEPT_NAME,
        'deptLevelType': '0',  # 최상위(본부보다 위)
        'dept2Code': HR_SYNC_ROOT_DEPT_CODE,
        'dept3Code': HR_SYNC_ROOT_DEPT_CODE,
        'deptOrder': '0',  # 정렬 맨 앞
    }

    def has_root(records) -> bool:
        return any(
            isinstance(r, dict) and str(r.get(_F_DEPT_CODE, '')).strip() == HR_SYNC_ROOT_DEPT_CODE for r in records
        )

    if isinstance(snapshot, list):
        if not has_root(snapshot):
            snapshot.insert(0, dict(root))
    elif isinstance(snapshot, dict):
        for v in snapshot.values():
            if isinstance(v, list):
                if not has_root(v):
                    v.insert(0, dict(root))
                break
    return snapshot


# ============================ 조직도 생성 ============================


def build_org_chart(dept_snapshot, emp_snapshot, day: str) -> dict:
    """부서+직원 스냅샷 → 조직도(부서 계층 트리 + 조직별 인원). org.json 의 내용.

    키·값 모두 원본(영문 키·코드값) 그대로 쓴다 — 코드→한글 라벨 변환은 읽는 도구가 한다.
    - 조직 노드: {deptCode, deptName, deptLevelType, members, children}
    - 부모: dept2Code→dept3Code 중 자기 deptCode 와 처음으로 다른 코드(전부 같으면 최상위).
    - 인원(member): 이름·직위·직급·담당업무·내선 등 — 사번·이메일은 싣지 않는다.
      최상위 코드 소속(임원 등)은 루트 직속으로, 부서 목록에 없는 부서코드의 직원은
      "미분류" 노드(최상위)로 포함한다(누락 방지).
    - 정렬용 int(deptOrder/positionOrder)는 출력에서 빼고 배열 순서로 대신한다. 조직은
      deptOrder, 인원은 positionOrder 오름차순, 값이 없으면 뒤로·같으면 이름순.
    """

    def s(rec, field_name: str) -> str:
        val = rec.get(field_name)
        return '' if val is None else str(val).strip()

    def rank(rec, field_name: str) -> tuple:
        try:
            return (0, float(rec[field_name]))
        except (KeyError, TypeError, ValueError):
            return (1, 0.0)  # 값 없으면 뒤로

    nodes: dict = {}
    node_sort: dict = {}
    recs: list = []
    for r in _records_of(dept_snapshot):
        code = s(r, _F_DEPT_CODE)
        if not code or code in nodes:
            continue
        nodes[code] = {
            'deptCode': code,
            'deptName': s(r, 'deptName'),
            'deptLevelType': s(r, 'deptLevelType'),  # raw 코드 — 라벨 변환은 읽는 쪽에서
            'members': [],
            'children': [],
        }
        node_sort[code] = rank(r, 'deptOrder') + (s(r, 'deptName'),)
        recs.append((code, r))

    roots: list = []
    for code, r in recs:
        parent = next(
            (p for p in (s(r, 'dept2Code'), s(r, 'dept3Code')) if p and p != code and p in nodes),
            None,
        )
        # 상위가 없는 노드(본부 등)는 최상위 노드 아래로 모아 루트를 하나로 유지한다.
        if (
            parent is None
            and HR_SYNC_ROOT_DEPT_CODE
            and code != HR_SYNC_ROOT_DEPT_CODE
            and HR_SYNC_ROOT_DEPT_CODE in nodes
        ):
            parent = HR_SYNC_ROOT_DEPT_CODE
        (nodes[parent]['children'] if parent else roots).append(nodes[code])

    # members 에는 (정렬키, dict) 튜플을 임시로 모았다가 finalize 에서 정렬 후 dict 만 남긴다
    # (정렬용 positionOrder 는 출력에 넣지 않는다 — 배열 순서로 대신).
    for e in _records_of(emp_snapshot):
        code = s(e, _F_DEPT_CODE)
        node = nodes.get(code)
        if node is None:
            node = nodes[code] = {
                'deptCode': code,
                'deptName': s(e, 'deptName') or f'미분류({code or "없음"})',
                'deptLevelType': s(e, 'deptLevelType'),  # emp 에 없으면 빈 값
                'members': [],
                'children': [],
            }
            node_sort[code] = (2, 0.0, node['deptName'])  # 정렬 맨 뒤
            roots.append(node)
        node['members'].append(
            (
                rank(e, 'positionOrder') + (s(e, _F_EMP_NAME),),
                {
                    # 키·값 모두 원본(영문·코드) 그대로 — 라벨 변환은 읽는 도구에서.
                    'name': s(e, _F_EMP_NAME),
                    'positionTitle': s(e, _F_EMP_TITLE),
                    'position': s(e, _F_EMP_GRADE),
                    'assignedTask': s(e, 'assignedTask'),
                    'workTelno': s(e, 'workTelno'),  # 내선번호(문자열)
                    'dutyType': s(e, 'dutyType'),
                    'workingOfficeType': s(e, 'workingOfficeType'),
                    'dispatched': s(e, 'dispatched'),
                    'retired': s(e, 'retired'),
                    'absence': s(e, 'absence'),
                    'daynightType': s(e, 'daynightType'),
                },
            )
        )

    def finalize(items: list) -> None:
        items.sort(key=lambda n: node_sort[n['deptCode']])
        for n in items:
            n['members'] = [m for _, m in sorted(n['members'], key=lambda t: t[0])]
            finalize(n['children'])

    finalize(roots)
    return {'generated': day, 'orgs': roots}


# ============================ 수집 단계 ============================


def _sync_simple(url: str, filename: str, day: str, transform=None) -> int:
    """단일 스냅샷 수집(직원·부서). 저장한 레코드 수를 돌려주고, 실패는 예외로 올린다."""
    data = _drop_unused(_fetch(url))  # useYn=Y 만 저장
    # 0건을 그대로 저장하면 읽는 쪽이 "전원 없음"으로 보게 된다 — 이전 파일을 남긴다.
    # 판정은 가공(루트 노드 삽입) 전에 한다 — 삽입분 때문에 빈 응답이 1건으로 보이지 않게.
    if not _records_of(data):
        raise RuntimeError('API returned no usable rows')
    if transform:
        data = transform(data)
    _save_snapshot(filename, data, day)
    return len(_records_of(data))


def _fetch_holiday_range(url: str, from_date: str, to_date: str):
    """공휴일 구간 조회 — 레코드가 없으면 None(호출부가 연 단위로 분할 재시도).

    fromDate 는 필수, toDate 를 생략하면 하루치가 되므로 항상 함께 보낸다.
    """
    data = _fetch(url, {'fromDate': from_date, 'toDate': to_date})
    return data if _records_of(data) else None


def _sync_holidays(url: str, day: str) -> int:
    """공휴일 스냅샷 수집(올해 기준 과거/미래 N년). 저장한 레코드 수를 돌려준다."""
    year = datetime.now(_tz()).year
    years = list(range(year - HR_SYNC_HOLIDAY_YEARS_BACK, year + HR_SYNC_HOLIDAY_YEARS_AHEAD + 1))
    data = _fetch_holiday_range(url, f'{years[0]}-01-01', f'{years[-1]}-12-31')
    if data is None:
        # 여러 해를 한 번에 못 받는 API 일 수 있다(범위 제한·응답 크기) — 연 단위로 나눠
        # 받아 합친다. 하루 1회라 몇 번 더 호출해도 부담이 아니다.
        merged: list = []
        for y in years:
            part = _fetch_holiday_range(url, f'{y}-01-01', f'{y}-12-31')
            if part is not None:
                merged.extend(_records_of(part))
        if not merged:
            raise RuntimeError('holiday API returned no usable rows (whole range and per-year)')
        data = {'holidayList': merged}
    rows = len(_records_of(data))
    _save_snapshot(HOLIDAY_FILENAME, _drop_unused(data), day)
    return rows


def _sync_org(day: str) -> int:
    """저장된 emp+dept 파일로 조직도를 만든다. 소스가 없으면 0(건너뜀)."""
    emp = _read_json(os.path.join(HR_SYNC_DIR, EMP_FILENAME))
    dept = _read_json(os.path.join(HR_SYNC_DIR, DEPT_FILENAME))
    if emp is None or dept is None:
        log.warning('HR sync: org chart skipped (emp/dept snapshot missing)')
        return 0
    org = build_org_chart(dept, emp, day)
    _save_snapshot(ORG_FILENAME, org, day)
    return len(org['orgs'])


def sync_snapshots(day: str) -> dict:
    """스냅샷 4종을 한 번에 갱신한다(동기 — 호출부에서 스레드로 돌린다).

    단계별로 독립 처리한다 — 한 API 가 죽어도 나머지는 갱신하고, 실패한 항목은 직전 파일이
    그대로 남아 읽는 쪽이 보관본으로 계속 동작한다(다음 날 다시 시도).
    조직도는 항상 파일 기준으로 다시 만든다(이번에 emp/dept 수집이 실패했다면 직전 내용으로
    오늘자가 생성된다 — 소비자에게는 "없음"보다 낫다).
    """
    result: dict = {}
    for label, url, filename, transform in (
        ('emp', HR_SYNC_EMP_API_URL, EMP_FILENAME, None),
        ('dept', HR_SYNC_DEPT_API_URL, DEPT_FILENAME, _with_root_dept),
    ):
        if not url:
            continue
        try:
            result[label] = _sync_simple(url, filename, day, transform)
        except Exception as e:
            result[label] = f'failed: {e!r}'
            log.error(f'HR sync: {filename} fetch failed: {e!r}')

    if HR_SYNC_HOLIDAY_API_URL:
        try:
            result['holiday'] = _sync_holidays(HR_SYNC_HOLIDAY_API_URL, day)
        except Exception as e:
            result['holiday'] = f'failed: {e!r}'
            log.error(f'HR sync: {HOLIDAY_FILENAME} fetch failed: {e!r}')

    try:
        result['org'] = _sync_org(day)
    except Exception as e:
        result['org'] = f'failed: {e!r}'
        log.error(f'HR sync: {ORG_FILENAME} build failed: {e!r}')

    return result


# ============================ 스케줄러 ============================


def _parse_time(raw: str) -> dtime:
    """HH:MM → time. 형식이 틀리면 기본값 08:00."""
    try:
        hh, mm = raw.split(':', 1)
        return dtime(hour=int(hh), minute=int(mm))
    except Exception:
        log.warning(f'HR sync: invalid HR_SYNC_TIME {raw!r}, using 08:00')
        return dtime(hour=8, minute=10)


def _stale_targets(day: str) -> list:
    """오늘자가 아직 없는 스냅샷 이름 목록(설정된 것만 확인)."""
    targets = [(HR_SYNC_EMP_API_URL, EMP_FILENAME), (HR_SYNC_DEPT_API_URL, DEPT_FILENAME)]
    targets.append((HR_SYNC_HOLIDAY_API_URL, HOLIDAY_FILENAME))
    stale = [fn for url, fn in targets if url and not _is_fresh(fn, day)]
    if (HR_SYNC_EMP_API_URL or HR_SYNC_DEPT_API_URL) and not _is_fresh(ORG_FILENAME, day):
        stale.append(ORG_FILENAME)
    return stale


async def _run_once(day: str, reason: str) -> None:
    log.info(f'HR sync started ({reason}, day={day})')
    result = await asyncio.to_thread(sync_snapshots, day)
    log.info(f'HR sync finished (day={day}): {result}')


async def hr_sync_loop() -> None:
    """매일 HR_SYNC_TIME(기본 08:00 KST)에 스냅샷 4종을 갱신하는 백그라운드 루프.

    실행 시각 판정은 달력 날짜 기준이라 하루 한 번만 돈다(파일명 라벨은 롤오버 기준이라
    별개다). 긴 sleep 대신 1분마다 시각을 다시 읽어, 컨테이너 일시정지·시계 조정으로
    시간이 튀어도 예정 시각을 지나치지 않는다.

    UVICORN_WORKERS=1(기본) 전제다. 여러 워커로 띄우면 워커 수만큼 같은 시각에 호출이
    나간다 — 저장 자체는 원자적이라 파일이 깨지진 않지만 API 호출이 중복된다.
    """
    if not HR_SYNC_ENABLED:
        return
    if not (HR_SYNC_EMP_API_URL or HR_SYNC_DEPT_API_URL or HR_SYNC_HOLIDAY_API_URL):
        log.warning('HR sync enabled but no API URL configured — skipped')
        return

    tz = _tz()
    target = _parse_time(HR_SYNC_TIME)
    if target.hour < HR_SYNC_ROLLOVER_HOUR:
        # 롤오버 전에 저장하면 전날 라벨이 붙어, 읽는 쪽이 오늘자가 없다고 판정한다.
        log.warning(
            f'HR sync: HR_SYNC_TIME({HR_SYNC_TIME}) is before '
            f'HR_SYNC_ROLLOVER_HOUR({HR_SYNC_ROLLOVER_HOUR}) — snapshots will be labeled '
            f'with the previous day'
        )
    log.info(f'HR sync scheduled daily at {target.strftime("%H:%M")} {HR_SYNC_TZ} (dir: {HR_SYNC_DIR})')

    now = datetime.now(tz)
    # 기동 시점이 이미 예정 시각을 지났다면 오늘 몫은 끝난 것으로 둔다 — 재기동마다 다시
    # 받지 않게. 정말 오늘자가 없으면 바로 아래 보충 실행이 채운다.
    last_run: date | None = now.date() if now.time() >= target else None

    if HR_SYNC_RUN_ON_START:
        day = snapshot_day(now)
        stale = _stale_targets(day)
        if stale:
            try:
                await _run_once(day, f'startup catch-up: {", ".join(stale)}')
                last_run = now.date()
            except Exception:
                log.exception('HR sync: startup catch-up failed')

    while True:
        try:
            now = datetime.now(tz)
            if last_run != now.date() and now.time() >= target:
                last_run = now.date()  # 실패해도 같은 날 반복하지 않는다(다음 날 재시도)
                await _run_once(snapshot_day(now), 'scheduled')
        except Exception:
            log.exception('HR sync: unexpected error')
        await asyncio.sleep(_POLL_SECONDS)
