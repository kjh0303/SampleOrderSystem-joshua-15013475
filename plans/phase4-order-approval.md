## 목표
`OrderController.approve_order`에 재고 충분/부족 분기 로직을 구현한다
(현재 `NotImplementedError`로 막혀 있음). 재고가 충분하면 즉시 `CONFIRMED`로,
부족하면 실 생산량/총 생산 시간을 계산해 `ProductionQueue`에 등록하고
`PRODUCING`으로 전환한다. 함께 `receive_order`/`reject_order`도 이번에
테스트를 붙인다(아직 테스트 없음).

생산이 실제로 언제 시작(`started_at`)되고 완료(`finished_at`)되는지 판단하는
동기화 로직(`sync_production_state`)과 FIFO 직렬 처리는 **Phase 5**에서
다룬다 — 이번 Phase에서는 큐에 "등록"하는 것까지만 구현한다.

## 완료 기준 / 검증 테스트

`tests/controllers/test_order_controller.py` (FakeOrderView 사용,
`tmp_path` 기반 실제 Repository 사용)

- `test_receive_order_creates_reserved_order_when_sample_exists`
- `test_receive_order_shows_error_when_sample_does_not_exist`
- `test_approve_order_confirms_immediately_when_stock_is_sufficient`
  - 입력: 시료 재고 20, 주문 수량 10
  - 기대값: 주문 상태 `CONFIRMED`, `ProductionQueue`에는 아무 것도 생기지 않음
- `test_approve_order_enqueues_production_when_stock_is_insufficient`
  - 입력: 시료 재고 5, 주문 수량 20, 수율 0.8, 평균생산시간 2.0
  - 기대값: 부족분 = 20 - 5 = 15, `target_qty = ceil(15 / 0.8) = 19`,
    `total_production_time = 2.0 * 19 = 38.0`
  - 주문 상태 `PRODUCING`, `ProductionQueue`에 `target_qty=19`,
    `total_production_time=38.0`, `started_at is None`(아직 큐 등록만) 항목 생성
- `test_approve_order_shows_message_when_order_not_found_or_not_reserved`
- `test_reject_order_transitions_reserved_order_to_rejected`
- `test_reject_order_shows_message_when_order_not_found_or_not_reserved`

DoD: 위 테스트 전체 통과 + 전체 스위트 clean.

## 구현 범위
- `ConsoleMVC/controllers/order_controller.py`
  - 생성자 파라미터를 `production_line: ProductionLine`에서
    `queue_repo: ProductionQueueRepository`로 교체 (현재 `ProductionLine`은
    빈 placeholder라 실제로 쓸 수 없음 — Phase 5에서 별도 목적으로 재도입)
  - `approve_order`에 재고 비교 → `math.ceil` 기반 `target_qty`/
    `total_production_time` 계산 → 부족 시 `ProductionQueue` 생성 로직 구현
- `ConsoleMVC/main.py`의 `OrderController` 생성 부분을 `queue_repo` 주입으로 변경
- `tests/controllers/test_order_controller.py` 추가 (`FakeOrderView` 정의)

## 범위 밖
- `started_at`/`finished_at` 설정, 생산 완료 판단(`sync_production_state`),
  FIFO 직렬 처리 — Phase 5
- 생산 현황/대기열 조회 화면 — Phase 5
- `ProductionLine`(현재 placeholder) 자체 구현 — Phase 5에서 실제 용도 결정
