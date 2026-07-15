class ProductionView:
    """생산 라인 화면 (입출력만 담당).

    실제 생산 현황/대기열 표시 로직은 PLAN.md Phase 5 구현에 맞춰 추가한다.
    """

    def show_menu(self) -> str:
        print("\n----- 생산 라인 -----")
        print("1. 생산 현황 확인")
        print("2. 대기 주문 확인")
        print("0. 이전 메뉴")
        return input("메뉴를 선택하세요 >> ").strip()

    def show_message(self, message: str) -> None:
        print(message)
