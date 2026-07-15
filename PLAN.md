# PLAN — 구현 계획

도메인/요구사항은 [CLAUDE.md](./CLAUDE.md), [PRD.md](./PRD.md) 참고.
본 문서는 구현 순서와 단계별 완료 기준(DoD)을 정의한다.

## 개발 원칙

- 각 단계는 테스트(pytest)와 함께 완료한다 (Harness 우선 구축).
- 커밋은 [Conventional Commits](https://www.conventionalcommits.org/)
  컨벤션(`feat:`, `fix:`, `refactor:`, `test:`, `docs:` 등)을 따르며,
  기능 단위로 작게 나눠 커밋한다.
- 도메인 로직(상태 전이, 재고 계산, 생산량 계산)을 UI(콘솔 입출력)와
  분리해 테스트 가능한 구조로 만든다.
- 이 `PLAN.md`는 Phase 단위의 상위 로드맵만 관리한다. 각 Phase(또는 그
  안의 세부 단계)에 실제 착수할 때는
  [test-driven-development](.claude/skills/test-driven-development/SKILL.md)
  스킬이 요구하는 별도의 `Plan.md`(예: `plans/phase1-step1.md`)를 그때
  생성해 RED-GREEN-REVIEW 사이클로 진행한다.

## 단계별 계획

### Phase 0. 기존 PoC 정합성 점검 (완료)

- `ConsoleMVC/`, `Data/` 폴더에 있는 기존 PoC 코드를 확인했다.
- 점검 결과: `Data/`의 JSON 기반 모델/저장소(`models.py`, `repository.py`,
  `crud.py`)는 `CLAUDE.md` 스키마와 정확히 일치. `ConsoleMVC/`는 MVC 구조는
  문서 방향과 맞았으나, 아래 로직이 문서 규칙과 불일치했다.
  - 주문 승인 시 재고 충분/부족 분기 없음 (무조건 PRODUCING)
  - 생산 라인에 target_qty/총 생산 시간/started_at·finished_at 등 시간·수율
    기반 모델이 전혀 없음 (조회 시 즉시 완료 처리)
  - 재고 여유/부족/고갈 상태 판정 없음
- 결정: MVC 구조 유지 + `Data/`의 모델·저장소를 `ConsoleMVC/models/`로
  흡수 통합 (필드명을 CLAUDE.md 스키마에 맞춤: `stock_qty`,
  `OrderStatus` 멤버명 등). 위에서 발견한 불일치 로직은 해당 값을
  담당하는 Phase(4/5/7)에서 이미 다루도록 계획되어 있어, 삭제하고
  `NotImplementedError` 자리표시자로 대체했다. `Data/` 폴더는 제거.
- 디렉토리 구조는 [CLAUDE.md](./CLAUDE.md#디렉토리-구조) 참고.
- DoD: 불일치 항목 목록과 재사용 여부에 대한 사용자 확인 완료 ✅

### Phase 1. 프로젝트 세팅 (완료)

- 루트 `pyproject.toml`에 pytest 설정 추가 (`testpaths = ["tests"]`,
  `pythonpath = ["."]`)
- `tests/test_harness_setup.py` 추가, `ConsoleMVC/__init__.py` 추가해
  `ConsoleMVC.models...` 형태로 테스트에서 import 가능하도록 구성
- `pytest-cov` 커버리지 설정 추가 (`addopts = "--cov=ConsoleMVC
  --cov-report=term-missing"`) — `pytest` 실행 시 파일별 커버리지 표 자동 출력
- 상세 Plan: [plans/phase1-project-setup.md](./plans/phase1-project-setup.md)
- DoD: `pytest` 실행 시 정상 동작 + 커버리지 리포트 출력 ✅ (1 passed, TOTAL 3%)

### Phase 2. 도메인 모델 & 데이터 저장소 (완료)

- `Sample`, `Order`(+`OrderStatus`), `ProductionQueue` 3개 모델(Phase 0에서
  이관)에 대한 단위 테스트 24개 작성 (`tests/models/`)
- 테스트 작성 중 `ConsoleMVC` 내부 import가 실행 방식에 따라 깨지는 문제를
  발견해, `models`/`controllers`/`views`/`main.py` 전체를 `ConsoleMVC.`
  절대경로 import로 통일 (사용자 확인 후 진행). 콘솔 앱 실행 방법이
  `python -m ConsoleMVC.main`(프로젝트 루트에서)으로 변경됨 — 상세는
  [CLAUDE.md](./CLAUDE.md#import-컨벤션--실행-방법) 참고
- 상세 Plan: [plans/phase2-domain-model-repository-tests.md](./plans/phase2-domain-model-repository-tests.md)
- DoD: 24개 테스트 통과, 커버리지 3%→35% ✅

### Phase 3. 시료 관리

- 시료 등록 / 조회(재고 수량 포함) / 검색
- DoD: 등록·조회·검색 단위 테스트 통과, 콘솔 메뉴 연동

### Phase 4. 주문 (접수 / 승인 / 거절)

- 시료 예약(주문 생성, `RESERVED`)
- 접수된 주문 목록 표시
- 주문 승인: 재고 충분/부족 분기 로직 (`CONFIRMED` / `PRODUCING`)
- 주문 거절 (`REJECTED`)
- DoD: 승인 시 재고 분기 로직에 대한 단위 테스트 통과

### Phase 5. 생산 라인

- 생산량/생산 시간 계산 (`ceil(부족분 / 수율)`, `평균 생산시간 * 실 생산량`)
- 생산 큐(FIFO) 및 대기 주문 확인. 생산 라인은 직렬 처리(동시 1개 작업)
- `ProductionQueue`에는 `status` 컬럼을 두지 않고 `started_at`/`finished_at`만
  저장한다. WAITING/PRODUCING/DONE 여부는 조회 시점에 두 필드와 현재
  시각을 비교해 판단한다.
- **타이머/스케줄러는 사용하지 않는다.** 콘솔 조작이 들어올 때마다 현재
  시각과 진행 중인 작업의 `finished_at`을 비교해 동기화하는 함수(예:
  `sync_production_state()`)를 만들고, 재고/생산 현황 관련 메뉴 진입 시
  공통으로 호출한다.
  - `now >= finished_at`이면 재고 반영 + 주문 상태 전환
    (`PRODUCING` → `CONFIRMED`) + 다음 대기 항목의 `started_at = now` 설정을
    처리하고, 완료 조건을 만족하는 항목이 없을 때까지 반복한다.
- 생산 현황 표기
- DoD: 생산량 계산 단위 테스트 통과, FIFO 큐 동작(직렬 처리) 검증,
  `started_at`/`finished_at` 기반 상태 판단 로직 테스트 통과, 조회 시점
  동기화 함수가 경과 시간에 따라 재고/주문 상태를 올바르게 갱신하는지에
  대한 테스트 통과 (테스트에서는 `started_at`을 과거 시각으로 주입해
  경과 시간을 시뮬레이션)

### Phase 6. 출고 처리

- `CONFIRMED` 주문 출고 실행 → `RELEASE` 전환
- DoD: 출고 처리 단위 테스트 통과

### Phase 7. 모니터링

- 상태별 주문량 확인 (REJECTED 제외)
- 재고량 확인 및 여유/부족/고갈 상태 판정
- DoD: 상태 판정 로직 단위 테스트 통과

### Phase 8. 콘솔 UI 통합

- 메인 메뉴(시료 관리 / 주문 / 모니터링 / 출고 처리 / 생산 라인) 구성
- 각 메뉴의 하위 기능 연결 및 입출력 처리
- DoD: 전체 흐름(예약 → 승인 → (생산) → 출고)이 콘솔에서 end-to-end 동작

## 진행 상태

| Phase | 상태 |
|---|---|
| 0. 기존 PoC 정합성 점검 | 완료 |
| 1. 프로젝트 세팅 | 완료 (pytest 하네스 구성 완료) |
| 2. 도메인 모델 & 데이터 저장소 | 완료 (단위 테스트 24개) |
| 3. 시료 관리 | 초안 있음 (PoC 이관 완료, 테스트 없음) |
| 4. 주문 | 초안 있음 (접수/거절만, 승인 분기 로직 미구현) |
| 5. 생산 라인 | 미착수 (placeholder만 존재) |
| 6. 출고 처리 | 초안 있음 (PoC 이관 완료, 테스트 없음) |
| 7. 모니터링 | 초안 있음 (여유/부족/고갈 판정 미구현) |
| 8. 콘솔 UI 통합 | 초안 있음 (메뉴 연결은 되어 있음) |
