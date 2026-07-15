from ConsoleMVC.models.order import OrderStatus
from ConsoleMVC.models.order_repository import OrderRepository
from ConsoleMVC.models.production_line import ProductionLine
from ConsoleMVC.models.sample_repository import SampleRepository
from ConsoleMVC.views.shipment_view import ShipmentView


class ShipmentController:
    """CONFIRMED 상태 주문에 대한 출고 처리"""

    def __init__(
        self,
        order_repo: OrderRepository,
        sample_repo: SampleRepository,
        production_line: ProductionLine,
        view: ShipmentView,
    ):
        self._order_repo = order_repo
        self._sample_repo = sample_repo
        self._production_line = production_line
        self._view = view

    def ship_order(self) -> None:
        self._production_line.sync()
        confirmed_orders = self._order_repo.find_by_status(OrderStatus.CONFIRMED)
        self._view.show_orders(confirmed_orders)
        order_id = self._view.input_order_id()
        if order_id is None:
            self._view.show_message("출고가 취소되었습니다.")
            return
        order = self._order_repo.find_by_id(order_id)
        if order is None or order.status != OrderStatus.CONFIRMED:
            self._view.show_message("출고할 수 없는 주문입니다.")
            return

        sample = self._sample_repo.find_by_id(order.sample_id)
        sample.remove_stock(order.quantity)
        self._sample_repo.save(sample)
        order.change_status(OrderStatus.RELEASE)
        self._order_repo.save(order)
        self._view.show_message(f"[출고 완료] 주문 #{order.order_id} -> 상태 RELEASE 전환")

    def run(self) -> None:
        while True:
            choice = self._view.show_menu()
            if choice == "1":
                self.ship_order()
            elif choice == "0":
                break
            else:
                self._view.show_message("잘못된 입력입니다.")
