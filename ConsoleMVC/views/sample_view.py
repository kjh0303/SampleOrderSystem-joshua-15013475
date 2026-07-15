from typing import List, Optional, Tuple

from models.sample import Sample


class SampleView:
    """시료 관리 화면 (입출력만 담당, 비즈니스 로직 없음)"""

    def show_menu(self) -> str:
        print("\n----- 시료 관리 -----")
        print("1. 시료 등록")
        print("2. 시료 목록 조회")
        print("3. 이름으로 검색")
        print("0. 이전 메뉴")
        return input("메뉴를 선택하세요 >> ").strip()

    def input_new_sample(self) -> Optional[Tuple[int, str, float, float]]:
        raw_id = input("시료 ID (0: 취소): ").strip()
        if raw_id == "0":
            return None
        sample_id = int(raw_id)
        name = input("이름: ").strip()
        avg_production_time = float(input("평균 생산시간(분): ").strip())
        yield_rate = float(input("수율(%): ").strip())
        return sample_id, name, avg_production_time, yield_rate

    def input_search_keyword(self) -> str:
        return input("검색할 이름을 입력하세요: ").strip()

    def show_samples(self, samples: List[Sample]) -> None:
        if not samples:
            print("등록된 시료가 없습니다.")
            return
        print(f"{'ID':<5}{'이름':<15}{'평균생산시간':<14}{'수율':<8}{'재고':<8}")
        for s in samples:
            print(
                f"{s.sample_id:<5}{s.name:<15}{s.avg_production_time:<14}{s.yield_rate:<8}{s.stock_qty:<8}"
            )

    def show_message(self, message: str) -> None:
        print(message)
