from typing import Dict, List

from models.order import Order
from models.sample import Sample

_DISPLAY_STATUS_ORDER = ["RESERVED", "CONFIRMED", "PRODUCING", "RELEASE"]


class MonitoringView:
    """모니터링 화면 (입출력만 담당)"""

    def show_menu(self) -> str:
        print("\n----- 모니터링 -----")
        print("1. 주문량 확인")
        print("2. 재고량 확인")
        print("0. 이전 메뉴")
        return input("메뉴를 선택하세요 >> ").strip()

    def show_orders_by_status(self, orders: List[Order]) -> None:
        """RESERVED/CONFIRMED/PRODUCING/RELEASE 상태별 주문 목록을 출력한다. (REJECTED 제외)"""
        grouped: Dict[str, List[Order]] = {name: [] for name in _DISPLAY_STATUS_ORDER}
        for o in orders:
            grouped[o.status.value].append(o)

        print("\n[상태별 주문 목록]")
        for status_name in _DISPLAY_STATUS_ORDER:
            status_orders = grouped[status_name]
            print(f"\n- {status_name} ({len(status_orders)}건)")
            if not status_orders:
                print("  해당 주문 없음")
                continue
            for o in status_orders:
                print(f"  주문 #{o.order_id} | 시료ID {o.sample_id} | {o.customer_name} | 수량 {o.quantity}")

    def show_stock_status(self, samples: List[Sample]) -> None:
        # TODO(PLAN.md Phase 7): 주문 대비 여유/부족/고갈 상태 판정은 아직 없음.
        print("\n[시료별 재고 현황]")
        if not samples:
            print("등록된 시료가 없습니다.")
            return
        for s in samples:
            print(f"- {s.name} (ID:{s.sample_id}): 재고 {s.stock_qty}개")

    def show_message(self, message: str) -> None:
        print(message)
