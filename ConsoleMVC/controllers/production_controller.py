from ConsoleMVC.models.order_repository import OrderRepository
from ConsoleMVC.models.production_line import ProductionLine
from ConsoleMVC.models.sample_repository import SampleRepository
from ConsoleMVC.views.production_view import ProductionView


class ProductionController:
    """생산 현황 확인 / 대기 주문(FIFO) 확인.

    두 메뉴 모두 진입 시 `ProductionLine.sync()`를 먼저 호출해, 조회
    시점의 현재 시각 기준으로 완료된 작업의 재고/주문 상태를 갱신하고
    필요하면 다음 대기 항목을 시작시킨 뒤 화면을 표시한다.
    """

    def __init__(
        self,
        production_line: ProductionLine,
        order_repo: OrderRepository,
        sample_repo: SampleRepository,
        view: ProductionView,
    ):
        self._production_line = production_line
        self._order_repo = order_repo
        self._sample_repo = sample_repo
        self._view = view

    def show_current_status(self) -> None:
        self._production_line.sync()
        item = self._production_line.current_item()
        if item is None:
            self._view.show_message("현재 생산 중인 주문이 없습니다.")
            return
        order = self._order_repo.find_by_id(item.order_id)
        sample = self._sample_repo.find_by_id(item.sample_id)
        self._view.show_current_status(item, order, sample)

    def show_waiting_orders(self) -> None:
        self._production_line.sync()
        items = self._production_line.waiting_items()
        if not items:
            self._view.show_message("대기 중인 생산 주문이 없습니다.")
            return
        rows = [
            (item, self._order_repo.find_by_id(item.order_id), self._sample_repo.find_by_id(item.sample_id))
            for item in items
        ]
        self._view.show_queue(rows)

    def run(self) -> None:
        while True:
            choice = self._view.show_menu()
            if choice == "1":
                self.show_current_status()
            elif choice == "2":
                self.show_waiting_orders()
            elif choice == "0":
                break
            else:
                self._view.show_message("잘못된 입력입니다.")
