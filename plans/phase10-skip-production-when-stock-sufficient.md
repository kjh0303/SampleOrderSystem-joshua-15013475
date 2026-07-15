## 배경 / 버그
검증 중 발견: 주문A(100개, 재고0 → target_qty=200)를 승인해 즉시 생산을
시작하고, 곧이어 주문B(50개, 여전히 재고0 → target_qty=100)를 승인하면
라인이 바빠 대기(WAITING)로 등록된다. 주문A의 생산(200개)이 끝나 재고가
200이 되면, 이미 주문B가 필요로 하는 50개를 훨씬 초과하는데도
`ProductionLine.sync()`는 재확인 없이 주문B의 큐 항목(100개)을 그대로
생산 시작시킨다 → 불필요한 과잉 생산(150개 초과 재고) 발생.

## 목표
대기 중인 다음 큐 항목을 **실제로 생산 시작시키기 직전**, 그 시점의
재고가 이미 해당 주문 수량을 충족하는지 다시 확인한다. 충분하면 생산을
시작하지 않고 큐 항목을 제거한 뒤 주문을 바로 `CONFIRMED`로 전환한다.
부족하면 기존대로 생산을 시작한다. 이 확인은 대기열의 각 항목마다
순서대로 반복되어, 여러 주문이 연쇄적으로 재고 충분 판정을 받으면
모두 한 번의 `sync()`에서 처리된다(기존 완료 캐스케이드와 동일한 패턴).

## 완료 기준 / 검증 테스트

`tests/models/test_production_line.py` (기존 파일에 추가)
- `test_sync_confirms_directly_without_production_when_stock_already_sufficient`
  - 대기 중인 큐 항목(target_qty=100)의 주문 수량 50 < 이미 확보된 재고 60
  - `sync()` 호출 시: 주문 상태가 `CONFIRMED`로 전환되고, 재고는 그대로 60
    (target_qty만큼 추가되지 않음), 해당 큐 항목은 더 이상 존재하지 않음
    (`queue_repo.all()`에서 제거됨)
- `test_sync_cascades_skip_across_multiple_waiting_orders_when_stock_becomes_sufficient`
  - 사용자가 제시한 시나리오 그대로 재현: 수율 0.5, 주문1 수량 100
    (target_qty=200, 이미 진행 중이며 완료 시각이 지남), 주문2 수량 50
    (target_qty=100, 대기 중)
  - `sync()` 한 번 호출로: 주문1 완료 처리(재고 0→200) → 주문2는 재고
    200이 이미 50을 충족하므로 생산 없이 바로 `CONFIRMED` 전환, 재고는
    200 그대로 유지(300이 되지 않음)
- `test_sync_still_starts_production_when_stock_remains_insufficient`
  - (회귀 확인) 대기 항목의 주문 수량이 현재 재고보다 크면 기존과 동일하게
    생산이 시작됨(`started_at`/`finished_at` 설정)

DoD: 위 테스트 통과 + 전체 스위트 clean + 콘솔에서 시나리오 재현 확인.

## 구현 범위
- `ConsoleMVC/models/production_queue_repository.py`: `delete(queue_id)`
  래퍼 메서드 추가 (기존 `JsonRepository.delete`를 노출)
- `ConsoleMVC/models/production_line.py`: `sync()`에서 다음 대기 항목을
  꺼내기 전에 재고 재확인 로직 추가, 충분하면 큐 항목 삭제 + 주문
  CONFIRMED 전환(생산 없이)

## 범위 밖
- 승인 시점(`OrderController.approve_order`)의 최초 재고 계산 로직 변경 없음
  (문제는 "이미 큐에 들어간 뒤, 시작 시점"에서만 재확인하는 것)
- 이미 시작(생산 중)된 작업을 중간에 취소하는 기능
