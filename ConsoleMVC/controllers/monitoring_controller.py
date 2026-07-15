from models.order_repository import OrderRepository
from models.sample_repository import SampleRepository
from views.monitoring_view import MonitoringView


class MonitoringController:
    """상태별 주문량 및 시료별 재고량을 조회"""

    def __init__(self, order_repo: OrderRepository, sample_repo: SampleRepository, view: MonitoringView):
        self._order_repo = order_repo
        self._sample_repo = sample_repo
        self._view = view

    def show_order_volume(self) -> None:
        valid_orders = self._order_repo.find_valid_orders()
        self._view.show_orders_by_status(valid_orders)

    def show_stock_volume(self) -> None:
        samples = self._sample_repo.all()
        self._view.show_stock_status(samples)

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
