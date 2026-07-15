from typing import List, Optional, Tuple

from ConsoleMVC.models.order import Order


class OrderView:
    """주문 접수/승인/거절 화면 (입출력만 담당)"""

    def show_menu(self) -> str:
        print("\n----- 주문 관리 (접수/승인/거절) -----")
        print("1. 주문 접수")
        print("2. 주문 승인")
        print("3. 주문 거절")
        print("0. 이전 메뉴")
        return input("메뉴를 선택하세요 >> ").strip()

    def input_new_order(self) -> Optional[Tuple[int, str, int]]:
        raw_sample_id = input("시료 ID (0: 취소): ").strip()
        if raw_sample_id == "0":
            return None
        sample_id = int(raw_sample_id)
        customer_name = input("고객명: ").strip()
        quantity = int(input("주문 수량: ").strip())
        return sample_id, customer_name, quantity

    def input_order_id(self, action_name: str = "") -> Optional[int]:
        raw_order_id = input(f"{action_name} 처리할 주문 ID (0: 취소): ").strip()
        if raw_order_id == "0":
            return None
        return int(raw_order_id)

    def show_orders(self, orders: List[Order]) -> None:
        if not orders:
            print("해당하는 주문이 없습니다.")
            return
        print(f"{'ID':<5}{'시료ID':<8}{'고객명':<12}{'수량':<6}{'상태':<10}")
        for o in orders:
            print(f"{o.order_id:<5}{o.sample_id:<8}{o.customer_name:<12}{o.quantity:<6}{o.status.value:<10}")

    def show_message(self, message: str) -> None:
        print(message)
