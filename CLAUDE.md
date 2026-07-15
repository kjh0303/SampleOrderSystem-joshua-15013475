# 반도체 시료 생산주문관리 프로그램

## 개요

반도체 시료(Sample)의 주문 접수 → 승인/거절 → 생산 → 출고 흐름을 관리하는
**Python 콘솔 기반** 프로그램.

## 도메인 모델

### 시료 (Sample)

시스템의 가장 기본이 되는 단위. 시스템에 등록된 시료만 주문 가능하다.

| 속성 | 설명 |
|---|---|
| 시료 ID | 고유 식별자 |
| 이름 | 시료 이름 (검색 대상) |
| 평균 생산시간 | 시료 1개를 생산하는 데 걸리는 평균 시간 |
| 수율 | 정상 생산품 수 / 총 생산 수 (ex. 100개 생산 중 정상 90개 → 0.9) |

### 주문 (Order)

고객이 시료와 수량을 지정해 생성하며, 아래 상태 중 하나를 가진다.

| 상태 | 의미 |
|---|---|
| RESERVED | 주문 접수 |
| REJECTED | 주문 거절 (최종 상태) |
| PRODUCING | 주문 승인 완료 + 재고 부족으로 생산 중 |
| CONFIRMED | 주문 승인 완료 + 출고 대기 중 |
| RELEASE | 출고 완료 (최종 상태) |

예약(생성) 시 입력값: 시료 ID, 고객명, 주문 수량.

#### 상태 전이 규칙

```
RESERVED --(승인, 재고 충분)--> CONFIRMED
RESERVED --(승인, 재고 부족)--> PRODUCING   (생산 라인에 자동 등록)
RESERVED --(거절)-------------> REJECTED    [최종]
PRODUCING --(생산 완료)-------> CONFIRMED
CONFIRMED --(출고 실행)-------> RELEASE      [최종]
```

- 승인 처리 시 재고 충분 여부는 시스템이 자동으로 판단해 CONFIRMED/PRODUCING 중 하나로 분기한다.
- REJECTED, RELEASE는 더 이상 전이되지 않는 최종 상태다.

## 데이터베이스 스키마

**DB 종류**: JSON 파일 기반 저장소. 별도 DB 서버/엔진 없이 테이블별로
JSON 파일을 두고 직접 읽기/쓰기로 영속화한다.

- `samples.json`
- `orders.json`
- `production_queue.json`

세 개의 테이블(=JSON 파일)로 구성한다.

### Sample

| 컬럼 | 설명 |
|---|---|
| sample_id (PK) | 시료 ID |
| name | 이름 |
| avg_production_time | 평균 생산시간 |
| yield_rate | 수율 |
| stock_qty | 현재 재고 수량 |

### Order

| 컬럼 | 설명 |
|---|---|
| order_id (PK) | 주문 ID |
| sample_id (FK → Sample) | 주문 대상 시료 |
| customer_name | 고객명 |
| quantity | 주문 수량 |
| status | RESERVED / REJECTED / PRODUCING / CONFIRMED / RELEASE |
| reserved_at | 접수 시각 |
| decided_at | 승인/거절 처리 시각 |
| released_at | 출고 시각 |

### ProductionQueue

| 컬럼 | 설명 |
|---|---|
| queue_id (PK) | 큐 항목 ID |
| order_id (FK → Order) | 대상 주문 |
| sample_id (FK → Sample) | 생산 대상 시료 |
| target_qty | 목표 생산량 (실 생산량 = `ceil(부족분 / 수율)`) |
| total_production_time | 총 생산 시간 (`평균 생산시간 * target_qty`) |
| enqueued_at | 큐 등록 시각 (FIFO 정렬 기준) |
| started_at | 생산 시작 시각 (PRODUCING 전환 시점, `NULL`이면 아직 대기 중) |
| finished_at | 생산 종료 예정/완료 시각 (`started_at + total_production_time`, `started_at`이 `NULL`이면 `NULL`) |

`status` 컬럼은 별도로 두지 않는다. 대신 아래 규칙으로 상태를 **판단**한다.

- `started_at IS NULL` → WAITING
- `started_at`이 있고 `now < finished_at` → PRODUCING
- `finished_at`이 있고 `now >= finished_at` → DONE

생산 라인은 직렬 처리이므로 PRODUCING으로 판단되는 행은 항상 최대 1개만
존재한다.

**타이머/스케줄러는 사용하지 않는다.** 콘솔에서 어떤 조작(메뉴 입력)이
들어올 때마다, 그 시점의 현재 시각을 기준으로 진행 중인 생산 항목의
`finished_at`을 확인해 아래 동기화 로직을 수행한 뒤 결과를 출력한다.

1. 현재 `PRODUCING`으로 판단되는 큐 항목이 있고 `now >= finished_at`이면
   - `Sample.stock_qty`를 `target_qty`만큼 증가시킨다.
   - 해당 `Order.status`를 `PRODUCING` → `CONFIRMED`로 전환한다.
   - 이 큐 항목을 DONE 처리(완료로 판단되도록 둠)하고, 다음 `WAITING`
     항목이 있으면 `started_at = now`로 설정해 생산을 시작시킨다.
2. 위 과정을 다음 대기 항목이 이미 완료 조건을 만족할 때까지(짧은 생산
   시간이 몰려 있는 경우) 반복한다.

이 동기화는 재고/생산 현황에 관련된 메뉴(모니터링, 생산 라인, 시료 조회 등)
진입 시 공통으로 호출하는 함수로 구현해, 어떤 화면에 진입하든 최신 상태가
반영되도록 한다.

## 메인 메뉴 구성

### 1. 시료 관리

새로운 시료를 등록하고 조회/검색한다.

- **시료 등록**: 새 시료 추가. 속성값 = 시료 ID, 이름, 평균 생산시간, 수율
- **시료 조회**: 등록된 모든 시료 목록 확인 (현재 재고 수량 함께 표시)
- **시료 검색**: 이름 등 속성으로 특정 시료 검색

### 2. 주문 (접수 / 승인 / 거절)

고객 주문 접수 및 생산 라인 담당자의 승인·거절 처리.

- **시료 예약(접수)**: 고객이 원하는 시료와 수량을 주문 → RESERVED 상태로 생성
- **접수된 주문 목록**: RESERVED 상태 주문 목록 표시
- **주문 승인**: 접수된 특정 주문 승인
  - 재고 충분 → 즉시 CONFIRMED로 전환
  - 재고 부족 → 생산 라인에 자동 등록, PRODUCING으로 전환
- **주문 거절**: 접수된 특정 주문 거절 → 즉시 REJECTED로 전환

### 3. 모니터링

담당자가 시스템 상태를 한눈에 파악할 수 있도록 구성.

- **주문량 확인**: 상태별(RESERVED / CONFIRMED / PRODUCING / RELEASE) 주문 목록 확인
  - REJECTED는 유효하지 않은 주문이므로 집계에서 제외
- **재고량 확인**: 시료별 현재 재고 수량 확인. 주문 대비 재고 수량에 따라 상태 표기
  - **여유**: 주문 대비 재고 충분
  - **부족**: 주문 대비 재고 수량 부족
  - **고갈**: 재고 수량이 0

### 4. 출고 처리

CONFIRMED 상태 주문에 대해 출고를 실행.

- 재고가 충분해진 CONFIRMED 주문에 대해 특정 주문의 출고를 실행
- 실행 시 주문 상태가 RELEASE로 전환

### 5. 생산 라인

주문량 대비 부족분을 생산하며, 수율 및 오차를 고려해 실제 생산량을 계산한다.

- **생산 계산식**
  - 실 생산량 = `ceil(부족분 / 수율)`
  - 총 생산 시간 = `평균 생산시간 * 실 생산량`
- **생산 라인 동시성**: 생산 라인은 한 번에 **하나의 작업만** 처리한다
  (직렬 처리). 다음 작업은 현재 작업이 끝나야 큐(FIFO)에서 꺼내 시작한다.
- **완료 처리(타이머 스케줄링)**: 작업이 시작될 때 총 생산 시간만큼의
  완료 스케줄을 예약(schedule)한다. 예약된 시각이 되면 콜백을 통해
  - 재고를 실 생산량만큼 증가시키고
  - 해당 주문 상태를 PRODUCING → CONFIRMED로 전환하고
  - 큐에 대기 중인 다음 작업이 있으면 이어서 시작한다.

  조회 시점에 경과 시간을 계산하는 방식(lazy evaluation)이 아니라,
  타이머 기반으로 스케줄된 시점에 상태를 갱신하는 방식을 사용한다.
- **생산 현황 표기**: 현재 생산 중인 시료 정보 표시 (주문 정보, 현재까지 생산량 등 — 표기 수준은 구현 시 자율 결정)
- **대기 주문 확인**: 생산 큐(대기열)의 목록 확인. 스케줄링 전략은 **FIFO**

## 기술 스택

- Python, 콘솔(CLI) 기반 프로그램

## 디렉토리 구조

PoC(`ConsoleMVC/`, `Data/`) 정합성 점검(PLAN.md Phase 0) 결과, `Data/`의
JSON 기반 모델/저장소를 `ConsoleMVC/models/`로 흡수 통합했다. `Data/`
폴더는 제거되었다.

```
ConsoleMVC/
├── main.py
├── data/                        # JSON 파일 저장소 (samples/orders/production_queue)
├── controllers/                 # 메뉴별 컨트롤러
├── views/                       # 콘솔 입출력 (비즈니스 로직 없음)
└── models/
    ├── sample.py                # Sample dataclass
    ├── order.py                 # Order dataclass, OrderStatus
    ├── production_queue.py      # ProductionQueue dataclass
    ├── json_repository.py       # 범용 JSON CRUD 리포지토리
    ├── sample_repository.py
    ├── order_repository.py
    ├── production_queue_repository.py  # Phase 5에서 사용 예정 (아직 미연결)
    └── production_line.py       # Phase 5에서 재구현 예정 (현재 placeholder)
```

시료 관리 / 주문 접수·거절 / 출고 처리는 PoC 로직이 문서 규칙과 일치해
그대로 유지했다. 아래 항목은 PoC 구현이 문서 규칙과 어긋나 있어 자리표시자
(`NotImplementedError`)로 대체했고, 해당 PLAN.md Phase에서 별도 Plan.md로
다시 구현한다.

- 주문 승인 시 재고 충분/부족에 따른 CONFIRMED/PRODUCING 분기 (Phase 4)
- 생산 라인의 target_qty/총 생산 시간 계산, started_at/finished_at 기반
  완료 판단(sync_production_state), FIFO 직렬 처리 (Phase 5)
- 재고 여유/부족/고갈 상태 판정은 아직 표시만 없고 조회 자체는 동작한다 (Phase 7)

## 개발 주안점

1. **문서 관리**: `CLAUDE.md`, `PRD.md`, `PLAN.md`를 함께 관리한다.
   - `CLAUDE.md`: 도메인 규칙, 메뉴 구성 등 프로젝트 컨텍스트 (본 문서)
   - `PRD.md`: 요구사항 정의 문서
   - `PLAN.md`: 구현 계획 문서
2. **테스트 하네스 도입**: `pytest` 기반 테스트 프레임워크를 구축하고, 단위/통합 테스트를 자동으로 실행할 수 있도록 한다.
3. **Test**: 핵심 로직(상태 전이, 재고 계산, 생산량 계산 등)은 테스트로 검증한다.
4. **Clean Code**: 가독성과 유지보수성을 고려한 코드 작성.
5. **Commit 이력**: [Conventional Commits](https://www.conventionalcommits.org/) 컨벤션(`feat:`, `fix:`, `refactor:` 등)을 따르며, 기능 단위로 자주 커밋한다.
