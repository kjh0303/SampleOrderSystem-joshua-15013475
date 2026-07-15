## 목표
`MonitoringController.show_stock_volume`에 재고 상태 판정(여유/부족/고갈)을
구현한다. 또한 다른 메뉴(시료 관리/생산 라인/출고 처리)와 동일하게
`ProductionLine.sync()`를 호출해, 방금 완료된 생산이 재고에 반영된 뒤
표시되도록 한다 (Phase 5 follow-up에서 "Phase 7에서 재검토"로 남겨둔 항목).

## 판정 규칙 (CLAUDE.md 기준)
- **고갈**: `stock_qty == 0` (수요와 무관하게 최우선 판정)
- **부족**: `stock_qty < 해당 시료에 대한 미출고 수요 합계`
- **여유**: 그 외 (재고가 수요 이상)

"미출고 수요"는 아직 출고(RELEASE)되지 않았고 거절(REJECTED)되지도 않은
주문의 수량 합 — 즉 `RESERVED`/`PRODUCING`/`CONFIRMED` 상태 주문의 수량
합으로 정의한다 (CONFIRMED도 아직 실제 출고 전이라 재고에서 빠지지
않았으므로 수요에 포함).

## 완료 기준 / 검증 테스트

`tests/controllers/test_monitoring_controller.py` (신규)
- `test_show_order_volume_passes_valid_orders_to_view`
  (REJECTED 제외한 주문만 view로 전달되는지 — 기존 `find_valid_orders` 재사용 확인)
- `test_show_stock_volume_marks_zero_stock_as_고갈_regardless_of_demand`
- `test_show_stock_volume_marks_stock_below_demand_as_부족`
- `test_show_stock_volume_marks_stock_at_or_above_demand_as_여유`
- `test_show_stock_volume_syncs_production_before_computing_status`
  (완료 시각이 지난 큐 항목이 있으면, 조회 시 재고가 갱신된 뒤 상태가
  판정되는지 확인)

DoD: 위 5개 테스트 통과 + 전체 스위트 clean + 콘솔 수동 확인.

## 구현 범위
- `ConsoleMVC/controllers/monitoring_controller.py`
  - 생성자에 `production_line` 추가
  - `show_stock_volume`에서 `sync()` 호출 후, 시료별 재고 상태(여유/부족/고갈)를
    계산해 `(sample, status)` 목록을 view로 전달
- `ConsoleMVC/views/monitoring_view.py`: `show_stock_status`가
  `(sample, status)` 목록을 받아 상태 라벨과 함께 출력하도록 변경
- `ConsoleMVC/main.py`: `MonitoringController` 생성 시 `production_line` 주입

## 범위 밖
- 콘솔 UI 전체 통합/최종 점검 — Phase 8
