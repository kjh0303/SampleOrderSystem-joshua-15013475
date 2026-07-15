class ProductionView:
    """생산 라인 화면 (입출력만 담당)"""

    def show_menu(self) -> str:
        print("\n----- 생산 라인 -----")
        print("1. 생산 현황 확인")
        print("2. 대기 주문 확인")
        print("0. 이전 메뉴")
        return input("메뉴를 선택하세요 >> ").strip()

    def show_current_status(self, item, order, sample) -> None:
        print("\n[생산 현황]")
        print(f"- 주문 #{order.order_id} | 고객: {order.customer_name} | 시료: {sample.name} (ID:{sample.sample_id})")
        print(f"- 목표 생산량: {item.target_qty}개 | 시작: {item.started_at} | 완료 예정: {item.finished_at}")

    def show_queue(self, rows) -> None:
        print("\n[생산 대기열] (FIFO: 등록된 순서대로 생산)")
        for position, (item, order, sample) in enumerate(rows, start=1):
            print(
                f"{position}. 주문 #{order.order_id} ({sample.name} x {item.target_qty}) - "
                f"고객: {order.customer_name}"
            )

    def show_message(self, message: str) -> None:
        print(message)
