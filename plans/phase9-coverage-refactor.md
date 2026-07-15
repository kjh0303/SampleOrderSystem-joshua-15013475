## 목표
Phase 0~8 완료 시점의 커버리지 분석(대화 중 논의) 결과에 따라:
1. `pyproject.toml`에 `main.py`, `ConsoleMVC/scripts/*`, `ConsoleMVC/views/*`를
   커버리지 측정 대상에서 제외(omit)한다 — 진입점/개발도구/순수 I/O로,
   테스트 가치가 낮다고 이미 판단한 영역이다.
2. 실제로 필요하지만 아직 테스트가 없던 코드(5개 컨트롤러의 `run()` 메뉴
   루프, `order_controller`의 취소 분기 3곳, `production_controller`의
   "대기 없음" 분기)에 대한 테스트를 추가한다.
삭제 대상으로 판단된 코드는 없다.

## 완료 기준 / 검증 테스트

`tests/controllers/test_sample_controller.py`
- `test_run_dispatches_to_register_list_search_and_exits_on_zero`
- `test_run_shows_message_on_invalid_choice`

`tests/controllers/test_order_controller.py`
- `test_receive_order_shows_cancel_message_when_input_is_none`
- `test_approve_order_shows_cancel_message_when_order_id_input_is_none`
- `test_reject_order_shows_cancel_message_when_order_id_input_is_none`
- `test_run_dispatches_to_receive_approve_reject_and_exits_on_zero`
- `test_run_shows_message_on_invalid_choice`

`tests/controllers/test_production_controller.py`
- `test_show_waiting_orders_shows_message_when_queue_is_empty`
- `test_run_dispatches_to_status_and_waiting_and_exits_on_zero`
- `test_run_shows_message_on_invalid_choice`

`tests/controllers/test_shipment_controller.py`
- `test_run_dispatches_to_ship_order_and_exits_on_zero`
- `test_run_shows_message_on_invalid_choice`

`tests/controllers/test_monitoring_controller.py`
- `test_run_dispatches_to_order_volume_and_stock_volume_and_exits_on_zero`
- `test_run_shows_message_on_invalid_choice`

`run()` 테스트는 FakeView의 `show_menu()`가 여러 번 호출될 때마다 다른
값을 순서대로 반환하도록(리스트 + 인덱스 또는 `iter()`) 구성해, 선택한
메뉴에 따라 해당 메서드가 호출됐는지(스텁 카운터/플래그로) 확인한다.

DoD: 위 테스트 전체 통과 + 전체 스위트 clean + `omit` 적용 후
`ConsoleMVC/controllers/*`, `ConsoleMVC/models/*` 커버리지 100% (또는
잔여 미커버 라인이 있다면 그 이유를 PLAN.md에 명시).

## 구현 범위
- `pyproject.toml`의 `[tool.coverage.run]`에 `omit` 추가
- 위 테스트 파일들에 테스트 추가 (기존 FakeView 클래스 재사용/확장)
- 테스트 작성 중 실제 버그(예: `run()` 루프가 잘못 분기하는 경우)가
  발견되면 그 자리에서 수정한다

## 범위 밖
- 새로운 기능 추가
- `views/*.py` 자체에 대한 테스트 작성 (Phase 3 결정 유지, 이번엔 omit
  설정으로 명시적으로 범위 밖임을 표시)
- `main.py`/`generate_dummy_data.py`에 대한 테스트 작성
