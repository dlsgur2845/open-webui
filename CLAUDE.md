# CLAUDE.md

이 저장소에서 작업할 때 반드시 지켜야 할 규칙. (어느 PC에서 작업하든 동일하게 적용)

## 저장소 / 브랜치

- 이 저장소는 `dlsgur2845/open-webui` 포크. 배포 브랜치는 `X.Y.Z-fixN` 형식 (예: `0.10.2-fix1`)이며 업스트림 버전 + 커스텀 이식 커밋으로 구성된다.
- **브랜치 체크아웃/생성 전에 반드시 `git fetch`로 리모트에 같은 이름의 브랜치가 있는지 먼저 확인할 것.** "checkout to X"는 대부분 이미 존재하는 리모트 브랜치로 전환하라는 의미다. (같은 이름으로 새 로컬 브랜치를 만들면 기존 커스텀 커밋이 빠진 채 작업하게 됨)
- `package.json`의 `version`은 브랜치명과 동일하게 (예: `0.10.2-fix1`).
- 커스텀 기능 내역·차기 버전 업그레이드 절차는 **`CUSTOMIZATIONS_0.10.2-fix1.md`**(현행 기준 문서)를 따를 것. `CUSTOMIZATIONS_0.6.43-fix2.1.md`는 역사적 기록(대체됨), `MIGRATION_RUNBOOK_to_0.10.2.md`는 DB/데이터 이관 런북 템플릿.
- 코드에 추가하는 주석은 한글로 작성.

## Docker 빌드 / 배포

- **이미지 태그는 항상 `ax/` 프리픽스**: `ax/open-webui:<버전>` 형식.
- **플랫폼은 linux/amd64** (서버가 리눅스 amd64).
- **컨테이너는 non-root 필수**: `appusr:appgrp` (UID/GID 1000). Dockerfile 기본값에 반영되어 있음.
- **CUDA 미사용**: 서버에 GPU 없음. `USE_CUDA=false` (Dockerfile 기본값). CUDA를 켜면 이미지가 5GB→11GB로 커지므로 주의.
- CI 빌드는 의도적으로 제거됨 — 로컬에서 docker build 후 tar.gz로 배포한다:
  ```bash
  docker build --build-arg BUILD_HASH=$(git rev-parse --short HEAD) -t ax/open-webui:<버전> .
  docker save ax/open-webui:<버전> | pigz > <프로젝트 상위 경로>/open-webui-<버전>.tar.gz
  ```
  내보내기 전 기존 tar.gz는 교체(덮어쓰기)하고, 서버에서는 `docker load`로 올린다.

## 설정 관리 방침

- **`ENABLE_PERSISTENT_CONFIG`는 기본값(`true`)을 그대로 쓴다.** 관리자 UI에서 바꾼 설정이 재시작 후에도 유지되어야 하기 때문. compose에 이 env를 넣지 말 것.
- 그 결과 **DB `config` 테이블이 env보다 우선한다.** `models/config.py`의 `persistent_enabled_for()`가 `True`를 반환 → `Config.get()`이 DB 행을 읽고, 행이 없을 때만 `DEFAULT_CONFIG`(=env)로 폴백한다. 부팅 시 `seed_defaults()`는 **DB에 없는 키만 삽입**하므로 기존 행은 절대 덮어쓰지 않는다.
- **따라서 `DEFAULT_CONFIG`에 등록된 키는 env를 고쳐도 기존 설치본에 반영되지 않는다.** (실사례: `ENABLE_WEBPAGE_ATTACHMENT=false` / `ENABLE_USER_PERSONAL_INFO=false` 무시 — 0.6.43-fix2.1 DB 이관본에 해당 행이 `true`로 이미 존재) env는 신규 설치의 초기값일 뿐이다.
- 값이 안 먹으면 **DB를 확인하고 직접 UPDATE**한다. `value`는 JSON 컬럼이므로 문자열 `'false'`가 아니라 JSON 불리언이어야 한다:
  ```sql
  SELECT key, value FROM config WHERE key = 'ui.enable_webpage_attachment';
  UPDATE config
  SET value = 'false'::json, updated_at = EXTRACT(EPOCH FROM NOW())::bigint
  WHERE key IN ('ui.enable_webpage_attachment', 'ui.enable_user_personal_info');
  ```
  `Config.get_many()`는 캐시 없이 매 요청 DB를 조회하므로 재기동 없이 즉시 반영된다.
- 커스텀 기능 토글 3종(`ui.enable_image_capture` / `ui.enable_webpage_attachment` / `ui.enable_user_personal_info`)은 **쓰기 API가 없다** (`routers/` 전체에 쓰기 경로 0건, `main.py`의 읽기 전용 노출뿐). 관리자 UI로 되돌아갈 일이 없으므로 위 UPDATE는 사실상 영구 설정이다.

## 서버 환경 (배포 대상)

- 리눅스 amd64. 서버 시계는 NTP 동기화됨(2026-07-14 적용). 다만 **동기화 여부와 무관하게 시계 차이를 전제로 코드를 작성할 것** — 클라이언트(브라우저) 시계는 언제든 어긋날 수 있다.
- 짧은 토큰 만료(`JWT_EXPIRES_IN=3m` 수준)를 사용하므로 시계 차이에 민감하다.
- **토큰/세션 등 시간 검증은 서버에서만 한다.** 프론트엔드에서 브라우저 시계로 만료를 직접 판정하는 코드를 넣지 말 것. 프론트의 시간 표시/타이머는 세션 응답의 `server_timestamp`로 clockSkew를 보정해 서버 시간 기준으로 계산하고, 로그아웃 같은 최종 판정은 서버 응답(401)을 확인한 뒤 수행할 것.

## 테스트

- 토큰/세션 관련 프론트엔드 수정은 **API 테스트만으로 부족**하다. 반드시 브라우저 시계를 어긋나게 한 시나리오까지 검증할 것:
  - Playwright에서 `Date`를 +180초 시프트(=서버가 3분 느린 상황)한 브라우저로 로그인 → 세션이 유지되는지
  - 유휴 상태로 실제 만료 시점까지 대기 → 서버 시간 기준으로 정상 로그아웃되는지
  - 테스트 컨테이너는 `-e JWT_EXPIRES_IN=3m`으로 실전과 동일한 짧은 만료로 띄운다
- 앱 레이아웃(`src/routes/(app)/+layout.svelte`)에 1초 주기 만료 타이머와 clockSkew 보정, 활동 기반 자동 갱신(mousemove 제외: keydown/click/touchstart/scroll만) 로직이 있다.

## 공용 PC 주의사항

- git `user.name`/`user.email`/`credential.helper` 등은 `--global` 없이 **저장소 로컬로만** 설정.
- 도구 설치는 사용자 로컬 우선 (예: node는 nvm으로 홈 디렉토리에).
- GCM으로 GitHub 인증 시 토큰이 Windows 자격 증명 관리자에 남으므로, 민감한 환경에서는 작업 후 삭제.
