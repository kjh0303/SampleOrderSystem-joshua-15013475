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

### Phase 3. 시료 관리 (완료)

- `SampleController`(등록/조회/검색) 단위 테스트 5개 작성
  (`tests/controllers/test_sample_controller.py`), `FakeSampleView` 테스트
  더블 사용
- 상세 Plan: [plans/phase3-sample-management.md](./plans/phase3-sample-management.md)
- DoD: 5개 테스트 통과 (기존 구현이 문서와 일치해 즉시 통과, 콘솔 메뉴는
  Phase 0 이관 시점에 이미 연동됨) ✅

### Phase 4. 주문 (접수 / 승인 / 거절) (완료)

- `OrderController.approve_order`에 재고 충분/부족 분기 구현: 충분하면
  즉시 `CONFIRMED`, 부족하면 `target_qty = ceil(부족분/수율)`,
  `total_production_time = 평균생산시간 * target_qty` 계산 후
  `ProductionQueue`에 등록(`started_at`은 아직 미설정)하고 `PRODUCING` 전환
- 생성자 의존성을 `ProductionLine`(placeholder) → `ProductionQueueRepository`로
  교체, `main.py` 의존성 주입 갱신
- `receive_order`/`reject_order` 포함 단위 테스트 7개 작성
- 상세 Plan: [plans/phase4-order-approval.md](./plans/phase4-order-approval.md)
- DoD: 7개 테스트 통과 + 콘솔 스모크 테스트로 실제 분기 확인 ✅

### Phase 5. 생산 라인 (완료)

- `ProductionLine.sync(now)` 구현: 조회 시점마다 진행 중인 작업을 완료
  처리(재고 반영 + 주문 `PRODUCING`→`CONFIRMED`)하고, 빈 자리가 생기면
  대기열에서 다음 항목을 시작(직렬 처리, 동시 1개). "이미 처리됨" 판단은
  별도 플래그 없이 연결된 주문 상태로 판단해 멱등성 확보
  - 완료 후 다음 항목은 "지금"이 아니라 "직전 작업이 끝난 시각"부터 이어
    붙여 시작 — 오래 조회하지 않아 밀린 완료 건이 여러 개여도 한 번의
    `sync()`로 순서대로 모두 처리(캐스케이드)되도록 함
- `current_item()`/`waiting_items()`(FIFO) 제공, `ProductionController`/
  `ProductionView`에서 화면 표시 구현
- `main.py`에서 `ProductionLine(order_repo, sample_repo, queue_repo)`로 배선
- 상세 Plan: [plans/phase5-production-line.md](./plans/phase5-production-line.md)
- DoD: 단위 테스트 11개 통과 + 콘솔에서 실제 완료 처리(재고 증가, 상태
  전환) 수동 확인 ✅

**Follow-up (사용자 피드백 반영, 완료)**: "생산 라인" 메뉴는 조회 전용이지
생산을 트리거하는 메뉴가 아니라는 피드백에 따라 동작을 조정했다.
- `OrderController.approve_order`가 재고 부족으로 큐에 등록한 **직후**
  `ProductionLine.sync()`를 호출해, 생산 라인이 비어 있으면 그 자리에서
  바로 생산을 시작한다 (더 이상 "생산 라인" 메뉴 진입을 기다리지 않음)
- `sync()` 호출 지점을 시료 관리(조회/검색) · 생산 라인(조회) · 출고 처리
  3곳으로 확장해, 사용자가 어떤 관련 화면을 보든 최신 재고/주문 상태가
  반영되도록 함
- 상세 Plan: [plans/phase5-followup-eager-start-and-sync-hooks.md](./plans/phase5-followup-eager-start-and-sync-hooks.md)
- DoD: 신규/보강 테스트 8개 통과, 콘솔에서 승인 직후 즉시 시작 확인 ✅

### Phase 6. 출고 처리 (완료)

- `CONFIRMED` 주문 출고 실행 → `RELEASE` 전환. 기존 PoC 구현이 문서
  규칙과 이미 일치해 프로덕션 코드 수정 없이 테스트만 추가
- 정상 출고(재고 감소 + RELEASE 전환) / 취소 / 잘못된 주문 3개 테스트 추가
  (sync 훅 반영 테스트는 Phase 5 follow-up에서 이미 작성됨)
- 상세 Plan: [plans/phase6-shipment.md](./plans/phase6-shipment.md)
- DoD: 출고 처리 단위 테스트 4개 통과 ✅

### Phase 7. 모니터링 (완료)

- 상태별 주문량 확인 (REJECTED 제외, 기존 `find_valid_orders` 재사용)
- 재고량 확인 및 여유/부족/고갈 상태 판정 구현
  - 고갈: `stock_qty == 0` (최우선 판정)
  - 부족: `stock_qty <` 미출고 수요 합계(`RESERVED`+`PRODUCING`+`CONFIRMED` 주문 수량)
  - 여유: 그 외
- `show_stock_volume`에도 `ProductionLine.sync()` 훅 추가 (Phase 5
  follow-up에서 남겨둔 재검토 항목 반영)
- 상세 Plan: [plans/phase7-monitoring.md](./plans/phase7-monitoring.md)
- DoD: 단위 테스트 5개 통과 + 콘솔 수동 확인(고갈 표시) ✅

### Phase 8. 콘솔 UI 통합 (완료)

- 메인 메뉴(시료 관리 / 주문 / 모니터링 / 출고 처리 / 생산 라인) 배선은
  각 Phase 진행 중 `main.py`에 이미 반영돼 있어, 이번 Phase는 새 기능
  구현이 아니라 **통합 검증**으로 진행
- `tests/test_end_to_end.py` 추가: 재고 충분/부족 두 시나리오 모두
  실제 Repository/ProductionLine을 조합해 등록→접수→승인→(생산)→출고
  전체 흐름을 검증 (배선 문제 없이 첫 실행에 바로 통과)
- 콘솔에서 5개 메뉴 전체(시료 관리 등록/조회/검색, 주문 접수/승인,
  생산 라인 현황/대기열, 모니터링 주문량/재고상태, 잘못된 메뉴 입력 처리)
  수동 확인 완료
- 상세 Plan: [plans/phase8-console-integration.md](./plans/phase8-console-integration.md)
- DoD: 통합 테스트 2개 통과 + 콘솔 전체 시나리오 수동 확인 ✅

### Phase 9. 커버리지 기반 리팩토링 (완료)

Phase 0~8을 마친 시점의 커버리지(65%, TOTAL 726 stmts / 253 miss)를
검토해, 커버리지가 없는 코드마다 "정말 필요한 코드인지"를 판단한다.
불필요하면 삭제하고, 필요하면 테스트를 보강한다 — 커버리지 숫자를
올리는 것 자체가 목적이 아니라, 미검증 코드/죽은 코드를 솎아내는 것이
목적이다.

**분석 결과 (이번 세션에서 확인)**

| 대상 | 미커버 내용 | 판단 |
|---|---|---|
| 5개 컨트롤러의 `run()` | 메뉴 선택 dispatch 루프 전체 | **필요함** — `main.py`가 실제로 호출하는 코드. 테스트 보강 |
| `order_controller.py` 취소 분기(접수/승인/거절) | `input_new_order`/`input_order_id`가 `None`을 반환하는 취소 경로 | **필요함** — 사용자가 실제로 "0: 취소"를 누르는 경로. 테스트 보강 |
| `production_controller.show_waiting_orders`의 "대기 없음" 분기 | 큐가 비었을 때 메시지 분기 | **필요함** — 테스트 보강 |
| `ConsoleMVC/main.py` | 전체(0%) | **필요함**(진입점) — 하지만 `input()` 루프를 직접 단위 테스트하는 것은 비용 대비 가치가 낮음. 커버리지 측정 대상에서 의도적으로 제외(omit) |
| `ConsoleMVC/scripts/generate_dummy_data.py` | 전체(0%) | **필요함**(수동 테스트용 개발 도구) — 다만 랜덤 더미 데이터 생성기 자체를 단위 테스트하는 것은 가치가 낮음. 커버리지 측정 대상에서 제외(omit) |
| `views/*.py` (25~32%) | `print`/`input` 위주 I/O 코드 | Phase 3에서 이미 "로직이 없어 테스트 생략"으로 결정된 영역 — 재확인만 하고 커버리지 omit 설정으로 명시 |

- 구현 범위: `pyproject.toml` 커버리지 `omit` 설정(`main.py`,
  `ConsoleMVC/scripts/*`, `ConsoleMVC/views/*`), 각 컨트롤러 `run()` 테스트,
  `order_controller` 취소 분기 3곳 + `production_controller` "대기 없음"
  분기 테스트를 기존 `tests/controllers/` 파일들에 추가
- 진행 중 추가로 발견: `JsonRepository.update()`가 앱 어디서도 호출되지
  않는 죽은 코드임을 확인(`SampleRepository`/`OrderRepository`/
  `ProductionQueueRepository` 모두 `save()`만 사용) → 삭제하고 관련 테스트도
  제거. 대신 실제로 쓰이는 `save()`의 미발견(KeyError) 분기 테스트를 추가
- 범위 밖: 새로운 기능 추가, views 자체 테스트 작성(Phase 3 결정 유지)
- DoD: 테스트 76개 통과 + omit 적용 후 controllers/models 커버리지 **100%** ✅
- 상세 Plan: [plans/phase9-coverage-refactor.md](./plans/phase9-coverage-refactor.md)

### Phase 10. 동작 검증 중 발견된 버그 수정 — 재고 충분 시 생산 스킵 (완료)

Phase 0~9 완료 후 수동 동작 검증 중 발견: 대기 중인 생산 큐 항목을 실제로
시작시킬 때 그 시점의 재고를 재확인하지 않아, 앞선 주문의 생산으로 재고가
이미 충분해진 경우에도 불필요하게 생산이 진행되는 과잉 생산 버그가 있었다
(예: 수율 0.5인 시료에 주문 100개+50개를 연속 승인 → 각각 200개/100개
생산 계획이 잡히는데, 100개 생산 완료로 재고가 200이 된 뒤에도 두 번째
100개 생산을 그대로 진행해버림).

- `ProductionLine.sync()`가 대기 항목을 시작시키기 직전 재고를 재확인해,
  이미 주문 수량을 충족하면 생산 없이 큐 항목을 제거하고 주문을 바로
  `CONFIRMED`로 전환하도록 수정
- `ProductionQueueRepository.delete()` 추가
- 상세 Plan: [plans/phase10-skip-production-when-stock-sufficient.md](./plans/phase10-skip-production-when-stock-sufficient.md)
- DoD: 단위 테스트 3개 추가(신규 스킵 케이스 2개 + 회귀 확인 1개) 통과,
  전체 스위트 79개 clean, 커버리지 100% 유지, 사용자 시나리오 재현 검증
  (재고 200에서 멈춤, 300이 되지 않음) ✅

---

**모든 Phase(0~10) 완료.**

## 진행 상태

| Phase | 상태 |
|---|---|
| 0. 기존 PoC 정합성 점검 | 완료 |
| 1. 프로젝트 세팅 | 완료 (pytest 하네스 구성 완료) |
| 2. 도메인 모델 & 데이터 저장소 | 완료 (단위 테스트 24개) |
| 3. 시료 관리 | 완료 (단위 테스트 5개) |
| 4. 주문 | 완료 (단위 테스트 7개, 재고 분기 로직 구현) |
| 5. 생산 라인 | 완료 (단위 테스트 11개) |
| 6. 출고 처리 | 완료 (단위 테스트 4개) |
| 7. 모니터링 | 완료 (단위 테스트 5개) |
| 8. 콘솔 UI 통합 | 완료 (통합 테스트 2개) |
| 9. 커버리지 기반 리팩토링 | 완료 (models/controllers 커버리지 100%) |
| 10. 재고 충분 시 생산 스킵 버그 수정 | 완료 (단위 테스트 3개 추가) |
