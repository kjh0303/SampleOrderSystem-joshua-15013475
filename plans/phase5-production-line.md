## 목표
`ProductionLine`(현재 빈 placeholder)에 CLAUDE.md에 정의된 동기화 로직을
구현한다: 타이머 없이, 조회 시점마다 현재 시각과 `ProductionQueue`의
`started_at`/`finished_at`을 비교해 (1) 완료된 작업의 재고 반영 + 주문
상태 전환(`PRODUCING`→`CONFIRMED`), (2) 다음 대기 항목 시작을 처리한다.
생산 라인은 직렬 처리이므로 동시에 진행 중인 작업은 최대 1개다.

완료 여부의 "이미 처리됨" 판단은 별도 플래그 없이 **주문 상태**를 이용한다
(주문이 아직 `PRODUCING`이면 미완료, `CONFIRMED`면 이미 처리됨) — 이렇게
하면 `sync()`를 여러 번 호출해도 재고가 중복으로 늘어나지 않는다(멱등성).

## 완료 기준 / 검증 테스트

`tests/models/test_production_line.py` (`now`를 인자로 주입해 시간을 고정)

- `test_sync_starts_first_waiting_item_when_none_active`
- `test_sync_does_not_start_next_item_while_current_is_still_producing`
- `test_sync_completes_active_item_and_updates_stock_and_order_status_when_time_elapsed`
- `test_sync_starts_next_waiting_item_after_completing_current`
- `test_sync_cascades_through_multiple_already_elapsed_items`
  (대기 중인 항목 2개의 소요 시간을 모두 지난 시점으로 `now`를 주면, 한 번의
  `sync()` 호출로 둘 다 순서대로 완료 처리되어야 함)
- `test_current_item_returns_none_when_nothing_active`
- `test_waiting_items_returns_items_sorted_by_enqueued_at`
- `test_sync_is_idempotent_when_called_twice_at_same_time`
  (같은 `now`로 두 번 호출해도 재고가 두 번 늘지 않음)

`tests/controllers/test_production_controller.py` (`FakeProductionView` 사용)

- `test_show_current_status_displays_active_item_after_sync`
- `test_show_current_status_shows_message_when_nothing_producing`
- `test_show_waiting_orders_displays_items_in_fifo_order`

DoD: 위 테스트 전체 통과 + 전체 스위트 clean + 콘솔에서 수동 확인
(더미 데이터로 승인 → 생산 라인 메뉴 진입 시 재고/주문 상태 갱신 확인).

## 구현 범위
- `ConsoleMVC/models/production_line.py`: `ProductionLine` 클래스 구현
  - 생성자: `(order_repo, sample_repo, queue_repo)`
  - `sync(now: datetime | None = None)`: 완료 처리 → 다음 시작을 변화가
    없을 때까지 반복
  - `current_item()`: 현재 진행 중(활성) 항목 반환 (없으면 `None`)
  - `waiting_items()`: 아직 시작 안 한 항목을 `enqueued_at` 순으로 반환
- `ConsoleMVC/controllers/production_controller.py`: `sync()` 호출 후
  `current_item()`/`waiting_items()` 기반으로 화면 표시하도록 구현
  (`NotImplementedError` 제거)
- `ConsoleMVC/views/production_view.py`: 생산 현황/대기열 표시 메서드 추가
- `ConsoleMVC/main.py`: `ProductionLine(order_repo, sample_repo, queue_repo)`로
  생성, `ProductionController`에 주입
- 위 테스트 파일들 추가

## 범위 밖
- 모니터링(Phase 7)/시료 조회(이미 완료된 Phase 3) 메뉴에 진입 시에도
  `sync()`를 호출해 재고를 갱신하는 것 — 이번 Phase는 "생산 라인" 메뉴
  진입 시에만 동기화한다. 다른 메뉴에서 재고가 최신이 아닐 수 있는 점은
  Phase 7(모니터링) 진행 시 다시 검토한다.
- 생산 시간 단위/포맷 변경 (분 단위, `%Y-%m-%d %H:%M` 그대로 사용)
