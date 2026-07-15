from typing import List, Optional

from ConsoleMVC.models.order import Order


class ShipmentView:
    """출고 처리 화면 (입출력만 담당)"""

    def show_menu(self) -> str:
        print("\n----- 출고 처리 -----")
        print("1. 출고 실행")
        print("0. 이전 메뉴")
        return input("메뉴를 선택하세요 >> ").strip()

    def input_order_id(self) -> Optional[int]:
        raw_order_id = input("출고할 주문 ID (0: 취소): ").strip()
        if raw_order_id == "0":
            return None
        return int(raw_order_id)

    def show_orders(self, orders: List[Order]) -> None:
        if not orders:
            print("출고 대상 주문이 없습니다.")
            return
        print(f"{'ID':<5}{'시료ID':<8}{'고객명':<12}{'수량':<6}{'상태':<10}")
        for o in orders:
            print(f"{o.order_id:<5}{o.sample_id:<8}{o.customer_name:<12}{o.quantity:<6}{o.status.value:<10}")

    def show_message(self, message: str) -> None:
        print(message)
