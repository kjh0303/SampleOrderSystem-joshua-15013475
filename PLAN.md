# PLAN — 구현 계획

도메인/요구사항은 [CLAUDE.md](./CLAUDE.md), [PRD.md](./PRD.md) 참고.
본 문서는 구현 순서와 단계별 완료 기준(DoD)을 정의한다.

## 개발 원칙

- 각 단계는 테스트(pytest)와 함께 완료한다 (Harness 우선 구축).
- 커밋은 [Conventional Commits](https://www.conventionalcommits.org/)
  컨벤션(`feat:`, `fix:`, `refactor:`, `test:`, `docs:` 등)을 따르며,
  기능 단위로 작게 나눠 커밋한다.
- 도메인 로직(상태 전이, 재고 계산, 생산량 계산)을 UI(콘솔 입출력)와
  분리해 테스트 가능한 구조로 만든다.

## 단계별 계획

### Phase 0. 프로젝트 세팅

- 디렉토리 구조, `pytest` 테스트 하네스 구성
- DoD: `pytest` 실행 시 (빈 테스트라도) 정상 동작

### Phase 1. 도메인 모델 & 데이터 저장소

- `Sample`, `Order`(+`OrderStatus`), `ProductionQueue` 3개 모델 구현
  (스키마는 CLAUDE.md 참고)
- JSON 파일(`samples.json`, `orders.json`, `production_queue.json`) 기반
  저장소(repository) 계층 구현 (읽기/쓰기)
- 상태 전이 규칙을 검증하는 단위 테스트 작성
- DoD: 상태 전이 규칙에 대한 테스트 통과, 3개 모델의 CRUD 동작 테스트 통과

### Phase 2. 시료 관리

- 시료 등록 / 조회(재고 수량 포함) / 검색
- DoD: 등록·조회·검색 단위 테스트 통과, 콘솔 메뉴 연동

### Phase 3. 주문 (접수 / 승인 / 거절)

- 시료 예약(주문 생성, `RESERVED`)
- 접수된 주문 목록 표시
- 주문 승인: 재고 충분/부족 분기 로직 (`CONFIRMED` / `PRODUCING`)
- 주문 거절 (`REJECTED`)
- DoD: 승인 시 재고 분기 로직에 대한 단위 테스트 통과

### Phase 4. 생산 라인

- 생산량/생산 시간 계산 (`ceil(부족분 / 수율)`, `평균 생산시간 * 실 생산량`)
- 생산 큐(FIFO) 및 대기 주문 확인. 생산 라인은 직렬 처리(동시 1개 작업)
- `ProductionQueue`에는 `status` 컬럼을 두지 않고 `started_at`/`finished_at`만
  저장한다. WAITING/PRODUCING/DONE 여부는 조회 시점에 두 필드와 현재
  시각을 비교해 판단한다.
- **타이머/스케줄러는 사용하지 않는다.** 콘솔 조작이 들어올 때마다 현재
  시각과 진행 중인 작업의 `finished_at`을 비교해 동기화하는 함수(예:
  `sync_production_state()`)를 만들고, 재고/생산 현황 관련 메뉴 진입 시
  공통으로 호출한다.
  - `now >= finished_at`이면 재고 반영 + 주문 상태 전환
    (`PRODUCING` → `CONFIRMED`) + 다음 대기 항목의 `started_at = now` 설정을
    처리하고, 완료 조건을 만족하는 항목이 없을 때까지 반복한다.
- 생산 현황 표기
- DoD: 생산량 계산 단위 테스트 통과, FIFO 큐 동작(직렬 처리) 검증,
  `started_at`/`finished_at` 기반 상태 판단 로직 테스트 통과, 조회 시점
  동기화 함수가 경과 시간에 따라 재고/주문 상태를 올바르게 갱신하는지에
  대한 테스트 통과 (테스트에서는 `started_at`을 과거 시각으로 주입해
  경과 시간을 시뮬레이션)

### Phase 5. 출고 처리

- `CONFIRMED` 주문 출고 실행 → `RELEASE` 전환
- DoD: 출고 처리 단위 테스트 통과

### Phase 6. 모니터링

- 상태별 주문량 확인 (REJECTED 제외)
- 재고량 확인 및 여유/부족/고갈 상태 판정
- DoD: 상태 판정 로직 단위 테스트 통과

### Phase 7. 콘솔 UI 통합

- 메인 메뉴(시료 관리 / 주문 / 모니터링 / 출고 처리 / 생산 라인) 구성
- 각 메뉴의 하위 기능 연결 및 입출력 처리
- DoD: 전체 흐름(예약 → 승인 → (생산) → 출고)이 콘솔에서 end-to-end 동작

## 진행 상태

| Phase | 상태 |
|---|---|
| 0. 프로젝트 세팅 | 미착수 |
| 1. 도메인 모델 | 미착수 |
| 2. 시료 관리 | 미착수 |
| 3. 주문 | 미착수 |
| 4. 생산 라인 | 미착수 |
| 5. 출고 처리 | 미착수 |
| 6. 모니터링 | 미착수 |
| 7. 콘솔 UI 통합 | 미착수 |
