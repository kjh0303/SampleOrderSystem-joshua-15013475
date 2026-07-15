## 목표
프로젝트 루트에서 `pytest`를 실행하면 (테스트가 하나도 없더라도) 정상
동작하도록 테스트 하네스를 구성한다. 이후 Phase에서 `ConsoleMVC` 하위
모듈(`models`, `controllers`, `views`)을 `tests/`에서 import해 테스트할 수
있도록 경로를 설정해둔다.

## 완료 기준 / 검증 테스트
- 테스트: `tests/test_harness_setup.py::test_sample_model_is_importable`
- 입력: 없음 (단순 import 및 인스턴스 생성 확인)
- 기대값: `ConsoleMVC.models.sample.Sample`을 정상적으로 import하고
  인스턴스를 생성할 수 있다 (`sample.stock_qty == 0`)
- 위 테스트를 포함해 프로젝트 루트에서 `pytest` 실행 시 exit code 0

## 구현 범위
- 루트에 `pyproject.toml` 생성
  - `[tool.pytest.ini_options]`: `testpaths = ["tests"]`,
    `pythonpath = ["."]` (→ `ConsoleMVC.models...` 형태로 import)
- `tests/` 디렉토리 및 `tests/test_harness_setup.py` 생성 (위 완료 기준 테스트 1개)
- `ConsoleMVC/models/__init__.py`, `ConsoleMVC/controllers/__init__.py`,
  `ConsoleMVC/views/__init__.py`는 이미 존재 — 필요하면 최상위
  `ConsoleMVC/__init__.py`를 추가해 패키지로 만든다

## 범위 밖
- 도메인 로직(상태 전이, 재고 계산 등) 테스트 — Phase 2에서 진행
- `ConsoleMVC/main.py`, `controllers`, `views`의 기존 `from models...` 스타일
  상대 import를 리팩터링하는 것 — 지금은 건드리지 않는다 (콘솔 앱 실행은
  기존 방식대로 `ConsoleMVC` 디렉토리에서 `python main.py`로 유지, 테스트는
  `tests/`에서 `ConsoleMVC.models...`로 별도 경로를 사용)
- CI 파이프라인 구성

## 추가: pytest-cov 커버리지 설정

### 목표
`pytest` 실행 시 커버리지 리포트가 함께 출력되도록 `pytest-cov` 설정을
`pyproject.toml`에 추가한다 (venv에 이미 설치되어 있음, `plugins: cov-7.1.0`).

### 완료 기준
- 별도 옵션 없이 `pytest` 실행 시 `--cov=ConsoleMVC --cov-report=term-missing`가
  자동 적용되어 파일별 커버리지 표(`Name / Stmts / Miss / Cover / Missing`)가
  출력된다. 빌드/설정 변경이므로 별도 단위 테스트 대신 실행 결과로 확인한다.

### 구현 범위
- `pyproject.toml`의 `[tool.pytest.ini_options]`에 `addopts` 추가:
  `--cov=ConsoleMVC --cov-report=term-missing`

### 범위 밖
- 커버리지 임계치(예: `--cov-fail-under`) 강제 — 지금은 표시만, 실패 조건은
  아직 두지 않는다 (필요해지면 별도로 논의)
