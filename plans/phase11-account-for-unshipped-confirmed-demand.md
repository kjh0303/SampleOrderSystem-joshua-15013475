## 배경 / 버그
사용자 검증 중 발견: 주문 승인 시 재고 충분/부족을 판단할 때
`sample.stock_qty`를 그대로 사용해, **이미 CONFIRMED됐지만 아직
출고(RELEASE)되지 않은 다른 주문의 수량**을 감안하지 않았다.

재현: 시료1(수율 0.5)에 주문1(100개) 승인 → 재고 부족 → 200개 생산 →
완료 시 재고 200, 주문1 CONFIRMED(아직 미출고). 이 상태에서 주문2(101개)를
승인하면 실제 "다른 주문에 물려있지 않은" 가용 재고는 200-100=100개뿐이라
101개는 부족(PRODUCING이어야 함)한데, 기존 로직은 재고 200 전체와
비교해 "충분"으로 잘못 판단해 즉시 CONFIRMED로 처리해버렸다.

Phase 10에서 고친 "대기 항목 시작 직전 재확인" 로직도 같은 방식
(`stock_qty` 그대로 비교)이라 동일한 결함이 있다 — 예를 들어 두 주문이
동시에 큐에 대기 중일 때, 첫 주문 완료 후 재고가 늘어도 두 번째 주문이
필요로 하는 양보다 실제 가용량이 적을 수 있는데 이를 반영하지 못한다.

## 목표
재고 충분/부족 판단 시 "가용 재고 = `stock_qty` - (같은 시료에 대해
아직 출고되지 않은 다른 CONFIRMED 주문 수량의 합)"을 기준으로 삼는다.
이 기준을 주문 승인(`OrderController.approve_order`)과 대기 항목 시작
직전 재확인(`ProductionLine.sync()`) 두 곳 모두에 일관되게 적용한다.

## 완료 기준 / 검증 테스트

`tests/models/test_order_repository.py` (기존 파일에 추가)
- `test_sum_confirmed_quantity_sums_only_confirmed_orders_for_the_sample`
  (다른 시료, 다른 상태의 주문은 합계에서 제외되는지 확인)
- `test_sum_confirmed_quantity_excludes_given_order_id`

`tests/controllers/test_order_controller.py` (기존 파일에 추가)
- `test_approve_order_goes_to_producing_when_stock_is_claimed_by_other_unshipped_confirmed_order`
  - 사용자가 제시한 정확한 시나리오 재현: 주문1(100개, 수율 0.5) 생산
    완료로 재고 200・주문1 CONFIRMED(미출고) 상태에서 주문2(101개) 승인 시
    → 가용 재고 100 < 101 → 부족분 1 → PRODUCING 전환, 실제 부족분 기준
    `target_qty`가 계산되는지 확인
- `test_approve_order_still_confirms_when_available_stock_after_other_confirmed_orders_is_sufficient`
  (회귀 확인: 주문2가 100개면 가용 재고 100으로 정확히 충족 → CONFIRMED)

`tests/models/test_production_line.py` (기존 파일에 추가)
- `test_sync_starts_production_when_available_stock_after_other_confirmed_demand_is_insufficient`
  (두 주문이 동시에 대기 중일 때, 첫 주문 완료로 재고가 늘어도 다른
  CONFIRMED 주문의 수량을 빼면 두 번째 주문이 부족한 경우 생산이
  시작되는지 확인 — Phase 10에서 놓친 케이스)

DoD: 위 테스트 전체 통과 + 전체 스위트 clean + 커버리지 100% 유지 +
콘솔/스크립트로 사용자 시나리오 재현 확인.

## 구현 범위
- `ConsoleMVC/models/order_repository.py`에
  `sum_confirmed_quantity(sample_id, exclude_order_id=None)` 추가
- `ConsoleMVC/controllers/order_controller.py`의 재고 비교 로직을
  가용 재고 기준으로 수정
- `ConsoleMVC/models/production_line.py`의 대기 항목 시작 직전 재확인
  로직도 동일 기준으로 수정

## 범위 밖
- 이미 큐에 등록된 `target_qty`(생산 계획량) 자체를 나중에 재조정하는
  기능 — 이번엔 "CONFIRMED로 보낼지 PRODUCING으로 보낼지" 판단 기준만
  고친다
