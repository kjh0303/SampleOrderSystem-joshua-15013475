class MainView:
    """최상위 메인 메뉴 화면"""

    def show_menu(self) -> str:
        print("\n===== 반도체 시료 생산 주문 관리 시스템 =====")
        print("1. 시료 관리")
        print("2. 주문 관리 (접수/승인/거절)")
        print("3. 모니터링")
        print("4. 생산 라인")
        print("5. 출고 처리")
        print("0. 종료")
        return input("메뉴를 선택하세요 >> ").strip()

    def show_message(self, message: str) -> None:
        print(message)
