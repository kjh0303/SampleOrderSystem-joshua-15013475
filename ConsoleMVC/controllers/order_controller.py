import math

from ConsoleMVC.models.order import OrderStatus
from ConsoleMVC.models.order_repository import OrderRepository
from ConsoleMVC.models.production_queue import ProductionQueue
from ConsoleMVC.models.production_queue_repository import ProductionQueueRepository
from ConsoleMVC.models.sample_repository import SampleRepository
from ConsoleMVC.views.order_view import OrderView


class OrderController:
    """고객 주문 접수 및 생산 라인 담당자의 승인/거절을 처리"""

    def __init__(
        self,
        order_repo: OrderRepository,
        sample_repo: SampleRepository,
        queue_repo: ProductionQueueRepository,
        view: OrderView,
    ):
        self._order_repo = order_repo
        self._sample_repo = sample_repo
        self._queue_repo = queue_repo
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
        """재고가 충분하면 즉시 CONFIRMED로, 부족하면 부족분을 수율로 나눈
        실 생산량을 ProductionQueue에 등록하고 PRODUCING으로 전환한다.

        started_at/finished_at 설정과 생산 완료 판단(sync_production_state),
        FIFO 직렬 처리는 PLAN.md Phase 5에서 구현한다.
        """
        self._view.show_orders(self._order_repo.find_by_status(OrderStatus.RESERVED))
        order_id = self._view.input_order_id("승인")
        if order_id is None:
            self._view.show_message("승인이 취소되었습니다.")
            return
        order = self._order_repo.find_by_id(order_id)
        if order is None or order.status != OrderStatus.RESERVED:
            self._view.show_message("승인할 수 없는 주문입니다.")
            return

        sample = self._sample_repo.find_by_id(order.sample_id)
        if sample.stock_qty >= order.quantity:
            order.change_status(OrderStatus.CONFIRMED)
            self._order_repo.save(order)
            self._view.show_message(f"[승인 완료] 주문 #{order.order_id} -> 재고 충분, CONFIRMED 전환")
            return

        shortage = order.quantity - sample.stock_qty
        target_qty = math.ceil(shortage / sample.yield_rate)
        total_production_time = sample.avg_production_time * target_qty
        queue_item = ProductionQueue(
            queue_id="",
            order_id=order.order_id,
            sample_id=sample.sample_id,
            target_qty=target_qty,
            total_production_time=total_production_time,
        )
        self._queue_repo.add(queue_item)
        order.change_status(OrderStatus.PRODUCING)
        self._order_repo.save(order)
        self._view.show_message(f"[승인 완료] 주문 #{order.order_id} -> 재고 부족, 생산 대기열 등록")

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
