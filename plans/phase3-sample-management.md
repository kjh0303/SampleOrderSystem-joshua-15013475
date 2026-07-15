## 목표
`SampleController`(등록/목록 조회/이름 검색)의 동작을 단위 테스트로 검증한다.
`SampleView`는 입출력만 담당하고 로직이 없으므로, 실제 콘솔(stdin/stdout) 대신
테스트 더블(FakeSampleView)로 대체해 컨트롤러 로직만 검증한다. 저장소는
`tmp_path` 기반 실제 `SampleRepository`를 사용한다(파일 I/O 자체는
Phase 2에서 이미 검증됨).

## 완료 기준 / 검증 테스트

`tests/controllers/test_sample_controller.py`
- `test_register_sample_adds_to_repository_and_shows_success_message`
  - 입력: FakeView가 `input_new_sample()`에서 `(1, "WaferA", 2.0, 0.9)` 반환
  - 기대값: repo에 sample_id=1이 저장됨, FakeView에 "[등록 완료] #1 WaferA" 메시지 기록
- `test_register_sample_shows_cancel_message_when_input_is_none`
  - 입력: FakeView가 `input_new_sample()`에서 `None` 반환
  - 기대값: repo에 아무것도 추가되지 않음, "취소" 메시지 기록
- `test_register_sample_shows_error_message_on_duplicate_id`
  - 입력: 동일 sample_id로 두 번 등록 시도
  - 기대값: 두 번째 시도에서 repo가 올린 `ValueError` 메시지가 그대로 표시됨
    (repo에는 여전히 1개만 존재)
- `test_list_samples_shows_all_samples_from_repository`
  - 입력: repo에 시료 2개 미리 등록
  - 기대값: FakeView.show_samples가 그 2개를 그대로 전달받음
- `test_search_samples_shows_only_matching_samples`
  - 입력: repo에 "8inch Wafer", "SiC Sample" 등록, FakeView가 검색어 "wafer" 반환
  - 기대값: FakeView.show_samples가 "8inch Wafer"만 포함한 리스트를 전달받음

DoD: 위 5개 테스트 통과 + 전체 스위트 clean.

## 구현 범위
- `tests/controllers/__init__.py`(필요 시) 및
  `tests/controllers/test_sample_controller.py` 생성
- 테스트 파일 내에 `FakeSampleView` 테스트 더블 정의 (SampleView와 동일한
  메서드 시그니처: `input_new_sample`, `input_search_keyword`, `show_samples`,
  `show_message`, `show_menu`는 이번 테스트에서 불필요하면 생략 가능)

## 범위 밖
- `SampleView`(실제 입출력 클래스) 자체에 대한 테스트 — 로직이 없어 생략
- `run()`의 메뉴 루프 테스트 — 단순 반복문이라 낮은 가치, 생략
- 다른 컨트롤러(주문/생산/출고/모니터링) — 각자의 Phase에서 진행
