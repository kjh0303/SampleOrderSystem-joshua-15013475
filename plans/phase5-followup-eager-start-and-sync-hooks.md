## 배경 / 변경 이유
Phase 5 구현은 "생산 라인" 메뉴에 진입해야만 `ProductionLine.sync()`가
호출되어 대기 중인 작업이 시작되고, 완료된 작업의 재고/주문 상태가
반영됐다. 사용자 피드백에 따라 다음과 같이 바꾼다.

1. 주문 승인 시 재고 부족으로 `ProductionQueue`에 등록되는 **그 순간**,
   생산 라인이 비어 있다면 즉시 생산이 시작(`started_at` 설정)되어야
   한다. "생산 라인" 메뉴는 조회 전용이지, 생산을 트리거하는 메뉴가
   아니다.
2. 재고/생산 상태 반영(`sync`)은 사용자가 관련 화면을 사용하는 **어떤
   시점에든** 이루어지면 된다 — 지금까지는 "생산 라인" 메뉴에서만
   호출했는데, **시료 관리(조회/검색)**, **생산 라인(조회)**,
   **출고 처리** 세 곳 모두에서 진입 시 호출하도록 넓힌다.

## 목표
`OrderController.approve_order`가 큐 등록 직후 `ProductionLine.sync()`를
호출해 즉시 생산을 시작시키고, `SampleController`(조회/검색)와
`ShipmentController`(출고)도 각 동작 시작 시 `ProductionLine.sync()`를
호출하도록 만든다.

## 완료 기준 / 검증 테스트

`tests/controllers/test_order_controller.py` (기존 파일에 추가)
- `test_approve_order_starts_production_immediately_when_line_is_idle`
  - 재고 부족으로 큐 등록 → 생산 라인이 비어 있으므로 등록 직후
    `started_at`이 설정되어 있어야 함 (더 이상 `None`이 아님)
- `test_approve_order_keeps_new_item_waiting_when_line_is_busy`
  - 이미 진행 중인 작업이 있는 상태에서 재고 부족 주문을 승인하면,
    새 큐 항목은 `started_at is None`(WAITING)으로 남아야 함

`tests/controllers/test_sample_controller.py` (기존 파일에 추가)
- `test_list_samples_reflects_completed_production_via_sync`
  - 이미 완료 시각이 지난 큐 항목이 있는 상태에서 `list_samples()` 호출 시
    재고가 갱신된 상태로 조회됨을 확인
- `test_search_samples_reflects_completed_production_via_sync`

`tests/controllers/test_shipment_controller.py` (신규 파일 — 최소 범위)
- `test_ship_order_reflects_completed_production_via_sync`
  - 완료 시각이 지난 큐 항목으로 주문이 막 `CONFIRMED`가 될 상황에서
    `ship_order()` 호출 시 해당 주문이 출고 대상 목록에 나타나고 정상
    출고됨을 확인
  - `ShipmentController`의 나머지 전체 테스트(정상 출고, 잘못된 주문 등)는
    Phase 6에서 별도로 다룬다 — 여기서는 sync 훅 배선만 확인한다

DoD: 위 테스트 전체 통과 + 전체 스위트 clean + 콘솔 수동 확인(승인 즉시
생산 시작되는지, 시료 조회/출고 화면에서 완료된 생산이 반영되는지).

## 구현 범위
- `ConsoleMVC/controllers/order_controller.py`: 생성자에 `production_line`
  추가, `approve_order`의 큐 등록 직후 `self._production_line.sync()` 호출
- `ConsoleMVC/controllers/sample_controller.py`: 생성자에 `production_line`
  추가, `list_samples`/`search_samples` 시작 시 `sync()` 호출
- `ConsoleMVC/controllers/shipment_controller.py`: 생성자에
  `production_line` 추가, `ship_order` 시작 시 `sync()` 호출
- `ConsoleMVC/main.py`: 세 컨트롤러 생성 시 `production_line` 주입
- 관련 테스트 추가/보강 (위 참고)

## 범위 밖
- `ShipmentController`의 전체 테스트 커버리지(정상/거절/실패 케이스 등) —
  Phase 6에서 진행
- 모니터링(Phase 7) 메뉴에도 `sync()`를 붙일지 여부 — Phase 7에서 다시 결정
