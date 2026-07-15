from ConsoleMVC.models.order import OrderStatus
from ConsoleMVC.models.order_repository import OrderRepository
from ConsoleMVC.models.production_line import ProductionLine
from ConsoleMVC.models.sample_repository import SampleRepository
from ConsoleMVC.views.monitoring_view import MonitoringView

_PENDING_STATUSES = (OrderStatus.RESERVED, OrderStatus.PRODUCING, OrderStatus.CONFIRMED)


class MonitoringController:
    """상태별 주문량 및 시료별 재고량을 조회"""

    def __init__(
        self,
        order_repo: OrderRepository,
        sample_repo: SampleRepository,
        production_line: ProductionLine,
        view: MonitoringView,
    ):
        self._order_repo = order_repo
        self._sample_repo = sample_repo
        self._production_line = production_line
        self._view = view

    def show_order_volume(self) -> None:
        valid_orders = self._order_repo.find_valid_orders()
        self._view.show_orders_by_status(valid_orders)

    def show_stock_volume(self) -> None:
        self._production_line.sync()
        samples = self._sample_repo.all()
        orders = self._order_repo.all()
        rows = [(sample, self._determine_stock_status(sample, orders)) for sample in samples]
        self._view.show_stock_status(rows)

    @staticmethod
    def _determine_stock_status(sample, orders) -> str:
        if sample.stock_qty == 0:
            return "고갈"
        demand = sum(
            o.quantity for o in orders
            if o.sample_id == sample.sample_id and o.status in _PENDING_STATUSES
        )
        if sample.stock_qty < demand:
            return "부족"
        return "여유"

    def run(self) -> None:
        while True:
            choice = self._view.show_menu()
            if choice == "1":
                self.show_order_volume()
            elif choice == "2":
                self.show_stock_volume()
            elif choice == "0":
                break
            else:
                self._view.show_message("잘못된 입력입니다.")
