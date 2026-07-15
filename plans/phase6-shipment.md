## 목표
`ShipmentController.ship_order`(CONFIRMED 주문 출고 → RELEASE 전환)의
나머지 케이스에 대한 단위 테스트를 보강한다. sync 훅 배선과 완료된 생산
반영 테스트는 Phase 5 follow-up에서 이미 추가됨
(`test_ship_order_reflects_completed_production_via_sync`).

## 완료 기준 / 검증 테스트

`tests/controllers/test_shipment_controller.py` (기존 파일에 추가)
- `test_ship_order_removes_stock_and_transitions_to_release`
  - 입력: 재고 20, CONFIRMED 주문 수량 10
  - 기대값: 출고 후 재고 10, 주문 상태 `RELEASE`
- `test_ship_order_shows_cancel_message_when_input_is_none`
- `test_ship_order_shows_error_when_order_not_found_or_not_confirmed`

DoD: 위 테스트 통과 + 전체 스위트 clean.

## 구현 범위
- `tests/controllers/test_shipment_controller.py`에 테스트 3개 추가
  (FakeShipmentView는 이미 있음, 재사용)
- 기존 `ShipmentController` 구현이 이미 문서 규칙과 일치하는 것으로
  확인되면(Phase 0 판단대로) 프로덕션 코드는 수정하지 않는다. 테스트
  작성 중 불일치가 발견되면 그때 수정한다.

## 범위 밖
- 모니터링(Phase 7), 콘솔 UI 통합(Phase 8)
