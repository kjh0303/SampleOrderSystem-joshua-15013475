from models.order_repository import OrderRepository
from models.production_line import ProductionLine
from models.sample_repository import SampleRepository
from views.production_view import ProductionView


class ProductionController:
    """생산 현황 확인 / 대기 주문(FIFO) 확인.

    target_qty(ceil(부족분/수율)) 계산, 총 생산 시간 계산, started_at/finished_at
    기반 완료 판단(sync_production_state) 등 실제 생산 로직은 PLAN.md Phase 5에서
    별도 Plan.md(RED-GREEN-REVIEW)로 구현한다. 여기서는 아직 구현하지 않는다.
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
        raise NotImplementedError("생산 현황 확인은 PLAN.md Phase 5에서 구현 예정")

    def show_waiting_orders(self) -> None:
        raise NotImplementedError("대기 주문(FIFO) 확인은 PLAN.md Phase 5에서 구현 예정")

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
