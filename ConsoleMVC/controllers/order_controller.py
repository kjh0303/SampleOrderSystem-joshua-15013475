from ConsoleMVC.models.order import OrderStatus
from ConsoleMVC.models.order_repository import OrderRepository
from ConsoleMVC.models.production_line import ProductionLine
from ConsoleMVC.models.sample_repository import SampleRepository
from ConsoleMVC.views.order_view import OrderView


class OrderController:
    """고객 주문 접수 및 생산 라인 담당자의 승인/거절을 처리"""

    def __init__(
        self,
        order_repo: OrderRepository,
        sample_repo: SampleRepository,
        production_line: ProductionLine,
        view: OrderView,
    ):
        self._order_repo = order_repo
        self._sample_repo = sample_repo
        self._production_line = production_line
        self._view = view

    def receive_order(self) -> None:
        result = self._view.input_new_order()
        if result is None:
            self._view.show_message("접수가 취소되었습니다.")
            return
        sample_id, customer_name, quantity = result
        sample = self._sample_repo.find_by_id(sample_id)
        if sample is None:
            self._view.show_message("존재하지 않는 시료입니다.")
            return
        order = self._order_repo.add(sample_id, customer_name, quantity)
        self._view.show_message(f"[접수 완료] 주문 #{order.order_id}")

    def approve_order(self) -> None:
        """재고 충분/부족에 따른 CONFIRMED/PRODUCING 분기는 PLAN.md Phase 4에서
        별도 Plan.md(RED-GREEN-REVIEW)로 구현한다. 여기서는 아직 구현하지 않는다."""
        self._view.show_orders(self._order_repo.find_by_status(OrderStatus.RESERVED))
        order_id = self._view.input_order_id("승인")
        if order_id is None:
            self._view.show_message("승인이 취소되었습니다.")
            return
        order = self._order_repo.find_by_id(order_id)
        if order is None or order.status != OrderStatus.RESERVED:
            self._view.show_message("승인할 수 없는 주문입니다.")
            return
        raise NotImplementedError("주문 승인의 재고 분기 로직은 PLAN.md Phase 4에서 구현 예정")

    def reject_order(self) -> None:
        self._view.show_orders(self._order_repo.find_by_status(OrderStatus.RESERVED))
        order_id = self._view.input_order_id("거절")
        if order_id is None:
            self._view.show_message("거절이 취소되었습니다.")
            return
        order = self._order_repo.find_by_id(order_id)
        if order is None or order.status != OrderStatus.RESERVED:
            self._view.show_message("거절할 수 없는 주문입니다.")
            return
        order.change_status(OrderStatus.REJECTED)
        self._order_repo.save(order)
        self._view.show_message(f"[거절 완료] 주문 #{order.order_id}")

    def run(self) -> None:
        while True:
            choice = self._view.show_menu()
            if choice == "1":
                self.receive_order()
            elif choice == "2":
                self.approve_order()
            elif choice == "3":
                self.reject_order()
            elif choice == "0":
                break
            else:
                self._view.show_message("잘못된 입력입니다.")
