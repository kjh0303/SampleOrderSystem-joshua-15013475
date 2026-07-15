## 목표
지금까지 각 Phase에서 개별적으로 검증한 컨트롤러들이 `main.py`를 통해
실제로 하나의 흐름(예약 → 승인 → (생산) → 출고 → 모니터링)으로 정상
연결되는지 확인한다. `main.py` 자체의 배선은 이미 각 Phase 진행 중
갱신돼 있으므로, 이번 Phase는 새 기능 구현이 아니라 **통합 검증**이 핵심이다.

## 완료 기준 / 검증 테스트

`tests/test_end_to_end.py` (신규, 컨트롤러를 직접 조합해 전체 흐름 검증 —
Fake View로 입력만 대체하고 실제 Repository/ProductionLine을 그대로 사용)

- `test_full_lifecycle_when_stock_is_sufficient`
  - 시료 등록 → 주문 접수 → 승인(재고 충분 → 즉시 CONFIRMED) → 출고(RELEASE)
  - 각 단계 후 상태와 재고를 확인
- `test_full_lifecycle_when_stock_is_insufficient`
  - 시료 등록(재고 0) → 주문 접수 → 승인(재고 부족 → PRODUCING, 큐 등록 +
    즉시 생산 시작) → 생산 완료 시점 이후 조회(모니터링) → CONFIRMED 전환
    확인 → 출고(RELEASE)

추가로 콘솔 자체에서 수동으로 아래 시나리오를 1회씩 실행해 확인한다.
- `python -m ConsoleMVC.main`으로 실행
- 시료 등록 → 조회 → 검색
- 주문 접수 → 승인(재고 부족 케이스) → 생산 라인에서 현황/대기열 확인
- 모니터링에서 상태별 주문량 + 재고 상태(여유/부족/고갈) 확인
- 출고 처리 → 모니터링에서 RELEASE 반영 확인
- 잘못된 메뉴 입력 시 "잘못된 입력입니다." 처리 확인

DoD: 통합 테스트 2개 통과 + 전체 스위트 clean + 위 콘솔 시나리오 수동 확인.

## 구현 범위
- `tests/test_end_to_end.py` 추가
- 통합 테스트 진행 중 배선 문제나 누락된 예외 처리가 발견되면 그 자리에서
  수정한다 (새 기능 추가가 아니라 기존 배선의 버그 수정 범위로 한정)

## 범위 밖
- 새로운 메뉴/기능 추가
- `main.py`의 입출력 방식(콘솔) 자체를 바꾸는 것
