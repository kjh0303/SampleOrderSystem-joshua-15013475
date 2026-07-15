## 목표
Phase 0에서 이관된 도메인 모델(`Sample`, `Order`, `ProductionQueue`)과
저장소(`JsonRepository`, `SampleRepository`, `OrderRepository`,
`ProductionQueueRepository`)의 핵심 동작을 단위 테스트로 검증한다.

이미 구현되어 있는 코드에 테스트를 붙이는 작업이므로, 테스트 작성 직후 바로
통과하는 항목도 있을 수 있다(순수 RED는 아님). 다만 아래 완료 기준 테스트를
먼저 작성해 실행하고, 실패하는 경우(버그 발견)는 구현을 고쳐 통과시킨다.

## 완료 기준 / 검증 테스트

`tests/models/test_sample.py`
- `test_add_stock_increases_stock_qty`
- `test_remove_stock_decreases_stock_qty`

`tests/models/test_order.py`
- `test_new_order_defaults_to_reserved_status`
- `test_change_status_updates_status`
- `test_to_dict_serializes_status_as_plain_string`
- `test_from_dict_parses_status_string_back_to_enum`

`tests/models/test_production_queue.py`
- `test_to_dict_and_from_dict_roundtrip`

`tests/models/test_json_repository.py` (임시 파일 경로에 `tmp_path` fixture 사용)
- `test_create_generates_id_when_empty`
- `test_create_keeps_given_id_when_provided`
- `test_get_returns_none_when_missing`
- `test_list_all_returns_all_created_records`
- `test_update_persists_partial_changes`
- `test_save_overwrites_whole_record`
- `test_delete_removes_record_and_returns_true`
- `test_delete_returns_false_when_missing`

`tests/models/test_sample_repository.py`
- `test_add_raises_when_duplicate_sample_id`
- `test_find_by_name_is_case_insensitive_substring_match`

`tests/models/test_order_repository.py`
- `test_add_assigns_incrementing_order_id`
- `test_find_by_status_filters_correctly`
- `test_find_valid_orders_excludes_rejected`
- `test_count_by_status_counts_every_status_including_zero`

`tests/models/test_production_queue_repository.py`
- `test_add_and_find_by_id_roundtrip`
- `test_save_overwrites_started_at_and_finished_at`

DoD: 위 테스트 전체 통과 + 전체 스위트(`pytest`) clean.

## 구현 범위
- `tests/models/` 디렉토리 및 위 테스트 파일 생성
- 각 저장소 테스트는 실제 파일시스템 대신 `tmp_path`(pytest 내장 fixture)로
  격리된 JSON 파일 경로를 사용해 테스트 간 데이터가 섞이지 않게 한다
- 테스트 작성 중 실제 버그가 발견되면(구현이 Plan의 완료 기준을 만족하지
  못하면) `ConsoleMVC/models/*.py`를 수정해 통과시킨다

## 범위 밖
- `ProductionQueue`의 `target_qty`/`total_production_time` 계산, FIFO 직렬
  처리, `started_at`/`finished_at` 기반 완료 판단(`sync_production_state`) —
  Phase 5에서 별도 Plan.md로 진행
- 주문 승인의 재고 분기 로직 — Phase 4에서 진행
- 컨트롤러/뷰 계층 테스트 — 각 메뉴 Phase(3, 4, 6, 7)에서 진행
